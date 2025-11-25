"""
Test current optimized prompt with reasoning_effort=high
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

# Load OpenAI API key with configurable path
ENV_PATH = os.getenv('ENV_FILE_PATH', '../backend/.env')
load_dotenv(ENV_PATH)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    print("❌ No OpenAI API key found")
    exit(1)

import openai
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Load optimized prompt from file
PROMPT_FILE = Path('../backend/prompts/validator_prompt_optimized.txt')
with open(PROMPT_FILE, 'r') as f:
    OPTIMIZED_PROMPT = f.read()

# Ensure prompt has citation placeholder
if '{citation}' not in OPTIMIZED_PROMPT:
    OPTIMIZED_PROMPT += "\n\nCitation: {citation}"

def load_test_citations():
    """Load corrected test set."""
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

def test_model_high_reasoning(citations):
    """Test with reasoning_effort=high."""
    results = []
    output_file = Path('GPT-5-mini_optimized_high_detailed_121.jsonl')

    # Check for existing progress
    start_idx = 0
    if output_file.exists():
        with open(output_file, 'r') as f:
            for line in f:
                results.append(json.loads(line))
        start_idx = len(results)
        print(f"\n📂 Found existing progress: {start_idx} citations complete", flush=True)
        print(f"   Resuming from citation {start_idx + 1}...\n", flush=True)

    print(f"\n🚀 Testing: GPT-5-mini + reasoning_effort=high", flush=True)
    print(f"📋 Test set: {len(citations)} citations (processing {len(citations) - start_idx})", flush=True)
    print(f"🌡️  Temperature: 1", flush=True)
    print(f"🧠 Reasoning: high", flush=True)
    print(f"⏱️  Estimated time: ~{(len(citations) - start_idx) * 2} minutes (~2 min/citation)", flush=True)
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
                prompt = OPTIMIZED_PROMPT.format(citation=item['citation'])

                # Call API with high reasoning
                response = client.chat.completions.create(
                    model="gpt-5-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=1,  # Required for GPT-5
                    reasoning_effort="high"
                )

                # Parse response using PRODUCTION logic
                # Valid: "✓ No APA 7 formatting errors detected"
                # Invalid: Lines starting with "❌"
                response_text = response.choices[0].message.content.strip()

                # Check for valid marker (production checks both variations)
                if '✓ No APA 7 formatting errors detected' in response_text or 'No APA 7 formatting errors' in response_text:
                    predicted = True
                # Check for error markers (production checks for ❌ at line start)
                elif '❌' in response_text:
                    predicted = False
                else:
                    # Ambiguous response - mark as error for investigation
                    predicted = None

                # Calculate correctness (None = parse error, always wrong)
                if predicted is None:
                    correct = False
                else:
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
                outf.flush()  # Ensure written to disk

                # Progress indicator - show every citation
                correct_so_far = sum(1 for r in results if r['correct'])
                truth_str = str(item['ground_truth'])
                pred_str = str(predicted) if predicted is not None else 'PARSE_ERR'
                print(f"  [{i:3d}/{len(citations)}] {truth_str:5s} -> {pred_str:10s} {'✓' if correct else '✗'} ({correct_so_far}/{i} = {100*correct_so_far/i:.1f}%)", flush=True)

            except openai.RateLimitError as e:
                print(f"  ⏱️  Rate limit on citation {i}: {e}", flush=True)
                result = {
                    'citation': item['citation'],
                    'ground_truth': item['ground_truth'],
                    'predicted': None,
                    'correct': False,
                    'error': 'RateLimitError',
                    'error_details': str(e)
                }
                results.append(result)
                json.dump(result, outf)
                outf.write('\n')
                outf.flush()
                time.sleep(5)  # Back off on rate limit
            except openai.AuthenticationError as e:
                print(f"  🔑 Auth error on citation {i}: {e}", flush=True)
                result = {
                    'citation': item['citation'],
                    'ground_truth': item['ground_truth'],
                    'predicted': None,
                    'correct': False,
                    'error': 'AuthenticationError',
                    'error_details': str(e)
                }
                results.append(result)
                json.dump(result, outf)
                outf.write('\n')
                outf.flush()
            except openai.APIError as e:
                print(f"  🌐 API error on citation {i}: {e}", flush=True)
                result = {
                    'citation': item['citation'],
                    'ground_truth': item['ground_truth'],
                    'predicted': None,
                    'correct': False,
                    'error': 'APIError',
                    'error_details': str(e)
                }
                results.append(result)
                json.dump(result, outf)
                outf.write('\n')
                outf.flush()
            except Exception as e:
                print(f"  ❌ Unexpected error on citation {i}: {e}", flush=True)
                result = {
                    'citation': item['citation'],
                    'ground_truth': item['ground_truth'],
                    'predicted': None,
                    'correct': False,
                    'error': 'UnexpectedError',
                    'error_details': str(e)
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

    return results, accuracy

def main():
    print("="*70)
    print("TEST: Current Prompt + High Reasoning")
    print("="*70)

    # Load test data
    citations = load_test_citations()
    print(f"\n✓ Loaded {len(citations)} test citations")

    # Run test (results now written incrementally)
    results, accuracy = test_model_high_reasoning(citations)

    # Results already saved incrementally
    output_file = Path('GPT-5-mini_optimized_high_detailed_121.jsonl')

    print(f"\n{'='*70}")
    print(f"RESULTS: Current + High Reasoning")
    print(f"{'='*70}")
    print(f"Accuracy: {accuracy:.2%} ({sum(1 for r in results if r['correct'])}/{len(results)})")
    print(f"Output: {output_file}")
    print(f"{'='*70}\n")

    # Save summary
    summary = {
        'model': 'GPT-5-mini_optimized',
        'reasoning_effort': 'high',
        'temperature': 1,
        'test_set': '../Checker_Prompt_Optimization/test_set_121_corrected.jsonl',
        'test_set_size': len(results),
        'accuracy': accuracy,
        'correct': sum(1 for r in results if r['correct']),
        'errors': sum(1 for r in results if not r['correct']),
        'output_file': str(output_file)
    }

    summary_file = Path('current_high_reasoning_summary.json')
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"✓ Summary saved: {summary_file}\n")

    # Compare to existing results
    print("📊 Comparison to Other Tests:")
    print(f"  Low reasoning:     74.38% (90/121)")
    print(f"  Medium reasoning:  80.17% (97/121)")
    print(f"  High reasoning:    {accuracy:.2%} ({sum(1 for r in results if r['correct'])}/{len(results)}) ← NEW")
    print(f"  Consistency avg:   75.76%")

    improvement_vs_medium = accuracy - 0.8017
    print(f"\n  High vs Medium: {improvement_vs_medium:+.2%} ({int(improvement_vs_medium*121):+d} citations)")

if __name__ == '__main__':
    main()