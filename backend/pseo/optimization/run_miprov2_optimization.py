"""
Run MIPROv2 optimization on citation validator.

MIPROv2 is the state-of-the-art optimizer in DSPy 2.6+, providing:
- Automatic prompt optimization
- Better few-shot example selection
- More sophisticated than BootstrapFewShot
"""
import dspy
from dspy.teleprompt import MIPROv2
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
    print("MIPROv2 OPTIMIZATION FOR CITATION VALIDATOR")
    print("="*70)

    # Setup DSPy
    lm = setup_dspy()

    # Load datasets
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

    # MIPROv2 Optimization
    print("\n" + "-"*70)
    print("RUNNING OPTIMIZATION (MIPROv2)")
    print("-"*70)

    print("\nOptimizing with MIPROv2...")
    print("This will:")
    print("  - Process all training examples")
    print("  - Optimize prompts automatically")
    print("  - Select best few-shot examples")
    print("  - May take 5-15 minutes...")

    # Configure optimizer
    optimizer = MIPROv2(
        metric=citation_validator_metric,
        auto=None,  # Disable auto mode so we can set custom params
        num_candidates=10,  # Number of prompt candidates to try
        init_temperature=1.0,  # Temperature for prompt generation
        verbose=True  # Show progress
    )

    # Run optimization
    try:
        print(f"\n[Info] Training on {len(train_data)} examples")

        optimized_validator = optimizer.compile(
            student=CitationValidator(),
            trainset=train_data,  # Use ALL training examples
            num_trials=50,  # Number of optimization trials
            max_bootstrapped_demos=4,  # Max few-shot examples
            max_labeled_demos=4,  # Max labeled examples
            requires_permission_to_run=False  # Auto-proceed without confirmation
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

        optimized_validator.save(str(output_dir / "miprov2_validator.json"))
        print(f"\n✓ Saved optimized validator to: {output_dir / 'miprov2_validator.json'}")

        # Save metrics
        results = {
            "optimizer": "MIPROv2",
            "training_examples": len(train_data),
            "baseline": baseline_metrics,
            "optimized_val": optimized_metrics,
            "optimized_test": test_metrics,
            "improvement": {
                "f1_delta": f1_improvement,
                "precision_delta": optimized_metrics['error_detection']['precision'] - baseline_metrics['error_detection']['precision'],
                "recall_delta": optimized_metrics['error_detection']['recall'] - baseline_metrics['error_detection']['recall']
            }
        }

        with open(output_dir / "miprov2_results.json", 'w') as f:
            json.dump(results, f, indent=2)

        print(f"✓ Saved results to: {output_dir / 'miprov2_results.json'}")

        # Success criteria
        print("\n" + "="*70)
        print("OPTIMIZATION SUMMARY")
        print("="*70)

        if test_metrics['error_detection']['f1'] >= 0.85:
            print("✅ SUCCESS: F1 >= 0.85 (Strong performance)")
        elif test_metrics['error_detection']['f1'] >= 0.75:
            print("⚠️  GOOD: F1 >= 0.75 (Acceptable, could improve)")
        else:
            print("⚠️  MODERATE: F1 < 0.75 (Consider more data or tuning)")

        if test_metrics['error_detection']['recall'] >= 0.90:
            print("✅ Excellent recall (catching 90%+ of errors)")
        elif test_metrics['error_detection']['recall'] >= 0.80:
            print("⚠️  Good recall (catching 80%+ of errors)")
        else:
            print("⚠️  Moderate recall")

        if test_metrics['error_detection']['precision'] >= 0.80:
            print("✅ Excellent precision (few false alarms)")
        elif test_metrics['error_detection']['precision'] >= 0.70:
            print("⚠️  Good precision (some false alarms)")
        else:
            print("⚠️  Moderate precision")

    except Exception as e:
        print(f"\n❌ Optimization failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
