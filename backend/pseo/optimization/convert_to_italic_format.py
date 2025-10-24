#!/usr/bin/env python3
"""
Convert all citations to [ITALIC] marker format to match backend HTML converter.

This script intelligently adds [ITALIC] markers based on source type and APA 7 rules.
"""

import json
import re
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
DATASETS_DIR = SCRIPT_DIR / "datasets"

def add_italic_markers_journal(citation: str) -> str:
    """
    Add [ITALIC] markers to journal article citations.

    Italicize:
    - Journal/periodical title
    - Volume number (but NOT issue number)
    """
    # Pattern: Title. Journal Name, Volume(Issue)
    # Example: Article title. Journal of Psychology, 45(2), 123-145.

    # Find journal title and volume (between article title and issue/pages)
    # This is a heuristic approach - looks for pattern after first period

    # Pattern 1: ...title. Journal Name, 45(2)...
    pattern1 = r'(\.\s+)([A-Z][^,.]+)(,\s*)(\d+)(\()'
    if re.search(pattern1, citation):
        citation = re.sub(
            pattern1,
            r'\1[ITALIC]\2[/ITALIC]\3[ITALIC]\4[/ITALIC]\5',
            citation,
            count=1  # Only first occurrence
        )

    return citation

def add_italic_markers_book(citation: str) -> str:
    """
    Add [ITALIC] markers to book citations.

    Italicize:
    - Book title (after year, before publisher or edition)
    """
    # Pattern: (Year). Book Title. Publisher
    # or: (Year). Book Title (Edition). Publisher

    # Pattern: (YYYY). Title. Publisher or (ed.)
    pattern = r'(\(\d{4}\)\.\s+)([^(.]+?)(\.\s+(?:[A-Z][^.]+\.|$|\())'
    if re.search(pattern, citation):
        citation = re.sub(
            pattern,
            r'\1[ITALIC]\2[/ITALIC]\3',
            citation,
            count=1
        )

    return citation

def add_italic_markers_book_chapter(citation: str) -> str:
    """
    Add [ITALIC] markers to book chapter citations.

    Italicize:
    - Book title (after "In ... (Eds.),", before page numbers)
    """
    # Pattern: In Editor (Eds.), Book Title (pp. 123-145)
    pattern = r'(\(Eds?\.\),\s+)([^(]+?)(\s+\(pp\.)'
    if re.search(pattern, citation):
        citation = re.sub(
            pattern,
            r'\1[ITALIC]\2[/ITALIC]\3',
            citation,
            count=1
        )

    return citation

def add_italic_markers_webpage(citation: str) -> str:
    """
    Add [ITALIC] markers to webpage citations.

    Italicize:
    - Website name (before URL or "Retrieved")
    """
    # Pattern: Website Name. Retrieved or URL
    # Example: Article title. Website Name. https://...

    # Look for pattern before "Retrieved" or "https://"
    pattern = r'(\.\s+)([A-Z][^.]+?)(\.\s+(?:Retrieved|https?://))'
    if re.search(pattern, citation):
        citation = re.sub(
            pattern,
            r'\1[ITALIC]\2[/ITALIC]\3',
            citation,
            count=1
        )

    return citation

def add_italic_markers_social_media(citation: str) -> str:
    """
    Add [ITALIC] markers to social media citations.

    Italicize:
    - Post title/content (first 20 words before [Content Type])
    """
    # Pattern: Title text [Tweet] or [Video] or [Photograph]
    pattern = r'(\.\s+)([^[]+)(\s+\[(?:Tweet|Video|Photograph|Instagram post|Facebook post)\])'
    if re.search(pattern, citation):
        citation = re.sub(
            pattern,
            r'\1[ITALIC]\2[/ITALIC]\3',
            citation,
            count=1
        )

    return citation

def convert_citation_to_italic_format(citation: str, source_type: str) -> str:
    """
    Convert citation to [ITALIC] format based on source type.

    Args:
        citation: Citation text
        source_type: One of: journal article, book, book chapter, webpage, social media, other

    Returns:
        Citation with [ITALIC] markers added
    """
    source_type = source_type.lower()

    if 'journal' in source_type or source_type == 'other':
        # Try journal article pattern (works for many "other" types too)
        return add_italic_markers_journal(citation)
    elif source_type == 'book':
        return add_italic_markers_book(citation)
    elif 'chapter' in source_type:
        return add_italic_markers_book_chapter(citation)
    elif 'web' in source_type or 'electronic' in source_type:
        return add_italic_markers_webpage(citation)
    elif 'social' in source_type:
        return add_italic_markers_social_media(citation)
    else:
        # Default: try journal pattern
        return add_italic_markers_journal(citation)

def process_file(input_file: Path, output_file: Path, key_name='citation_text'):
    """
    Process a JSONL file and add [ITALIC] markers to all citations.

    Args:
        input_file: Input JSONL file path
        output_file: Output JSONL file path
        key_name: JSON key containing citation text (default: 'citation_text')
    """
    print(f"\nProcessing: {input_file.name}")

    converted_count = 0
    skipped_count = 0

    with open(input_file) as f_in, open(output_file, 'w') as f_out:
        for line_num, line in enumerate(f_in, 1):
            data = json.loads(line)

            # Get citation and source type
            citation = data.get(key_name, data.get('citation', ''))
            source_type = data.get('source_type', data.get('_reference_source_type', 'other'))

            # Skip if already has [ITALIC] markers
            if '[ITALIC]' in citation:
                skipped_count += 1
            else:
                # Convert to italic format
                new_citation = convert_citation_to_italic_format(citation, source_type)

                # Update citation
                if key_name in data:
                    data[key_name] = new_citation
                elif 'citation' in data:
                    data['citation'] = new_citation

                if new_citation != citation:
                    converted_count += 1

            f_out.write(json.dumps(data) + '\n')

    print(f"  ✓ Converted {converted_count} citations")
    print(f"  ⊘ Skipped {skipped_count} (already had markers)")
    print(f"  → Saved to: {output_file.name}")

    return converted_count

def main():
    """Convert all dataset files to [ITALIC] format."""
    print("="*80)
    print("CONVERT CITATIONS TO [ITALIC] FORMAT")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    total_converted = 0

    # Process valid citations
    total_converted += process_file(
        DATASETS_DIR / "valid_citations_no_placeholders.jsonl",
        DATASETS_DIR / "valid_citations_italic.jsonl",
        key_name='citation_text'
    )

    # Process invalid citations
    total_converted += process_file(
        DATASETS_DIR / "invalid_citations_enhanced.jsonl",
        DATASETS_DIR / "invalid_citations_italic.jsonl",
        key_name='citation_text'
    )

    # Process social media citations
    total_converted += process_file(
        DATASETS_DIR / "social_media_citations.jsonl",
        DATASETS_DIR / "social_media_italic.jsonl",
        key_name='citation_text'
    )

    # Summary
    print("\n" + "="*80)
    print("CONVERSION SUMMARY")
    print("="*80)
    print(f"✓ Total citations converted: {total_converted}")
    print("\nNext step: Merge files and regenerate train/val/test splits")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
