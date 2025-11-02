import pytest
import tempfile
import os
from fastapi.testclient import TestClient

def setup_test_client():
    """Create a fresh test client with isolated database for each test."""
    # Create temporary database for this test
    test_db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    test_db_path = test_db_file.name
    test_db_file.close()

    # Set environment variable for database path
    os.environ['TEST_DB_PATH'] = test_db_path

    # Import modules after setting environment variable
    from backend.app import app
    from backend.database import init_db, add_credits

    # Initialize fresh database
    init_db()

    return TestClient(app), test_db_path, add_credits


def test_credits_balance_existing_user():
    """Test returns correct balance for existing user."""
    client, test_db_path, add_credits = setup_test_client()

    # Add a test user with 100 credits
    add_credits("test-token-123", 100, "order-1")

    response = client.get("/api/credits?token=test-token-123")

    assert response.status_code == 200
    data = response.json()
    assert data["token"] == "test-token-123"
    assert data["credits"] == 100

    # Cleanup
    if os.path.exists(test_db_path):
        os.unlink(test_db_path)


def test_credits_balance_nonexistent_user():
    """Test returns 0 for non-existent token."""
    client, test_db_path, add_credits = setup_test_client()

    response = client.get("/api/credits?token=nonexistent-token")

    assert response.status_code == 200
    data = response.json()
    assert data["token"] == "nonexistent-token"
    assert data["credits"] == 0

    # Cleanup
    if os.path.exists(test_db_path):
        os.unlink(test_db_path)


def test_credits_balance_missing_token():
    """Test returns error if token parameter missing."""
    client, test_db_path, add_credits = setup_test_client()

    response = client.get("/api/credits")

    assert response.status_code == 422  # FastAPI validation error for missing query param

    # Cleanup
    if os.path.exists(test_db_path):
        os.unlink(test_db_path)


def test_credits_balance_empty_token():
    """Test returns error if token parameter is empty."""
    client, test_db_path, add_credits = setup_test_client()

    response = client.get("/api/credits?token=")

    assert response.status_code == 400
    assert "Token required" in response.json()["detail"]

    # Cleanup
    if os.path.exists(test_db_path):
        os.unlink(test_db_path)


def test_credits_balance_user_with_zero_credits():
    """Test returns 0 for user with zero credits."""
    client, test_db_path, add_credits = setup_test_client()

    # Create user with 0 initial credits
    add_credits("zero-credit-user", 0, "order-zero")

    response = client.get("/api/credits?token=zero-credit-user")

    assert response.status_code == 200
    data = response.json()
    assert data["token"] == "zero-credit-user"
    assert data["credits"] == 0

    # Cleanup
    if os.path.exists(test_db_path):
        os.unlink(test_db_path)


def test_credits_balance_after_adding_more():
    """Test returns updated balance after adding more credits."""
    client, test_db_path, add_credits = setup_test_client()

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

    # Cleanup
    if os.path.exists(test_db_path):
        os.unlink(test_db_path)