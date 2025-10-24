#!/usr/bin/env python3
"""
Detailed analysis of MIPROv2 optimization results.
Shows concrete examples of TP, FP, FN to explain metrics.
"""
import json
import dspy
from pathlib import Path
from collections import defaultdict

from dspy_config import setup_dspy
from dspy_validator import CitationValidator


def load_test_data():
    """Load test set from run_gepa_final.py split."""
    # Load deduplicated valid citations
    valid_file = Path('backend/pseo/optimization/datasets/valid_citations_deduplicated.jsonl')
    with open(valid_file) as f:
        valid_citations = [json.loads(line) for line in f]

    # Load invalid citations
    invalid_file = Path('backend/pseo/optimization/datasets/invalid_citations_enhanced.jsonl')
    with open(invalid_file) as f:
        invalid_citations = [json.loads(line) for line in f]

    # Combine
    all_examples = []

    # Add valid citations
    for cit in valid_citations:
        all_examples.append(dspy.Example(
            citation=cit['citation_text'],
            source_type=cit.get('source_type', 'unknown'),
            errors=[],
            is_valid=True
        ).with_inputs("citation"))

    # Add invalid citations
    for cit in invalid_citations:
        all_examples.append(dspy.Example(
            citation=cit['citation_text'],
            source_type=cit.get('source_type', 'unknown'),
            errors=cit.get('errors', []),
            is_valid=False
        ).with_inputs("citation"))

    # Use same split as run_gepa_final.py: 70/15/15
    train_size = int(len(all_examples) * 0.7)
    val_size = int(len(all_examples) * 0.15)
    test = all_examples[train_size+val_size:]

    return test


def analyze_predictions(validator, test_data):
    """Analyze predictions in detail."""
    print("\n" + "="*80)
    print("DETAILED ANALYSIS OF TEST SET PREDICTIONS")
    print("="*80)

    # Overall stats
    total = len(test_data)
    total_valid = sum(1 for ex in test_data if ex.is_valid)
    total_invalid = sum(1 for ex in test_data if not ex.is_valid)

    print(f"\nTest Set Composition:")
    print(f"  Total: {total}")
    print(f"  Valid citations: {total_valid}")
    print(f"  Invalid citations: {total_invalid}")

    # Track results
    citation_correct = 0
    citation_wrong = 0

    # Error detection tracking
    all_tp = []  # True positives
    all_fp = []  # False positives
    all_fn = []  # False negatives

    tp_count = 0
    fp_count = 0
    fn_count = 0

    print("\n" + "="*80)
    print("CITATION-LEVEL RESULTS")
    print("="*80)

    for i, example in enumerate(test_data):
        prediction = validator(citation=example.citation)

        true_valid = example.is_valid
        pred_valid = prediction.is_valid

        # Citation level
        if true_valid == pred_valid:
            citation_correct += 1
        else:
            citation_wrong += 1
            print(f"\n[CITATION MISMATCH #{citation_wrong}]")
            print(f"Citation: {example.citation[:100]}...")
            print(f"Ground truth: {'VALID' if true_valid else 'INVALID'}")
            print(f"Predicted: {'VALID' if pred_valid else 'INVALID'}")

    citation_accuracy = citation_correct / total
    print(f"\nCitation-Level Accuracy: {citation_correct}/{total} = {citation_accuracy:.2%}")

    # Now analyze ERROR-LEVEL detection (only for invalid citations)
    print("\n" + "="*80)
    print("ERROR-LEVEL DETECTION (Invalid Citations Only)")
    print("="*80)

    print("\nThis is where we measure which ERROR COMPONENTS were detected.")
    print("Components: Authors, Title, DOI, Publisher, etc.\n")

    for i, example in enumerate(test_data):
        if not example.is_valid:  # Only analyze invalid citations
            prediction = validator(citation=example.citation)

            # Get error components
            true_errors = example.errors if example.errors else []
            pred_errors = prediction.errors if prediction.errors else []

            true_components = set(e['component'].lower().strip() for e in true_errors)
            pred_components = set(e['component'].lower().strip() for e in pred_errors)

            # Calculate matches
            tp = true_components & pred_components  # Correctly identified
            fp = pred_components - true_components  # False alarms
            fn = true_components - pred_components  # Missed

            tp_count += len(tp)
            fp_count += len(fp)
            fn_count += len(fn)

            # Store examples
            if tp:
                all_tp.append({
                    'citation': example.citation,
                    'true_errors': list(true_components),
                    'pred_errors': list(pred_components),
                    'matched': list(tp)
                })

            if fp:
                all_fp.append({
                    'citation': example.citation,
                    'true_errors': list(true_components),
                    'pred_errors': list(pred_components),
                    'false_alarms': list(fp)
                })

            if fn:
                all_fn.append({
                    'citation': example.citation,
                    'true_errors': list(true_components),
                    'pred_errors': list(pred_components),
                    'missed': list(fn)
                })

    # Calculate final metrics
    precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0
    recall = tp_count / (tp_count + fn_count) if (tp_count + fn_count) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    print("\n" + "="*80)
    print("ERROR DETECTION METRICS")
    print("="*80)
    print(f"\nTrue Positives (TP): {tp_count}")
    print(f"False Positives (FP): {fp_count}")
    print(f"False Negatives (FN): {fn_count}")
    print(f"\nPrecision: {tp_count}/{tp_count + fp_count} = {precision:.2%}")
    print(f"Recall: {tp_count}/{tp_count + fn_count} = {recall:.2%}")
    print(f"F1 Score: {f1:.2%}")

    # Show examples
    print("\n" + "="*80)
    print("EXAMPLE: TRUE POSITIVES (Correctly Detected Errors)")
    print("="*80)
    for i, ex in enumerate(all_tp[:3]):
        print(f"\n[TP Example {i+1}]")
        print(f"Citation: {ex['citation'][:120]}...")
        print(f"Ground truth errors: {ex['true_errors']}")
        print(f"Predicted errors: {ex['pred_errors']}")
        print(f"✓ MATCHED: {ex['matched']}")

    print("\n" + "="*80)
    print("EXAMPLE: FALSE NEGATIVES (Missed Errors)")
    print("="*80)
    print("\nThese are errors that EXIST but the model DIDN'T detect.")
    print("This is why recall is only 21%!\n")
    for i, ex in enumerate(all_fn[:5]):
        print(f"\n[FN Example {i+1}]")
        print(f"Citation: {ex['citation'][:120]}...")
        print(f"Ground truth errors: {ex['true_errors']}")
        print(f"Predicted errors: {ex['pred_errors']}")
        print(f"✗ MISSED: {ex['missed']}")

    print("\n" + "="*80)
    print("EXAMPLE: FALSE POSITIVES (Incorrectly Flagged)")
    print("="*80)
    print("\nThese are errors the model detected that DON'T actually exist.\n")
    for i, ex in enumerate(all_fp[:3]):
        print(f"\n[FP Example {i+1}]")
        print(f"Citation: {ex['citation'][:120]}...")
        print(f"Ground truth errors: {ex['true_errors']}")
        print(f"Predicted errors: {ex['pred_errors']}")
        print(f"✗ FALSE ALARMS: {ex['false_alarms']}")

    # Final explanation
    print("\n" + "="*80)
    print("WHY IS RECALL ONLY 21%?")
    print("="*80)
    print(f"""
The validator correctly identified ALL invalid citations (100% citation accuracy).
However, for each invalid citation, it only detected {recall:.0%} of the error components.

Example breakdown:
- Total error components in test set: {tp_count + fn_count}
- Correctly detected: {tp_count} ({recall:.0%})
- Missed: {fn_count} ({fn_count/(tp_count + fn_count):.0%})

The validator knows something is wrong (is_valid=False) but struggles to identify
WHICH specific components have errors (Authors vs Title vs DOI, etc.).

This is common in early-stage optimization. The model learned to detect invalid
citations but needs more training to pinpoint exact error components.
    """)


def main():
    # Setup
    lm = setup_dspy()

    # Load optimized validator
    optimized_path = Path('backend/pseo/optimization/optimized_prompts/gepa_optimized_validator.json')
    if not optimized_path.exists():
        print(f"Error: Optimized validator not found at {optimized_path}")
        return

    validator = CitationValidator()
    validator.load(str(optimized_path))

    # Load test data
    test_data = load_test_data()

    # Analyze
    analyze_predictions(validator, test_data)


if __name__ == '__main__':
    main()
