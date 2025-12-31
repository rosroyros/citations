#!/usr/bin/env python3
"""
Build the comprehensive Chicago test set by combining valid and invalid citations.
Then split into train and holdout sets.
"""

import json
import random

def main():
    # Read valid citations
    valid_citations = []
    with open('chicago_raw_valid.jsonl', 'r') as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                valid_citations.append({
                    "citation": entry['citation'],
                    "ground_truth": True,
                    "source_type": entry.get('source_type', 'unknown'),
                    "source_url": entry.get('source_url', '')
                })

    # Read invalid variants
    invalid_citations = []
    with open('chicago_invalid_variants.jsonl', 'r') as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                invalid_citations.append({
                    "citation": entry['citation'],
                    "ground_truth": False,
                    "source_type": entry.get('source_type', 'unknown'),
                    "error_type": entry.get('error_type', 'unknown')
                })

    print(f"Valid citations: {len(valid_citations)}")
    print(f"Invalid citations: {len(invalid_citations)}")

    # Combine and shuffle
    all_citations = valid_citations + invalid_citations
    random.seed(42)  # Reproducible shuffle
    random.shuffle(all_citations)

    print(f"Total citations: {len(all_citations)}")

    # Write comprehensive test set
    with open('chicago_test_set_COMPREHENSIVE.jsonl', 'w') as f:
        for entry in all_citations:
            # Simplified format for testing (matches MLA format)
            f.write(json.dumps({
                "citation": entry['citation'],
                "ground_truth": entry['ground_truth']
            }) + '\n')

    print(f"Wrote chicago_test_set_COMPREHENSIVE.jsonl")

    # Split into train (80%) and holdout (20%)
    split_idx = int(len(all_citations) * 0.8)
    train_set = all_citations[:split_idx]
    holdout_set = all_citations[split_idx:]

    # Write train set
    with open('chicago_train_set.jsonl', 'w') as f:
        for entry in train_set:
            f.write(json.dumps({
                "citation": entry['citation'],
                "ground_truth": entry['ground_truth']
            }) + '\n')

    # Write holdout set
    with open('chicago_holdout_set.jsonl', 'w') as f:
        for entry in holdout_set:
            f.write(json.dumps({
                "citation": entry['citation'],
                "ground_truth": entry['ground_truth']
            }) + '\n')

    # Count valid/invalid in each set
    train_valid = sum(1 for e in train_set if e['ground_truth'])
    train_invalid = len(train_set) - train_valid
    holdout_valid = sum(1 for e in holdout_set if e['ground_truth'])
    holdout_invalid = len(holdout_set) - holdout_valid

    print(f"\nTrain set: {len(train_set)} total ({train_valid} valid, {train_invalid} invalid)")
    print(f"Holdout set: {len(holdout_set)} total ({holdout_valid} valid, {holdout_invalid} invalid)")

    # Write detailed version with metadata for debugging
    with open('chicago_test_set_DETAILED.jsonl', 'w') as f:
        for entry in all_citations:
            f.write(json.dumps(entry) + '\n')

    print(f"\nWrote chicago_test_set_DETAILED.jsonl (with metadata)")

if __name__ == '__main__':
    main()
