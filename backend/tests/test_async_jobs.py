"""Tests for async job infrastructure."""

import pytest
import json
import time
import uuid
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import sys
import os

# Mock the dashboard import
from unittest.mock import MagicMock
sys.modules['dashboard'] = MagicMock()
sys.modules['dashboard.log_parser'] = MagicMock()

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app import app

client = TestClient(app)


class TestAsyncJobs:
    """Test async job processing functionality."""

    def test_create_async_job_returns_job_id(self, caplog):
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

        # NEW: Check that async user ID logging is present
        log_messages = [record.message for record in caplog.records]
        validation_logs = [msg for msg in log_messages if "Async validation request - user_type=" in msg]
        assert len(validation_logs) > 0, "Expected to find user ID logging in async validation request"

        # Check that user type and IDs are logged correctly for anonymous user
        user_id_log = validation_logs[0]
        assert "user_type=anonymous" in user_id_log
        assert "paid_user_id=N/A" in user_id_log
        assert "free_user_id=N/A" in user_id_log
        assert "style=apa7" in user_id_log

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

    def test_async_job_returns_partial_when_free_limit_exceeded(self):
        """Test that async job returns partial results when free tier has already used limit."""
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

        # Wait for job to complete with partial results
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

        # Should be completed with partial results (all citations locked)
        assert data["status"] == "completed"
        assert "results" in data
        result = data["results"]
        assert result["partial"] is True
        assert result["citations_checked"] == 0
        assert result["citations_remaining"] >= 1
        assert len(result["results"]) == 0  # Empty results array

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
        assert results["free_used_total"] == 5  # Up to free limit
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

    def test_free_tier_limit_returns_accurate_citation_count(self):
        """Test that free tier limit endpoint counts citations accurately using LLM."""
        import base64

        # Setup: User at free tier limit
        request_data = {
            "citations": (
                "<p>Smith, J. (2023). First citation. <em>Journal</em>, 1(1), 1-10.</p>"
                "<p>Doe, J. (2023). Second citation. <em>Journal</em>, 1(2), 11-20.</p>"
                "<p>Brown, A. (2023). Third citation. <em>Journal</em>, 1(3), 21-30.</p>"
            ),
            "style": "apa7"
        }
        # Encode free_used as base64 per API design
        free_used_header = base64.b64encode("10".encode('utf-8')).decode('utf-8')
        headers = {"X-Free-Used": free_used_header}  # At free tier limit

        # Create async job
        response = client.post("/api/validate/async", json=request_data, headers=headers)
        assert response.status_code == 200
        job_id = response.json()["job_id"]

        # Wait for job to complete
        import time
        max_wait = 60
        wait_time = 0
        result = None

        while wait_time < max_wait:
            response = client.get(f"/api/jobs/{job_id}")
            assert response.status_code == 200
            data = response.json()

            if data["status"] == "completed":
                result = data.get("results")  # API returns "results" not "result"
                break

            time.sleep(1)
            wait_time += 1

        # Verify job completed with partial results
        assert result is not None, "Job did not complete within timeout"
        assert result["partial"] is True, "Should return partial results"
        assert result["citations_checked"] == 0, "Should have 0 checked (at limit)"
        assert result["citations_remaining"] == 3, "Should accurately count 3 citations"
        assert len(result["results"]) == 0, "Should return empty results array"
        assert result["free_used"] == 5, "Should show free tier limit reached"

    def test_free_tier_limit_citation_count_fallback(self):
        """Test that citation counting falls back gracefully if LLM fails."""
        # This test verifies the fallback logic exists in the code
        import app
        import inspect

        # Get function source code
        source = inspect.getsource(app.process_validation_job)

        # Verify fallback logic exists for citation counting
        assert "try:" in source, "Should have try-except for LLM call"
        assert "except Exception" in source, "Should catch exceptions"
        assert "split('\\n\\n')" in source, "Should have fallback parsing"
        assert "Fallback citation count" in source or "fallback" in source.lower(), \
            "Should log fallback behavior"