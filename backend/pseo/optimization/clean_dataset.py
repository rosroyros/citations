#!/usr/bin/env python3
"""
Remove placeholder citations from datasets
"""
import json
import re
from pathlib import Path

# Placeholder patterns to detect and remove
PLACEHOLDER_PATTERNS = [
    r'\bAuthor, A\. A\.',
    r'\bLastname, F\. M\.',
    r'\bLast Name, F\. M\.',
    r'\bEditor, E\. E\.',
    r'\bHost, A\. A\.',
    r'\bName of Group\b',
    r'\[@username\]',
    r'\bTitle of (chapter|article|book|video|dataset|software|dissertation|thesis|presentation|talk|page|post|episode)\b',
    r'\bTitle of Periodical\b',
    r'\bTitle of Publication\b',
    r'\bPublisher\b(?! Information)',  # Publisher as placeholder, not "Publisher Information"
    r'\bURL\b',
    r'\bVersion No\.',
    r'\bPublication No\.',
    r'\bDatabase Name\b',
    r'http://example',
    r'https://example',
    r'https://doi\.org/xx\.',
    r'10\.xxxx',
    r'\bVol\.\(Issue\)',
    r'\bVol\.\(No\.\)',
    r'\bName of publishing website\b',
    r'\bStreaming Service\b',
    r'\bSite Name\b',
    r'\bType of post\b',
    r'\bContent of the post up to the first 20 words\b',
]

COMBINED_PATTERN = '|'.join(f'({p})' for p in PLACEHOLDER_PATTERNS)
REGEX = re.compile(COMBINED_PATTERN, re.IGNORECASE)


def is_placeholder(citation_text: str) -> bool:
    """Check if citation contains placeholder patterns"""
    return bool(REGEX.search(citation_text))


def clean_dataset_file(input_path: Path, output_path: Path):
    """Remove placeholders from dataset file"""
    print(f"\n=== Cleaning {input_path.name} ===")

    with open(input_path) as f:
        examples = [json.loads(line) for line in f]

    original_count = len(examples)
    print(f"Original: {original_count} examples")

    # Separate real vs placeholder
    real_examples = []
    placeholders = []

    for ex in examples:
        citation = ex.get('citation', '')
        if is_placeholder(citation):
            placeholders.append((citation[:100], ex))
        else:
            real_examples.append(ex)

    print(f"Real citations: {len(real_examples)}")
    print(f"Placeholders removed: {len(placeholders)}")

    if placeholders:
        print("\nSample placeholders removed:")
        for cit, _ in placeholders[:3]:
            print(f"  - {cit}...")

    # Write cleaned dataset
    with open(output_path, 'w') as f:
        for ex in real_examples:
            f.write(json.dumps(ex) + '\n')

    print(f"Saved to: {output_path}")
    return len(real_examples), len(placeholders)


if __name__ == '__main__':
    datasets_dir = Path('backend/pseo/optimization/datasets')

    total_real = 0
    total_removed = 0

    # Clean train/val/test v2
    for dataset in ['train_v2', 'val_v2', 'test_v2']:
        input_file = datasets_dir / f'{dataset}.jsonl'
        output_file = datasets_dir / f'{dataset}_cleaned.jsonl'

        real, removed = clean_dataset_file(input_file, output_file)
        total_real += real
        total_removed += removed

    print(f"\n=== SUMMARY ===")
    print(f"Total real citations: {total_real}")
    print(f"Total placeholders removed: {total_removed}")
    print(f"Removal rate: {total_removed/(total_real+total_removed)*100:.1f}%")
