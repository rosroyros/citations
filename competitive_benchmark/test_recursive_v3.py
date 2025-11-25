#!/usr/bin/env python3
"""
Recursive validation v3: Targeted self-review approach
- Round 1: Standard v2 validation (one citation at a time)
- Round 2: Targeted self-review based on Round 1 decision

This addresses the failure of citations-ietz by using self-review instead of adversarial review.
"""

import json
import os
import sys
import time
import statistics
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Force unbuffered output for monitoring
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Load OpenAI API key
ENV_PATH = os.getenv('ENV_FILE_PATH', '../backend/.env')
load_dotenv(ENV_PATH)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Configuration
MODEL = 'gpt-4o-mini'
TEMPERATURE = 0
TEST_SET = Path('../Checker_Prompt_Optimization/test_set_121_corrected.jsonl')
ROUND = int(sys.argv[1]) if len(sys.argv) > 1 else 1

# Load prompts - all in parent backend/prompts dir
v2_prompt = Path('../backend/prompts/validator_prompt_v2.txt').read_text()
review_invalid_prompt = Path('../backend/prompts/validator_prompt_recursive_review_invalid.txt').read_text()
review_valid_prompt = Path('../backend/prompts/validator_prompt_recursive_review_valid.txt').read_text()

def parse_decision(response_text):
    """Parse VALID/INVALID from response."""
    if '✓ No APA 7 formatting errors detected' in response_text:
        return True  # VALID
    elif '❌' in response_text:
        return False  # INVALID
    elif 'no apa 7 formatting errors' in response_text.lower():
        return True  # VALID
    elif 'final decision: valid' in response_text.lower():
        return True  # VALID
    elif 'final decision: invalid' in response_text.lower():
        return False  # INVALID
    else:
        return False  # INVALID (default)

def extract_errors(response_text):
    """Extract list of errors from response."""
    if '❌' not in response_text:
        return []

    lines = response_text.split('\n')
    errors = [line.strip() for line in lines if '❌' in line]
    return errors

def validate_citation(client, citation):
    """Round 1: Standard v2 validation."""
    prompt = v2_prompt.format(citation=citation)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=TEMPERATURE
            )

            response_text = response.choices[0].message.content
            decision = parse_decision(response_text)
            errors = extract_errors(response_text) if not decision else []

            return {
                'decision': decision,
                'errors': errors,
                'raw_response': response_text
            }

        except Exception as e:
            if attempt == max_retries - 1:
                print(f"  ⚠️  API error after {max_retries} attempts: {e}")
                return {
                    'decision': False,  # Conservative: INVALID on error
                    'errors': [f"API error: {e}"],
                    'raw_response': f"Error: {e}"
                }
            time.sleep(2 ** attempt)  # Exponential backoff

def self_review(client, citation, round1_result):
    """Round 2: Self-review based on Round 1 decision."""

    if round1_result['decision'] == False:  # Marked INVALID
        # Use review_invalid prompt
        error_list = '\n'.join(round1_result['errors'])
        prompt = review_invalid_prompt.format(
            citation=citation,
            round1_error_list=error_list
        )
    else:  # Marked VALID
        # Use review_valid prompt
        prompt = review_valid_prompt.format(citation=citation)

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=TEMPERATURE
            )

            response_text = response.choices[0].message.content
            decision = parse_decision(response_text)

            return {
                'decision': decision,
                'raw_response': response_text
            }

        except Exception as e:
            if attempt == max_retries - 1:
                print(f"  ⚠️  Review API error after {max_retries} attempts: {e}")
                return {
                    'decision': round1_result['decision'],  # Fall back to Round 1 decision
                    'raw_response': f"Review error: {e}"
                }
            time.sleep(2 ** attempt)

def main():
    print(f"🔄 Recursive Validation v3 - Round {ROUND}")
    print(f"📊 Model: {MODEL}, Temperature: {TEMPERATURE}")
    print(f"📋 Processing 121 citations with targeted self-review")
    print("=" * 70)

    # Load test set
    with open(TEST_SET) as f:
        test_data = [json.loads(line) for line in f]

    client = OpenAI(api_key=OPENAI_API_KEY)
    results = []

    for i, item in enumerate(test_data, 1):
        citation = item['citation']
        ground_truth = item['ground_truth']

        print(f"📝 [{i:3d}/121] Processing citation...")

        # Round 1: Standard validation
        round1 = validate_citation(client, citation)

        # Round 2: Self-review
        round2 = self_review(client, citation, round1)

        # Record result
        result = {
            'citation': citation,
            'ground_truth': ground_truth,
            'round1_decision': round1['decision'],
            'round1_errors': round1['errors'],
            'round2_decision': round2['decision'],
            'final_decision': round2['decision'],
            'correct': (round2['decision'] == ground_truth),
            'changed': (round1['decision'] != round2['decision']),
            'round1_response': round1['raw_response'],
            'round2_response': round2['raw_response']
        }
        results.append(result)

        # Progress indicator
        status = "✓" if result['correct'] else "✗"
        change = "→" if result['changed'] else "="
        print(f"   {status} {result['round1_decision']} {change} {result['final_decision']} ({'changed' if result['changed'] else 'same'})")

        # Progress summary every 10 citations
        if i % 10 == 0:
            correct = sum(1 for r in results if r['correct'])
            changed = sum(1 for r in results if r['changed'])
            print(f"   📊 Progress: {i}/121 - {correct}/{i} correct ({100*correct/i:.1f}%), {changed} changes")

        # Small delay to avoid rate limiting
        time.sleep(0.5)

    # Calculate final metrics
    correct = sum(1 for r in results if r['correct'])
    changed = sum(1 for r in results if r['changed'])
    accuracy = correct / len(results)

    # Changes analysis
    invalid_to_valid = sum(1 for r in results if not r['round1_decision'] and r['round2_decision'])
    valid_to_invalid = sum(1 for r in results if r['round1_decision'] and not r['round2_decision'])

    invalid_to_valid_correct = sum(1 for r in results if not r['round1_decision'] and r['round2_decision'] and r['correct'])
    valid_to_invalid_correct = sum(1 for r in results if r['round1_decision'] and not r['round2_decision'] and r['correct'])

    print(f"\n{'='*70}")
    print(f"ROUND {ROUND} RESULTS: Recursive Validation v3")
    print(f"{'='*70}")
    print(f"Accuracy: {accuracy:.2%} ({correct}/121)")
    print(f"Changes: {changed} citations revised")
    print(f"  INVALID → VALID: {invalid_to_valid} ({invalid_to_valid_correct} correct)")
    print(f"  VALID → INVALID: {valid_to_invalid} ({valid_to_invalid_correct} correct)")
    print(f"{'='*70}")

    # Save results
    output_file = f'recursive_v3_round{ROUND}_detailed_121.jsonl'
    with open(output_file, 'w') as f:
        for result in results:
            json.dump(result, f)
            f.write('\n')

    print(f"✅ Results saved to {output_file}")
    print(f"💰 Estimated cost: ${len(results) * 2 * 0.00015:.2f} (242 API calls)")

    return results

if __name__ == '__main__':
    results = main()