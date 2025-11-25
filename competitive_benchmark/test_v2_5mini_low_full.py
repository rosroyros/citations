"""
Test v2 prompt with GPT-5-mini + reasoning_effort=low (121 citations, 3 rounds)
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

def load_test_citations():
    """Load all 121 citations from test set."""
    citations = []
    test_file = Path('../Checker_Prompt_Optimization/test_set_121_corrected.jsonl')
    with open(test_file, 'r') as f:
        for line in f:
            item = json.loads(line)
            citations.append({
                'citation': item['citation'],
                'ground_truth': item['ground_truth']
            })
    return citations

def test_round(citations, round_num):
    """Test one round with reasoning_effort=low."""
    results = []
    output_file = Path(f'GPT-5-mini_v2_low_round{round_num}_detailed_121.jsonl')

    # Check for existing progress
    start_idx = 0
    if output_file.exists():
        with open(output_file, 'r') as f:
            for line in f:
                results.append(json.loads(line))
        start_idx = len(results)
        print(f"\n📂 Found existing progress: {start_idx} citations complete", flush=True)
        print(f"   Resuming from citation {start_idx + 1}...\n", flush=True)

    print(f"\n🚀 Testing: GPT-5-mini + v2 prompt + reasoning_effort=low (Round {round_num})", flush=True)
    print(f"📋 Test set: {len(citations)} citations (processing {len(citations) - start_idx})", flush=True)
    print(f"🌡️  Temperature: 1", flush=True)
    print(f"🧠 Reasoning: low", flush=True)
    print(f"⏱️  Estimated time: ~{(len(citations) - start_idx) * 1} minutes (~1 min/citation)", flush=True)
    print(f"💰 Estimated cost: ~${(len(citations) - start_idx) * 0.01:.2f}", flush=True)
    print(f"\n📊 Starting API calls...", flush=True)
    print(f"Format: [idx/total] truth -> pred result (running accuracy)", flush=True)
    print(f"{'─'*60}\n", flush=True)

    # Open file in append mode for incremental writes
    with open(output_file, 'a') as outf:
        for i, item in enumerate(citations, 1):
            if i <= start_idx:
                continue  # Skip already processed

            try:
                # Format prompt with citation
                prompt = V2_PROMPT.format(citation=item['citation'])

                # Call API with low reasoning
                response = client.chat.completions.create(
                    model="gpt-5-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=1,
                    reasoning_effort="low"
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
    print("FULL TEST: V2 Prompt + GPT-5-mini + Low Reasoning (3 Rounds)")
    print("="*70)

    # Load test data
    citations = load_test_citations()
    print(f"\n✓ Loaded {len(citations)} test citations")

    all_results = {}

    # Run 3 rounds
    for round_num in range(1, 4):
        print(f"\n{'='*70}")
        print(f"ROUND {round_num}/3")
        print(f"{'='*70}")

        results, accuracy, output_file = test_round(citations, round_num)

        print(f"\n{'─'*70}")
        print(f"ROUND {round_num} RESULTS: V2 + 5mini + Low")
        print(f"{'─'*70}")
        print(f"Accuracy: {accuracy:.2%} ({sum(1 for r in results if r['correct'])}/{len(results)})")
        print(f"Output: {output_file}")
        print(f"{'─'*70}\n")

        all_results[f'round{round_num}'] = {
            'accuracy': accuracy,
            'correct': sum(1 for r in results if r['correct']),
            'errors': sum(1 for r in results if not r['correct']),
            'output_file': str(output_file)
        }

    # Calculate consistency metrics
    accuracies = [all_results[f'round{i}']['accuracy'] for i in range(1, 4)]
    avg_accuracy = sum(accuracies) / len(accuracies)
    std_dev = (sum((acc - avg_accuracy) ** 2 for acc in accuracies) / len(accuracies)) ** 0.5

    print(f"\n{'='*70}")
    print(f"FINAL SUMMARY: V2 + 5mini + Low (3 Rounds)")
    print(f"{'='*70}")
    for i in range(1, 4):
        print(f"Round {i}: {all_results[f'round{i}']['accuracy']:.2%} ({all_results[f'round{i}']['correct']}/{len(citations)})")
    print(f"{'─'*70}")
    print(f"Average:  {avg_accuracy:.2%}")
    print(f"Std Dev:  {std_dev:.2%}")
    print(f"{'='*70}\n")

    # Save summary
    summary = {
        'model': 'GPT-5-mini',
        'prompt': 'v2',
        'reasoning_effort': 'low',
        'temperature': 1,
        'test_set': '../Checker_Prompt_Optimization/test_set_121_corrected.jsonl',
        'test_set_size': len(citations),
        'rounds': all_results,
        'avg_accuracy': avg_accuracy,
        'std_dev': std_dev
    }

    summary_file = Path('v2_5mini_low_summary.json')
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"✓ Summary saved: {summary_file}\n")

if __name__ == '__main__':
    main()
