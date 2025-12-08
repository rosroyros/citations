#!/usr/bin/env python3
"""
Token Threshold Monitor and Alert System
Analyzes token usage patterns and calculates dynamic thresholds
"""
import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import statistics
import argparse


class TokenThresholdMonitor:
    def __init__(self, db_path: str = None):
        """
        Initialize the token threshold monitor

        Args:
            db_path: Path to dashboard database
        """
        if not db_path:
            db_path = os.path.join(os.path.dirname(__file__), "dashboard", "data", "validations.db")
        self.db_path = db_path
        self.thresholds_file = "token_thresholds.json"

    def calculate_thresholds(self, days: int = 7) -> Dict:
        """
        Calculate token thresholds based on historical data

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with calculated thresholds
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Query token usage data
        query = """
            SELECT
                token_usage_prompt,
                token_usage_completion,
                token_usage_total,
                citation_count,
                user_type,
                created_at
            FROM validations
            WHERE created_at >= ?
            AND created_at <= ?
            AND token_usage_total IS NOT NULL
        """

        cursor.execute(query, (start_date.isoformat(), end_date.isoformat()))
        rows = cursor.fetchall()

        if len(rows) < 10:
            print(f"⚠️  Insufficient data: Only {len(rows)} jobs found in last {days} days")
            print("Need at least 10 jobs to calculate reliable thresholds")
            return {}

        # Extract token data
        input_tokens = [r[0] or 0 for r in rows if r[0]]
        output_tokens = [r[1] or 0 for r in rows if r[1]]
        total_tokens = [r[2] or 0 for r in rows if r[2]]

        # Remove zeros (indicate logging issues)
        input_tokens = [t for t in input_tokens if t > 0]
        output_tokens = [t for t in output_tokens if t > 0]
        total_tokens = [t for t in total_tokens if t > 0]

        if not input_tokens or not output_tokens or not total_tokens:
            print("⚠️  No valid token data found")
            return {}

        # Calculate statistics
        def calc_stats(data):
            return {
                'mean': statistics.mean(data),
                'median': statistics.median(data),
                'p90': sorted(data)[int(len(data) * 0.90)],
                'p95': sorted(data)[int(len(data) * 0.95)],
                'p99': sorted(data)[int(len(data) * 0.99)],
                'max': max(data),
                'min': min(data),
                'std': statistics.stdev(data) if len(data) > 1 else 0
            }

        input_stats = calc_stats(input_tokens)
        output_stats = calc_stats(output_tokens)
        total_stats = calc_stats(total_tokens)

        # Calculate thresholds using P95 + 2*STD
        thresholds = {
            'input_tokens': {
                'warning': int(input_stats['p95'] + 2 * input_stats['std']),
                'critical': int(input_stats['p95'] + 4 * input_stats['std']),
                'p50': int(input_stats['median']),
                'p90': int(input_stats['p90']),
                'p95': int(input_stats['p95']),
                'p99': int(input_stats['p99'])
            },
            'output_tokens': {
                'warning': int(output_stats['p95'] + 2 * output_stats['std']),
                'critical': int(output_stats['p95'] + 4 * output_stats['std']),
                'p50': int(output_stats['median']),
                'p90': int(output_stats['p90']),
                'p95': int(output_stats['p95']),
                'p99': int(output_stats['p99'])
            },
            'total_tokens': {
                'warning': int(total_stats['p95'] + 2 * total_stats['std']),
                'critical': int(total_stats['p95'] + 4 * total_stats['std']),
                'p50': int(total_stats['median']),
                'p90': int(total_stats['p90']),
                'p95': int(total_stats['p95']),
                'p99': int(total_stats['p99'])
            },
            'metadata': {
                'calculated_at': datetime.now().isoformat(),
                'days_analyzed': days,
                'total_jobs': len(rows),
                'valid_jobs': len(total_tokens)
            }
        }

        conn.close()
        return thresholds

    def check_current_jobs(self, thresholds: Dict, hours: int = 24) -> List[Dict]:
        """
        Check recent jobs against thresholds and flag anomalies

        Args:
            thresholds: Dictionary with threshold values
            hours: Number of recent hours to check

        Returns:
            List of anomalies found
        """
        if not thresholds:
            return []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get recent jobs
        start_time = datetime.now() - timedelta(hours=hours)

        query = """
            SELECT
                job_id,
                created_at,
                token_usage_prompt,
                token_usage_completion,
                token_usage_total,
                citation_count,
                user_type
            FROM validations
            WHERE created_at >= ?
            AND token_usage_total IS NOT NULL
            ORDER BY created_at DESC
        """

        cursor.execute(query, (start_time.isoformat(),))
        rows = cursor.fetchall()

        anomalies = []

        for row in rows:
            job_id, created_at, input_tok, output_tok, total_tok, citations, user_type = row
            input_tok = input_tok or 0
            output_tok = output_tok or 0
            total_tok = total_tok or 0

            issues = []

            # Check against thresholds
            if total_tok == 0:
                issues.append("ZERO_TOKENS")
            elif total_tok >= thresholds['total_tokens']['critical']:
                issues.append("CRITICAL_TOTAL_TOKENS")
            elif total_tok >= thresholds['total_tokens']['warning']:
                issues.append("WARNING_TOTAL_TOKENS")

            if input_tok > 0 and input_tok >= thresholds['input_tokens']['critical']:
                issues.append("CRITICAL_INPUT_TOKENS")
            elif input_tok > 0 and input_tok >= thresholds['input_tokens']['warning']:
                issues.append("WARNING_INPUT_TOKENS")

            if output_tok > 0 and output_tok >= thresholds['output_tokens']['critical']:
                issues.append("CRITICAL_OUTPUT_TOKENS")
            elif output_tok > 0 and output_tok >= thresholds['output_tokens']['warning']:
                issues.append("WARNING_OUTPUT_TOKENS")

            # Check for unusual ratios
            if input_tok > 0 and output_tok > 0:
                ratio = output_tok / input_tok
                if ratio > 5:  # Output much larger than input
                    issues.append("HIGH_OUTPUT_RATIO")
                elif ratio < 0.1:  # Input much larger than output
                    issues.append("LOW_OUTPUT_RATIO")

            # Check tokens per citation
            if citations and citations > 0 and total_tok > 0:
                tokens_per_citation = total_tok / citations
                if tokens_per_citation > 500:  # Unusually high tokens per citation
                    issues.append("HIGH_TOKENS_PER_CITATION")

            if issues:
                anomalies.append({
                    'job_id': job_id,
                    'created_at': created_at,
                    'input_tokens': input_tok,
                    'output_tokens': output_tok,
                    'total_tokens': total_tok,
                    'citation_count': citations,
                    'user_type': user_type,
                    'issues': issues
                })

        conn.close()
        return anomalies

    def save_thresholds(self, thresholds: Dict):
        """Save thresholds to JSON file"""
        with open(self.thresholds_file, 'w') as f:
            json.dump(thresholds, f, indent=2)
        print(f"✅ Thresholds saved to {self.thresholds_file}")

    def load_thresholds(self) -> Dict:
        """Load thresholds from JSON file"""
        if os.path.exists(self.thresholds_file):
            with open(self.thresholds_file, 'r') as f:
                return json.load(f)
        return {}

    def print_report(self, thresholds: Dict, anomalies: List[Dict]):
        """Print a comprehensive report"""
        print("\n" + "=" * 80)
        print("🎯 TOKEN THRESHOLD ANALYSIS REPORT")
        print("=" * 80)

        if not thresholds:
            print("❌ No threshold data available")
            return

        # Print thresholds
        print("\n📊 CALCULATED THRESHOLDS")
        print("-" * 40)
        print("Input Tokens:")
        print(f"  P50: {thresholds['input_tokens']['p50']:,}")
        print(f"  P90: {thresholds['input_tokens']['p90']:,}")
        print(f"  P95: {thresholds['input_tokens']['p95']:,} (warning level)")
        print(f"  Warning: > {thresholds['input_tokens']['warning']:,}")
        print(f"  Critical: > {thresholds['input_tokens']['critical']:,}")

        print("\nOutput Tokens:")
        print(f"  P50: {thresholds['output_tokens']['p50']:,}")
        print(f"  P90: {thresholds['output_tokens']['p90']:,}")
        print(f"  P95: {thresholds['output_tokens']['p95']:,} (warning level)")
        print(f"  Warning: > {thresholds['output_tokens']['warning']:,}")
        print(f"  Critical: > {thresholds['output_tokens']['critical']:,}")

        print("\nTotal Tokens:")
        print(f"  P50: {thresholds['total_tokens']['p50']:,}")
        print(f"  P90: {thresholds['total_tokens']['p90']:,}")
        print(f"  P95: {thresholds['total_tokens']['p95']:,} (warning level)")
        print(f"  Warning: > {thresholds['total_tokens']['warning']:,}")
        print(f"  Critical: > {thresholds['total_tokens']['critical']:,}")

        # Print anomalies
        if anomalies:
            print(f"\n🚨 ANOMALIES DETECTED (last 24 hours)")
            print("-" * 40)
            print(f"Total anomalies: {len(anomalies)}")

            # Group by issue type
            issue_counts = {}
            for anomaly in anomalies:
                for issue in anomaly['issues']:
                    issue_counts[issue] = issue_counts.get(issue, 0) + 1

            print("\nBreakdown by issue type:")
            for issue, count in sorted(issue_counts.items()):
                print(f"  {issue}: {count}")

            # Show top 5 anomalies by token count
            print("\nTop 5 anomalies by total tokens:")
            top_anomalies = sorted(anomalies, key=lambda x: x['total_tokens'], reverse=True)[:5]
            for anomaly in top_anomalies:
                issues_str = ", ".join(anomaly['issues'])
                print(f"\n  Job: {anomaly['job_id']}")
                print(f"    Tokens: {anomaly['total_tokens']:,} (in: {anomaly['input_tokens']:,}, out: {anomaly['output_tokens']:,})")
                print(f"    Issues: {issues_str}")
                print(f"    Citations: {anomaly['citation_count']}")
        else:
            print("\n✅ No anomalies detected in the last 24 hours")

        print(f"\n📈 Analysis based on {thresholds['metadata']['total_jobs']} jobs")
        print(f"   Calculated on: {thresholds['metadata']['calculated_at']}")


def main():
    parser = argparse.ArgumentParser(description="Token Threshold Monitor")
    parser.add_argument("--days", type=int, default=7, help="Days to analyze for threshold calculation")
    parser.add_argument("--hours", type=int, default=24, help="Hours to check for anomalies")
    parser.add_argument("--db", type=str, help="Path to database file")
    parser.add_argument("--recalculate", action="store_true", help="Force recalculation of thresholds")
    args = parser.parse_args()

    monitor = TokenThresholdMonitor(args.db)

    # Load or calculate thresholds
    if args.recalculate or not os.path.exists(monitor.thresholds_file):
        print(f"🔄 Calculating thresholds based on last {args.days} days...")
        thresholds = monitor.calculate_thresholds(args.days)
        if thresholds:
            monitor.save_thresholds(thresholds)
    else:
        print("📂 Loading existing thresholds...")
        thresholds = monitor.load_thresholds()

    # Check for anomalies
    if thresholds:
        print(f"\n🔍 Checking recent jobs (last {args.hours} hours)...")
        anomalies = monitor.check_current_jobs(thresholds, args.hours)
        monitor.print_report(thresholds, anomalies)

        # Exit with error code if critical anomalies found
        critical_anomalies = [a for a in anomalies if any('CRITICAL' in issue for issue in a['issues'])]
        if critical_anomalies:
            print(f"\n⚠️  Found {len(critical_anomalies)} critical anomalies!")
            exit(1)


if __name__ == "__main__":
    main()