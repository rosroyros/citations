#!/usr/bin/env python3
"""Show false positive examples from test set (precision errors)."""

import json
import logging
from pathlib import Path
from dspy_validator import CitationValidator
import dspy

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def load_test_data():
    """Load test dataset."""
    test_file = Path(__file__).parent / "datasets" / "test.jsonl"
    examples = []
    with open(test_file) as f:
        for line in f:
            examples.append(json.loads(line))
    return examples

def main():
    # Initialize LLM
    import os
    from dotenv import load_dotenv
    load_dotenv()

    lm = dspy.LM(
        model="openai/gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.0,
        max_tokens=2000
    )
    dspy.configure(lm=lm)

    # Load validator
    validator = CitationValidator()
    validator.load("backend/pseo/optimization/models/optimized_validator.json")

    # Load test data
    test_data = load_test_data()

    # Find false positives (valid citations flagged as invalid)
    false_positives = []

    print("=" * 80)
    print("FALSE POSITIVES (Precision Errors)")
    print("=" * 80)
    print("\nThese are VALID citations that were incorrectly flagged as INVALID:\n")

    for i, example in enumerate(test_data, 1):
        citation = example['citation']
        is_valid = example['is_valid']

        # Only check actually valid citations
        if not is_valid:
            continue

        # Get prediction
        result = validator(citation=citation)
        predicted_valid = result.is_valid
        predicted_errors = result.errors

        # False positive: valid citation flagged as invalid
        if not predicted_valid:
            false_positives.append({
                'citation': citation,
                'predicted_errors': predicted_errors
            })

            print(f"Example {len(false_positives)}:")
            print(f"Citation: {citation}")
            print(f"\nIncorrectly flagged errors:")
            for error in predicted_errors:
                print(f"  - {error.get('component', 'Unknown')}: {error.get('problem', 'No problem specified')}")
                if 'correction' in error:
                    print(f"    → Suggested: {error['correction']}")
            print("\n" + "-" * 80 + "\n")

    print(f"\n{'=' * 80}")
    print(f"SUMMARY: Found {len(false_positives)} false positives out of {sum(1 for ex in test_data if ex['is_valid'])} valid citations")
    print(f"Precision Error Rate: {len(false_positives) / sum(1 for ex in test_data if ex['is_valid']) * 100:.1f}%")
    print(f"{'=' * 80}\n")

if __name__ == "__main__":
    main()
