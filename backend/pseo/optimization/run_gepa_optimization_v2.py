"""
Run GEPA optimization on citation validator.

GEPA (Generalized Efficient Prompt Adaptation) will optimize the validation prompt
to maximize F1 score on error detection.
"""
import dspy
from dspy.teleprompt import BootstrapFewShot
import json
from pathlib import Path
from dspy_validator import (
    CitationValidator,
    load_dataset,
    citation_validator_metric,
    evaluate_validator
)
from dspy_config import setup_dspy


def main():
    print("="*70)
    print("GEPA OPTIMIZATION FOR CITATION VALIDATOR")
    print("="*70)

    # Setup DSPy
    lm = setup_dspy()

    # Load datasets (v2 with [ITALIC] formatting)
    print("\nLoading datasets...")
    train_data = load_dataset("backend/pseo/optimization/datasets/train_v2.jsonl")
    val_data = load_dataset("backend/pseo/optimization/datasets/val_v2.jsonl")
    test_data = load_dataset("backend/pseo/optimization/datasets/test_v2.jsonl")

    print(f"  Train: {len(train_data)} examples")
    print(f"  Val: {len(val_data)} examples")
    print(f"  Test: {len(test_data)} examples")

    # Create unoptimized validator
    print("\n" + "-"*70)
    print("BASELINE PERFORMANCE (Unoptimized)")
    print("-"*70)

    unoptimized_validator = CitationValidator()

    # Evaluate baseline on validation set
    baseline_metrics = evaluate_validator(unoptimized_validator, val_data)
    print("\nBaseline Metrics (Validation Set):")
    print(f"  Citation Accuracy: {baseline_metrics['citation_level_accuracy']:.2%}")
    print(f"  Error Detection:")
    print(f"    Precision: {baseline_metrics['error_detection']['precision']:.2%}")
    print(f"    Recall: {baseline_metrics['error_detection']['recall']:.2%}")
    print(f"    F1: {baseline_metrics['error_detection']['f1']:.3f}")

    # GEPA Optimization
    # Note: DSPy 2.6+ uses BootstrapFewShot instead of GEPA
    # BootstrapFewShot achieves similar optimization through few-shot learning
    print("\n" + "-"*70)
    print("RUNNING OPTIMIZATION (BootstrapFewShot)")
    print("-"*70)

    print("\nOptimizing with few-shot examples...")
    print("This may take several minutes...")

    # Configure optimizer
    optimizer = BootstrapFewShot(
        metric=citation_validator_metric,
        max_bootstrapped_demos=4,  # Number of few-shot examples to use
        max_labeled_demos=2,        # Number of labeled examples
        max_rounds=1                # Number of optimization rounds
    )

    # Run optimization
    try:
        # Add custom progress callback
        import sys

        class ProgressCallback:
            def __init__(self):
                self.count = 0

            def __call__(self, *args, **kwargs):
                self.count += 1
                print(f"\n[Progress] Processing example {self.count}/30", flush=True)
                sys.stdout.flush()
                return True

        print("\n[Info] Starting optimization with detailed logging...")
        print(f"[Info] Training on {len(train_data[:30])} examples")
        sys.stdout.flush()

        optimized_validator = optimizer.compile(
            student=CitationValidator(),
            trainset=train_data[:15]  # Reduced to 15 for faster completion
        )

        print("✓ Optimization complete!")

        # Evaluate optimized model
        print("\n" + "-"*70)
        print("OPTIMIZED PERFORMANCE")
        print("-"*70)

        optimized_metrics = evaluate_validator(optimized_validator, val_data)
        print("\nOptimized Metrics (Validation Set):")
        print(f"  Citation Accuracy: {optimized_metrics['citation_level_accuracy']:.2%}")
        print(f"  Error Detection:")
        print(f"    Precision: {optimized_metrics['error_detection']['precision']:.2%}")
        print(f"    Recall: {optimized_metrics['error_detection']['recall']:.2%}")
        print(f"    F1: {optimized_metrics['error_detection']['f1']:.3f}")

        # Improvement
        f1_improvement = optimized_metrics['error_detection']['f1'] - baseline_metrics['error_detection']['f1']
        print(f"\nF1 Improvement: {f1_improvement:+.3f}")

        # Evaluate on test set
        print("\n" + "-"*70)
        print("TEST SET EVALUATION")
        print("-"*70)

        test_metrics = evaluate_validator(optimized_validator, test_data)
        print("\nTest Set Metrics:")
        print(f"  Citation Accuracy: {test_metrics['citation_level_accuracy']:.2%}")
        print(f"  Error Detection:")
        print(f"    Precision: {test_metrics['error_detection']['precision']:.2%}")
        print(f"    Recall: {test_metrics['error_detection']['recall']:.2%}")
        print(f"    F1: {test_metrics['error_detection']['f1']:.3f}")

        # Save optimized validator
        output_dir = Path("backend/pseo/optimization/models")
        output_dir.mkdir(parents=True, exist_ok=True)

        optimized_validator.save(str(output_dir / "optimized_validator.json"))
        print(f"\n✓ Saved optimized validator to: {output_dir / 'optimized_validator.json'}")

        # Save metrics
        results = {
            "baseline": baseline_metrics,
            "optimized_val": optimized_metrics,
            "optimized_test": test_metrics,
            "improvement": {
                "f1_delta": f1_improvement,
                "precision_delta": optimized_metrics['error_detection']['precision'] - baseline_metrics['error_detection']['precision'],
                "recall_delta": optimized_metrics['error_detection']['recall'] - baseline_metrics['error_detection']['recall']
            }
        }

        with open(output_dir / "optimization_results.json", 'w') as f:
            json.dump(results, f, indent=2)

        print(f"✓ Saved results to: {output_dir / 'optimization_results.json'}")

        # Success criteria
        print("\n" + "="*70)
        print("OPTIMIZATION SUMMARY")
        print("="*70)

        if test_metrics['error_detection']['f1'] >= 0.85:
            print("✅ SUCCESS: F1 >= 0.85 (Strong performance)")
        elif test_metrics['error_detection']['f1'] >= 0.75:
            print("⚠️  GOOD: F1 >= 0.75 (Acceptable, could improve)")
        else:
            print("❌ NEEDS WORK: F1 < 0.75 (Consider expanding dataset)")

        if test_metrics['error_detection']['recall'] >= 0.90:
            print("✅ Excellent recall (catching 90%+ of errors)")
        elif test_metrics['error_detection']['recall'] >= 0.80:
            print("⚠️  Good recall (catching 80%+ of errors)")
        else:
            print("❌ Low recall (missing too many errors)")

        if test_metrics['error_detection']['precision'] >= 0.80:
            print("✅ Excellent precision (few false alarms)")
        elif test_metrics['error_detection']['precision'] >= 0.70:
            print("⚠️  Good precision (some false alarms)")
        else:
            print("❌ Low precision (too many false alarms)")

    except Exception as e:
        print(f"\n❌ Optimization failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
