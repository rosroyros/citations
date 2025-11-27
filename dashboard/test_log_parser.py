import unittest
from datetime import datetime
import sys
import os

# Add the dashboard directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from log_parser import (
    extract_timestamp,
    extract_creation,
    extract_completion,
    extract_duration,
    extract_citation_count,
    extract_token_usage,
    extract_failure,
    parse_job_events,
    find_job_by_timestamp,
    parse_metrics,
    parse_logs
)


class TestLogParser(unittest.TestCase):
    def test_extract_timestamp_valid_line(self):
        """Test extracting timestamp from a valid log line."""
        log_line = "2025-11-04 21:42:48 - citation_validator - INFO - app.py:258 - Validation request received for style: apa7"
        timestamp = extract_timestamp(log_line)
        expected = datetime(2025, 11, 4, 21, 42, 48)
        self.assertEqual(timestamp, expected)

    def test_extract_timestamp_different_date(self):
        """Test extracting timestamp from a different date."""
        log_line = "2025-11-27 07:57:46 - citation_validator - INFO - app.py:590 - Creating async job abc-123 for free user"
        timestamp = extract_timestamp(log_line)
        expected = datetime(2025, 11, 27, 7, 57, 46)
        self.assertEqual(timestamp, expected)

    def test_extract_timestamp_invalid_line(self):
        """Test extracting timestamp from an invalid log line returns None."""
        log_line = "This is not a valid log line"
        timestamp = extract_timestamp(log_line)
        self.assertIsNone(timestamp)

    def test_extract_timestamp_empty_line(self):
        """Test extracting timestamp from an empty line returns None."""
        log_line = ""
        timestamp = extract_timestamp(log_line)
        self.assertIsNone(timestamp)

    def test_extract_creation_free_user(self):
        """Test extracting job creation info for free user."""
        log_line = "2025-11-27 07:57:46 - citation_validator - INFO - app.py:590 - Creating async job abc-123 for free user"
        job_id, timestamp, user_type = extract_creation(log_line)
        self.assertEqual(job_id, "abc-123")
        self.assertEqual(timestamp, datetime(2025, 11, 27, 7, 57, 46))
        self.assertEqual(user_type, "free")

    def test_extract_creation_paid_user(self):
        """Test extracting job creation info for paid user."""
        log_line = "2025-11-27 08:15:22 - citation_validator - INFO - app.py:590 - Creating async job def-456 for paid user"
        job_id, timestamp, user_type = extract_creation(log_line)
        self.assertEqual(job_id, "def-456")
        self.assertEqual(timestamp, datetime(2025, 11, 27, 8, 15, 22))
        self.assertEqual(user_type, "paid")

    def test_extract_creation_invalid_line(self):
        """Test extracting job creation info from invalid line returns None."""
        log_line = "This is not a job creation line"
        result = extract_creation(log_line)
        self.assertIsNone(result)

    def test_extract_creation_empty_line(self):
        """Test extracting job creation info from empty line returns None."""
        log_line = ""
        result = extract_creation(log_line)
        self.assertIsNone(result)

    def test_extract_completion_valid(self):
        """Test extracting job completion info."""
        log_line = "2025-11-27 07:58:33 - citation_validator - INFO - app.py:539 - Job abc-123: Completed successfully"
        job_id, timestamp = extract_completion(log_line)
        self.assertEqual(job_id, "abc-123")
        self.assertEqual(timestamp, datetime(2025, 11, 27, 7, 58, 33))

    def test_extract_completion_invalid_line(self):
        """Test extracting job completion info from invalid line returns None."""
        log_line = "This is not a job completion line"
        result = extract_completion(log_line)
        self.assertIsNone(result)

    def test_extract_duration_valid(self):
        """Test extracting LLM duration."""
        log_line = "2025-11-27 07:58:33 - openai_provider - INFO - openai_provider.py:119 - OpenAI API call completed in 47.0s"
        duration = extract_duration(log_line)
        self.assertEqual(duration, 47.0)

    def test_extract_duration_invalid_line(self):
        """Test extracting duration from invalid line returns None."""
        log_line = "This is not a duration line"
        result = extract_duration(log_line)
        self.assertIsNone(result)

    def test_extract_citation_count_valid(self):
        """Test extracting citation count."""
        log_line = "2025-11-27 07:58:33 - citation_validator - INFO - app.py:539 - Found 1 citation result(s)"
        count = extract_citation_count(log_line)
        self.assertEqual(count, 1)

    def test_extract_citation_count_multiple(self):
        """Test extracting multiple citation count."""
        log_line = "2025-11-27 07:58:33 - citation_validator - INFO - app.py:539 - Found 5 citation results"
        count = extract_citation_count(log_line)
        self.assertEqual(count, 5)

    def test_extract_citation_count_invalid_line(self):
        """Test extracting citation count from invalid line returns None."""
        log_line = "This is not a citation count line"
        result = extract_citation_count(log_line)
        self.assertIsNone(result)

    def test_parse_job_events_complete_flow(self):
        """Test parsing job events (Pass 1) with complete flow."""
        log_lines = [
            "2025-11-27 07:57:46 - citation_validator - INFO - app.py:590 - Creating async job abc-123 for free user",
            "2025-11-27 07:58:33 - citation_validator - INFO - app.py:539 - Job abc-123: Completed successfully"
        ]
        jobs = parse_job_events(log_lines)
        self.assertEqual(len(jobs), 1)
        job = jobs["abc-123"]
        self.assertEqual(job["job_id"], "abc-123")
        self.assertEqual(job["user_type"], "free")
        self.assertEqual(job["status"], "completed")

    def test_find_job_by_timestamp_exact_match(self):
        """Test finding job by timestamp with exact match."""
        jobs = {
            "abc-123": {
                "created_at": datetime(2025, 11, 27, 7, 57, 46),
                "completed_at": datetime(2025, 11, 27, 7, 58, 33),
                "status": "completed"
            }
        }
        target_timestamp = datetime(2025, 11, 27, 7, 57, 50)
        job = find_job_by_timestamp(jobs, target_timestamp)
        self.assertEqual(job["job_id"], "abc-123")

    def test_parse_metrics_duration_and_citations(self):
        """Test parsing metrics (Pass 2) with duration and citations."""
        log_lines = [
            "2025-11-27 07:58:33 - openai_provider - INFO - openai_provider.py:119 - OpenAI API call completed in 47.0s",
            "2025-11-27 07:58:33 - citation_validator - INFO - app.py:539 - Found 1 citation result(s)"
        ]
        jobs = {
            "abc-123": {
                "created_at": datetime(2025, 11, 27, 7, 57, 46),
                "completed_at": datetime(2025, 11, 27, 7, 58, 33),
                "status": "completed"
            }
        }
        updated_jobs = parse_metrics(log_lines, jobs)
        job = updated_jobs["abc-123"]
        self.assertEqual(job["duration_seconds"], 47.0)
        self.assertEqual(job["citation_count"], 1)

    def test_integration_with_real_log_file(self):
        """Test parsing with real log file."""
        # Test with sample log file from project
        log_file_path = "../logs/app.log"

        # Parse last 24 hours of logs
        from datetime import datetime, timedelta
        start_time = datetime.now() - timedelta(days=1)

        try:
            jobs = parse_logs(log_file_path, start_timestamp=start_time)

            # Basic validation
            self.assertIsInstance(jobs, list)

            # If there are jobs, check they have expected fields
            for job in jobs:
                self.assertIn("job_id", job)
                self.assertIn("created_at", job)
                self.assertIn("user_type", job)
                self.assertIn("status", job)

                # Check timestamp format
                created_at = job["created_at"]
                self.assertTrue(created_at.endswith("Z"))

                # Verify it's a valid ISO timestamp
                from datetime import datetime
                parsed_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                self.assertIsInstance(parsed_time, datetime)

        except FileNotFoundError:
            # Log file doesn't exist in test environment, skip test
            self.skipTest("Log file not found in test environment")

    def test_extract_token_usage_valid(self):
        line = "2025-11-27 07:58:33 - openai_provider - INFO - openai_provider.py:119 - Token usage: 1025 prompt + 997 completion = 2022 total"
        result = extract_token_usage(line)
        self.assertIsNotNone(result)
        self.assertEqual(result["prompt"], 1025)
        self.assertEqual(result["completion"], 997)
        self.assertEqual(result["total"], 2022)

    def test_extract_token_usage_invalid_line(self):
        line = "2025-11-27 07:58:33 - openai_provider - INFO - openai_provider.py:119 - No token usage here"
        result = extract_token_usage(line)
        self.assertIsNone(result)

    def test_extract_failure_valid(self):
        line = "2025-11-27 07:58:45 - citation_validator - ERROR - app.py:542 - Job abc-123: Failed with error: OpenAI API timeout"
        result = extract_failure(line)
        self.assertIsNotNone(result)
        job_id, timestamp, error_message = result
        self.assertEqual(job_id, "abc-123")
        self.assertEqual(error_message, "OpenAI API timeout")
        self.assertIsNotNone(timestamp)

    def test_extract_failure_invalid_line(self):
        line = "2025-11-27 07:58:45 - citation_validator - INFO - app.py:542 - Job abc-123: Completed successfully"
        result = extract_failure(line)
        self.assertIsNone(result)

    def test_parse_metrics_includes_token_usage(self):
        log_lines = [
            "2025-11-27 07:57:46 - citation_validator - INFO - app.py:590 - Creating async job abc-123 for free user",
            "2025-11-27 07:58:33 - openai_provider - INFO - openai_provider.py:119 - Token usage: 1025 prompt + 997 completion = 2022 total",
            "2025-11-27 07:58:33 - openai_provider - INFO - openai_provider.py:101 - OpenAI API call completed in 47.0s",
            "2025-11-27 07:58:33 - openai_provider - INFO - openai_provider.py:119 - Found 1 citation result(s)",
            "2025-11-27 07:58:33 - citation_validator - INFO - app.py:539 - Job abc-123: Completed successfully"
        ]

        # First pass to create jobs
        jobs = parse_job_events(log_lines)

        # Second pass to match metrics
        jobs = parse_metrics(log_lines, jobs)

        job = jobs["abc-123"]
        self.assertEqual(job["token_usage_prompt"], 1025)
        self.assertEqual(job["token_usage_completion"], 997)
        self.assertEqual(job["token_usage_total"], 2022)
        self.assertEqual(job["duration_seconds"], 47.0)
        self.assertEqual(job["citation_count"], 1)


if __name__ == '__main__':
    unittest.main()