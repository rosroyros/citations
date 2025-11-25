#!/usr/bin/env python3
"""
DEBUG TEST: 5 citations to validate the fix works
"""

import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Force unbuffered output for monitoring
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Load OpenAI API key
ENV_PATH = os.getenv('ENV_FILE_PATH', 'backend/.env')
load_dotenv(ENV_PATH)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Configuration
MODEL = 'gpt-4o-mini'
TEMPERATURE = 0

# Load prompts
v2_prompt = Path('backend/prompts/validator_prompt_v2.txt').read_text()
review_invalid_prompt = Path('backend/prompts/validator_prompt_recursive_review_invalid.txt').read_text()
review_valid_prompt = Path('backend/prompts/validator_prompt_recursive_review_valid.txt').read_text()

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

    print(f"🔍 PROMPT LENGTH: {len(prompt)} chars")
    print(f"📝 PROMPT END:\n{prompt[-500:]}")
    print("=" * 70)

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

            print(f"📤 RESPONSE LENGTH: {len(response_text)} chars")
            print(f"📋 RESPONSE START:\n{response_text[:300]}")
            print("=" * 70)

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
    print(f"🔧 DEBUG TEST: 5 citations to validate fix")
    print(f"📊 Model: {MODEL}, Temperature: {TEMPERATURE}")
    print("=" * 70)

    # Small test set - 5 citations from the original set
    test_citations = [
        {
            "citation": "Smith, J. (2023). A study on machine learning. Journal of AI Research, 15(2), 123-145. https://doi.org/10.1234/jair.2023.123",
            "ground_truth": True
        },
        {
            "citation": "Johnson, M.B., & Davis, S.K. (2022). Neural networks in practice. In: Proceedings of the International Conference on AI (pp. 45-67). New York, NY: Academic Press.",
            "ground_truth": False  # Should be INVALID - missing DOI and DOI format
        },
        {
            "citation": "Williams, A. (2021). Understanding algorithms. Tech Press.",
            "ground_truth": False  # Should be INVALID - missing publication details
        },
        {
            "citation": "Brown, C.D., & Lee, E.F. (2020). Data analysis methods. Journal of Statistics, 42(3), 789-812. doi:10.5678/js.2020.789",
            "ground_truth": True
        },
        {
            "citation": "Taylor, R. (2019). Software engineering principles. ACM Computing Surveys, 51(4), 1-25. https://doi.org/10.1145/1234567",
            "ground_truth": True
        }
    ]

    client = OpenAI(api_key=OPENAI_API_KEY)
    results = []

    for i, item in enumerate(test_citations, 1):
        citation = item['citation']
        ground_truth = item['ground_truth']

        print(f"\n{'='*70}")
        print(f"📝 [{i}/5] Testing citation:")
        print(f"📄 CITATION: {citation}")
        print(f"✅ GROUND TRUTH: {'VALID' if ground_truth else 'INVALID'}")
        print(f"{'='*70}")

        # Round 1: Standard validation
        print(f"\n🔄 ROUND 1: Standard v2 validation")
        round1 = validate_citation(client, citation)
        print(f"📊 ROUND 1 RESULT: {'VALID' if round1['decision'] else 'INVALID'}")
        if round1['errors']:
            for j, error in enumerate(round1['errors'], 1):
                print(f"  ❌ Error {j}: {error}")
        else:
            print("  ✓ No errors found")

        # Round 2: Self-review
        print(f"\n🔄 ROUND 2: Self-review")
        round2 = self_review(client, citation, round1)
        print(f"📊 ROUND 2 RESULT: {'VALID' if round2['decision'] else 'INVALID'}")
        print(f"📋 ROUND 2 REASONING:")
        reasoning_lines = round2['raw_response'].split('\n')[:10]
        for line in reasoning_lines:
            if line.strip():
                print(f"  {line}")

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

        # Analysis
        print(f"\n📈 ANALYSIS:")
        print(f"  Round 1: {'VALID' if round1['decision'] else 'INVALID'}")
        print(f"  Round 2: {'VALID' if round2['decision'] else 'INVALID'}")
        print(f"  Changed: {'Yes' if result['changed'] else 'No'}")
        print(f"  Correct: {'✅' if result['correct'] else '❌'}")

        time.sleep(2)  # Small delay between citations

    # Final summary
    print(f"\n{'='*70}")
    print(f"📊 FINAL SUMMARY - 5 Citation Test")
    print(f"{'='*70}")

    correct = sum(1 for r in results if r['correct'])
    changed = sum(1 for r in results if r['changed'])
    accuracy = correct / len(results)

    print(f"Accuracy: {accuracy:.2%} ({correct}/{5})")
    print(f"Changes: {changed} citations revised")

    # Changes analysis
    invalid_to_valid = sum(1 for r in results if not r['round1_decision'] and r['round2_decision'])
    valid_to_invalid = sum(1 for r in results if r['round1_decision'] and not r['round2_decision'])

    print(f"  INVALID → VALID: {invalid_to_valid}")
    print(f"  VALID → INVALID: {valid_to_invalid}")

    # Detailed results
    print(f"\n📋 DETAILED RESULTS:")
    for i, result in enumerate(results, 1):
        status = "✅" if result['correct'] else "❌"
        change = "→" if result['changed'] else "="
        print(f"  {i}. {status} {result['round1_decision']} {change} {result['final_decision']} (GT: {result['ground_truth']})")

    # Save results
    output_file = f'debug_recursive_v3_5_citations.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to {output_file}")
    print(f"🔍 PLEASE REVIEW: Are the citations actually being validated?")

    return results

if __name__ == '__main__':
    results = main()