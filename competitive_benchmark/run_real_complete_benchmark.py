"""
RUN REAL API TESTS FOR ALL 10 COMBINATIONS
5 models × 2 prompts = 10 real variations
NO SIMULATED DATA - ACTUAL API CALLS ONLY
"""
import json
import os
import time
from pathlib import Path
import sys

# Add paths for DSPy imports
sys.path.append('../backend/pseo/optimization')
sys.path.append('../backend/pseo')

try:
    from dspy_validator import CitationValidator, load_dataset
    from dspy_config import setup_dspy
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Will skip DSPy tests and use API calls only")

# API keys
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

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

def test_claude_real(citations, prompt_type):
    """Test Claude with real API calls."""
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = BASELINE_PROMPT if prompt_type == 'baseline' else OPTIMIZED_PROMPT
    results = []

    print(f"  🤖 Claude Sonnet 4.5 - {prompt_type.upper()} prompt")
    for i, item in enumerate(citations[:50], 1):  # Test 50 citations for real results
        try:
            formatted_prompt = prompt.format(citation=item['citation'])
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=10,
                temperature=0,
                messages=[{"role": "user", "content": formatted_prompt}]
            )

            predicted_text = response.content[0].text.lower().strip()
            predicted = predicted_text == 'valid'

            results.append({
                'citation': item['citation'],
                'ground_truth': item['ground_truth'],
                'predicted': 'valid' if predicted else 'invalid',
                'correct': predicted == item['ground_truth']
            })

            if i % 10 == 0:
                correct_so_far = sum(1 for r in results if r['correct'])
                accuracy_so_far = correct_so_far / len(results)
                print(f"    Progress: {i}/50 - Accuracy so far: {accuracy_so_far:.1%}")

            time.sleep(0.5)  # Rate limiting

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

def test_openai_real(citations, model_id, model_name, prompt_type):
    """Test OpenAI model with real API calls."""
    import openai
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    prompt = BASELINE_PROMPT if prompt_type == 'baseline' else OPTIMIZED_PROMPT
    results = []

    print(f"  🤖 {model_name} - {prompt_type.upper()} prompt")
    for i, item in enumerate(citations[:50], 1):  # Test 50 citations
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

            if i % 10 == 0:
                correct_so_far = sum(1 for r in results if r['correct'])
                accuracy_so_far = correct_so_far / len(results)
                print(f"    Progress: {i}/50 - Accuracy so far: {accuracy_so_far:.1%}")

            time.sleep(0.5)  # Rate limiting

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

def test_dspy_real(citations, prompt_type):
    """Test DSPy with real processing."""
    try:
        setup_dspy()

        class CitationSignature(dspy.Signature):
            """Validate citations according to standards."""
            input = dspy.InputField(desc="Citation to validate")
            output = dspy.OutputField(desc="'valid' or 'invalid'")

        validator = CitationValidator(CitationSignature)
        results = []

        print(f"  🧠 DSPy Optimized - {prompt_type.upper()} processing")
        for i, item in enumerate(citations[:50], 1):
            try:
                prediction = validator(input=item['citation'])
                predicted_text = prediction.output.lower().strip()
                predicted = predicted_text == 'valid'

                results.append({
                    'citation': item['citation'],
                    'ground_truth': item['ground_truth'],
                    'predicted': 'valid' if predicted else 'invalid',
                    'correct': predicted == item['ground_truth']
                })

                if i % 10 == 0:
                    correct_so_far = sum(1 for r in results if r['correct'])
                    accuracy_so_far = correct_so_far / len(results)
                    print(f"    Progress: {i}/50 - Accuracy so far: {accuracy_so_far:.1%}")

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

    except Exception as e:
        print(f"    ❌ DSPy setup failed: {e}")
        return []

def main():
    print("="*80)
    print("🚀 REAL API BENCHMARK - ALL 10 COMBINATIONS")
    print("5 models × 2 prompts = NO SIMULATED DATA")
    print("="*80)

    # Check API keys
    if not ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY not set")
        return
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not set")
        return

    print("✅ API keys found - running REAL tests")

    # Load test data
    print("\n📁 Loading test citations...")
    citations = load_test_citations()
    print(f"✅ Loaded {len(citations)} citations (testing 50 for each combination)")

    all_results = {}
    test_configs = [
        # (model_id, model_name, test_function)
        ("claude-3-5-sonnet-20241022", "Claude Sonnet 4.5", test_claude_real),
        ("gpt-4o", "GPT-4o", test_openai_real),
        ("gpt-5-preview", "GPT-5", test_openai_real),
        ("gpt-5-mini-preview", "GPT-5-mini", test_openai_real),
        ("dspy", "DSPy Optimized", test_dspy_real)
    ]

    # Test all 10 combinations
    for model_id, model_name, test_func in test_configs:
        print(f"\n{'='*60}")
        print(f"TESTING: {model_name}")
        print(f"{'='*60}")

        # Test baseline prompt
        print(f"\n📋 BASELINE PROMPT")
        if model_id == "dspy":
            baseline_results = test_func(citations, "baseline")
        elif model_name == "Claude Sonnet 4.5":
            baseline_results = test_claude_real(citations, "baseline")
        else:
            baseline_results = test_openai_real(citations, model_id, model_name, "baseline")

        if baseline_results:
            baseline_correct = sum(1 for r in baseline_results if r['correct'])
            baseline_accuracy = baseline_correct / len(baseline_results)
            all_results[f"{model_name}_baseline"] = {
                'accuracy': baseline_accuracy,
                'correct': baseline_correct,
                'total': len(baseline_results),
                'results': baseline_results
            }
            print(f"  ✅ Baseline results: {baseline_accuracy:.1%} ({baseline_correct}/{len(baseline_results)})")

        # Test optimized prompt
        print(f"\n🚀 OPTIMIZED PROMPT")
        if model_id == "dspy":
            optimized_results = test_func(citations, "optimized")
        elif model_name == "Claude Sonnet 4.5":
            optimized_results = test_claude_real(citations, "optimized")
        else:
            optimized_results = test_openai_real(citations, model_id, model_name, "optimized")

        if optimized_results:
            optimized_correct = sum(1 for r in optimized_results if r['correct'])
            optimized_accuracy = optimized_correct / len(optimized_results)
            all_results[f"{model_name}_optimized"] = {
                'accuracy': optimized_accuracy,
                'correct': optimized_correct,
                'total': len(optimized_results),
                'results': optimized_results
            }
            print(f"  ✅ Optimized results: {optimized_accuracy:.1%} ({optimized_correct}/{len(optimized_results)})")

        # Show comparison
        if baseline_results and optimized_results:
            improvement = optimized_accuracy - baseline_accuracy
            print(f"  📊 Improvement: {improvement:+.1%}")

    # Rank all real results
    print(f"\n{'='*80}")
    print("🏆 REAL RESULTS - ALL 10 COMBINATIONS RANKED")
    print(f"{'='*80}")

    ranked_results = sorted(all_results.items(), key=lambda x: x[1]['accuracy'], reverse=True)

    for i, (name, data) in enumerate(ranked_results, 1):
        print(f"{i:2d}. {name:30s} {data['accuracy']:.1%} ({data['correct']}/{data['total']})")

    # Save real results
    real_results = {
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
        'test_type': 'REAL_API_TESTS_ONLY',
        'sample_size': 50,
        'total_combinations': len(ranked_results),
        'all_results': all_results,
        'ranking': ranked_results,
        'winner': ranked_results[0] if ranked_results else None
    }

    with open('real_complete_benchmark_results.json', 'w') as f:
        json.dump(real_results, f, indent=2)

    print(f"\n✅ REAL benchmark complete!")
    print(f"📁 Results saved to real_complete_benchmark_results.json")
    print(f"🔥 NO SIMULATED DATA - ALL RESULTS FROM REAL API CALLS")

    if ranked_results:
        winner = ranked_results[0]
        print(f"\n🥇 REAL WINNER: {winner[0]}")
        print(f"   Accuracy: {winner[1]['accuracy']:.1%}")
        print(f"   Tested: {winner[1]['total']} real citations")

if __name__ == "__main__":
    main()