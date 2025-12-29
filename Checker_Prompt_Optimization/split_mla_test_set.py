#!/usr/bin/env python3
"""
Split the comprehensive MLA test set into training and holdout sets.

The comprehensive set has pairs of valid/invalid citations. We split by pairs
to maintain the structure where each valid citation has a matching invalid variant.
This ensures both sets have the same 50/50 valid/invalid ratio.

Output:
- mla9_test_set.jsonl: Training set (half the data)
- mla9_holdout_set.jsonl: Holdout set (other half)
"""

import json
import random
from pathlib import Path

# Set seed for reproducibility
RANDOM_SEED = 42

def main():
    input_file = Path(__file__).parent / "mla9_test_set_COMPREHENSIVE.jsonl"
    train_file = Path(__file__).parent / "mla9_test_set.jsonl"
    holdout_file = Path(__file__).parent / "mla9_holdout_set.jsonl"
    
    # Load all citations
    with open(input_file, 'r') as f:
        citations = [json.loads(line) for line in f if line.strip()]
    
    print(f"Total citations: {len(citations)}")
    
    # Count valid/invalid
    valid_count = sum(1 for c in citations if c['ground_truth'] is True)
    invalid_count = sum(1 for c in citations if c['ground_truth'] is False)
    print(f"Valid: {valid_count}, Invalid: {invalid_count}")
    
    # Group into pairs (valid, invalid) - they're consecutive in the file
    pairs = []
    for i in range(0, len(citations), 2):
        if i + 1 < len(citations):
            valid = citations[i]
            invalid = citations[i + 1]
            
            # Verify the pair structure
            if valid['ground_truth'] is True and invalid['ground_truth'] is False:
                pairs.append((valid, invalid))
            else:
                print(f"Warning: Line {i+1}-{i+2} doesn't follow valid/invalid pattern")
                pairs.append((citations[i], citations[i + 1]))
    
    print(f"Total pairs: {len(pairs)}")
    
    # Shuffle pairs deterministically
    random.seed(RANDOM_SEED)
    shuffled_pairs = pairs.copy()
    random.shuffle(shuffled_pairs)
    
    # Split in half
    split_point = len(shuffled_pairs) // 2
    train_pairs = shuffled_pairs[:split_point]
    holdout_pairs = shuffled_pairs[split_point:]
    
    print(f"Training pairs: {len(train_pairs)}")
    print(f"Holdout pairs: {len(holdout_pairs)}")
    
    # Flatten back to individual citations
    train_citations = []
    for valid, invalid in train_pairs:
        train_citations.append(valid)
        train_citations.append(invalid)
    
    holdout_citations = []
    for valid, invalid in holdout_pairs:
        holdout_citations.append(valid)
        holdout_citations.append(invalid)
    
    # Verify ratios
    train_valid = sum(1 for c in train_citations if c['ground_truth'] is True)
    train_invalid = sum(1 for c in train_citations if c['ground_truth'] is False)
    holdout_valid = sum(1 for c in holdout_citations if c['ground_truth'] is True)
    holdout_invalid = sum(1 for c in holdout_citations if c['ground_truth'] is False)
    
    print(f"\nTraining set: {len(train_citations)} citations")
    print(f"  Valid: {train_valid}, Invalid: {train_invalid}")
    print(f"  Ratio: {train_valid/len(train_citations)*100:.1f}% valid")
    
    print(f"\nHoldout set: {len(holdout_citations)} citations")
    print(f"  Valid: {holdout_valid}, Invalid: {holdout_invalid}")
    print(f"  Ratio: {holdout_valid/len(holdout_citations)*100:.1f}% valid")
    
    # Write output files
    with open(train_file, 'w') as f:
        for citation in train_citations:
            f.write(json.dumps(citation) + '\n')
    
    with open(holdout_file, 'w') as f:
        for citation in holdout_citations:
            f.write(json.dumps(citation) + '\n')
    
    print(f"\nWrote {train_file.name} ({len(train_citations)} citations)")
    print(f"Wrote {holdout_file.name} ({len(holdout_citations)} citations)")

if __name__ == "__main__":
    main()
