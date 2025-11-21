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

    @patch('app.get_credits')
    def test_async_job_fails_with_zero_credits(self, mock_get_credits):
        """Test that async job fails when user has zero credits."""
        # Mock user has zero credits
        mock_get_credits.return_value = 0

        # Create job with user token
        request_data = {
            "citations": "<p>Test citation</p>",
            "style": "apa7"
        }
        headers = {"X-User-Token": "test_user_token"}

        response = client.post("/api/validate/async", json=request_data, headers=headers)
        assert response.status_code == 200
        job_id = response.json()["job_id"]

        # Wait for job to fail due to zero credits
        import time
        max_wait = 30  # Max 30 seconds
        wait_time = 0
        while wait_time < max_wait:
            response = client.get(f"/api/jobs/{job_id}")
            data = response.json()

            if data["status"] == "failed":
                break

            time.sleep(1)
            wait_time += 1

        # Should be failed with credit error message
        assert data["status"] == "failed"
        assert "error" in data
        assert "0 Citation Credits" in data["error"]
        mock_get_credits.assert_called_once_with("test_user_token")

    def test_async_job_fails_when_free_limit_exceeded(self):
        """Test that async job fails when free tier has already used limit."""
        # Create job with X-Free-Used header indicating user has already used 10 citations
        import base64
        free_used_header = base64.b64encode(b"10").decode('utf-8')

        request_data = {
            "citations": "<p>Test citation</p>",
            "style": "apa7"
        }
        headers = {"X-Free-Used": free_used_header}

        response = client.post("/api/validate/async", json=request_data, headers=headers)
        assert response.status_code == 200
        job_id = response.json()["job_id"]

        # Wait for job to fail due to free limit exceeded
        import time
        max_wait = 30  # Max 30 seconds
        wait_time = 0
        while wait_time < max_wait:
            response = client.get(f"/api/jobs/{job_id}")
            data = response.json()

            if data["status"] == "failed":
                break

            time.sleep(1)
            wait_time += 1

        # Should be failed with free tier limit error
        assert data["status"] == "failed"
        assert "error" in data
        assert "Free tier limit reached" in data["error"]

    def test_async_job_returns_partial_results_for_insufficient_free_credits(self):
        """Test that async job returns partial results when free user has some credits left."""
        # Create job with X-Free-Used header indicating user has already used 8 citations (2 remaining)
        import base64
        free_used_header = base64.b64encode(b"8").decode('utf-8')

        # Submit 5 citations (should only get 2 processed)
        request_data = {
            "citations": "<p>Citation 1</p><p>Citation 2</p><p>Citation 3</p><p>Citation 4</p><p>Citation 5</p>",
            "style": "apa7"
        }
        headers = {"X-Free-Used": free_used_header}

        response = client.post("/api/validate/async", json=request_data, headers=headers)
        assert response.status_code == 200
        job_id = response.json()["job_id"]

        # Wait for job to complete
        import time
        max_wait = 30  # Max 30 seconds
        wait_time = 0
        while wait_time < max_wait:
            response = client.get(f"/api/jobs/{job_id}")
            data = response.json()

            if data["status"] == "completed":
                break

            time.sleep(1)
            wait_time += 1

        # Should be completed with partial results
        assert data["status"] == "completed"
        assert "results" in data

        results = data["results"]
        assert results["partial"] is True  # Should indicate partial results
        assert results["citations_checked"] == 2  # Only 2 credits remaining
        assert results["citations_remaining"] == 3  # 3 citations locked
        assert results["free_used_total"] == 10  # Up to free limit
        assert len(results["results"]) == 2  # Only 2 actual citation results

    def test_job_cleanup_function_exists(self):
        """Test that cleanup_old_jobs function exists and can be called."""
        import app

        # Verify cleanup function exists
        assert hasattr(app, 'cleanup_old_jobs'), \
            "cleanup_old_jobs function not found in app module"
        assert callable(app.cleanup_old_jobs), \
            "cleanup_old_jobs should be callable"

    def test_job_cleanup_logic_structure(self):
        """Test that cleanup logic has proper structure for removing old jobs."""
        import app

        # Verify the cleanup function contains the expected elements
        # Since it runs in an infinite loop, we can't test execution directly
        # but we can verify the function signature and import structure

        # Get function source code and check it has key elements
        import inspect
        source = inspect.getsource(app.cleanup_old_jobs)

        # Should contain infinite loop for background processing
        assert "while True:" in source
        # Should contain 30-minute threshold for cleanup
        assert "30 * 60" in source
        # Should contain deletion logic
        assert "del jobs[" in source