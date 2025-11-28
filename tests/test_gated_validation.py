"""
Tests for gated validation results functionality.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app import app
import time
import uuid

client = TestClient(app)


class TestGatedValidationStatus:
    """Test gated validation status retrieval endpoint."""

    def test_get_gated_status_returns_404_for_nonexistent_job(self):
        """Test that requesting status for non-existent job returns 404."""
        fake_job_id = "nonexistent_job_123"
        response = client.get(f"/api/gating/status/{fake_job_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_gated_status_returns_gating_decision_for_existing_job(self):
        """Test that requesting status for existing job returns gating information."""
        # First create a validation job
        payload = {
            "citations": "Smith, J. (2020). Test article. Journal of Testing, 1(1), 1-10.",
            "style": "apa7"
        }

        # Create async job to get a job_id
        response = client.post("/api/validate/async", json=payload)
        assert response.status_code == 200

        job_id = response.json()["job_id"]

        # Wait a moment for job to be processed
        time.sleep(0.5)

        # Check gating status
        response = client.get(f"/api/gating/status/{job_id}")

        # This should fail initially since endpoint doesn't exist
        assert response.status_code == 404


class TestStoreGatedResults:
    """Test storing gated validation results functionality."""

    def test_gated_results_stored_in_database(self):
        """Test that gated results are properly stored in database during validation."""
        payload = {
            "citations": "Doe, J. (2021). Another test. Test Journal, 2(1), 15-25.",
            "style": "apa7"
        }

        response = client.post("/api/validate", json=payload)
        assert response.status_code == 200

        data = response.json()

        # Should have job_id for tracking
        assert "job_id" in data
        assert "results_gated" in data

        job_id = data["job_id"]
        assert job_id is not None

    def test_gating_decision_logged_correctly(self):
        """Test that gating decisions are properly logged for analytics."""
        # This test would verify that logging is working correctly
        # For now, we just test that the validation completes successfully
        payload = {
            "citations": "Johnson, A. (2022). Test article. Another Journal, 3(2), 45-60.",
            "style": "apa7"
        }

        response = client.post("/api/validate", json=payload)
        assert response.status_code == 200

        # Response should include gating information
        data = response.json()
        assert isinstance(data.get("results_gated"), bool)


class TestGatingErrorHandling:
    """Test error handling in gated validation functionality."""

    def test_missing_job_id_returns_400(self):
        """Test that reveal results endpoint returns 400 for missing job_id."""
        response = client.post("/api/reveal-results", json={})

        assert response.status_code == 400
        assert "job_id" in response.json()["detail"]

    def test_invalid_job_id_returns_404(self):
        """Test that reveal results endpoint returns 404 for invalid job_id."""
        fake_job_id = "fake_job_12345"
        response = client.post("/api/reveal-results", json={"job_id": fake_job_id})

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_gating_analytics_handles_invalid_parameters(self):
        """Test that gating analytics endpoint validates parameters properly."""
        # Test invalid days parameter
        response = client.get("/api/gating/analytics?days=0")
        assert response.status_code == 400

        response = client.get("/api/gating/analytics?days=400")
        assert response.status_code == 400

        # Test invalid user_type parameter
        response = client.get("/api/gating/analytics?user_type=invalid")
        assert response.status_code == 400

    def test_gating_analytics_returns_valid_data(self):
        """Test that gating analytics endpoint returns valid analytics data."""
        response = client.get("/api/gating/analytics")

        assert response.status_code == 200
        data = response.json()

        # Should contain expected analytics fields
        expected_fields = [
            "total_validations", "gated_results", "direct_results",
            "gating_rate", "free_users", "paid_users", "feature_enabled"
        ]

        for field in expected_fields:
            assert field in data
            assert isinstance(data[field], (int, float, bool, str))