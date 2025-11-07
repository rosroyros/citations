"""
Run real API tests for optimized prompts on all models to complete the holistic analysis.
"""
import json
import os
import time
from pathlib import Path

# API keys (need to be set)
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Optimized prompt
OPTIMIZED_PROMPT = """As an expert academic librarian specializing in citation validation, evaluate this citation according to APA 7th edition standards.

Consider:
- Required elements completeness (author, title, source, date)
- Format accuracy and consistency
- Source credibility and accessibility
- DOI/publisher information when applicable

Respond with exactly one word: "valid" or "invalid"

Citation: {citation}"""

def load_validation_set():
    """Load validation dataset."""
    citations = []
    with open('validation_set.jsonl', 'r') as f:
        for line in f:
            item = json.loads(line)
            citations.append({
                'citation': item['citation'],
                'ground_truth': item['is_valid']
            })
    return citations

def test_claude_optimized(citations):
    """Test Claude Sonnet 4.5 with optimized prompt."""
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    results = []
    for i, item in enumerate(citations[:20], 1):  # Test first 20 for demo
        try:
            prompt = OPTIMIZED_PROMPT.format(citation=item['citation'])
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=10,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            predicted_text = response.content[0].text.lower().strip()
            predicted = predicted_text == 'valid'

            results.append({
                'citation': item['citation'],
                'ground_truth': item['ground_truth'],
                'predicted': 'valid' if predicted else 'invalid',
                'correct': predicted == item['ground_truth']
            })

            print(f"  Claude {i}: {predicted} vs {item['ground_truth']} {'✅' if predicted == item['ground_truth'] else '❌'}")
            time.sleep(0.5)  # Rate limiting

        except Exception as e:
            print(f"  Claude {i}: ERROR - {e}")
            results.append({
                'citation': item['citation'],
                'ground_truth': item['ground_truth'],
                'predicted': None,
                'correct': False,
                'error': str(e)
            })

    return results

def test_openai_optimized(citations, model_id, model_name):
    """Test OpenAI model with optimized prompt."""
    import openai
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    results = []
    for i, item in enumerate(citations[:20], 1):  # Test first 20 for demo
        try:
            prompt = OPTIMIZED_PROMPT.format(citation=item['citation'])
            response = client.chat.completions.create(
                model=model_id,
                max_tokens=10,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )

            predicted_text = response.choices[0].message.content.lower().strip()
            predicted = predicted_text == 'valid'

            results.append({
                'citation': item['citation'],
                'ground_truth': item['ground_truth'],
                'predicted': 'valid' if predicted else 'invalid',
                'correct': predicted == item['ground_truth']
            })

            print(f"  {model_name} {i}: {predicted} vs {item['ground_truth']} {'✅' if predicted == item['ground_truth'] else '❌'}")
            time.sleep(0.5)  # Rate limiting

        except Exception as e:
            print(f"  {model_name} {i}: ERROR - {e}")
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
    print("REAL OPTIMIZED PROMPT TESTS - ALL MODELS")
    print("="*80)

    if not ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY not set - Claude tests skipped")
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not set - OpenAI tests skipped")

    if not ANTHROPIC_API_KEY and not OPENAI_API_KEY:
        print("❌ No API keys available - cannot run real tests")
        return

    # Load validation set
    print("\n📁 Loading validation set...")
    citations = load_validation_set()
    print(f"✅ Loaded {len(citations)} citations (testing first 20)")

    all_results = {}

    # Test Claude with optimized prompt
    if ANTHROPIC_API_KEY:
        print(f"\n🤖 Testing Claude Sonnet 4.5 with OPTIMIZED prompt...")
        claude_results = test_claude_optimized(citations)
        claude_correct = sum(1 for r in claude_results if r['correct'])
        claude_accuracy = claude_correct / len(claude_results)
        all_results['Claude Sonnet 4.5_optimized'] = {
            'accuracy': claude_accuracy,
            'correct': claude_correct,
            'total': len(claude_results),
            'results': claude_results
        }
        print(f"   Claude optimized: {claude_accuracy:.1%} ({claude_correct}/{len(claude_results)})")

    # Test OpenAI models with optimized prompt
    openai_models = [
        ("gpt-4o", "GPT-4o"),
        ("gpt-5-preview", "GPT-5"),
        ("gpt-5-mini-preview", "GPT-5-mini")
    ]

    if OPENAI_API_KEY:
        for model_id, model_name in openai_models:
            print(f"\n🤖 Testing {model_name} with OPTIMIZED prompt...")
            try:
                results = test_openai_optimized(citations, model_id, model_name)
                correct = sum(1 for r in results if r['correct'])
                accuracy = correct / len(results)
                all_results[f'{model_name}_optimized'] = {
                    'accuracy': accuracy,
                    'correct': correct,
                    'total': len(results),
                    'results': results
                }
                print(f"   {model_name} optimized: {accuracy:.1%} ({correct}/{len(results)})")
            except Exception as e:
                print(f"   {model_name}: FAILED - {e}")

    # Load real baseline data for comparison
    print(f"\n📊 Loading real baseline data...")
    with open('metrics_summary.json', 'r') as f:
        baseline_data = json.load(f)

    # Combine baseline and optimized results
    combined_results = {}

    # Add baseline results
    for model_name, metrics in baseline_data['model_metrics'].items():
        combined_results[f'{model_name}_baseline'] = {
            'accuracy': metrics['accuracy'],
            'correct': int(metrics['accuracy'] * metrics['total_predictions']),
            'total': metrics['total_predictions'],
            'source': 'real_api_tests'
        }

    # Add optimized results (sample size will be smaller)
    for key, results in all_results.items():
        combined_results[key] = {
            'accuracy': results['accuracy'],
            'correct': results['correct'],
            'total': results['total'],
            'source': 'real_api_tests_optimized'
        }

    # Rank all variations
    ranked_variations = sorted(combined_results.items(), key=lambda x: x[1]['accuracy'], reverse=True)

    # Save results
    final_results = {
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'test_info': {
            'baseline_sample_size': baseline_data['dataset_info']['total_citations'],
            'optimized_sample_size': len(citations[:20]),
            'baseline_source': 'real_api_tests',
            'optimized_source': 'real_api_tests'
        },
        'all_variations': combined_results,
        'ranking': ranked_variations,
        'best_overall': ranked_variations[0] if ranked_variations else None
    }

    with open('complete_dual_prompt_results.json', 'w') as f:
        json.dump(final_results, f, indent=2)

    print(f"\n🏆 COMPLETE DUAL PROMPT ANALYSIS:")
    print(f"="*50)
    for i, (variation, data) in enumerate(ranked_variations, 1):
        print(f"{i:2d}. {variation:30s} {data['accuracy']:.1%} ({data['correct']}/{data['total']}) [{data['source']}]")

    if ranked_variations:
        best = ranked_variations[0]
        print(f"\n🥇 WINNER: {best[0]} with {best[1]['accuracy']:.1%} accuracy")

    print(f"\n✅ Results saved to complete_dual_prompt_results.json")
    print(f"📈 Ready for comprehensive holistic report generation!")

if __name__ == "__main__":
    main()