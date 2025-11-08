"""
FOCUSED TEST: Only GPT-5-mini with reasoning_effort="minimal"
Compares against existing 77.7% baseline from previous tests
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

# Same optimized prompt used in previous tests
OPTIMIZED_PROMPT = """As an expert academic librarian specializing in citation validation, evaluate this citation according to APA 7th edition standards.

Consider:
- Required elements completeness (author, title, source, date)
- Format accuracy and consistency
- Source credibility and accessibility
- DOI/publisher information when applicable

Respond with exactly one word: "valid" or "invalid"

Citation: {citation}"""

def load_test_citations():
    """Load test citations."""
    citations = []
    with open('validation_set.jsonl', 'r') as f:
        for line in f:
            item = json.loads(line)
            citations.append({
                'citation': item['citation'],
                'ground_truth': item['is_valid']
            })
    return citations

def main():
    print("="*80, flush=True)
    print("🎯 FOCUSED TEST: GPT-5-mini + reasoning_effort='minimal'", flush=True)
    print("Testing if minimal reasoning maintains 77.7% accuracy", flush=True)
    print("="*80, flush=True)

    # Load test data
    citations = load_test_citations()
    print(f"📁 Testing {len(citations)} citations", flush=True)

    # Load previous GPT-5-mini optimized results for comparison
    try:
        with open('detailed_121_test_summary_corrected.json', 'r') as f:
            previous_results = json.load(f)
        previous_accuracy = previous_results['accuracies']['GPT-5-mini_optimized']
        previous_correct = int(previous_accuracy * len(citations))
        print(f"📊 Previous GPT-5-mini optimized: {previous_accuracy:.1%} ({previous_correct}/{len(citations)})", flush=True)
    except FileNotFoundError:
        print("⚠️  Could not load previous results", flush=True)
        previous_accuracy = None
        previous_correct = None

    print(f"\n🚀 Testing GPT-5-mini with reasoning_effort='minimal'...", flush=True)

    results = []
    start_time = time.time()

    for i, item in enumerate(citations, 1):
        try:
            formatted_prompt = OPTIMIZED_PROMPT.format(citation=item['citation'])

            # API call with reasoning_effort="minimal"
            response = client.chat.completions.create(
                model="gpt-5-mini",
                max_completion_tokens=10,
                temperature=1,
                reasoning_effort="minimal",  # The key parameter we're testing
                messages=[{"role": "user", "content": formatted_prompt}]
            )

            predicted_text = response.choices[0].message.content.lower().strip()
            predicted = predicted_text == 'valid'
            correct = predicted == item['ground_truth']

            results.append({
                'citation_index': i,
                'correct': correct,
                'predicted': predicted,
                'ground_truth': item['ground_truth'],
                'raw_response': response.choices[0].message.content.strip()
            })

            # Progress updates
            if i % 20 == 0 or i <= 10:
                correct_so_far = sum(1 for r in results if r['correct'])
                accuracy_so_far = correct_so_far / len(results)
                status = "✅" if correct else "❌"
                print(f"  {i:3d}. {status} Accuracy so far: {accuracy_so_far:.1%}")

            # Rate limiting
            time.sleep(0.2)

        except Exception as e:
            print(f"  {i:3d}. ❌ ERROR: {e}")
            results.append({
                'citation_index': i,
                'correct': False,
                'predicted': False,
                'ground_truth': item['ground_truth'],
                'raw_response': f"ERROR: {e}"
            })

    end_time = time.time()

    # Calculate final results
    correct_count = sum(1 for r in results if r['correct'])
    accuracy = correct_count / len(results)

    print(f"\n{'='*80}")
    print("🏆 RESULTS")
    print(f"{'='*80}")

    print(f"GPT-5-mini + minimal reasoning: {accuracy:.1%} ({correct_count}/{len(results)})")
    print(f"Test completed in {end_time - start_time:.1f} seconds")

    # Comparison analysis
    if previous_accuracy:
        diff = accuracy - previous_accuracy
        diff_citations = int(diff * len(citations))
        diff_pct = diff * 100

        print(f"\n📊 COMPARISON:")
        print(f"Previous optimized:     {previous_accuracy:.1%} ({previous_correct}/{len(citations)})")
        print(f"Current minimal:       {accuracy:.1%} ({correct_count}/{len(citations)})")
        print(f"Difference:            {diff_pct:+.1f}% ({diff_citations:+d} citations)")

        if diff > 0.02:
            print("🎉 MINIMAL REASONING PERFORMED BETTER!")
        elif diff < -0.02:
            print("⚠️  MINIMAL REASONING PERFORMED WORSE!")
        else:
            print("✅ MINIMAL REASONING MAINTAINED SIMILAR PERFORMANCE")

        # Performance impact analysis
        if abs(diff) <= 0.02:
            print(f"💡 CONCLUSION: reasoning_effort='minimal' successfully reduces latency while maintaining accuracy!")
        elif diff > 0.02:
            print(f"💡 CONCLUSION: minimal reasoning actually improved performance!")
        else:
            print(f"💡 CONCLUSION: minimal reasoning hurts accuracy - reconsider production use")

    # Save results
    detailed_file = "gpt5_mini_minimal_reasoning_detailed.jsonl"
    summary_file = "gpt5_mini_minimal_reasoning_summary.json"

    # Save detailed results
    with open(detailed_file, 'w') as f:
        for result in results:
            json.dump(result, f)
            f.write('\n')

    # Save summary
    summary = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'test_type': 'GPT-5-mini_minimal_reasoning_only',
        'model': 'gpt-5-mini',
        'prompt_type': 'optimized',
        'reasoning_effort': 'minimal',
        'citations_tested': len(citations),
        'accuracy': accuracy,
        'correct_count': correct_count,
        'previous_accuracy': previous_accuracy,
        'accuracy_difference': diff if previous_accuracy else None,
        'test_duration_seconds': end_time - start_time,
        'detailed_file': detailed_file
    }

    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n📁 Detailed results: {detailed_file}")
    print(f"📁 Summary results: {summary_file}")
    print(f"🔥 TEST COMPLETED!")

if __name__ == "__main__":
    main()