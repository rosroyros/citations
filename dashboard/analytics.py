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

    # Initialize counters per variant (4-variant scheme for A/B test)
    # 1.1: Credits + Button, 1.2: Credits + Inline
    # 2.1: Passes + Button, 2.2: Passes + Inline
    variant_template = {
        'pricing_table_shown': 0,
        'product_selected': 0,
        'checkout_started': 0,
        'purchase_completed': 0,
        'purchase_failed': 0,
        'credits_applied': 0,
        'revenue_cents': 0,
        'tokens': set()  # Track unique users
    }
    variants_data = {
        '1.1': variant_template.copy(),
        '1.2': {**variant_template, 'tokens': set()},
        '2.1': {**variant_template, 'tokens': set()},
        '2.2': {**variant_template, 'tokens': set()},
    }
    # Re-initialize tokens as sets (copy doesn't deep copy)
    for v in variants_data.values():
        v['tokens'] = set()

    total_events = 0
    first_timestamp = None
    last_timestamp = None

    # Read and parse log file
    with open(log_file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Initialize event variables
            timestamp = None
            event_time = None
            event_name = None
            variant = None
            token = None
            amount_cents = None
            
            # Helper to extract timestamp from log line prefix
            # Format: 2025-12-16 10:00:00 ...
            ts_match = re.search(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
            if ts_match:
                try:
                    event_time = datetime.strptime(ts_match.group(1), "%Y-%m-%d %H:%M:%S")
                    timestamp = event_time.timestamp()
                except ValueError:
                    pass

            # Method 1: Regex for UPGRADE_WORKFLOW (New Format)
            if 'UPGRADE_WORKFLOW:' in line:
                # Regex to match key-value pairs including token
                # Note: token is truncated to first 8 chars in logs for privacy
                workflow_match = re.search(
                    r'UPGRADE_WORKFLOW: job_id=([\w-]+|None) event=(\w+) token=([\w]+|None)(?: variant=(\w+))?(?: product_id=([\w_]+))?(?: amount_cents=(\d+))?', 
                    line
                )
                
                if workflow_match:
                    event_name = workflow_match.group(2)
                    token = workflow_match.group(3)
                    variant = workflow_match.group(4)
                    if workflow_match.group(6):
                        amount_cents = int(workflow_match.group(6))
                    
                    # Handle 'None' string from log
                    if token == 'None':
                        token = None

            # Method 2: Legacy JSON (UPGRADE_EVENT)
            elif 'UPGRADE_EVENT:' in line:
                try:
                    json_start = line.index('UPGRADE_EVENT:') + len('UPGRADE_EVENT:')
                    json_str = line[json_start:].strip()
                    event = json.loads(json_str)
                    
                    timestamp = event.get('timestamp')
                    event_name = event.get('event')
                    variant = event.get('experiment_variant')
                    token = event.get('token')
                    amount_cents = event.get('amount_cents')
                    
                    if timestamp:
                        try:
                            event_time = datetime.fromtimestamp(timestamp)
                        except (ValueError, OSError):
                            pass
                except (json.JSONDecodeError, ValueError):
                    continue

            # Skip if parsing failed
            if not event_name or not event_time:
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

            # Map legacy variants to new format (backward compatibility)
            # Legacy '1' -> '1.1' (Credits + Button)
            # Legacy '2' -> '2.1' (Passes + Button)
            if variant == '1':
                variant = '1.1'
            elif variant == '2':
                variant = '2.1'
            elif variant not in ['1.1', '1.2', '2.1', '2.2']:
                # print(f"Warning: Unknown variant '{variant}' at line {line_num}")
                continue

            # Increment counters
            variant_data = variants_data[variant]

            if event_name in variant_data:
                variant_data[event_name] += 1

            # Track revenue
            if amount_cents and event_name == 'purchase_completed':
                variant_data['revenue_cents'] += amount_cents

            # Track unique tokens (or job_ids)
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

    # Build result with 4 variants
    def build_variant_result(v_key):
        return {
            'pricing_table_shown': variants_data[v_key]['pricing_table_shown'],
            'product_selected': variants_data[v_key]['product_selected'],
            'checkout_started': variants_data[v_key]['checkout_started'],
            'purchase_completed': variants_data[v_key]['purchase_completed'],
            'purchase_failed': variants_data[v_key]['purchase_failed'],
            'credits_applied': variants_data[v_key]['credits_applied'],
            'conversion_rates': calculate_conversion_rates(variants_data[v_key]),
            'revenue_cents': variants_data[v_key]['revenue_cents']
        }

    result = {
        'variant_1_1': build_variant_result('1.1'),
        'variant_1_2': build_variant_result('1.2'),
        'variant_2_1': build_variant_result('2.1'),
        'variant_2_2': build_variant_result('2.2'),
        # Legacy aliases for backward compatibility
        'variant_1': build_variant_result('1.1'),
        'variant_2': build_variant_result('2.1'),
        'total_events': total_events,
        'date_range': {
            'start': first_timestamp.isoformat() if first_timestamp else None,
            'end': last_timestamp.isoformat() if last_timestamp else None
        },
        'unique_tokens': {
            'variant_1_1': len(variants_data['1.1']['tokens']),
            'variant_1_2': len(variants_data['1.2']['tokens']),
            'variant_2_1': len(variants_data['2.1']['tokens']),
            'variant_2_2': len(variants_data['2.2']['tokens']),
            # Legacy aliases
            'variant_1': len(variants_data['1.1']['tokens']),
            'variant_2': len(variants_data['2.1']['tokens'])
        },
        'conversion_rates': {
            'variant_1_1': calculate_conversion_rates(variants_data['1.1']),
            'variant_1_2': calculate_conversion_rates(variants_data['1.2']),
            'variant_2_1': calculate_conversion_rates(variants_data['2.1']),
            'variant_2_2': calculate_conversion_rates(variants_data['2.2']),
            # Legacy aliases
            'variant_1': calculate_conversion_rates(variants_data['1.1']),
            'variant_2': calculate_conversion_rates(variants_data['2.1'])
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