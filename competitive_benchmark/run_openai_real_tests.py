"""
RUN REAL API TESTS - OPENAI MODELS ONLY
Test GPT-4o, GPT-5, GPT-5-mini with both baseline and optimized prompts
NO SIMULATED DATA - ACTUAL API CALLS ONLY
"""
import json
import os
import time
from pathlib import Path

# Load OpenAI API key from .env
with open('../backend/.env', 'r') as f:
    env_content = f.read()
    for line in env_content.split('\n'):
        if line.startswith('OPENAI_API_KEY=') and '=' in line:
            OPENAI_API_KEY = line.split('=', 1)[1].strip()
            break
    else:
        OPENAI_API_KEY = None

if not OPENAI_API_KEY or OPENAI_API_KEY == 'your_openai_key_here':
    print("❌ No valid OpenAI API key found in ../backend/.env")
    print("Please add your real OpenAI API key to the .env file")
    exit(1)

print(f"✅ Found OpenAI API key")

# Real prompts
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

def load_test_citations():
    """Load real test citations."""
    citations = []
    with open('validation_set.jsonl', 'r') as f:
        for line in f:
            item = json.loads(line)
            citations.append({
                'citation': item['citation'],
                'ground_truth': item['is_valid']
            })
    return citations

def test_openai_model_real(citations, model_id, model_name, prompt_type):
    """Test OpenAI model with real API calls."""
    import openai
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    prompt = BASELINE_PROMPT if prompt_type == 'baseline' else OPTIMIZED_PROMPT
    results = []

    print(f"  🤖 {model_name} - {prompt_type.upper()} prompt")
    print(f"  Testing {len(citations)} citations...")

    for i, item in enumerate(citations, 1):
        try:
            formatted_prompt = prompt.format(citation=item['citation'])
            response = client.chat.completions.create(
                model=model_id,
                max_tokens=10,
                temperature=0,
                messages=[{"role": "user", "content": formatted_prompt}]
            )

            predicted_text = response.choices[0].message.content.lower().strip()
            predicted = predicted_text == 'valid'

            results.append({
                'citation': item['citation'],
                'ground_truth': item['ground_truth'],
                'predicted': 'valid' if predicted else 'invalid',
                'correct': predicted == item['ground_truth']
            })

            # Show progress every 10 citations
            if i % 10 == 0:
                correct_so_far = sum(1 for r in results if r['correct'])
                accuracy_so_far = correct_so_far / len(results)
                print(f"    Progress: {i}/{len(citations)} - Accuracy: {accuracy_so_far:.1%}")

            # Rate limiting
            time.sleep(0.3)

        except Exception as e:
            print(f"    ❌ Error on citation {i}: {e}")
            results.append({
                'citation': item['citation'],
                'ground_truth': item['ground_truth'],
                'predicted': None,
                'correct': False,
                'error': str(e)
            })

    return results

def main():
    print("="*80)
    print("🚀 REAL OPENAI API BENCHMARK")
    print("Testing GPT models with REAL API calls - NO SIMULATION")
    print("="*80)

    # Load test data
    print("\n📁 Loading test citations...")
    citations = load_test_citations()
    test_sample = citations[:30]  # Test 30 citations for real results
    print(f"✅ Using sample of {len(test_sample)} citations for real testing")

    all_results = {}

    # OpenAI models to test
    models_to_test = [
        ("gpt-4o", "GPT-4o"),
        ("gpt-4o-mini", "GPT-4o-mini"),
        ("gpt-5-preview", "GPT-5"),
        ("gpt-5-mini-preview", "GPT-5-mini")
    ]

    # Test all 8 combinations (4 models × 2 prompts)
    for model_id, model_name in models_to_test:
        print(f"\n{'='*60}")
        print(f"TESTING: {model_name}")
        print(f"{'='*60}")

        # Test baseline prompt
        print(f"\n📋 BASELINE PROMPT")
        baseline_results = test_openai_model_real(test_sample, model_id, model_name, "baseline")

        if baseline_results:
            baseline_correct = sum(1 for r in baseline_results if r['correct'])
            baseline_accuracy = baseline_correct / len(baseline_results)
            all_results[f"{model_name}_baseline"] = {
                'accuracy': baseline_accuracy,
                'correct': baseline_correct,
                'total': len(baseline_results),
                'results': baseline_results
            }
            print(f"  ✅ Baseline: {baseline_accuracy:.1%} ({baseline_correct}/{len(baseline_results)})")

        # Test optimized prompt
        print(f"\n🚀 OPTIMIZED PROMPT")
        optimized_results = test_openai_model_real(test_sample, model_id, model_name, "optimized")

        if optimized_results:
            optimized_correct = sum(1 for r in optimized_results if r['correct'])
            optimized_accuracy = optimized_correct / len(optimized_results)
            all_results[f"{model_name}_optimized"] = {
                'accuracy': optimized_accuracy,
                'correct': optimized_correct,
                'total': len(optimized_results),
                'results': optimized_results
            }
            print(f"  ✅ Optimized: {optimized_accuracy:.1%} ({optimized_correct}/{len(optimized_results)})")

        # Show improvement
        if baseline_results and optimized_results:
            improvement = optimized_accuracy - baseline_accuracy
            print(f"  📊 Improvement: {improvement:+.1%} ({improvement*100:+.1f} percentage points)")

    # Rank all real results
    print(f"\n{'='*80}")
    print("🏆 REAL RESULTS - ALL 6 COMBINATIONS RANKED")
    print(f"{'='*80}")

    ranked_results = sorted(all_results.items(), key=lambda x: x[1]['accuracy'], reverse=True)

    for i, (name, data) in enumerate(ranked_results, 1):
        model, prompt = name.split('_')
        print(f"{i}. {model:15s} + {prompt.upper():9s} → {data['accuracy']:.1%} ({data['correct']}/{data['total']})")

    # Save real results
    real_results = {
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'test_type': 'REAL_OPENAI_API_TESTS_ONLY',
        'sample_size': len(test_sample),
        'models_tested': [name for _, name in models_to_test],
        'prompts_tested': ['baseline', 'optimized'],
        'total_combinations': len(ranked_results),
        'all_results': all_results,
        'ranking': ranked_results,
        'winner': ranked_results[0] if ranked_results else None
    }

    with open('real_openai_benchmark_results.json', 'w') as f:
        json.dump(real_results, f, indent=2)

    if ranked_results:
        winner = ranked_results[0]
        winner_model, winner_prompt = winner[0].split('_')
        print(f"\n🥇 REAL WINNER: {winner_model} with {winner_prompt} prompt")
        print(f"   Accuracy: {winner[1]['accuracy']:.1%} ({winner[1]['correct']}/{winner[1]['total']})")
        print(f"   Based on {len(test_sample)} real citation tests")

    print(f"\n✅ REAL OpenAI benchmark complete!")
    print(f"📁 Results saved to real_openai_benchmark_results.json")
    print(f"🔥 ALL DATA FROM REAL API CALLS - NO SIMULATION")

if __name__ == "__main__":
    main()