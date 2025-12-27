import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys

# Add parent directory to path to allow importing dashboard modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.telegram_notifier import format_message, get_upgrade_funnel_icons

class TestTelegramNotifier(unittest.TestCase):
    
    def test_get_upgrade_funnel_icons_simple(self):
        """Test simple upgrade states."""
        self.assertIn("🔒 Gated", get_upgrade_funnel_icons("locked"))
        self.assertIn("🛒 Pricing Shown", get_upgrade_funnel_icons("shown"))
        self.assertIn("💳 Checkout", get_upgrade_funnel_icons("checkout"))
        self.assertIn("💸 Upgraded!", get_upgrade_funnel_icons("success"))
        
    def test_get_upgrade_funnel_icons_complex(self):
        """Test complex csv states."""
        state = "locked,clicked,modal,success"
        icons = get_upgrade_funnel_icons(state)
        self.assertIn("🔒 Gated", icons)
        self.assertIn("🛒 Pricing Shown", icons)
        self.assertIn("💳 Checkout", icons)
        self.assertIn("💸 Upgraded!", icons)
        
    def test_get_upgrade_funnel_icons_empty(self):
        """Test empty state."""
        self.assertEqual("", get_upgrade_funnel_icons(None))
        self.assertEqual("", get_upgrade_funnel_icons(""))

    def test_format_message_completed_job(self):
        """Test formatting a completed paid job."""
        job = {
            "job_id": "12345678-abcd",
            "status": "completed",
            "duration_seconds": 3.5,
            "citation_count": 5,
            "valid_citations_count": 4,
            "invalid_citations_count": 1,
            "user_type": "paid",
            "provider": "model_c",
            "results_revealed_at": "2023-01-01T12:00:00",
            "results_gated": False,
            "corrections_copied": 2,
            "upgrade_state": None
        }
        
        msg = format_message(job)
        
        self.assertIn("📋 Job: `12345678`", msg)
        self.assertIn("✅ 4 Valid", msg)
        self.assertIn("❌ 1 Invalid", msg)
        self.assertIn("👤 Paid User", msg)
        self.assertIn("🤖 Gemini", msg)
        self.assertIn("🔓 Revealed: Yes", msg)
        self.assertIn("📋 Corrections: 2 copied", msg)

    def test_format_message_gated_job(self):
        """Test formatting a gated free job."""
        job = {
            "job_id": "87654321-zyxw",
            "status": "completed",
            "duration_seconds": 1.2,
            "citation_count": 10,
            "valid_citations_count": 0,
            "invalid_citations_count": 0,
            "user_type": "free",
            "provider": "model_a",
            "results_revealed_at": None,
            "results_gated": True,
            "corrections_copied": 0,
            "upgrade_state": "locked,clicked"
        }
        
        msg = format_message(job)
        
        self.assertIn("👤 Free User", msg)
        self.assertIn("🤖 OpenAI", msg)
        self.assertIn("🔒 Revealed: No", msg)
        self.assertIn("🔒 Gated", msg)
        self.assertIn("🛒 Pricing Shown", msg)
        # Should NOT have corrections line
        self.assertNotIn("📋 Corrections:", msg)

if __name__ == "__main__":
    unittest.main()
