"""
Test GPT-5-mini with reasoning_effort="minimal" to compare against previous 77.7% accuracy.
This tests the production configuration that was implemented to reduce latency.
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
   - The title of the dissertation is italics.
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

def load_test_citations(limit=121):
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

def test_model_detailed(model_id, model_name, prompt_type, citations, reasoning_effort=None):
    """Test a model with detailed per-citation results."""
    prompt = BASELINE_PROMPT if prompt_type == 'baseline' else OPTIMIZED_PROMPT
    results = []

    print(f"\n📋 {prompt_type.upper()}:")
    print(f"  🤖 {model_name} - {prompt_type.upper()}", end="")
    if reasoning_effort:
        print(f" (reasoning_effort={reasoning_effort})")
    else:
        print()

    for i, item in enumerate(citations, 1):
        try:
            formatted_prompt = prompt.format(citation=item['citation'])

            # API Configuration with optional reasoning_effort
            api_params = {
                "model": model_id,
                "temperature": 1,  # GPT-5 requires temperature=1
                "messages": [{"role": "user", "content": formatted_prompt}]
            }

            # Add reasoning_effort only if specified
            if reasoning_effort:
                api_params["reasoning_effort"] = reasoning_effort

            response = client.chat.completions.create(**api_params)

            predicted = response.choices[0].message.content.strip().lower()
            # Extract just valid/invalid from potentially longer responses
            if 'valid' in predicted and 'invalid' not in predicted:
                predicted = 'valid'
            elif 'invalid' in predicted:
                predicted = 'invalid'
            else:
                # Default case - if neither clear, assume invalid
                predicted = 'invalid'
            correct = predicted == str(item['ground_truth'])

            results.append({
                "citation": item['citation'],
                "ground_truth": item['ground_truth'],
                "predicted": predicted == 'valid',
                "raw_response": response.choices[0].message.content.strip(),
                "correct": correct
            })

            if i % 20 == 0 or i <= 10:
                status = "✅" if correct else "❌"
                print(f"    {i:3d}. {status} {item['ground_truth']} vs {predicted}", flush=True)

        except Exception as e:
            print(f"    ERROR processing citation {i}: {e}", flush=True)
            results.append({
                "citation": item['citation'],
                "ground_truth": item['ground_truth'],
                "predicted": False,
                "raw_response": f"ERROR: {e}",
                "correct": False
            })

    accuracy = sum(1 for r in results if r['correct']) / len(results)
    correct = int(accuracy * len(citations))
    print(f"  Accuracy: {accuracy:.1%} ({correct}/{len(citations)})", flush=True)

    return results, accuracy

def main():
    print("🔍 GPT-5-mini MINIMAL REASONING TEST", flush=True)
    print("=" * 60, flush=True)
    print("Testing if reasoning_effort='minimal' maintains ~77.7% accuracy")
    print("=" * 60, flush=True)

    citations = load_test_citations(limit=121)
    print(f"\n📁 Loaded {len(citations)} citations for testing", flush=True)

    # Load previous results for comparison
    try:
        with open('detailed_121_test_summary_corrected.json', 'r') as f:
            previous_results = json.load(f)
        previous_accuracy = previous_results['accuracies']['GPT-5-mini_optimized']
        print(f"📊 Previous GPT-5-mini optimized accuracy: {previous_accuracy:.1%} ({int(previous_accuracy * 121)}/121)")
    except FileNotFoundError:
        print("⚠️  Could not load previous results for comparison")
        previous_accuracy = None

    print(f"\n" + "="*60)
    print(f"TESTING: GPT-5-mini with reasoning_effort='minimal'")
    print("="*60)

    # Test only the optimized prompt with minimal reasoning (production config)
    results, accuracy = test_model_detailed('gpt-5-mini', 'GPT-5-mini', 'optimized', citations, reasoning_effort='minimal')

    # Save detailed results
    filename = "GPT-5-mini_optimized_minimal_reasoning_121.jsonl"
    with open(filename, 'w') as f:
        for result in results:
            json.dump(result, f)
            f.write('\n')

    print(f"  📁 Detailed results saved to: {filename}")

    # Comparison with previous results
    print(f"\n" + "="*60)
    print("🏆 COMPARISON RESULTS")
    print("="*60)

    if previous_accuracy:
        diff = accuracy - previous_accuracy
        diff_pct = diff * 100
        correct_now = int(accuracy * 121)
        correct_before = int(previous_accuracy * 121)

        print(f"Previous GPT-5-mini optimized: {previous_accuracy:.1%} ({correct_before}/121)")
        print(f"Current GPT-5-mini minimal:    {accuracy:.1%} ({correct_now}/121)")
        print(f"Difference:                    {diff_pct:+.1f}% ({diff:+.1f} citations)")

        if diff > 0.02:  # More than 2% improvement
            print("🎉 MINIMAL REASONING PERFORMED BETTER!")
        elif diff < -0.02:  # More than 2% degradation
            print("⚠️  MINIMAL REASONING PERFORMED WORSE!")
        else:
            print("✅ MINIMAL REASONING MAINTAINED SIMILAR PERFORMANCE")
    else:
        print(f"GPT-5-mini with minimal reasoning: {accuracy:.1%} ({int(accuracy * 121)}/121)")

    # Save summary
    summary = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'test_type': 'GPT-5-MINI_MINIMAL_REASONING_TEST',
        'citations_tested': len(citations),
        'model': 'GPT-5-mini',
        'prompt_type': 'optimized',
        'reasoning_effort': 'minimal',
        'accuracy': accuracy,
        'correct_count': int(accuracy * 121),
        'previous_accuracy': previous_accuracy,
        'accuracy_difference': accuracy - previous_accuracy if previous_accuracy else None
    }

    with open('gpt5_mini_minimal_reasoning_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n📁 Summary saved to: gpt5_mini_minimal_reasoning_summary.json")
    print(f"🔥 TEST COMPLETED!")

if __name__ == "__main__":
    main()