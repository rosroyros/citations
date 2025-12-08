#!/usr/bin/env python3
"""
Analyze token usage for the last 3 days with filtering for eligible jobs only
Excludes test data, short content, and deduplicates appropriately
"""
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Set
import statistics
import re


def is_test_citation(citation_text: str) -> bool:
    """
    Check if citation appears to be test data
    """
    test_indicators = [
        'test', 'asdf', 'foo', 'bar', 'example', 'sample', 'demo',
        '123', 'test123', 'fake', 'placeholder', 'lorem', 'ipsum'
    ]
    citation_lower = citation_text.lower()
    return any(indicator in citation_lower for indicator in test_indicators)


def is_short_content(citation_text: str) -> bool:
    """
    Check if citation content is too short to be meaningful
    """
    # Remove whitespace and check actual character count
    cleaned = re.sub(r'\s+', '', citation_text.strip())
    return len(cleaned) < 20  # Less than 20 chars is likely invalid


def get_filtered_token_stats(db_path: str = None, days: int = 3) -> Dict:
    """
    Analyze token usage statistics for the last 3 days with filtering

    Args:
        db_path: Path to dashboard database
        days: Number of days to analyze

    Returns:
        Dictionary with filtered token statistics
    """
    if not db_path:
        db_path = os.path.join(os.path.dirname(__file__), "dashboard", "data", "validations.db")

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    print(f"Analyzing FILTERED token usage from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print("=" * 80)

    # Query all validation data including citation text for filtering
    query = """
        SELECT
            v.created_at,
            v.token_usage_prompt,
            v.token_usage_completion,
            v.token_usage_total,
            v.citation_count,
            v.user_type,
            v.job_id,
            r.citations_text
        FROM validations v
        LEFT JOIN results r ON v.job_id = r.job_id
        WHERE v.created_at >= ?
        AND v.created_at <= ?
        AND v.token_usage_total IS NOT NULL
        ORDER BY v.created_at DESC
    """

    cursor.execute(query, (start_date.isoformat(), end_date.isoformat()))
    rows = cursor.fetchall()

    if not rows:
        print("No token usage data found for the specified period")
        return {}

    # Filter jobs
    eligible_jobs = []
    excluded_jobs = {
        'test_data': 0,
        'short_content': 0,
        'no_citation_text': 0,
        'zero_tokens': 0
    }

    print("\n🔍 FILTERING PROCESS")
    print("-" * 40)

    for row in rows:
        date_str = row[0][:10]
        input_tokens = row[1] or 0
        output_tokens = row[2] or 0
        total_tokens = row[3] or 0
        citation_count = row[4] or 0
        user_type = row[5]
        job_id = row[6]
        citations_text = row[7]

        # Exclude zero token jobs (logging issues)
        if total_tokens == 0:
            excluded_jobs['zero_tokens'] += 1
            continue

        # Exclude jobs without citation text
        if not citations_text:
            excluded_jobs['no_citation_text'] += 1
            continue

        # Split into individual citations
        individual_citations = [c.strip() for c in citations_text.split('\n') if c.strip()]

        # Filter out test citations
        filtered_citations = []
        test_count = 0
        short_count = 0

        for citation in individual_citations:
            if is_test_citation(citation):
                test_count += 1
            elif is_short_content(citation):
                short_count += 1
            else:
                filtered_citations.append(citation)

        # If all citations are test data, exclude the job
        if len(filtered_citations) == 0 and len(individual_citations) > 0:
            excluded_jobs['test_data'] += 1
            continue

        # If all citations are too short, exclude the job
        if len(filtered_citations) == 0 and len(individual_citations) > 0:
            excluded_jobs['short_content'] += 1
            continue

        # Add eligible job with deduplicated citation count
        unique_citations = len(set(filtered_citations))  # Deduplicate within job
        eligible_jobs.append({
            'date': date_str,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens,
            'citation_count': unique_citations,
            'user_type': user_type,
            'job_id': job_id,
            'original_citation_count': citation_count,
            'filtered_citation_count': len(filtered_citations),
            'test_citations_removed': test_count,
            'short_citations_removed': short_count
        })

    # Print filtering summary
    total_jobs = len(rows)
    eligible_count = len(eligible_jobs)
    excluded_count = total_jobs - eligible_count

    print(f"Total jobs processed: {total_jobs}")
    print(f"Eligible jobs: {eligible_count} ({eligible_count/total_jobs*100:.1f}%)")
    print(f"Excluded jobs: {excluded_count} ({excluded_count/total_jobs*100:.1f}%)")
    print("\nExclusion breakdown:")
    for reason, count in excluded_jobs.items():
        if count > 0:
            print(f"  - {reason.replace('_', ' ').title()}: {count}")

    if eligible_count == 0:
        print("\n⚠️  No eligible jobs found after filtering")
        return {}

    # Calculate statistics for eligible jobs only
    daily_stats = {}
    all_input_tokens = []
    all_output_tokens = []
    all_total_tokens = []
    citations_per_job = []

    for job in eligible_jobs:
        date = job['date']

        # Initialize daily stats
        if date not in daily_stats:
            daily_stats[date] = {
                'jobs': [],
                'input_tokens': [],
                'output_tokens': [],
                'total_tokens': [],
                'citations': [],
                'user_types': {'free': 0, 'paid': 0}
            }

        # Add to daily stats
        daily_stats[date]['jobs'].append(job)
        daily_stats[date]['input_tokens'].append(job['input_tokens'])
        daily_stats[date]['output_tokens'].append(job['output_tokens'])
        daily_stats[date]['total_tokens'].append(job['total_tokens'])
        daily_stats[date]['citations'].append(job['citation_count'])
        daily_stats[date]['user_types'][job['user_type']] += 1

        # Add to overall stats
        all_input_tokens.append(job['input_tokens'])
        all_output_tokens.append(job['output_tokens'])
        all_total_tokens.append(job['total_tokens'])
        citations_per_job.append(job['citation_count'])

    # Calculate and display statistics
    print("\n📊 FILTERED TOKEN STATISTICS (ELIGIBLE JOBS ONLY)")
    print("-" * 40)
    print(f"Total Eligible Jobs: {eligible_count}")
    print(f"Total Input Tokens: {sum(all_input_tokens):,}")
    print(f"Total Output Tokens: {sum(all_output_tokens):,}")
    print(f"Total Tokens: {sum(all_total_tokens):,}")
    print(f"Average Input Tokens per Job: {statistics.mean(all_input_tokens):.0f}")
    print(f"Average Output Tokens per Job: {statistics.mean(all_output_tokens):.0f}")
    print(f"Average Total Tokens per Job: {statistics.mean(all_total_tokens):.0f}")
    print(f"Median Input Tokens: {statistics.median(all_input_tokens):.0f}")
    print(f"Median Output Tokens: {statistics.median(all_output_tokens):.0f}")
    print(f"Median Total Tokens: {statistics.median(all_total_tokens):.0f}")

    # P95, P99 calculations
    p95_input = sorted(all_input_tokens)[int(len(all_input_tokens) * 0.95)]
    p95_output = sorted(all_output_tokens)[int(len(all_output_tokens) * 0.95)]
    p95_total = sorted(all_total_tokens)[int(len(all_total_tokens) * 0.95)]
    p99_input = sorted(all_input_tokens)[int(len(all_input_tokens) * 0.99)]
    p99_output = sorted(all_output_tokens)[int(len(all_output_tokens) * 0.99)]
    p99_total = sorted(all_total_tokens)[int(len(all_total_tokens) * 0.99)]

    print(f"\nP95 Values:")
    print(f"  Input Tokens: {p95_input:.0f}")
    print(f"  Output Tokens: {p95_output:.0f}")
    print(f"  Total Tokens: {p95_total:.0f}")
    print(f"\nP99 Values:")
    print(f"  Input Tokens: {p99_input:.0f}")
    print(f"  Output Tokens: {p99_output:.0f}")
    print(f"  Total Tokens: {p99_total:.0f}")

    # Citation statistics
    print(f"\n📄 CITATION STATISTICS (FILTERED)")
    print(f"Average Citations per Job: {statistics.mean(citations_per_job):.1f}")
    print(f"Median Citations per Job: {statistics.median(citations_per_job):.0f}")
    print(f"Max Citations in a Job: {max(citations_per_job)}")

    # Daily breakdown
    print("\n📅 DAILY BREAKDOWN (ELIGIBLE JOBS)")
    print("-" * 40)
    for date in sorted(daily_stats.keys(), reverse=True):
        stats = daily_stats[date]
        jobs = stats['jobs']

        print(f"\n{date}:")
        print(f"  Eligible Jobs: {len(jobs)} (Free: {stats['user_types']['free']}, Paid: {stats['user_types']['paid']})")
        print(f"  Input Tokens: {sum(stats['input_tokens']):,} (avg: {statistics.mean(stats['input_tokens']):.0f})")
        print(f"  Output Tokens: {sum(stats['output_tokens']):,} (avg: {statistics.mean(stats['output_tokens']):.0f})")
        print(f"  Total Tokens: {sum(stats['total_tokens']):,} (avg: {statistics.mean(stats['total_tokens']):.0f})")
        print(f"  Citations: {sum(stats['citations'])} (avg: {statistics.mean(stats['citations']):.1f})")

        # Calculate tokens per citation for this day
        if sum(stats['citations']) > 0:
            tokens_per_citation = sum(stats['total_tokens']) / sum(stats['citations'])
            print(f"  Tokens per Citation: {tokens_per_citation:.1f}")

    # Threshold recommendations (more conservative due to filtering)
    print("\n🎯 THRESHOLD RECOMMENDATIONS (ELIGIBLE JOBS)")
    print("-" * 40)
    print(f"Input Token Warning: > {p95_input:.0f} (P95)")
    print(f"Input Token Critical: > {p99_input:.0f} (P99)")
    print(f"\nOutput Token Warning: > {p95_output:.0f} (P95)")
    print(f"Output Token Critical: > {p99_output:.0f} (P99)")
    print(f"\nTotal Token Warning: > {p95_total:.0f} (P95)")
    print(f"Total Token Critical: > {p99_total:.0f} (P99)")

    # Cost estimation
    print("\n💰 COST ANALYSIS (ELIGIBLE JOBS ONLY)")
    print("-" * 40)
    input_cost_per_1m = 0.075  # GPT-5-mini pricing
    output_cost_per_1m = 0.300

    total_input_cost = (sum(all_input_tokens) / 1_000_000) * input_cost_per_1m
    total_output_cost = (sum(all_output_tokens) / 1_000_000) * output_cost_per_1m
    total_cost = total_input_cost + total_output_cost

    print(f"Input Token Cost: ${total_input_cost:.2f}")
    print(f"Output Token Cost: ${total_output_cost:.2f}")
    print(f"Total Cost: ${total_cost:.2f}")
    print(f"Average Cost per Eligible Job: ${total_cost / eligible_count:.4f}")

    # Outlier detection
    print("\n🔍 OUTLIER DETECTION (ELIGIBLE JOBS)")
    print("-" * 40)

    # High token jobs (above P99)
    high_token_jobs = [job for job in eligible_jobs if job['total_tokens'] > p99_total]
    if high_token_jobs:
        print(f"Jobs above P99 ({p99_total:.0f} tokens): {len(high_token_jobs)}")
        for job in sorted(high_token_jobs, key=lambda x: x['total_tokens'], reverse=True)[:3]:
            print(f"  - {job['job_id']}: {job['total_tokens']:,} tokens, {job['citation_count']} citations")

    # High tokens per citation ratio
    tokens_per_citation_jobs = []
    for job in eligible_jobs:
        if job['citation_count'] > 0:
            ratio = job['total_tokens'] / job['citation_count']
            if ratio > 500:  # Unusually high
                tokens_per_citation_jobs.append((job, ratio))

    if tokens_per_citation_jobs:
        print(f"\nHigh token-per-citation ratios (>500): {len(tokens_per_citation_jobs)}")
        for job, ratio in sorted(tokens_per_citation_jobs, key=lambda x: x[1], reverse=True)[:3]:
            print(f"  - {job['job_id']}: {ratio:.0f} tokens/citation ({job['citation_count']} citations)")

    conn.close()

    return {
        'filtering': {
            'total_jobs': total_jobs,
            'eligible_jobs': eligible_count,
            'excluded_jobs': excluded_jobs,
            'eligibility_rate': eligible_count / total_jobs * 100
        },
        'statistics': {
            'total_input_tokens': sum(all_input_tokens),
            'total_output_tokens': sum(all_output_tokens),
            'total_tokens': sum(all_total_tokens),
            'avg_input_tokens': statistics.mean(all_input_tokens),
            'avg_output_tokens': statistics.mean(all_output_tokens),
            'avg_total_tokens': statistics.mean(all_total_tokens),
            'median_input_tokens': statistics.median(all_input_tokens),
            'median_output_tokens': statistics.median(all_output_tokens),
            'median_total_tokens': statistics.median(all_total_tokens),
            'p95_input': p95_input,
            'p95_output': p95_output,
            'p95_total': p95_total,
            'p99_input': p99_input,
            'p99_output': p99_output,
            'p99_total': p99_total
        },
        'citations': {
            'avg_citations_per_job': statistics.mean(citations_per_job),
            'median_citations_per_job': statistics.median(citations_per_job),
            'max_citations': max(citations_per_job)
        },
        'cost': {
            'total_cost': total_cost,
            'avg_cost_per_job': total_cost / eligible_count
        },
        'daily': daily_stats,
        'outliers': {
            'high_token_jobs': high_token_jobs,
            'high_ratio_jobs': tokens_per_citation_jobs
        }
    }


if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else None
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    stats = get_filtered_token_stats(db_path, days)