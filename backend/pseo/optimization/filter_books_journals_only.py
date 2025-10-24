#!/usr/bin/env python3
"""
Filter datasets to include only book and journal article citations.
Creates new datasets for optimization runs focused on these source types.
"""
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def filter_dataset(input_file: Path, output_file: Path, allowed_types: set):
    """Filter citations to only include specific source types."""
    filtered = []
    total = 0

    with open(input_file) as f:
        for line in f:
            total += 1
            citation = json.loads(line)
            source_type = citation.get('source_type', '').lower()

            # Check if source type matches any allowed type
            if any(allowed in source_type for allowed in allowed_types):
                filtered.append(citation)

    logger.info(f"Filtered {input_file.name}: {len(filtered)}/{total} citations kept")

    # Write filtered citations
    with open(output_file, 'w') as f:
        for citation in filtered:
            f.write(json.dumps(citation) + '\n')

    return len(filtered), total


def main():
    datasets_dir = Path('backend/pseo/optimization/datasets')

    # Source types to include
    allowed_types = {'book', 'journal'}

    logger.info("Filtering datasets to include only books and journals...")
    logger.info(f"Allowed source types: {allowed_types}")

    # Filter valid citations
    valid_in = datasets_dir / 'valid_citations_clean_final.jsonl'
    valid_out = datasets_dir / 'valid_citations_books_journals.jsonl'
    valid_kept, valid_total = filter_dataset(valid_in, valid_out, allowed_types)

    # Filter invalid citations
    invalid_in = datasets_dir / 'invalid_citations_standardized.jsonl'
    invalid_out = datasets_dir / 'invalid_citations_books_journals.jsonl'
    invalid_kept, invalid_total = filter_dataset(invalid_in, invalid_out, allowed_types)

    logger.info("\n=== Summary ===")
    logger.info(f"Valid citations: {valid_kept}/{valid_total} ({valid_kept/valid_total*100:.1f}%)")
    logger.info(f"Invalid citations: {invalid_kept}/{invalid_total} ({invalid_kept/invalid_total*100:.1f}%)")
    logger.info(f"Total citations: {valid_kept + invalid_kept}/{valid_total + invalid_total}")

    logger.info(f"\n✅ Filtered datasets created:")
    logger.info(f"  - {valid_out}")
    logger.info(f"  - {invalid_out}")

    # Show breakdown by source type
    logger.info("\n=== Source Type Breakdown ===")
    source_types = {}

    for output_file in [valid_out, invalid_out]:
        with open(output_file) as f:
            for line in f:
                citation = json.loads(line)
                source_type = citation.get('source_type', 'unknown')
                source_types[source_type] = source_types.get(source_type, 0) + 1

    for source_type, count in sorted(source_types.items()):
        logger.info(f"  {source_type}: {count}")


if __name__ == '__main__':
    main()
