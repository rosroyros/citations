"""
Test 30 citations with detailed per-citation results to investigate GPT-5 behavior.
Save full results: citation, ground_truth, predicted, model response, correct.
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

def load_test_citations(limit=30):
    """Load first N test citations."""
    citations = []
    with open('validation_set.jsonl', 'r') as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            item = json.loads(line)
            citations.append({
                'citation': item['citation'],
                'ground_truth': item['is_valid']
            })
    return citations

def test_model_detailed(model_id, model_name, prompt_type, citations):
    """Test a model with real API calls and save detailed results."""
    prompt = BASELINE_PROMPT if prompt_type == 'baseline' else OPTIMIZED_PROMPT
    results = []

    print(f"\n🤖 Testing {model_name} - {prompt_type.upper()}")

    for i, item in enumerate(citations, 1):
        try:
            formatted_prompt = prompt.format(citation=item['citation'])

            # Use appropriate parameters for each model
            # No token limits - let models respond naturally like ChatGPT
            if model_id.startswith('gpt-5'):
                response = client.chat.completions.create(
                    model=model_id,
                    temperature=1,  # GPT-5 requires temperature=1
                    messages=[{"role": "user", "content": formatted_prompt}]
                )
            else:
                response = client.chat.completions.create(
                    model=model_id,
                    temperature=0,  # Deterministic for GPT-4 models
                    messages=[{"role": "user", "content": formatted_prompt}]
                )

            raw_response = response.choices[0].message.content
            predicted_text = raw_response.lower().strip()
            predicted = predicted_text == 'valid'
            is_correct = predicted == item['ground_truth']

            result = {
                'citation': item['citation'],
                'ground_truth': item['ground_truth'],
                'predicted': predicted,
                'raw_response': raw_response,
                'correct': is_correct
            }
            results.append(result)

            status = "✅" if is_correct else "❌"
            print(f"  {i:2d}. {status} GT:{item['ground_truth']} Pred:{predicted} Raw:'{raw_response}'")

            time.sleep(0.5)  # Rate limiting

        except Exception as e:
            print(f"  {i:2d}. ❌ ERROR: {e}")
            results.append({
                'citation': item['citation'],
                'ground_truth': item['ground_truth'],
                'predicted': None,
                'raw_response': None,
                'correct': False,
                'error': str(e)
            })

    # Calculate accuracy
    correct_count = sum(1 for r in results if r['correct'])
    accuracy = correct_count / len(results) if results else 0

    print(f"  📊 Accuracy: {accuracy:.1%} ({correct_count}/{len(results)})")

    return results, accuracy

def main():
    print("="*80)
    print("🔍 DETAILED TEST - 30 Citations per Combination")
    print("4 models × 2 prompts with full per-citation results")
    print("="*80)

    # Load test data
    citations = load_test_citations(limit=30)
    print(f"\n📁 Loaded {len(citations)} citations for testing")

    # Models to test
    models = [
        ("gpt-4o", "GPT-4o"),
        ("gpt-4o-mini", "GPT-4o-mini"),
        ("gpt-5", "GPT-5"),
        ("gpt-5-mini", "GPT-5-mini")
    ]

    all_results = {}
    all_accuracies = {}

    # Test all combinations
    for model_id, model_name in models:
        print(f"\n{'='*60}")
        print(f"MODEL: {model_name}")
        print(f"{'='*60}")

        # Test baseline
        baseline_results, baseline_acc = test_model_detailed(
            model_id, model_name, 'baseline', citations
        )

        # Save to JSONL
        baseline_file = f"{model_id}_baseline_detailed.jsonl"
        with open(baseline_file, 'w') as f:
            for result in baseline_results:
                f.write(json.dumps(result) + '\n')
        print(f"  💾 Saved: {baseline_file}")

        all_results[f"{model_name}_baseline"] = baseline_results
        all_accuracies[f"{model_name}_baseline"] = baseline_acc

        # Test optimized
        optimized_results, optimized_acc = test_model_detailed(
            model_id, model_name, 'optimized', citations
        )

        # Save to JSONL
        optimized_file = f"{model_id}_optimized_detailed.jsonl"
        with open(optimized_file, 'w') as f:
            for result in optimized_results:
                f.write(json.dumps(result) + '\n')
        print(f"  💾 Saved: {optimized_file}")

        all_results[f"{model_name}_optimized"] = optimized_results
        all_accuracies[f"{model_name}_optimized"] = optimized_acc

        # Show improvement
        improvement = optimized_acc - baseline_acc
        print(f"  📈 Improvement: {improvement:+.1%}")

    # Final summary
    print(f"\n{'='*80}")
    print("📊 FINAL RESULTS - ALL COMBINATIONS")
    print(f"{'='*80}")

    ranked = sorted(all_accuracies.items(), key=lambda x: x[1], reverse=True)
    for i, (name, acc) in enumerate(ranked, 1):
        model, prompt = name.split('_')
        correct = int(acc * len(citations))
        print(f"{i}. {model:15s} + {prompt.upper():9s} → {acc:.1%} ({correct}/{len(citations)})")

    # Save summary
    summary = {
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'test_type': 'DETAILED_30_CITATION_TEST',
        'citations_tested': len(citations),
        'models_tested': len(models),
        'combinations': len(ranked),
        'accuracies': all_accuracies,
        'ranking': ranked
    }

    with open('detailed_30_test_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n✅ Test complete!")
    print(f"📁 Summary: detailed_30_test_summary.json")
    print(f"📁 Per-citation results: *_detailed.jsonl files")

    # Investigate GPT-5 identical results
    if all_accuracies.get('GPT-5_baseline') == all_accuracies.get('GPT-5_optimized'):
        print(f"\n⚠️  WARNING: GPT-5 baseline and optimized have IDENTICAL accuracy!")
        print(f"   This suggests the prompt may not be affecting GPT-5's responses.")
        print(f"   Check the detailed JSONL files to see actual responses.")

if __name__ == "__main__":
    main()
