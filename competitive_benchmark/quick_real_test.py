"""
Quick real API test on small sample to get actual performance data.
"""
import json
import os
import time
from pathlib import Path

# API keys
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Prompts
BASELINE_PROMPT = """Is this citation valid or invalid? Respond with exactly one word: "valid" or "invalid".

Citation: {citation}"""

OPTIMIZED_PROMPT = """As an expert academic librarian specializing in citation validation, evaluate this citation according to APA 7th edition standards.

Consider:
- Required elements completeness (author, title, source, date)
- Format accuracy and consistency
- Source credibility and accessibility
- DOI/publisher information when applicable

Respond with exactly one word: "valid" or "invalid"

Citation: {citation}"""

def test_claude(citation, ground_truth, prompt_type):
    """Test Claude Sonnet 4.5 with real API call."""
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = BASELINE_PROMPT if prompt_type == 'baseline' else OPTIMIZED_PROMPT
    prompt = prompt.format(citation=citation)

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=10,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        predicted_text = response.content[0].text.lower().strip()
        predicted = predicted_text == 'valid'

        return {
            'citation': citation,
            'ground_truth': ground_truth,
            'predicted': 'valid' if predicted else 'invalid',
            'correct': predicted == ground_truth
        }
    except Exception as e:
        return {
            'citation': citation,
            'ground_truth': ground_truth,
            'predicted': None,
            'correct': False,
            'error': str(e)
        }

def main():
    print("="*60)
    print("QUICK REAL API TEST - Claude Sonnet 4.5")
    print("="*60)

    if not ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY not set")
        return

    # Load first 10 citations from validation set
    with open('validation_set.jsonl', 'r') as f:
        lines = f.readlines()[:10]

    dataset = []
    for line in lines:
        item = json.loads(line)
        dataset.append({
            'citation': item['citation'],
            'ground_truth': item['is_valid']
        })

    print(f"Testing {len(dataset)} citations...\n")

    # Test baseline prompt
    print("📋 BASELINE PROMPT TEST")
    baseline_results = []
    for i, item in enumerate(dataset, 1):
        result = test_claude(item['citation'], item['ground_truth'], 'baseline')
        baseline_results.append(result)
        status = "✅" if result['correct'] else "❌"
        print(f"  {i}. {status} {result['predicted']} vs {item['ground_truth']}")
        time.sleep(0.5)  # Rate limiting

    baseline_correct = sum(1 for r in baseline_results if r['correct'])
    baseline_accuracy = baseline_correct / len(baseline_results)

    print(f"\nBaseline Results: {baseline_correct}/{len(baseline_results)} = {baseline_accuracy:.1%}")

    # Test optimized prompt
    print(f"\n🚀 OPTIMIZED PROMPT TEST")
    optimized_results = []
    for i, item in enumerate(dataset, 1):
        result = test_claude(item['citation'], item['ground_truth'], 'optimized')
        optimized_results.append(result)
        status = "✅" if result['correct'] else "❌"
        print(f"  {i}. {status} {result['predicted']} vs {item['ground_truth']}")
        time.sleep(0.5)  # Rate limiting

    optimized_correct = sum(1 for r in optimized_results if r['correct'])
    optimized_accuracy = optimized_correct / len(optimized_results)

    print(f"\nOptimized Results: {optimized_correct}/{len(optimized_results)} = {optimized_accuracy:.1%}")

    improvement = optimized_accuracy - baseline_accuracy
    print(f"\n📊 SUMMARY:")
    print(f"   Baseline:  {baseline_accuracy:.1%}")
    print(f"   Optimized: {optimized_accuracy:.1%}")
    print(f"   Change:    {improvement:+.1%}")

    # Save results
    results = {
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'sample_size': len(dataset),
        'baseline': {
            'accuracy': baseline_accuracy,
            'correct': baseline_correct,
            'results': baseline_results
        },
        'optimized': {
            'accuracy': optimized_accuracy,
            'correct': optimized_correct,
            'results': optimized_results
        },
        'improvement': improvement
    }

    with open('quick_real_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Results saved to quick_real_test_results.json")
    print("📌 This shows REAL API performance (not simulated!)")

if __name__ == "__main__":
    main()