#!/usr/bin/env python3
"""
Cron-based incremental log parser
Handles incremental log parsing with metadata tracking
"""
from datetime import datetime, timedelta
from typing import List, Dict

from dashboard.database import DatabaseManager
from dashboard.log_parser import parse_logs


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
                job_time = datetime.fromisoformat(job["created_at"].replace("Z", "+00:00"))
                if latest_timestamp is None or job_time > latest_timestamp:
                    latest_timestamp = job_time

            if latest_timestamp:
                db.set_metadata("last_parsed_timestamp", latest_timestamp.isoformat())
            else:
                # Fallback to now if no jobs found
                now = datetime.now()
                db.set_metadata("last_parsed_timestamp", now.isoformat())
        else:
            # No jobs parsed, update to now
            now = datetime.now()
            db.set_metadata("last_parsed_timestamp", now.isoformat())

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
                    last_timestamp = datetime.fromisoformat(last_timestamp_str)
                except ValueError:
                    # Invalid timestamp, fallback to initial load
                    last_timestamp = None

            if not last_timestamp:
                # No previous timestamp, do initial load
                self.parse_initial_load(log_file_path)
                return

            # Parse logs from last timestamp
            parsed_jobs = parse_logs(log_file_path, start_timestamp=last_timestamp)

            # Insert to database
            self._insert_parsed_jobs(db, parsed_jobs)

            # Update last parsed timestamp
            self._update_timestamp_metadata(db, parsed_jobs)

    def parse_initial_load(self, log_file_path: str):
        """
        Initial load: parse logs from last 3 days

        Args:
            log_file_path: Path to log file to parse
        """
        with DatabaseManager(self.db_path) as db:
            # Parse logs from 3 days ago
            three_days_ago = datetime.now() - timedelta(days=3)
            parsed_jobs = parse_logs(log_file_path, start_timestamp=three_days_ago)

            # Insert to database
            self._insert_parsed_jobs(db, parsed_jobs)

            # Update last parsed timestamp
            self._update_timestamp_metadata(db, parsed_jobs)