#!/usr/bin/env python3
"""
Standardize component names in invalid citations dataset.

Maps all variations to canonical lowercase names.
"""
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Canonical component names (lowercase)
COMPONENT_MAPPING = {
    # Authors variations
    'authors': 'authors',
    'author': 'authors',

    # Title variations
    'title': 'title',
    'article title': 'title',
    'chapter title': 'title',

    # Journal variations
    'journal': 'journal',
    'journal title': 'journal',
    'periodical title': 'journal',
    'periodical': 'journal',

    # DOI variations
    'doi': 'doi',
    'url': 'doi',

    # Publisher variations
    'publisher': 'publisher',
    'publisher location': 'publisher',

    # Date variations
    'date': 'date',
    'year': 'date',
    'publication date': 'date',

    # Volume variations
    'volume': 'volume',
    'volume number': 'volume',

    # Issue variations
    'issue': 'issue',
    'issue number': 'issue',

    # Pages variations
    'pages': 'pages',
    'page numbers': 'pages',

    # Format variations (spacing, punctuation, capitalization)
    'format': 'format',
    'formatting': 'format',
    'spacing': 'format',
    'punctuation': 'format',
    'capitalization': 'format',
}


def standardize_component(component: str) -> str:
    """Map component name to canonical form."""
    normalized = component.lower().strip()
    return COMPONENT_MAPPING.get(normalized, normalized)


def standardize_dataset(input_file: Path, output_file: Path):
    """Standardize component names in dataset."""
    logger.info(f"Reading from: {input_file}")

    standardized_citations = []
    component_changes = {}

    with open(input_file) as f:
        for line in f:
            data = json.loads(line.strip())

            # Standardize error components
            if 'errors' in data and data['errors']:
                for error in data['errors']:
                    original = error['component']
                    standardized = standardize_component(original)

                    # Track changes
                    if original != standardized:
                        component_changes[original] = component_changes.get(original, 0) + 1

                    error['component'] = standardized

            standardized_citations.append(data)

    # Write standardized dataset
    logger.info(f"Writing to: {output_file}")
    with open(output_file, 'w') as f:
        for citation in standardized_citations:
            f.write(json.dumps(citation) + '\n')

    logger.info(f"Processed {len(standardized_citations)} citations")

    if component_changes:
        logger.info("\nComponent name changes:")
        for original, count in sorted(component_changes.items(), key=lambda x: -x[1]):
            standardized = standardize_component(original)
            logger.info(f"  '{original}' → '{standardized}': {count} occurrences")
    else:
        logger.info("No component names needed standardization")


def main():
    # Standardize invalid citations
    invalid_file = Path('backend/pseo/optimization/datasets/invalid_citations_enhanced.jsonl')
    output_file = Path('backend/pseo/optimization/datasets/invalid_citations_standardized.jsonl')

    if not invalid_file.exists():
        logger.error(f"Input file not found: {invalid_file}")
        return

    standardize_dataset(invalid_file, output_file)

    logger.info(f"\n✓ Standardization complete!")
    logger.info(f"Original: {invalid_file}")
    logger.info(f"Standardized: {output_file}")


if __name__ == '__main__':
    main()
