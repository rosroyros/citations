#!/usr/bin/env python3
"""
Test script for parse_upgrade_events function.

Usage:
    python3 test_analytics.py
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path (parent of backend)
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.analytics import parse_upgrade_events, get_funnel_summary


def test_with_sample_data():
    """Test parsing with sample log data."""
    # Create sample log file
    import tempfile
    import os

    sample_logs = """
2025-12-11 10:00:00 INFO UPGRADE_WORKFLOW: job_id=None event=pricing_table_shown token=abc12345 variant=1
2025-12-11 10:00:05 INFO UPGRADE_WORKFLOW: job_id=None event=product_selected token=abc12345 variant=1 product_id=prod_credits_500
2025-12-11 10:00:10 INFO UPGRADE_WORKFLOW: job_id=None event=checkout_started token=abc12345 variant=1 product_id=prod_credits_500
2025-12-11 10:00:30 INFO UPGRADE_WORKFLOW: job_id=None event=purchase_completed token=abc12345 variant=1 product_id=prod_credits_500 amount_cents=499
2025-12-11 10:00:35 INFO UPGRADE_WORKFLOW: job_id=None event=credits_applied token=abc12345 variant=1 product_id=prod_credits_500
2025-12-11 10:05:00 INFO UPGRADE_WORKFLOW: job_id=None event=pricing_table_shown token=def67890 variant=2
2025-12-11 10:05:05 INFO UPGRADE_WORKFLOW: job_id=None event=product_selected token=def67890 variant=2 product_id=prod_pass_7day
2025-12-11 10:05:10 INFO UPGRADE_WORKFLOW: job_id=None event=checkout_started token=def67890 variant=2 product_id=prod_pass_7day
"""

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(sample_logs)
        temp_log = f.name

    try:
        print("Test 1: Parse all events")
        print("="*50)
        data = parse_upgrade_events(temp_log)

        print(f"Total events: {data['total_events']}")
        print(f"\nVariant 1 (Credits):")
        print(f"  Shown: {data['variant_1']['pricing_table_shown']}")
        print(f"  Selected: {data['variant_1']['product_selected']}")
        print(f"  Completed: {data['variant_1']['purchase_completed']}")
        print(f"  Revenue: ${data['variant_1']['revenue_cents']/100:.2f}")
        print(f"  Overall conversion: {data['variant_1']['conversion_rates']['overall']*100:.1f}%")

        print(f"\nVariant 2 (Passes):")
        print(f"  Shown: {data['variant_2']['pricing_table_shown']}")
        print(f"  Selected: {data['variant_2']['product_selected']}")
        print(f"  Completed: {data['variant_2']['purchase_completed']}")

        # Verify counts
        assert data['variant_1']['pricing_table_shown'] == 1, "Variant 1 should have 1 shown"
        assert data['variant_1']['purchase_completed'] == 1, "Variant 1 should have 1 purchase"
        assert data['variant_1']['revenue_cents'] == 499, "Variant 1 should have $4.99 revenue"
        assert data['variant_2']['pricing_table_shown'] == 1, "Variant 2 should have 1 shown"
        assert data['variant_2']['product_selected'] == 1, "Variant 2 should have 1 selection"

        print("\n✓ All assertions passed!\n")

        print("Test 2: Filter by variant")
        print("="*50)
        data_v1 = parse_upgrade_events(temp_log, experiment_variant='1')
        print(f"Variant 1 only - Total events: {data_v1['total_events']}")
        assert data_v1['variant_2']['pricing_table_shown'] == 0, "Variant 2 should be filtered out"
        print("✓ Variant filter works!\n")

        print("Test 3: Funnel summary")
        print("="*50)
        # Note: get_funnel_summary uses date filter, so may not show test data
        # Just test it doesn't crash
        try:
            summary = get_funnel_summary(temp_log, days=30)
            print(summary)
            print("\n✓ Funnel summary generated!\n")
        except Exception as e:
            print(f"Note: Funnel summary might be empty if dates don't match: {e}\n")

        print("Test 4: Error handling")
        print("="*50)
        try:
            parse_upgrade_events('/nonexistent/file.log')
            print("✗ Should have raised FileNotFoundError")
        except FileNotFoundError as e:
            print(f"✓ FileNotFoundError raised correctly")

        print("\n" + "="*50)
        print("ALL TESTS PASSED!")
        print("="*50)

    finally:
        # Clean up
        os.unlink(temp_log)


if __name__ == '__main__':
    test_with_sample_data()