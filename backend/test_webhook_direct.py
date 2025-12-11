#!/usr/bin/env python3
"""
Test webhook handlers directly by calling the functions.

This tests the tracking logic without needing to go through the webhook endpoint.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import handle_checkout_updated
from polar_sdk.models.webhookcheckoutupdatedpayload import WebhookCheckoutUpdatedPayload
from polar_sdk.models.webhookcheckoutupdatedpayloaddata import WebhookCheckoutUpdatedPayloadData
from polar_sdk.models.webhookcheckoutupdatedpayloaddatalineitem import WebhookCheckoutUpdatedPayloadDataLineItem
from polar_sdk.models.webhookcheckoutupdatedpayloaddatametadata import WebhookCheckoutUpdatedPayloadDataMetadata
import subprocess
import time

class MockWebhook:
    """Mock webhook object for testing."""
    def __init__(self, status, order_id, metadata, line_items):
        self.data = MockData(status, order_id, metadata, line_items)

class MockData:
    """Mock webhook data."""
    def __init__(self, status, order_id, metadata, line_items):
        self.status = status
        self.order_id = order_id
        self.metadata = metadata
        self.line_items = line_items

class MockLineItem:
    """Mock line item."""
    def __init__(self, product_id, price_amount):
        self.product_id = product_id
        self.price_amount = price_amount

async def test_webhook_tracking():
    """Test webhook tracking by calling handlers directly."""
    print("Testing webhook tracking directly...")
    print("=" * 60)

    # Test 1: Credits purchase
    print("\n1. Testing credits purchase...")
    webhook_credits = MockWebhook(
        status="completed",
        order_id="test_order_123_credits",
        metadata={"token": "test_token_abcdef"},
        line_items=[MockLineItem("prod_credits_500", 499)]
    )

    try:
        await handle_checkout_updated(webhook_credits)
        print("✓ Credits webhook processed successfully")
    except Exception as e:
        print(f"✗ Error processing credits webhook: {e}")
        import traceback
        traceback.print_exc()

    # Test 2: Pass purchase
    print("\n2. Testing pass purchase...")
    webhook_pass = MockWebhook(
        status="completed",
        order_id="test_order_456_pass",
        metadata={"token": "test_token_xyz123"},
        line_items=[MockLineItem("prod_pass_7day", 499)]
    )

    try:
        await handle_checkout_updated(webhook_pass)
        print("✓ Pass webhook processed successfully")
    except Exception as e:
        print(f"✗ Error processing pass webhook: {e}")
        import traceback
        traceback.print_exc()

    # Test 3: Test idempotency
    print("\n3. Testing idempotency...")
    try:
        await handle_checkout_updated(webhook_credits)  # Same webhook again
        print("✓ Idempotency test completed")
    except Exception as e:
        print(f"✗ Error in idempotency test: {e}")

    # Wait a moment for logging
    time.sleep(1)

    # Check logs
    print("\n4. Checking app.log for events...")

    result = subprocess.run(
        ['tail', '-100', 'app.log'],
        capture_output=True,
        text=True
    )

    lines = result.stdout.split('\n')

    print("\nLooking for purchase_completed events:")
    purchase_count = 0
    for line in lines:
        if 'UPGRADE_EVENT' in line and 'purchase_completed' in line:
            print(f"  ✓ {line.strip()}")
            purchase_count += 1

    print("\nLooking for credits_applied events:")
    credits_count = 0
    for line in lines:
        if 'UPGRADE_EVENT' in line and 'credits_applied' in line:
            print(f"  ✓ {line.strip()}")
            credits_count += 1

    print("\nLooking for PURCHASE_COMPLETED logs:")
    for line in lines:
        if 'PURCHASE_COMPLETED' in line:
            print(f"  ✓ {line.strip()}")

    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"- Found {purchase_count} purchase_completed events (expected: 2-3)")
    print(f"- Found {credits_count} credits_applied events (expected: 2)")
    print("- Third purchase_completed event is from idempotency test")

    # Test product config lookups
    print("\n5. Testing PRODUCT_CONFIG lookups...")
    from pricing_config import PRODUCT_CONFIG

    print("\nProduct configurations:")
    for product_id in ['prod_credits_500', 'prod_pass_7day']:
        config = PRODUCT_CONFIG.get(product_id)
        if config:
            print(f"  {product_id}:")
            print(f"    variant: {config['variant']}")
            print(f"    type: {config['type']}")
            print(f"    amount: {config.get('amount', 'N/A')}")
            print(f"    days: {config.get('days', 'N/A')}")
        else:
            print(f"  ✗ {product_id} not found in PRODUCT_CONFIG")

if __name__ == "__main__":
    asyncio.run(test_webhook_tracking())