"""
Unit tests for upgrade event parsing in log_parser.py.

Tests the extract_upgrade_workflow_event function which parses
UPGRADE_WORKFLOW log lines for dashboard analytics.
"""
import unittest
import sys
import os

# Add the dashboard directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from log_parser import (
    extract_upgrade_workflow_event,
    parse_job_events,
)


class TestUpgradeEventParsing(unittest.TestCase):
    """Test suite for extract_upgrade_workflow_event function."""

    def test_extract_upgrade_event_basic(self):
        """Test extracting a standard button click upgrade event."""
        log_line = (
            "2025-12-17 10:00:00 - citation_validator - INFO - "
            "UPGRADE_WORKFLOW: job_id=abc-123-def event=clicked_upgrade"
        )
        result = extract_upgrade_workflow_event(log_line)

        self.assertIsNotNone(result)
        self.assertEqual(result["job_id"], "abc-123-def")
        self.assertEqual(result["event"], "clicked_upgrade")

    def test_extract_upgrade_event_with_interaction_type(self):
        """Test extracting event with interaction_type='auto' for inline variants."""
        log_line = (
            "2025-12-17 10:00:00 - citation_validator - INFO - "
            "UPGRADE_WORKFLOW: job_id=def-456-abc event=pricing_viewed "
            "variant=1.2 interaction_type=auto"
        )
        result = extract_upgrade_workflow_event(log_line)

        self.assertIsNotNone(result)
        self.assertEqual(result["job_id"], "def-456-abc")
        self.assertEqual(result["event"], "pricing_viewed")
        self.assertEqual(result["experiment_variant"], "1.2")
        self.assertEqual(result["interaction_type"], "auto")

    def test_extract_upgrade_event_with_all_fields(self):
        """Test extracting event with all optional fields present."""
        log_line = (
            "2025-12-17 10:00:00 - citation_validator - INFO - "
            "UPGRADE_WORKFLOW: job_id=xyz-789-uvw event=purchase_completed "
            "variant=2.1 product_id=credit_20 amount_cents=499 "
            "currency=usd order_id=polar_ord_123 token=abc12345"
        )
        result = extract_upgrade_workflow_event(log_line)

        self.assertIsNotNone(result)
        self.assertEqual(result["job_id"], "xyz-789-uvw")
        self.assertEqual(result["event"], "purchase_completed")
        self.assertEqual(result["experiment_variant"], "2.1")
        self.assertEqual(result["product_id"], "credit_20")
        self.assertEqual(result["amount_cents"], 499)
        self.assertEqual(result["currency"], "usd")
        self.assertEqual(result["order_id"], "polar_ord_123")
        self.assertEqual(result["token"], "abc12345")

    def test_extract_upgrade_event_malformed_log(self):
        """Test that invalid/malformed log lines return None gracefully."""
        # No UPGRADE_WORKFLOW marker
        log_line = "2025-12-17 10:00:00 - citation_validator - INFO - Regular log message"
        result = extract_upgrade_workflow_event(log_line)
        self.assertIsNone(result)

        # Has marker but malformed content
        log_line = "2025-12-17 10:00:00 - UPGRADE_WORKFLOW: invalid format"
        result = extract_upgrade_workflow_event(log_line)
        self.assertIsNone(result)

        # Empty line
        result = extract_upgrade_workflow_event("")
        self.assertIsNone(result)

    def test_extract_upgrade_event_missing_job_id(self):
        """Test that missing required job_id field returns None."""
        log_line = (
            "2025-12-17 10:00:00 - citation_validator - INFO - "
            "UPGRADE_WORKFLOW: event=clicked_upgrade variant=1.1"
        )
        result = extract_upgrade_workflow_event(log_line)
        self.assertIsNone(result)

    def test_extract_upgrade_event_uuid_job_id(self):
        """Test extracting event with UUID format job_id."""
        log_line = (
            "2025-12-17 10:00:00 - citation_validator - INFO - "
            "UPGRADE_WORKFLOW: job_id=550e8400-e29b-41d4-a716-446655440000 "
            "event=checkout_started variant=2.2"
        )
        result = extract_upgrade_workflow_event(log_line)

        self.assertIsNotNone(result)
        self.assertEqual(result["job_id"], "550e8400-e29b-41d4-a716-446655440000")
        self.assertEqual(result["event"], "checkout_started")
        self.assertEqual(result["experiment_variant"], "2.2")

    def test_extract_upgrade_event_none_job_id_string(self):
        """Test handling of 'None' string for job_id (edge case)."""
        log_line = (
            "2025-12-17 10:00:00 - citation_validator - INFO - "
            "UPGRADE_WORKFLOW: job_id=None event=pricing_viewed"
        )
        result = extract_upgrade_workflow_event(log_line)

        # Should still extract, job_id will be the string "None"
        self.assertIsNotNone(result)
        self.assertEqual(result["job_id"], "None")
        self.assertEqual(result["event"], "pricing_viewed")

    def test_extract_upgrade_event_token_none_excluded(self):
        """Test that token='None' is not included in result."""
        log_line = (
            "2025-12-17 10:00:00 - citation_validator - INFO - "
            "UPGRADE_WORKFLOW: job_id=abc-123 event=clicked token=None"
        )
        result = extract_upgrade_workflow_event(log_line)

        self.assertIsNotNone(result)
        self.assertNotIn("token", result)

    def test_integration_parse_job_events_with_upgrade(self):
        """Test that parse_job_events correctly processes upgrade workflow events."""
        log_lines = [
            "2025-12-17 10:00:00 Creating async job abc-123-def for free user",
            "2025-12-17 10:00:10 - UPGRADE_WORKFLOW: job_id=abc-123-def event=pricing_viewed variant=1.1",
            "2025-12-17 10:00:15 - UPGRADE_WORKFLOW: job_id=abc-123-def event=clicked_upgrade variant=1.1",
            "2025-12-17 10:01:00 Job abc-123-def: Completed successfully"
        ]

        jobs = parse_job_events(log_lines)

        # Verify job was created
        self.assertIn("abc-123-def", jobs)
        job = jobs["abc-123-def"]
        self.assertEqual(job["user_type"], "free")
        self.assertEqual(job["status"], "completed")
        # Note: parse_job_events adds upgrade_state, not individual upgrade event fields
        self.assertIn("upgrade_state", job)


class TestUpgradeEventVariantFormats(unittest.TestCase):
    """Test various variant format handling in upgrade events."""

    def test_variant_1_1_credits_button(self):
        """Test variant 1.1 (Credits + Button) format."""
        log_line = (
            "2025-12-17 10:00:00 - "
            "UPGRADE_WORKFLOW: job_id=test-123 event=clicked_upgrade variant=1.1"
        )
        result = extract_upgrade_workflow_event(log_line)

        self.assertIsNotNone(result)
        self.assertEqual(result["experiment_variant"], "1.1")

    def test_variant_1_2_credits_inline(self):
        """Test variant 1.2 (Credits + Inline) format."""
        log_line = (
            "2025-12-17 10:00:00 - "
            "UPGRADE_WORKFLOW: job_id=test-123 event=pricing_viewed variant=1.2 interaction_type=auto"
        )
        result = extract_upgrade_workflow_event(log_line)

        self.assertIsNotNone(result)
        self.assertEqual(result["experiment_variant"], "1.2")
        self.assertEqual(result["interaction_type"], "auto")

    def test_variant_2_1_passes_button(self):
        """Test variant 2.1 (Passes + Button) format."""
        log_line = (
            "2025-12-17 10:00:00 - "
            "UPGRADE_WORKFLOW: job_id=test-123 event=clicked_upgrade variant=2.1"
        )
        result = extract_upgrade_workflow_event(log_line)

        self.assertIsNotNone(result)
        self.assertEqual(result["experiment_variant"], "2.1")

    def test_variant_2_2_passes_inline(self):
        """Test variant 2.2 (Passes + Inline) format."""
        log_line = (
            "2025-12-17 10:00:00 - "
            "UPGRADE_WORKFLOW: job_id=test-123 event=pricing_viewed variant=2.2 interaction_type=auto"
        )
        result = extract_upgrade_workflow_event(log_line)

        self.assertIsNotNone(result)
        self.assertEqual(result["experiment_variant"], "2.2")
        self.assertEqual(result["interaction_type"], "auto")

    def test_legacy_variant_format(self):
        """Test legacy '1' or '2' variant format still works."""
        log_line = (
            "2025-12-17 10:00:00 - "
            "UPGRADE_WORKFLOW: job_id=test-123 event=clicked_upgrade variant=1"
        )
        result = extract_upgrade_workflow_event(log_line)

        self.assertIsNotNone(result)
        self.assertEqual(result["experiment_variant"], "1")


if __name__ == '__main__':
    unittest.main()
