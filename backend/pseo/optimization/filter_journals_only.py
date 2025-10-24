#!/usr/bin/env python3
"""
Filter datasets to include only journal article citations.
"""
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def filter_journals_only(input_file, output_file):
    """Filter JSONL file to only journal articles."""
    journal_count = 0
    total_count = 0

    with open(input_file) as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            total_count += 1
            data = json.loads(line)

            # Only keep journal articles
            if data.get('source_type') == 'journal article':
                f_out.write(line)
                journal_count += 1

    logger.info(f"{input_file.name}: {journal_count}/{total_count} journal articles")
    return journal_count


def main():
    datasets_dir = Path('backend/pseo/optimization/datasets')

    logger.info("="*80)
    logger.info("FILTERING DATASETS TO JOURNALS ONLY")
    logger.info("="*80)

    # Filter valid citations
    valid_in = datasets_dir / 'valid_citations_books_journals.jsonl'
    valid_out = datasets_dir / 'valid_citations_journals_only.jsonl'
    valid_count = filter_journals_only(valid_in, valid_out)
    logger.info(f"✓ Created {valid_out.name} with {valid_count} citations")

    # Filter invalid citations
    invalid_in = datasets_dir / 'invalid_citations_books_journals.jsonl'
    invalid_out = datasets_dir / 'invalid_citations_journals_only.jsonl'
    invalid_count = filter_journals_only(invalid_in, invalid_out)
    logger.info(f"✓ Created {invalid_out.name} with {invalid_count} citations")

    logger.info("="*80)
    logger.info(f"TOTAL: {valid_count + invalid_count} journal citations")
    logger.info("="*80)


if __name__ == '__main__':
    main()
