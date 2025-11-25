#!/usr/bin/env python3
"""
Temperature Ensemble Voting - Phase 1 Diagnostic Test
Tests if high-variance citations correlate with baseline errors

Sample: 30 citations (mix of correct/incorrect from baseline)
Method: 5 samples at temp=0.7, measure variance and agreement
Goal: Confirm high-variance citations have lower baseline accuracy
"""

import json
import os
import sys
import time
import statistics
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from collections import Counter

# Force unbuffered output for monitoring
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Load OpenAI API key
ENV_PATH = os.getenv('ENV_FILE_PATH', '../backend/.env')
load_dotenv(ENV_PATH)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Configuration
MODEL = 'gpt-4o-mini'
TEMPERATURE = 0.7  # Higher temperature for variance
NUM_SAMPLES = 5
BASELINE_FILE = Path('competitive_benchmark/GPT-4o-mini_baseline_detailed_121.jsonl')
TEST_SET_FILE = Path('../Checker_Prompt_Optimization/test_set_121_corrected.jsonl')
PROMPT_FILE = Path('../backend/prompts/validator_prompt_v2.txt')

def parse_decision(response_text):
    """Parse VALID/INVALID from response."""
    # Remove markdown formatting for robust parsing
    cleaned = response_text.replace('*', '').replace('_', '').lower()

    if '✓ no apa 7 formatting errors detected' in response_text.lower():
        return True  # VALID
    elif '❌' in response_text:
        return False  # INVALID
    elif 'no apa 7 formatting errors' in cleaned:
        return True  # VALID
    elif 'final decision: valid' in cleaned:
        return True  # VALID
    elif 'final decision: invalid' in cleaned:
        return False  # INVALID
    else:
        # Default to INVALID if unparseable
        return False

def load_baseline_data():
    """Load baseline results to get correctness data."""
    print("📊 Loading baseline data...")
    baseline = {}

    with open(BASELINE_FILE) as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                citation = item['citation']
                baseline[citation] = {
                    'correct': item['correct'],
                    'predicted': item['predicted']
                }

    print(f"   ✓ Loaded {len(baseline)} baseline results")
    return baseline

def select_sample_citations(baseline_data, sample_size=30):
    """Select balanced sample of correct/incorrect citations."""
    correct_items = [(c, data) for c, data in baseline_data.items() if data['correct']]
    incorrect_items = [(c, data) for c, data in baseline_data.items() if not data['correct']]

    print(f"📈 Baseline: {len(correct_items)} correct, {len(incorrect_items)} incorrect")

    # Balanced sample: 15 correct, 15 incorrect
    correct_sample = correct_items[:min(15, len(correct_items))]
    incorrect_sample = incorrect_items[:min(15, len(incorrect_items))]

    sample = correct_sample + incorrect_sample
    print(f"   ✓ Selected {len(sample)} citations ({len(correct_sample)} correct, {len(incorrect_sample)} incorrect)")

    return sample

def validate_citation_ensemble(client, citation, prompt):
    """Run multiple temperature samples for ensemble voting."""
    samples = []
    responses = []

    for i in range(NUM_SAMPLES):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt.format(citation=citation)}],
                temperature=TEMPERATURE
            )

            response_text = response.choices[0].message.content
            decision = parse_decision(response_text)

            samples.append(decision)
            responses.append(response_text)

        except Exception as e:
            print(f"    ⚠️  Sample {i+1} API error: {e}")
            # Use baseline decision as fallback
            samples.append(True)  # Conservative fallback
            responses.append(f"Error: {e}")

        # Small delay to avoid rate limiting
        time.sleep(0.2)

    # Calculate ensemble metrics
    decision_counts = Counter(samples)
    majority_decision = decision_counts.most_common(1)[0][0]
    agreement = decision_counts[majority_decision] / NUM_SAMPLES
    variance = len(decision_counts) > 1  # True if not unanimous

    return {
        'samples': samples,
        'responses': responses,
        'majority_decision': majority_decision,
        'agreement': agreement,
        'variance': variance,
        'decision_counts': dict(decision_counts)
    }

def main():
    print("🎯 Temperature Ensemble Voting - Phase 1 Diagnostic")
    print(f"📊 Model: {MODEL}, Temperature: {TEMPERATURE}")
    print(f"🔬 Testing variance vs. baseline accuracy correlation")
    print(f"📋 Sample: 30 citations (15 correct, 15 incorrect from baseline)")
    print("=" * 70)

    # Load data
    baseline_data = load_baseline_data()
    sample_citations = select_sample_citations(baseline_data)

    # Load prompt
    with open(PROMPT_FILE) as f:
        prompt = f.read()

    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)

    results = []

    for i, (citation, baseline_info) in enumerate(sample_citations, 1):
        print(f"📝 [{i:2d}/30] Processing citation...")

        # Run ensemble validation
        ensemble_result = validate_citation_ensemble(client, citation, prompt)

        # Record result
        result = {
            'citation': citation,
            'baseline_correct': baseline_info['correct'],
            'baseline_predicted': baseline_info['predicted'],
            'samples': ensemble_result['samples'],
            'majority_decision': ensemble_result['majority_decision'],
            'agreement': ensemble_result['agreement'],
            'variance': ensemble_result['variance'],
            'decision_counts': ensemble_result['decision_counts'],
            'ensemble_correct': (ensemble_result['majority_decision'] ==
                               [item for item in json.load(open(TEST_SET_FILE))
                                if item['citation'] == citation][0]['ground_truth'])
        }
        results.append(result)

        # Progress indicator
        baseline_status = "✓" if result['baseline_correct'] else "✗"
        ensemble_status = "✓" if result['ensemble_correct'] else "✗"
        variance_indicator = "🔄" if result['variance'] else "🔒"

        print(f"     {baseline_status}→{ensemble_status} {variance_indicator} "
              f"Agreement: {result['agreement']:.1f} "
              f"({result['decision_counts']})")

        # Progress summary every 10 citations
        if i % 10 == 0:
            high_variance = [r for r in results if r['variance']]
            low_variance = [r for r in results if not r['variance']]

            hv_baseline_correct = sum(1 for r in high_variance if r['baseline_correct'])
            lv_baseline_correct = sum(1 for r in low_variance if r['baseline_correct'])

            print(f"     📊 Progress: {i}/30")
            print(f"        High variance ({len(high_variance)}): {hv_baseline_correct}/{len(high_variance)} baseline correct")
            print(f"        Low variance ({len(low_variance)}): {lv_baseline_correct}/{len(low_variance)} baseline correct")

    # Analysis
    print(f"\n{'='*70}")
    print("PHASE 1 DIAGNOSTIC RESULTS")
    print(f"{'='*70}")

    high_variance = [r for r in results if r['variance']]
    low_variance = [r for r in results if not r['variance']]

    # Baseline accuracy by variance
    hv_baseline_acc = sum(1 for r in high_variance if r['baseline_correct']) / len(high_variance) if high_variance else 0
    lv_baseline_acc = sum(1 for r in low_variance if r['baseline_correct']) / len(low_variance) if low_variance else 0

    print(f"Citations with variance: {len(high_variance)}/30 ({len(high_variance)/30:.1%})")
    print(f"  Baseline accuracy: {hv_baseline_acc:.2%}")
    print(f"Citations without variance: {len(low_variance)}/30 ({len(low_variance)/30:.1%})")
    print(f"  Baseline accuracy: {lv_baseline_acc:.2%}")

    # Ensemble vs Baseline
    ensemble_correct = sum(1 for r in results if r['ensemble_correct'])
    baseline_correct = sum(1 for r in results if r['baseline_correct'])

    print(f"\nComparison on 30 citations:")
    print(f"  Baseline accuracy: {baseline_correct/30:.2%} ({baseline_correct}/30)")
    print(f"  Ensemble accuracy: {ensemble_correct/30:.2%} ({ensemble_correct}/30)")

    # Agreement analysis
    high_agreement = [r for r in results if r['agreement'] >= 0.8]
    medium_agreement = [r for r in results if 0.6 <= r['agreement'] < 0.8]
    low_agreement = [r for r in results if r['agreement'] < 0.6]

    print(f"\nAgreement levels:")
    print(f"  High (≥80%): {len(high_agreement)} citations")
    print(f"  Medium (60-79%): {len(medium_agreement)} citations")
    print(f"  Low (<60%): {len(low_agreement)} citations")

    # Key finding
    variance_gap = lv_baseline_acc - hv_baseline_acc
    print(f"\n🔍 KEY FINDING: Variance correlates with errors")
    print(f"   Low-variance citations: {lv_baseline_acc:.1%} baseline accuracy")
    print(f"   High-variance citations: {hv_baseline_acc:.1%} baseline accuracy")
    print(f"   Gap: {variance_gap:.1%} percentage points")

    if variance_gap > 0.2:  # 20% gap
        print("   ✅ STRONG correlation - Proceed to Phase 2")
    elif variance_gap > 0.1:  # 10% gap
        print("   ⚠️  Moderate correlation - Consider Phase 2")
    else:
        print("   ❌ Weak correlation - Reconsider approach")

    print(f"{'='*70}")

    # Save results
    output_file = 'competitive_benchmark/ensemble_voting_phase1_30.jsonl'
    with open(output_file, 'w') as f:
        for result in results:
            json.dump(result, f)
            f.write('\n')

    print(f"✅ Results saved to {output_file}")
    print(f"💰 Estimated cost: ${30 * NUM_SAMPLES * 0.00015:.2f} ({30 * NUM_SAMPLES} API calls)")

    return results

if __name__ == '__main__':
    results = main()