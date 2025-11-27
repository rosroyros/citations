#!/usr/bin/env python3
"""
Cron-based incremental log parser
Handles incremental log parsing with metadata tracking
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict

from dashboard.database import DatabaseManager
from dashboard.log_parser import parse_logs

logger = logging.getLogger(__name__)


class CronLogParser:
    """
    Handles incremental log parsing for cron jobs

    Features:
    - Tracks last parsed timestamp in metadata
    - Only parses new lines since last run
    - Initial load parses last 3 days
    - Inserts parsed data to database
    """

    def __init__(self, db_path: str):
        """
        Initialize parser with database connection

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path

    def _update_timestamp_metadata(self, db: DatabaseManager, parsed_jobs: List[Dict]):
        """
        Update last parsed timestamp to the most recent job's timestamp

        Args:
            db: Database manager instance
            parsed_jobs: List of parsed jobs
        """
        if parsed_jobs:
            # Find the most recent timestamp among parsed jobs
            latest_timestamp = None
            for job in parsed_jobs:
                # Parse job created_at timestamp and make it naive
                job_time = datetime.fromisoformat(job["created_at"].replace("Z", "+00:00")).replace(tzinfo=None)
                if latest_timestamp is None or job_time > latest_timestamp:
                    latest_timestamp = job_time

            if latest_timestamp:
                # Store as naive datetime to match extract_timestamp() return type
                db.set_metadata("last_parsed_timestamp", latest_timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                # Fallback to now if no jobs found
                now = datetime.now()
                db.set_metadata("last_parsed_timestamp", now.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            # No jobs parsed, update to now
            now = datetime.now()
            db.set_metadata("last_parsed_timestamp", now.strftime("%Y-%m-%d %H:%M:%S"))

    def _insert_parsed_jobs(self, db: DatabaseManager, parsed_jobs: List[Dict]):
        """
        Insert parsed jobs into database

        Args:
            db: Database manager instance
            parsed_jobs: List of parsed jobs to insert
        """
        for job in parsed_jobs:
            db.insert_validation(job)

    def parse_incremental(self, log_file_path: str):
        """
        Parse only new log entries since last timestamp

        Args:
            log_file_path: Path to log file to parse
        """
        with DatabaseManager(self.db_path) as db:
            # Get last parsed timestamp
            last_timestamp_str = db.get_metadata("last_parsed_timestamp")
            last_timestamp = None

            if last_timestamp_str:
                try:
                    # Try ISO format first (for legacy data)
                    last_timestamp = datetime.fromisoformat(last_timestamp_str)
                except ValueError:
                    try:
                        # Try naive datetime format (YYYY-MM-DD HH:MM:SS)
                        last_timestamp = datetime.strptime(last_timestamp_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        # Invalid timestamp, fallback to initial load
                        last_timestamp = None

            if not last_timestamp:
                # No previous timestamp, do initial load
                self.parse_initial_load(log_file_path)
                return

            # Parse logs from last timestamp (ensure naive datetime for comparison)
            if last_timestamp and last_timestamp.tzinfo:
                last_timestamp = last_timestamp.replace(tzinfo=None)

            try:
                logger.info(f"Parsing logs from {last_timestamp}")
                parsed_jobs = parse_logs(log_file_path, start_timestamp=last_timestamp)

                if parsed_jobs:
                    logger.info(f"Found {len(parsed_jobs)} new jobs to insert")
                    # Insert to database
                    self._insert_parsed_jobs(db, parsed_jobs)

                    # Update last parsed timestamp
                    self._update_timestamp_metadata(db, parsed_jobs)
                    logger.info(f"Updated last_parsed_timestamp")
                else:
                    logger.info("No new jobs found in log segment")
                    # Still update timestamp to avoid reprocessing same logs
                    if last_timestamp:
                        db.set_metadata("last_parsed_timestamp", last_timestamp.strftime("%Y-%m-%d %H:%M:%S"))

            except Exception as e:
                # Log parsing error to database
                error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.error(f"Error parsing logs: {str(e)}")
                db.insert_parser_error(error_time, str(e), f"Error parsing {log_file_path}")

                # Still update timestamp to avoid retrying same logs on every run
                if last_timestamp:
                    db.set_metadata("last_parsed_timestamp", last_timestamp.strftime("%Y-%m-%d %H:%M:%S"))
                else:
                    db.set_metadata("last_parsed_timestamp", error_time)

    def parse_initial_load(self, log_file_path: str):
        """
        Initial load: parse logs from last 3 days

        Args:
            log_file_path: Path to log file to parse
        """
        with DatabaseManager(self.db_path) as db:
            # Parse logs from 3 days ago
            three_days_ago = datetime.now() - timedelta(days=3)

            try:
                logger.info(f"Running initial load from {three_days_ago}")
                parsed_jobs = parse_logs(log_file_path, start_timestamp=three_days_ago)

                if parsed_jobs:
                    logger.info(f"Initial load found {len(parsed_jobs)} jobs from last 3 days")
                    # Insert to database
                    self._insert_parsed_jobs(db, parsed_jobs)

                    # Update last parsed timestamp
                    self._update_timestamp_metadata(db, parsed_jobs)
                    logger.info(f"Initial load completed and timestamp updated")
                else:
                    logger.info(f"No jobs found in initial load from last 3 days")
                    # Still update timestamp
                    db.set_metadata("last_parsed_timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            except Exception as e:
                # Log parsing error to database
                error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.error(f"Initial load error: {str(e)}")
                db.insert_parser_error(error_time, str(e), f"Error parsing {log_file_path}")

                # Still update timestamp to avoid retrying same logs on every run
                db.set_metadata("last_parsed_timestamp", error_time)