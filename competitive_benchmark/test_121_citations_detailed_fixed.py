"""
Test 121 citations with detailed per-citation results using FIXED working configuration.
Based on the working test_30_citations_detailed.py but scaled to full dataset.
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

# Real prompts (FIXED VERSIONS from working script)
BASELINE_PROMPT = """Is this citation valid or invalid? Respond with exactly one word: "valid" or "invalid".

Note: Italics in citations are indicated by underscores (e.g., _Journal Title_ represents italicized text).

Citation: {citation}"""

# Full production prompt from validator_prompt_optimized.txt (FIXED VERSION)
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

def test_model_detailed(model_id, model_name, prompt_type, citations):
    """Test a model with detailed per-citation results."""
    prompt = BASELINE_PROMPT if prompt_type == 'baseline' else OPTIMIZED_PROMPT
    results = []

    print(f"\n📋 {prompt_type.upper()}:")
    print(f"  🤖 {model_name} - {prompt_type.upper()}")

    for i, item in enumerate(citations, 1):
        try:
            formatted_prompt = prompt.format(citation=item['citation'])

            # FIXED API Configuration from working script
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
    print("🔍 DETAILED TEST - 121 Citations per Combination (FIXED VERSION)", flush=True)
    print("=" * 60, flush=True)

    citations = load_test_citations(limit=121)
    print(f"\n📁 Loaded {len(citations)} citations for testing", flush=True)

    models = [
        ('gpt-4o', 'GPT-4o'),
        ('gpt-4o-mini', 'GPT-4o-mini'),
        ('gpt-5', 'GPT-5'),
        ('gpt-5-mini', 'GPT-5-mini')
    ]

    all_results = {}
    accuracies = {}

    for model_id, model_name in models:
        print(f"\n" + "="*60)
        print(f"TESTING: {model_name}")
        print("="*60)

        for prompt_type in ['baseline', 'optimized']:
            key = f"{model_name}_{prompt_type}"
            results, acc = test_model_detailed(model_id, model_name, prompt_type, citations)

            # Save detailed results
            filename = f"{model_name}_{prompt_type}_detailed_121.jsonl"
            with open(filename, 'w') as f:
                for result in results:
                    json.dump(result, f)
                    f.write('\n')

            print(f"  📁 Detailed: {filename}")

            all_results[key] = results
            accuracies[key] = acc

    # Summary
    print("\n" + "="*60)
    print("🏆 RESULTS RANKED")
    print("="*60)

    ranking = sorted(accuracies.items(), key=lambda x: x[1], reverse=True)
    for i, (key, acc) in enumerate(ranking, 1):
        model, prompt_type = key.rsplit('_', 1)
        correct = int(acc * len(citations))
        print(f"{i:2d}. {model:15s} + {prompt_type.upper():9s} → {acc:.1%} ({correct}/{len(citations)})")

    # Save summary
    summary = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'test_type': 'DETAILED_121_CITATION_TEST_FIXED',
        'citations_tested': len(citations),
        'models_tested': len(models),
        'combinations': len(ranking),
        'accuracies': accuracies,
        'ranking': [[key, acc] for key, acc in ranking]
    }

    with open('detailed_121_test_summary_fixed.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n📁 Summary: detailed_121_test_summary_fixed.json")
    print(f"🔥 ALL 4 MODELS TESTED WITH FIXED CONFIGURATION!")

if __name__ == "__main__":
    main()