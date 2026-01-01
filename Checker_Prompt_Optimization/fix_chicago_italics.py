#!/usr/bin/env python3
"""
Add underscore markers for italics to Chicago citations.

Chicago 17th Edition italics rules:
- Book titles: italicized (standalone works)
- Journal/magazine/newspaper names: italicized
- Film/video titles: italicized (feature-length works)
- Website names (as containers): italicized

NOT italicized (use quotes):
- Article titles
- Chapter titles
- Short video titles
- Blog post titles
"""

import json
import re

def add_book_italics(citation):
    """Add italics to book titles.

    Pattern: Author. Title. [Translated/Edited by X.] Place: Publisher, Year.
    """
    # Skip if already has italics
    if '_' in citation:
        return citation

    # Skip if starts with quote (article/chapter)
    parts = citation.split('. ')
    if len(parts) < 2:
        return citation

    # Find the title - it's after author(s) and before publication info
    # Author patterns: "Last, First." or "Last, First, and First Last."

    result = citation

    # Pattern 1: Single word author (like "Homer" or "Herodotus" or "Augustine")
    match = re.match(r'^([A-Z][a-z]+)\. ([^.]+?)\. (Translated|Edited|Read|[A-Z][a-z]+, [A-Z]{2}:|[A-Z][a-z]+:|\d)', result)
    if match:
        author, title, rest_start = match.groups()
        if not title.startswith('"'):
            result = f'{author}. _{title}_. {rest_start}' + result[match.end():]
            return result

    # Pattern 2: Standard "Last, First." author
    match = re.match(r'^([A-Z][^.]+)\. ([^.]+?)\. (Translated|Edited|Read|Vol\.|[A-Z][a-z]+, [A-Z]{2}:|[A-Z][a-z]+:|\d|Open Road|Kindle|ProQuest|https)', result)
    if match:
        author, title, rest_start = match.groups()
        if not title.startswith('"') and not title.startswith('_'):
            result = f'{author}. _{title}_. {rest_start}' + result[match.end():]
            return result

    # Pattern 3: "Last, First." followed by title and place
    # More permissive - find title between first period and place:publisher
    match = re.match(r'^([^.]+\.) ([^.]+)\. ([A-Z][a-z]+(?:, [A-Z]{2})?:)', result)
    if match:
        author, title, place = match.groups()
        if not title.startswith('"') and not title.startswith('_'):
            result = f'{author} _{title}_. {place}' + result[match.end():]
            return result

    return citation


def add_journal_italics(citation):
    """Add italics to journal names.

    Pattern: Author. "Article Title." Journal Name vol, no. (year): pages.
    """
    if '_' in citation:
        return citation

    # Journal name is between closing quote+period and volume number
    # Example: "Article." Journal Name 58, no. 4 (2007): 585-625.
    match = re.search(r'"\s+([A-Z][^"]+?)\s+(\d+),?\s*no\.', citation)
    if match:
        journal = match.group(1).strip()
        return citation.replace(f'" {journal} ', f'" _{journal}_ ')

    # Alternative: Journal Name vol (year)
    match = re.search(r'"\s+([A-Z][^"]+?)\s+(\d+)\s*\(', citation)
    if match:
        journal = match.group(1).strip()
        return citation.replace(f'" {journal} ', f'" _{journal}_ ')

    return citation


def add_newspaper_magazine_italics(citation):
    """Add italics to newspaper/magazine names.

    Pattern: Author. "Headline." Publication Name, Date.
    """
    if '_' in citation:
        return citation

    # Publication name is between closing quote and date
    # Date patterns: Month Day, Year or Month Year
    months = r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)'

    match = re.search(rf'"\s+([A-Z][^,]+?),\s+{months}', citation)
    if match:
        pub = match.group(1).strip()
        if not pub.startswith('_'):
            return citation.replace(f'" {pub},', f'" _{pub}_,')

    return citation


def add_film_italics(citation):
    """Add italics to film titles.

    Pattern: Director, dir. Film Title. Year; Place: Distributor, Year. Format.
    """
    if '_' in citation:
        return citation

    # Film title after "dir. " and before year or place
    match = re.match(r'^([^.]+, dir\.)\s+([^.]+)\.\s+(\d{4}|[A-Z])', citation)
    if match:
        before, title, after = match.groups()
        return f'{before} _{title}_. {after}' + citation[match.end():]

    return citation


def add_italics_to_citation(citation, source_type):
    """Add underscore markers for italics based on source type."""

    if source_type in ['book', 'audiobook']:
        return add_book_italics(citation)

    elif source_type == 'book_chapter':
        # Book title in "In Book Title," should be italicized
        match = re.search(r'In ([^,]+), edited by', citation)
        if match:
            book_title = match.group(1)
            if not book_title.startswith('_'):
                return citation.replace(f'In {book_title},', f'In _{book_title}_,')
        return citation

    elif source_type == 'journal':
        return add_journal_italics(citation)

    elif source_type in ['newspaper', 'magazine']:
        return add_newspaper_magazine_italics(citation)

    elif source_type == 'film':
        return add_film_italics(citation)

    # For other types (website, video, thesis, etc.), typically no italics needed
    # or they use quotes instead
    return citation


def process_citations():
    """Process all citation files and add italics."""

    # Read raw valid citations
    citations = []
    with open('chicago_raw_valid.jsonl', 'r') as f:
        for line in f:
            if line.strip():
                citations.append(json.loads(line))

    print(f"Processing {len(citations)} valid citations")

    # Track changes
    changed = 0
    unchanged = 0
    by_type = {}

    for entry in citations:
        source_type = entry.get('source_type', 'unknown')
        original = entry['citation']
        entry['citation'] = add_italics_to_citation(original, source_type)

        if entry['citation'] != original:
            changed += 1
            by_type[source_type] = by_type.get(source_type, 0) + 1
            # Print sample
            if by_type[source_type] <= 2:
                print(f"\n[{source_type}] BEFORE: {original[:80]}...")
                print(f"[{source_type}] AFTER:  {entry['citation'][:80]}...")
        else:
            unchanged += 1

    print(f"\nChanged: {changed}, Unchanged: {unchanged}")
    print(f"By type: {by_type}")

    # Write updated valid citations
    with open('chicago_raw_valid.jsonl', 'w') as f:
        for entry in citations:
            f.write(json.dumps(entry) + '\n')

    print(f"\nUpdated chicago_raw_valid.jsonl")


if __name__ == '__main__':
    process_citations()
