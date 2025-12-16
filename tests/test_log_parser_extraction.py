import unittest
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path to import dashboard.log_parser
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dashboard.log_parser import (
    extract_partial_results_event,
    extract_upgrade_workflow_event,
    parse_job_events
)

class TestLogParserExtraction(unittest.TestCase):
    
    def setUp(self):
        # Use valid hex IDs because the regex expects [a-f0-9-]+
        self.job_id = "abc-123" 
    
    def test_extract_partial_results_empty(self):
        log_line = f"2025-12-16 10:00:00 INFO: Job {self.job_id}: Free tier limit reached - returning empty partial results"
        result = extract_partial_results_event(log_line)
        self.assertEqual(result, (self.job_id, 'empty'))

    def test_extract_partial_results_locked(self):
        log_line = f"2025-12-16 10:00:00 INFO: Job {self.job_id}: Completed - free tier limit reached, returning locked partial results"
        result = extract_partial_results_event(log_line)
        self.assertEqual(result, (self.job_id, 'locked'))

    def test_extract_partial_results_none(self):
        log_line = f"2025-12-16 10:00:00 INFO: Job {self.job_id}: Completed successfully"
        result = extract_partial_results_event(log_line)
        self.assertIsNone(result)

    def test_extract_upgrade_workflow_event(self):
        log_line = f"2025-12-16 10:00:00 INFO: UPGRADE_WORKFLOW: job_id={self.job_id} event=clicked_upgrade"
        result = extract_upgrade_workflow_event(log_line)
        self.assertEqual(result, {"job_id": self.job_id, "event": 'clicked_upgrade'})
        
        log_line = f"2025-12-16 10:00:00 INFO: UPGRADE_WORKFLOW: job_id={self.job_id} event=success"
        result = extract_upgrade_workflow_event(log_line)
        self.assertEqual(result, {"job_id": self.job_id, "event": 'success'})
        
        log_line = f"2025-12-16 10:00:00 INFO: UPGRADE_WORKFLOW: job_id={self.job_id} event=purchase_completed"
        result = extract_upgrade_workflow_event(log_line)
        self.assertEqual(result, {"job_id": self.job_id, "event": 'purchase_completed'})

    def test_extract_upgrade_workflow_event_rich_data(self):
        # Test extraction of new fields
        log_line = f"2025-12-16 10:00:00 INFO: UPGRADE_WORKFLOW: job_id={self.job_id} event=purchase_completed variant=1 product_id=prod_123 amount_cents=1000 currency=USD order_id=ord_123"
        result = extract_upgrade_workflow_event(log_line)
        self.assertEqual(result, {
            "job_id": self.job_id,
            "event": "purchase_completed",
            "experiment_variant": "1",
            "product_id": "prod_123",
            "amount_cents": 1000,
            "currency": "USD",
            "order_id": "ord_123"
        })

    def test_extract_upgrade_workflow_event_malformed(self):
        log_line = "2025-12-16 10:00:00 INFO: UPGRADE_WORKFLOW: invalid format"
        result = extract_upgrade_workflow_event(log_line)
        self.assertIsNone(result)

    def test_state_accumulation(self):
        # Simulate a sequence of log lines for a single job
        log_lines = [
            f"2025-12-16 10:00:00 INFO: Job {self.job_id}: Completed - free tier limit reached, returning locked partial results",
            f"2025-12-16 10:01:00 INFO: UPGRADE_WORKFLOW: job_id={self.job_id} event=clicked_upgrade",
            f"2025-12-16 10:02:00 INFO: UPGRADE_WORKFLOW: job_id={self.job_id} event=modal_proceed",
            f"2025-12-16 10:03:00 INFO: UPGRADE_WORKFLOW: job_id={self.job_id} event=purchase_completed"
        ]
        
        jobs = parse_job_events(log_lines)
        
        self.assertIn(self.job_id, jobs)
        job = jobs[self.job_id]
        
        # Verify upgrade_state accumulation
        # Expected order: locked -> clicked -> modal -> success
        # Note: 'locked' is prepended if found via partial results logic
        # 'purchase_completed' maps to 'success'
        
        expected_state = "locked,clicked,modal,success"
        self.assertEqual(job.get('upgrade_state'), expected_state)

    def test_state_accumulation_deduplication(self):
        # Verify duplicates are handled gracefully
        log_lines = [
            f"2025-12-16 10:00:00 INFO: Job {self.job_id}: Completed - free tier limit reached, returning locked partial results",
            f"2025-12-16 10:01:00 INFO: UPGRADE_WORKFLOW: job_id={self.job_id} event=clicked_upgrade",
            f"2025-12-16 10:01:05 INFO: UPGRADE_WORKFLOW: job_id={self.job_id} event=clicked_upgrade", # Duplicate
            f"2025-12-16 10:02:00 INFO: UPGRADE_WORKFLOW: job_id={self.job_id} event=modal_proceed"
        ]
        
        jobs = parse_job_events(log_lines)
        job = jobs[self.job_id]
        
        expected_state = "locked,clicked,modal"
        self.assertEqual(job.get('upgrade_state'), expected_state)
    
    def test_job_creation_detection(self):
        # Use a new ID for this test
        job_id = "abc-456"
        log_line = f"2025-12-16 10:00:00 INFO: Creating async job {job_id} for free user"
        jobs = parse_job_events([log_line])
        self.assertIn(job_id, jobs)
        self.assertEqual(jobs[job_id]['status'], 'pending')
        self.assertEqual(jobs[job_id]['user_type'], 'free')

    def test_job_completion_detection(self):
        job_id = "abc-789"
        log_lines = [
            f"2025-12-16 10:00:00 INFO: Creating async job {job_id} for paid user",
            f"2025-12-16 10:05:00 INFO: Job {job_id}: Completed"
        ]
        jobs = parse_job_events(log_lines)
        self.assertIn(job_id, jobs)
        self.assertEqual(jobs[job_id]['status'], 'completed')
        self.assertIsNotNone(jobs[job_id].get('completed_at'))

if __name__ == '__main__':
    unittest.main()
