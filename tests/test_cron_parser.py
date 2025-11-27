#!/usr/bin/env python3
"""
Test cron job functionality for incremental log parsing
"""
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import pytest

from dashboard.database import get_database
from dashboard.cron_parser import CronLogParser


class TestCronLogParser:
    """Test suite for cron-based incremental log parsing"""

    def test_incremental_parsing_reads_from_last_timestamp(self):
        """Test that incremental parsing reads from last_parsed_timestamp metadata"""
        # Create temporary log file with old and new entries
        old_timestamp = datetime.now() - timedelta(days=1)
        new_timestamp = datetime.now() - timedelta(minutes=10)

        log_content = f"""{old_timestamp.strftime('%Y-%m-%d %H:%M:%S')} - citation_validator - INFO - app.py:590 - Creating async job abc123 for free user
{old_timestamp.strftime('%Y-%m-%d %H:%M:%S')} - citation_validator - INFO - app.py:539 - Job abc123: Completed successfully
{new_timestamp.strftime('%Y-%m-%d %H:%M:%S')} - citation_validator - INFO - app.py:590 - Creating async job def456 for paid user
{new_timestamp.strftime('%Y-%m-%d %H:%M:%S')} - citation_validator - INFO - app.py:539 - Job def456: Completed successfully
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write(log_content)
            log_file_path = f.name

        try:
            # Setup database and metadata
            with get_database() as db:
                # Set last parsed timestamp to between old and new entries
                last_parsed = old_timestamp + timedelta(hours=12)
                db.set_metadata("last_parsed_timestamp", last_parsed.isoformat())

                # Create parser and run incremental parse
                parser = CronLogParser(db_path=db.db_path)
                parser.parse_incremental(log_file_path)

                # Should only find and insert the new job
                new_job = db.get_validation("def456")
                old_job = db.get_validation("abc123")

                assert new_job is not None, "New job should be parsed and inserted"
                assert new_job["user_type"] == "paid"
                assert old_job is None, "Old job should not be parsed"

        finally:
            os.unlink(log_file_path)

    def test_initial_load_parses_last_3_days(self):
        """Test that initial load parses all entries from last 3 days"""
        # Create log file with entries from different times
        now = datetime.now()
        four_days_ago = now - timedelta(days=4)
        two_days_ago = now - timedelta(days=2)
        one_day_ago = now - timedelta(days=1)

        log_content = f"""{four_days_ago.strftime('%Y-%m-%d %H:%M:%S')} - citation_validator - INFO - app.py:590 - Creating async job abc123789 for free user
{two_days_ago.strftime('%Y-%m-%d %H:%M:%S')} - citation_validator - INFO - app.py:590 - Creating async job def123456 for paid user
{one_day_ago.strftime('%Y-%m-%d %H:%M:%S')} - citation_validator - INFO - app.py:590 - Creating async job abc789012 for free user
{two_days_ago.strftime('%Y-%m-%d %H:%M:%S')} - citation_validator - INFO - app.py:539 - Job def123456: Completed successfully
{one_day_ago.strftime('%Y-%m-%d %H:%M:%S')} - citation_validator - INFO - app.py:539 - Job abc789012: Completed successfully
{four_days_ago.strftime('%Y-%m-%d %H:%M:%S')} - citation_validator - INFO - app.py:539 - Job abc123789: Completed successfully
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write(log_content)
            log_file_path = f.name

        try:
            with get_database() as db:
                parser = CronLogParser(db_path=db.db_path)

                # Run initial load (no previous timestamp)
                parser.parse_initial_load(log_file_path)

                # Should only find jobs from last 3 days
                recent_job_1 = db.get_validation("def123456")
                recent_job_2 = db.get_validation("abc789012")
                too_old_job = db.get_validation("abc123789")

                assert recent_job_1 is not None, "Recent job should be parsed"
                assert recent_job_2 is not None, "Recent job should be parsed"
                assert too_old_job is None, "Job older than 3 days should not be parsed"

        finally:
            os.unlink(log_file_path)

    def test_updates_last_parsed_timestamp(self):
        """Test that parser updates last_parsed_timestamp after parsing"""
        recent_timestamp = datetime.now() - timedelta(minutes=5)
        log_content = f"""{recent_timestamp.strftime('%Y-%m-%d %H:%M:%S')} - citation_validator - INFO - app.py:590 - Creating async job abc999999 for free user
{recent_timestamp.strftime('%Y-%m-%d %H:%M:%S')} - citation_validator - INFO - app.py:539 - Job abc999999: Completed successfully
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write(log_content)
            log_file_path = f.name

        try:
            with get_database() as db:
                parser = CronLogParser(db_path=db.db_path)

                # Run incremental parsing
                parser.parse_incremental(log_file_path)

                # Check that job was parsed and timestamp was updated
                job = db.get_validation("abc999999")
                assert job is not None, "Job should be parsed and inserted"

                updated_timestamp_str = db.get_metadata("last_parsed_timestamp")
                updated_timestamp = datetime.fromisoformat(updated_timestamp_str)

                # Should be close to the log entry timestamp (allow small buffer)
                time_diff = abs((updated_timestamp - recent_timestamp).total_seconds())
                assert time_diff < 301, f"Timestamp should be updated to recent entry, got {updated_timestamp}"

        finally:
            os.unlink(log_file_path)

    def test_handles_empty_log_file(self):
        """Test that parser gracefully handles empty log files"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("")
            log_file_path = f.name

        try:
            with get_database() as db:
                parser = CronLogParser(db_path=db.db_path)

                # Should not raise exception
                parser.parse_incremental(log_file_path)
                parser.parse_initial_load(log_file_path)

        finally:
            os.unlink(log_file_path)