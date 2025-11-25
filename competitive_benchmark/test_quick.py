"""Quick test with 2 citations"""
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

print("Starting quick test...", flush=True)

load_dotenv('../backend/.env')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    print("❌ No API key", flush=True)
    exit(1)

print(f"✅ API key found (length: {len(OPENAI_API_KEY)})", flush=True)

import openai
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Load prompt
PROMPT_FILE = Path('../backend/prompts/validator_prompt_optimized.txt')
with open(PROMPT_FILE, 'r') as f:
    OPTIMIZED_PROMPT = f.read()
if '{citation}' not in OPTIMIZED_PROMPT:
    OPTIMIZED_PROMPT += "\n\nCitation: {citation}"

print(f"✅ Loaded prompt ({len(OPTIMIZED_PROMPT)} chars)", flush=True)

# Load just 2 test citations
test_file = Path('../Checker_Prompt_Optimization/test_set_121_corrected.jsonl')
citations = []
with open(test_file, 'r') as f:
    for i, line in enumerate(f):
        if i >= 2:
            break
        citations.append(json.loads(line))

print(f"✅ Loaded {len(citations)} test citations", flush=True)

# Test with first citation
print(f"\nTesting citation 1...", flush=True)
prompt = OPTIMIZED_PROMPT.format(citation=citations[0]['citation'])
print(f"Making API call to gpt-5-mini with reasoning_effort=high...", flush=True)

try:
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=1,
        reasoning_effort="high"
    )
    print(f"✅ Got response: {response.choices[0].message.content[:100]}...", flush=True)
except Exception as e:
    print(f"❌ Error: {e}", flush=True)
    
print("\nTest complete!", flush=True)
