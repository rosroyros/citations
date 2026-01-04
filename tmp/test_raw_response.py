#!/usr/bin/env python3
"""Test raw Gemini response for Chicago validation."""

import os
import sys
sys.path.insert(0, '/Users/roy/Documents/Projects/citations/backend')

from dotenv import load_dotenv
load_dotenv('/Users/roy/Documents/Projects/citations/backend/.env')

from prompt_manager import PromptManager
from google import genai
from google.genai import types

# Test citation - INVALID (missing period at end)
CITATION = 'Martin, Steve. "Sports-Interview Shocker." _New Yorker_, May 6, 2002, 84'

# Get API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY not found")
    sys.exit(1)

# Load Chicago prompt
pm = PromptManager()
prompt = pm.load_prompt("chicago17")
print(f"Loaded prompt: {len(prompt)} characters")
print(f"Prompt starts with: {prompt[:200]}...")
print()

# Format citations
formatted = f"CITATIONS TO VALIDATE:\n\n1. {CITATION}"
full_prompt = f"{prompt}\n\n{formatted}"

print(f"Full prompt: {len(full_prompt)} characters")
print("=" * 60)
print("Calling Gemini API...")

# Call Gemini directly
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

print("=" * 60)
print("RAW LLM RESPONSE:")
print("=" * 60)
print(response.text)
print("=" * 60)

# Check for error indicators
has_errors = "❌" in response.text
has_success = "✓" in response.text or "No Chicago 17 formatting errors" in response.text

print(f"\nHas error markers (❌): {has_errors}")
print(f"Has success markers (✓): {has_success}")
