import pytest
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)


def test_health_check_returns_200():
    """Test that health check endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ===== Chicago Styles Endpoint Tests =====


def test_styles_includes_chicago_when_enabled():
    """Chicago should appear when CHICAGO_ENABLED=true."""
    # Note: CHICAGO_ENABLED is set at module import time,
    # so we verify the expected behavior based on current env
    response = client.get("/api/styles")
    assert response.status_code == 200
    data = response.json()

    # When CHICAGO_ENABLED=true in env, chicago17 should be present
    import os
    if os.getenv("CHICAGO_ENABLED", "false").lower() == "true":
        assert "chicago17" in data["styles"]
        assert data["styles"]["chicago17"] == "Chicago 17th (Notes-Bib)"
    else:
        # When disabled, chicago17 should not be present
        assert "chicago17" not in data["styles"]


def test_styles_always_includes_apa():
    """APA7 should always be available regardless of feature flags."""
    response = client.get("/api/styles")
    assert response.status_code == 200
    data = response.json()
    assert "apa7" in data["styles"]
    assert data["styles"]["apa7"] == "APA 7th Edition"


def test_styles_returns_default():
    """Styles endpoint should return default style."""
    response = client.get("/api/styles")
    assert response.status_code == 200
    data = response.json()
    assert "default" in data
    assert data["default"] == "apa7"


# ===== Chicago Validation Tests =====


def test_validate_accepts_chicago17_style():
    """Validation endpoint should accept chicago17 style."""
    payload = {
        "citations": "Morrison, Toni. Beloved. New York: Knopf, 1987.",
        "style": "chicago17"
    }
    response = client.post("/api/validate/async", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert isinstance(data["job_id"], str)


def test_validate_rejects_invalid_chicago_style():
    """Validation should reject typos in style name."""
    payload = {
        "citations": "Some citation",
        "style": "chicago"  # Missing '17'
    }
    response = client.post("/api/validate/async", json=payload)
    assert response.status_code == 422  # Validation error


def test_validate_rejects_chicago16_style():
    """Validation should reject Chicago 16 (not supported)."""
    payload = {
        "citations": "Some citation",
        "style": "chicago16"
    }
    response = client.post("/api/validate/async", json=payload)
    assert response.status_code == 422  # Validation error


def test_chicago_validation_with_multiple_citations():
    """Chicago validation should handle multiple citations."""
    payload = {
        "citations": """Morrison, Toni. Beloved. New York: Knopf, 1987.

Woolf, Virginia. Mrs Dalloway. London: Hogarth Press, 1925.""",
        "style": "chicago17"
    }
    response = client.post("/api/validate/async", json=payload)
    assert response.status_code == 200
    assert "job_id" in response.json()
