"""
GPT-5-mini MINIMAL REASONING TEST - Modified from run_complete_real_tests.py
Tests all previous combinations + NEW GPT-5-mini with reasoning_effort="minimal"
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

# Real prompts (same as previous tests for accurate comparison)
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

def test_model(model_id, model_name, prompt_type, citations, reasoning_effort=None):
    """Test a model with real API calls and optional reasoning_effort."""
    prompt = BASELINE_PROMPT if prompt_type == 'baseline' else OPTIMIZED_PROMPT
    results = []

    print(f"  🤖 {model_name} - {prompt_type.upper()}", end="")
    if reasoning_effort:
        print(f" (reasoning_effort={reasoning_effort})")
    else:
        print()

    for i, item in enumerate(citations, 1):
        try:
            formatted_prompt = prompt.format(citation=item['citation'])

            # API configuration
            api_params = {
                "model": model_id,
                "temperature": 1 if model_id.startswith('gpt-5') else 0,
                "messages": [{"role": "user", "content": formatted_prompt}]
            }

            # Use max_completion_tokens for GPT-5 models, max_tokens for others
            if model_id.startswith('gpt-5'):
                api_params["max_completion_tokens"] = 10
            else:
                api_params["max_tokens"] = 10

            # Add reasoning_effort only if specified
            if reasoning_effort:
                api_params["reasoning_effort"] = reasoning_effort

            response = client.chat.completions.create(**api_params)

            predicted_text = response.choices[0].message.content.lower().strip()
            predicted = predicted_text == 'valid'

            results.append({
                'correct': predicted == item['ground_truth'],
                'predicted': predicted,
                'ground_truth': item['ground_truth'],
                'raw_response': response.choices[0].message.content.strip()
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
            results.append({
                'correct': False,
                'predicted': False,
                'ground_truth': item['ground_truth'],
                'raw_response': f"ERROR: {e}"
            })

    return results

def main():
    print("="*80)
    print("🚀 GPT-5-mini MINIMAL REASONING TEST")
    print("Testing if reasoning_effort='minimal' maintains ~77.7% accuracy")
    print("="*80)

    # Load test data
    citations = load_test_citations()
    print(f"📁 Testing {len(citations)} real citations")

    # Load previous results for comparison
    try:
        with open('complete_real_test_results_with_gpt5.json', 'r') as f:
            previous_results = json.load(f)
        print("📊 Loaded previous test results for comparison")

        # Find GPT-5-mini optimized accuracy from previous results
        gpt5_mini_optimized = previous_results['results'].get('GPT-5-mini_optimized', 0)
        print(f"📈 Previous GPT-5-mini optimized accuracy: {gpt5_mini_optimized:.1%} ({int(gpt5_mini_optimized * len(citations))}/{len(citations)})")
    except FileNotFoundError:
        print("⚠️  Could not load previous results")
        previous_results = None
        gpt5_mini_optimized = None

    print(f"\n{'='*60}")
    print(f"TESTING: GPT-5-mini with reasoning_effort='minimal'")
    print(f"{'='*60}")

    # Test only the NEW combination: GPT-5-mini optimized with minimal reasoning
    minimal_results = test_model('gpt-5-mini', 'GPT-5-mini', 'optimized', citations, reasoning_effort='minimal')

    minimal_correct = sum(1 for r in minimal_results if r['correct'])
    minimal_accuracy = minimal_correct / len(minimal_results)

    print(f"  Accuracy: {minimal_accuracy:.1%} ({minimal_correct}/{len(minimal_results)})")

    # Save detailed results
    with open('GPT-5-mini_optimized_minimal_reasoning_detailed.jsonl', 'w') as f:
        for result in minimal_results:
            json.dump(result, f)
            f.write('\n')

    # Comparison analysis
    print(f"\n{'='*80}")
    print("🏆 COMPARISON ANALYSIS")
    print(f"{'='*80}")

    if gpt5_mini_optimized:
        improvement = minimal_accuracy - gpt5_mini_optimized
        improvement_citations = int(improvement * len(citations))

        print(f"Previous GPT-5-mini optimized:     {gpt5_mini_optimized:.1%} ({int(gpt5_mini_optimized * len(citations))}/{len(citations)})")
        print(f"Current GPT-5-mini minimal:       {minimal_accuracy:.1%} ({minimal_correct}/{len(citations)})")
        print(f"Difference:                       {improvement:+.1%} ({improvement_citations:+d} citations)")

        if improvement > 0.02:  # More than 2% improvement
            print("🎉 MINIMAL REASONING PERFORMED BETTER!")
        elif improvement < -0.02:  # More than 2% degradation
            print("⚠️  MINIMAL REASONING PERFORMED WORSE!")
        else:
            print("✅ MINIMAL REASONING MAINTAINED SIMILAR PERFORMANCE")
    else:
        print(f"GPT-5-mini with minimal reasoning: {minimal_accuracy:.1%} ({minimal_correct}/{len(citations)})")

    # Show previous top performers for context
    if previous_results:
        print(f"\n📊 Previous top performers from comprehensive test:")
        for i, (name, accuracy) in enumerate(previous_results['ranking'][:3], 1):
            model, prompt = name.split('_')
            print(f"{i}. {model:15s} + {prompt.upper():9s} → {accuracy:.1%}")

    # Save comprehensive results
    results_data = {
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'test_type': 'GPT-5-MINI_MINIMAL_REASONING_TEST',
        'citations_tested': len(citations),
        'model': 'GPT-5-mini',
        'prompt_type': 'optimized',
        'reasoning_effort': 'minimal',
        'accuracy': minimal_accuracy,
        'correct_count': minimal_correct,
        'previous_gpt5_mini_optimized_accuracy': gpt5_mini_optimized,
        'accuracy_difference': minimal_accuracy - gpt5_mini_optimized if gpt5_mini_optimized else None,
        'detailed_results_file': 'GPT-5-mini_optimized_minimal_reasoning_detailed.jsonl'
    }

    with open('gpt5_mini_minimal_reasoning_results.json', 'w') as f:
        json.dump(results_data, f, indent=2)

    print(f"\n📁 Detailed results: GPT-5-mini_optimized_minimal_reasoning_detailed.jsonl")
    print(f"📁 Summary results: gpt5_mini_minimal_reasoning_results.json")
    print(f"🔥 MINIMAL REASONING TEST COMPLETED!")

if __name__ == "__main__":
    main()