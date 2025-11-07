"""
Fix parsing issue in 121-citation results by reprocessing existing JSONL files.
No API calls needed - just reprocess the raw responses we already have.
"""
import json

def parse_response(raw_response):
    """Fixed parsing logic to extract valid/invalid from model responses."""
    raw_response = raw_response.strip().lower()

    # Extract just valid/invalid from potentially longer responses
    if 'valid' in raw_response and 'invalid' not in raw_response:
        return True  # valid
    elif 'invalid' in raw_response:
        return False  # invalid
    else:
        # Default case - if neither clear, assume invalid
        return False

def process_jsonl_file(filename):
    """Process a JSONL file and recalculate accuracy with fixed parsing."""
    results = []
    correct_count = 0

    with open(filename, 'r') as f:
        for line in f:
            data = json.loads(line)

            # Apply fixed parsing to raw_response
            raw_response = data.get('raw_response', '')
            predicted = parse_response(raw_response)
            ground_truth = data.get('ground_truth', False)

            # Update data with corrected prediction
            data['predicted'] = predicted
            data['correct'] = predicted == ground_truth

            if data['correct']:
                correct_count += 1

            results.append(data)

    accuracy = correct_count / len(results) if results else 0
    return results, accuracy, correct_count

def main():
    print("🔧 Fixing parsing issue in 121-citation results...")

    # Define all 8 model/prompt combinations
    models = [
        "GPT-4o_baseline",
        "GPT-4o_optimized",
        "GPT-4o-mini_baseline",
        "GPT-4o-mini_optimized",
        "GPT-5_baseline",
        "GPT-5_optimized",
        "GPT-5-mini_baseline",
        "GPT-5-mini_optimized"
    ]

    all_results = {}
    accuracies = {}

    for model in models:
        filename = f"{model}_detailed_121.jsonl"
        print(f"\n📁 Processing: {filename}")

        try:
            results, accuracy, correct = process_jsonl_file(filename)
            all_results[model] = results
            accuracies[model] = accuracy

            print(f"✅ {model}: {accuracy:.1%} ({correct}/121)")

        except FileNotFoundError:
            print(f"❌ File not found: {filename}")
            continue

    # Sort by accuracy
    ranking = sorted(accuracies.items(), key=lambda x: x[1], reverse=True)

    print(f"\n🏆 RANKED RESULTS:")
    print("=" * 60)
    for i, (model, acc) in enumerate(ranking, 1):
        correct = int(acc * 121)
        print(f"{i:2d}. {model:25s} → {acc:.1%} ({correct}/121)")

    # Save fixed results
    summary = {
        'timestamp': '2025-11-07 FIXED_PARSING',
        'test_type': 'DETAILED_121_CITATION_TEST_PARSED_CORRECTLY',
        'citations_tested': 121,
        'models_tested': 4,
        'combinations': len(ranking),
        'accuracies': accuracies,
        'ranking': [[model, acc] for model, acc in ranking]
    }

    output_file = 'detailed_121_test_summary_fixed_parsed.json'
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n📁 Fixed results saved: {output_file}")
    print(f"🎉 Parsing issue resolved! Real 121-citation results available!")

if __name__ == "__main__":
    main()