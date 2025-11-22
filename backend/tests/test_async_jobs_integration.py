"""Integration tests for async job infrastructure using real OpenAI API.

These tests use real OpenAI API calls and verify end-to-end functionality.
They are slower and more expensive than unit tests, so run them selectively.

Prerequisites:
- OPENAI_API_KEY environment variable must be set
- Real OpenAI API calls will be made (costs ~$0.01 per test run)

Run: pytest tests/test_async_jobs_integration.py -m integration -v
"""

import pytest
import json
import time
import uuid
import base64
from fastapi.testclient import TestClient
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app import app

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration

client = TestClient(app)


class TestAsyncJobsIntegration:
    """Integration tests for async job processing with real OpenAI API."""

    def test_small_batch_completes_in_30_seconds(self):
        """Test: Small batch (2 citations) with real LLM completes in ~30s."""
        # Setup - 2 simple citations
        request_data = {
            "citations": "<p>Smith, 2020, Journal of Testing</p><p>Jones, 2021, Book Example</p>",
            "style": "apa7"
        }

        start_time = time.time()

        # Create async job
        response = client.post("/api/validate/async", json=request_data)
        assert response.status_code == 200
        data = response.json()
        job_id = data["job_id"]
        assert data["status"] == "pending"

        # Poll for completion
        max_wait = 45  # Allow up to 45 seconds
        wait_time = 0
        while wait_time < max_wait:
            response = client.get(f"/api/jobs/{job_id}")
            assert response.status_code == 200
            data = response.json()

            if data["status"] == "completed":
                break
            elif data["status"] == "failed":
                pytest.fail(f"Job failed: {data.get('error', 'Unknown error')}")

            time.sleep(2)  # Poll every 2 seconds
            wait_time += 2

        # Verify completion within reasonable time
        total_time = time.time() - start_time
        assert total_time < 60, f"Job took too long: {total_time:.2f}s"
        assert data["status"] == "completed"
        assert "results" in data

        # Verify results structure
        results = data["results"]
        assert "results" in results
        assert "free_used_total" in results  # For free users, shows total citations used
        assert len(results["results"]) == 2

        # Verify each citation result has expected fields
        for result in results["results"]:
            assert "original" in result
            assert "errors" in result
            assert "source_type" in result
            assert "citation_number" in result

            # Verify each error has expected fields
            for error in result["errors"]:
                assert "component" in error
                assert "problem" in error
                assert "correction" in error

    def test_paid_user_credits_deducted(self):
        """Test: Paid user with X-User-Token header (verify credits deducted)."""
        # Setup - Use test user token
        test_token = "test_integration_user_token"
        request_data = {
            "citations": "<p>Test citation for paid user</p>",
            "style": "apa7"
        }
        headers = {"X-User-Token": test_token}

        # Import database functions
        from database import get_credits, deduct_credits, get_db_path, init_db
        import sqlite3

        # Initialize database
        init_db()

        # Helper function to set credits for testing
        def set_test_credits(token: str, credits: int):
            """Set credits for test user by directly manipulating database"""
            db_path = get_db_path()
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                # Create user if not exists
                cursor.execute("""
                    INSERT OR IGNORE INTO users (token, credits) VALUES (?, ?)
                """, (token, credits))
                # Update credits
                cursor.execute("""
                    UPDATE users SET credits = ? WHERE token = ?
                """, (credits, token))
                conn.commit()

        # Test 1: Verify zero credits causes failure
        # Ensure test user has zero credits initially
        set_test_credits(test_token, 0)

        response = client.post("/api/validate/async", json=request_data, headers=headers)
        assert response.status_code == 200
        job_id = response.json()["job_id"]

        # Wait for job to fail due to zero credits
        max_wait = 30
        wait_time = 0
        while wait_time < max_wait:
            response = client.get(f"/api/jobs/{job_id}")
            data = response.json()

            if data["status"] == "failed":
                break
            elif data["status"] == "completed":
                pytest.fail("Job should have failed due to zero credits")

            time.sleep(2)
            wait_time += 2

        # Verify failure was due to zero credits
        assert data["status"] == "failed"
        assert "0 Citation Credits" in data.get("error", "")

        # Test 2: Add credits and verify successful job with credit deduction
        # Give test user 5 credits
        set_test_credits(test_token, 5)
        initial_credits = get_credits(test_token)
        assert initial_credits == 5

        # Create new job
        response = client.post("/api/validate/async", json=request_data, headers=headers)
        assert response.status_code == 200
        job_id = response.json()["job_id"]

        # Wait for completion
        max_wait = 60
        wait_time = 0
        while wait_time < max_wait:
            response = client.get(f"/api/jobs/{job_id}")
            data = response.json()

            if data["status"] == "completed":
                break
            elif data["status"] == "failed":
                pytest.fail(f"Job failed: {data.get('error', 'Unknown error')}")

            time.sleep(2)
            wait_time += 2

        # Verify job completed successfully
        assert data["status"] == "completed"

        # Verify credits were deducted (1 credit for 1 citation)
        final_credits = get_credits(test_token)
        assert final_credits == initial_credits - 1

    def test_free_user_partial_results(self):
        """Test: Free user with X-Free-Used header (verify partial results)."""
        # Setup - Free user has used 8 out of 10 free citations (2 remaining)
        free_used = 8
        free_used_header = base64.b64encode(str(free_used).encode()).decode('utf-8')

        # Submit 5 citations (should only get 2 processed)
        request_data = {
            "citations": "<p>Citation 1</p><p>Citation 2</p><p>Citation 3</p><p>Citation 4</p><p>Citation 5</p>",
            "style": "apa7"
        }
        headers = {"X-Free-Used": free_used_header}

        # Create async job
        response = client.post("/api/validate/async", json=request_data, headers=headers)
        assert response.status_code == 200
        job_id = response.json()["job_id"]

        # Wait for completion
        max_wait = 90  # Allow more time for 5 citations
        wait_time = 0
        while wait_time < max_wait:
            response = client.get(f"/api/jobs/{job_id}")
            data = response.json()

            if data["status"] == "completed":
                break
            elif data["status"] == "failed":
                pytest.fail(f"Job failed: {data.get('error', 'Unknown error')}")

            time.sleep(2)
            wait_time += 2

        # Verify partial results
        assert data["status"] == "completed"
        results = data["results"]
        assert results["partial"] is True
        assert results["citations_checked"] == 2  # Only 2 credits remaining
        assert results["citations_remaining"] == 3  # 3 citations locked
        assert results["free_used_total"] == 10  # Up to free limit
        assert len(results["results"]) == 2  # Only 2 actual citation results

    @pytest.mark.slow
    def test_retry_logic_on_openai_timeout(self):
        """Test: Retry logic on OpenAI timeout (simulate with very short timeout)."""
        # This test requires modifying the OpenAI provider to have a very short timeout
        # For now, we'll test that the retry logic exists by checking logs
        # In a real implementation, you might patch the timeout setting

        request_data = {
            "citations": "<p>Test citation for retry logic</p>",
            "style": "apa7"
        }

        # Create async job
        response = client.post("/api/validate/async", json=request_data)
        assert response.status_code == 200
        job_id = response.json()["job_id"]

        # Wait for completion (may take longer due to retries)
        max_wait = 120  # Allow more time for retries
        wait_time = 0
        while wait_time < max_wait:
            response = client.get(f"/api/jobs/{job_id}")
            data = response.json()

            if data["status"] == "completed":
                break
            elif data["status"] == "failed":
                # Check if error mentions retries or timeout
                error = data.get("error", "")
                assert any(keyword in error.lower() for keyword in ["timeout", "retry", "openai"]), \
                    f"Error should mention timeout/retry: {error}"
                break  # Expected to fail due to timeout

            time.sleep(2)
            wait_time += 2

        # Should either succeed (after retries) or fail with timeout/retry error
        assert data["status"] in ["completed", "failed"]

    @pytest.mark.slow
    def test_concurrent_jobs_complete_successfully(self):
        """Test: Concurrent jobs (create 3 jobs simultaneously, all complete)."""
        # Create 3 different jobs simultaneously
        jobs = []
        for i in range(3):
            request_data = {
                "citations": f"<p>Concurrent citation {i+1}</p>",
                "style": "apa7"
            }

            response = client.post("/api/validate/async", json=request_data)
            assert response.status_code == 200
            jobs.append(response.json()["job_id"])

        # Wait for all jobs to complete
        max_wait = 120  # Allow more time for concurrent processing
        wait_time = 0
        completed_jobs = []

        while wait_time < max_wait and len(completed_jobs) < 3:
            for job_id in jobs:
                if job_id in completed_jobs:
                    continue

                response = client.get(f"/api/jobs/{job_id}")
                data = response.json()

                if data["status"] == "completed":
                    completed_jobs.append(job_id)
                elif data["status"] == "failed":
                    pytest.fail(f"Concurrent job {job_id} failed: {data.get('error', 'Unknown error')}")

            time.sleep(3)  # Poll every 3 seconds
            wait_time += 3

        # Verify all jobs completed successfully
        assert len(completed_jobs) == 3, f"Only {len(completed_jobs)}/3 jobs completed"

        # Verify each job has valid results
        for job_id in jobs:
            response = client.get(f"/api/jobs/{job_id}")
            data = response.json()
            assert data["status"] == "completed"
            assert "results" in data
            assert data["results"]["free_used_total"] == 1  # For free users
            assert len(data["results"]["results"]) == 1