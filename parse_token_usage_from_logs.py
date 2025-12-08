#!/usr/bin/env python3
"""
Parse token usage from log files for the last 3 days
"""
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import statistics
import gzip


def parse_logs_for_token_usage(log_paths: List[str], days: int = 3) -> Dict:
    """
    Parse log files to extract token usage information

    Args:
        log_paths: List of log file paths to parse
        days: Number of recent days to analyze

    Returns:
        Dictionary with token usage statistics
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    print(f"Analyzing token usage from logs")
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print("=" * 60)

    # Token usage pattern: "Token usage: X input + Y output = Z total"
    token_pattern = re.compile(r'Token usage: (\d+) (?:input|prompt) \+ (\d+) (?:output|completion|out) = (\d+) total')

    input_tokens = []
    output_tokens = []
    total_tokens = []
    daily_data = {}
    total_lines_processed = 0

    for log_path in log_paths:
        if not os.path.exists(log_path):
            print(f"⚠️  Log file not found: {log_path}")
            continue

        print(f"\n📂 Processing: {log_path}")

        # Determine if file is gzipped
        is_gzipped = log_path.endswith('.gz')
        open_func = gzip.open if is_gzipped else open

        try:
            with open_func(log_path, 'rt', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    total_lines_processed += 1

                    # Extract timestamp from log line
                    # Pattern: 2025-12-06 10:15:23
                    timestamp_match = re.search(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if not timestamp_match:
                        continue

                    try:
                        timestamp = datetime.strptime(timestamp_match.group(1), "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        continue

                    # Check if within date range
                    if not (start_date <= timestamp <= end_date):
                        continue

                    # Search for token usage pattern
                    match = token_pattern.search(line)
                    if match:
                        input_tok = int(match.group(1))
                        output_tok = int(match.group(2))
                        total_tok = int(match.group(3))

                        # Skip zero token entries
                        if total_tok == 0:
                            continue

                        input_tokens.append(input_tok)
                        output_tokens.append(output_tok)
                        total_tokens.append(total_tok)

                        # Group by day
                        date = timestamp.strftime('%Y-%m-%d')
                        if date not in daily_data:
                            daily_data[date] = {
                                'input': [],
                                'output': [],
                                'total': []
                            }

                        daily_data[date]['input'].append(input_tok)
                        daily_data[date]['output'].append(output_tok)
                        daily_data[date]['total'].append(total_tok)

        except Exception as e:
            print(f"❌ Error processing {log_path}: {e}")
            continue

    if not input_tokens:
        print("\n❌ No token usage data found in logs")
        print("\nSearched patterns:")
        print('  - "Token usage: X input + Y output = Z total"')
        print('  - "Token usage: X prompt + Y completion = Z total"')
        return {}

    print(f"\n📊 Log Processing Summary")
    print(f"Lines processed: {total_lines_processed:,}")
    print(f"Token usage entries found: {len(total_tokens)}")
    print(f"Date range with data: {len(daily_data)} days")

    # Calculate metrics
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
    print(f"  Input + Output = Total: {total_input + total_output:,} = {total_sum:,}")

    # Daily breakdown
    print(f"\n📅 DAILY BREAKDOWN")
    print("-" * 30)

    for date in sorted(daily_data.keys(), reverse=True):
        daily_input = daily_data[date]['input']
        daily_output = daily_data[date]['output']
        daily_total = daily_data[date]['total']

        print(f"\n{date}:")
        print(f"  Entries: {len(daily_total)}")
        print(f"  Input - Total: {sum(daily_input):,}, Avg: {statistics.mean(daily_input):.0f}, Median: {statistics.median(daily_input):.0f}")
        print(f"  Output - Total: {sum(daily_output):,}, Avg: {statistics.mean(daily_output):.0f}, Median: {statistics.median(daily_output):.0f}")
        print(f"  Total - Total: {sum(daily_total):,}, Avg: {statistics.mean(daily_total):.0f}, Median: {statistics.median(daily_total):.0f}")

    # Percentiles
    print(f"\n📈 PERCENTILES")
    print("-" * 30)

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
        print(f"  90th: {p90:.0f}")
        print(f"  95th: {p95:.0f}")
        print(f"  99th: {p99:.0f}")
        print(f"  Max: {max_val:.0f}")

        return p95  # Return P95 for threshold calculation

    input_p95 = get_percentiles(input_tokens, "Input Tokens")
    output_p95 = get_percentiles(output_tokens, "Output Tokens")
    total_p95 = get_percentiles(total_tokens, "Total Tokens")

    # Threshold recommendations
    print(f"\n🎯 THRESHOLD RECOMMENDATIONS (P95)")
    print("-" * 30)
    print(f"Input Token Alert: > {input_p95:.0f}")
    print(f"Output Token Alert: > {output_p95:.0f}")
    print(f"Total Token Alert: > {total_p95:.0f}")

    return {
        'overall': {
            'input': {
                'total': total_input,
                'average': avg_input,
                'median': median_input,
                'p95': input_p95
            },
            'output': {
                'total': total_output,
                'average': avg_output,
                'median': median_output,
                'p95': output_p95
            },
            'total': {
                'total': total_sum,
                'average': avg_total,
                'median': median_total,
                'p95': total_p95
            }
        },
        'daily': daily_data,
        'thresholds': {
            'input': input_p95,
            'output': output_p95,
            'total': total_p95
        }
    }


def main():
    import sys

    # Common log file locations
    log_paths = [
        '/var/log/citations/app.log',
        '/var/log/citations/app.log.1',
        '/opt/citations/logs/app.log',
        './logs/app.log',
        './backend/logs/app.log'
    ]

    # Add any paths from command line
    if len(sys.argv) > 1:
        log_paths.extend(sys.argv[1:])

    days = 3  # Last 3 days

    metrics = parse_logs_for_token_usage(log_paths, days)

    # Save to JSON if requested
    if '--save' in sys.argv:
        import json
        with open('token_metrics_from_logs.json', 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"\n✅ Metrics saved to token_metrics_from_logs.json")


if __name__ == "__main__":
    main()