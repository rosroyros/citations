#!/usr/bin/env python3
"""
Fix placeholders in clean citation datasets.
Adapted from fix_template_placeholders.py for our clean datasets.
"""
import json
import re
from pathlib import Path


def fix_placeholders(citation):
    """Replace validation-breaking placeholders with realistic values"""

    # Fix "Retrieved Month Date, Year" first (before other replacements)
    citation = re.sub(
        r'Retrieved Month Date, Year',
        'Retrieved March 15, 2020',
        citation
    )

    # Fix (n.d.) - no date
    citation = re.sub(r'\(n\.d\.\)', '(2020)', citation)

    # Fix "Year, Month Date" (date-specific)
    citation = re.sub(
        r'\(Year, Month Date\)',
        '(2020, March 15)',
        citation
    )

    # Fix standalone "Year of publication"
    citation = re.sub(
        r'\(Year of publication\)',
        '(2020)',
        citation
    )

    # Fix standalone "Year"
    citation = re.sub(r'\(Year\)', '(2020)', citation)

    # Fix "Month Date" if still present
    citation = re.sub(r'Month Date', 'March 15', citation)

    # Fix "Lastname, F. M." (author placeholder)
    citation = re.sub(r'Lastname, F\. M\.', 'Smith, J. A.', citation)

    # Fix "Title of post" or "Title of Post"
    citation = re.sub(r'Title of [Pp]ost', 'How to cite sources', citation)

    return citation


def process_file(input_path, output_path):
    """Process a file and fix placeholders"""

    fixed_count = 0
    total_count = 0

    with open(input_path, 'r') as infile, open(output_path, 'w') as outfile:
        for line in infile:
            if line.strip():
                total_count += 1
                data = json.loads(line)
                original = data['citation_text']
                fixed = fix_placeholders(original)

                if fixed != original:
                    fixed_count += 1
                    data['citation_text'] = fixed

                outfile.write(json.dumps(data, ensure_ascii=False) + '\n')

    return fixed_count, total_count


def main():
    print("="*80)
    print("FIXING PLACEHOLDERS IN CLEAN DATASETS")
    print("="*80)

    # Fix valid citations
    print("\n1. Processing valid citations...")
    valid_input = Path('backend/pseo/optimization/datasets/valid_citations_clean_final.jsonl')
    valid_output = Path('backend/pseo/optimization/datasets/valid_citations_clean_final_fixed.jsonl')

    fixed, total = process_file(valid_input, valid_output)
    print(f"   Fixed: {fixed}/{total} citations")
    print(f"   Output: {valid_output}")

    # Replace original
    valid_output.replace(valid_input)
    print(f"   ✓ Replaced original file")

    # Fix invalid citations
    print("\n2. Processing invalid citations...")
    invalid_input = Path('backend/pseo/optimization/datasets/invalid_citations_standardized.jsonl')
    invalid_output = Path('backend/pseo/optimization/datasets/invalid_citations_standardized_fixed.jsonl')

    fixed_inv, total_inv = process_file(invalid_input, invalid_output)
    print(f"   Fixed: {fixed_inv}/{total_inv} citations")
    print(f"   Output: {invalid_output}")

    # Replace original
    invalid_output.replace(invalid_input)
    print(f"   ✓ Replaced original file")

    print("\n" + "="*80)
    print(f"COMPLETE: Fixed {fixed + fixed_inv} placeholders across {total + total_inv} total citations")
    print("="*80)

    print("\nPlaceholder replacements:")
    print("  (Year) → (2020)")
    print("  Month Date → March 15")
    print("  (n.d.) → (2020)")
    print("  Retrieved Month Date, Year → Retrieved March 15, 2020")
    print("  Lastname, F. M. → Smith, J. A.")
    print("  Title of post → How to cite sources")


if __name__ == "__main__":
    main()
