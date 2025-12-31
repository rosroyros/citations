#!/usr/bin/env python3
"""
Generate invalid Chicago citation variants for testing.
Based on common errors documented in docs/chicago-research.md
"""

import json
import re
import random

# Error types and their mutation functions
def use_initials(citation, source_type):
    """Replace full first name with initials (APA habit)"""
    # Match "Last, First" at start or after "and "
    pattern = r'([A-Z][a-z]+), ([A-Z][a-z]+)'
    match = re.search(pattern, citation)
    if match:
        last, first = match.groups()
        initial = first[0] + "."
        return citation.replace(f"{last}, {first}", f"{last}, {initial}", 1), "author_initials"
    return None, None

def use_ampersand(citation, source_type):
    """Replace 'and' with '&' for multiple authors"""
    if ", and " in citation:
        return citation.replace(", and ", " & ", 1), "ampersand"
    if " and " in citation and "edited by" not in citation.lower():
        return citation.replace(" and ", " & ", 1), "ampersand"
    return None, None

def remove_place(citation, source_type):
    """Remove place of publication (critical Chicago error)"""
    if source_type in ['book', 'book_chapter']:
        # Match "Place: Publisher, Year" pattern
        pattern = r'([A-Z][a-zA-Z\s,]+): ([A-Z][a-zA-Z\s&]+), (\d{4})'
        match = re.search(pattern, citation)
        if match:
            place, publisher, year = match.groups()
            return citation.replace(f"{place}: {publisher}, {year}", f"{publisher}, {year}"), "missing_place"
    return None, None

def use_sentence_case(citation, source_type):
    """Change Title Case to sentence case"""
    # Find title in italics or quotes
    # For books - title is after author period, before next period
    if source_type in ['book', 'audiobook']:
        parts = citation.split('. ')
        if len(parts) >= 2:
            title = parts[1]
            # Convert to sentence case (lowercase except first word)
            words = title.split()
            if len(words) > 2:
                new_title = words[0] + " " + " ".join(w.lower() if w[0].isupper() and w not in ['I', 'A'] else w for w in words[1:])
                if new_title != title:
                    return citation.replace(title, new_title, 1), "sentence_case"
    return None, None

def add_page_prefix(citation, source_type):
    """Add 'p.' or 'pp.' before page numbers (not used in Chicago)"""
    if source_type in ['journal', 'magazine', 'book_chapter']:
        # Match page range like ": 123-45" or ": 45-59"
        pattern = r': (\d+[–-]\d+)'
        match = re.search(pattern, citation)
        if match:
            pages = match.group(1)
            return citation.replace(f": {pages}", f": pp. {pages}"), "page_prefix"
        # Single page
        pattern = r': (\d+)\.'
        match = re.search(pattern, citation)
        if match:
            page = match.group(1)
            return citation.replace(f": {page}.", f": p. {page}."), "page_prefix"
    return None, None

def remove_ending_period(citation, source_type):
    """Remove final period"""
    if citation.endswith('.'):
        return citation[:-1], "missing_period"
    return None, None

def use_colon_after_author(citation, source_type):
    """Use colon instead of period after author"""
    # Match "Author. Title" and replace with "Author: Title"
    pattern = r'^([A-Z][a-zA-Z]+, [A-Z][a-zA-Z]+)\. '
    match = re.match(pattern, citation)
    if match:
        author = match.group(1)
        return citation.replace(f"{author}. ", f"{author}: ", 1), "colon_after_author"
    return None, None

def remove_quotes_from_article(citation, source_type):
    """Remove quotation marks from article/chapter titles"""
    if source_type in ['journal', 'newspaper', 'magazine', 'book_chapter']:
        if '"' in citation:
            # Find the quoted title and remove quotes
            pattern = r'"([^"]+)"'
            match = re.search(pattern, citation)
            if match:
                title = match.group(1)
                return citation.replace(f'"{title}"', title), "missing_quotes"
    return None, None

def add_retrieved_from(citation, source_type):
    """Add 'Retrieved from' before URL (APA habit)"""
    if 'http' in citation and 'Retrieved from' not in citation:
        return citation.replace('http', 'Retrieved from http'), "retrieved_from"
    return None, None

def missing_comma_date(citation, source_type):
    """Remove comma in date format"""
    if source_type in ['newspaper', 'magazine']:
        # Match "Month Day, Year"
        pattern = r'(January|February|March|April|May|June|July|August|September|October|November|December) (\d+), (\d{4})'
        match = re.search(pattern, citation)
        if match:
            month, day, year = match.groups()
            return citation.replace(f"{month} {day}, {year}", f"{month} {day} {year}"), "missing_comma_date"
    return None, None

def use_eds_abbreviation(citation, source_type):
    """Use 'ed.' or 'eds.' instead of 'edited by' or 'editor'"""
    if "edited by" in citation:
        return citation.replace("edited by", "ed."), "eds_abbreviation"
    if ", editor." in citation:
        return citation.replace(", editor.", ", ed."), "eds_abbreviation"
    return None, None

# All mutation functions
MUTATIONS = [
    use_initials,
    use_ampersand,
    remove_place,
    use_sentence_case,
    add_page_prefix,
    remove_ending_period,
    use_colon_after_author,
    remove_quotes_from_article,
    add_retrieved_from,
    missing_comma_date,
    use_eds_abbreviation,
]

def generate_invalid_variant(entry):
    """Generate one invalid variant for a valid citation"""
    citation = entry['citation']
    source_type = entry['source_type']

    # Shuffle mutations and try each
    random.shuffle(MUTATIONS)

    for mutation_func in MUTATIONS:
        result, error_type = mutation_func(citation, source_type)
        if result and result != citation:
            return {
                "citation": result,
                "ground_truth": False,
                "source_type": source_type,
                "error_type": error_type,
                "paired_with": citation
            }

    return None

def main():
    # Read valid citations
    valid_citations = []
    with open('chicago_raw_valid.jsonl', 'r') as f:
        for line in f:
            if line.strip():
                valid_citations.append(json.loads(line))

    print(f"Loaded {len(valid_citations)} valid citations")

    # Generate invalid variants
    invalid_variants = []
    for entry in valid_citations:
        variant = generate_invalid_variant(entry)
        if variant:
            invalid_variants.append(variant)

    print(f"Generated {len(invalid_variants)} invalid variants")

    # Count error types
    error_counts = {}
    for v in invalid_variants:
        error_type = v['error_type']
        error_counts[error_type] = error_counts.get(error_type, 0) + 1

    print("\nError type distribution:")
    for error_type, count in sorted(error_counts.items(), key=lambda x: -x[1]):
        print(f"  {error_type}: {count}")

    # Write output
    with open('chicago_invalid_variants.jsonl', 'w') as f:
        for v in invalid_variants:
            f.write(json.dumps(v) + '\n')

    print(f"\nWrote {len(invalid_variants)} invalid variants to chicago_invalid_variants.jsonl")

if __name__ == '__main__':
    main()
