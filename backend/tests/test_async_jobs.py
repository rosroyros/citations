"""Tests for async job infrastructure."""

import pytest
import json
import time
import uuid
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app import app

client = TestClient(app)


class TestAsyncJobs:
    """Test async job processing functionality."""

    def test_create_async_job_returns_job_id(self):
        """Test that POST /api/validate/async creates a job and returns job_id."""
        # Setup
        request_data = {
            "citations": "<p>Test citation 1</p><p>Test citation 2</p>",
            "style": "apa7"
        }

        # This should succeed and return job_id
        response = client.post("/api/validate/async", json=request_data)

        # Expect success response
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert "status" in data
        assert data["status"] == "pending"

        # Verify job_id is a valid UUID format
        import uuid
        uuid.UUID(data["job_id"])  # Will raise ValueError if invalid

        # Verify job was stored in jobs dict
        import app
        assert data["job_id"] in app.jobs

    def test_get_job_status_returns_job_data(self):
        """Test that GET /api/jobs/{job_id} returns job status and data."""
        # First create a job
        request_data = {
            "citations": "<p>Test citation</p>",
            "style": "apa7"
        }
        create_response = client.post("/api/validate/async", json=request_data)
        job_id = create_response.json()["job_id"]

        # Wait for job to complete (real async processing)
        import time
        max_wait = 60  # Max 60 seconds
        wait_time = 0
        while wait_time < max_wait:
            response = client.get(f"/api/jobs/{job_id}")
            assert response.status_code == 200
            data = response.json()

            if data["status"] in ["completed", "failed"]:
                break

            time.sleep(1)
            wait_time += 1

        # Should be completed now
        assert data["status"] in ["completed", "failed"]
        assert "status" in data

    def test_get_job_status_returns_404_for_nonexistent_job(self):
        """Test that GET /api/jobs/{job_id} returns 404 for nonexistent job."""
        fake_job_id = str(uuid.uuid4())

        response = client.get(f"/api/jobs/{fake_job_id}")

        # Expect 404 for nonexistent job
        assert response.status_code == 404

    def test_job_storage_dict_exists(self):
        """Test that jobs storage dict is available in app module."""
        import app

        # This should fail because jobs dict doesn't exist yet
        assert hasattr(app, 'jobs'), "jobs storage dict not found in app module"
        assert isinstance(app.jobs, dict), "jobs should be a dict"

    def test_process_validation_job_function_exists(self):
        """Test that process_validation_job function exists."""
        import app

        # This should fail because function doesn't exist yet
        assert hasattr(app, 'process_validation_job'), \
            "process_validation_job function not found in app module"
        assert callable(app.process_validation_job), \
            "process_validation_job should be callable"