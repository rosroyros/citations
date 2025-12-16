import unittest
import os
import sys
import tempfile
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dashboard.cron_parser import CronLogParser
from dashboard.database import DatabaseManager

class TestCronIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'validations_cron.db')
        self.log_path = os.path.join(self.test_dir, 'test.log')
        
        # Initialize DB
        self.db = DatabaseManager(self.db_path)
        
    def tearDown(self):
        self.db.close()
        import shutil
        shutil.rmtree(self.test_dir)

    def test_incremental_parsing(self):
        # 1. Write initial logs
        with open(self.log_path, 'w') as f:
            f.write("2025-12-16 10:00:00 INFO: Creating async job abc-123 for free user\n")
            f.write("2025-12-16 10:00:01 INFO: UPGRADE_WORKFLOW: job_id=abc-123 event=clicked_upgrade variant=1\n")
            f.write("2025-12-16 10:00:05 INFO: Job abc-123: Completed\n")
            
        # 2. Run cron parser
        parser = CronLogParser(self.db_path)
        parser.parse_incremental(self.log_path)
        
        # 3. Verify DB has abc-123
        job = self.db.get_validation('abc-123')
        self.assertIsNotNone(job)
        self.assertEqual(job['experiment_variant'], '1')
        self.assertIn('clicked', job['upgrade_state'])
        
        # 4. Append new logs
        with open(self.log_path, 'a') as f:
            f.write("2025-12-16 10:05:00 INFO: Creating async job def-456 for paid user\n")
            f.write("2025-12-16 10:05:01 INFO: UPGRADE_WORKFLOW: job_id=def-456 event=purchase_completed variant=2 amount_cents=500\n")
            f.write("2025-12-16 10:05:05 INFO: Job def-456: Completed\n")
            
        # 5. Run cron parser again
        parser.parse_incremental(self.log_path)
        
        # 6. Verify DB has def-456
        job2 = self.db.get_validation('def-456')
        self.assertIsNotNone(job2)
        self.assertEqual(job2['experiment_variant'], '2')
        self.assertEqual(job2['amount_cents'], 500)
        self.assertIn('success', job2['upgrade_state'])
        
        # Verify abc-123 is still there
        job1 = self.db.get_validation('abc-123')
        self.assertIsNotNone(job1)

if __name__ == '__main__':
    unittest.main()
