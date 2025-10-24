#!/usr/bin/env python3
"""
Standardize scraped citations to match existing dataset format
- Convert italics to underscore format
- Ensure consistent JSONL structure
- Merge with existing data
"""

import json
import re
import os

def standardize_citation_text(citation_text):
    """Convert citation text to standard format with underscores for italics"""

    # Remove extra spaces
    text = re.sub(r'\s+', ' ', citation_text.strip())

    # Pattern to identify journal/book titles that should be italicized
    # These usually appear after the year and before volume/publisher info
    patterns_to_italicize = [
        # Journal articles: title after year, before journal name
        r'\(\d{4\)\.\s*([^,]+?),\s*([A-Z][^,]+?),\s*\d+\(',
        # Books: title after year, before publisher
        r'\(\d{4\)\.\s*([^,]+?)\.\s*([A-Z][^,]*Press)',
        # Electronic sources: title after year, before website/publisher
        r'\(\d{4\)\.\s*([^,]+?)\.\s*([A-Z][^,]+?)\.?\s*(?:Retrieved|https?://)',
    ]

    for pattern in patterns_to_italicize:
        text = re.sub(pattern, lambda m: f"({m.group(1)}). _{m.group(2)}_, ", text)

    # Specific known titles that should be italicized
    known_titles = [
        "The eclipse of listening",
        "Alexander the Great: A life in legend",
        "Writing your journal article in twelve weeks: A guide to academic publishing success",
        "Obesity in adults: Role of physical activity and exercise",
        "Encyclopedia of big data",
        "Nighthawks",
        "SubStance",
        "What is an assemblage?"
    ]

    for title in known_titles:
        if title in text and not f"_{title}_" in text:
            text = text.replace(title, f"_{title}_")

    # Ensure journal titles are italicized
    journal_patterns = [
        r"([A-Z][a-z\s]+),\s+\d+\(",
        r"([A-Z][a-z\s]+Journal),",
        r"([A-Z][a-z\s]+Review),",
        r"([A-Z][a-z\s]+Quarterly),",
        r"([A-Z][a-z\s]+Studies),"
    ]

    for pattern in journal_patterns:
        text = re.sub(pattern, lambda m: f"_{m.group(1)}_,", text)

    # Clean up spacing around underscores
    text = re.sub(r'\s*_\s*', '_', text)
    text = re.sub(r'_\s*', '_', text)
    text = re.sub(r'\s*_', '_', text)

    return text

def standardize_scraped_data():
    """Standardize scraped citations and merge with existing"""

    # Files to process
    scraped_file = "backend/pseo/optimization/datasets/valid_citations_enhanced.jsonl"
    existing_valid_file = "backend/pseo/optimization/datasets/valid_citations_clean_final.jsonl"
    output_file = "backend/pseo/optimization/datasets/valid_citations_merged.jsonl"

    # Load scraped citations
    scraped_citations = []
    if os.path.exists(scraped_file):
        with open(scraped_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    scraped_citations.append(json.loads(line))

    # Load existing valid citations
    existing_citations = []
    if os.path.exists(existing_valid_file):
        with open(existing_valid_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    existing_citations.append(json.loads(line))

    print(f"📊 Loaded {len(scraped_citations)} scraped citations")
    print(f"📊 Loaded {len(existing_citations)} existing citations")

    # Standardize scraped citations
    standardized_scraped = []
    for citation in scraped_citations:
        # Copy original
        standardized = citation.copy()

        # Standardize the citation text
        original_text = citation['citation_text']
        standardized_text = standardize_citation_text(original_text)

        if standardized_text != original_text:
            print(f"✏️  Standardized: {original_text[:50]}...")
            print(f"   To: {standardized_text[:50]}...")

        standardized['citation_text'] = standardized_text
        standardized['metadata']['formatting_standardized'] = True
        standardized['metadata']['original_text'] = original_text

        standardized_scraped.append(standardized)

    # Merge datasets
    all_citations = existing_citations + standardized_scraped

    # Remove duplicates based on citation text
    unique_citations = []
    seen_texts = set()

    for citation in all_citations:
        text = citation['citation_text']
        if text not in seen_texts:
            seen_texts.add(text)
            unique_citations.append(citation)

    # Save merged dataset
    with open(output_file, 'w', encoding='utf-8') as f:
        for citation in unique_citations:
            f.write(json.dumps(citation, ensure_ascii=False) + '\n')

    print(f"\n{'='*60}")
    print("STANDARDIZATION COMPLETE")
    print(f"{'='*60}")
    print(f"Total citations after merging: {len(unique_citations)}")
    print(f"Removed duplicates: {len(all_citations) - len(unique_citations)}")
    print(f"Standardized citations: {len(standardized_scraped)}")
    print(f"Saved to: {output_file}")

    # Type breakdown
    type_counts = {}
    source_counts = {}

    for citation in unique_citations:
        source_type = citation['source_type']
        source = citation['metadata'].get('source', 'Unknown')

        type_counts[source_type] = type_counts.get(source_type, 0) + 1
        source_counts[source] = source_counts.get(source, 0) + 1

    print("\nBy citation type:")
    for source_type, count in sorted(type_counts.items()):
        print(f"  {source_type}: {count}")

    print("\nBy source:")
    for source, count in sorted(source_counts.items()):
        print(f"  {source}: {count}")

    return unique_citations

def show_examples(citations, count=5):
    """Show examples of standardized citations"""

    print(f"\n📝 Example standardized citations:")

    for i, citation in enumerate(citations[:count], 1):
        print(f"\n{i}. {citation['citation_text']}")
        print(f"   Source: {citation['metadata'].get('source', 'Unknown')}")
        print(f"   Type: {citation['source_type']}")
        print(f"   ID: {citation['citation_id']}")

if __name__ == "__main__":
    citations = standardize_scraped_data()
    show_examples(citations)