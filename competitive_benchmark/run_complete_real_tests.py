"""
FAST REAL API TESTS - Complete results for all models
Test all 121 citations with corrected GPT-5 parameters
"""
import json
import os
import time
from dotenv import load_dotenv

# Load OpenAI API key
load_dotenv('../backend/.env')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    print("❌ No OpenAI API key found")
    exit(1)

import openai
client = openai.OpenAI(api_key=OPENAI_API_KEY)

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
    """Load ALL test citations for complete results."""
    citations = []
    with open('validation_set.jsonl', 'r') as f:
        for line in f:
            item = json.loads(line)
            citations.append({
                'citation': item['citation'],
                'ground_truth': item['is_valid']
            })
    return citations

def test_model(model_id, model_name, prompt_type, citations):
    """Test a model with real API calls."""
    prompt = BASELINE_PROMPT if prompt_type == 'baseline' else OPTIMIZED_PROMPT
    results = []

    print(f"  🤖 {model_name} - {prompt_type.upper()}")

    for i, item in enumerate(citations, 1):
        try:
            formatted_prompt = prompt.format(citation=item['citation'])

            # Use max_completion_tokens for GPT-5 models, max_tokens for others
            if model_id.startswith('gpt-5'):
                response = client.chat.completions.create(
                    model=model_id,
                    max_completion_tokens=10,
                    temperature=1,  # GPT-5 requires temperature=1
                    messages=[{"role": "user", "content": formatted_prompt}]
                )
            else:
                response = client.chat.completions.create(
                    model=model_id,
                    max_tokens=10,
                    temperature=0,
                    messages=[{"role": "user", "content": formatted_prompt}]
                )

            predicted_text = response.choices[0].message.content.lower().strip()
            predicted = predicted_text == 'valid'

            results.append({
                'correct': predicted == item['ground_truth']
            })

            # Show progress every 20 citations
            if i % 20 == 0:
                correct_so_far = sum(1 for r in results if r['correct'])
                accuracy_so_far = correct_so_far / len(results)
                print(f"    Progress: {i}/{len(citations)} - Accuracy: {accuracy_so_far:.1%}")

            # Rate limiting
            time.sleep(0.2)

        except Exception as e:
            print(f"    {i}. ❌ ERROR: {e}")
            results.append({'correct': False})

    return results

def main():
    print("="*80)
    print("🚀 FAST REAL API TESTS - ALL 4 MODELS WORKING")
    print("Including corrected GPT-5 parameters")
    print("="*80)

    # Load test data
    citations = load_test_citations()
    print(f"📁 Testing {len(citations)} real citations")

    # Models to test (all working now)
    models = [
        ("gpt-4o", "GPT-4o"),
        ("gpt-4o-mini", "GPT-4o-mini"),
        ("gpt-5", "GPT-5"),
        ("gpt-5-mini", "GPT-5-mini")
    ]

    all_results = {}

    # Test all 8 combinations
    for model_id, model_name in models:
        print(f"\n{'='*60}")
        print(f"TESTING: {model_name}")
        print(f"{'='*60}")

        # Test baseline
        print(f"\n📋 BASELINE:")
        baseline_results = test_model(model_id, model_name, 'baseline', citations)
        baseline_correct = sum(1 for r in baseline_results if r['correct'])
        baseline_accuracy = baseline_correct / len(baseline_results)
        all_results[f"{model_name}_baseline"] = baseline_accuracy
        print(f"  Accuracy: {baseline_accuracy:.1%} ({baseline_correct}/{len(baseline_results)})")

        # Test optimized
        print(f"\n🚀 OPTIMIZED:")
        optimized_results = test_model(model_id, model_name, 'optimized', citations)
        optimized_correct = sum(1 for r in optimized_results if r['correct'])
        optimized_accuracy = optimized_correct / len(optimized_results)
        all_results[f"{model_name}_optimized"] = optimized_accuracy
        print(f"  Accuracy: {optimized_accuracy:.1%} ({optimized_correct}/{len(optimized_results)})")

        # Show improvement
        improvement = optimized_accuracy - baseline_accuracy
        print(f"  📊 Improvement: {improvement:+.1%}")

    # Rank all results
    print(f"\n{'='*80}")
    print("🏆 COMPLETE RESULTS - ALL 8 COMBINATIONS RANKED")
    print(f"{'='*80}")

    ranked = sorted(all_results.items(), key=lambda x: x[1], reverse=True)
    for i, (name, accuracy) in enumerate(ranked, 1):
        model, prompt = name.split('_')
        print(f"{i}. {model:15s} + {prompt.upper():9s} → {accuracy:.1%}")

    # Save results
    results_data = {
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'test_type': 'COMPLETE_REAL_API_TESTS_WITH_GPT5',
        'citations_tested': len(citations),
        'models_tested': len(models),
        'combinations': len(ranked),
        'results': all_results,
        'ranking': ranked
    }

    with open('complete_real_test_results_with_gpt5.json', 'w') as f:
        json.dump(results_data, f, indent=2)

    winner_name, winner_accuracy = ranked[0]
    winner_model, winner_prompt = winner_name.split('_')

    print(f"\n🥇 WINNER: {winner_model} with {winner_prompt} prompt")
    print(f"   Accuracy: {winner_accuracy:.1%} ({int(winner_accuracy * len(citations))}/{len(citations)})")
    print(f"📁 Results saved to complete_real_test_results_with_gpt5.json")
    print(f"🔥 ALL 4 MODELS TESTED WITH REAL API CALLS!")

if __name__ == "__main__":
    main()