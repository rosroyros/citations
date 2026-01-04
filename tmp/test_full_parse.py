#!/usr/bin/env python3
"""Test full end-to-end parsing from actual Gemini response."""

import os
import sys
sys.path.insert(0, '/Users/roy/Documents/Projects/citations/backend')

from dotenv import load_dotenv
load_dotenv('/Users/roy/Documents/Projects/citations/backend/.env')

from prompt_manager import PromptManager
from providers.gemini_provider import GeminiProvider
from google import genai
from google.genai import types

# Test citation
CITATION = 'Martin, Steve. "Sports-Interview Shocker." _New Yorker_, May 6, 2002, 84'

# Get raw response
api_key = os.getenv("GEMINI_API_KEY")
pm = PromptManager()
prompt = pm.load_prompt("chicago17")

formatted = f"CITATIONS TO VALIDATE:\n\n1. {CITATION}"
full_prompt = f"{prompt}\n\n{formatted}"

client = genai.Client(api_key=api_key)
config = types.GenerateContentConfig(
    temperature=0.0,
    max_output_tokens=10000,
    thinking_config=types.ThinkingConfig(thinking_budget=1024)
)

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=full_prompt,
    config=config
)

response_text = response.text

print("="*60)
print("RAW RESPONSE (first 1000 chars):")
print("="*60)
print(response_text[:1000])

print("\n" + "="*60)
print("NOW TESTING PRODUCTION PARSER:")
print("="*60)

# Create provider and test parser
provider = GeminiProvider()
parsed = provider._parse_response(response_text, "chicago17")

print(f"\nParsed {len(parsed)} citation(s)")

for p in parsed:
    print(f"\nCitation #{p.get('citation_number')}:")
    print(f"  Source type: {p.get('source_type')}")
    print(f"  Error count: {len(p.get('errors', []))}")
    print(f"  Errors: {p.get('errors')}")
