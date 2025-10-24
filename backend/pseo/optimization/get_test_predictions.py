#!/usr/bin/env python3
"""
Run optimized validator on test set and save detailed predictions.
"""
import dspy
import json
import random
from pathlib import Path
import logging

from dspy_validator import CitationValidator, load_dataset
from dspy_config import setup_dspy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def prepare_test_set():
    """Get test set using same split logic as optimization."""
    # Load data
    valid_file = Path('backend/pseo/optimization/datasets/valid_citations_clean_final.jsonl')
    with open(valid_file) as f:
        valid_citations = [json.loads(line) for line in f]

    invalid_file = Path('backend/pseo/optimization/datasets/invalid_citations_standardized.jsonl')
    with open(invalid_file) as f:
        invalid_citations = [json.loads(line) for line in f]

    # Create examples
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

    # Shuffle with same seed
    random.seed(42)
    random.shuffle(all_examples)

    # Split
    train_size = int(len(all_examples) * 0.7)
    val_size = int(len(all_examples) * 0.15)
    test = all_examples[train_size+val_size:]

    return test


def main():
    logger.info("Setting up DSPy...")
    lm = setup_dspy()

    logger.info("Loading test set...")
    test_set = prepare_test_set()
    logger.info(f"Test set size: {len(test_set)}")

    logger.info("Loading optimized validator...")
    validator_path = Path('backend/pseo/optimization/optimized_prompts/gepa_optimized_validator.json')

    optimized_validator = CitationValidator()
    optimized_validator.load(str(validator_path))

    logger.info("Running predictions on test set...")
    results = []

    for i, example in enumerate(test_set):
        logger.info(f"Processing citation {i+1}/{len(test_set)}")

        try:
            prediction = optimized_validator(citation=example.citation)

            result = {
                'index': i,
                'citation': example.citation,
                'ground_truth': {
                    'is_valid': example.is_valid,
                    'source_type': example.source_type,
                    'errors': example.errors
                },
                'prediction': {
                    'source_type': prediction.source_type,
                    'is_valid': prediction.is_valid,
                    'errors': prediction.errors if hasattr(prediction, 'errors') else []
                }
            }
            results.append(result)

        except Exception as e:
            logger.error(f"Error on citation {i}: {e}")
            results.append({
                'index': i,
                'citation': example.citation,
                'ground_truth': {
                    'is_valid': example.is_valid,
                    'source_type': example.source_type,
                    'errors': example.errors
                },
                'prediction': {
                    'error': str(e)
                }
            })

    # Save results
    output_path = Path('backend/pseo/optimization/test_predictions.json')
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"✓ Saved {len(results)} predictions to: {output_path}")

    # Summary
    correct = sum(1 for r in results if r.get('prediction', {}).get('is_valid') == r['ground_truth']['is_valid'])
    logger.info(f"\nAccuracy: {correct}/{len(results)} = {correct/len(results)*100:.1f}%")


if __name__ == '__main__':
    main()
