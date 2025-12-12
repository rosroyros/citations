import pytest
import tempfile
import os
import json
from unittest.mock import AsyncMock, patch, MagicMock
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import add_credits
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


@patch('app.validate_event')
def test_webhook_valid_signature_accepted(mock_validate_event, client):
    """Test that webhook with valid signature is accepted"""
    # Mock signature verification as successful - return a mock webhook payload
    from polar_sdk.models.webhookordercreatedpayload import WebhookOrderCreatedPayload

    mock_webhook = MagicMock(spec=WebhookOrderCreatedPayload)
    mock_webhook.data = MagicMock()
    mock_webhook.data.id = "order_abc123"
    mock_webhook.data.metadata = {"token": "user-token-xyz"}
    mock_validate_event.return_value = mock_webhook

    # Send valid webhook
    headers = {
        "webhook-signature": "valid_signature",
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
        key.lower() == 'webhook-signature' and value == "valid_signature"
        for key, value in header_dict.items()
    )
    assert signature_found, f"webhook-signature header not found in headers: {list(header_dict.keys())}"

    # Check that secret was passed
    assert call_args.kwargs['secret'] == os.getenv('POLAR_WEBHOOK_SECRET')


@patch('app.validate_event')
def test_webhook_invalid_signature_rejected(mock_validate_event, client):
    """Test that webhook with invalid signature is rejected"""
    # Mock signature verification as failed - raise exception
    from polar_sdk.webhooks import WebhookVerificationError
    mock_validate_event.side_effect = WebhookVerificationError("Invalid signature")

    # Send webhook with invalid signature
    headers = {
        "webhook-signature": "invalid_signature",
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


@patch('app.validate_event')
def test_webhook_order_created_grants_credits(mock_validate_event, client):
    """Test that order.created event grants 1,000 credits"""
    # Mock signature verification as successful - return a mock webhook payload
    # that appears to be an instance of WebhookOrderCreatedPayload
    from polar_sdk.models.webhookordercreatedpayload import WebhookOrderCreatedPayload

    mock_webhook = MagicMock(spec=WebhookOrderCreatedPayload)
    mock_webhook.data = MagicMock()
    mock_webhook.data.id = "order_abc123"
    mock_webhook.data.metadata = {"token": "user-token-xyz"}
    mock_validate_event.return_value = mock_webhook

    # Send order.created webhook
    headers = {
        "webhook-signature": "valid_signature",
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


@patch('app.validate_event')
def test_webhook_checkout_updated_completed_grants_credits(mock_validate_event, client):
    """Test that checkout.updated with completed status grants credits"""
    # Mock signature verification as successful - return a mock webhook payload
    # that appears to be an instance of WebhookCheckoutUpdatedPayload
    from polar_sdk.models.webhookcheckoutupdatedpayload import WebhookCheckoutUpdatedPayload

    mock_webhook = MagicMock(spec=WebhookCheckoutUpdatedPayload)
    mock_webhook.data = MagicMock()
    mock_webhook.data.status = "completed"
    mock_webhook.data.order_id = "order_def456"
    mock_webhook.data.metadata = {"token": "user-token-789"}
    mock_webhook.data.amount_cents = 89900  # $8.99 in cents
    # Add mock line item with product_id and price_amount
    mock_line_item = MagicMock()
    mock_line_item.product_id = "fe7b0260-e411-4f9a-87c8-0856bf1d8b95"  # 2000 credits product
    mock_line_item.price_amount = 99900  # $9.99 in cents
    mock_webhook.data.line_items = [mock_line_item]
    mock_validate_event.return_value = mock_webhook

    # Send checkout.updated webhook with completed status
    headers = {
        "webhook-signature": "valid_signature",
        "Content-Type": "application/json"
    }
    response = client.post(
        "/api/polar-webhook",
        json=MOCK_CHECKOUT_WEBHOOK,
        headers=headers
    )

    assert response.status_code == 200

    # Check that credits were granted (2000 credits for $9.99 product)
    from database import get_credits
    credits = get_credits("user-token-789")
    assert credits == 2000


@patch('app.validate_event')
def test_webhook_duplicate_order_id_rejected(mock_validate_event, client):
    """Test that duplicate webhook with same order_id doesn't grant credits twice"""
    # Mock signature verification as successful - return a mock webhook payload
    from polar_sdk.models.webhookordercreatedpayload import WebhookOrderCreatedPayload

    mock_webhook = MagicMock(spec=WebhookOrderCreatedPayload)
    mock_webhook.data = MagicMock()
    mock_webhook.data.id = "order_abc123"
    mock_webhook.data.metadata = {"token": "user-token-xyz"}
    mock_validate_event.return_value = mock_webhook

    # Pre-add credits for the order to simulate it was already processed
    add_credits("user-token-xyz", 1000, "order_abc123")

    # Send duplicate webhook
    headers = {
        "webhook-signature": "valid_signature",
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


@patch('app.validate_event')
def test_webhook_non_order_event_ignored(mock_validate_event, client):
    """Test that non-order events are ignored"""
    # Mock signature verification as successful - return a mock webhook payload
    # that is NOT one of the expected types
    mock_webhook = MagicMock()
    mock_validate_event.return_value = mock_webhook

    # Send non-order webhook
    headers = {
        "webhook-signature": "valid_signature",
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


@patch('app.validate_event')
def test_webhook_missing_signature_header(mock_validate_event, client):
    """Test that webhook without signature header is rejected"""
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


@patch('app.validate_event')
def test_webhook_checkout_updated_non_completed_ignored(mock_validate_event, client):
    """Test that checkout.updated with non-completed status is ignored"""
    # Mock signature verification as successful - return a mock webhook payload
    from polar_sdk.models.webhookcheckoutupdatedpayload import WebhookCheckoutUpdatedPayload

    mock_webhook = MagicMock(spec=WebhookCheckoutUpdatedPayload)
    mock_webhook.data = MagicMock()
    mock_webhook.data.status = "pending"
    mock_validate_event.return_value = mock_webhook

    # Create webhook with non-completed status
    non_completed_webhook = MOCK_CHECKOUT_WEBHOOK.copy()
    non_completed_webhook["data"]["status"] = "pending"

    # Send webhook with non-completed status
    headers = {
        "webhook-signature": "valid_signature",
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])