"""
Detailed citation-by-citation analysis of optimized validator.
"""
import dspy
from dspy_validator import (
    CitationValidator,
    load_dataset,
    citation_validator_metric,
    calculate_error_metrics
)
from dspy_config import setup_dspy
from pathlib import Path
import json

def analyze_citation_by_citation():
    """Analyze each citation in the test set with detailed output."""

    # Setup DSPy
    print("Setting up DSPy...")
    lm = setup_dspy()

    # Load optimized validator
    print("Loading optimized validator...")
    optimized_path = Path('backend/pseo/optimization/optimized_prompts/gepa_optimized_validator.json')

    if not optimized_path.exists():
        print(f"ERROR: Optimized validator not found at {optimized_path}")
        return

    validator = CitationValidator()
    validator.load(str(optimized_path))

    # Load test data
    print("Loading test dataset...")
    # Use same split as optimization
    import random

    # Load deduplicated valid citations
    valid_file = Path('backend/pseo/optimization/datasets/valid_citations_deduplicated.jsonl')
    with open(valid_file) as f:
        valid_citations = [json.loads(line) for line in f]

    # Load standardized invalid citations
    invalid_file = Path('backend/pseo/optimization/datasets/invalid_citations_standardized.jsonl')
    with open(invalid_file) as f:
        invalid_citations = [json.loads(line) for line in f]

    # Combine and shuffle with same seed
    all_examples = []
    for cit in valid_citations:
        all_examples.append(dspy.Example(
            citation=cit['citation_text'],
            source_type=cit.get('source_type', 'unknown'),
            errors=[],
            is_valid=True
        ).with_inputs("citation"))

    for cit in invalid_citations:
        all_examples.append(dspy.Example(
            citation=cit['citation_text'],
            source_type=cit.get('source_type', 'unknown'),
            errors=cit.get('errors', []),
            is_valid=False
        ).with_inputs("citation"))

    random.seed(42)
    random.shuffle(all_examples)

    # Split 70/15/15
    train_size = int(len(all_examples) * 0.7)
    val_size = int(len(all_examples) * 0.15)

    test_data = all_examples[train_size+val_size:]

    print(f"\nTest set: {len(test_data)} examples")
    print(f"  Valid: {sum(1 for ex in test_data if ex.is_valid)}")
    print(f"  Invalid: {sum(1 for ex in test_data if not ex.is_valid)}")

    print("\n" + "="*100)
    print("CITATION-BY-CITATION ANALYSIS")
    print("="*100)

    # Track metrics
    correct_classifications = 0
    total_score = 0.0

    for i, example in enumerate(test_data, 1):
        print(f"\n{'='*100}")
        print(f"CITATION #{i}")
        print(f"{'='*100}")

        # Show citation
        citation_preview = example.citation[:120] + "..." if len(example.citation) > 120 else example.citation
        print(f"\nCitation: {citation_preview}")

        # Ground truth
        print(f"\n--- GROUND TRUTH ---")
        print(f"Valid: {example.is_valid}")
        if not example.is_valid:
            print(f"Errors ({len(example.errors)}):")
            for err in example.errors:
                print(f"  - {err['component']}: {err['problem']}")

        # Prediction
        print(f"\n--- PREDICTION ---")
        prediction = validator(citation=example.citation)
        print(f"Valid: {prediction.is_valid}")
        print(f"Source Type: {prediction.source_type}")

        if not prediction.is_valid:
            print(f"Errors ({len(prediction.errors)}):")
            for err in prediction.errors:
                print(f"  - {err.get('component', 'Unknown')}: {err.get('problem', 'N/A')}")

        # Analysis
        print(f"\n--- ANALYSIS ---")

        # Classification result
        classification_correct = example.is_valid == prediction.is_valid
        correct_classifications += classification_correct

        if classification_correct:
            print(f"✅ Classification: CORRECT")
        else:
            if example.is_valid and not prediction.is_valid:
                print(f"❌ Classification: FALSE POSITIVE (valid → invalid)")
            else:
                print(f"❌ Classification: FALSE NEGATIVE (invalid → valid)")

        # Error matching (if both agree it's invalid)
        if not example.is_valid and not prediction.is_valid:
            error_metrics = calculate_error_metrics(example.errors, prediction.errors)
            print(f"\nError Detection:")
            print(f"  True Positives: {error_metrics['tp']}")
            print(f"  False Positives: {error_metrics['fp']}")
            print(f"  False Negatives: {error_metrics['fn']}")
            print(f"  Precision: {error_metrics['precision']:.2%}")
            print(f"  Recall: {error_metrics['recall']:.2%}")
            print(f"  F1: {error_metrics['f1']:.2%}")

        # Balanced metric score
        score = citation_validator_metric(example, prediction)
        total_score += score
        print(f"\nBalanced Metric Score: {score:.3f}")

        print(f"\n{'='*100}")

    # Final summary
    print(f"\n{'='*100}")
    print("SUMMARY")
    print(f"{'='*100}")
    print(f"\nTotal Citations: {len(test_data)}")
    print(f"Correct Classifications: {correct_classifications}/{len(test_data)} ({correct_classifications/len(test_data):.2%})")
    print(f"Average Balanced Score: {total_score/len(test_data):.3f} ({total_score/len(test_data)*100:.2f}%)")

    # Breakdown by type
    valid_correct = sum(1 for ex in test_data if ex.is_valid and validator(citation=ex.citation).is_valid)
    valid_total = sum(1 for ex in test_data if ex.is_valid)
    invalid_correct = sum(1 for ex in test_data if not ex.is_valid and not validator(citation=ex.citation).is_valid)
    invalid_total = sum(1 for ex in test_data if not ex.is_valid)

    print(f"\nBreakdown:")
    print(f"  Valid citations correctly identified: {valid_correct}/{valid_total} ({valid_correct/valid_total:.2%})")
    print(f"  Invalid citations correctly identified: {invalid_correct}/{invalid_total} ({invalid_correct/invalid_total:.2%})")

if __name__ == "__main__":
    analyze_citation_by_citation()
