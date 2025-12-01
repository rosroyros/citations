import os
import shutil
from logger import setup_logger
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import sqlite3
from database import get_validations_db_path


# Initialize logger for citation logging
logger = setup_logger("citation_logger")


def log_citations_to_dashboard(job_id: str, citations: List[str]) -> bool:
    """
    Log citations to dashboard in structured format for parsing.

    Args:
        job_id: Unique identifier for the validation job
        citations: List of citation strings to log

    Returns:
        bool: True if successful, False if failed (never raises exceptions)

    Format:
        <<JOB_ID:job_id>>
        citation1
        citation2
        ...
        <<<END_JOB>>>
    """
    log_file_path = os.environ.get('CITATION_LOG_PATH', DEFAULT_LOG_PATH)

    try:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file_path)
        os.makedirs(log_dir, exist_ok=True)

        # Check disk space before attempting write
        disk_info = check_disk_space(log_dir)
        if disk_info['error']:
            logger.critical(f"Disk space check failed for job {job_id}: {disk_info['error']}")
            return False

        if not disk_info['has_minimum']:
            logger.critical(f"Insufficient disk space for citation logging - only {disk_info['available_gb']:.2f}GB available, minimum required: {MIN_DISK_SPACE_BYTES / (1024 * 1024 * 1024):.2f}GB")
            return False

        if disk_info['has_warning']:
            logger.warning(f"Low disk space warning for citation logging - only {disk_info['available_gb']:.2f}GB available")

        # Build structured content
        content = []
        content.append(f"<<JOB_ID:{job_id}>>")

        # Add each citation (empty list will skip this loop)
        for citation in citations:
            content.append(citation)

        # Add end marker
        content.append("<<<END_JOB>>>")

        # Write to file with newline separators
        content_str = "\n".join(content) + "\n"

        # Append to log file with enhanced error handling
        try:
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(content_str)
                # Force write to disk
                f.flush()
                os.fsync(f.fileno())
        except (IOError, OSError) as write_error:
            # Check if it's a disk space issue after write attempt
            if "No space left on device" in str(write_error):
                logger.critical(f"Disk space exhausted during citation logging for job {job_id}: {str(write_error)}")
                # Check disk space again for accurate reporting in critical alert
                # Note: This provides real-time data for operators, despite pre-write check
                post_write_disk_info = check_disk_space(log_dir)
                if post_write_disk_info['available_gb'] < 0.1:
                    logger.critical(f"CRITICAL: Disk space nearly exhausted - only {post_write_disk_info['available_gb']:.3f}GB remaining")
            else:
                logger.critical(f"Write operation failed for job {job_id}: {str(write_error)}")
            return False

        logger.info(f"Successfully logged {len(citations)} citations for job {job_id}")
        return True

    except (IOError, OSError) as e:
        logger.critical(f"Failed to log citations for job {job_id}: {str(e)}")
        return False
    except Exception as e:
        logger.critical(f"Unexpected error logging citations for job {job_id}: {str(e)}")
        return False


def ensure_citation_log_ready() -> bool:
    """
    Ensure citation log directory and file permissions are ready for logging.

    Returns:
        bool: True if directory exists and write permissions are validated, False otherwise
    """
    log_dir = Path(os.environ.get('CITATION_LOG_DIR', DEFAULT_LOG_DIR))
    log_file = log_dir / "citations.log"

    try:
        # Create directory with parents if it doesn't exist
        log_dir.mkdir(parents=True, exist_ok=True)

        # Test write permissions by attempting to touch the file
        if not log_file.exists():
            log_file.touch()

        # Verify write permissions using os.access
        if os.access(log_file, os.W_OK):
            logger.info("Citation log directory and permissions are ready")
            return True
        else:
            logger.critical("No write permissions to citation log file")
            return False

    except (OSError, IOError, PermissionError) as e:
        logger.critical(f"Failed to prepare citation log directory: {str(e)}")
        return False
    except Exception as e:
        logger.critical(f"Unexpected error preparing citation log: {str(e)}")
        return False


# Constants for citation parsing
JOB_ID_START_MARKER = '<<JOB_ID:'
JOB_ID_END_MARKER = '>>'
END_JOB_MARKER = '<<<END_JOB>>>'

# Default configuration constants
DEFAULT_LOG_PATH = "/opt/citations/logs/citations.log"
DEFAULT_LOG_DIR = "/opt/citations/logs"

# Disk space thresholds
MIN_DISK_SPACE_BYTES = 100 * 1024 * 1024  # 100MB minimum free space
WARNING_DISK_SPACE_BYTES = 500 * 1024 * 1024  # 500MB warning level


def check_disk_space(path: str) -> Dict[str, Any]:
    """
    Check available disk space for a given path.

    Args:
        path: Path to check disk space for

    Returns:
        Dict with disk space information:
        - available_bytes: Available disk space in bytes
        - total_bytes: Total disk space in bytes
        - available_gb: Available disk space in GB
        - has_minimum: True if minimum space is available
        - has_warning: True if space is at warning level
        - error: Error message if check failed
    """
    try:
        stat = shutil.disk_usage(path)
        available_bytes = stat.free
        total_bytes = stat.total
        available_gb = available_bytes / (1024 * 1024 * 1024)

        has_minimum = available_bytes >= MIN_DISK_SPACE_BYTES
        has_warning = available_bytes < WARNING_DISK_SPACE_BYTES

        return {
            'available_bytes': available_bytes,
            'total_bytes': total_bytes,
            'available_gb': available_gb,
            'has_minimum': has_minimum,
            'has_warning': has_warning,
            'error': None
        }

    except Exception as e:
        logger.error(f"Failed to check disk space for path {path}: {str(e)}")
        return {
            'available_bytes': 0,
            'total_bytes': 0,
            'available_gb': 0,
            'has_minimum': False,
            'has_warning': True,
            'error': str(e)
        }

def extract_job_id_from_marker(line: str) -> str:
    """
    Extract job_id from a JOB_ID marker line.

    Args:
        line: Line containing the JOB_ID marker

    Returns:
        Extracted job_id string
    """
    return line[len(JOB_ID_START_MARKER):-len(JOB_ID_END_MARKER)]

def parse_citation_blocks(content: str) -> List[Tuple[str, List[str]]]:
    """
    Parse structured citation format into list of (job_id, citations) tuples.

    Args:
        content: String containing citation blocks in structured format

    Returns:
        List of tuples where each tuple contains (job_id, citations_list)

    Format expected:
        <<JOB_ID:job_id>>
        citation1
        citation2
        ...
        <<<END_JOB>>>
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
                logger.warning(f"Incomplete citation block found for job {current_job_id} - missing {END_JOB_MARKER}")

            try:
                current_job_id = extract_job_id_from_marker(line)
                current_citations = []
            except Exception as e:
                logger.error(f"Failed to parse job ID from line: {line} - {str(e)}")
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

        # Add citation if we're in a block
        if current_job_id is not None:
            current_citations.append(line)

    # Check for incomplete block at end of content
    if current_job_id is not None:
        logger.warning(f"Incomplete citation block found for job {current_job_id} at end of content - missing {END_JOB_MARKER}")

    return results


class CitationLogParser:
    """
    Stateful parser for processing citation logs and integrating with dashboard data flow.

    This class maintains state about processed jobs to prevent duplicate processing
    and integrates with the existing jobs data structure and database connections.

    Usage:
        jobs_dict = {}  # Your existing jobs dictionary from app.py
        parser = CitationLogParser(jobs_dict)
        parser.process_citations_for_dashboard()
        jobs_with_citations = parser.get_jobs_with_citations()
    """

    def __init__(self, jobs_dict: Dict[str, Dict[str, Any]]):
        """
        Initialize the parser with a reference to the jobs dictionary.

        Args:
            jobs_dict: Reference to the global jobs dictionary from app.py
        """
        self.jobs_dict = jobs_dict
        self.processed_jobs: set = set()

    def process_citations_for_dashboard(self, log_file_path: Optional[str] = None) -> bool:
        """
        Main integration function to process citations from log file into dashboard data flow.

        This function:
        1. Reads the citation log file
        2. Parses structured citation blocks using parse_citation_blocks()
        3. For each job, checks if it exists in validations database
        4. Adds citations to existing jobs in the jobs dictionary
        5. Marks jobs as processed to prevent duplicates

        Args:
            log_file_path: Path to the citation log file (optional, uses CITATION_LOG_PATH env var if not provided)

        Returns:
            bool: True if processing completed successfully, False otherwise
        """
        try:
            # Use default path if not provided
            if log_file_path is None:
                log_file_path = os.environ.get('CITATION_LOG_PATH', DEFAULT_LOG_PATH)

            # Read citation log file
            if not os.path.exists(log_file_path):
                logger.info(f"Citation log file not found: {log_file_path}")
                return True  # Not an error - just no citations to process

            with open(log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse structured citation blocks
            citation_blocks = parse_citation_blocks(content)
            logger.info(f"Parsed {len(citation_blocks)} citation blocks from log")

            # Process each citation block
            for job_id, citations in citation_blocks:
                self._process_single_job_citations(job_id, citations)

            logger.info(f"Successfully processed citations for dashboard")
            return True

        except (IOError, OSError) as e:
            logger.error(f"File system error processing citations for dashboard: {str(e)}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Database error processing citations for dashboard: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error processing citations for dashboard: {str(e)}")
            return False

    def _process_single_job_citations(self, job_id: str, citations: List[str]) -> None:
        """
        Process citations for a single job.

        Args:
            job_id: Unique identifier for the validation job
            citations: List of citation strings for this job
        """
        try:
            # Skip if already processed
            if job_id in self.processed_jobs:
                logger.debug(f"Job {job_id} already processed, skipping")
                return

            # Check if job exists in validations database
            if not self.job_exists_in_validations(job_id):
                logger.debug(f"Job {job_id} not found in validations database, skipping")
                return

            # Add citations to job if job exists in jobs dict
            if self.add_citations_to_job(job_id, citations):
                # Mark as processed to prevent duplicates
                self.mark_job_citations_processed(job_id)
                logger.info(f"Added {len(citations)} citations to job {job_id}")

        except Exception as e:
            logger.error(f"Error processing citations for job {job_id}: {str(e)}")

    def job_exists_in_validations(self, job_id: Optional[str]) -> bool:
        """
        Check if a job exists in the validations database.

        Args:
            job_id: Unique identifier for the validation job (can be None or empty)

        Returns:
            bool: True if job exists in validations database, False otherwise
        """
        # Input validation
        if not job_id or not isinstance(job_id, str):
            logger.debug(f"Invalid job_id type or value: {type(job_id)}")
            return False

        job_id = job_id.strip()
        if len(job_id) == 0:
            logger.debug("Empty job_id after stripping whitespace")
            return False

        try:
            db_path = get_validations_db_path()

            if not os.path.exists(db_path):
                logger.debug(f"Validations database not found: {db_path}")
                return False

            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()

                # Check for job in validations table
                cursor.execute("SELECT job_id FROM validations WHERE job_id = ?", (job_id,))
                result = cursor.fetchone()

                return result is not None

        except sqlite3.Error as e:
            logger.error(f"Database error checking job {job_id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error checking job {job_id}: {str(e)}")
            return False

    def add_citations_to_job(self, job_id: str, citations: List[str]) -> bool:
        """
        Add citations to an existing job in the jobs dictionary.

        Args:
            job_id: Unique identifier for the validation job
            citations: List of citation strings to add to the job

        Returns:
            bool: True if citations were added successfully, False otherwise
        """
        try:
            # Check if job exists in jobs dictionary
            if job_id not in self.jobs_dict:
                logger.debug(f"Job {job_id} not found in jobs dictionary")
                return False

            # Add citations to the job
            job = self.jobs_dict[job_id]
            job['citations'] = citations
            job['citation_count'] = len(citations)
            job['has_citations'] = True

            logger.debug(f"Added {len(citations)} citations to job {job_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding citations to job {job_id}: {str(e)}")
            return False

    def mark_job_citations_processed(self, job_id: str) -> None:
        """
        Mark a job as having its citations processed to prevent duplicate processing.

        Args:
            job_id: Unique identifier for the validation job
        """
        self.processed_jobs.add(job_id)
        logger.debug(f"Marked job {job_id} as processed")

    def get_jobs_with_citations(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all jobs that have citations processed.

        Returns:
            Dict of job_id -> job_data for jobs with citations
        """
        jobs_with_citations = {}

        for job_id, job_data in self.jobs_dict.items():
            if job_data.get('has_citations', False):
                jobs_with_citations[job_id] = job_data

        return jobs_with_citations