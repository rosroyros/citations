import pytest
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)


def test_health_check_returns_200():
    """Test that health check endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_validate_endpoint_accepts_json():
    """Test that POST /api/validate accepts JSON and returns 200."""
    payload = {
        "citations": "Smith, J. (2020). Test article. Journal of Testing, 1(1), 1-10.",
        "style": "apa7"
    }
    response = client.post("/api/validate", json=payload)
    assert response.status_code == 200


def test_validate_endpoint_returns_results():
    """Test that endpoint returns validation results with proper structure."""
    payload = {
        "citations": "Smith, J. (2020). First article. Journal of Testing, 1(1), 1-10.\n\nJones, A. (2021). Second article. Testing Quarterly, 2(2), 20-30.",
        "style": "apa7"
    }
    response = client.post("/api/validate", json=payload)
    data = response.json()

    # Should return results with proper structure
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) >= 1  # LLM should detect at least one citation
