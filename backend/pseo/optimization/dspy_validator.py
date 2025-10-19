"""
DSPy Citation Validator Module with GEPA Optimization.

This module validates APA 7 citations and identifies errors with specific corrections.
"""
import dspy
import json
from typing import List, Dict
from pathlib import Path


class CitationValidation(dspy.Signature):
    """
    Validate APA 7th edition citation and identify errors.

    The validator must:
    1. Detect the citation source type (journal article, book, webpage, etc.)
    2. Validate against APA 7 rules
    3. List specific errors with components and corrections
    """

    citation = dspy.InputField(desc="Citation text to validate")

    # Output fields
    source_type = dspy.OutputField(desc="Detected source type: journal article, book, book chapter, webpage, or other")
    is_valid = dspy.OutputField(desc="Boolean: true if no errors, false if errors found")
    errors = dspy.OutputField(desc="""JSON list of errors. Each error MUST use one of these exact component names (lowercase):
    - 'authors' for author name and formatting errors
    - 'title' for article/book/chapter title errors
    - 'journal' for journal or periodical name errors
    - 'doi' for DOI or URL errors
    - 'publisher' for publisher name and location errors
    - 'date' for publication date errors
    - 'volume' for volume number errors
    - 'issue' for issue number errors
    - 'pages' for page number errors
    - 'format' for spacing, punctuation, or capitalization errors

    Format: [{"component": "<exact name from list>", "problem": "<description>", "correction": "<fix>"}]
    Use empty list [] if citation is valid.""")


class CitationValidator(dspy.Module):
    """DSPy module for citation validation."""

    def __init__(self):
        super().__init__()
        self.validate = dspy.ChainOfThought(CitationValidation)

    def forward(self, citation: str):
        """Validate a citation and return structured results."""
        result = self.validate(citation=citation)

        # Parse outputs
        try:
            # Ensure is_valid is boolean
            is_valid_str = str(result.is_valid).lower()
            is_valid = is_valid_str in ['true', '1', 'yes']

            # Parse errors (handle both string and list formats)
            if isinstance(result.errors, str):
                if result.errors.strip() in ['[]', '', 'none', '{}']:
                    errors = []
                else:
                    try:
                        errors = json.loads(result.errors)
                    except:
                        # If parsing fails, create single error from string
                        errors = [{"component": "Unknown", "problem": result.errors, "correction": "See APA 7 guidelines"}]
            else:
                errors = result.errors if result.errors else []

            return dspy.Prediction(
                source_type=result.source_type,
                is_valid=is_valid,
                errors=errors
            )
        except Exception as e:
            # Fallback if parsing fails
            return dspy.Prediction(
                source_type="unknown",
                is_valid=False,
                errors=[{"component": "System", "problem": f"Parsing error: {str(e)}", "correction": "Manual review needed"}]
            )


def load_dataset(filepath: str) -> List[dspy.Example]:
    """Load dataset from JSONL file into DSPy examples."""
    examples = []

    with open(filepath, 'r') as f:
        for line in f:
            data = json.loads(line.strip())

            # Create DSPy example
            # Input: citation text only (NO source_type!)
            # Output: is_valid, errors, source_type (for evaluation)
            example = dspy.Example(
                citation=data['citation'],
                is_valid=data['is_valid'],
                errors=data['errors'],
                source_type=data.get('_reference_source_type', 'unknown')
            ).with_inputs('citation')  # Only citation is input

            examples.append(example)

    return examples


def calculate_error_metrics(true_errors: List[Dict], pred_errors: List[Dict]) -> Dict:
    """
    Calculate precision, recall, F1 for error detection.

    Matches errors by component (Authors, Title, DOI, etc.).
    """
    # Normalize error components for comparison
    def normalize_component(comp):
        return comp.lower().strip()

    true_components = set(normalize_component(e['component']) for e in true_errors)
    pred_components = set(normalize_component(e['component']) for e in pred_errors)

    # Calculate matches
    tp = len(true_components & pred_components)  # Correctly identified errors
    fp = len(pred_components - true_components)  # False alarms
    fn = len(true_components - pred_components)  # Missed errors

    # Metrics
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }


def citation_validator_metric(example, prediction, trace=None):
    """
    Balanced evaluation metric optimizing for both valid and invalid performance.

    Scoring breakdown:
    - 50% weight: Citation-level correctness (valid vs invalid classification)
    - 50% weight: Error-level accuracy (specific error component matching)

    This ensures the model can't game the metric by over-flagging or under-flagging.
    Higher is better (0.0 to 1.0).
    """
    true_is_valid = example.is_valid
    pred_is_valid = prediction.is_valid

    true_errors = example.errors if example.errors else []
    pred_errors = prediction.errors if prediction.errors else []

    # Citation-level correctness (50% weight)
    citation_correct = 1.0 if true_is_valid == pred_is_valid else 0.0

    # Error-level accuracy (50% weight)
    if not true_is_valid and not pred_is_valid:
        # Both agree it's invalid - score on error component matching
        error_metrics = calculate_error_metrics(true_errors, pred_errors)
        error_score = error_metrics['f1']
    elif true_is_valid and pred_is_valid:
        # Both agree it's valid - perfect error score
        error_score = 1.0
    else:
        # Disagreement on validity - error score is 0
        error_score = 0.0

    # Balanced score: 50/50 weighting
    final_score = 0.5 * citation_correct + 0.5 * error_score

    return final_score


def evaluate_validator(validator, dataset):
    """
    Comprehensive evaluation of validator on dataset.

    Returns detailed metrics including per-component accuracy.
    """
    total_examples = len(dataset)

    # Track metrics
    citation_level_correct = 0
    error_metrics_sum = {"tp": 0, "fp": 0, "fn": 0}

    all_predictions = []

    for example in dataset:
        prediction = validator(citation=example.citation)
        all_predictions.append(prediction)

        # Citation-level accuracy
        if example.is_valid == prediction.is_valid:
            citation_level_correct += 1

        # Error-level metrics
        if not example.is_valid:
            metrics = calculate_error_metrics(
                example.errors if example.errors else [],
                prediction.errors if prediction.errors else []
            )
            error_metrics_sum["tp"] += metrics["tp"]
            error_metrics_sum["fp"] += metrics["fp"]
            error_metrics_sum["fn"] += metrics["fn"]

    # Overall error detection metrics
    tp = error_metrics_sum["tp"]
    fp = error_metrics_sum["fp"]
    fn = error_metrics_sum["fn"]

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "total_examples": total_examples,
        "citation_level_accuracy": citation_level_correct / total_examples,
        "error_detection": {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "true_positives": tp,
            "false_positives": fp,
            "false_negatives": fn
        }
    }


if __name__ == "__main__":
    from dspy_config import setup_dspy

    # Setup DSPy
    lm = setup_dspy()

    # Load datasets
    train_data = load_dataset("backend/pseo/optimization/datasets/train.jsonl")
    val_data = load_dataset("backend/pseo/optimization/datasets/val.jsonl")
    test_data = load_dataset("backend/pseo/optimization/datasets/test.jsonl")

    print(f"Loaded datasets:")
    print(f"  Train: {len(train_data)} examples")
    print(f"  Val: {len(val_data)} examples")
    print(f"  Test: {len(test_data)} examples")

    # Test validator on a few examples
    print("\n" + "="*70)
    print("TESTING UNOPTIMIZED VALIDATOR")
    print("="*70)

    validator = CitationValidator()

    # Test on first validation example
    test_example = val_data[0]
    print(f"\nTest Citation: {test_example.citation[:100]}...")
    print(f"True Valid: {test_example.is_valid}")
    print(f"True Errors: {test_example.errors if test_example.errors else 'None'}")

    prediction = validator(citation=test_example.citation)
    print(f"\nPredicted Valid: {prediction.is_valid}")
    print(f"Predicted Errors: {prediction.errors}")
    print(f"Detected Type: {prediction.source_type}")

    # Evaluate on validation set
    print("\n" + "="*70)
    print("BASELINE EVALUATION (Validation Set)")
    print("="*70)

    val_metrics = evaluate_validator(validator, val_data[:5])  # Test on first 5
    print(json.dumps(val_metrics, indent=2))
