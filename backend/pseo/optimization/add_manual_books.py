#!/usr/bin/env python3
"""
Add manually extracted book citations to the dataset.
"""
import json
from pathlib import Path
from collections import Counter
import re


def inject_book_errors(valid_citation):
    """Generate invalid versions of a book citation"""
    invalid_citations = []
    citation_text = valid_citation['citation_text']
    base_id = valid_citation['citation_id']

    # Error 1: Use 'and' instead of '&' before final author
    if ' & ' in citation_text:
        modified = citation_text.replace(' & ', ' and ', 1)
        invalid_citations.append({
            "citation_text": modified,
            "source_type": valid_citation['source_type'],
            "is_valid": False,
            "errors": [{
                "component": "authors",
                "problem": "Using 'and' instead of '&' before final author",
                "correction": "Should use '&' in reference list"
            }],
            "metadata": {
                **valid_citation['metadata'],
                "derived_from": base_id,
                "error_injection_method": "programmatic",
                "error_types": ["auth001"],
                "date_created": "2025-10-21"
            },
            "citation_id": f"{base_id}_err_and"
        })

    # Error 2: Include publisher location (removed in APA 7)
    if any(pub in citation_text for pub in ['Press', 'Publishing', 'Wiley', 'Viking', 'Associates']):
        # Insert location before publisher
        modified = re.sub(
            r'(\.\s+)([A-Z][a-z]+(?:\s+[A-Z&][a-z]+)*(?:\s+(?:Press|Publishing|Associates|Wiley|Viking|Irwin)))',
            r'\1New York, NY: \2',
            citation_text
        )
        if modified != citation_text:
            invalid_citations.append({
                "citation_text": modified,
                "source_type": valid_citation['source_type'],
                "is_valid": False,
                "errors": [{
                    "component": "publisher",
                    "problem": "Including publisher location (removed in APA 7)",
                    "correction": "Should remove location"
                }],
                "metadata": {
                    **valid_citation['metadata'],
                    "derived_from": base_id,
                    "error_injection_method": "programmatic",
                    "error_types": ["pub001"],
                    "date_created": "2025-10-21"
                },
                "citation_id": f"{base_id}_err_loc"
            })

    # Error 3: Title case instead of sentence case for book title
    # Find italicized title (between underscores)
    title_match = re.search(r'_([^_]+)_', citation_text)
    if title_match:
        original_title = title_match.group(1)
        # Title case version
        title_cased = ' '.join(
            word.capitalize() if len(word) > 2 and word not in ['and', 'the', 'of', 'in', 'at', 'to']
            else word
            for word in original_title.split()
        )
        # Capitalize first word always
        if title_cased:
            title_cased = title_cased[0].upper() + title_cased[1:]

        modified = citation_text.replace(f'_{original_title}_', f'_{title_cased}_', 1)

        if modified != citation_text and original_title != title_cased:
            invalid_citations.append({
                "citation_text": modified,
                "source_type": valid_citation['source_type'],
                "is_valid": False,
                "errors": [{
                    "component": "title",
                    "problem": "Using title case instead of sentence case for book title",
                    "correction": f"Should be: {original_title}"
                }],
                "metadata": {
                    **valid_citation['metadata'],
                    "derived_from": base_id,
                    "error_injection_method": "programmatic",
                    "error_types": ["cap001"],
                    "date_created": "2025-10-21"
                },
                "citation_id": f"{base_id}_err_cap"
            })

    return invalid_citations


def main():
    print("=" * 80)
    print("ADDING MANUAL BOOK CITATIONS")
    print("=" * 80)

    # Load manual books
    manual_books = []

    # Load from both files
    for filename in ['manual_book_citations.jsonl', 'additional_books.jsonl']:
        manual_path = Path(__file__).parent / filename
        if manual_path.exists():
            with open(manual_path) as f:
                for line in f:
                    manual_books.append(json.loads(line))

    print(f"\n📚 Loaded {len(manual_books)} manual book citations")

    # Load current datasets
    datasets_dir = Path(__file__).parent / 'datasets'
    valid_path = datasets_dir / 'valid_citations_clean_final.jsonl'
    invalid_path = datasets_dir / 'invalid_citations_standardized.jsonl'

    # Load existing
    existing_valid = []
    with open(valid_path) as f:
        for line in f:
            existing_valid.append(json.loads(line))

    existing_invalid = []
    with open(invalid_path) as f:
        for line in f:
            existing_invalid.append(json.loads(line))

    print(f"📋 Current valid: {len(existing_valid)}")
    print(f"📋 Current invalid: {len(existing_invalid)}")

    # Add books to valid
    all_valid = existing_valid + manual_books

    with open(valid_path, 'w') as f:
        for citation in all_valid:
            f.write(json.dumps(citation, ensure_ascii=False) + '\n')

    print(f"\n✓ Added {len(manual_books)} books to valid citations")
    print(f"  New total: {len(all_valid)}")

    # Generate invalid versions
    print(f"\n🔧 Generating invalid book citations...")
    all_invalid_books = []

    for book in manual_books:
        invalid_versions = inject_book_errors(book)
        all_invalid_books.extend(invalid_versions)

    print(f"  Generated {len(all_invalid_books)} invalid versions")

    # Add to invalid
    all_invalid = existing_invalid + all_invalid_books

    with open(invalid_path, 'w') as f:
        for citation in all_invalid:
            f.write(json.dumps(citation, ensure_ascii=False) + '\n')

    print(f"  ✓ Added {len(all_invalid_books)} invalid books")
    print(f"  New total invalid: {len(all_invalid)}")

    # Report distribution
    print("\n" + "=" * 80)
    print("UPDATED SOURCE TYPE DISTRIBUTION")
    print("=" * 80)

    type_counts = Counter(c['source_type'] for c in all_valid)
    total = len(all_valid)

    for source_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        pct = (count / total * 100)
        print(f"  {source_type:20s}: {count:3d} ({pct:5.1f}%)")

    print(f"\n  Total valid: {total}")
    print(f"  Total invalid: {len(all_invalid)}")
    print(f"  Combined: {total + len(all_invalid)}")

    print("\n" + "=" * 80)
    print("✅ MANUAL BOOKS ADDED")
    print("=" * 80)


if __name__ == "__main__":
    main()
