import pytest
import tempfile
import os
import json
from unittest.mock import AsyncMock, patch, MagicMock
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import DB_PATH, add_credits
from fastapi.testclient import TestClient
from app import app

# Mock webhook payload for order.created event
MOCK_ORDER_WEBHOOK = {
    "type": "order.created",
    "data": {
        "id": "order_abc123",
        "amount": 899,
        "metadata": {
            "token": "user-token-xyz"
        }
    }
}

# Mock webhook payload for checkout.updated event (completed)
MOCK_CHECKOUT_WEBHOOK = {
    "type": "checkout.updated",
    "data": {
        "id": "checkout_456",
        "status": "completed",
        "order_id": "order_def456",
        "metadata": {
            "token": "user-token-789"
        }
    }
}

# Mock webhook payload for non-order event
MOCK_NON_ORDER_WEBHOOK = {
    "type": "user.created",
    "data": {
        "id": "user_789",
        "email": "test@example.com"
    }
}


def setup_test_db():
    """Set up a temporary database for testing"""
    from database import set_test_db_path, init_db

    test_db_path = tempfile.mktemp(suffix='.db')

    # Override the database path for testing
    set_test_db_path(test_db_path)

    # Initialize the test database
    init_db()

    return test_db_path


def cleanup_test_db(test_db_path):
    """Clean up test database and restore database path"""
    from database import reset_test_db_path

    reset_test_db_path()

    if os.path.exists(test_db_path):
        os.unlink(test_db_path)


@patch('app.validate_event')
def test_webhook_valid_signature_accepted(mock_validate_event):
    """Test that webhook with valid signature is accepted"""
    test_db_path = setup_test_db()

    try:
        # Mock signature verification as successful - return a mock webhook payload
        mock_webhook = MagicMock()
        mock_webhook.type = "order.created"
        mock_webhook.data.id = "order_abc123"
        mock_webhook.data.metadata.token = "user-token-xyz"
        mock_validate_event.return_value = mock_webhook

        client = TestClient(app)

        # Send valid webhook
        headers = {
            "X-Polar-Signature": "valid_signature",
            "Content-Type": "application/json"
        }
        response = client.post(
            "/api/polar-webhook",
            json=MOCK_ORDER_WEBHOOK,
            headers=headers
        )

        assert response.status_code == 200

        # Verify signature was checked with correct parameters
        call_args = mock_validate_event.call_args
        assert call_args is not None

        # Check that body was passed (as bytes)
        assert 'body' in call_args.kwargs
        assert json.loads(call_args.kwargs['body']) == MOCK_ORDER_WEBHOOK

        # Check that headers include the signature (may be lowercase)
        assert 'headers' in call_args.kwargs
        header_dict = call_args.kwargs['headers']
        # Check for signature header in various forms
        signature_found = any(
            key.lower() == 'x-polar-signature' and value == "valid_signature"
            for key, value in header_dict.items()
        )
        assert signature_found, f"X-Polar-Signature header not found in headers: {list(header_dict.keys())}"

        # Check that secret was passed
        assert call_args.kwargs['secret'] == os.getenv('POLAR_WEBHOOK_SECRET')

    finally:
        cleanup_test_db(test_db_path)


@patch('app.validate_event')
def test_webhook_invalid_signature_rejected(mock_validate_event):
    """Test that webhook with invalid signature is rejected"""
    test_db_path = setup_test_db()

    try:
        # Mock signature verification as failed - raise exception
        from polar_sdk.webhooks import WebhookVerificationError
        mock_validate_event.side_effect = WebhookVerificationError("Invalid signature")

        client = TestClient(app)

        # Send webhook with invalid signature
        headers = {
            "X-Polar-Signature": "invalid_signature",
            "Content-Type": "application/json"
        }
        response = client.post(
            "/api/polar-webhook",
            json=MOCK_ORDER_WEBHOOK,
            headers=headers
        )

        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "Invalid signature"

    finally:
        cleanup_test_db(test_db_path)


@patch('app.validate_event')
def test_webhook_order_created_grants_credits(mock_validate_event):
    """Test that order.created event grants 1,000 credits"""
    test_db_path = setup_test_db()

    try:
        # Mock signature verification as successful - return a mock webhook payload
        mock_webhook = MagicMock()
        mock_webhook.type = "order.created"
        mock_webhook.data.id = "order_abc123"
        mock_webhook.data.metadata.token = "user-token-xyz"
        mock_validate_event.return_value = mock_webhook

        client = TestClient(app)

        # Send order.created webhook
        headers = {
            "X-Polar-Signature": "valid_signature",
            "Content-Type": "application/json"
        }
        response = client.post(
            "/api/polar-webhook",
            json=MOCK_ORDER_WEBHOOK,
            headers=headers
        )

        assert response.status_code == 200

        # Check that credits were granted
        from database import get_credits
        credits = get_credits("user-token-xyz")
        assert credits == 1000

    finally:
        cleanup_test_db(test_db_path)


@patch('app.validate_event')
def test_webhook_checkout_updated_completed_grants_credits(mock_validate_event):
    """Test that checkout.updated with completed status grants credits"""
    test_db_path = setup_test_db()

    try:
        # Mock signature verification as successful - return a mock webhook payload
        mock_webhook = MagicMock()
        mock_webhook.type = "checkout.updated"
        mock_webhook.data.status = "completed"
        mock_webhook.data.order_id = "order_def456"
        mock_webhook.data.metadata.token = "user-token-789"
        mock_validate_event.return_value = mock_webhook

        client = TestClient(app)

        # Send checkout.updated webhook with completed status
        headers = {
            "X-Polar-Signature": "valid_signature",
            "Content-Type": "application/json"
        }
        response = client.post(
            "/api/polar-webhook",
            json=MOCK_CHECKOUT_WEBHOOK,
            headers=headers
        )

        assert response.status_code == 200

        # Check that credits were granted
        from database import get_credits
        credits = get_credits("user-token-789")
        assert credits == 1000

    finally:
        cleanup_test_db(test_db_path)


@patch('app.validate_event')
def test_webhook_duplicate_order_id_rejected(mock_validate_event):
    """Test that duplicate webhook with same order_id doesn't grant credits twice"""
    test_db_path = setup_test_db()

    try:
        # Mock signature verification as successful - return a mock webhook payload
        mock_webhook = MagicMock()
        mock_webhook.type = "order.created"
        mock_webhook.data.id = "order_abc123"
        mock_webhook.data.metadata.token = "user-token-xyz"
        mock_validate_event.return_value = mock_webhook

        # Pre-add credits for the order to simulate it was already processed
        add_credits("user-token-xyz", 1000, "order_abc123")

        client = TestClient(app)

        # Send duplicate webhook
        headers = {
            "X-Polar-Signature": "valid_signature",
            "Content-Type": "application/json"
        }
        response = client.post(
            "/api/polar-webhook",
            json=MOCK_ORDER_WEBHOOK,
            headers=headers
        )

        assert response.status_code == 200  # Still returns 200 to prevent Polar retries

        # Check that no additional credits were added (should still be 1000)
        from database import get_credits
        credits = get_credits("user-token-xyz")
        assert credits == 1000

    finally:
        cleanup_test_db(test_db_path)


@patch('app.validate_event')
def test_webhook_non_order_event_ignored(mock_validate_event):
    """Test that non-order events are ignored"""
    test_db_path = setup_test_db()

    try:
        # Mock signature verification as successful - return a mock webhook payload
        mock_webhook = MagicMock()
        mock_webhook.type = "user.created"
        mock_validate_event.return_value = mock_webhook

        client = TestClient(app)

        # Send non-order webhook
        headers = {
            "X-Polar-Signature": "valid_signature",
            "Content-Type": "application/json"
        }
        response = client.post(
            "/api/polar-webhook",
            json=MOCK_NON_ORDER_WEBHOOK,
            headers=headers
        )

        assert response.status_code == 200

        # Check that no credits were granted
        from database import get_credits
        credits = get_credits("nonexistent-token")
        assert credits == 0

    finally:
        cleanup_test_db(test_db_path)


@patch('app.validate_event')
def test_webhook_missing_signature_header(mock_validate_event):
    """Test that webhook without signature header is rejected"""
    test_db_path = setup_test_db()

    try:
        client = TestClient(app)

        # Send webhook without signature header
        response = client.post(
            "/api/polar-webhook",
            json=MOCK_ORDER_WEBHOOK
        )

        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "Invalid signature"

        # Signature verification should not be called
        mock_validate_event.assert_not_called()

    finally:
        cleanup_test_db(test_db_path)


@patch('app.validate_event')
def test_webhook_checkout_updated_non_completed_ignored(mock_validate_event):
    """Test that checkout.updated with non-completed status is ignored"""
    test_db_path = setup_test_db()

    try:
        # Mock signature verification as successful - return a mock webhook payload
        mock_webhook = MagicMock()
        mock_webhook.type = "checkout.updated"
        mock_webhook.data.status = "pending"
        mock_validate_event.return_value = mock_webhook

        # Create webhook with non-completed status
        non_completed_webhook = MOCK_CHECKOUT_WEBHOOK.copy()
        non_completed_webhook["data"]["status"] = "pending"

        client = TestClient(app)

        # Send webhook with non-completed status
        headers = {
            "X-Polar-Signature": "valid_signature",
            "Content-Type": "application/json"
        }
        response = client.post(
            "/api/polar-webhook",
            json=non_completed_webhook,
            headers=headers
        )

        assert response.status_code == 200

        # Check that no credits were granted
        from database import get_credits
        credits = get_credits("user-token-789")
        assert credits == 0

    finally:
        cleanup_test_db(test_db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])