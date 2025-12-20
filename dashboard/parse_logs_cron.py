#!/usr/bin/env python3
"""
Cron job entry point for incremental log parsing
Runs every 5 minutes to parse new log entries and update database
"""
import logging
import sys
import time
import os
from pathlib import Path

from dashboard.cron_parser import CronLogParser

# Configure logging
CRON_LOG_PATH = os.getenv('CRON_LOG_PATH', '/opt/citations/logs/cron.log')

# Ensure log directory exists if we are using a custom path, or fallback to stdout if permission denied (handled by try/except block typically, but here we just set it up)
try:
    file_handler = logging.FileHandler(CRON_LOG_PATH)
except (FileNotFoundError, PermissionError):
    # Fallback to local file if system path is not accessible
    file_handler = logging.FileHandler('cron.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        file_handler,
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Production paths (default)
DEFAULT_LOG_PATH = "/opt/citations/logs/app.log"
DEFAULT_DB_PATH = "/opt/citations/dashboard/data/validations.db"
DEFAULT_NGINX_LOG_PATH = "/var/log/nginx/access.log"

# Allow overrides via environment variables
PRODUCTION_LOG_PATH = os.getenv("CITATION_LOG_PATH", DEFAULT_LOG_PATH)
PRODUCTION_DB_PATH = os.getenv("CITATION_DB_PATH", DEFAULT_DB_PATH)
PRODUCTION_NGINX_LOG_PATH = os.getenv("NGINX_LOG_PATH", DEFAULT_NGINX_LOG_PATH)

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
            # Don't exit, try parsing nginx logs even if app log is missing

        if not db_path.exists():
            logger.error(f"Database not found: {PRODUCTION_DB_PATH}")
            sys.exit(1)

        # Initialize parser
        parser = CronLogParser(PRODUCTION_DB_PATH)
        
        # Parse application logs
        if log_path.exists():
            parser.parse_incremental(PRODUCTION_LOG_PATH)
            
        # Parse Nginx logs
        if os.path.exists(PRODUCTION_NGINX_LOG_PATH):
            logger.info(f"Parsing Nginx logs: {PRODUCTION_NGINX_LOG_PATH}")
            parser.parse_nginx_incremental(PRODUCTION_NGINX_LOG_PATH)
        else:
            logger.warning(f"Nginx log file not found: {PRODUCTION_NGINX_LOG_PATH}")

        duration = time.time() - start_time
        logger.info(f"Incremental log parsing completed successfully in {duration:.2f} seconds")

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Cron job failed after {duration:.2f} seconds: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()