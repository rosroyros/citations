#!/usr/bin/env python3
"""Final debugging test - trace the entire flow."""

import os
import sys
sys.path.insert(0, '/Users/roy/Documents/Projects/citations/backend')

from dotenv import load_dotenv
load_dotenv('/Users/roy/Documents/Projects/citations/backend/.env')

from providers.gemini_provider import GeminiProvider
import asyncio

# Test citation
CITATION = 'Martin, Steve. "Sports-Interview Shocker." _New Yorker_, May 6, 2002, 84'

async def main():
    print("="*60)
    print("TESTING REAL PROVIDER END-TO-END")
    print("="*60)
    
    # Create provider
    provider = GeminiProvider()
    print(f"Provider created: {type(provider)}")
    print(f"Model: {provider.model}")
    
    # Call validate_citations exactly like app.py does
    result = await provider.validate_citations(
        citations=CITATION,
        style="chicago17"
    )
    
    print("\n" + "="*60)
    print("RESULT FROM provider.validate_citations():")
    print("="*60)
    print(f"Result type: {type(result)}")
    print(f"Result keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
    
    # Extract results like app.py does
    results = result.get("results", [])
    print(f"\nNumber of citation results: {len(results)}")
    
    for i, r in enumerate(results):
        print(f"\n--- Citation {i+1} ---")
        print(f"  citation_number: {r.get('citation_number')}")
        print(f"  source_type: {r.get('source_type')}")
        print(f"  errors count: {len(r.get('errors', []))}")
        print(f"  errors: {r.get('errors')}")
        print(f"  corrected_citation: {r.get('corrected_citation', '')[:80] if r.get('corrected_citation') else 'None'}...")

asyncio.run(main())
