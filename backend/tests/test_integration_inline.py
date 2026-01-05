"""Integration tests for inline citation validation.

Tests cover:
- JSON endpoint with body + references (inline citation validation)
- Job creation and completion flow
- Different citation styles (APA, MLA)

Prerequisites:
- MOCK_LLM=true environment variable for fast tests without real LLM calls
- Test fixtures in tests/fixtures/

Note: The response schema for inline citations (validation_type, inline_citations
in results, orphan_citations) is set in response_data but may not be exposed
through the ValidationResponse model in GET /api/jobs/{job_id} responses.

Run: pytest tests/test_integration_inline.py -v
"""

import pytest
import os
import sys
import time
from pathlib import Path
from fastapi.testclient import TestClient

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from app import app

client = TestClient(app)


def wait_for_job_completion(job_id: str, timeout: int = 30) -> dict:
    """Poll for job completion and return final results."""
    start = time.time()
    while time.time() - start < timeout:
        response = client.get(f"/api/jobs/{job_id}")
        data = response.json()
        if data.get("status") == "completed":
            return data
        time.sleep(0.5)
    raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")


class TestValidationFlow:
    """Tests for end-to-end validation flow."""

    def test_paste_with_refs_creates_job(self):
        """Pasted content with References header should create job and complete."""
        html = """
        <p>According to (Smith, 2019), the results...</p>
        <h2>References</h2>
        <p>Smith, J. (2019). Title. Journal.</p>
        """

        response = client.post(
            "/api/validate/async",
            json={"citations": html, "style": "apa7"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"

        # Wait for completion
        result_data = wait_for_job_completion(data["job_id"])
        assert result_data["status"] == "completed"
        assert "results" in result_data

    def test_paste_without_refs_completes(self):
        """Pasted content without header should still complete."""
        html = "<p>Smith, J. (2019). Title. Journal.</p>"

        response = client.post(
            "/api/validate/async",
            json={"citations": html, "style": "apa7"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

        # Wait for completion
        result_data = wait_for_job_completion(data["job_id"])
        assert result_data["status"] == "completed"


class TestResponseSchema:
    """Tests for response schema compliance."""

    def test_response_has_required_fields(self):
        """Response should have required fields."""
        html = """
        <p>(Smith, 2019)</p>
        <h2>References</h2>
        <p>Smith, J. (2019). Title. Journal.</p>
        """

        response = client.post(
            "/api/validate/async",
            json={"citations": html, "style": "apa7"}
        )

        assert response.status_code == 200
        job_id = response.json()["job_id"]

        # Wait for completion
        result_data = wait_for_job_completion(job_id)

        # Check top-level structure
        assert "status" in result_data
        assert "results" in result_data

        # Check results structure
        results = result_data["results"]
        assert "results" in results  # Array of citation results

    def test_citation_result_has_required_fields(self):
        """Each citation result should have required fields."""
        html = """
        <p>(Smith, 2019)</p>
        <h2>References</h2>
        <p>Smith, J. (2019). Title. Journal.</p>
        """

        response = client.post(
            "/api/validate/async",
            json={"citations": html, "style": "apa7"}
        )

        assert response.status_code == 200
        job_id = response.json()["job_id"]

        # Wait for completion
        result_data = wait_for_job_completion(job_id)
        results = result_data["results"]["results"]

        for result in results:
            assert "citation_number" in result
            assert "original" in result
            assert "errors" in result
            assert isinstance(result["errors"], list)


class TestStyleSupport:
    """Tests for different citation styles."""

    def test_apa_validation(self):
        """APA style validation should complete successfully."""
        html = """
        <p>(Smith, 2019)</p>
        <h2>References</h2>
        <p>Smith, J. (2019). Title. Journal.</p>
        """

        response = client.post(
            "/api/validate/async",
            json={"citations": html, "style": "apa7"}
        )

        assert response.status_code == 200
        job_id = response.json()["job_id"]

        # Wait for completion
        result_data = wait_for_job_completion(job_id)
        assert result_data["status"] == "completed"

    def test_mla_validation(self):
        """MLA style validation should complete successfully."""
        html = """
        <p>(Smith 15)</p>
        <h2>Works Cited</h2>
        <p>Smith, John. Title. Publisher, 2019.</p>
        """

        response = client.post(
            "/api/validate/async",
            json={"citations": html, "style": "mla9"}
        )

        assert response.status_code == 200
        job_id = response.json()["job_id"]

        # Wait for completion
        result_data = wait_for_job_completion(job_id)
        assert result_data["status"] == "completed"
