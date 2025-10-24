#!/usr/bin/env python3
"""
GEPA optimization for APA 7 citation validator.

Uses GEPA (Reflective Prompt Evolution) optimizer with feedback-driven evolution.
"""
import dspy
from dspy.teleprompt import GEPA
import json
from pathlib import Path
import logging

from dspy_validator import (
    CitationValidator,
    load_dataset,
    citation_validator_metric,
    evaluate_validator
)
from dspy_config import setup_dspy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def prepare_gepa_dataset(use_books_journals_only=False, use_journals_only=False):
    """
    Prepare dataset for GEPA optimization.

    Use cleaned deduplicated valid citations + standardized invalid citations
    Split: 60% train, 25% val, 15% test (with shuffling for balanced splits)

    Args:
        use_books_journals_only: If True, only use book and journal citations
        use_journals_only: If True, only use journal article citations
    """
    import random

    logger.info("Preparing dataset for GEPA...")

    # Choose dataset files based on filter
    if use_journals_only:
        logger.info("Using JOURNALS ONLY dataset")
        valid_file = Path('backend/pseo/optimization/datasets/valid_citations_journals_only.jsonl')
        invalid_file = Path('backend/pseo/optimization/datasets/invalid_citations_journals_only.jsonl')
    elif use_books_journals_only:
        logger.info("Using BOOKS AND JOURNALS ONLY dataset")
        valid_file = Path('backend/pseo/optimization/datasets/valid_citations_books_journals.jsonl')
        invalid_file = Path('backend/pseo/optimization/datasets/invalid_citations_books_journals.jsonl')
    else:
        logger.info("Using FULL dataset (all source types)")
        valid_file = Path('backend/pseo/optimization/datasets/valid_citations_clean_final.jsonl')
        invalid_file = Path('backend/pseo/optimization/datasets/invalid_citations_standardized.jsonl')

    # Load CLEAN deduplicated valid citations
    with open(valid_file) as f:
        valid_citations = [json.loads(line) for line in f]

    logger.info(f"Loaded {len(valid_citations)} CLEAN deduplicated valid citations")

    # Load STANDARDIZED invalid citations
    if invalid_file.exists():
        with open(invalid_file) as f:
            invalid_citations = [json.loads(line) for line in f]
        logger.info(f"Loaded {len(invalid_citations)} standardized invalid citations")
    else:
        logger.warning("No standardized invalid citations found - will only use valid citations")
        invalid_citations = []

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

    logger.info(f"Total examples: {len(all_examples)}")

    # Shuffle to mix valid and invalid citations
    random.seed(42)  # Reproducible splits
    random.shuffle(all_examples)
    logger.info("Shuffled examples for balanced splits")

    # Split 60/25/15 (increased val for more reliable optimization)
    train_size = int(len(all_examples) * 0.6)
    val_size = int(len(all_examples) * 0.25)

    train = all_examples[:train_size]
    val = all_examples[train_size:train_size+val_size]
    test = all_examples[train_size+val_size:]

    # Log composition of each split
    train_valid = sum(1 for ex in train if ex.is_valid)
    val_valid = sum(1 for ex in val if ex.is_valid)
    test_valid = sum(1 for ex in test if ex.is_valid)

    logger.info(f"Split - Train: {len(train)} ({train_valid} valid, {len(train)-train_valid} invalid)")
    logger.info(f"Split - Val: {len(val)} ({val_valid} valid, {len(val)-val_valid} invalid)")
    logger.info(f"Split - Test: {len(test)} ({test_valid} valid, {len(test)-test_valid} invalid)")

    return train, val, test


def main():
    import sys

    # Check for command-line arguments to filter dataset
    use_journals_only = '--journals-only' in sys.argv
    use_books_journals_only = '--books-journals-only' in sys.argv

    print("="*80)
    print("GEPA OPTIMIZATION FOR APA 7 CITATION VALIDATOR")
    if use_journals_only:
        print("DATASET: JOURNALS ONLY")
    elif use_books_journals_only:
        print("DATASET: BOOKS AND JOURNALS ONLY")
    else:
        print("DATASET: ALL SOURCE TYPES")
    print("="*80)
    print()
    print("GEPA uses reflective feedback to evolve prompts iteratively")
    print("to maximize balanced 50/50 metric (citation accuracy + error F1).")
    print("="*80)

    # Setup DSPy with GPT-4o-mini (cost-effective)
    logger.info("Setting up DSPy...")
    lm = setup_dspy()

    # Prepare dataset
    train_data, val_data, test_data = prepare_gepa_dataset(
        use_books_journals_only=use_books_journals_only,
        use_journals_only=use_journals_only
    )

    if len(train_data) < 10:
        logger.error(f"Insufficient training data ({len(train_data)} examples)")
        logger.error("Need at least 10 examples. Run error injection first.")
        return

    # Create baseline validator
    logger.info("\n" + "="*80)
    logger.info("BASELINE EVALUATION")
    logger.info("="*80)

    baseline_validator = CitationValidator()

    # Evaluate baseline
    baseline_metrics = evaluate_validator(baseline_validator, val_data)
    logger.info(f"\nBaseline Metrics:")
    logger.info(f"  Citation Accuracy: {baseline_metrics.get('citation_level_accuracy', 0):.2%}")
    logger.info(f"  Error Detection F1: {baseline_metrics.get('error_detection', {}).get('f1', 0):.2%}")

    # Configure GEPA optimizer
    logger.info("\n" + "="*80)
    logger.info("CONFIGURING GEPA OPTIMIZER")
    logger.info("="*80)

    # Create strong reflection LM (GEPA benefits from strong reflection model)
    reflection_lm = dspy.LM(model='gpt-4o', temperature=1.0, max_tokens=8000)

    gepa_optimizer = GEPA(
        metric=citation_validator_metric,
        auto="medium",  # light/medium/heavy budget
        reflection_lm=reflection_lm,  # Strong model for reflection
        reflection_minibatch_size=3,  # Examples per reflection step
        candidate_selection_strategy="pareto",  # Stochastic Pareto frontier selection
        skip_perfect_score=True,  # Skip examples with perfect scores
        use_merge=True,  # Enable merge-based optimization
        max_merge_invocations=5,  # Max merge attempts
        failure_score=0.0,
        perfect_score=1.0,
        track_stats=True,  # Track detailed results
        seed=42,  # Reproducibility
    )

    logger.info("GEPA Config:")
    logger.info(f"  Auto mode: medium")
    logger.info(f"  Reflection LM: gpt-4o (temperature=1.0)")
    logger.info(f"  Minibatch size: 3")
    logger.info(f"  Strategy: Pareto frontier")
    logger.info(f"  Metric: Balanced 50/50 (citation accuracy + error F1)")

    # Run GEPA optimization
    logger.info("\n" + "="*80)
    logger.info("RUNNING GEPA OPTIMIZATION")
    logger.info("="*80)
    logger.info("This will take several minutes (GEPA uses reflection)...")

    try:
        optimized_validator = gepa_optimizer.compile(
            student=baseline_validator,
            trainset=train_data,
            valset=val_data,
        )

        logger.info("\n✓ Optimization complete!")

    except Exception as e:
        logger.error(f"\n✗ Optimization failed: {e}")
        logger.exception(e)
        return

    # Evaluate optimized validator
    logger.info("\n" + "="*80)
    logger.info("FINAL EVALUATION (Test Set)")
    logger.info("="*80)

    optimized_metrics = evaluate_validator(optimized_validator, test_data)

    logger.info(f"\nOptimized Metrics:")
    logger.info(f"  Citation Accuracy: {optimized_metrics.get('citation_level_accuracy', 0):.2%}")
    logger.info(f"  Error Detection:")
    logger.info(f"    Precision: {optimized_metrics.get('error_detection', {}).get('precision', 0):.2%}")
    logger.info(f"    Recall: {optimized_metrics.get('error_detection', {}).get('recall', 0):.2%}")
    logger.info(f"    F1: {optimized_metrics.get('error_detection', {}).get('f1', 0):.2%}")

    # Compare
    logger.info("\n" + "="*80)
    logger.info("IMPROVEMENT SUMMARY")
    logger.info("="*80)

    baseline_f1 = baseline_metrics.get('error_detection', {}).get('f1', 0)
    optimized_f1 = optimized_metrics.get('error_detection', {}).get('f1', 0)
    improvement = optimized_f1 - baseline_f1

    logger.info(f"Baseline F1:   {baseline_f1:.2%}")
    logger.info(f"Optimized F1:  {optimized_f1:.2%}")
    logger.info(f"Improvement:   {improvement:+.2%}")

    # Save optimized prompt
    logger.info("\n" + "="*80)
    logger.info("SAVING OPTIMIZED VALIDATOR")
    logger.info("="*80)

    output_dir = Path('backend/pseo/optimization/optimized_prompts')
    output_dir.mkdir(exist_ok=True, parents=True)

    # Save DSPy module
    optimized_validator.save(str(output_dir / 'gepa_optimized_validator.json'))
    logger.info(f"✓ Saved to: {output_dir / 'gepa_optimized_validator.json'}")

    # Extract and save prompt text
    try:
        prompt_text = optimized_validator.forward.extended_signature.instructions
        with open(output_dir / 'gepa_optimized_prompt.txt', 'w') as f:
            f.write(prompt_text)
        logger.info(f"✓ Saved prompt to: {output_dir / 'gepa_optimized_prompt.txt'}")
    except Exception as e:
        logger.warning(f"Could not extract prompt text: {e}")

    logger.info("\n" + "="*80)
    logger.info("OPTIMIZATION COMPLETE")
    logger.info("="*80)


if __name__ == '__main__':
    main()
