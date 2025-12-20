import pytest
import tempfile
import os
import json
from unittest.mock import AsyncMock, patch, MagicMock
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from app import app

# Mock the Polar SDK checkout response object
class MockCheckoutResponse:
    def __init__(self):
        self.id = "checkout_123"
        self.url = "https://checkout.polar.sh/test-checkout-url"
        self.embed_origin = "http://localhost:5173"
        self.product_id = "ead5b66b-4f95-49fa-ad41-87c081ea977a"
        self.metadata = {"token": "test-token-123"}

MOCK_CHECKOUT_RESPONSE = MockCheckoutResponse()


def setup_test_db():
    """Set up a temporary database for testing using TEST_DB_PATH env var"""
    test_db_path = tempfile.mktemp(suffix='.db')
    
    # Set the test database path via environment variable
    original_test_db_path = os.environ.get('TEST_DB_PATH')
    os.environ['TEST_DB_PATH'] = test_db_path
    
    # Ensure MOCK_LLM is false so tests exercise the Polar API path
    original_mock_llm = os.environ.get('MOCK_LLM')
    os.environ['MOCK_LLM'] = 'false'
    
    # Set FRONTEND_URL for embed_origin
    original_frontend_url = os.environ.get('FRONTEND_URL')
    os.environ['FRONTEND_URL'] = 'http://localhost:5173'
    
    return test_db_path, original_test_db_path, original_mock_llm, original_frontend_url


def cleanup_test_db(test_db_path, original_test_db_path, original_mock_llm, original_frontend_url):
    """Clean up test database and restore all env vars"""
    # Restore TEST_DB_PATH
    if original_test_db_path is not None:
        os.environ['TEST_DB_PATH'] = original_test_db_path
    elif 'TEST_DB_PATH' in os.environ:
        del os.environ['TEST_DB_PATH']
    
    # Restore MOCK_LLM
    if original_mock_llm is not None:
        os.environ['MOCK_LLM'] = original_mock_llm
    elif 'MOCK_LLM' in os.environ:
        del os.environ['MOCK_LLM']
    
    # Restore FRONTEND_URL
    if original_frontend_url is not None:
        os.environ['FRONTEND_URL'] = original_frontend_url
    elif 'FRONTEND_URL' in os.environ:
        del os.environ['FRONTEND_URL']

    if os.path.exists(test_db_path):
        os.unlink(test_db_path)


@patch('app.polar')
def test_checkout_creates_uuid_if_no_token_provided(mock_polar):
    """Test that checkout generates UUID if no token provided"""
    test_db_path, orig_db_path, orig_mock_llm, orig_frontend_url = setup_test_db()

    try:
        # Mock Polar checkout creation (use MagicMock, not AsyncMock since create() is sync)
        mock_polar.checkouts.create = MagicMock(return_value=MOCK_CHECKOUT_RESPONSE)

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
        call_args = mock_polar.checkouts.create.call_args.kwargs['request']

        assert "products" in call_args  # Note: API uses 'products' list, not 'product_id'
        assert "embed_origin" in call_args
        assert "metadata" in call_args
        assert "token" in call_args["metadata"]

    finally:
        cleanup_test_db(test_db_path, orig_db_path, orig_mock_llm, orig_frontend_url)


@patch('app.polar')
def test_checkout_uses_existing_token_if_provided(mock_polar):
    """Test that checkout uses existing token if provided"""
    test_db_path, orig_db_path, orig_mock_llm, orig_frontend_url = setup_test_db()

    try:
        # Mock Polar checkout creation (use MagicMock, not AsyncMock since create() is sync)
        mock_polar.checkouts.create = MagicMock(return_value=MOCK_CHECKOUT_RESPONSE)

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
        call_args = mock_polar.checkouts.create.call_args.kwargs['request']
        assert call_args["metadata"]["token"] == existing_token

    finally:
        cleanup_test_db(test_db_path, orig_db_path, orig_mock_llm, orig_frontend_url)


@patch('app.polar')
def test_checkout_handles_polar_api_error(mock_polar):
    """Test that checkout handles Polar API errors gracefully"""
    test_db_path, orig_db_path, orig_mock_llm, orig_frontend_url = setup_test_db()

    try:
        # Mock Polar API error (use MagicMock since create() is sync)
        mock_polar.checkouts.create = MagicMock(side_effect=Exception("Polar API Error"))

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
        cleanup_test_db(test_db_path, orig_db_path, orig_mock_llm, orig_frontend_url)


@patch('app.polar')
def test_checkout_invalid_credentials_error(mock_polar):
    """Test that checkout handles Polar authentication errors"""
    test_db_path, orig_db_path, orig_mock_llm, orig_frontend_url = setup_test_db()

    try:
        # Mock Polar auth error - use generic Exception since PolarError requires raw_response
        mock_polar.checkouts.create = MagicMock(side_effect=Exception("Authentication failed"))

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
        cleanup_test_db(test_db_path, orig_db_path, orig_mock_llm, orig_frontend_url)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])