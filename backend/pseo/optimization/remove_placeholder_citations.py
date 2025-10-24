#!/usr/bin/env python3
"""
Remove citations containing placeholder text from datasets.

Instead of trying to fix placeholders, we completely remove any citation
that contains common placeholder patterns. This ensures only real, complete
citations remain in the training data.
"""
import json
import re
from pathlib import Path
from collections import Counter


# Comprehensive list of placeholder patterns
PLACEHOLDER_PATTERNS = [
    r'\bYear\b',
    r'\bMonth Date\b',
    r'Title of (article|work|book|post|page|chapter|presentation|entry|dataset|software|talk)',
    r'Author, [A-Z]\. [A-Z]\.',
    r'Lastname, F\. M\.',
    r'volume number',
    r'issue number',
    r'\(n\.d\.\)',
    r'Year of publication',
    r'pages of chapter',
    r'Publisher Name',
    r'Site Name',
    r'Name of (publishing website|podcast|Institution)',
    r'DOI \(if available\)',
    r'\[username\]',
    r'Editor, [A-Z]\. [A-Z]\.',
    r'Group name',
    r'Host, [A-Z]\. [A-Z]\.',
    r'pp\. pages',
    r'Version No\.',
    r'Retrieved Month Date, Year',
]


def contains_placeholder(citation_text):
    """Check if citation contains any placeholder pattern"""
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, citation_text, re.IGNORECASE):
            return True
    return False


def filter_dataset(input_path, output_path):
    """Filter dataset to remove citations with placeholders"""

    kept = []
    removed = []
    removed_reasons = []

    with open(input_path, 'r') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                citation_text = data.get('citation_text', data.get('citation', ''))

                if contains_placeholder(citation_text):
                    removed.append(data)
                    # Find which pattern matched (for reporting)
                    for pattern in PLACEHOLDER_PATTERNS:
                        if re.search(pattern, citation_text, re.IGNORECASE):
                            removed_reasons.append(pattern)
                            break
                else:
                    kept.append(data)

    # Write kept citations to output
    with open(output_path, 'w') as f:
        for data in kept:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')

    return kept, removed, removed_reasons


def analyze_source_types(citations):
    """Analyze source type distribution"""
    types = Counter()
    for citation in citations:
        source_type = citation.get('source_type', 'unknown')
        types[source_type] += 1
    return types


def main():
    print("=" * 80)
    print("REMOVING PLACEHOLDER CITATIONS")
    print("=" * 80)

    datasets = {
        'valid': 'backend/pseo/optimization/datasets/valid_citations_clean_final.jsonl',
        'invalid': 'backend/pseo/optimization/datasets/invalid_citations_standardized.jsonl'
    }

    all_kept = []
    all_removed = []

    for name, path in datasets.items():
        print(f"\n📋 Processing {name} citations...")
        input_path = Path(path)
        backup_path = input_path.with_suffix('.jsonl.backup')

        # Backup original
        import shutil
        shutil.copy(input_path, backup_path)
        print(f"   ✓ Backed up to: {backup_path}")

        # Filter
        kept, removed, reasons = filter_dataset(input_path, input_path)

        print(f"   Kept: {len(kept)}")
        print(f"   Removed: {len(removed)}")

        all_kept.extend(kept)
        all_removed.extend(removed)

        if removed:
            print(f"\n   Top removal reasons:")
            reason_counts = Counter(reasons)
            for reason, count in reason_counts.most_common(5):
                print(f"     - {reason}: {count}")

    print("\n" + "=" * 80)
    print("DATASET SUMMARY")
    print("=" * 80)

    print(f"\nTotal citations kept: {len(all_kept)}")
    print(f"Total citations removed: {len(all_removed)}")

    print("\n📊 Source Type Distribution (Kept Citations):")
    types = analyze_source_types(all_kept)
    for source_type, count in sorted(types.items(), key=lambda x: -x[1]):
        pct = (count / len(all_kept) * 100) if all_kept else 0
        print(f"   {source_type:20s}: {count:3d} ({pct:5.1f}%)")

    print("\n" + "=" * 80)
    print("✅ CLEANUP COMPLETE")
    print("=" * 80)
    print(f"\nOriginal files backed up with .backup extension")
    print(f"Cleaned datasets ready for optimization")


if __name__ == "__main__":
    main()
