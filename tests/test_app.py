import pytest
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)


def test_health_check_returns_200():
    """Test that health check endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
