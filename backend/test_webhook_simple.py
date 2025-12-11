#!/usr/bin/env python3
"""
Simple test of webhook tracking functionality.

Tests the core logic without SDK dependencies.
"""

import subprocess
import time
import json
from pricing_config import PRODUCT_CONFIG

def test_product_config():
    """Test that PRODUCT_CONFIG has expected products."""
    print("Testing PRODUCT_CONFIG...")
    print("=" * 60)

    # Test products
    test_products = [
        ("prod_credits_500", "credits", "500"),
        ("prod_pass_7day", "pass", "7")
    ]

    print("\nChecking product configurations:")
    for product_id, expected_type, expected_amount in test_products:
        config = PRODUCT_CONFIG.get(product_id)
        if config:
            print(f"\n✓ {product_id}:")
            print(f"  variant: {config['variant']}")
            print(f"  type: {config['type']}")
            if 'amount' in config:
                print(f"  amount: {config['amount']}")
            if 'days' in config:
                print(f"  days: {config['days']}")

            # Verify expected values
            assert config['type'] == expected_type, f"Expected type {expected_type}, got {config['type']}"
            if expected_type == 'credits':
                assert config['amount'] == int(expected_amount), f"Expected amount {expected_amount}, got {config['amount']}"
            else:
                assert config['days'] == int(expected_amount), f"Expected days {expected_amount}, got {config['days']}"
        else:
            print(f"\n✗ {product_id} NOT FOUND in PRODUCT_CONFIG")
            return False

    print("\n✓ All products found with correct configuration!")
    return True

def verify_webhook_implementation():
    """Verify the webhook implementation changes are present."""
    print("\n\nVerifying webhook implementation...")
    print("=" * 60)

    # Read the webhook handler
    with open('app.py', 'r') as f:
        content = f.read()

    # Check for required imports
    checks = [
        ("PRODUCT_CONFIG import", "from pricing_config import PRODUCT_CONFIG" in content),
        ("add_pass import", "add_pass" in content and "from database import" in content),
        ("log_upgrade_event calls", "log_upgrade_event(" in content),
        ("purchase_completed event", "'purchase_completed'" in content),
        ("credits_applied event", "'credits_applied'" in content),
        ("product_id extraction", "line_items[0].product_id" in content),
        ("amount_cents extraction", "amount_cents = line_items[0].price_amount" in content),
        ("experiment_variant extraction", "experiment_variant = product_config['variant']" in content)
    ]

    print("\nChecking implementation:")
    all_passed = True
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False

    return all_passed

def check_recent_logs():
    """Check recent logs for upgrade events."""
    print("\n\nChecking recent logs...")
    print("=" * 60)

    # Try to get recent logs
    try:
        result = subprocess.run(
            ['tail', '-20', 'app.log'],
            capture_output=True,
            text=True
        )

        lines = result.stdout.split('\n')

        print("\nLooking for recent upgrade events:")
        found_events = []

        for line in lines:
            if 'UPGRADE_EVENT' in line:
                found_events.append(line.strip())
                print(f"  {line.strip()}")

        if not found_events:
            print("  No upgrade events found in recent logs")
            print("  (This is expected if no webhooks have been processed recently)")

        return len(found_events)

    except FileNotFoundError:
        print("  app.log not found (expected if backend hasn't run)")
        return 0

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("WEBHOOK TRACKING IMPLEMENTATION TEST")
    print("=" * 60)

    # Run tests
    config_ok = test_product_config()
    impl_ok = verify_webhook_implementation()
    event_count = check_recent_logs()

    # Summary
    print("\n\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    print(f"\n✓ Product configuration: {'PASS' if config_ok else 'FAIL'}")
    print(f"✓ Webhook implementation: {'PASS' if impl_ok else 'FAIL'}")
    print(f"✓ Recent upgrade events: {event_count} found")

    if config_ok and impl_ok:
        print("\n✅ Implementation appears complete!")
        print("\nNext steps:")
        print("1. Start the backend server")
        print("2. Send test webhooks (test_webhook_tracking.py)")
        print("3. Check logs for upgrade events")
    else:
        print("\n❌ Implementation has issues that need to be fixed")

    print("\nExpected behavior:")
    print("- When a completed checkout webhook arrives:")
    print("  1. Extract product_id and amount_cents")
    print("  2. Look up product in PRODUCT_CONFIG")
    print("  3. Log 'purchase_completed' event")
    print("  4. Call add_credits() OR add_pass()")
    print("  5. Log 'credits_applied' event on success")
    print("  6. Include revenue (amount_cents) in events")

if __name__ == "__main__":
    main()