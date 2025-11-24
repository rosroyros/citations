"""
Test current optimized prompt with reasoning_effort=high
"""
import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Load OpenAI API key
load_dotenv('../backend/.env')
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

    print(f"\n🚀 Testing: GPT-5-mini + reasoning_effort=high")
    print(f"📋 Test set: {len(citations)} citations")
    print(f"🌡️  Temperature: 1")
    print(f"🧠 Reasoning: high")
    print(f"⏱️  Estimated time: ~2-3 minutes (121 calls × 0.5s delay)")
    print(f"💰 Estimated cost: ~$0.50-1.00")
    print(f"\n📊 Starting API calls...")
    print(f"Format: [idx/total] truth -> pred result (running accuracy)")
    print(f"{'─'*60}\n")

    for i, item in enumerate(citations, 1):
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

            # Parse response
            response_text = response.choices[0].message.content.strip().lower()
            predicted = 'valid' in response_text
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

            # Progress indicator - show every citation
            correct_so_far = sum(1 for r in results if r['correct'])
            print(f"  [{i:3d}/{len(citations)}] {item['ground_truth']:5s} -> {predicted:5s} {'✓' if correct else '✗'} ({correct_so_far}/{i} = {100*correct_so_far/i:.1f}%)")

        except Exception as e:
            print(f"  ❌ Error on citation {i}: {e}")
            result = {
                'citation': item['citation'],
                'ground_truth': item['ground_truth'],
                'predicted': None,
                'correct': False,
                'error': str(e)
            }
            results.append(result)

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

    # Run test
    results, accuracy = test_model_high_reasoning(citations)

    # Save detailed results
    output_file = Path('GPT-5-mini_optimized_high_detailed_121.jsonl')
    with open(output_file, 'w') as f:
        for result in results:
            json.dump(result, f)
            f.write('\n')

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