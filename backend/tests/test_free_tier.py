"""Tests for free tier enforcement using X-Free-Used header."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import json
import sys
import os
import asyncio
import base64

# Mock the dashboard import
from unittest.mock import MagicMock
sys.modules['dashboard'] = MagicMock()
sys.modules['dashboard.log_parser'] = MagicMock()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app

client = TestClient(app)


def encode_free_used(value: int) -> str:
    """Encode free usage count as base64 for X-Free-Used header."""
    return base64.b64encode(str(value).encode('utf-8')).decode('utf-8')


class TestFreeTierEnforcement:
    """Test free tier enforcement logic using X-Free-Used header."""

    @patch('app.llm_provider.validate_citations', new_callable=AsyncMock)
    def test_free_user_under_limit_5_requested_0_used(self, mock_llm, caplog):
        """Test free user under limit (5 citations requested, 0 used) should succeed."""
        # Setup
        mock_llm.return_value = {
            "results": [
                {
                    "citation_number": 1,
                    "original": "Smith, 2023",
                    "source_type": "journal",
                    "errors": []
                },
                {
                    "citation_number": 2,
                    "original": "Jones, 2022",
                    "source_type": "book",
                    "errors": []
                },
                {
                    "citation_number": 3,
                    "original": "Brown, 2021",
                    "source_type": "article",
                    "errors": []
                },
                {
                    "citation_number": 4,
                    "original": "Davis, 2020",
                    "source_type": "website",
                    "errors": []
                },
                {
                    "citation_number": 5,
                    "original": "Wilson, 2019",
                    "source_type": "report",
                    "errors": []
                }
            ]
        }

        # Request with X-Free-Used header showing 0 citations used
        response = client.post(
            "/api/validate",
            json={"citations": "Smith, 2023\nJones, 2022\nBrown, 2021\nDavis, 2020\nWilson, 2019", "style": "apa7"},
            headers={"X-Free-Used": encode_free_used(0)}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 5
        assert data["partial"] is False
        assert data["free_used"] == 5  # Should be updated to 5

        # NEW: Check that user ID logging is present
        log_messages = [record.message for record in caplog.records]
        validation_logs = [msg for msg in log_messages if "Validation request - user_type=" in msg]
        assert len(validation_logs) > 0, "Expected to find user ID logging in validation request"

        # Check that user type and IDs are logged correctly for anonymous free user
        user_id_log = validation_logs[0]
        assert "user_type=free" in user_id_log
        assert "paid_user_id=N/A" in user_id_log
        assert "free_user_id=N/A" in user_id_log
        assert "style=apa7" in user_id_log

    @patch('app.llm_provider.validate_citations', new_callable=AsyncMock)
    def test_free_user_at_limit_2_requested_8_used(self, mock_llm):
        """Test free user at limit (2 citations requested, 8 used) should succeed."""
        # Setup
        mock_llm.return_value = {
            "results": [
                {
                    "citation_number": 1,
                    "original": "Smith, 2023",
                    "source_type": "journal",
                    "errors": []
                },
                {
                    "citation_number": 2,
                    "original": "Jones, 2022",
                    "source_type": "book",
                    "errors": []
                }
            ]
        }

        # Request with X-Free-Used header showing 8 citations used (8+2=10, at limit)
        response = client.post(
            "/api/validate",
            json={"citations": "Smith, 2023\nJones, 2022", "style": "apa7"},
            headers={"X-Free-Used": encode_free_used(8)}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2
        assert data["partial"] is False
        assert data["free_used"] == 10  # Should be updated to 10 (at limit)

    @patch('app.llm_provider.validate_citations', new_callable=AsyncMock)
    def test_free_user_over_limit_8_requested_5_used(self, mock_llm):
        """Test free user over limit (8 citations requested, 5 used) should be limited."""
        # Setup - return 8 potential results
        mock_llm.return_value = {
            "results": [
                {"citation_number": i+1, "original": f"Source {i+1}", "source_type": "journal", "errors": []}
                for i in range(8)
            ]
        }

        # Request with X-Free-Used header showing 5 citations used (5+8=13, over limit of 10)
        response = client.post(
            "/api/validate",
            json={"citations": "8 citations here", "style": "apa7"},
            headers={"X-Free-Used": encode_free_used(5)}
        )

        # Assertions - should only process 5 more citations (5 used + 5 new = 10 total)
        assert response.status_code == 200
        data = response.json()
        assert data["partial"] is True
        assert data["citations_checked"] == 5  # Only processed 5 out of 8
        assert data["citations_remaining"] == 3  # 3 left unprocessed
        assert len(data["results"]) == 5  # Only first 5 results
        assert data["free_used"] == 10  # At limit

    @patch('app.llm_provider.validate_citations', new_callable=AsyncMock)
    def test_free_user_already_at_limit_5_requested_10_used(self, mock_llm):
        """Test free user already at limit (5 citations requested, 10 used) should return empty partial results."""
        # Setup - return 5 potential results
        mock_llm.return_value = {
            "results": [
                {"citation_number": i+1, "original": f"Source {i+1}", "source_type": "journal", "errors": []}
                for i in range(5)
            ]
        }

        # Request with X-Free-Used header showing 10 citations used (already at limit)
        response = client.post(
            "/api/validate",
            json={"citations": "5 citations here", "style": "apa7"},
            headers={"X-Free-Used": encode_free_used(10)}
        )

        # Assertions - should return empty partial results with locked teaser
        assert response.status_code == 200
        data = response.json()
        assert data["partial"] is True
        assert data["citations_checked"] == 0
        assert data["citations_remaining"] == 5
        assert len(data["results"]) == 0
        assert data["free_used"] == 10

    @patch('app.llm_provider.validate_citations', new_callable=AsyncMock)
    def test_missing_free_used_header_treated_as_0(self, mock_llm):
        """Test missing X-Free-Used header should be treated as 0 used."""
        # Setup
        mock_llm.return_value = {
            "results": [
                {
                    "citation_number": 1,
                    "original": "Smith, 2023",
                    "source_type": "journal",
                    "errors": []
                }
            ]
        }

        # Request without X-Free-Used header
        response = client.post(
            "/api/validate",
            json={"citations": "Smith, 2023", "style": "apa7"}
        )

        # Assertions - should treat as 0 used and allow processing
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["partial"] is False
        assert data["free_used"] == 1  # Should be updated to 1

    @patch('app.llm_provider.validate_citations', new_callable=AsyncMock)
    def test_invalid_free_used_header_returns_400(self, mock_llm):
        """Test invalid X-Free-Used header should return 400 Bad Request."""
        # Setup - mock LLM response (though this test expects 400 before LLM is called)
        mock_llm.return_value = {"results": []}
        # Request with invalid X-Free-Used header (non-numeric)
        response = client.post(
            "/api/validate",
            json={"citations": "Smith, 2023", "style": "apa7"},
            headers={"X-Free-Used": "invalid"}
        )

        # Assertions - should reject with 400 Bad Request
        assert response.status_code == 400
        error_data = response.json()
        assert "Invalid" in error_data["detail"]
        assert "X-Free-Used" in error_data["detail"]

    @patch('app.llm_provider.validate_citations', new_callable=AsyncMock)
    def test_free_user_id_logging_with_uuid(self, mock_llm, caplog):
        """Test that free user ID is logged correctly when X-Free-User-ID header is present."""
        # Setup
        mock_llm.return_value = {
            "results": [
                {
                    "citation_number": 1,
                    "original": "Smith, 2023",
                    "source_type": "journal",
                    "errors": []
                }
            ]
        }

        # Test UUID for free user
        test_uuid = "550e8400-e29b-41d4-a716-446655440000"

        # Request with X-Free-User-ID header
        response = client.post(
            "/api/validate",
            json={"citations": "Smith, 2023", "style": "apa7"},
            headers={
                "X-Free-User-ID": base64.b64encode(test_uuid.encode()).decode(),
                "X-Free-Used": encode_free_used(3)
            }
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1

        # Check that user ID logging is present and correct
        log_messages = [record.message for record in caplog.records]
        validation_logs = [msg for msg in log_messages if "Validation request - user_type=" in msg]
        assert len(validation_logs) > 0, "Expected to find user ID logging in validation request"

        # Check that free user ID is logged correctly
        user_id_log = validation_logs[0]
        assert "user_type=free" in user_id_log
        assert "paid_user_id=N/A" in user_id_log
        assert f"free_user_id={test_uuid}" in user_id_log
        assert "style=apa7" in user_id_log