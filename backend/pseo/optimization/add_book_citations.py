#!/usr/bin/env python3
"""
Add book citations to the dataset by scraping authoritative sources.

Features:
- Scrapes APA book examples and Purdue OWL non-print sources
- Filters for books/book chapters only
- Removes placeholders
- Adds to valid citations
- Generates corresponding invalid citations with errors
- Reports statistics
"""
import sys
from pathlib import Path

# Add data_collection to path for scraper import
sys.path.insert(0, str(Path(__file__).parent / 'data_collection'))

from rescrape_with_formatting import FormattingPreservingScraper, convert_html_to_markdown_italics
import json
import re
from collections import Counter


# Placeholder patterns (same as remove_placeholder_citations.py)
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


def contains_placeholder(text):
    """Check if text contains any placeholder"""
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def scrape_apa_books(scraper):
    """Scrape APA book reference examples"""
    print("\n📚 Scraping APA Book References...")
    url = "https://apastyle.apa.org/style-grammar-guidelines/references/examples/book-references"

    try:
        response = scraper.client.get(url)
        response.raise_for_status()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find citation examples (adjust selectors based on actual HTML)
        citation_blocks = soup.find_all(['p', 'li', 'div'])

        books = []
        book_id = 1

        for block in citation_blocks:
            text_preview = block.get_text(strip=True)

            if len(text_preview) < 20:
                continue

            if scraper._looks_like_citation(text_preview):
                html = str(block)
                citation_text = convert_html_to_markdown_italics(html)

                # Must be book-related
                if not any(keyword in citation_text.lower() for keyword in ['press', 'publisher', 'publishing', '(ed', 'edition']):
                    continue

                # Skip if has placeholders
                if contains_placeholder(citation_text):
                    continue

                source_type = scraper._detect_source_type(citation_text)

                # Only keep books and book chapters
                if source_type not in ['book', 'book chapter']:
                    continue

                citation_data = {
                    "citation_id": f"apa_book_{book_id:03d}",
                    "citation_text": citation_text,
                    "source_type": source_type,
                    "is_valid": True,
                    "metadata": {
                        "source": "APA Style Guide",
                        "url": url,
                        "section": "Book References",
                        "date_collected": "2025-10-21",
                        "verified_against_kb": True
                    }
                }

                books.append(citation_data)
                book_id += 1

                if book_id <= 3:
                    print(f"  ✓ Example: {citation_text[:80]}...")

        print(f"  Found {len(books)} book citations from APA")
        return books

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return []


def scrape_purdue_nonprint(scraper):
    """Scrape Purdue OWL non-print sources for books"""
    print("\n📚 Scraping Purdue OWL Non-Print Sources...")
    url = "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_other_non_print_sources.html"

    citations = scraper.scrape_purdue_owl(url, "Non-Print Sources")

    # Filter for books only
    books = [c for c in citations if c['source_type'] in ['book', 'book chapter']]
    books = [c for c in books if not contains_placeholder(c['citation_text'])]

    print(f"  Found {len(books)} book citations from Purdue OWL")
    return books


def inject_book_errors(valid_citation):
    """Generate invalid versions of a book citation"""
    invalid_citations = []
    citation_text = valid_citation['citation_text']
    base_id = valid_citation['citation_id']

    # Error 1: Use 'and' instead of '&' before final author
    if ' & ' in citation_text and citation_text.count('&') >= 1:
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
                "error_types": ["auth001"]
            },
            "citation_id": f"{base_id}_err_and"
        })

    # Error 2: Include publisher location (removed in APA 7)
    if 'Press' in citation_text or 'Publishing' in citation_text:
        # Insert location before publisher
        modified = re.sub(
            r'(\.\s+)([A-Z][a-z]+\s+(?:University\s+)?Press)',
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
                    "error_types": ["pub001"]
                },
                "citation_id": f"{base_id}_err_loc"
            })

    # Error 3: Title case instead of sentence case
    # Find the title (after year, before publisher)
    title_match = re.search(r'\([\d\-]+\)\.\s+([^.]+)\.', citation_text)
    if title_match:
        original_title = title_match.group(1)
        # Title case version (capitalize most words)
        title_cased = ' '.join(word.capitalize() if len(word) > 3 else word for word in original_title.split())
        modified = citation_text.replace(original_title, title_cased, 1)

        if modified != citation_text:
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
                    "error_types": ["cap001"]
                },
                "citation_id": f"{base_id}_err_cap"
            })

    return invalid_citations


def main():
    print("=" * 80)
    print("ADDING BOOK CITATIONS TO DATASET")
    print("=" * 80)

    scraper = FormattingPreservingScraper()

    # Scrape books from both sources
    apa_books = scrape_apa_books(scraper)
    purdue_books = scrape_purdue_nonprint(scraper)

    all_books = apa_books + purdue_books

    print(f"\n📊 Total books scraped: {len(all_books)}")

    # Check for duplicates by citation text
    seen_texts = set()
    unique_books = []
    duplicates = 0

    for book in all_books:
        text_key = book['citation_text'].lower().strip()
        if text_key not in seen_texts:
            seen_texts.add(text_key)
            unique_books.append(book)
        else:
            duplicates += 1

    print(f"  Duplicates removed: {duplicates}")
    print(f"  Unique books: {len(unique_books)}")

    # Load current datasets
    datasets_dir = Path(__file__).parent / 'datasets'
    valid_path = datasets_dir / 'valid_citations_clean_final.jsonl'
    invalid_path = datasets_dir / 'invalid_citations_standardized.jsonl'

    # Load existing valid citations
    existing_valid = []
    if valid_path.exists():
        with open(valid_path) as f:
            for line in f:
                existing_valid.append(json.loads(line))

    print(f"\n📋 Current valid citations: {len(existing_valid)}")

    # Check for citation_id conflicts
    existing_ids = {c['citation_id'] for c in existing_valid}
    books_to_add = []

    for book in unique_books:
        # Regenerate ID if conflict
        if book['citation_id'] in existing_ids:
            # Find next available ID
            base = book['citation_id'].rsplit('_', 1)[0]
            counter = 1
            while f"{base}_{counter:03d}" in existing_ids:
                counter += 1
            book['citation_id'] = f"{base}_{counter:03d}"

        existing_ids.add(book['citation_id'])
        books_to_add.append(book)

    # Add to valid citations
    all_valid = existing_valid + books_to_add

    with open(valid_path, 'w') as f:
        for citation in all_valid:
            f.write(json.dumps(citation, ensure_ascii=False) + '\n')

    print(f"  ✓ Added {len(books_to_add)} books to valid citations")
    print(f"  New total: {len(all_valid)}")

    # Generate invalid versions
    print(f"\n🔧 Generating invalid book citations...")
    all_invalid_books = []

    for book in books_to_add:
        invalid_versions = inject_book_errors(book)
        all_invalid_books.extend(invalid_versions)

    print(f"  Generated {len(all_invalid_books)} invalid book citations")

    # Load existing invalid citations
    existing_invalid = []
    if invalid_path.exists():
        with open(invalid_path) as f:
            for line in f:
                existing_invalid.append(json.loads(line))

    # Add to invalid citations
    all_invalid = existing_invalid + all_invalid_books

    with open(invalid_path, 'w') as f:
        for citation in all_invalid:
            f.write(json.dumps(citation, ensure_ascii=False) + '\n')

    print(f"  ✓ Added {len(all_invalid_books)} invalid books")
    print(f"  New total invalid: {len(all_invalid)}")

    # Report source type distribution
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
    print("✅ BOOK CITATIONS ADDED")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Re-run remove_placeholder_citations.py (safety check)")
    print("2. Verify source distribution")
    print("3. Run optimization: python3 backend/pseo/optimization/run_gepa_final.py")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
