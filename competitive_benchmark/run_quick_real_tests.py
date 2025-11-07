"""
QUICK REAL API TESTS - 4 models × 2 prompts = 8 combinations
Test 10 citations each for fast real results
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

Note: Italics in citations are indicated by underscores (e.g., _Journal Title_ represents italicized text).

Citation: {citation}"""

# Full production prompt from validator_prompt_optimized.txt
OPTIMIZED_PROMPT = """You are an APA 7th edition citation validator. Your task is to validate whether a given citation adheres to the APA 7th edition format rules.

━━━ INSTRUCTIONS ━━━

1. Analyze the components of the given citation to determine if they follow APA 7th edition guidelines. Different types of sources may have different formatting requirements.

2. For a web page citation, ensure it includes:
   - The author, which can be an organization like Wikipedia if no specific author is listed.
   - The date of publication in the order: year, month day.
   - The title of the page in italics.
   - The website name and then the URL.

3. For a book citation, verify:
   - The authors' last names followed by their initials.
   - The publication year in parentheses.
   - The title of the work in italics.
   - The publisher's name included at the end.

4. For an unpublished doctoral dissertation, ensure:
   - The author's last name and initials are provided.
   - The year of publication is in parentheses.
   - The title of the dissertation is in italics.
   - It is specified as an unpublished doctoral dissertation.
   - The institution's name is included where the dissertation was completed.

5. For a journal article, verify:
   - The authors' last names followed by their initials.
   - The publication year in parentheses.
   - The article title (not italicized).
   - The journal name in italics.
   - Volume number (italicized) and issue number (in parentheses, not italicized).
   - Page numbers and DOI or URL.

━━━ FORMATTING NOTES ━━━

IMPORTANT: In the input citations, italic formatting is indicated using markdown underscores.
Example: _Journal of Studies_ means the text should be italicized.

━━━ OUTPUT FORMAT ━━━

For this benchmark test, respond with ONLY ONE WORD: "valid" or "invalid"

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

            status = "✅" if predicted == item['ground_truth'] else "❌"
            print(f"    {i}. {status} {predicted} vs {item['ground_truth']}")

            time.sleep(0.5)  # Rate limiting

        except Exception as e:
            print(f"    {i}. ❌ ERROR: {e}")
            results.append({'correct': False})

    return results

def main():
    print("="*80)
    print("🚀 QUICK REAL API TESTS - 8 COMBINATIONS")
    print("4 models × 2 prompts = ACTUAL API CALLS ONLY")
    print("="*80)

    # Load test data
    citations = load_test_citations()
    print(f"📁 Testing {len(citations)} real citations")

    # Models to test
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
    print("🏆 REAL RESULTS RANKED")
    print(f"{'='*80}")

    ranked = sorted(all_results.items(), key=lambda x: x[1], reverse=True)
    for i, (name, accuracy) in enumerate(ranked, 1):
        model, prompt = name.split('_')
        print(f"{i}. {model:15s} + {prompt.upper():9s} → {accuracy:.1%}")

    # Save results
    results_data = {
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'test_type': 'REAL_API_TESTS',
        'citations_tested': len(citations),
        'models_tested': len(models),
        'combinations': len(ranked),
        'results': all_results,
        'ranking': ranked
    }

    with open('quick_real_test_results.json', 'w') as f:
        json.dump(results_data, f, indent=2)

    winner_name, winner_accuracy = ranked[0]
    winner_model, winner_prompt = winner_name.split('_')

    print(f"\n🥇 WINNER: {winner_model} with {winner_prompt} prompt")
    print(f"   Accuracy: {winner_accuracy:.1%} ({int(winner_accuracy * len(citations))}/{len(citations)})")
    print(f"📁 Results saved to quick_real_test_results.json")
    print(f"🔥 ALL DATA FROM REAL API CALLS!")

if __name__ == "__main__":
    main()