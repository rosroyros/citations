import pytest
import tempfile
import os
import json
from unittest.mock import AsyncMock, patch, MagicMock
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import DB_PATH
from fastapi.testclient import TestClient
from app import app

# Mock the Polar SDK checkout response
MOCK_CHECKOUT_RESPONSE = {
    "id": "checkout_123",
    "url": "https://checkout.polar.sh/test-checkout-url",
    "success_url": "http://localhost:5173/success?token=test-token-123",
    "product_id": "ead5b66b-4f95-49fa-ad41-87c081ea977a",
    "metadata": {"token": "test-token-123"}
}


def setup_test_db():
    """Set up a temporary database for testing"""
    test_db_path = tempfile.mktemp(suffix='.db')

    # Override the DB_PATH for testing
    original_db_path = DB_PATH
    import database
    database.DB_PATH = test_db_path

    return test_db_path, original_db_path


def cleanup_test_db(test_db_path, original_db_path):
    """Clean up test database and restore DB_PATH"""
    import database
    database.DB_PATH = original_db_path

    if os.path.exists(test_db_path):
        os.unlink(test_db_path)


@patch('app.polar')
def test_checkout_creates_uuid_if_no_token_provided(mock_polar):
    """Test that checkout generates UUID if no token provided"""
    test_db_path, original_db_path = setup_test_db()

    try:
        # Mock Polar checkout creation
        mock_polar.checkouts.create = AsyncMock(return_value=MOCK_CHECKOUT_RESPONSE)

        # Initialize database (for context, though not directly used in checkout)
        from database import init_db
        init_db()

        client = TestClient(app)

        # Test without providing token
        response = client.post("/api/create-checkout", json={})

        assert response.status_code == 200
        data = response.json()

        # Check that token was generated (UUID format)
        assert "token" in data
        assert len(data["token"]) == 36  # UUID length
        assert data["token"].count('-') == 4  # UUID format

        # Check checkout URL is returned
        assert "checkout_url" in data
        assert data["checkout_url"] == "https://checkout.polar.sh/test-checkout-url"

        # Verify Polar API was called with correct parameters
        mock_polar.checkouts.create.assert_called_once()
        call_args = mock_polar.checkouts.create.call_args[0][0]

        assert call_args["product_id"] == "ead5b66b-4f95-49fa-ad41-87c081ea977a"
        assert "success_url" in call_args
        assert "metadata" in call_args
        assert "token" in call_args["metadata"]

    finally:
        cleanup_test_db(test_db_path, original_db_path)


@patch('app.polar')
def test_checkout_uses_existing_token_if_provided(mock_polar):
    """Test that checkout uses existing token if provided"""
    test_db_path, original_db_path = setup_test_db()

    try:
        # Mock Polar checkout creation
        mock_polar.checkouts.create = AsyncMock(return_value=MOCK_CHECKOUT_RESPONSE)

        # Initialize database
        from database import init_db
        init_db()

        client = TestClient(app)
        existing_token = "existing-user-token-456"

        # Test with existing token
        response = client.post("/api/create-checkout", json={"token": existing_token})

        assert response.status_code == 200
        data = response.json()

        # Check that provided token is used
        assert data["token"] == existing_token
        assert "checkout_url" in data

        # Verify Polar API was called with the existing token
        mock_polar.checkouts.create.assert_called_once()
        call_args = mock_polar.checkouts.create.call_args[0][0]
        assert call_args["metadata"]["token"] == existing_token

    finally:
        cleanup_test_db(test_db_path, original_db_path)


@patch('app.polar')
def test_checkout_handles_polar_api_error(mock_polar):
    """Test that checkout handles Polar API errors gracefully"""
    test_db_path, original_db_path = setup_test_db()

    try:
        # Mock Polar API error
        mock_polar.checkouts.create = AsyncMock(side_effect=Exception("Polar API Error"))

        # Initialize database
        from database import init_db
        init_db()

        client = TestClient(app)

        # Test checkout with API error
        response = client.post("/api/create-checkout", json={})

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    finally:
        cleanup_test_db(test_db_path, original_db_path)


@patch('app.polar')
def test_checkout_invalid_credentials_error(mock_polar):
    """Test that checkout handles Polar authentication errors"""
    test_db_path, original_db_path = setup_test_db()

    try:
        # Mock Polar auth error
        from polar_sdk import PolarError
        mock_polar.checkouts.create = AsyncMock(side_effect=PolarError("Authentication failed"))

        # Initialize database
        from database import init_db
        init_db()

        client = TestClient(app)

        # Test checkout with auth error
        response = client.post("/api/create-checkout", json={})

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    finally:
        cleanup_test_db(test_db_path, original_db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])