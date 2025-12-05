#!/usr/bin/env python3
"""
Cron job entry point for incremental citation log parsing
Runs every 5 minutes to parse new citation entries and update citations_dashboard table
"""
import logging
import sys
import time
from pathlib import Path

# Add dashboard directory to the Python path
sys.path.insert(0, '/opt/citations/dashboard')

from log_parser import CitationLogParser
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

        # Initialize citation parser with file offset tracking
        parser = CitationLogParser(
            log_file_path=PRODUCTION_CITATION_LOG_PATH,
            position_file_path="/opt/citations/logs/citations.position"
        )

        # Initialize database manager for citations_dashboard table
        with DatabaseManager(PRODUCTION_DB_PATH) as db:
            logger.info(f"Processing citations from log: {PRODUCTION_CITATION_LOG_PATH}")

            # Parse new citations from the log file (only new entries since last run)
            jobs_data = parser.parse_new_entries()

            # Extract citations from job data and convert to dashboard format
            citations_data = []
            for job in jobs_data:
                # Extract citation information from job
                if job.get('citations_full'):
                    citations_data.append({
                        'job_id': job.get('job_id'),
                        'citation_text': job.get('citations_full'),
                        'citation_type': 'full',
                        'user_type': job.get('user_type'),
                        'processing_time_ms': job.get('duration_seconds', 0) * 1000 if job.get('duration_seconds') else None
                    })
                elif job.get('citations_preview'):
                    citations_data.append({
                        'job_id': job.get('job_id'),
                        'citation_text': job.get('citations_preview'),
                        'citation_type': 'preview',
                        'user_type': job.get('user_type'),
                        'processing_time_ms': job.get('duration_seconds', 0) * 1000 if job.get('duration_seconds') else None
                    })

            if citations_data:
                logger.info(f"Found {len(citations_data)} new citations to process")

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
                        else:
                            logger.debug(f"Skipping duplicate citation for job {citation.get('job_id')}")

                    except Exception as e:
                        logger.error(f"Failed to insert citation for job {citation.get('job_id', 'unknown')}: {str(e)}")

                logger.info(f"Successfully processed {len(citations_data)} citations")
            else:
                logger.info("No new citations found in log segment")

        duration = time.time() - start_time
        logger.info(f"Incremental citation log parsing completed successfully in {duration:.2f} seconds")

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Citation cron job failed after {duration:.2f} seconds: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()