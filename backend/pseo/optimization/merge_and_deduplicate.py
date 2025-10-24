#!/usr/bin/env python3
"""
Merge all valid citations and remove duplicates.
"""
import json
from pathlib import Path

def main():
    print("="*80)
    print("MERGING AND DEDUPLICATING CITATIONS")
    print("="*80)

    # All sources of valid citations
    sources = [
        'backend/pseo/optimization/datasets/valid_citations_final_cleaned.jsonl',
        'backend/pseo/optimization/datasets/train_v2_cleaned.jsonl',
        'backend/pseo/optimization/datasets/val_v2_cleaned.jsonl',
        'backend/pseo/optimization/datasets/test_v2_cleaned.jsonl',
    ]

    # Track unique citations by text
    unique_citations = {}

    for source_path in sources:
        filepath = Path(source_path)
        if not filepath.exists():
            continue

        print(f"\nProcessing: {filepath.name}")
        with open(filepath) as f:
            citations = [json.loads(line) for line in f]

        print(f"  Found: {len(citations)} citations")

        added = 0
        for cit in citations:
            # Get citation text (handle different formats)
            text = cit.get('citation_text', cit.get('citation', ''))

            if not text:
                continue

            # Only add if not seen before
            if text not in unique_citations:
                unique_citations[text] = cit
                added += 1

        print(f"  Added: {added} new unique citations")

    print(f"\n{'='*80}")
    print(f"TOTAL UNIQUE CITATIONS: {len(unique_citations)}")
    print(f"{'='*80}")

    # Save deduplicated dataset
    output_file = Path('backend/pseo/optimization/datasets/valid_citations_deduplicated.jsonl')

    with open(output_file, 'w') as f:
        for cit in unique_citations.values():
            # Standardize format
            standardized = {
                'citation_text': cit.get('citation_text', cit.get('citation', '')),
                'source_type': cit.get('source_type', 'unknown'),
                'is_valid': True,
                'metadata': cit.get('metadata', {})
            }
            f.write(json.dumps(standardized) + '\n')

    print(f"\n✓ Saved {len(unique_citations)} deduplicated citations to:")
    print(f"  {output_file}")

    # Verify [ITALIC] formatting preserved
    with_italic = sum(1 for cit in unique_citations.values()
                      if '[ITALIC]' in cit.get('citation_text', cit.get('citation', '')))

    print(f"\n✓ Citations with [ITALIC] formatting: {with_italic}/{len(unique_citations)}")
    print(f"  ({with_italic/len(unique_citations)*100:.1f}%)")

if __name__ == '__main__':
    main()
