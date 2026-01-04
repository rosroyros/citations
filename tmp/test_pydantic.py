#!/usr/bin/env python3
"""Check exact format of errors and test Pydantic validation."""

import os
import sys
sys.path.insert(0, '/Users/roy/Documents/Projects/citations/backend')

from dotenv import load_dotenv
load_dotenv('/Users/roy/Documents/Projects/citations/backend/.env')

# First get the raw provider output
from providers.gemini_provider import GeminiProvider
import asyncio

CITATION = 'Martin, Steve. "Sports-Interview Shocker." _New Yorker_, May 6, 2002, 84'

async def get_raw_result():
    provider = GeminiProvider()
    result = await provider.validate_citations(citations=CITATION, style="chicago17")
    return result["results"][0]

raw_result = asyncio.run(get_raw_result())

print("="*60)
print("RAW PROVIDER RESULT:")
print("="*60)
print(f"Keys: {raw_result.keys()}")
print(f"errors: {raw_result.get('errors')}")
print(f"error type[0] if exists: {type(raw_result.get('errors', [None])[0]) if raw_result.get('errors') else 'N/A'}")

if raw_result.get('errors'):
    for i, err in enumerate(raw_result['errors']):
        print(f"\nError {i}:")
        print(f"  Keys: {err.keys()}")
        print(f"  component: {err.get('component')}")
        print(f"  problem: {err.get('problem')}")
        print(f"  correction: {err.get('correction')!r}")  # repr to see if empty string

# Now try to pass through Pydantic
print("\n" + "="*60)
print("TESTING PYDANTIC VALIDATION:")
print("="*60)

from pydantic import BaseModel
from typing import Optional

class CitationError(BaseModel):
    component: str
    problem: str
    correction: str

class CitationResult(BaseModel):
    citation_number: int
    original: str
    source_type: str
    errors: list[CitationError]
    corrected_citation: Optional[str] = None

try:
    validated = CitationResult(**raw_result)
    print(f"Pydantic validation SUCCESS!")
    print(f"Validated errors: {validated.errors}")
except Exception as e:
    print(f"Pydantic validation FAILED: {e}")
