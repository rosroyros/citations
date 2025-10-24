"""
Merge citations from different sources into a single dataset.
"""
import json
from pathlib import Path


def merge_citations():
    """Merge citations from Purdue OWL, APA Blog, and other sources."""

    all_citations = []

    # Load Purdue OWL citations
    purdue_file = Path("backend/pseo/optimization/datasets/valid_citations_raw.jsonl")
    if purdue_file.exists():
        with open(purdue_file, 'r') as f:
            for line in f:
                citation = json.loads(line.strip())
                all_citations.append(citation)
        print(f"✓ Loaded {len(all_citations)} citations from Purdue OWL")

    # Load APA Blog citations
    apa_file = Path("backend/pseo/optimization/data_collection/apa_blog_citations.json")
    if apa_file.exists():
        with open(apa_file, 'r') as f:
            apa_citations = json.load(f)
            all_citations.extend(apa_citations)
        print(f"✓ Added {len(apa_citations)} citations from APA Style Blog")

    # Save merged dataset
    output_file = Path("backend/pseo/optimization/datasets/valid_citations_merged.jsonl")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        for citation in all_citations:
            f.write(json.dumps(citation) + '\n')

    print(f"\n✓ Merged dataset saved: {output_file}")
    print(f"✓ Total valid citations: {len(all_citations)}")

    # Statistics
    from collections import Counter
    by_source = Counter(c['metadata']['source'] for c in all_citations)
    by_type = Counter(c['source_type'] for c in all_citations)

    print("\nDataset Statistics:")
    print("="*60)
    print(f"Total citations: {len(all_citations)}")
    print(f"\nBy source:")
    for source, count in by_source.items():
        print(f"  {source}: {count}")
    print(f"\nBy type:")
    for type_, count in by_type.items():
        print(f"  {type_}: {count}")

    return all_citations


if __name__ == "__main__":
    citations = merge_citations()
