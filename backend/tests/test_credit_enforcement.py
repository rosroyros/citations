"""Tests for credit enforcement in validation endpoint."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import json
import sys
import os

# Mock the dashboard import
from unittest.mock import MagicMock
sys.modules['dashboard'] = MagicMock()
sys.modules['dashboard.log_parser'] = MagicMock()

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app

client = TestClient(app)


class TestCreditEnforcement:
    """Test credit enforcement logic in validation endpoint."""

    @patch('database.get_credits')
    @patch('database.deduct_credits')
    @patch('app.llm_provider.validate_citations')
    def test_no_token_freeTier_returns_all_results(self, mock_llm, mock_deduct, mock_get, caplog):
        """Test that free tier (no token) returns all results without credit checks."""
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

        # Request without token
        response = client.post(
            "/api/validate",
            json={"citations": "Smith, 2023", "style": "apa7"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["partial"] is False  # Should be False for free tier

        # Verify database functions were not called
        mock_get.assert_not_called()
        mock_deduct.assert_not_called()

        # NEW: Check that user ID logging is present for anonymous free user
        log_messages = [record.message for record in caplog.records]
        validation_logs = [msg for msg in log_messages if "Validation request - user_type=" in msg]
        assert len(validation_logs) > 0, "Expected to find user ID logging in validation request"

        # Check that user type and IDs are logged correctly for anonymous user
        user_id_log = validation_logs[0]
        assert "user_type=free" in user_id_log
        assert "paid_user_id=N/A" in user_id_log
        assert "free_user_id=N/A" in user_id_log

    @patch('backend.database.get_credits')
    @patch('backend.database.deduct_credits')
    @patch('backend.app.llm_provider.validate_citations')
    def test_token_sufficientCredits_deducts_and_returns_all(self, mock_llm, mock_deduct, mock_get):
        """Test that token with sufficient credits gets all results and credits are deducted."""
        # Setup
        mock_get.return_value = 100
        mock_deduct.return_value = True
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

        # Request with token header
        response = client.post(
            "/api/validate",
            json={"citations": "Smith, 2023\nJones, 2022", "style": "apa7"},
            headers={"X-User-Token": "test-token-123"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2
        assert data["credits_remaining"] == 98  # 100 - 2 citations

        # Verify database calls
        mock_get.assert_called_once_with("test-token-123")
        mock_deduct.assert_called_once_with("test-token-123", 2)

    @patch('backend.database.get_credits')
    @patch('backend.database.deduct_credits')
    @patch('backend.app.llm_provider.validate_citations')
    def test_token_insufficientCredits_returns_partial_results(self, mock_llm, mock_deduct, mock_get):
        """Test that token with insufficient credits gets partial results."""
        # Setup
        mock_get.return_value = 3  # Only 3 credits
        mock_deduct.return_value = True
        mock_llm.return_value = {
            "results": [
                {"citation_number": 1, "original": "Smith, 2023", "source_type": "journal", "errors": []},
                {"citation_number": 2, "original": "Jones, 2022", "source_type": "book", "errors": []},
                {"citation_number": 3, "original": "Brown, 2021", "source_type": "article", "errors": []},
                {"citation_number": 4, "original": "Davis, 2020", "source_type": "website", "errors": []},
                {"citation_number": 5, "original": "Wilson, 2019", "source_type": "report", "errors": []},
            ]
        }

        # Request with token header
        response = client.post(
            "/api/validate",
            json={"citations": "Five citations here", "style": "apa7"},
            headers={"X-User-Token": "test-token-123"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["partial"] is True
        assert data["citations_checked"] == 3
        assert data["citations_remaining"] == 2
        assert data["credits_remaining"] == 0
        assert len(data["results"]) == 3  # Only first 3 results

        # Verify database calls
        mock_get.assert_called_once_with("test-token-123")
        mock_deduct.assert_called_once_with("test-token-123", 3)  # Deduct all available

    @patch('backend.database.get_credits')
    def test_token_zeroCredits_returns_402_error(self, mock_get):
        """Test that token with zero credits returns 402 Payment Required error."""
        # Setup
        mock_get.return_value = 0

        # Request with token header
        response = client.post(
            "/api/validate",
            json={"citations": "Smith, 2023", "style": "apa7"},
            headers={"X-User-Token": "test-token-123"}
        )

        # Assertions
        assert response.status_code == 402
        error_data = response.json()
        assert "0 Citation Credits remaining" in error_data["detail"]

        # Verify database call
        mock_get.assert_called_once_with("test-token-123")

    @patch('backend.database.get_credits')
    @patch('backend.database.deduct_credits')
    @patch('backend.app.llm_provider.validate_citations')
    def test_token_exactCredits_edge_case(self, mock_llm, mock_deduct, mock_get):
        """Test edge case where user has exactly the number of credits needed."""
        # Setup
        mock_get.return_value = 50  # Exactly 50 credits
        mock_deduct.return_value = True
        mock_llm.return_value = {
            "results": [{"citation_number": i+1, "original": f"Source {i+1}",
                        "source_type": "journal", "errors": []} for i in range(50)]
        }

        # Request with token header
        response = client.post(
            "/api/validate",
            json={"citations": "50 citations", "style": "apa7"},
            headers={"X-User-Token": "test-token-123"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 50
        assert data["credits_remaining"] == 0
        assert data["partial"] is False  # Should not be partial

        # Verify database calls
        mock_get.assert_called_once_with("test-token-123")
        mock_deduct.assert_called_once_with("test-token-123", 50)

    @patch('backend.database.get_credits')
    @patch('backend.database.deduct_credits')
    @patch('backend.app.llm_provider.validate_citations')
    def test_token_singleCreditEdge_case(self, mock_llm, mock_deduct, mock_get):
        """Test edge case where user has exactly 1 credit."""
        # Setup
        mock_get.return_value = 1  # Exactly 1 credit
        mock_deduct.return_value = True
        mock_llm.return_value = {
            "results": [
                {"citation_number": 1, "original": "Smith, 2023", "source_type": "journal", "errors": []}
            ]
        }

        # Request with token header
        response = client.post(
            "/api/validate",
            json={"citations": "Single citation", "style": "apa7"},
            headers={"X-User-Token": "test-token-123"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["credits_remaining"] == 0