#!/usr/bin/env python3
"""
Temperature Ensemble Voting - Phase 2 Full Test
Complete 121-citation ensemble test based on successful Phase 1 results

Phase 1 Results:
- 15% accuracy gap between high/low variance citations (moderate correlation)
- 33.3% of citations show variance at temp=0.7
- Ensemble improved accuracy: 56.67% vs 50% baseline (+6.67%)
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
TEMPERATURE = 0.7
NUM_SAMPLES = 5
TEST_SET_FILE = Path('../Checker_Prompt_Optimization/test_set_121_corrected.jsonl')
PROMPT_FILE = Path('../backend/prompts/validator_prompt_v2.txt')
BASELINE_FILE = Path('GPT-4o-mini_v2_default_round1_detailed_121.jsonl')

def parse_decision(response_text):
    """Parse VALID/INVALID from response."""
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

def load_test_data():
    """Load test set with ground truth."""
    print("📊 Loading test data...")
    test_data = []
    ground_truth_data = {}

    with open(TEST_SET_FILE) as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                test_data.append(item)
                ground_truth_data[item['citation']] = item['ground_truth']

    print(f"   ✓ Loaded {len(test_data)} citations with ground truth")
    return test_data, ground_truth_data

def load_baseline_data():
    """Load baseline results for comparison."""
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

    baseline_correct = sum(1 for data in baseline.values() if data['correct'])
    baseline_accuracy = baseline_correct / len(baseline)

    print(f"   ✓ Loaded {len(baseline)} baseline results")
    print(f"   ✓ Baseline accuracy: {baseline_accuracy:.2%} ({baseline_correct}/{len(baseline)})")
    return baseline, baseline_accuracy

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
            samples.append(True)  # Conservative fallback
            responses.append(f"Error: {e}")

        # Small delay to avoid rate limiting
        time.sleep(0.2)

    # Calculate ensemble metrics
    decision_counts = Counter(samples)
    majority_decision = decision_counts.most_common(1)[0][0]
    confidence = decision_counts[majority_decision] / NUM_SAMPLES
    variance = len(decision_counts) > 1

    return {
        'samples': samples,
        'responses': responses,
        'majority_decision': majority_decision,
        'confidence': confidence,
        'variance': variance,
        'decision_counts': dict(decision_counts)
    }

def main():
    print("🎯 Temperature Ensemble Voting - Phase 2 Full Test")
    print(f"📊 Model: {MODEL}, Temperature: {TEMPERATURE}")
    print(f"🔬 Running ensemble voting on all 121 citations")
    print(f"📋 Based on Phase 1 success: 15% variance-error correlation")
    print("=" * 70)

    # Load data
    test_data, ground_truth_data = load_test_data()
    baseline_data, baseline_accuracy = load_baseline_data()

    # Load prompt
    with open(PROMPT_FILE) as f:
        prompt = f.read()

    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)

    results = []

    for i, item in enumerate(test_data, 1):
        citation = item['citation']
        ground_truth = item['ground_truth']

        print(f"📝 [{i:3d}/121] Processing citation...")

        # Run ensemble validation
        ensemble_result = validate_citation_ensemble(client, citation, prompt)

        # Get baseline info if available
        baseline_info = baseline_data.get(citation, {'correct': None, 'predicted': None})

        # Record result
        result = {
            'citation': citation,
            'ground_truth': ground_truth,
            'baseline_correct': baseline_info['correct'],
            'baseline_predicted': baseline_info['predicted'],
            'samples': ensemble_result['samples'],
            'majority_decision': ensemble_result['majority_decision'],
            'confidence': ensemble_result['confidence'],
            'variance': ensemble_result['variance'],
            'decision_counts': ensemble_result['decision_counts'],
            'ensemble_correct': ensemble_result['majority_decision'] == ground_truth
        }
        results.append(result)

        # Progress indicator
        baseline_status = "✓" if result['baseline_correct'] else "✗" if result['baseline_correct'] is False else "?"
        ensemble_status = "✓" if result['ensemble_correct'] else "✗"
        variance_indicator = "🔄" if result['variance'] else "🔒"

        print(f"     {baseline_status}→{ensemble_status} {variance_indicator} "
              f"Confidence: {result['confidence']:.1f} "
              f"({result['decision_counts']})")

        # Progress summary every 20 citations
        if i % 20 == 0:
            correct = sum(1 for r in results if r['ensemble_correct'])
            changed = sum(1 for r in results if r['variance'])
            print(f"     📊 Progress: {i}/121 - {correct}/{i} correct ({100*correct/i:.1f}%), {changed} with variance")

    # Analysis
    print(f"\n{'='*70}")
    print("PHASE 2 FULL RESULTS: Temperature Ensemble Voting")
    print(f"{'='*70}")

    # Overall accuracy
    ensemble_correct = sum(1 for r in results if r['ensemble_correct'])
    baseline_correct = sum(1 for r in results if r['baseline_correct'] is True)
    ensemble_accuracy = ensemble_correct / len(results)

    print(f"OVERALL ACCURACY:")
    print(f"  Baseline: {baseline_correct/len(results):.2%} ({baseline_correct}/{len(results)})")
    print(f"  Ensemble: {ensemble_accuracy:.2%} ({ensemble_correct}/{len(results)})")
    print(f"  Improvement: {ensemble_accuracy - (baseline_correct/len(results)):.2%}")

    # Variance analysis
    high_variance = [r for r in results if r['variance']]
    low_variance = [r for r in results if not r['variance']]

    hv_baseline_correct = sum(1 for r in high_variance if r['baseline_correct'])
    lv_baseline_correct = sum(1 for r in low_variance if r['baseline_correct'])
    hv_ensemble_correct = sum(1 for r in high_variance if r['ensemble_correct'])
    lv_ensemble_correct = sum(1 for r in low_variance if r['ensemble_correct'])

    print(f"\nVARIANCE ANALYSIS:")
    print(f"  Citations with variance: {len(high_variance)}/121 ({len(high_variance)/121:.1%})")
    print(f"    Baseline accuracy: {hv_baseline_correct/len(high_variance):.2%}")
    print(f"    Ensemble accuracy: {hv_ensemble_correct/len(high_variance):.2%}")
    print(f"  Citations without variance: {len(low_variance)}/121 ({len(low_variance)/121:.1%})")
    print(f"    Baseline accuracy: {lv_baseline_correct/len(low_variance):.2%}")
    print(f"    Ensemble accuracy: {lv_ensemble_correct/len(low_variance):.2%}")

    # Confidence levels
    high_conf = [r for r in results if r['confidence'] >= 0.8]
    medium_conf = [r for r in results if 0.6 <= r['confidence'] < 0.8]
    low_conf = [r for r in results if r['confidence'] < 0.6]

    high_conf_accuracy = sum(1 for r in high_conf if r['ensemble_correct']) / len(high_conf) if high_conf else 0
    medium_conf_accuracy = sum(1 for r in medium_conf if r['ensemble_correct']) / len(medium_conf) if medium_conf else 0
    low_conf_accuracy = sum(1 for r in low_conf if r['ensemble_correct']) / len(low_conf) if low_conf else 0

    print(f"\nCONFIDENCE LEVELS:")
    print(f"  High confidence (≥80%): {len(high_conf)} citations - {high_conf_accuracy:.1%} accuracy")
    print(f"  Medium confidence (60-79%): {len(medium_conf)} citations - {medium_conf_accuracy:.1%} accuracy")
    print(f"  Low confidence (<60%): {len(low_conf)} citations - {low_conf_accuracy:.1%} accuracy")

    # Success assessment
    improvement = ensemble_accuracy - (baseline_correct/len(results))
    print(f"\n🔍 SUCCESS ASSESSMENT:")
    if improvement >= 0.08:
        tier = "Tier 3 (Excellent: >8% improvement)"
        recommendation = "✅ READY FOR PRODUCTION"
    elif improvement >= 0.05:
        tier = "Tier 2 (Great: 5-8% improvement)"
        recommendation = "✅ PROCEED TO CASCADE EXPERIMENT"
    elif improvement >= 0.03:
        tier = "Tier 1 (Good: 3-5% improvement)"
        recommendation = "⚠️  CONSIDER ADVERSARIAL PAIRING"
    else:
        tier = "Below threshold (<3% improvement)"
        recommendation = "❌ SKIP TO CASCADE EXPERIMENT"

    print(f"  Result: {tier}")
    print(f"  Recommendation: {recommendation}")
    print(f"  Cost per citation: ${5 * 0.00015:.4f}")
    print(f"  Total cost: ${len(results) * 5 * 0.00015:.2f}")

    print(f"{'='*70}")

    # Save results
    output_file = 'ensemble_voting_phase2_121.jsonl'
    with open(output_file, 'w') as f:
        for result in results:
            json.dump(result, f)
            f.write('\n')

    print(f"✅ Results saved to {output_file}")
    print(f"💰 Estimated cost: ${len(results) * NUM_SAMPLES * 0.00015:.2f} ({len(results) * NUM_SAMPLES} API calls)")

    return results

if __name__ == '__main__':
    results = main()