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
    extract_duration_with_job,
    extract_citation_count,
    extract_citation_count_with_job,
    extract_token_usage,
    extract_failure,
    extract_citations_preview,
    extract_full_citations,
    extract_user_ids,
    extract_provider_selection,
    extract_correction_event,
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

    def test_extract_citation_count_with_job_valid(self):
        """Test extracting citation count with job ID."""
        log_line = "2025-11-27 07:58:33 - INFO - Job abc-123-def: Found 5 citation result(s)"
        result = extract_citation_count_with_job(log_line)
        self.assertIsNotNone(result)
        job_id, count = result
        self.assertEqual(job_id, "abc-123-def")
        self.assertEqual(count, 5)

    def test_extract_citation_count_with_job_uuid(self):
        """Test extracting citation count with UUID job ID."""
        log_line = "2025-11-27 07:58:33 - INFO - Job 12345678-1234-1234-1234-123456789abc: Found 100 citation results"
        result = extract_citation_count_with_job(log_line)
        self.assertIsNotNone(result)
        job_id, count = result
        self.assertEqual(job_id, "12345678-1234-1234-1234-123456789abc")
        self.assertEqual(count, 100)

    def test_extract_citation_count_with_job_invalid_line(self):
        """Test extracting citation count with job from invalid line returns None."""
        log_line = "Found 5 citation results"  # No job ID prefix
        result = extract_citation_count_with_job(log_line)
        self.assertIsNone(result)

    def test_extract_duration_with_job_valid(self):
        """Test extracting duration with job ID."""
        log_line = "2025-12-24 10:00:00 - INFO - Job abc-123-def: LLM API completed in 15.5s"
        result = extract_duration_with_job(log_line)
        self.assertIsNotNone(result)
        job_id, duration = result
        self.assertEqual(job_id, "abc-123-def")
        self.assertEqual(duration, 15.5)

    def test_extract_duration_with_job_uuid(self):
        """Test extracting duration with UUID job ID."""
        log_line = "2025-12-24 10:00:00 - INFO - Job 12345678-1234-1234-1234-123456789abc: LLM API completed in 47.123s"
        result = extract_duration_with_job(log_line)
        self.assertIsNotNone(result)
        job_id, duration = result
        self.assertEqual(job_id, "12345678-1234-1234-1234-123456789abc")
        self.assertEqual(duration, 47.123)

    def test_extract_duration_with_job_invalid_line(self):
        """Test extracting duration with job from invalid line returns None."""
        log_line = "OpenAI API call completed in 15.5s"  # Old format without job ID
        result = extract_duration_with_job(log_line)
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
        """Test parsing metrics (Pass 2) with duration and citations (citation count via Pass 1)."""
        log_lines = [
            "2025-11-27 07:57:46 - citation_validator - INFO - Creating async job abc-123 for free user",
            "2025-11-27 07:58:33 - openai_provider - INFO - openai_provider.py:119 - OpenAI API call completed in 47.0s",
            "2025-11-27 07:58:33 - citation_validator - INFO - Job abc-123: Found 1 citation result(s)",
            "2025-11-27 07:58:33 - citation_validator - INFO - Job abc-123: Completed successfully"
        ]
        # First pass to create jobs and extract citation count
        jobs = parse_job_events(log_lines)
        # Second pass to match other metrics (duration, tokens)
        jobs = parse_metrics(log_lines, jobs)
        
        job = jobs["abc-123"]
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

    def test_extract_token_usage_valid_input_output(self):
        """Test extraction of token usage with input/output format."""
        line = "2025-11-27 07:58:33 - openai_provider - INFO - openai_provider.py:119 - Token usage: 1025 input + 997 output = 2022 total"
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
            "2025-11-27 07:58:33 - citation_validator - INFO - Job abc-123: Found 1 citation result(s)",
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

    def test_extract_citations_preview_basic(self):
        """Test extracting citation preview from log line."""
        log_line = "2025-11-04 21:42:48 - citation_validator - DEBUG - app.py:275 - Citation text preview: Adli, A. (2013). Syntactic variation in French Wh-questions: A quantitative study from the angle of Bourdieu's sociocultural theory. _Linguistics_, _51_(3), 473-515."
        result = extract_citations_preview(log_line)
        expected = "Adli, A. (2013). Syntactic variation in French Wh-questions: A quantitative study from the angle of Bourdieu&#x27;s sociocultural theory. _Linguistics_, _51_(3), 473-515."
        self.assertIsNotNone(result)
        citations_text, was_truncated = result
        self.assertEqual(citations_text, expected)
        self.assertFalse(was_truncated)

    def test_extract_citations_preview_with_ellipsis(self):
        """Test extracting citation preview that ends with ellipsis."""
        log_line = "2025-11-04 21:42:48 - citation_validator - DEBUG - app.py:275 - Citation text preview: Adli, A. (2013). Syntactic variation in French Wh-questions. Agarwal, D., Naaman, M., & Vashis..."
        result = extract_citations_preview(log_line)
        expected = "Adli, A. (2013). Syntactic variation in French Wh-questions. Agarwal, D., Naaman, M., & Vashis"
        self.assertIsNotNone(result)
        citations_text, was_truncated = result
        self.assertEqual(citations_text, expected)
        self.assertFalse(was_truncated)

    def test_extract_citations_preview_no_match(self):
        """Test extracting citation preview from line without pattern."""
        log_line = "2025-11-04 21:42:48 - citation_validator - INFO - app.py:539 - Job abc-123: Completed successfully"
        result = extract_citations_preview(log_line)
        self.assertIsNone(result)

    def test_extract_citations_preview_security_xss(self):
        """Test that XSS content is sanitized in citation preview."""
        log_line = "2025-11-04 21:42:48 - citation_validator - DEBUG - app.py:275 - Citation text preview: <script>alert('xss')</script>Adli, A. (2013). <b>Bold text</b>"
        result = extract_citations_preview(log_line)
        self.assertIsNotNone(result)
        citations_text, was_truncated = result
        # Check HTML escaping and script removal
        self.assertNotIn("<script>", citations_text)
        self.assertNotIn("</script>", citations_text)
        self.assertIn("&lt;b&gt;Bold text&lt;/b&gt;", citations_text)

    def test_extract_citations_preview_sql_injection(self):
        """Test that SQL injection patterns are neutralized."""
        log_line = "2025-11-04 21:42:48 - citation_validator - DEBUG - app.py:275 - Citation text preview: Adli, A. (2013). ' OR '1'='1; DROP TABLE users; --"
        result = extract_citations_preview(log_line)
        self.assertIsNotNone(result)
        citations_text, was_truncated = result
        # Check SQL injection patterns are removed/neutralized
        self.assertNotIn("' OR '1'='1", citations_text)
        self.assertNotIn("DROP TABLE", citations_text)

    def test_extract_full_citations_basic(self):
        """Test extracting full citation from multiline pattern."""
        log_lines = [
            "2025-11-04 21:43:04 - openai_provider - INFO - openai_provider.py:116 - Parsing LLM response into structured format",
            "ORIGINAL:",
            "Adli, A. (2013). Syntactic variation in French Wh-questions: A quantitative study from the angle of Bourdieu's sociocultural theory. _Linguistics_, _51_(3), 473-515.",
            "Agarwal, D., Naaman, M., & Vashistha, V. (2013). Content credibility on Twitter. _WWW '13_: 549-558.",
            "2025-11-04 21:43:04 - openai_provider - INFO - openai_provider.py:79 - Parsed response in 0.001s"
        ]
        result = extract_full_citations(log_lines, 1)  # Start from line index 1 (ORIGINAL: line)
        expected = "Adli, A. (2013). Syntactic variation in French Wh-questions: A quantitative study from the angle of Bourdieu&#x27;s sociocultural theory. _Linguistics_, _51_(3), 473-515.\nAgarwal, D., Naaman, M., & Vashistha, V. (2013). Content credibility on Twitter. _WWW &#x27;13_: 549-558."
        self.assertIsNotNone(result)
        citations_text, was_truncated = result
        self.assertEqual(citations_text, expected)
        self.assertFalse(was_truncated)

    def test_extract_full_citations_single_line(self):
        """Test extracting full citation that spans only one line."""
        log_lines = [
            "2025-11-04 21:43:04 - openai_provider - INFO - openai_provider.py:116 - Parsing LLM response into structured format",
            "ORIGINAL:",
            "Adli, A. (2013). Syntactic variation in French Wh-questions: A quantitative study from the angle of Bourdieu's sociocultural theory. _Linguistics_, _51_(3), 473-515.",
            "2025-11-04 21:43:04 - openai_provider - INFO - openai_provider.py:79 - Parsed response in 0.001s"
        ]
        result = extract_full_citations(log_lines, 1)
        expected = "Adli, A. (2013). Syntactic variation in French Wh-questions: A quantitative study from the angle of Bourdieu&#x27;s sociocultural theory. _Linguistics_, _51_(3), 473-515."
        self.assertIsNotNone(result)
        citations_text, was_truncated = result
        self.assertEqual(citations_text, expected)
        self.assertFalse(was_truncated)

    def test_extract_full_citations_no_original(self):
        """Test extracting full citations when no ORIGINAL: pattern found."""
        log_lines = [
            "2025-11-04 21:43:04 - openai_provider - INFO - openai_provider.py:116 - Parsing LLM response",
            "2025-11-04 21:43:04 - openai_provider - INFO - openai_provider.py:79 - Parsed response in 0.001s"
        ]
        result = extract_full_citations(log_lines, 0)
        self.assertIsNone(result)

    def test_extract_full_citations_with_security_content(self):
        """Test extracting full citations with malicious content."""
        log_lines = [
            "2025-11-04 21:43:04 - openai_provider - INFO - openai_provider.py:116 - Parsing LLM response",
            "ORIGINAL:",
            "<script>alert('xss')</script>Adli, A. (2013). <b>Bold text</b> ' OR '1'='1; DROP TABLE users;",
            "2025-11-04 21:43:04 - openai_provider - INFO - openai_provider.py:79 - Parsed response"
        ]
        result = extract_full_citations(log_lines, 1)
        self.assertIsNotNone(result)
        citations_text, was_truncated = result
        # Check security sanitization
        self.assertNotIn("<script>", citations_text)
        self.assertNotIn("</script>", citations_text)
        self.assertNotIn("' OR '1'='1", citations_text)
        self.assertNotIn("DROP TABLE", citations_text)
        self.assertIn("&lt;b&gt;Bold text&lt;/b&gt;", citations_text)

    def test_extract_full_citations_length_truncation(self):
        """Test that long citations are truncated properly."""
        # Create very long citation content
        long_citation = "A" * 15000  # Much longer than 10000 limit
        log_lines = [
            "2025-11-04 21:43:04 - openai_provider - INFO - openai_provider.py:116 - Parsing LLM response",
            "ORIGINAL:",
            long_citation,
            "2025-11-04 21:43:04 - openai_provider - INFO - openai_provider.py:79 - Parsed response"
        ]
        result = extract_full_citations(log_lines, 1)
        self.assertIsNotNone(result)
        citations_text, was_truncated = result
        self.assertTrue(was_truncated)
        self.assertTrue(len(citations_text) <= 10000 + len('[TRUNCATED]'))
        self.assertIn('[TRUNCATED]', citations_text)

    def test_integration_citations_with_parse_logs(self):
        """Test integration of citation extraction with complete log parsing workflow."""
        log_lines = [
            "2025-11-27 07:57:46 - citation_validator - INFO - app.py:590 - Creating async job abc-123 for free user",
            "2025-11-27 07:57:46 - citation_validator - DEBUG - app.py:275 - Citation text preview: Adli, A. (2013). Syntactic variation in French Wh-questions. Agarwal, D., Naaman, M., & Vashis...",
            "2025-11-27 07:58:33 - openai_provider - INFO - openai_provider.py:43 - Starting validation for 1310 characters of citation text",
            "2025-11-27 07:58:33 - openai_provider - INFO - openai_provider.py:116 - Parsing LLM response into structured format",
            "ORIGINAL:",
            "Adli, A. (2013). Syntactic variation in French Wh-questions: A quantitative study from the angle of Bourdieu's sociocultural theory. _Linguistics_, _51_(3), 473-515.",
            "Agarwal, D., Naaman, M., & Vashistha, V. (2013). Content credibility on Twitter. _WWW '13_: 549-558.",
            "2025-11-27 07:58:33 - openai_provider - INFO - openai_provider.py:79 - Parsed response in 0.001s",
            "2025-11-27 07:58:33 - openai_provider - INFO - openai_provider.py:101 - OpenAI API call completed in 47.0s",
            "2025-11-27 07:58:33 - citation_validator - INFO - Job abc-123: Found 2 citation result(s)",
            "2025-11-27 07:58:33 - openai_provider - INFO - openai_provider.py:119 - Token usage: 1025 prompt + 997 completion = 2022 total",
            "2025-11-27 07:58:33 - citation_validator - INFO - app.py:539 - Job abc-123: Completed successfully"
        ]

        # Create temporary log file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write('\n'.join(log_lines))
            temp_log_path = f.name

        try:
            # Test complete parsing workflow
            jobs = parse_logs(temp_log_path)

            # Should have parsed 1 job
            self.assertEqual(len(jobs), 1)
            job = jobs[0]

            # Check basic job info
            self.assertEqual(job["job_id"], "abc-123")
            self.assertEqual(job["user_type"], "free")
            self.assertEqual(job["status"], "completed")

            # Check citation preview extraction
            self.assertIsNotNone(job["citations_preview"])
            self.assertIn("Syntactic variation in French Wh-questions", job["citations_preview"])
            self.assertFalse(job["citations_preview_truncated"])

            # Check full citations extraction
            self.assertIsNotNone(job["citations_full"])
            self.assertIn("Adli, A. (2013)", job["citations_full"])
            self.assertIn("Agarwal, D., Naaman, M.", job["citations_full"])
            self.assertFalse(job["citations_full_truncated"])

            # Check other metrics still work
            self.assertEqual(job["duration_seconds"], 47.0)
            self.assertEqual(job["citation_count"], 2)
            self.assertEqual(job["token_usage_prompt"], 1025)
            self.assertEqual(job["token_usage_completion"], 997)
            self.assertEqual(job["token_usage_total"], 2022)

        finally:
            # Clean up temp file
            import os
            os.unlink(temp_log_path)

    # ==================== USER ID EXTRACTION TESTS ====================

    def test_extract_user_ids_paid_user(self):
        """Test extracting user IDs from a paid user validation request."""
        log_line = "2025-12-03 10:15:00 - citation_validator - INFO - Validation request - user_type=paid, paid_user_id=abc12345, free_user_id=N/A, style=apa7"
        paid_id, free_id = extract_user_ids(log_line)

        self.assertEqual(paid_id, "abc12345")
        self.assertIsNone(free_id)

    def test_extract_user_ids_free_user(self):
        """Test extracting user IDs from a free user validation request."""
        log_line = "2025-12-03 10:16:00 - citation_validator - INFO - Validation request - user_type=free, paid_user_id=N/A, free_user_id=550e8400-e29b-41d4-a716-446655440000, style=mla9"
        paid_id, free_id = extract_user_ids(log_line)

        self.assertIsNone(paid_id)
        self.assertEqual(free_id, "550e8400-e29b-41d4-a716-446655440000")

    def test_extract_user_ids_anonymous_user(self):
        """Test extracting user IDs from an anonymous user validation request."""
        log_line = "2025-12-03 10:17:00 - citation_validator - INFO - Validation request - user_type=free, paid_user_id=N/A, free_user_id=N/A, style=chicago"
        paid_id, free_id = extract_user_ids(log_line)

        self.assertIsNone(paid_id)
        self.assertIsNone(free_id)

    def test_extract_user_ids_old_log_format(self):
        """Test extracting user IDs from an old log line without user ID information."""
        log_line = "2025-12-01 10:00:00 - citation_validator - INFO - Validation request received for style: apa7"
        paid_id, free_id = extract_user_ids(log_line)

        self.assertIsNone(paid_id)
        self.assertIsNone(free_id)

    def test_extract_user_ids_no_validation_request(self):
        """Test extracting user IDs from a log line that's not a validation request."""
        log_line = "2025-12-03 10:15:00 - citation_validator - INFO - Some other log message"
        paid_id, free_id = extract_user_ids(log_line)

        self.assertIsNone(paid_id)
        self.assertIsNone(free_id)

    def test_extract_user_ids_empty_line(self):
        """Test extracting user IDs from an empty line."""
        paid_id, free_id = extract_user_ids("")

        self.assertIsNone(paid_id)
        self.assertIsNone(free_id)

    def test_extract_user_ids_malformed_user_type(self):
        """Test extracting user IDs from a log line with malformed user type."""
        log_line = "2025-12-03 10:15:00 - citation_validator - INFO - Validation request - user_type=invalid, paid_user_id=abc123, free_user_id=N/A"
        paid_id, free_id = extract_user_ids(log_line)

        # Should still extract the IDs even if user_type is unusual
        self.assertEqual(paid_id, "abc123")
        self.assertIsNone(free_id)

    def test_extract_user_ids_partial_match(self):
        """Test extracting user IDs when only partial pattern matches."""
        log_line = "2025-12-03 10:15:00 - some message about user_type=free but no full pattern"
        paid_id, free_id = extract_user_ids(log_line)

        self.assertIsNone(paid_id)
        self.assertIsNone(free_id)

    def test_parse_job_events_with_user_ids(self):
        """Test that parse_job_events correctly associates user IDs with jobs."""
        log_lines = [
            "2025-12-03 10:15:00 Creating async job abc-123-def for paid user",
            "2025-12-03 10:15:01 - citation_validator - INFO - Validation request - user_type=paid, paid_user_id=abc12345, free_user_id=N/A, style=apa7",
            "2025-12-03 10:16:00 Creating async job def-456-abc for free user",
            "2025-12-03 10:16:01 - citation_validator - INFO - Validation request - user_type=free, paid_user_id=N/A, free_user_id=550e8400-e29b-41d4-a716-446655440000, style=mla9",
            "2025-12-03 10:17:00 Creating async job bcd-789-ef0 for free user",
            "2025-12-03 10:17:01 - citation_validator - INFO - Validation request - user_type=free, paid_user_id=N/A, free_user_id=N/A, style=chicago"
        ]

        jobs = parse_job_events(log_lines)

        # Check that we have 3 jobs
        self.assertEqual(len(jobs), 3)

        # Check paid user job
        paid_job = jobs.get("abc-123-def")
        self.assertIsNotNone(paid_job)
        self.assertEqual(paid_job["paid_user_id"], "abc12345")
        self.assertIsNone(paid_job["free_user_id"])
        self.assertEqual(paid_job["user_type"], "paid")

        # Check free user job
        free_job = jobs.get("def-456-abc")
        self.assertIsNotNone(free_job)
        self.assertIsNone(free_job["paid_user_id"])
        self.assertEqual(free_job["free_user_id"], "550e8400-e29b-41d4-a716-446655440000")
        self.assertEqual(free_job["user_type"], "free")

        # Check anonymous user job (no user IDs)
        anonymous_job = jobs.get("bcd-789-ef0")
        self.assertIsNotNone(anonymous_job)
        self.assertIsNone(anonymous_job["paid_user_id"])
        self.assertIsNone(anonymous_job["free_user_id"])
        self.assertEqual(anonymous_job["user_type"], "free")

    def test_parse_job_events_user_id_timeout(self):
        """Test that user ID association times out after 5 minutes."""
        log_lines = [
            "2025-12-03 10:15:00 Creating async job cde-234-f5a for paid user",
            # User ID log is 6 minutes later - should not associate
            "2025-12-03 10:21:00 - citation_validator - INFO - Validation request - user_type=paid, paid_user_id=abc12345, free_user_id=N/A, style=apa7"
        ]

        jobs = parse_job_events(log_lines)

        # Job should exist but without user ID (due to timeout)
        job = jobs.get("cde-234-f5a")
        self.assertIsNotNone(job)
        self.assertIsNone(job["paid_user_id"])
        self.assertIsNone(job["free_user_id"])

    def test_parse_job_events_multiple_jobs_same_timestamp(self):
        """Test user ID association when multiple jobs exist with similar timestamps."""
        log_lines = [
            "2025-12-03 10:15:00 Creating async job abc-123-def for paid user",
            "2025-12-03 10:15:01 Creating async job def-456-abc for paid user",
            "2025-12-03 10:15:02 - citation_validator - INFO - Validation request - user_type=paid, paid_user_id=abc12345, free_user_id=N/A, style=apa7",
            "2025-12-03 10:15:03 - citation_validator - INFO - Validation request - user_type=paid, paid_user_id=def67890, free_user_id=N/A, style=mla9"
        ]

        jobs = parse_job_events(log_lines)

        # Both jobs should get their respective user IDs
        job1 = jobs.get("abc-123-def")
        job2 = jobs.get("def-456-abc")

        self.assertIsNotNone(job1)
        self.assertIsNotNone(job2)
        self.assertEqual(job1["paid_user_id"], "abc12345")
        self.assertEqual(job2["paid_user_id"], "def67890")

    def test_parse_job_events_user_id_override(self):
        """Test that user IDs are not overwritten once set."""
        log_lines = [
            "2025-12-03 10:15:00 Creating async job eff-456-78a for paid user",
            "2025-12-03 10:15:01 - citation_validator - INFO - Validation request - user_type=paid, paid_user_id=abc12345, free_user_id=N/A, style=apa7",
            # This should not overwrite the first user ID
            "2025-12-03 10:15:02 - citation_validator - INFO - Validation request - user_type=paid, paid_user_id=xyz98765, free_user_id=N/A, style=mla9"
        ]

        jobs = parse_job_events(log_lines)

        job = jobs.get("eff-456-78a")
        self.assertIsNotNone(job)
        # Should keep the first user ID that was associated
        self.assertEqual(job["paid_user_id"], "abc12345")

    # ==================== PROVIDER SELECTION TESTS ====================

    def test_extract_provider_selection_model_a(self):
        """Test extracting provider selection for model_a (legacy format without style)."""
        log_line = "2025-12-09 10:00:00 - INFO - PROVIDER_SELECTION: job_id=abc-123 model=model_a status=success fallback=False"
        result = extract_provider_selection(log_line)
        self.assertIsNotNone(result)
        job_id, style, provider = result
        self.assertEqual(job_id, "abc-123")
        self.assertEqual(style, "apa7")  # Default for legacy logs
        self.assertEqual(provider, "model_a")

    def test_extract_provider_selection_model_b(self):
        """Test extracting provider selection for model_b (legacy format without style)."""
        log_line = "2025-12-09 10:00:00 - INFO - PROVIDER_SELECTION: job_id=test-job-456 model=model_b status=success fallback=false"
        result = extract_provider_selection(log_line)
        self.assertIsNotNone(result)
        job_id, style, provider = result
        self.assertEqual(job_id, "test-job-456")
        self.assertEqual(style, "apa7")  # Default for legacy logs
        self.assertEqual(provider, "model_b")

    def test_extract_provider_selection_uuid_job_id(self):
        """Test extracting provider selection with UUID job ID (legacy format)."""
        log_line = "2025-12-09 10:00:00 - INFO - PROVIDER_SELECTION: job_id=12345678-1234-1234-1234-123456789abc model=model_b status=success fallback=False"
        result = extract_provider_selection(log_line)
        self.assertIsNotNone(result)
        job_id, style, provider = result
        self.assertEqual(job_id, "12345678-1234-1234-1234-123456789abc")
        self.assertEqual(style, "apa7")  # Default for legacy logs
        self.assertEqual(provider, "model_b")

    def test_extract_provider_selection_with_style(self):
        """Test extracting provider selection with new format including style."""
        log_line = "2025-12-09 10:00:00 - INFO - PROVIDER_SELECTION: job_id=abc-123-def style=mla9 model=model_c status=success fallback=False"
        result = extract_provider_selection(log_line)
        self.assertIsNotNone(result)
        job_id, style, provider = result
        self.assertEqual(job_id, "abc-123-def")
        self.assertEqual(style, "mla9")
        self.assertEqual(provider, "model_c")

    def test_extract_provider_selection_invalid_line(self):
        """Test extracting provider selection from non-matching line."""
        log_line = "2025-12-09 10:00:00 - INFO - Some other log line"
        result = extract_provider_selection(log_line)
        self.assertIsNone(result)

    def test_extract_provider_selection_empty_line(self):
        """Test extracting provider selection from empty line."""
        result = extract_provider_selection("")
        self.assertIsNone(result)

    def test_parse_job_events_with_provider(self):
        """Test that parse_job_events correctly extracts and associates provider."""
        log_lines = [
            "2025-12-09 10:15:00 Creating async job abc-123 for free user",
            "2025-12-09 10:15:01 - INFO - PROVIDER_SELECTION: job_id=abc-123 model=model_b status=success fallback=False",
            "2025-12-09 10:15:10 Job abc-123: Completed successfully"
        ]

        jobs = parse_job_events(log_lines)

        # Check that provider was extracted
        job = jobs.get("abc-123")
        self.assertIsNotNone(job)
        self.assertEqual(job["provider"], "model_b")
        self.assertEqual(job["status"], "completed")

    def test_parse_job_events_provider_fallback(self):
        """Test provider extraction when fallback occurs."""
        log_lines = [
            "2025-12-09 10:15:00 Creating async job def-456 for paid user",
            "2025-12-09 10:15:01 - INFO - PROVIDER_SELECTION: job_id=def-456 model=model_a status=success fallback=true",
            "2025-12-09 10:15:10 Job def-456: Completed successfully"
        ]

        jobs = parse_job_events(log_lines)

        job = jobs.get("def-456")
        self.assertIsNotNone(job)
        # Even with fallback, the provider logged is model_a (the one actually used)
        self.assertEqual(job["provider"], "model_a")

    # ==================== CORRECTION EVENT TESTS ====================

    def test_extract_correction_event_valid(self):
        """Test extracting correction event from valid log line."""
        log_line = "2025-12-26 10:00:00 - INFO - CORRECTION_EVENT: job_id=abc-123-def action=copied citation_number=2 source_type=journal"
        result = extract_correction_event(log_line)
        self.assertIsNotNone(result)
        self.assertEqual(result["job_id"], "abc-123-def")
        self.assertEqual(result["action"], "copied")

    def test_extract_correction_event_uuid_job_id(self):
        """Test extracting correction event with UUID job ID."""
        log_line = "2025-12-26 10:00:00 - INFO - CORRECTION_EVENT: job_id=12345678-1234-1234-1234-123456789abc action=copied citation_number=1 source_type=book"
        result = extract_correction_event(log_line)
        self.assertIsNotNone(result)
        self.assertEqual(result["job_id"], "12345678-1234-1234-1234-123456789abc")
        self.assertEqual(result["action"], "copied")

    def test_extract_correction_event_none(self):
        """Test that non-matching lines return None."""
        log_line = "2025-12-26 10:00:00 - INFO - Some other log line"
        result = extract_correction_event(log_line)
        self.assertIsNone(result)

    def test_extract_correction_event_empty_line(self):
        """Test extracting correction event from empty line."""
        result = extract_correction_event("")
        self.assertIsNone(result)

    def test_parse_job_events_increments_corrections(self):
        """Test that parse_job_events counts multiple correction events per job."""
        log_lines = [
            "2025-12-26 10:00:00 Creating async job abc-123-def for free user",
            "2025-12-26 10:05:00 - INFO - CORRECTION_EVENT: job_id=abc-123-def action=copied citation_number=1 source_type=journal",
            "2025-12-26 10:05:30 - INFO - CORRECTION_EVENT: job_id=abc-123-def action=copied citation_number=2 source_type=book",
            "2025-12-26 10:06:00 - INFO - CORRECTION_EVENT: job_id=abc-123-def action=copied citation_number=3 source_type=website"
        ]

        jobs = parse_job_events(log_lines)

        job = jobs.get("abc-123-def")
        self.assertIsNotNone(job)
        self.assertEqual(job["corrections_copied"], 3)

    def test_parse_job_events_correction_event_creates_job(self):
        """Test that correction events can create jobs if they don't exist."""
        log_lines = [
            "2025-12-26 10:05:00 - INFO - CORRECTION_EVENT: job_id=new-job-123 action=copied citation_number=1 source_type=journal"
        ]

        jobs = parse_job_events(log_lines)

        job = jobs.get("new-job-123")
        self.assertIsNotNone(job)
        self.assertEqual(job["corrections_copied"], 1)


if __name__ == '__main__':
    unittest.main()