#!/usr/bin/env python3
"""
Remove citations containing placeholder text from scrpbee dataset.
Based on the existing remove_placeholder_citations.py but adapted for scrpbee files.
"""

import json
import re
from pathlib import Path
from collections import Counter

# Comprehensive list of placeholder patterns (same as original)
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

def filter_scrpbee_dataset(input_path, output_path):
    """Filter scrpbee dataset to remove citations with placeholders"""

    kept = []
    removed = []
    removed_reasons = []

    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                try:
                    data = json.loads(line)
                    citation_text = data.get('citation_text', '')

                    if contains_placeholder(citation_text):
                        removed.append(data)
                        # Find which pattern matched (for reporting)
                        for pattern in PLACEHOLDER_PATTERNS:
                            if re.search(pattern, citation_text, re.IGNORECASE):
                                removed_reasons.append((pattern, line_num, data.get('citation_id', 'unknown')))
                                break
                    else:
                        kept.append(data)
                except json.JSONDecodeError as e:
                    print(f"⚠️  Line {line_num}: JSON decode error - {e}")
                    continue

    # Write kept citations to output
    with open(output_path, 'w', encoding='utf-8') as f:
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
    print("REMOVING PLACEHOLDER CITATIONS FROM SCRPBEE DATASET")
    print("=" * 80)

    input_path = "backend/pseo/optimization/datasets/scrpbee/scrpbee_valid_citations.jsonl"
    output_path = "backend/pseo/optimization/datasets/scrpbee/scrpbee_valid_citations_clean.jsonl"
    backup_path = "backend/pseo/optimization/datasets/scrpbee/scrpbee_valid_citations_original.jsonl"

    # Check if input file exists
    if not Path(input_path).exists():
        print(f"❌ Input file not found: {input_path}")
        return

    # Backup original
    import shutil
    shutil.copy(input_path, backup_path)
    print(f"   ✓ Backed up original to: {backup_path}")

    # Filter
    print(f"\n📋 Processing {input_path}...")
    kept, removed, removed_reasons = filter_scrpbee_dataset(input_path, output_path)

    print(f"   ✓ Kept: {len(kept)}")
    print(f"   ❌ Removed: {len(removed)}")

    if removed:
        print(f"\n🚨 Removed citations with placeholders:")
        for reason, line_num, citation_id in removed_reasons:
            print(f"   Line {line_num} | ID: {citation_id} | Pattern: {reason}")

    print("\n" + "=" * 80)
    print("SCRPBEE DATASET SUMMARY")
    print("=" * 80)

    print(f"\nTotal original citations: {len(kept) + len(removed)}")
    print(f"Total cleaned citations: {len(kept)}")
    print(f"Citations removed with placeholders: {len(removed)}")

    print("\n📊 Source Type Distribution (Cleaned Citations):")
    types = analyze_source_types(kept)
    for source_type, count in sorted(types.items(), key=lambda x: -x[1]):
        pct = (count / len(kept) * 100) if kept else 0
        print(f"   {source_type:20s}: {count:3d} ({pct:5.1f}%)")

    # Show sample of kept citations
    print(f"\n📝 Sample cleaned citations:")
    for i, citation in enumerate(kept[:3], 1):
        print(f"{i}. {citation['citation_text']}")
        print(f"   Type: {citation['source_type']} | ID: {citation['citation_id']}")

    print("\n" + "=" * 80)
    print("✅ SCRPBEE CLEANUP COMPLETE")
    print("=" * 80)
    print(f"\n✓ Original file backed up to: {backup_path}")
    print(f"✓ Clean dataset saved to: {output_path}")
    print(f"\n🎯 Ready for error injection and training!")

if __name__ == "__main__":
    main()