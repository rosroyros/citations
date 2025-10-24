#!/usr/bin/env python3
"""
View all citations in organized format
"""

import json

def view_all_citations():
    """Display all citations organized by type"""

    file_path = "backend/pseo/optimization/datasets/valid_citations_fixed.jsonl"

    citations = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                citations.append(json.loads(line))

    # Group by source type
    by_type = {}
    for citation in citations:
        source_type = citation['source_type']
        if source_type not in by_type:
            by_type[source_type] = []
        by_type[source_type].append(citation)

    print(f"📊 TOTAL CITATIONS: {len(citations)}")
    print(f"{'='*80}")

    for source_type, type_citations in sorted(by_type.items()):
        print(f"\n📚 {source_type.upper()} ({len(type_citations)} citations)")
        print(f"{'-'*60}")

        for i, citation in enumerate(type_citations, 1):
            print(f"{i:2d}. {citation['citation_text']}")
            print(f"    ID: {citation['citation_id']}")
            print(f"    Source: {citation['metadata']['source']}")

        print()

if __name__ == "__main__":
    view_all_citations()