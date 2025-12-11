import re
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path


def parse_upgrade_events(
    log_file_path: str = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    experiment_variant: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse UPGRADE_EVENT logs and return analytics data for dashboard.

    Purpose: Extract upgrade funnel events from app.log to measure A/B test
    performance. Returns event counts and conversion rates per variant.

    Args:
        log_file_path: Path to app.log (defaults to /opt/citations/logs/app.log)
        start_date: Filter events after this date (inclusive)
        end_date: Filter events before this date (inclusive)
        experiment_variant: Filter to specific variant ('1' or '2', None = both)

    Returns:
        Dictionary with structure:
        {
            "variant_1": {
                "pricing_table_shown": <count>,
                "product_selected": <count>,
                "checkout_started": <count>,
                "purchase_completed": <count>,
                "purchase_failed": <count>,
                "credits_applied": <count>,
                "conversion_rates": {
                    "table_to_selection": <float 0-1>,
                    "selection_to_checkout": <float 0-1>,
                    "checkout_to_purchase": <float 0-1>,
                    "overall": <float 0-1>
                },
                "revenue_cents": <int>
            },
            "variant_2": { ... },
            "total_events": <int>,
            "date_range": {"start": <str>, "end": <str>},
            "unique_tokens": {"variant_1": <int>, "variant_2": <int>}
        }

    Example Usage:
        # Get all events
        data = parse_upgrade_events()

        # Get last 7 days
        from datetime import datetime, timedelta
        end = datetime.now()
        start = end - timedelta(days=7)
        data = parse_upgrade_events(start_date=start, end_date=end)

        # Get only variant 1 (Credits)
        data = parse_upgrade_events(experiment_variant='1')

    Common Issues:
        - FileNotFoundError: Check log_file_path, default is /opt/citations/logs/app.log
        - Empty results: Check if UPGRADE_EVENT logs exist with: grep UPGRADE_EVENT app.log
        - Invalid JSON: Log line corrupted, function will skip it and log warning
    """
    # Default log path
    if log_file_path is None:
        log_file_path = os.environ.get('APP_LOG_PATH', '/opt/citations/logs/app.log')

    # Check if file exists
    if not os.path.exists(log_file_path):
        raise FileNotFoundError(
            f"Log file not found: {log_file_path}. "
            f"Set APP_LOG_PATH environment variable or pass log_file_path argument."
        )

    # Initialize counters per variant
    variants_data = {
        '1': {
            'pricing_table_shown': 0,
            'product_selected': 0,
            'checkout_started': 0,
            'purchase_completed': 0,
            'purchase_failed': 0,
            'credits_applied': 0,
            'revenue_cents': 0,
            'tokens': set()  # Track unique users
        },
        '2': {
            'pricing_table_shown': 0,
            'product_selected': 0,
            'checkout_started': 0,
            'purchase_completed': 0,
            'purchase_failed': 0,
            'credits_applied': 0,
            'revenue_cents': 0,
            'tokens': set()
        }
    }

    total_events = 0
    first_timestamp = None
    last_timestamp = None

    # Read and parse log file
    with open(log_file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Look for UPGRADE_EVENT prefix
            if not line.startswith('UPGRADE_EVENT:') and 'UPGRADE_EVENT:' not in line:
                continue

            # Extract JSON portion (after "UPGRADE_EVENT: ")
            try:
                # Handle different log formats
                if 'UPGRADE_EVENT:' in line:
                    json_start = line.index('UPGRADE_EVENT:') + len('UPGRADE_EVENT:')
                    json_str = line[json_start:].strip()
                else:
                    continue

                # Parse JSON
                event = json.loads(json_str)

            except (json.JSONDecodeError, ValueError) as e:
                # Skip malformed lines but log warning
                print(f"Warning: Skipping malformed JSON at line {line_num}: {e}")
                continue

            # Extract fields
            timestamp = event.get('timestamp')
            event_name = event.get('event')
            variant = event.get('experiment_variant')
            token = event.get('token')
            amount_cents = event.get('amount_cents')

            # Validate required fields
            if not timestamp or not event_name:
                print(f"Warning: Missing timestamp or event at line {line_num}")
                continue

            # Convert timestamp to datetime
            try:
                event_time = datetime.fromtimestamp(timestamp)
            except (ValueError, OSError):
                print(f"Warning: Invalid timestamp {timestamp} at line {line_num}")
                continue

            # Apply date filters
            if start_date and event_time < start_date:
                continue
            if end_date and event_time > end_date:
                continue

            # Apply variant filter
            if experiment_variant and variant != experiment_variant:
                continue

            # Track date range
            if first_timestamp is None or event_time < first_timestamp:
                first_timestamp = event_time
            if last_timestamp is None or event_time > last_timestamp:
                last_timestamp = event_time

            # Skip events without variant (shouldn't happen per Oracle #5, but defensive)
            if variant not in ['1', '2']:
                print(f"Warning: Unknown variant '{variant}' at line {line_num}")
                continue

            # Increment counters
            variant_data = variants_data[variant]

            if event_name in variant_data:
                variant_data[event_name] += 1

            # Track revenue
            if amount_cents and event_name == 'purchase_completed':
                variant_data['revenue_cents'] += amount_cents

            # Track unique tokens
            if token:
                variant_data['tokens'].add(token)

            total_events += 1

    # Calculate conversion rates for each variant
    def calculate_conversion_rates(data):
        rates = {}

        # Prevent division by zero
        shown = data['pricing_table_shown'] or 1
        selected = data['product_selected'] or 1
        started = data['checkout_started'] or 1

        rates['table_to_selection'] = data['product_selected'] / shown
        rates['selection_to_checkout'] = data['checkout_started'] / selected
        rates['checkout_to_purchase'] = data['purchase_completed'] / started
        rates['overall'] = data['purchase_completed'] / shown

        return rates

    # Build result
    result = {
        'variant_1': {
            'pricing_table_shown': variants_data['1']['pricing_table_shown'],
            'product_selected': variants_data['1']['product_selected'],
            'checkout_started': variants_data['1']['checkout_started'],
            'purchase_completed': variants_data['1']['purchase_completed'],
            'purchase_failed': variants_data['1']['purchase_failed'],
            'credits_applied': variants_data['1']['credits_applied'],
            'conversion_rates': calculate_conversion_rates(variants_data['1']),
            'revenue_cents': variants_data['1']['revenue_cents']
        },
        'variant_2': {
            'pricing_table_shown': variants_data['2']['pricing_table_shown'],
            'product_selected': variants_data['2']['product_selected'],
            'checkout_started': variants_data['2']['checkout_started'],
            'purchase_completed': variants_data['2']['purchase_completed'],
            'purchase_failed': variants_data['2']['purchase_failed'],
            'credits_applied': variants_data['2']['credits_applied'],
            'conversion_rates': calculate_conversion_rates(variants_data['2']),
            'revenue_cents': variants_data['2']['revenue_cents']
        },
        'total_events': total_events,
        'date_range': {
            'start': first_timestamp.isoformat() if first_timestamp else None,
            'end': last_timestamp.isoformat() if last_timestamp else None
        },
        'unique_tokens': {
            'variant_1': len(variants_data['1']['tokens']),
            'variant_2': len(variants_data['2']['tokens'])
        }
    }

    return result


def get_funnel_summary(log_file_path: str = None, days: int = 7) -> str:
    """
    Get human-readable funnel summary for last N days.

    Convenience function for quick analysis.

    Args:
        log_file_path: Path to app.log
        days: Number of days to analyze

    Returns:
        Formatted string with funnel summary

    Example output:
        Upgrade Funnel Analysis (Last 7 Days)
        ======================================

        Variant 1 (Credits):
          Pricing Shown:      150
          Product Selected:   45 (30.0%)
          Checkout Started:   40 (26.7%)
          Purchase Completed: 32 (21.3%)
          Revenue:            $159.68

        Variant 2 (Passes):
          Pricing Shown:      155
          Product Selected:   52 (33.5%)
          Checkout Started:   48 (31.0%)
          Purchase Completed: 40 (25.8%)
          Revenue:            $199.60

        Winner: Variant 2 (+4.5% conversion)
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    data = parse_upgrade_events(log_file_path, start_date, end_date)

    v1 = data['variant_1']
    v2 = data['variant_2']

    output = []
    output.append(f"Upgrade Funnel Analysis (Last {days} Days)")
    output.append("=" * 50)
    output.append("")

    output.append("Variant 1 (Credits):")
    output.append(f"  Pricing Shown:      {v1['pricing_table_shown']}")
    output.append(f"  Product Selected:   {v1['product_selected']} ({v1['conversion_rates']['table_to_selection']*100:.1f}%)")
    output.append(f"  Checkout Started:   {v1['checkout_started']} ({v1['checkout_started']/max(v1['pricing_table_shown'],1)*100:.1f}%)")
    output.append(f"  Purchase Completed: {v1['purchase_completed']} ({v1['conversion_rates']['overall']*100:.1f}%)")
    output.append(f"  Revenue:            ${v1['revenue_cents']/100:.2f}")
    output.append("")

    output.append("Variant 2 (Passes):")
    output.append(f"  Pricing Shown:      {v2['pricing_table_shown']}")
    output.append(f"  Product Selected:   {v2['product_selected']} ({v2['conversion_rates']['table_to_selection']*100:.1f}%)")
    output.append(f"  Checkout Started:   {v2['checkout_started']} ({v2['checkout_started']/max(v2['pricing_table_shown'],1)*100:.1f}%)")
    output.append(f"  Purchase Completed: {v2['purchase_completed']} ({v2['conversion_rates']['overall']*100:.1f}%)")
    output.append(f"  Revenue:            ${v2['revenue_cents']/100:.2f}")
    output.append("")

    # Determine winner
    if v1['conversion_rates']['overall'] > v2['conversion_rates']['overall']:
        diff = (v1['conversion_rates']['overall'] - v2['conversion_rates']['overall']) * 100
        output.append(f"Winner: Variant 1 (+{diff:.1f}% conversion)")
    elif v2['conversion_rates']['overall'] > v1['conversion_rates']['overall']:
        diff = (v2['conversion_rates']['overall'] - v1['conversion_rates']['overall']) * 100
        output.append(f"Winner: Variant 2 (+{diff:.1f}% conversion)")
    else:
        output.append("Winner: Tie")

    return "\n".join(output)