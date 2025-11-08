#!/usr/bin/env python3
"""
Recalculate benchmark accuracies by properly parsing raw LLM responses.
Fixes the bug where all predictions defaulted to True.
"""

import json
import re
from pathlib import Path
from typing import Dict, Tuple

def parse_raw_response(raw_response: str) -> bool:
    """
    Parse raw LLM response to boolean.
    Returns True if valid, False if invalid.
    """
    response = raw_response.strip().lower()

    # Direct matches
    if response == "valid":
        return True
    if response == "invalid":
        return False

    # Check for valid/invalid in response
    if "valid" in response and "invalid" not in response:
        return True
    if "invalid" in response:
        return False

    # Default: if unclear, mark as True (optimistic)
    print(f"  ⚠️  Unclear response: '{raw_response}' -> defaulting to True")
    return True


def recalculate_file(filepath: Path) -> Tuple[int, int, float]:
    """
    Recalculate accuracy for a single JSONL file.
    Returns (correct_count, total_count, accuracy).
    """
    correct = 0
    total = 0
    unclear_count = 0

    lines = []
    with open(filepath) as f:
        for line in f:
            data = json.loads(line)
            total += 1

            # Parse raw response properly
            predicted = parse_raw_response(data['raw_response'])
            ground_truth = data['ground_truth']

            is_correct = (predicted == ground_truth)
            if is_correct:
                correct += 1

            # Update the data
            data['predicted'] = predicted
            data['correct'] = is_correct
            lines.append(data)

    accuracy = correct / total if total > 0 else 0.0

    # Write corrected file
    corrected_path = filepath.parent / f"{filepath.stem}_corrected.jsonl"
    with open(corrected_path, 'w') as f:
        for data in lines:
            f.write(json.dumps(data) + '\n')

    return correct, total, accuracy


def main():
    benchmark_dir = Path("competitive_benchmark")

    # Find all detailed_121 JSONL files
    files = list(benchmark_dir.glob("*_detailed_121.jsonl"))

    if not files:
        print("❌ No *_detailed_121.jsonl files found")
        return

    print(f"Found {len(files)} files to recalculate\n")

    results = {}

    for filepath in sorted(files):
        model_name = filepath.stem.replace("_detailed_121", "")
        print(f"Processing {model_name}...")

        correct, total, accuracy = recalculate_file(filepath)
        results[model_name] = accuracy

        print(f"  ✓ {correct}/{total} = {accuracy:.4f} ({accuracy*100:.2f}%)")
        print(f"  Corrected file: {filepath.stem}_corrected.jsonl\n")

    # Sort by accuracy
    ranking = sorted(results.items(), key=lambda x: x[1], reverse=True)

    # Create summary
    summary = {
        "timestamp": "2025-11-07 PROPERLY_RECALCULATED",
        "test_type": "DETAILED_121_CITATION_TEST_CORRECTED",
        "citations_tested": 121,
        "models_tested": len(set(m.rsplit('_', 1)[0] for m in results.keys())),
        "combinations": len(results),
        "accuracies": results,
        "ranking": ranking
    }

    # Write summary
    summary_path = benchmark_dir / "detailed_121_test_summary_corrected.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print("\n" + "="*70)
    print("CORRECTED BENCHMARK RESULTS")
    print("="*70)
    print(f"\n{'Rank':<6} {'Model':<35} {'Accuracy':<10}")
    print("-" * 70)

    for rank, (model, acc) in enumerate(ranking, 1):
        print(f"{rank:<6} {model:<35} {acc*100:>6.2f}%")

    print(f"\n✅ Summary saved to: {summary_path}")
    print(f"✅ Corrected JSONL files saved with '_corrected' suffix")


if __name__ == "__main__":
    main()
