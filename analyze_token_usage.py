#!/usr/bin/env python3
"""
Analyze token usage for the last 3 days from the dashboard database
"""
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import statistics


def get_token_stats_last_3_days(db_path: str = None) -> Dict:
    """
    Analyze token usage statistics for the last 3 days

    Args:
        db_path: Path to dashboard database (defaults to dashboard/data/validations.db)

    Returns:
        Dictionary with token statistics
    """
    if not db_path:
        db_path = os.path.join(os.path.dirname(__file__), "dashboard", "data", "validations.db")

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Calculate date range (last 3 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3)

    print(f"Analyzing token usage from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print("=" * 80)

    # Query token usage data
    query = """
        SELECT
            created_at,
            token_usage_prompt,
            token_usage_completion,
            token_usage_total,
            citation_count,
            user_type,
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
        print("No token usage data found for the last 3 days")
        return {}

    # Process data
    daily_stats = {}
    all_input_tokens = []
    all_output_tokens = []
    all_total_tokens = []

    for row in rows:
        date_str = row[0][:10]  # Extract date part
        input_tokens = row[1] or 0
        output_tokens = row[2] or 0
        total_tokens = row[3] or 0
        citation_count = row[4] or 0
        user_type = row[5]

        # Initialize daily stats if not exists
        if date_str not in daily_stats:
            daily_stats[date_str] = {
                'input_tokens': [],
                'output_tokens': [],
                'total_tokens': [],
                'citations_per_job': [],
                'job_count': 0,
                'user_types': {'free': 0, 'paid': 0}
            }

        # Add to daily stats
        daily_stats[date_str]['input_tokens'].append(input_tokens)
        daily_stats[date_str]['output_tokens'].append(output_tokens)
        daily_stats[date_str]['total_tokens'].append(total_tokens)
        if citation_count > 0:
            daily_stats[date_str]['citations_per_job'].append(citation_count)
        daily_stats[date_str]['job_count'] += 1
        daily_stats[date_str]['user_types'][user_type] += 1

        # Add to overall stats
        all_input_tokens.append(input_tokens)
        all_output_tokens.append(output_tokens)
        all_total_tokens.append(total_tokens)

    # Calculate and display statistics
    print("\n📊 OVERALL 3-DAY STATISTICS")
    print("-" * 40)
    print(f"Total Jobs: {len(rows)}")
    print(f"Total Input Tokens: {sum(all_input_tokens):,}")
    print(f"Total Output Tokens: {sum(all_output_tokens):,}")
    print(f"Total Tokens: {sum(all_total_tokens):,}")
    print(f"Average Input Tokens per Job: {statistics.mean(all_input_tokens):.0f}")
    print(f"Average Output Tokens per Job: {statistics.mean(all_output_tokens):.0f}")
    print(f"Average Total Tokens per Job: {statistics.mean(all_total_tokens):.0f}")
    print(f"Median Input Tokens: {statistics.median(all_input_tokens):.0f}")
    print(f"Median Output Tokens: {statistics.median(all_output_tokens):.0f}")
    print(f"Median Total Tokens: {statistics.median(all_total_tokens):.0f}")
    print(f"Input Token P95: {sorted(all_input_tokens)[int(len(all_input_tokens) * 0.95)]:.0f}")
    print(f"Output Token P95: {sorted(all_output_tokens)[int(len(all_output_tokens) * 0.95)]:.0f}")
    print(f"Total Token P95: {sorted(all_total_tokens)[int(len(all_total_tokens) * 0.95)]:.0f}")

    # Per-day breakdown
    print("\n📅 DAILY BREAKDOWN")
    print("-" * 40)
    for date in sorted(daily_stats.keys(), reverse=True):
        stats = daily_stats[date]

        print(f"\n{date}:")
        print(f"  Jobs: {stats['job_count']} (Free: {stats['user_types']['free']}, Paid: {stats['user_types']['paid']})")
        print(f"  Input Tokens: {sum(stats['input_tokens']):,} (avg: {statistics.mean(stats['input_tokens']):.0f})")
        print(f"  Output Tokens: {sum(stats['output_tokens']):,} (avg: {statistics.mean(stats['output_tokens']):.0f})")
        print(f"  Total Tokens: {sum(stats['total_tokens']):,} (avg: {statistics.mean(stats['total_tokens']):.0f})")

        if stats['citations_per_job']:
            avg_citations = statistics.mean(stats['citations_per_job'])
            print(f"  Avg Citations per Job: {avg_citations:.1f}")

            # Tokens per citation ratio
            total_input = sum(stats['input_tokens'])
            total_output = sum(stats['output_tokens'])
            total_citations = sum(stats['citations_per_job'])

            if total_citations > 0:
                print(f"  Input Tokens per Citation: {total_input / total_citations:.1f}")
                print(f"  Output Tokens per Citation: {total_output / total_citations:.1f}")

    # Threshold recommendations based on P95
    print("\n🎯 THRESHOLD RECOMMENDATIONS (based on P95)")
    print("-" * 40)
    input_p95 = sorted(all_input_tokens)[int(len(all_input_tokens) * 0.95)]
    output_p95 = sorted(all_output_tokens)[int(len(all_output_tokens) * 0.95)]
    total_p95 = sorted(all_total_tokens)[int(len(all_total_tokens) * 0.95)]

    print(f"Input Token Threshold: {input_p95:.0f} (covers 95% of jobs)")
    print(f"Output Token Threshold: {output_p95:.0f} (covers 95% of jobs)")
    print(f"Total Token Threshold: {total_p95:.0f} (covers 95% of jobs)")

    # Cost estimation (assuming OpenAI pricing)
    print("\n💰 COST ANALYSIS (OpenAI GPT-5-mini estimated)")
    print("-" * 40)
    input_cost_per_1m = 0.075  # $0.075 per 1M input tokens
    output_cost_per_1m = 0.300  # $0.300 per 1M output tokens

    total_input_cost = (sum(all_input_tokens) / 1_000_000) * input_cost_per_1m
    total_output_cost = (sum(all_output_tokens) / 1_000_000) * output_cost_per_1m
    total_cost = total_input_cost + total_output_cost

    print(f"Input Token Cost: ${total_input_cost:.2f}")
    print(f"Output Token Cost: ${total_output_cost:.2f}")
    print(f"Total Cost: ${total_cost:.2f}")
    print(f"Average Cost per Job: ${total_cost / len(rows):.4f}")

    # Alert thresholds
    print("\n🚨 ALERT THRESHOLDS")
    print("-" * 40)
    print(f"High Input Token Alert: > {input_p95 * 1.5:.0f} tokens")
    print(f"High Output Token Alert: > {output_p95 * 1.5:.0f} tokens")
    print(f"High Total Token Alert: > {total_p95 * 1.5:.0f} tokens")
    print(f"Zero Token Alert: = 0 tokens (indicates logging issue)")

    # Find outliers
    print("\n🔍 OUTLIER DETECTION")
    print("-" * 40)

    # High token jobs
    high_token_threshold = total_p95 * 2
    high_token_jobs = [
        (row[6], row[3]) for row in rows
        if row[3] and row[3] > high_token_threshold
    ]

    if high_token_jobs:
        print(f"Jobs with > {high_token_threshold:.0f} tokens:")
        for job_id, tokens in high_token_jobs[:5]:  # Show top 5
            print(f"  - {job_id}: {tokens:,} tokens")
        if len(high_token_jobs) > 5:
            print(f"  ... and {len(high_token_jobs) - 5} more")

    # Zero token jobs (potential issues)
    zero_token_jobs = [row[6] for row in rows if row[3] == 0]
    if zero_token_jobs:
        print(f"\n⚠️  Jobs with 0 tokens (potential logging issues): {len(zero_token_jobs)}")
        for job_id in zero_token_jobs[:3]:
            print(f"  - {job_id}")
        if len(zero_token_jobs) > 3:
            print(f"  ... and {len(zero_token_jobs) - 3} more")

    conn.close()

    return {
        'overall': {
            'total_jobs': len(rows),
            'total_input_tokens': sum(all_input_tokens),
            'total_output_tokens': sum(all_output_tokens),
            'total_tokens': sum(all_total_tokens),
            'avg_input_tokens': statistics.mean(all_input_tokens),
            'avg_output_tokens': statistics.mean(all_output_tokens),
            'avg_total_tokens': statistics.mean(all_total_tokens),
            'input_p95': input_p95,
            'output_p95': output_p95,
            'total_p95': total_p95
        },
        'daily': daily_stats,
        'thresholds': {
            'input_alert': input_p95 * 1.5,
            'output_alert': output_p95 * 1.5,
            'total_alert': total_p95 * 1.5
        },
        'cost': {
            'total_cost': total_cost,
            'avg_cost_per_job': total_cost / len(rows)
        }
    }


if __name__ == "__main__":
    # You can pass a custom database path as argument
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else None

    stats = get_token_stats_last_3_days(db_path)