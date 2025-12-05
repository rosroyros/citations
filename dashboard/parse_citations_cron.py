#!/usr/bin/env python3
"""
Cron job entry point for incremental citation log parsing
Runs every 5 minutes to parse new citation entries and update citations_dashboard table
"""
import logging
import sys
import time
from pathlib import Path

# Add both directories to the Python path
sys.path.insert(0, '/opt/citations/dashboard')
sys.path.insert(0, '/opt/citations/backend')

from backend.citation_logger import parse_citation_blocks
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

        # Initialize database manager for citations_dashboard table
        with DatabaseManager(PRODUCTION_DB_PATH) as db:
            logger.info(f"Processing citations from log: {PRODUCTION_CITATION_LOG_PATH}")

            # Read the citation log file
            with open(PRODUCTION_CITATION_LOG_PATH, 'r') as f:
                content = f.read()

            # Parse citations using the correct parser for citation log format
            citation_blocks = parse_citation_blocks(content)

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

                # Insert citations into the database
                for citation in citations_data:
                    try:
                        db.insert_citation_to_dashboard(citation)
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