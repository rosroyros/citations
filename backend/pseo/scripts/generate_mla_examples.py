#!/usr/bin/env python3
"""
Generate MLA 9th Edition citation examples for PSEO knowledge base.
This script creates realistic but fictional examples that follow MLA 9 format.

Key MLA 9 Format Rules:
- Full author names (not initials)
- "and" between authors (not "&")
- Title Case for all titles
- Date AFTER publisher
- "pp." for page ranges in Works Cited
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# Journal name pools by field
LITERATURE_JOURNALS = [
    "Journal of Modern Arts",
    "Contemporary Literature",
    "American Literary Review",
    "Modern Fiction Studies",
    "Studies in the Novel",
    "The Journal of Narrative Technique",
    "Comparative Literature Studies",
    "Novel: A Forum on Fiction"
]

HISTORY_JOURNALS = [
    "Historical Journal",
    "The Anthropocene Review",
    "Journal of American History",
    "Past & Present",
    "American Historical Review",
    "Journal of World History",
    "The Journal of Modern History",
    "Social History"
]

SOCIAL_SCIENCE_JOURNALS = [
    "Social Research",
    "American Journal of Sociology",
    "Journal of Contemporary Ethnography",
    "Qualitative Sociology",
    "Sociological Review",
    "Theory and Society",
    "Annual Review of Sociology"
]

# Author name pools (full names for MLA)
LAST_NAMES = [
    "Morrison", "Khan", "Garcia", "Patel", "Lee", "Chen", "Rodriguez", "Kim",
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis",
    "Martinez", "Anderson", "Taylor", "Thomas", "Jackson", "Thompson", "White",
    "Harris", "Martin", "Robinson", "Clark", "Lewis", "Walker", "Hall", "Young"
]

FIRST_NAMES = [
    "Toni", "Samira", "Maria", "Sanjay", "Michael", "Sarah", "David", "Emily",
    "James", "Jennifer", "Robert", "Patricia", "John", "Linda", "William",
    "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Karen",
    "Christopher", "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony"
]

MIDDLE_NAMES = [
    "Elena", "David", "Marie", "James", "Lynn", "Alexander", "Grace", "Lee",
    "Rose", "Michael", "Anne", "Thomas", "Elizabeth", "Joseph", "Jane"
]

# Publisher pools
PUBLISHERS = [
    "Knopf", "Penguin", "Random House", "Harper", "Simon & Schuster",
    "Macmillan", "Houghton Mifflin", "Norton", "Oxford UP", "Cambridge UP",
    "Yale UP", "Harvard UP", "Princeton UP", "MIT Press", "Routledge",
    "McGraw-Hill", "Pearson", "Wiley", "Springer", "Sage"
]

# Website names
WEBSITES = [
    "Eco Report", "Tech Insights", "Health Today", "Science Daily",
    "Digital Trends", "Nature Today", "Climate Watch", "Education Corner",
    "Healthline", "Psychology Today", "National Geographic", "Smithsonian"
]

# Months abbreviated per MLA 9
MONTHS = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."]


def generate_example_id(source_type: str, number: int) -> str:
    """Generate unique example ID for MLA examples."""
    return f"mla9_{source_type}_{number:03d}"


def generate_authors(count: int) -> List[Dict[str, str]]:
    """
    Generate random author names with FULL NAMES (MLA 9 requirement).

    Returns list of dicts with:
    - last_name
    - first_name
    - middle_name (optional)
    - full_name
    """
    authors = []
    used_combinations = set()

    for i in range(count):
        # Ensure unique combinations
        while True:
            last_name = random.choice(LAST_NAMES)
            first_name = random.choice(FIRST_NAMES)
            combo = (first_name, last_name)
            if combo not in used_combinations:
                used_combinations.add(combo)
                break

        # 50% chance of middle name
        middle_name = random.choice(MIDDLE_NAMES) if random.random() < 0.5 else ""

        authors.append({
            "last_name": last_name,
            "first_name": first_name,
            "middle_name": middle_name,
            "full_name": f"{first_name} {middle_name} {last_name}".replace("  ", " ")
        })

    return authors


def format_authors_for_mla(authors: List[Dict[str, str]]) -> str:
    """
    Format authors for MLA 9 citation.

    Rules:
    - 1 author: Last, First Middle
    - 2 authors: Last, First Middle, and First Middle Last
    - 3+ authors: Last, First Middle, et al

    Note: Does NOT include trailing period - that's added by citation formatter
    """
    if len(authors) == 1:
        author = authors[0]
        if author['middle_name']:
            return f"{author['last_name']}, {author['first_name']} {author['middle_name']}"
        return f"{author['last_name']}, {author['first_name']}"

    elif len(authors) == 2:
        # First author inverted, second normal order
        first = authors[0]
        second = authors[1]

        if first['middle_name']:
            first_formatted = f"{first['last_name']}, {first['first_name']} {first['middle_name']}"
        else:
            first_formatted = f"{first['last_name']}, {first['first_name']}"

        if second['middle_name']:
            second_formatted = f"{second['first_name']} {second['middle_name']} {second['last_name']}"
        else:
            second_formatted = f"{second['first_name']} {second['last_name']}"

        return f"{first_formatted}, and {second_formatted}"

    else:
        # 3+ authors: first author + et al.
        first = authors[0]
        if first['middle_name']:
            return f"{first['last_name']}, {first['first_name']} {first['middle_name']}, et al."
        return f"{first['last_name']}, {first['first_name']}, et al."


def generate_doi() -> str:
    """Generate realistic DOI."""
    prefix = random.choice(["10.1177", "10.1093", "10.1080", "10.1017", "10.1215", "10.1353"])
    suffix = ''.join(random.choices('0123456789', k=10))
    return f"https://doi.org/{prefix}/{suffix}"


def generate_title(title_type: str = "article") -> str:
    """
    Generate realistic title in Title Case (MLA requirement).

    Title Case rules:
    - Capitalize first and last words
    - Capitalize all major words
    - Lowercase articles, conjunctions, short prepositions (unless first/last)
    """
    subjects = [
        "Climate Change", "Digital Technology", "Social Media", "Urban Development",
        "Mental Health", "Economic Policy", "Cultural Identity", "Educational Reform",
        "Environmental Justice", "Global Trade", "Public Health", "Artificial Intelligence",
        "Historical Memory", "Literary Theory", "Narrative Techniques", "Modern Storytelling"
    ]

    verbs = [
        "Effects", "Impact", "Influence", "Analysis", "Study", "Review",
        "Exploration", "Understanding", "Perspectives", "Trends", "Challenges"
    ]

    contexts = [
        "in the Digital Age", "in Contemporary Society", "in Urban Communities",
        "in the 21st Century", "in Modern Literature", "in Global Context",
        "in Higher Education", "in Public Policy", "in American Culture"
    ]

    # Generate different title patterns
    patterns = [
        f"The {random.choice(verbs)} of {random.choice(subjects)}",
        f"{random.choice(subjects)}: {random.choice(verbs)} and {random.choice(verbs)}",
        f"{random.choice(subjects)} {random.choice(contexts)}",
        f"Toward a New Understanding of {random.choice(subjects)}",
        f"Rethinking {random.choice(subjects)} {random.choice(contexts)}"
    ]

    return random.choice(patterns)


def generate_book_example(number: int) -> Dict:
    """Generate MLA 9 book citation example."""
    author_count = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
    authors = generate_authors(author_count)
    title = generate_title("book")
    publisher = random.choice(PUBLISHERS)
    year = random.randint(1985, 2024)

    # Format: Author. Title. Publisher, Year.
    author_str = format_authors_for_mla(authors)
    # Add period after author only if it doesn't already end with one (et al.)
    author_part = author_str if author_str.endswith('.') else f"{author_str}."
    citation = f"{author_part} *{title}*. {publisher}, {year}."

    return {
        "example_id": generate_example_id("book", number),
        "source_type": "book",
        "citation": citation,
        "components": {
            "authors": format_authors_for_mla(authors),
            "title": title,
            "publisher": publisher,
            "year": year
        },
        "validation_notes": [
            "Full author names (not initials)",
            "Book title in italics and Title Case",
            "Year after publisher",
            "Ends with period"
        ]
    }


def generate_journal_article_example(number: int) -> Dict:
    """Generate MLA 9 journal article citation example."""
    author_count = random.choices([1, 2, 3, 4], weights=[40, 35, 20, 5])[0]
    authors = generate_authors(author_count)
    article_title = generate_title("article")
    journal = random.choice(LITERATURE_JOURNALS + HISTORY_JOURNALS + SOCIAL_SCIENCE_JOURNALS)
    volume = random.randint(1, 50)
    issue = random.randint(1, 4)
    year = random.randint(2015, 2024)
    start_page = random.randint(10, 200)
    end_page = start_page + random.randint(10, 50)

    # 30% chance of DOI
    has_doi = random.random() < 0.3
    doi = generate_doi() if has_doi else None

    # Format: Author. "Article Title." Journal Name, vol. #, no. #, Year, pp. ##-##.
    author_str = format_authors_for_mla(authors)
    author_part = author_str if author_str.endswith('.') else f"{author_str}."
    citation = f"{author_part} \"{article_title}.\" *{journal}*, vol. {volume}, no. {issue}, {year}, pp. {start_page}-{end_page}."

    if doi:
        citation = citation[:-1] + f" {doi}."

    return {
        "example_id": generate_example_id("journal", number),
        "source_type": "journal_article",
        "citation": citation,
        "components": {
            "authors": format_authors_for_mla(authors),
            "article_title": article_title,
            "journal_name": journal,
            "volume": volume,
            "issue": issue,
            "year": year,
            "pages": f"pp. {start_page}-{end_page}",
            "doi": doi
        },
        "validation_notes": [
            "Article title in quotation marks and Title Case",
            "Journal name in italics",
            "Lowercase 'vol.' and 'no.'",
            "pp. before page numbers",
            "DOI includes https://doi.org/" if doi else "No DOI"
        ]
    }


def generate_website_example(number: int) -> Dict:
    """Generate MLA 9 website citation example."""
    # 70% chance of author
    has_author = random.random() < 0.7
    authors = generate_authors(1) if has_author else []

    page_title = generate_title("webpage")
    website = random.choice(WEBSITES)
    day = random.randint(1, 28)
    month = random.choice(MONTHS)
    year = random.randint(2020, 2024)

    # Generate URL
    url_slug = page_title.lower().replace(" ", "-").replace(":", "").replace(",", "")[:40]
    url = f"www.{website.lower().replace(' ', '')}.org/{url_slug}"

    # 50% chance of access date
    has_access_date = random.random() < 0.5
    access_day = random.randint(1, 28)
    access_month = random.choice(MONTHS)
    access_year = random.choice([2024, 2025])

    # Format
    if has_author:
        author_str = format_authors_for_mla(authors)
        author_part = author_str if author_str.endswith('.') else f"{author_str}."
        citation = f"{author_part} \"{page_title}.\" *{website}*, {day} {month} {year}, {url}."
    else:
        citation = f"\"{page_title}.\" *{website}*, {day} {month} {year}, {url}."

    if has_access_date:
        citation = citation[:-1] + f" Accessed {access_day} {access_month} {access_year}."

    return {
        "example_id": generate_example_id("website", number),
        "source_type": "website",
        "citation": citation,
        "components": {
            "authors": format_authors_for_mla(authors) if has_author else "No author",
            "page_title": page_title,
            "website_name": website,
            "date": f"{day} {month} {year}",
            "url": url,
            "access_date": f"Accessed {access_day} {access_month} {access_year}" if has_access_date else None
        },
        "validation_notes": [
            "Page title in quotation marks and Title Case",
            "Website name in italics",
            "Date format: Day Month Year",
            "URL without https://",
            "Access date optional" if has_access_date else "No access date"
        ]
    }


def generate_book_chapter_example(number: int) -> Dict:
    """Generate MLA 9 book chapter citation example."""
    author_count = random.choices([1, 2], weights=[70, 30])[0]
    authors = generate_authors(author_count)
    chapter_title = generate_title("chapter")
    book_title = generate_title("book")

    # Editor (not inverted - normal order)
    editor = generate_authors(1)[0]
    editor_formatted = f"{editor['first_name']} {editor['last_name']}"

    publisher = random.choice(PUBLISHERS)
    year = random.randint(2000, 2024)
    start_page = random.randint(10, 200)
    end_page = start_page + random.randint(10, 40)

    # Format: Author. "Chapter Title." Book Title, edited by First Last, Publisher, Year, pp. ##-##.
    author_str = format_authors_for_mla(authors)
    author_part = author_str if author_str.endswith('.') else f"{author_str}."
    citation = f"{author_part} \"{chapter_title}.\" *{book_title}*, edited by {editor_formatted}, {publisher}, {year}, pp. {start_page}-{end_page}."

    return {
        "example_id": generate_example_id("chapter", number),
        "source_type": "book_chapter",
        "citation": citation,
        "components": {
            "authors": format_authors_for_mla(authors),
            "chapter_title": chapter_title,
            "book_title": book_title,
            "editor": editor_formatted,
            "publisher": publisher,
            "year": year,
            "pages": f"pp. {start_page}-{end_page}"
        },
        "validation_notes": [
            "Chapter title in quotation marks and Title Case",
            "Book title in italics",
            "Editor name in normal order (not inverted)",
            "pp. before page numbers"
        ]
    }


def generate_all_examples(
    books: int = 30,
    articles: int = 40,
    websites: int = 30,
    chapters: int = 20
) -> List[Dict]:
    """Generate all MLA 9 citation examples."""
    examples = []

    print("Generating MLA 9 citation examples...")

    # Generate books
    print(f"  Generating {books} book examples...")
    for i in range(books):
        examples.append(generate_book_example(i + 1))

    # Generate journal articles
    print(f"  Generating {articles} journal article examples...")
    for i in range(articles):
        examples.append(generate_journal_article_example(i + 1))

    # Generate websites
    print(f"  Generating {websites} website examples...")
    for i in range(websites):
        examples.append(generate_website_example(i + 1))

    # Generate book chapters
    print(f"  Generating {chapters} book chapter examples...")
    for i in range(chapters):
        examples.append(generate_book_chapter_example(i + 1))

    print(f"✓ Generated {len(examples)} total examples")
    return examples


def main():
    """Main execution."""
    # Generate examples
    examples = generate_all_examples(
        books=30,
        articles=40,
        websites=30,
        chapters=20
    )

    # Output path
    output_dir = Path(__file__).parent.parent / "knowledge_base" / "mla9"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "examples.json"

    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(examples, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Examples saved to: {output_file}")
    print(f"  Total examples: {len(examples)}")

    # Summary
    type_counts = {}
    for ex in examples:
        source_type = ex['source_type']
        type_counts[source_type] = type_counts.get(source_type, 0) + 1

    print("\nBreakdown by type:")
    for source_type, count in sorted(type_counts.items()):
        print(f"  {source_type}: {count}")


if __name__ == "__main__":
    main()
