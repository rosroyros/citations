import os
from logger import setup_logger
from typing import List
from pathlib import Path


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
    log_file_path = "/opt/citations/logs/citations.log"

    try:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file_path)
        os.makedirs(log_dir, exist_ok=True)

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

        # Append to log file
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(content_str)

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
    log_dir = Path("/opt/citations/logs")
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