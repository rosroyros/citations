#!/usr/bin/env python3
"""
Cron job entry point for incremental citation log parsing
Runs every 5 minutes to parse new citation entries and update citations_dashboard table
"""
import logging
import sys
import time
import os
import tempfile
from pathlib import Path

# Add dashboard directory to the Python path
sys.path.insert(0, '/opt/citations/dashboard')

from database import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/citations/logs/citation-parser-cron.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Production paths
PRODUCTION_CITATION_LOG_PATH = "/opt/citations/logs/citations.log"
PRODUCTION_DB_PATH = "/opt/citations/dashboard/data/validations.db"
POSITION_FILE_PATH = "/opt/citations/logs/citations.position"

# Citation log format markers
JOB_ID_START_MARKER = "<<JOB_ID:"
JOB_ID_END_MARKER = ">>"
END_JOB_MARKER = "<<<END_JOB>>>"

def extract_job_id_from_marker(line: str) -> str:
    """Extract job ID from JOB_ID marker line."""
    return line[len(JOB_ID_START_MARKER):-len(JOB_ID_END_MARKER)]

def parse_citation_blocks(content: str):
    """
    Parse structured citation format into list of (job_id, citations) tuples.
    This is the correct parser for the citations.log file format.
    """
    if not content.strip():
        return []

    results = []
    lines = content.split('\n')
    current_job_id = None
    current_citations = []

    for line in lines:
        line = line.strip()

        # Check for start marker
        if line.startswith(JOB_ID_START_MARKER) and line.endswith(JOB_ID_END_MARKER):
            # If we encounter a new job ID while already processing one,
            # the previous block was incomplete (no END_JOB), so we discard it
            if current_job_id is not None:
                logging.warning(f"Incomplete citation block found for job {current_job_id} - missing {END_JOB_MARKER}")

            try:
                current_job_id = extract_job_id_from_marker(line)
                current_citations = []
            except Exception as e:
                logging.error(f"Failed to parse job ID from line: {line} - {str(e)}")
                current_job_id = None
                current_citations = []
            continue

        # Check for end marker
        if line == END_JOB_MARKER:
            if current_job_id is not None:
                results.append((current_job_id, current_citations.copy()))
                current_job_id = None
                current_citations = []
            continue

        # Add citation text if we're in a job block
        if current_job_id is not None and line:
            current_citations.append(line)

    return results

def load_position() -> int:
    """Load the last processed position from the position file."""
    try:
        if os.path.exists(POSITION_FILE_PATH):
            with open(POSITION_FILE_PATH, 'r') as f:
                content = f.read().strip()
                if content.isdigit():
                    pos = int(content)
                    if pos < 0:
                        logger.warning(f"Invalid negative position {pos} found in {POSITION_FILE_PATH}. Resetting to 0.")
                        return 0
                    return pos
                else:
                    logger.warning(f"Invalid content in position file {POSITION_FILE_PATH}: '{content}'")
    except (IOError, ValueError) as e:
        logger.warning(f"Could not read position file {POSITION_FILE_PATH}: {e}")
    return 0

def save_position(position: int) -> None:
    """Save the current position to the position file atomically."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(POSITION_FILE_PATH), exist_ok=True)

        # Write to temp file first to ensure atomicity
        with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=os.path.dirname(POSITION_FILE_PATH)) as tf:
            tf.write(str(position))
            temp_name = tf.name

        # Atomic rename
        os.replace(temp_name, POSITION_FILE_PATH)

    except IOError as e:
        logger.error(f"Could not save position to {POSITION_FILE_PATH}: {e}")
        # Clean up temp file if rename failed
        if 'temp_name' in locals() and os.path.exists(temp_name):
            try:
                os.remove(temp_name)
            except OSError:
                pass

def adjust_to_utf8_boundary(file_handle, byte_pos: int) -> int:
    """
    Adjust byte position to nearest valid UTF-8 character boundary.

    When seeking to a byte position in a UTF-8 file, the position might fall
    in the middle of a multi-byte character (e.g., Greek letters use 2 bytes).
    This function scans backwards to find the nearest valid character boundary.

    UTF-8 continuation bytes have bit pattern 10xxxxxx (0x80-0xBF).
    Valid start bytes do NOT have this pattern.

    Args:
        file_handle: File handle opened in binary mode
        byte_pos: Desired byte position to adjust

    Returns:
        Adjusted byte position that aligns with UTF-8 character boundary
    """
    if byte_pos == 0:
        return 0

    # Read a few bytes before AND including the position to check
    # UTF-8 characters are at most 4 bytes, so checking up to 3 bytes back plus
    # the byte at the position gives us enough context
    check_start = max(0, byte_pos - 3)
    # Read one extra byte to check if the position itself is a continuation byte
    check_end = min(byte_pos + 1, file_handle.seek(0, 2))  # Get file size
    file_handle.seek(check_start)

    chunk = file_handle.read(check_end - check_start)

    # Calculate where our target byte is within this chunk
    target_offset = byte_pos - check_start

    # If the byte at our target position is a continuation byte,
    # we need to scan backwards to find the start of the character
    byte_at_target = chunk[target_offset] if target_offset < len(chunk) else None

    if byte_at_target is not None and (byte_at_target & 0xC0) == 0x80:
        # This is a continuation byte - scan backwards to find character start
        for i in range(target_offset, -1, -1):
            byte_val = chunk[i]
            if (byte_val & 0xC0) != 0x80:  # Found a non-continuation byte
                # If it's a start byte (0xC0-0xFD), the character starts here
                # If it's ASCII (< 0x80), we're at a valid boundary
                return check_start + i

        # Shouldn't reach here, but if we do, return 0
        return 0

    # Target byte is not a continuation byte, so it's already at a valid boundary
    return byte_pos

def main():
    """Main cron job function for citation parsing"""
    start_time = time.time()

    try:
        logger.info("Starting incremental citation log parsing")

        # Verify paths exist
        log_path = Path(PRODUCTION_CITATION_LOG_PATH)
        db_path = Path(PRODUCTION_DB_PATH)

        if not log_path.exists():
            logger.error(f"Citation log file not found: {PRODUCTION_CITATION_LOG_PATH}")
            sys.exit(1)

        if not db_path.exists():
            logger.error(f"Database not found: {PRODUCTION_DB_PATH}")
            sys.exit(1)

        # Load last position
        last_position = load_position()
        try:
            current_file_size = log_path.stat().st_size
        except OSError as e:
            logger.error(f"Failed to get size of log file: {e}")
            sys.exit(1)

        # Check for log rotation
        if current_file_size < last_position:
            logger.warning(f"Log rotation detected (current size {current_file_size} < last position {last_position}). Resetting to 0.")
            last_position = 0

        # Check if there's new content
        if current_file_size <= last_position:
            logger.info("No new content to process")
            return

        logger.info(f"Processing new content from position {last_position} to {current_file_size}")

        # LAYER 1: Adjust position to UTF-8 boundary BEFORE reading
        # This prevents seeking to the middle of a multi-byte UTF-8 character
        with open(PRODUCTION_CITATION_LOG_PATH, 'rb') as f:
            adjusted_position = adjust_to_utf8_boundary(f, last_position)

            if adjusted_position != last_position:
                logger.warning(f"Adjusted position from {last_position} to {adjusted_position} (UTF-8 character boundary)")
                last_position = adjusted_position

        # LAYER 2: Read with errors='replace' as safety net
        # Handles edge cases like incomplete multi-byte characters at EOF
        try:
            with open(PRODUCTION_CITATION_LOG_PATH, 'r', encoding='utf-8', errors='replace') as f:
                f.seek(last_position)
                new_content = f.read()
                # Get the actual position after reading (handles if file grew during read)
                new_position = f.tell()
        except IOError as e:
             logger.error(f"Failed to read log file: {e}")
             sys.exit(1)

        # LAYER 3: Check for UTF-8 replacement characters (corruption detection)
        # If we see replacement characters, don't save position - let it retry next time
        if '\ufffd' in new_content:
            logger.warning(f"UTF-8 replacement characters (\\ufffd) detected in content - possible data corruption")
            logger.warning(f"Position NOT saved - will retry on next run to recover valid data")
            # Don't update position, don't process this batch
            # Next run will attempt to read from same position
            return

        # CRITICAL: Update position immediately after reading to prevent re-reading
        # if the subsequent processing crashes or takes too long.
        save_position(new_position)
        logger.info(f"Updated position to {new_position} (immediately after read)")

        # Parse citations from new content using the correct parser
        citation_blocks = parse_citation_blocks(new_content)

        # Convert to dashboard format
        citations_data = []
        for job_id, citations in citation_blocks:
            for citation_text in citations:
                citations_data.append({
                    'job_id': job_id,
                    'citation_text': citation_text,
                    'citation_type': 'full',
                    'user_type': 'unknown',  # User type not available in citation log format
                    'processing_time_ms': None
                })

        if citations_data:
            logger.info(f"Found {len(citations_data)} new citations to process")

            # Initialize database manager for citations_dashboard table
            with DatabaseManager(PRODUCTION_DB_PATH) as db:
                # Insert citations into the database with deduplication check
                for citation in citations_data:
                    try:
                        # Check if citation already exists to prevent duplicates
                        cursor = db.conn.cursor()
                        cursor.execute("""
                            SELECT COUNT(*) FROM citations_dashboard
                            WHERE job_id = ? AND citation_text = ?
                        """, (citation.get('job_id'), citation.get('citation_text')))

                        if cursor.fetchone()[0] == 0:
                            db.insert_citation_to_dashboard(citation)
                            logger.debug(f"Inserted citation for job {citation.get('job_id')}")
                        else:
                            logger.debug(f"Skipping duplicate citation for job {citation.get('job_id')}")

                    except Exception as e:
                        logger.error(f"Failed to insert citation for job {citation.get('job_id', 'unknown')}: {str(e)}")

                logger.info(f"Successfully processed {len(citations_data)} citations")
        else:
            logger.info("No new citations found in new content")

        duration = time.time() - start_time
        logger.info(f"Incremental citation log parsing completed successfully in {duration:.2f} seconds")

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Citation cron job failed after {duration:.2f} seconds: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
