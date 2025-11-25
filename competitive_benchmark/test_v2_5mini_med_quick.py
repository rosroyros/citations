"""
Test v2 prompt with GPT-5-mini + reasoning_effort=medium (5 citations validation)
"""
import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Force unbuffered output for monitoring
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Load OpenAI API key
ENV_PATH = os.getenv('ENV_FILE_PATH', '../backend/.env')
load_dotenv(ENV_PATH)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    print("❌ No OpenAI API key found", flush=True)
    exit(1)

import openai
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Load v2 prompt from file
PROMPT_FILE = Path('../backend/prompts/validator_prompt_v2.txt')
with open(PROMPT_FILE, 'r') as f:
    V2_PROMPT = f.read()

# Ensure prompt has citation placeholder
if '{citation}' not in V2_PROMPT:
    V2_PROMPT += "\n\nCitation: {citation}"

print(f"✓ Loaded v2 prompt ({len(V2_PROMPT)} chars)", flush=True)

def load_test_citations(limit=5):
    """Load first N citations from test set."""
    citations = []
    test_file = Path('../Checker_Prompt_Optimization/test_set_121_corrected.jsonl')
    with open(test_file, 'r') as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            item = json.loads(line)
            citations.append({
                'citation': item['citation'],
                'ground_truth': item['ground_truth']
            })
    return citations

def test_model(citations, round_num=1):
    """Test with reasoning_effort=medium."""
    results = []
    output_file = Path(f'GPT-5-mini_v2_medium_round{round_num}_quick_5.jsonl')

    print(f"\n🚀 Testing: GPT-5-mini + v2 prompt + reasoning_effort=medium (Round {round_num})", flush=True)
    print(f"📋 Test set: {len(citations)} citations", flush=True)
    print(f"🌡️  Temperature: 1", flush=True)
    print(f"🧠 Reasoning: medium", flush=True)
    print(f"\n📊 Starting API calls...", flush=True)
    print(f"Format: [idx/total] truth -> pred result (running accuracy)", flush=True)
    print(f"{'─'*60}\n", flush=True)

    # Open file for writing
    with open(output_file, 'w') as outf:
        for i, item in enumerate(citations, 1):
            try:
                # Format prompt with citation
                prompt = V2_PROMPT.format(citation=item['citation'])

                # Call API with medium reasoning
                response = client.chat.completions.create(
                    model="gpt-5-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=1,
                    reasoning_effort="medium"
                )

                # Parse response - PRODUCTION LOGIC (matches openai_provider.py)
                response_text = response.choices[0].message.content.strip()

                # Check for explicit "no errors" marker (valid)
                if '✓ No APA 7 formatting errors detected' in response_text:
                    predicted = True
                # Check for error markers (invalid)
                elif '❌' in response_text:
                    predicted = False
                # Fallback: check for "no errors" text
                elif 'no apa 7 formatting errors' in response_text.lower():
                    predicted = True
                # Otherwise assume invalid
                else:
                    predicted = False

                correct = (predicted == item['ground_truth'])

                # Store result
                result = {
                    'citation': item['citation'],
                    'ground_truth': item['ground_truth'],
                    'predicted': predicted,
                    'correct': correct,
                    'raw_response': response.choices[0].message.content
                }
                results.append(result)

                # Write result immediately
                json.dump(result, outf)
                outf.write('\n')
                outf.flush()

                # Progress indicator
                correct_so_far = sum(1 for r in results if r['correct'])
                truth_str = str(item['ground_truth'])
                pred_str = str(predicted)
                print(f"  [{i:3d}/{len(citations)}] {truth_str:5s} -> {pred_str:5s} {'✓' if correct else '✗'} ({correct_so_far}/{i} = {100*correct_so_far/i:.1f}%)", flush=True)

            except Exception as e:
                print(f"  ❌ Error on citation {i}: {e}", flush=True)
                result = {
                    'citation': item['citation'],
                    'ground_truth': item['ground_truth'],
                    'predicted': None,
                    'correct': False,
                    'error': str(e)
                }
                results.append(result)
                json.dump(result, outf)
                outf.write('\n')
                outf.flush()

            # Rate limiting
            time.sleep(0.5)

    # Calculate accuracy
    correct = sum(1 for r in results if r['correct'])
    accuracy = correct / len(results)

    return results, accuracy, output_file

def main():
    print("="*70)
    print("VALIDATION TEST: V2 Prompt + GPT-5-mini + Medium Reasoning")
    print("="*70)

    # Load test data (only 5 citations)
    citations = load_test_citations(limit=5)
    print(f"\n✓ Loaded {len(citations)} test citations (validation mode)")

    # Run test
    results, accuracy, output_file = test_model(citations, round_num=1)

    print(f"\n{'='*70}")
    print(f"RESULTS: V2 + 5mini + Medium (Quick Validation)")
    print(f"{'='*70}")
    print(f"Accuracy: {accuracy:.2%} ({sum(1 for r in results if r['correct'])}/{len(results)})")
    print(f"Output: {output_file}")
    print(f"{'='*70}\n")

    print("✅ Validation test complete! If results look good, proceed with full 121-citation test.\n")

if __name__ == '__main__':
    main()
