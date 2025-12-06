import pytest
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class TestUpgradeWorkflowAPI:
    """Test suite for upgrade workflow event tracking API."""

    def test_upgrade_event_clicked_upgrade(self):
        """Test logging clicked_upgrade event."""
        response = client.post(
            "/api/upgrade-event",
            json={"job_id": "test-job-123", "event": "clicked_upgrade"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["job_id"] == "test-job-123"
        assert data["event"] == "clicked_upgrade"
        assert "message" in data

    def test_upgrade_event_modal_proceed(self):
        """Test logging modal_proceed event."""
        response = client.post(
            "/api/upgrade-event",
            json={"job_id": "test-job-456", "event": "modal_proceed"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["job_id"] == "test-job-456"
        assert data["event"] == "modal_proceed"

    def test_upgrade_event_success(self):
        """Test logging success event."""
        response = client.post(
            "/api/upgrade-event",
            json={"job_id": "test-job-789", "event": "success"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["job_id"] == "test-job-789"
        assert data["event"] == "success"

    def test_upgrade_event_missing_job_id(self):
        """Test upgrade event without job_id returns 400."""
        response = client.post(
            "/api/upgrade-event",
            json={"event": "clicked_upgrade"}
        )

        assert response.status_code == 400
        assert "job_id is required" in response.json()["detail"]

    def test_upgrade_event_missing_event(self):
        """Test upgrade event without event returns 400."""
        response = client.post(
            "/api/upgrade-event",
            json={"job_id": "test-job-123"}
        )

        assert response.status_code == 400
        assert "event is required" in response.json()["detail"]

    def test_upgrade_event_invalid_event(self):
        """Test upgrade event with invalid event type returns 400."""
        response = client.post(
            "/api/upgrade-event",
            json={"job_id": "test-job-123", "event": "invalid_event"}
        )

        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "Invalid event" in detail
        assert "clicked_upgrade" in detail
        assert "modal_proceed" in detail
        assert "success" in detail

    def test_upgrade_event_empty_request(self):
        """Test upgrade event with empty request returns 400."""
        response = client.post("/api/upgrade-event", json={})

        assert response.status_code == 400
        # Should fail on missing job_id first
        assert "job_id is required" in response.json()["detail"]

    def test_upgrade_event_logs_structured_data(self, caplog):
        """Test that upgrade events are logged with structured data."""
        import logging

        # Capture INFO level logs
        with caplog.at_level(logging.INFO):
            response = client.post(
                "/api/upgrade-event",
                json={"job_id": "test-job-logged", "event": "success"}
            )

        assert response.status_code == 200

        # Check that the structured log was created
        upgrade_logs = [
            record for record in caplog.records
            if "UPGRADE_WORKFLOW" in record.message
        ]
        assert len(upgrade_logs) == 1
        assert "job_id=test-job-logged" in upgrade_logs[0].message
        assert "event=success" in upgrade_logs[0].message

    def test_dashboard_api_includes_upgrade_state(self):
        """Test that dashboard API returns upgrade_state field for validations."""
        response = client.get("/api/dashboard")

        assert response.status_code == 200
        data = response.json()

        # Check if validations data includes upgrade_state
        if "validations" in data and data["validations"]:
            # Sample first validation to check structure
            validation = data["validations"][0]
            assert "upgrade_state" in validation, "upgrade_state field missing from dashboard API"