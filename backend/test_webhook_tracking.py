#!/usr/bin/env python3
"""
Test webhook handler with mock Polar webhooks.

This tests the tracking integration without needing real Polar webhooks.

Dependencies:
- requests: Already included in requirements.txt
"""

import requests
import json
import subprocess
import time

BASE_URL = "http://localhost:5000"

# Mock webhook payload for credits purchase
webhook_credits = {
    "status": "completed",
    "order_id": "test_order_123_credits",
    "metadata": {
        "token": "test_token_abcdef"
    },
    "line_items": [
        {
            "product_id": "prod_credits_500",
            "price_amount": 499  # $4.99 in cents
        }
    ]
}

# Mock webhook payload for pass purchase
webhook_pass = {
    "status": "completed",
    "order_id": "test_order_456_pass",
    "metadata": {
        "token": "test_token_xyz123"
    },
    "line_items": [
        {
            "product_id": "prod_pass_7day",
            "price_amount": 499  # $4.99 in cents
        }
    ]
}

def check_logs_for_events():
    """Check app.log for upgrade events."""
    print("\n3. Checking app.log for events...")

    # Get recent logs
    result = subprocess.run(
        ['tail', '-50', 'app.log'],
        capture_output=True,
        text=True,
        cwd='.'
    )

    lines = result.stdout.split('\n')

    print("\nLooking for purchase_completed events:")
    for line in lines:
        if 'UPGRADE_EVENT' in line and 'purchase_completed' in line:
            print(f"  ✓ {line.strip()}")

    print("\nLooking for credits_applied events:")
    for line in lines:
        if 'UPGRADE_EVENT' in line and 'credits_applied' in line:
            print(f"  ✓ {line.strip()}")

    print("\nLooking for PURCHASE_COMPLETED logs:")
    for line in lines:
        if 'PURCHASE_COMPLETED' in line:
            print(f"  ✓ {line.strip()}")

def test_idempotency():
    """Test that duplicate webhooks don't double-grant."""
    print("\n4. Testing idempotency (Oracle #6)...")

    for i in range(2):
        print(f"\nAttempt {i+1}:")
        response = requests.post(
            f"{BASE_URL}/api/polar-webhook",
            json=webhook_credits,
            headers={"Content-Type": "application/json"}
        )
        print(f"Response: {response.status_code}")

    print("\nNote: Idempotency is handled by add_credits/add_pass functions.")
    print("Second attempt should log purchase_completed but not credits_applied.")

def main():
    print("Testing webhook tracking...")
    print("=" * 60)

    # Test 1: Credits purchase
    print("\n1. Testing credits purchase webhook...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/polar-webhook",
            json=webhook_credits,
            headers={"Content-Type": "application/json"}
        )
        print(f"Response: {response.status_code} - {response.text}")
    except requests.ConnectionError:
        print("ERROR: Could not connect to server. Make sure the backend is running on port 5000")
        return

    # Wait a moment for processing
    time.sleep(1)

    # Test 2: Pass purchase
    print("\n2. Testing pass purchase webhook...")
    response = requests.post(
        f"{BASE_URL}/api/polar-webhook",
        json=webhook_pass,
        headers={"Content-Type": "application/json"}
    )
    print(f"Response: {response.status_code} - {response.text}")

    # Wait a moment for processing
    time.sleep(1)

    # Check logs
    check_logs_for_events()

    # Test idempotency
    test_idempotency()

    print("\n" + "=" * 60)
    print("Done. Review output above for tracking events.")
    print("\nExpected events:")
    print("- Two purchase_completed events (one for credits, one for pass)")
    print("- Two credits_applied events (one for credits, one for pass)")
    print("- PURCHASE_COMPLETED logs with revenue information")

if __name__ == "__main__":
    main()