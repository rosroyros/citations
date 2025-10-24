"""Analyze what errors the optimized validator is making"""
import json
from pathlib import Path
from dspy_validator import CitationValidator, load_dataset
from dspy_config import setup_dspy


def main():
    # Setup
    setup_dspy()

    # Load optimized validator
    validator = CitationValidator()
    validator.load("backend/pseo/optimization/models/optimized_validator.json")

    # Load test set
    test_data = load_dataset("backend/pseo/optimization/datasets/test_v2.jsonl")

    print("="*80)
    print("ANALYZING VALIDATION ERRORS")
    print("="*80)

    false_positives = []
    false_negatives = []
    true_positives = []

    for example in test_data:
        citation = example.citation
        expected_valid = example.is_valid
        expected_errors = example.errors if hasattr(example, 'errors') else []

        # Run validation
        result = validator(citation=citation)
        predicted_valid = result.is_valid
        predicted_errors = result.errors

        # Categorize
        if not expected_valid and not predicted_valid:
            # True positive - correctly found errors
            true_positives.append({
                'citation': citation[:100],
                'expected': expected_errors,
                'predicted': predicted_errors
            })
        elif expected_valid and not predicted_valid:
            # False positive - flagged valid citation as invalid
            false_positives.append({
                'citation': citation[:100],
                'predicted_errors': predicted_errors
            })
        elif not expected_valid and predicted_valid:
            # False negative - missed actual errors
            false_negatives.append({
                'citation': citation[:100],
                'expected_errors': expected_errors
            })

    # Report false positives (most concerning)
    print(f"\nFALSE POSITIVES: {len(false_positives)}")
    print("="*80)
    print("Valid citations incorrectly flagged as having errors:\n")

    for i, fp in enumerate(false_positives[:10], 1):  # Show first 10
        print(f"{i}. {fp['citation']}...")
        print(f"   Predicted errors:")
        for err in fp['predicted_errors']:
            print(f"     - {err['component']}: {err['problem']}")
        print()

    # Report false negatives
    print(f"\nFALSE NEGATIVES: {len(false_negatives)}")
    print("="*80)
    print("Invalid citations that were marked as valid:\n")

    for i, fn in enumerate(false_negatives[:5], 1):
        print(f"{i}. {fn['citation']}...")
        print(f"   Expected errors:")
        for err in fn['expected_errors']:
            print(f"     - {err['component']}: {err['problem']}")
        print()

    # Report true positives (working correctly)
    print(f"\nTRUE POSITIVES: {len(true_positives)}")
    print("="*80)
    print("Correctly identified invalid citations:\n")

    for i, tp in enumerate(true_positives[:5], 1):
        print(f"{i}. {tp['citation']}...")
        print(f"   Expected: {len(tp['expected'])} errors")
        print(f"   Found: {len(tp['predicted'])} errors")
        print()

    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total test examples: {len(test_data)}")
    print(f"True Positives: {len(true_positives)}")
    print(f"False Positives: {len(false_positives)} ⚠️ (valid → flagged as invalid)")
    print(f"False Negatives: {len(false_negatives)} ⚠️ (invalid → marked as valid)")
    print(f"\nPrecision: {len(true_positives)/(len(true_positives)+len(false_positives)):.2%}")
    print(f"Recall: {len(true_positives)/(len(true_positives)+len(false_negatives)):.2%}")


if __name__ == "__main__":
    main()
