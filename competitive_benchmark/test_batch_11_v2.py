"""
Test v2 prompt with GPT-4o-mini using batch processing (11x11 batches, 3 rounds)
Currently configured for 2x2 testing
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

# TEST CONFIGURATION - Change for full run
TEST_MODE = False  # Set to False for full 11x11x3 run
TEST_BATCHES = 2  # Number of batches to test
TEST_CITATIONS_PER_BATCH = 2  # Citations per batch for testing

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

def test_round(citations, round_num, batch_size=11):
    """Test one round with batch processing."""
    results = []

    # Determine output filename based on test mode
    if TEST_MODE:
        output_file = Path(f'GPT-4o-mini_v2_batch{TEST_BATCHES}x{TEST_CITATIONS_PER_BATCH}_round{round_num}_test.jsonl')
        citations_to_test = citations[:TEST_BATCHES * TEST_CITATIONS_PER_BATCH]
        actual_batch_size = TEST_CITATIONS_PER_BATCH
        num_batches = TEST_BATCHES
    else:
        output_file = Path(f'GPT-4o-mini_v2_batch11_round{round_num}_detailed_121.jsonl')
        citations_to_test = citations
        actual_batch_size = batch_size
        num_batches = (len(citations) + batch_size - 1) // batch_size

    # Check for existing progress
    start_idx = 0
    if output_file.exists():
        with open(output_file, 'r') as f:
            for line in f:
                results.append(json.loads(line))
        start_idx = len(results)
        print(f"\n📂 Found existing progress: {start_idx} citations complete", flush=True)
        print(f"   Resuming from citation {start_idx + 1}...\n", flush=True)

    # Create batches
    batches = [citations_to_test[i:i+actual_batch_size] for i in range(0, len(citations_to_test), actual_batch_size)]

    mode_str = "TEST MODE" if TEST_MODE else "FULL MODE"
    print(f"\n🚀 Testing: GPT-4o-mini + v2 prompt (Round {round_num}) - {mode_str}", flush=True)
    print(f"📦 Batch size: {actual_batch_size} citations ({num_batches} batches total)", flush=True)
    print(f"📋 Test set: {len(citations_to_test)} citations (processing {len(citations_to_test) - start_idx})", flush=True)
    print(f"🌡️  Temperature: 0", flush=True)
    print(f"🧠 Reasoning: N/A (not supported)", flush=True)
    print(f"⏱️  Estimated time: ~{(len(citations_to_test) - start_idx) * 0.1} minutes (~6 sec/citation)", flush=True)
    print(f"💰 Estimated cost: ~${(len(citations_to_test) - start_idx) * 0.001:.2f}", flush=True)
    print(f"\n📊 Starting batch processing...", flush=True)
    print(f"{'─'*60}\n", flush=True)

    # Open file in append mode for incremental writes
    with open(output_file, 'a') as outf:
        for batch_idx, batch in enumerate(batches):
            if start_idx > 0 and (batch_idx * actual_batch_size) < start_idx:
                continue  # Skip already processed batches

            print(f"📦 Batch {batch_idx + 1}/{len(batches)}...", flush=True)

            batch_correct = 0
            batch_total = 0

            for citation_idx, item in enumerate(batch):
                global_idx = batch_idx * actual_batch_size + citation_idx + 1
                if global_idx <= start_idx:
                    continue  # Skip already processed citations

                try:
                    # Format prompt with citation
                    prompt = V2_PROMPT.format(citation=item['citation'])

                    # Call API (NO reasoning_effort for 4o-mini)
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0
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
                    if correct:
                        batch_correct += 1
                    batch_total += 1

                    # Store result
                    result = {
                        'citation': item['citation'],
                        'ground_truth': item['ground_truth'],
                        'predicted': predicted,
                        'correct': correct,
                        'raw_response': response.choices[0].message.content,
                        'batch_idx': batch_idx + 1,
                        'citation_in_batch': citation_idx + 1
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
                    print(f"    [{global_idx:3d}/{len(citations_to_test)}] {truth_str:5s} -> {pred_str:5s} {'✓' if correct else '✗'} ({correct_so_far}/{global_idx} = {100*correct_so_far/global_idx:.1f}%)", flush=True)

                except Exception as e:
                    print(f"    ❌ Error on citation {global_idx}: {e}", flush=True)
                    result = {
                        'citation': item['citation'],
                        'ground_truth': item['ground_truth'],
                        'predicted': None,
                        'correct': False,
                        'error': str(e),
                        'batch_idx': batch_idx + 1,
                        'citation_in_batch': citation_idx + 1
                    }
                    results.append(result)
                    json.dump(result, outf)
                    outf.write('\n')
                    outf.flush()

                # Rate limiting
                time.sleep(0.5)

            # Batch summary
            if batch_total > 0:
                batch_accuracy = batch_correct / batch_total
                print(f"📊 Batch {batch_idx + 1} complete: {batch_correct}/{batch_total} correct ({batch_accuracy:.1%})\n", flush=True)

    # Calculate overall accuracy
    correct = sum(1 for r in results if r['correct'])
    accuracy = correct / len(results) if results else 0

    return results, accuracy, output_file

def main():
    print("="*70)
    if TEST_MODE:
        print("TEST MODE: Batch Processing (2x2) - V2 Prompt + GPT-4o-mini")
    else:
        print("FULL TEST: Batch Processing (11x11x3) - V2 Prompt + GPT-4o-mini")
    print("="*70)

    # Load test data
    citations = load_test_citations()
    print(f"\n✓ Loaded {len(citations)} test citations")

    if TEST_MODE:
        print(f"🧪 Test mode: Using first {TEST_BATCHES * TEST_CITATIONS_PER_BATCH} citations")

    all_results = {}

    # Run rounds based on mode
    num_rounds = 1 if TEST_MODE else 3
    for round_num in range(1, num_rounds + 1):
        print(f"\n{'='*70}")
        print(f"ROUND {round_num}/{num_rounds}")
        print(f"{'='*70}")

        results, accuracy, output_file = test_round(citations, round_num)

        print(f"\n{'─'*70}")
        print(f"ROUND {round_num} RESULTS: Batch Processing")
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

        if TEST_MODE:
            break  # Only run 1 round in test mode

    # Calculate consistency metrics (only for full mode)
    if not TEST_MODE:
        accuracies = [all_results[f'round{i}']['accuracy'] for i in range(1, 4)]
        avg_accuracy = sum(accuracies) / len(accuracies)
        std_dev = (sum((acc - avg_accuracy) ** 2 for acc in accuracies) / len(accuracies)) ** 0.5

        print(f"\n{'='*70}")
        print("FINAL SUMMARY: Batch Processing (3 Rounds)")
        print(f"{'='*70}")
        for i in range(1, 4):
            print(f"Round {i}: {all_results[f'round{i}']['accuracy']:.2%} ({all_results[f'round{i}']['correct']}/{len(citations)})")
        print(f"{'─'*70}")
        print(f"Average:  {avg_accuracy:.2%}")
        print(f"Std Dev:  {std_dev:.2%}")
        print(f"{'='*70}\n")

        # Save summary
        summary = {
            'model': 'GPT-4o-mini',
            'prompt': 'v2',
            'batch_size': 11,
            'reasoning_effort': None,
            'temperature': 0,
            'test_set': '../Checker_Prompt_Optimization/test_set_121_corrected.jsonl',
            'test_set_size': len(citations),
            'rounds': all_results,
            'avg_accuracy': avg_accuracy,
            'std_dev': std_dev
        }

        summary_file = Path('batch11_experiment_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"✓ Summary saved: {summary_file}\n")

if __name__ == '__main__':
    main()