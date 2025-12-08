#!/usr/bin/env python3
"""
Average results from multiple OpenAI Responses API test runs.

Usage: python3 average_results.py

This script loads results from multiple test runs and calculates
averaged accuracy with standard deviation for statistical validation.
"""
import json
import sys
import os
from pathlib import Path

def load_all_runs():
    """Load results from all run files."""
    results = {}

    # Find all run files
    run_files = list(Path("Checker_Prompt_Optimization").glob("responses_api_run*.json"))
    run_files.sort(key=lambda x: int(x.stem.split("_")[1]))  # Sort by run number

    if not run_files:
        print("❌ No run files found. Expected: responses_api_run1.json, run2.json, run3.json")
        return None

    print(f"📊 Loading {len(run_files)} run files: {[f.name for f in run_files]}")

    for run_file in run_files:
        print(f"  Loading {run_file.name}...")
        with open(run_file, 'r') as f:
            run_data = json.load(f)

        for approach in ['old', 'new_v1', 'new_v2']:
            if approach not in results:
                results[approach] = {
                    'accuracies': [],
                    'response_lengths': [],
                    'correct_counts': [],
                    'parsed_counts': []
                }

            results[approach]['accuracies'].append(run_data[approach]['accuracy'])
            results[approach]['response_lengths'].append(run_data[approach]['response_length'])
            results[approach]['correct_counts'].append(run_data[approach]['details'])
            results[approach]['parsed_counts'].append(run_data[approach]['parsed_count'])

    return results

def calculate_statistics(results):
    """Calculate means, standard deviations, and confidence intervals."""
    if not results:
        return None

    print(f"\n📈 STATISTICAL ANALYSIS")
    print("=" * 50)

    stats = {}

    for approach, data in results.items():
        n = len(data['accuracies'])
        if n == 0:
            continue

        # Basic statistics
        avg_accuracy = sum(data['accuracies']) / n
        std_dev = (sum((x - avg_accuracy) ** 2 for x in data['accuracies']) / n) ** 0.5

        # Standard error (for confidence intervals)
        std_error = std_dev / (n ** 0.5)

        # 95% confidence interval
        margin_of_error = 1.96 * std_error
        ci_lower = avg_accuracy - margin_of_error
        ci_upper = avg_accuracy + margin_of_error

        # Response length stats
        avg_length = sum(data['response_lengths']) / n
        total_correct = sum(data['correct_counts'])

        stats[approach] = {
            'avg_accuracy': avg_accuracy,
            'std_dev': std_dev,
            'std_error': std_error,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'n_runs': n,
            'avg_response_length': avg_length,
            'total_correct': total_correct,
            'total_possible': total_correct / (avg_accuracy / 100) if avg_accuracy > 0 else 0,
            'raw_accuracies': data['accuracies'],
            'raw_response_lengths': data['response_lengths']
        }

        print(f"{approach.upper()}:")
        print(f"  Accuracy: {avg_accuracy:.2f}% ± {std_dev:.2f%}")
        print(f"  95% CI: [{ci_lower:.2f}%, {ci_upper:.2f}%]")
        print(f"  Response length: {avg_length:,.0f} chars avg")
        print(f"  Correct: {total_correct}/{stats[approach]['total_possible']} citations")
        print(f"  Runs: {n}")
        print()

    return stats

def compare_approaches(stats):
    """Compare approaches and determine statistical significance."""
    if not stats or len(stats) < 2:
        return

    print("🔍 APPROACH COMPARISONS")
    print("=" * 30)

    approaches = list(stats.keys())

    # All pairwise comparisons
    for i in range(len(approaches)):
        for j in range(i + 1, len(approaches)):
            app1 = approaches[i]
            app2 = approaches[j]

            if app1 in stats and app2 in stats:
                diff = stats[app1]['avg_accuracy'] - stats[app2]['avg_accuracy']
                pooled_se = ((stats[app1]['std_dev']**2 * (stats[app1]['n_runs']-1) +
                             stats[app2]['std_dev']**2 * (stats[app2]['n_runs']-1)) / \
                            (stats[app1]['n_runs'] + stats[app2]['n_runs'] - 2))
                t_stat = diff / pooled_se
                p_value = 2 * (1 - abs(t_stat))  # Two-tailed approximation

                print(f"{app1.upper()} vs {app2.upper()}:")
                print(f"  Difference: {diff:+.2f}%")
                print(f"  T-statistic: {t_stat:.3f}")
                print(f"  P-value: {p_value:.3f}")

                if p_value < 0.05:
                    print(f"  🔍 STATISTICALLY SIGNIFICANT (p < 0.05)")
                else:
                    print(f"  ⚖️  Not statistically significant")
                print()

    # Find winner
    winner = max(stats.keys(), key=lambda x: stats[x]['avg_accuracy'])
    print(f"🏆 OVERALL WINNER: {winner.upper()} ({stats[winner]['avg_accuracy']:.2f}% accuracy)")

def save_averaged_results(stats):
    """Save averaged results to file."""
    if not stats:
        return

    output_file = "Checker_Prompt_Optimization/averaged_results.json"

    # Add metadata
    averaged_data = {
        'metadata': {
            'total_runs': max([s['n_runs'] for s in stats.values()]),
            'total_citations_per_run': 121,
            'total_data_points_per_approach': max([s['n_runs'] * 121 for s in stats.values()]),
            'test_date': '2025-12-04',
            'based_on_issue': 'citations-w9pl',
            'linked_issue': 'citations-ogih'
        },
        'results': stats
    }

    with open(output_file, 'w') as f:
        json.dump(averaged_data, f, indent=2)

    print(f"💾 Averaged results saved to: {output_file}")

def main():
    """Main execution function."""
    print("🎯 OpenAI Responses API - Averaged Results Calculator")
    print("=" * 50)

    # Load all run results
    results = load_all_runs()
    if not results:
        print("❌ No results found to average.")
        sys.exit(1)

    # Calculate statistics
    stats = calculate_statistics(results)
    if not stats:
        print("❌ No statistics calculated.")
        sys.exit(1)

    # Compare approaches
    compare_approaches(stats)

    # Save averaged results
    save_averaged_results(stats)

    print("\n✅ Averaged results calculation completed!")

if __name__ == "__main__":
    main()