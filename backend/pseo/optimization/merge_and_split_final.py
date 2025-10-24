#!/usr/bin/env python3
"""
Merge all cleaned datasets and create final train/val/test splits.
"""

import json
from pathlib import Path
from sklearn.model_selection import train_test_split
import random

DATASETS_DIR = Path(__file__).parent / "datasets"

def load_citations(file_path: Path, key_name='citation_text') -> list:
    """Load citations from JSONL file."""
    citations = []
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return citations

    with open(file_path) as f:
        for line in f:
            data = json.loads(line)

            # Standardize format
            citation_text = data.get(key_name, data.get('citation', ''))

            example = {
                'citation': citation_text,
                'source_type': data.get('source_type', data.get('_reference_source_type', 'other')),
                'is_valid': data.get('is_valid', True),
                'errors': data.get('errors', [])
            }
            citations.append(example)

    return citations

def main():
    print("="*80)
    print("MERGING ALL DATASETS")
    print("="*80)

    all_examples = []

    # 1. Load valid citations (with formatting)
    print("\n1. Loading valid citations with [ITALIC] formatting...")
    valid_citations = load_citations(DATASETS_DIR / "valid_citations_with_formatting.jsonl")
    print(f"   ✓ Loaded {len(valid_citations)} valid citations")
    all_examples.extend(valid_citations)

    # 2. Load invalid citations
    print("\n2. Loading invalid citations...")
    invalid_citations = load_citations(DATASETS_DIR / "invalid_citations_enhanced.jsonl")
    print(f"   ✓ Loaded {len(invalid_citations)} invalid citations")
    all_examples.extend(invalid_citations)

    # 3. Load social media citations
    print("\n3. Loading social media citations...")
    social_citations = load_citations(DATASETS_DIR / "social_media_italic.jsonl")
    print(f"   ✓ Loaded {len(social_citations)} social media citations")
    all_examples.extend(social_citations)

    # Summary
    print("\n" + "="*80)
    print("DATASET SUMMARY")
    print("="*80)
    print(f"Total examples: {len(all_examples)}")
    print(f"  Valid: {sum(1 for ex in all_examples if ex['is_valid'])}")
    print(f"  Invalid: {sum(1 for ex in all_examples if not ex['is_valid'])}")

    # Check [ITALIC] marker coverage
    with_italic = sum(1 for ex in all_examples if '[ITALIC]' in ex['citation'])
    print(f"\nWith [ITALIC] markers: {with_italic}/{len(all_examples)} ({with_italic/len(all_examples)*100:.1f}%)")

    # Split into train/val/test (70/15/15)
    print("\n" + "="*80)
    print("CREATING SPLITS")
    print("="*80)

    # Set random seed for reproducibility
    random.seed(42)

    # Stratify by is_valid to ensure balanced splits
    valid_examples = [ex for ex in all_examples if ex['is_valid']]
    invalid_examples = [ex for ex in all_examples if not ex['is_valid']]

    print(f"\nSplitting {len(valid_examples)} valid citations...")
    valid_train_val, valid_test = train_test_split(valid_examples, test_size=0.15, random_state=42)
    valid_train, valid_val = train_test_split(valid_train_val, test_size=0.176, random_state=42)  # 0.176 * 0.85 ≈ 0.15

    print(f"Splitting {len(invalid_examples)} invalid citations...")
    invalid_train_val, invalid_test = train_test_split(invalid_examples, test_size=0.15, random_state=42)
    invalid_train, invalid_val = train_test_split(invalid_train_val, test_size=0.176, random_state=42)

    # Combine
    train = valid_train + invalid_train
    val = valid_val + invalid_val
    test = valid_test + invalid_test

    # Shuffle
    random.shuffle(train)
    random.shuffle(val)
    random.shuffle(test)

    print(f"\n✓ Train: {len(train)} ({sum(1 for ex in train if ex['is_valid'])} valid, {sum(1 for ex in train if not ex['is_valid'])} invalid)")
    print(f"✓ Val:   {len(val)} ({sum(1 for ex in val if ex['is_valid'])} valid, {sum(1 for ex in val if not ex['is_valid'])} invalid)")
    print(f"✓ Test:  {len(test)} ({sum(1 for ex in test if ex['is_valid'])} valid, {sum(1 for ex in test if not ex['is_valid'])} invalid)")

    # Save splits
    print("\n" + "="*80)
    print("SAVING SPLITS")
    print("="*80)

    train_file = DATASETS_DIR / "train_v2.jsonl"
    val_file = DATASETS_DIR / "val_v2.jsonl"
    test_file = DATASETS_DIR / "test_v2.jsonl"

    with open(train_file, 'w') as f:
        for ex in train:
            f.write(json.dumps(ex) + '\n')
    print(f"✓ Saved {train_file}")

    with open(val_file, 'w') as f:
        for ex in val:
            f.write(json.dumps(ex) + '\n')
    print(f"✓ Saved {val_file}")

    with open(test_file, 'w') as f:
        for ex in test:
            f.write(json.dumps(ex) + '\n')
    print(f"✓ Saved {test_file}")

    # Verify [ITALIC] coverage in each split
    print("\n" + "="*80)
    print("[ITALIC] MARKER COVERAGE")
    print("="*80)

    for name, split in [("Train", train), ("Val", val), ("Test", test)]:
        with_italic = sum(1 for ex in split if '[ITALIC]' in ex['citation'])
        print(f"{name}: {with_italic}/{len(split)} ({with_italic/len(split)*100:.1f}%)")

    print("\n" + "="*80)
    print("✅ MERGE AND SPLIT COMPLETE")
    print("="*80)
    print("\nReady for GEPA optimization!")
    print("Next: python3 run_gepa_optimization_v2.py")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
