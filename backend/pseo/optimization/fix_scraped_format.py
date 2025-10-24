#!/usr/bin/env python3
"""
Fix scraped citations to match existing format exactly
- Add proper underscore italics
- Match JSONL structure exactly
- Preserve rich text formatting for validation
"""

import json
import re
import os

def fix_italics_in_citation(citation_text):
    """Add proper underscores for italics following APA rules"""

    text = citation_text.strip()

    # Journal article titles (NOT italicized - sentence case)
    # But journal names ARE italicized

    # Book titles ARE italicized
    # Pattern: Author (Year). _Book Title_. Publisher.
    book_pattern = r'(\([A-Z]\.\s*\(\d{4}\)\.\s*)([^.]+?)(\.\s*[A-Z][^,]*Press)'

    def italicize_book_title(match):
        return f"{match.group(1)}_{match.group(2)}_{match.group(3)}"

    text = re.sub(book_pattern, italicize_book_title, text)

    # Journal names ARE italicized (after article title)
    # Pattern: Article title. _Journal Name_, volume(issue), pages.
    journal_patterns = [
        r'([^.!?]+\.)\s*([A-Z][a-zA-Z\s&]+),\s*(\d+\(\d+\))',
        r'([^.!?]+\.)\s*([A-Z][a-zA-Z\s&]+Journal),',
        r'([^.!?]+\.)\s*([A-Z][a-zA-Z\s&]+Review),',
        r'([^.!?]+\.)\s*([A-Z][a-zA-Z\s&]+Quarterly),',
        r'([^.!?]+\.)\s*([A-Z][a-zA-Z\s&]+Studies),',
    ]

    # Fix specific journal names that should be italicized
    journal_names = [
        "The New Criterion",
        "Purdue Journal of Service-Learning and International Engagement",
        "Writing Center Journal",
        "Time",
        "The Country Today",
        "Contemporary Psychology",
        "SubStance"
    ]

    for journal_name in journal_names:
        # Italicize journal names when they appear before volume info
        pattern = rf'(\. )({journal_name}),'
        text = re.sub(pattern, lambda m: f". _{m.group(2)}_,", text)

        # Also handle when journal appears at end
        pattern = rf'(. ){journal_name}\.$'
        text = re.sub(pattern, lambda m: f"{m.group(1)}_{journal_name}.", text)

    # Italicize book titles from known examples
    book_titles = [
        "Alexander the Great: A life in legend",
        "Writing your journal article in twelve weeks: A guide to academic publishing success",
        "Le morte darthur",
        "A new companion to Malory",
        "Symposium"
    ]

    for book_title in book_titles:
        if book_title in text and not f"_{book_title}_" in text:
            text = text.replace(book_title, f"_{book_title}_")

    # Italicize other work titles (artworks, etc.)
    work_titles = [
        "Nighthawks",
        "Sea smoke on Lake Michigan"
    ]

    for work_title in work_titles:
        if work_title in text and not f"_{work_title}_" in text:
            text = text.replace(f"{work_title} [", f"_{work_title}_ [")

    return text

def fix_scraped_citations():
    """Fix scraped citations to match existing format"""

    # Files
    scraped_file = "backend/pseo/optimization/datasets/valid_citations_enhanced.jsonl"
    existing_file = "backend/pseo/optimization/datasets/valid_citations_clean_final.jsonl"
    output_file = "backend/pseo/optimization/datasets/valid_citations_fixed.jsonl"

    # Load existing citations to match format
    existing_citations = []
    if os.path.exists(existing_file):
        with open(existing_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    existing_citations.append(json.loads(line))

    # Load scraped citations
    scraped_citations = []
    if os.path.exists(scraped_file):
        with open(scraped_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    scraped_citations.append(json.loads(line))

    print(f"📚 Loaded {len(existing_citations)} existing citations")
    print(f"🆕 Loaded {len(scraped_citations)} scraped citations")

    # Fix scraped citations
    fixed_scraped = []
    for i, citation in enumerate(scraped_citations):
        # Create new citation with proper ID format
        fixed_citation = {
            "citation_id": f"purdue_owl_{len(existing_citations) + i + 1:03d}",
            "citation_text": fix_italics_in_citation(citation['citation_text']),
            "source_type": citation['source_type'],
            "is_valid": True,
            "metadata": {
                "source": "Purdue OWL",
                "url": citation['metadata']['url'],
                "section": citation['metadata']['section'].replace('Articles in Periodicals', 'Journal Articles').replace('Books', 'Books'),
                "date_collected": citation['metadata']['date_collected'],
                "formatting_preserved": True,
                "verified_against_kb": False
            }
        }

        original_text = citation['citation_text']
        fixed_text = fixed_citation['citation_text']

        if original_text != fixed_text:
            print(f"✏️  Fixed italics: {original_text[:60]}...")
            print(f"   To: {fixed_text[:60]}...")

        fixed_scraped.append(fixed_citation)

    # Combine datasets
    all_citations = existing_citations + fixed_scraped

    # Remove duplicates based on citation text
    unique_citations = []
    seen_texts = set()

    for citation in all_citations:
        text = citation['citation_text']
        if text not in seen_texts:
            seen_texts.add(text)
            unique_citations.append(citation)

    # Save fixed dataset
    with open(output_file, 'w', encoding='utf-8') as f:
        for citation in unique_citations:
            f.write(json.dumps(citation, ensure_ascii=False) + '\n')

    print(f"\n{'='*60}")
    print("CITATION FORMAT FIXING COMPLETE")
    print(f"{'='*60}")
    print(f"Total citations: {len(unique_citations)}")
    print(f"Fixed scraped citations: {len(fixed_scraped)}")
    print(f"Removed duplicates: {len(all_citations) - len(unique_citations)}")
    print(f"Saved to: {output_file}")

    # Show examples of fixed citations
    print(f"\n📝 Examples of fixed citations:")
    for i, citation in enumerate(fixed_scraped[:3], 1):
        print(f"{i}. {citation['citation_text']}")
        print(f"   ID: {citation['citation_id']}")
        print(f"   Type: {citation['source_type']}")

    return unique_citations

if __name__ == "__main__":
    citations = fix_scraped_citations()