import pytest
from backend.database import add_credits


def test_credits_balance_existing_user(client):
    """Test returns correct balance for existing user."""
    # Add a test user with 100 credits
    add_credits("test-token-123", 100, "order-1")

    response = client.get("/api/credits?token=test-token-123")

    assert response.status_code == 200
    data = response.json()
    assert data["token"] == "test-token-123"
    assert data["credits"] == 100


def test_credits_balance_nonexistent_user(client):
    """Test returns 0 for non-existent token."""
    response = client.get("/api/credits?token=nonexistent-token")

    assert response.status_code == 200
    data = response.json()
    assert data["token"] == "nonexistent-token"
    assert data["credits"] == 0


def test_credits_balance_missing_token(client):
    """Test returns error if token parameter missing."""
    response = client.get("/api/credits")

    assert response.status_code == 422  # FastAPI validation error for missing query param


def test_credits_balance_empty_token(client):
    """Test returns error if token parameter is empty."""
    response = client.get("/api/credits?token=")

    assert response.status_code == 400
    assert "Token required" in response.json()["detail"]


def test_credits_balance_user_with_zero_credits(client):
    """Test returns 0 for user with zero credits."""
    # Create user with 0 initial credits
    add_credits("zero-credit-user", 0, "order-zero")

    response = client.get("/api/credits?token=zero-credit-user")

    assert response.status_code == 200
    data = response.json()
    assert data["token"] == "zero-credit-user"
    assert data["credits"] == 0


def test_credits_balance_after_adding_more(client):
    """Test returns updated balance after adding more credits."""
    # Start with 50 credits
    add_credits("increment-test", 50, "order-1")

    # Verify initial balance
    response = client.get("/api/credits?token=increment-test")
    assert response.json()["credits"] == 50

    # Add 25 more credits
    add_credits("increment-test", 25, "order-2")

    # Verify updated balance
    response = client.get("/api/credits?token=increment-test")
    assert response.status_code == 200
    data = response.json()
    assert data["token"] == "increment-test"
    assert data["credits"] == 75