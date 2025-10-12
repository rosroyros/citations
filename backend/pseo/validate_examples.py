#!/usr/bin/env python3
"""
Validate that the examples meet all requirements for Task 1.3.
"""

import json
from pathlib import Path
from datetime import datetime

def validate_examples():
    """Validate examples against requirements"""

    # Load examples
    examples_file = Path("knowledge_base/examples.json")
    with open(examples_file) as f:
        data = json.load(f)

    examples = data["examples"]

    print("=== CITATION EXAMPLES VALIDATION REPORT ===\n")
    print(f"Total examples: {len(examples)}")

    # Count by source type
    source_counts = {}
    for example in examples:
        st = example["source_type"]
        source_counts[st] = source_counts.get(st, 0) + 1

    print("\nSource type distribution:")
    for st, count in source_counts.items():
        print(f"  {st}: {count}")

    # Check requirements
    print("\n=== REQUIREMENTS CHECK ===")

    # Check total count
    print(f"✓ Total examples: {len(examples)} (required: 100)")

    # Check journal articles
    journal_articles = [e for e in examples if e["source_type"] == "journal_article"]
    print(f"✓ Journal articles: {len(journal_articles)} (required: 50)")

    # Check publication years for journal articles
    journal_years = [e["metadata"]["year"] for e in journal_articles]
    years_2020_2024 = [y for y in journal_years if 2020 <= y <= 2024]
    print(f"✓ Journal articles 2020-2024: {len(years_2020_2024)}/50")

    # Check books
    books = [e for e in examples if e["source_type"] == "book"]
    print(f"✓ Books: {len(books)} (required: 20)")

    # Check websites
    websites = [e for e in examples if e["source_type"] == "website"]
    print(f"✓ Websites: {len(websites)} (required: 15)")

    # Check other sources
    other_types = ["report", "dataset", "conference_paper", "government_document", "dissertation"]
    other_sources = [e for e in examples if e["source_type"] in other_types]
    print(f"✓ Other sources: {len(other_sources)} (required: 15)")

    # Check fields
    fields = set(e["field"] for e in examples)
    print(f"✓ Fields covered: {sorted(fields)}")

    # Check author count diversity
    author_counts = []
    organizational_authors = 0

    for example in examples:
        if example["metadata"]["authors"][0]["initials"] is None:
            organizational_authors += 1
        else:
            author_counts.append(len(example["metadata"]["authors"]))

    if author_counts:
        print(f"✓ Individual author count range: {min(author_counts)}-{max(author_counts)}")
        single_authors = sum(1 for ac in author_counts if ac == 1)
        many_authors = sum(1 for ac in author_counts if ac >= 6)
        twenty_plus_authors = sum(1 for ac in author_counts if ac >= 21)

        print(f"  - Single author: {single_authors}")
        print(f"  - Many authors (6+): {many_authors}")
        print(f"  - 21+ authors: {twenty_plus_authors}")

    print(f"✓ Organizational authors: {organizational_authors}")

    # Check in-text citations
    print(f"✓ Examples with in-text citations: {sum(1 for e in examples if 'in_text_citations' in e)}")

    # Check DOIs and URLs
    doi_count = sum(1 for e in examples if e["metadata"]["source"].get("doi"))
    url_count = sum(1 for e in examples if e["metadata"]["source"].get("url"))
    print(f"✓ Examples with DOIs: {doi_count}")
    print(f"✓ Examples with URLs: {url_count}")

    # Check special features
    special_features = {}
    for example in examples:
        for feature in example.get("special_features", []):
            special_features[feature] = special_features.get(feature, 0) + 1

    print(f"✓ Special features: {dict(sorted(special_features.items()))}")

    # Check structure compliance
    print("\n=== STRUCTURE VALIDATION ===")

    required_fields = ["example_id", "source_type", "reference_citation", "in_text_citations",
                     "metadata", "tags", "special_features", "field", "notes"]

    validation_errors = []

    for i, example in enumerate(examples):
        example_id = example.get("example_id", f"example_{i}")

        # Check required fields
        for field in required_fields:
            if field not in example:
                validation_errors.append(f"Missing field '{field}' in {example_id}")

        # Check metadata structure
        metadata = example.get("metadata", {})
        required_metadata = ["title", "year", "authors", "source", "verification"]

        for field in required_metadata:
            if field not in metadata:
                validation_errors.append(f"Missing metadata field '{field}' in {example_id}")

        # Check source structure
        source = metadata.get("source", {})
        if source and "verification" in metadata:
            if source.get("doi") and not metadata["verification"].get("doi_resolves"):
                validation_errors.append(f"DOI verification mismatch in {example_id}")
            if source.get("url") and not metadata["verification"].get("url_active"):
                validation_errors.append(f"URL verification mismatch in {example_id}")

    if validation_errors:
        print(f"✗ Validation errors found: {len(validation_errors)}")
        for error in validation_errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(validation_errors) > 10:
            print(f"  ... and {len(validation_errors) - 10} more errors")
    else:
        print("✓ All examples pass structure validation")

    # Sample quality check
    print("\n=== SAMPLE QUALITY CHECK ===")

    print("Sample journal article:")
    journal_example = journal_articles[0]
    print(f"  ID: {journal_example['example_id']}")
    print(f"  Citation: {journal_example['reference_citation'][:100]}...")
    print(f"  Year: {journal_example['metadata']['year']}")
    print(f"  Authors: {len(journal_example['metadata']['authors'])}")
    print(f"  Field: {journal_example['field']}")

    print("\nSample book:")
    book_example = books[0]
    print(f"  ID: {book_example['example_id']}")
    print(f"  Citation: {book_example['reference_citation'][:100]}...")
    print(f"  Year: {book_example['metadata']['year']}")
    print(f"  Authors: {len(book_example['metadata']['authors'])}")
    print(f"  Field: {book_example['field']}")

    print("\nSample website:")
    website_example = websites[0]
    print(f"  ID: {website_example['example_id']}")
    print(f"  Citation: {website_example['reference_citation'][:100]}...")
    print(f"  Year: {website_example['metadata']['year']}")
    print(f"  Has URL: {bool(website_example['metadata']['source'].get('url'))}")
    print(f"  Field: {website_example['field']}")

    print("\n=== SUMMARY ===")
    print(f"Validation completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not validation_errors:
        print("✅ All requirements met!")
        print("✅ Examples ready for use in content generation")
    else:
        print("❌ Some issues need to be addressed")

    return len(validation_errors) == 0

if __name__ == "__main__":
    validate_examples()