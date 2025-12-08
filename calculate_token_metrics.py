#!/usr/bin/env python3
"""
Calculate token usage metrics for the last 3 days
Separate input and output tokens, with total, average, and median
"""
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import statistics


def calculate_token_metrics(db_path: str = None, days: int = 3) -> Dict:
    """
    Calculate token usage metrics for the last N days

    Args:
        db_path: Path to dashboard database
        days: Number of days to analyze

    Returns:
        Dictionary with token metrics
    """
    if not db_path:
        db_path = os.path.join(os.path.dirname(__file__), "dashboard", "data", "validations.db")

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    print(f"Token Usage Metrics - Last {days} Days")
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print("=" * 60)

    # Query token usage data
    query = """
        SELECT
            created_at,
            token_usage_prompt,
            token_usage_completion,
            token_usage_total,
            job_id
        FROM validations
        WHERE created_at >= ?
        AND created_at <= ?
        AND token_usage_total IS NOT NULL
        ORDER BY created_at DESC
    """

    cursor.execute(query, (start_date.isoformat(), end_date.isoformat()))
    rows = cursor.fetchall()

    if not rows:
        print("No token usage data found")
        return {}

    # Extract token data
    input_tokens = []
    output_tokens = []
    total_tokens = []
    daily_data = {}

    for row in rows:
        date = row[0][:10]  # Get YYYY-MM-DD
        input_tok = row[1] or 0
        output_tok = row[2] or 0
        total_tok = row[3] or 0

        # Skip zero token jobs (potential logging errors)
        if total_tok == 0:
            continue

        input_tokens.append(input_tok)
        output_tokens.append(output_tok)
        total_tokens.append(total_tok)

        # Group by day
        if date not in daily_data:
            daily_data[date] = {
                'input': [],
                'output': [],
                'total': []
            }

        daily_data[date]['input'].append(input_tok)
        daily_data[date]['output'].append(output_tok)
        daily_data[date]['total'].append(total_tok)

    # Calculate overall metrics
    print("\n📊 OVERALL TOKEN METRICS")
    print("-" * 30)

    # Input tokens
    total_input = sum(input_tokens)
    avg_input = statistics.mean(input_tokens)
    median_input = statistics.median(input_tokens)

    print(f"\nINPUT TOKENS:")
    print(f"  Total: {total_input:,}")
    print(f"  Average: {avg_input:.0f}")
    print(f"  Median: {median_input:.0f}")

    # Output tokens
    total_output = sum(output_tokens)
    avg_output = statistics.mean(output_tokens)
    median_output = statistics.median(output_tokens)

    print(f"\nOUTPUT TOKENS:")
    print(f"  Total: {total_output:,}")
    print(f"  Average: {avg_output:.0f}")
    print(f"  Median: {median_output:.0f}")

    # Total tokens
    total_sum = sum(total_tokens)
    avg_total = statistics.mean(total_tokens)
    median_total = statistics.median(total_tokens)

    print(f"\nTOTAL TOKENS:")
    print(f"  Total: {total_sum:,}")
    print(f"  Average: {avg_total:.0f}")
    print(f"  Median: {median_total:.0f}")

    # Verify consistency
    print(f"\n📊 VERIFICATION:")
    print(f"  Input + Output = Total: {total_input + total_output:,} = {total_sum:,} ✓")

    # Daily breakdown
    print(f"\n📅 DAILY BREAKDOWN")
    print("-" * 30)

    for date in sorted(daily_data.keys(), reverse=True):
        daily_input = daily_data[date]['input']
        daily_output = daily_data[date]['output']
        daily_total = daily_data[date]['total']

        print(f"\n{date}:")
        print(f"  Jobs: {len(daily_total)}")
        print(f"  Input - Total: {sum(daily_input):,}, Avg: {statistics.mean(daily_input):.0f}, Median: {statistics.median(daily_input):.0f}")
        print(f"  Output - Total: {sum(daily_output):,}, Avg: {statistics.mean(daily_output):.0f}, Median: {statistics.median(daily_output):.0f}")
        print(f"  Total - Total: {sum(daily_total):,}, Avg: {statistics.mean(daily_total):.0f}, Median: {statistics.median(daily_total):.0f}")

    # Percentiles
    print(f"\n📈 PERCENTILES (ALL DAYS)")
    print("-" * 30)

    # Calculate percentiles
    def get_percentiles(data, label):
        data_sorted = sorted(data)
        p50 = statistics.median(data_sorted)
        p75 = data_sorted[int(len(data_sorted) * 0.75)]
        p90 = data_sorted[int(len(data_sorted) * 0.90)]
        p95 = data_sorted[int(len(data_sorted) * 0.95)]
        p99 = data_sorted[int(len(data_sorted) * 0.99)]
        max_val = max(data_sorted)

        print(f"\n{label}:")
        print(f"  50th (Median): {p50:.0f}")
        print(f"  75th: {p75:.0f}")
        print(f"  90th: {p90:.0f}")
        print(f"  95th: {p95:.0f}")
        print(f"  99th: {p99:.0f}")
        print(f"  Max: {max_val:.0f}")

        return {'p50': p50, 'p75': p75, 'p90': p90, 'p95': p95, 'p99': p99, 'max': max_val}

    input_percentiles = get_percentiles(input_tokens, "Input Tokens")
    output_percentiles = get_percentiles(output_tokens, "Output Tokens")
    total_percentiles = get_percentiles(total_tokens, "Total Tokens")

    # Summary statistics
    print(f"\n📋 SUMMARY STATISTICS")
    print("-" * 30)
    print(f"Total Jobs: {len(total_tokens)}")
    print(f"Date Range: {len(daily_data)} days")

    # Ratios
    if total_input > 0:
        output_to_input_ratio = total_output / total_input
        print(f"\nOutput/Input Ratio: {output_to_input_ratio:.2f}")

    if len(total_tokens) > 0:
        print(f"Tokens per Job - Avg: {avg_total:.0f}, Median: {median_total:.0f}")

    conn.close()

    return {
        'overall': {
            'input': {
                'total': total_input,
                'average': avg_input,
                'median': median_input,
                'percentiles': input_percentiles
            },
            'output': {
                'total': total_output,
                'average': avg_output,
                'median': median_output,
                'percentiles': output_percentiles
            },
            'total': {
                'total': total_sum,
                'average': avg_total,
                'median': median_total,
                'percentiles': total_percentiles
            },
            'jobs': len(total_tokens),
            'days': len(daily_data)
        },
        'daily': daily_data
    }


def main():
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else None
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    metrics = calculate_token_metrics(db_path, days)

    # Optional: Save to JSON
    if '--save' in sys.argv:
        import json
        with open('token_metrics.json', 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"\n✅ Metrics saved to token_metrics.json")


if __name__ == "__main__":
    main()