"""
Extract validation set from final_merged_dataset_v2.jsonl using seed=42 stratified split.

Uses same split logic as run_gepa_optimization_v2.py (80/20 split with seed=42).
"""
import json
import random
from pathlib import Path
from collections import Counter


def load_citations(filepath):
    """Load citations from JSONL file."""
    citations = []
    with open(filepath, 'r') as f:
        for line in f:
            citations.append(json.loads(line.strip()))
    return citations


def create_dspy_example(citation):
    """
    Convert citation to DSPy format.

    CRITICAL: Do NOT include source_type in input - LLM must detect it!
    """
    return {
        "citation": citation['citation'],  # INPUT: only the text
        "is_valid": citation['is_valid'],
        "errors": citation.get('errors', []),
        # Keep source_type for reference/evaluation only, not for LLM input
        "_reference_source_type": citation.get('metadata', {}).get('source_type', 'unknown')
    }


def stratified_split(valid_citations, invalid_citations, train_ratio=0.80, val_ratio=0.20):
    """
    Create stratified split maintaining ratio of valid/invalid in each set.

    Note: This matches the logic from create_dataset_split.py but uses 80/20 split
    instead of 70/15/15 since we only need train+validation for competitive benchmark.
    """
    random.seed(42)  # Reproducible splits

    # Shuffle both sets
    random.shuffle(valid_citations)
    random.shuffle(invalid_citations)

    # Calculate split sizes
    n_valid = len(valid_citations)
    n_invalid = len(invalid_citations)

    valid_train_end = int(n_valid * train_ratio)

    invalid_train_end = int(n_invalid * train_ratio)

    # Split valid citations
    valid_train = valid_citations[:valid_train_end]
    valid_val = valid_citations[valid_train_end:]

    # Split invalid citations
    invalid_train = invalid_citations[:invalid_train_end]
    invalid_val = invalid_citations[invalid_train_end:]

    # Combine and convert to DSPy format
    train = [create_dspy_example(c) for c in valid_train + invalid_train]
    val = [create_dspy_example(c) for c in valid_val + invalid_val]

    # Shuffle combined sets
    random.shuffle(train)
    random.shuffle(val)

    return train, val


def main():
    print("="*70)
    print("EXTRACTING VALIDATION SET FOR COMPETITIVE BENCHMARK")
    print("="*70)

    # Load dataset
    dataset_file = Path("../Checker_Prompt_Optimization/final_merged_dataset_v2.jsonl")

    if not dataset_file.exists():
        print(f"❌ Dataset file not found: {dataset_file}")
        print("Please ensure final_merged_dataset_v2.jsonl exists in Checker_Prompt_Optimization/")
        return

    citations = load_citations(dataset_file)
    print(f"Loaded {len(citations)} total citations")

    # Separate valid/invalid
    valid_citations = [c for c in citations if c['is_valid']]
    invalid_citations = [c for c in citations if not c['is_valid']]

    print(f"  Valid: {len(valid_citations)}")
    print(f"  Invalid: {len(invalid_citations)}")

    # Create stratified split (80/20 with seed=42)
    train, val = stratified_split(valid_citations, invalid_citations)

    # Save validation set
    output_dir = Path(".")
    val_file = output_dir / "validation_set.jsonl"

    with open(val_file, 'w') as f:
        for example in val:
            f.write(json.dumps(example) + '\n')

    # Statistics
    print("\n" + "="*70)
    print("SPLIT STATISTICS (seed=42, 80/20)")
    print("="*70)

    def print_stats(name, dataset):
        valid_count = sum(1 for ex in dataset if ex['is_valid'])
        invalid_count = len(dataset) - valid_count
        print(f"\n{name}:")
        print(f"  Total: {len(dataset)}")
        print(f"  Valid: {valid_count} ({valid_count/len(dataset)*100:.1f}%)")
        print(f"  Invalid: {invalid_count} ({invalid_count/len(dataset)*100:.1f}%)")

    print_stats("TRAINING SET", train)
    print_stats("VALIDATION SET", val)

    # Expected values for validation set (20% of total)
    expected_val_total = len(citations) * 0.20
    expected_val_valid = len(valid_citations) * 0.20
    expected_val_invalid = len(invalid_citations) * 0.20

    print(f"\nExpected validation set (20%):")
    print(f"  Total: ~{expected_val_total:.0f}")
    print(f"  Valid: ~{expected_val_valid:.0f}")
    print(f"  Invalid: ~{expected_val_invalid:.0f}")

    # Verify we're close to expected values
    val_valid_count = sum(1 for ex in val if ex['is_valid'])
    val_invalid_count = len(val) - val_valid_count

    print(f"\n✅ Validation set extracted:")
    print(f"  File: {val_file}")
    print(f"  Total: {len(val)} citations")
    print(f"  Valid: {val_valid_count}")
    print(f"  Invalid: {val_invalid_count}")

    # Success criteria
    print(f"\n" + "="*70)
    print("VERIFICATION")
    print("="*70)

    if abs(len(val) - expected_val_total) <= 2:
        print("✅ Total count matches expected 20% split")
    else:
        print(f"⚠️  Total count deviation: {len(val) - expected_val_total}")

    if abs(val_valid_count - expected_val_valid) <= 1:
        print("✅ Valid count matches expected 20% split")
    else:
        print(f"⚠️  Valid count deviation: {val_valid_count - expected_val_valid}")

    if abs(val_invalid_count - expected_val_invalid) <= 1:
        print("✅ Invalid count matches expected 20% split")
    else:
        print(f"⚠️  Invalid count deviation: {val_invalid_count - expected_val_invalid}")

    print(f"\n📝 Ready for competitive benchmark testing!")


if __name__ == "__main__":
    main()