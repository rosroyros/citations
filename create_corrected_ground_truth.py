#!/usr/bin/env python3
"""
Create corrected ground truth test set by applying manual corrections.
Issue: citations-154
"""

import json
import random
from pathlib import Path

def load_corrections():
    """Load manual corrections from audit."""
    corrections_file = Path('Checker_Prompt_Optimization/ALL_GROUND_TRUTH_CORRECTIONS.json')
    with open(corrections_file, 'r') as f:
        data = json.load(f)

    corrections = data['ground_truth_corrections']
    print(f'✓ Loaded {len(corrections)} corrections')

    # Map citation text to correct label
    correction_map = {}
    for corr in corrections:
        citation = corr['citation']
        correct_label = corr['corrected_ground_truth']  # Use 'corrected_ground_truth' key
        correction_map[citation] = correct_label

    return corrections, correction_map

def apply_corrections(full_data, correction_map, corrections):
    """Apply corrections to full dataset."""
    corrected_count = 0

    for item in full_data:
        citation = item['citation']
        if citation in correction_map:
            old_label = item['is_valid']
            new_label = (correction_map[citation] == 'VALID')
            if old_label != new_label:
                # Ensure metadata exists
                if 'metadata' not in item:
                    item['metadata'] = {}

                item['is_valid'] = new_label
                item['metadata']['ground_truth_corrected'] = True
                item['metadata']['original_label'] = 'VALID' if old_label else 'INVALID'
                item['metadata']['correction_reason'] = next(
                    c['reason'] for c in corrections if c['citation'] == citation
                )
                corrected_count += 1

    print(f'✓ Corrected {corrected_count} labels in full dataset')
    return corrected_count

def create_validation_set(full_data):
    """Create validation set using seed=42 for reproducibility."""
    random.seed(42)

    valid_examples = [d for d in full_data if d['is_valid']]
    invalid_examples = [d for d in full_data if not d['is_valid']]

    random.shuffle(valid_examples)
    random.shuffle(invalid_examples)

    # 80/20 split
    valid_split = int(len(valid_examples) * 0.8)
    invalid_split = int(len(invalid_examples) * 0.8)

    val_set = valid_examples[valid_split:] + invalid_examples[invalid_split:]

    print(f'✓ Created validation set with {len(val_set)} citations')
    print(f'  - Valid: {sum(1 for item in val_set if item["is_valid"])}')
    print(f'  - Invalid: {sum(1 for item in val_set if not item["is_valid"])}')

    return val_set

def create_summary(full_data, val_set, corrected_count, corrections):
    """Create summary report of corrections."""
    summary = {
        'total_citations': len(full_data),
        'validation_set_size': len(val_set),
        'corrections_applied': corrected_count,
        'corrections_by_type': {
            'VALID_to_INVALID': sum(1 for c in corrections if c['corrected_ground_truth'] == 'INVALID'),
            'INVALID_to_VALID': sum(1 for c in corrections if c['corrected_ground_truth'] == 'VALID')
        },
        'corrected_validation_distribution': {
            'valid': sum(1 for item in val_set if item['is_valid']),
            'invalid': sum(1 for item in val_set if not item['is_valid'])
        },
        'corrections_in_validation_set': sum(
            1 for item in val_set
            if item.get('metadata', {}).get('ground_truth_corrected')
        )
    }

    return summary

def main():
    print('Creating corrected ground truth test set...\n')

    # Step 1: Load corrections
    print('[1/4] Loading corrections...')
    corrections, correction_map = load_corrections()

    # Step 2: Load and correct full dataset
    print('\n[2/4] Applying corrections to full dataset...')
    full_data_file = Path('Checker_Prompt_Optimization/final_merged_dataset_v2.jsonl')
    with open(full_data_file, 'r') as f:
        full_data = [json.loads(line) for line in f]

    print(f'✓ Loaded {len(full_data)} citations from full dataset')
    corrected_count = apply_corrections(full_data, correction_map, corrections)

    # Save corrected full dataset
    output_file = Path('Checker_Prompt_Optimization/final_merged_dataset_v2_CORRECTED.jsonl')
    with open(output_file, 'w') as f:
        for item in full_data:
            f.write(json.dumps(item) + '\n')
    print(f'✓ Saved corrected dataset to {output_file}')

    # Step 3: Create corrected validation set
    print('\n[3/4] Creating corrected validation set...')
    val_set = create_validation_set(full_data)

    val_output = Path('Checker_Prompt_Optimization/validation_set_CORRECTED.jsonl')
    with open(val_output, 'w') as f:
        for item in val_set:
            f.write(json.dumps(item) + '\n')
    print(f'✓ Saved validation set to {val_output}')

    # Step 4: Create summary
    print('\n[4/4] Creating summary report...')
    summary = create_summary(full_data, val_set, corrected_count, corrections)

    summary_file = Path('Checker_Prompt_Optimization/CORRECTION_SUMMARY.json')
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'✓ Saved summary to {summary_file}')

    print('\n' + '='*60)
    print('SUMMARY')
    print('='*60)
    print(json.dumps(summary, indent=2))
    print('\n✅ Done! Corrected ground truth test set created.')

if __name__ == '__main__':
    main()
