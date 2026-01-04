#!/usr/bin/env python3
"""Debug _parse_citation_block from gemini_provider.py"""

import re
import sys
sys.path.insert(0, '/Users/roy/Documents/Projects/citations/backend')

from styles import get_style_config

# Extracted block content (what comes AFTER "CITATION #1\n═══...")
BLOCK_CONTENT = """

ORIGINAL:
1. Martin, Steve. "Sports-Interview Shocker." _New Yorker_, May 6, 2002, 84

SOURCE TYPE: newspaper/magazine

VALIDATION RESULTS:

❌ List Marker: The citation includes a leading list number ("1.").
   Should be: [Omit the number for a bibliography entry]

❌ Punctuation: Elements are separated by commas rather than periods, and it lacks a final period.
   Should be: Martin, Steve. "Sports-Interview Shocker." _New Yorker_, May 6, 2002. (Note: Page numbers are typically omitted for magazine/newspaper articles in the bibliography unless they are specific departments).

❌ Final Period: The entry does not end with a period.
   Should be: Every bibliography entry must end with a period.

───────────────────────────────────────────────────────────────────────────

CORRECTED CITATION:
Martin, Steve. "Sports-Interview Shocker." _New Yorker_, May 6, 2002.

───────────────────────────────────────────────────────────────────────────
"""

def parse_citation_block(citation_num: int, block: str, style: str = "chicago17"):
    """Exact copy of _parse_citation_block from gemini_provider.py"""
    lines = block.strip().split('\n')

    result = {
        "citation_number": citation_num,
        "original": "",
        "source_type": "",
        "errors": []
    }

    current_section = None
    original_lines = []

    for line_num, line in enumerate(lines):
        line_stripped = line.strip()
        print(f"Line {line_num}: section={current_section}, content={line_stripped[:60]}...")

        # Track sections
        if line_stripped.startswith('ORIGINAL:'):
            current_section = 'original'
            content = line_stripped.replace('ORIGINAL:', '').strip()
            if content:
                original_lines.append(content)
        elif line_stripped.startswith('SOURCE TYPE:'):
            current_section = 'source_type'
            source_type = line_stripped.replace('SOURCE TYPE:', '').strip()
            result["source_type"] = source_type
        elif line_stripped.startswith('VALIDATION RESULTS:'):
            current_section = 'validation'
            print(f"  -> ENTERED VALIDATION SECTION")
        # Parse content based on section
        elif current_section == 'original' and line_stripped and not line_stripped.startswith('SOURCE TYPE:'):
            original_lines.append(line_stripped)
        elif current_section == 'corrected_citation' and line_stripped:
            if line_stripped.startswith('─'):
                current_section = None
                continue
            if result.get("corrected_citation") is None:
                result["corrected_citation"] = line_stripped
            else:
                result["corrected_citation"] += " " + line_stripped
        elif current_section == 'validation':
            # Check for no errors using style-specific success message
            success_msg = get_style_config(style)["success_message"]
            print(f"  -> Checking for success: '{success_msg}' in '{line_stripped[:50]}'")
            if f'✓ {success_msg}' in line_stripped or success_msg in line_stripped:
                result["errors"] = []
                print(f"  -> FOUND SUCCESS MESSAGE!")
            # Parse error lines
            elif line_stripped.startswith('❌'):
                print(f"  -> FOUND ERROR LINE: {line_stripped[:60]}...")
                # Format: ❌ [Component]: [Problem]
                error_match = re.match(r'❌\s*([^:]+):\s*(.+)', line_stripped)
                if error_match:
                    error = {
                        "component": error_match.group(1).strip(),
                        "problem": error_match.group(2).strip(),
                        "correction": ""
                    }
                    result["errors"].append(error)
                    print(f"  -> ADDED ERROR: {error['component']}: {error['problem'][:40]}...")
            # Parse correction lines
            elif 'Should be:' in line_stripped and result["errors"]:
                correction = line_stripped.split('Should be:')[1].strip()
                result["errors"][-1]["correction"] = correction
        
        # Check for CORRECTED CITATION section start
        if line_stripped.startswith('CORRECTED CITATION:'):
            current_section = 'corrected_citation'
            content = line_stripped.replace('CORRECTED CITATION:', '').strip()
            if content:
                result["corrected_citation"] = content

    # Join original lines
    if original_lines:
        result["original"] = ' '.join(original_lines)

    return result


print("="*60)
print("PARSING BLOCK CONTENT:")
print("="*60)

result = parse_citation_block(1, BLOCK_CONTENT, "chicago17")

print("\n" + "="*60)
print("FINAL RESULT:")
print("="*60)
print(f"errors: {result['errors']}")
print(f"error count: {len(result['errors'])}")
print(f"original: {result.get('original', '')[:80]}...")
print(f"source_type: {result.get('source_type', '')}")
