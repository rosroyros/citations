import unittest
import sys
import os
import re
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Add backend to path to import app logic
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import log_upgrade_event
from dashboard.log_parser import extract_upgrade_workflow_event

class TestLogFormatContract(unittest.TestCase):
    
    @patch('backend.app.logger')
    def test_log_upgrade_event_format(self, mock_logger):
        # Test that log_upgrade_event emits logs matching the parser's regex
        
        job_id = "abc-123"  # Hex compatible
        event = "clicked_upgrade"
        token = "token123"
        variant = "1"
        
        log_upgrade_event(event, token, experiment_variant=variant, job_id=job_id)
        
        # Verify logger was called
        self.assertTrue(mock_logger.info.called)
        
        # Get the actual log message
        # log_upgrade_event calls logger.info(log_line)
        # We need to find the call with the UPGRADE_WORKFLOW string
        found_match = False
        for call in mock_logger.info.call_args_list:
            args, _ = call
            log_message = args[0]
            if "UPGRADE_WORKFLOW:" in log_message:
                # This is the log line we care about
                # Verify parser can read it
                parsed = extract_upgrade_workflow_event(log_message)
                self.assertIsNotNone(parsed, f"Parser failed to extract from: {log_message}")
                self.assertEqual(parsed["job_id"], job_id)
                self.assertEqual(parsed["event"], event)
                found_match = True
                
        self.assertTrue(found_match, "Did not find UPGRADE_WORKFLOW log call")

    @patch('backend.app.logger')
    def test_log_upgrade_event_purchase(self, mock_logger):
        # Test purchase event format
        
        job_id = "def-456"  # Hex compatible
        event = "purchase_completed"
        token = "token456"
        variant = "2"
        
        log_upgrade_event(event, token, experiment_variant=variant, job_id=job_id, amount_cents=1000, product_id="prod_1")
        
        found_match = False
        for call in mock_logger.info.call_args_list:
            args, _ = call
            log_message = args[0]
            if "UPGRADE_WORKFLOW:" in log_message:
                # Also check that product_id and amount_cents are present in the string
                # even if current parser regex doesn't extract them (it only extracts job_id and event)
                # But mostly we want to ensure basic extraction doesn't break
                
                parsed = extract_upgrade_workflow_event(log_message)
                self.assertIsNotNone(parsed)
                self.assertEqual(parsed["job_id"], job_id)
                self.assertEqual(parsed["event"], event)
                self.assertEqual(parsed.get("amount_cents"), 1000)
                found_match = True
                
        self.assertTrue(found_match)

if __name__ == '__main__':
    unittest.main()
