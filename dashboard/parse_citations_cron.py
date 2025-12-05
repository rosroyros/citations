#!/usr/bin/env python3
"""
Cron job entry point for incremental citation log parsing
Runs every 5 minutes to parse new citation entries and update citations_dashboard table
"""
import logging
import sys
import time
import os
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
                position_str = f.read().strip()
                if position_str.isdigit():
                    return int(position_str)
    except (IOError, ValueError) as e:
        logger.warning(f"Could not read position file {POSITION_FILE_PATH}: {e}")
    return 0

def save_position(position: int) -> None:
    """Save the current position to the position file."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(POSITION_FILE_PATH), exist_ok=True)
        with open(POSITION_FILE_PATH, 'w') as f:
            f.write(str(position))
    except IOError as e:
        logger.warning(f"Could not save position to {POSITION_FILE_PATH}: {e}")

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
        current_file_size = log_path.stat().st_size

        # Check if there's new content
        if current_file_size <= last_position:
            logger.info("No new content to process")
            return

        logger.info(f"Processing new content from position {last_position} to {current_file_size}")

        # Read only the new content
        with open(PRODUCTION_CITATION_LOG_PATH, 'r', encoding='utf-8') as f:
            f.seek(last_position)
            new_content = f.read()

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

        # Update position to end of file
        new_position = current_file_size
        save_position(new_position)
        logger.info(f"Updated position to {new_position}")

        duration = time.time() - start_time
        logger.info(f"Incremental citation log parsing completed successfully in {duration:.2f} seconds")

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Citation cron job failed after {duration:.2f} seconds: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()