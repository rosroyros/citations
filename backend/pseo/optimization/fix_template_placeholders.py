"""
Fix validation-breaking placeholders in template citations.

Replaces:
- Year → 2020
- Month Date → March 15
- (n.d.) → (2020)
- Retrieved Month Date, Year → Retrieved March 15, 2020
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

    return citation


def process_dataset(input_path, output_path):
    """Process a dataset file and fix placeholders"""

    fixed_count = 0
    total_count = 0

    with open(input_path, 'r') as infile, open(output_path, 'w') as outfile:
        for line in infile:
            if line.strip():
                total_count += 1
                data = json.loads(line)
                original = data['citation']
                fixed = fix_placeholders(original)

                if fixed != original:
                    fixed_count += 1
                    data['citation'] = fixed

                outfile.write(json.dumps(data) + '\n')

    return fixed_count, total_count


def main():
    print("="*80)
    print("FIXING TEMPLATE PLACEHOLDERS")
    print("="*80)

    datasets = {
        'train_v2': 'backend/pseo/optimization/datasets/train_v2.jsonl',
        'val_v2': 'backend/pseo/optimization/datasets/val_v2.jsonl',
        'test_v2': 'backend/pseo/optimization/datasets/test_v2.jsonl'
    }

    total_fixed = 0
    total_citations = 0

    for name, path in datasets.items():
        print(f"\nProcessing {name}...")

        # Create output path
        input_path = Path(path)
        output_path = input_path.parent / f"{input_path.stem}_fixed{input_path.suffix}"

        fixed, total = process_dataset(input_path, output_path)
        total_fixed += fixed
        total_citations += total

        print(f"  Fixed: {fixed}/{total} citations")
        print(f"  Output: {output_path}")

        # Replace original with fixed version
        output_path.replace(input_path)
        print(f"  ✓ Replaced original file")

    print("\n" + "="*80)
    print(f"COMPLETE: Fixed {total_fixed} citations across {total_citations} total")
    print("="*80)

    # Show example fixes
    print("\nExample fixes:")
    print("  Year → 2020")
    print("  Month Date → March 15")
    print("  (n.d.) → (2020)")
    print("  Retrieved Month Date, Year → Retrieved March 15, 2020")


if __name__ == "__main__":
    main()
