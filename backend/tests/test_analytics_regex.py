import unittest
import tempfile
import os
import sys
from datetime import datetime

# Add project root to path (parent of backend)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from dashboard.analytics import parse_upgrade_events

class TestAnalyticsRegex(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, 'test.log')

    def tearDown(self):
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        os.rmdir(self.test_dir)

    def test_parse_new_format_with_token(self):
        # Create log file with new UPGRADE_WORKFLOW format including token
        with open(self.log_file, 'w') as f:
            f.write("2025-12-16 10:00:00 INFO: UPGRADE_WORKFLOW: job_id=job-1 event=pricing_table_shown token=tok1 variant=1\n")
            f.write("2025-12-16 10:01:00 INFO: UPGRADE_WORKFLOW: job_id=job-1 event=product_selected token=tok1 variant=1 product_id=prod_1\n")
            f.write("2025-12-16 10:02:00 INFO: UPGRADE_WORKFLOW: job_id=job-1 event=purchase_completed token=tok1 variant=1 product_id=prod_1 amount_cents=1000\n")

        data = parse_upgrade_events(self.log_file)
        
        v1 = data['variant_1']
        self.assertEqual(v1['pricing_table_shown'], 1)
        self.assertEqual(v1['product_selected'], 1)
        self.assertEqual(v1['purchase_completed'], 1)
        self.assertEqual(v1['revenue_cents'], 1000)
        self.assertEqual(data['unique_tokens']['variant_1'], 1)

    def test_parse_none_token(self):
        with open(self.log_file, 'w') as f:
             f.write("2025-12-16 10:00:00 INFO: UPGRADE_WORKFLOW: job_id=None event=pricing_table_shown token=None variant=1\n")
        
        data = parse_upgrade_events(self.log_file)
        # Should count event but not unique token if token is None? 
        # Actually analytics logic adds token if truthy. 'None' string should be converted to None.
        
        v1 = data['variant_1']
        self.assertEqual(v1['pricing_table_shown'], 1)
        self.assertEqual(data['unique_tokens']['variant_1'], 0)

if __name__ == '__main__':
    unittest.main()
