#!/usr/bin/env python3
"""
Cron job entry point for incremental log parsing
Runs every 5 minutes to parse new log entries and update database
"""
import logging
import sys
import time
from pathlib import Path

from dashboard.cron_parser import CronLogParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/citations/logs/cron.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Production paths
PRODUCTION_LOG_PATH = "/opt/citations/logs/app.log"
PRODUCTION_DB_PATH = "/opt/citations/dashboard/data/validations.db"

def main():
    """Main cron job function"""
    start_time = time.time()

    try:
        logger.info("Starting incremental log parsing")

        # Verify paths exist
        log_path = Path(PRODUCTION_LOG_PATH)
        db_path = Path(PRODUCTION_DB_PATH)

        if not log_path.exists():
            logger.error(f"Log file not found: {PRODUCTION_LOG_PATH}")
            sys.exit(1)

        if not db_path.exists():
            logger.error(f"Database not found: {PRODUCTION_DB_PATH}")
            sys.exit(1)

        # Initialize parser and run incremental parsing
        parser = CronLogParser(PRODUCTION_DB_PATH)
        parser.parse_incremental(PRODUCTION_LOG_PATH)

        duration = time.time() - start_time
        logger.info(f"Incremental log parsing completed successfully in {duration:.2f} seconds")

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Cron job failed after {duration:.2f} seconds: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()