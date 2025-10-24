"""
Create train/validation/test split for DSPy optimization.

IMPORTANT: source_type is kept for reference but will NOT be provided to DSPy.
The model must detect the source type from the citation text itself.
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
        "citation_id": citation['citation_id'],
        "citation": citation['citation_text'],  # INPUT: only the text
        "is_valid": citation['is_valid'],
        "errors": citation.get('errors', []),
        # Keep source_type for reference/evaluation only, not for LLM input
        "_reference_source_type": citation.get('source_type', 'unknown')
    }


def stratified_split(valid_citations, invalid_citations, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15):
    """
    Create stratified split maintaining ratio of valid/invalid in each set.
    """
    random.seed(42)  # Reproducible splits

    # Shuffle both sets
    random.shuffle(valid_citations)
    random.shuffle(invalid_citations)

    # Calculate split sizes
    n_valid = len(valid_citations)
    n_invalid = len(invalid_citations)

    valid_train_end = int(n_valid * train_ratio)
    valid_val_end = valid_train_end + int(n_valid * val_ratio)

    invalid_train_end = int(n_invalid * train_ratio)
    invalid_val_end = invalid_train_end + int(n_invalid * val_ratio)

    # Split valid citations
    valid_train = valid_citations[:valid_train_end]
    valid_val = valid_citations[valid_train_end:valid_val_end]
    valid_test = valid_citations[valid_val_end:]

    # Split invalid citations
    invalid_train = invalid_citations[:invalid_train_end]
    invalid_val = invalid_citations[invalid_train_end:invalid_val_end]
    invalid_test = invalid_citations[invalid_val_end:]

    # Combine and convert to DSPy format
    train = [create_dspy_example(c) for c in valid_train + invalid_train]
    val = [create_dspy_example(c) for c in valid_val + invalid_val]
    test = [create_dspy_example(c) for c in valid_test + invalid_test]

    # Shuffle combined sets
    random.shuffle(train)
    random.shuffle(val)
    random.shuffle(test)

    return train, val, test


def main():
    # Load datasets
    valid_file = Path("backend/pseo/optimization/datasets/valid_citations_merged.jsonl")
    invalid_file = Path("backend/pseo/optimization/datasets/invalid_citations_enhanced.jsonl")

    valid_citations = load_citations(valid_file)
    invalid_citations = load_citations(invalid_file)

    print(f"Loaded {len(valid_citations)} valid citations")
    print(f"Loaded {len(invalid_citations)} invalid citations")
    print(f"Total: {len(valid_citations) + len(invalid_citations)}")

    # Create stratified split
    train, val, test = stratified_split(valid_citations, invalid_citations)

    # Save splits
    output_dir = Path("backend/pseo/optimization/datasets")

    with open(output_dir / "train.jsonl", 'w') as f:
        for example in train:
            f.write(json.dumps(example) + '\n')

    with open(output_dir / "val.jsonl", 'w') as f:
        for example in val:
            f.write(json.dumps(example) + '\n')

    with open(output_dir / "test.jsonl", 'w') as f:
        for example in test:
            f.write(json.dumps(example) + '\n')

    # Statistics
    print("\n" + "="*70)
    print("DATASET SPLIT STATISTICS")
    print("="*70)

    def print_stats(name, dataset):
        valid_count = sum(1 for ex in dataset if ex['is_valid'])
        invalid_count = len(dataset) - valid_count
        print(f"\n{name}:")
        print(f"  Total: {len(dataset)}")
        print(f"  Valid: {valid_count} ({valid_count/len(dataset)*100:.1f}%)")
        print(f"  Invalid: {invalid_count} ({invalid_count/len(dataset)*100:.1f}%)")

        # Error type distribution in invalid examples
        error_types = []
        for ex in dataset:
            if not ex['is_valid']:
                for error in ex['errors']:
                    error_types.append(error['component'])

        if error_types:
            print(f"  Error components:")
            for component, count in Counter(error_types).most_common(5):
                print(f"    {component}: {count}")

    print_stats("TRAINING SET", train)
    print_stats("VALIDATION SET", val)
    print_stats("TEST SET", test)

    print(f"\n✓ Saved to:")
    print(f"  - {output_dir / 'train.jsonl'}")
    print(f"  - {output_dir / 'val.jsonl'}")
    print(f"  - {output_dir / 'test.jsonl'}")

    print(f"\n📝 NOTE: source_type is NOT provided to DSPy - model must detect it!")


if __name__ == "__main__":
    main()
