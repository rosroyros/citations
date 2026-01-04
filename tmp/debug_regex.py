#!/usr/bin/env python3
"""Debug the regex pattern to understand parsing failure."""

import re

# Actual LLM response (copy from test output)
RESPONSE = """═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

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

# Production regex (from gemini_provider.py line 333)
production_pattern = r'(?:═+\s+)?CITATION #(\d+)\s*\n\s*═+(.+?)(?=(?:═+\s+)?CITATION #\d+|$)'

# Baseline regex (from test script line 82)
baseline_pattern = r'(?:═+\s+)?CITATION #(\d+)\s*\n\s*═+(.+?)(?=(?:═+\s+)?CITATION #\d+|$)'

print("Testing production regex:")
print(f"Pattern: {production_pattern}")
print()

matches = list(re.finditer(production_pattern, RESPONSE, re.DOTALL))
print(f"Found {len(matches)} matches")

for i, match in enumerate(matches):
    print(f"\nMatch {i+1}:")
    print(f"  Citation #: {match.group(1)}")
    print(f"  Block content (first 200 chars): {match.group(2)[:200]}...")

# Let's also try a different approach - what if the format is slightly different?
print("\n" + "="*60)
print("Checking response format:")
print("="*60)

# Show the first 500 chars to see exact format
print("First 500 chars of response:")
print(repr(RESPONSE[:500]))
