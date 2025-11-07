"""
Recalculate 121-citation results using ONLY raw_response and ground_truth fields.
Ignores the incorrect 'predicted' field that was generated with broken parsing.
"""
import json

def parse_raw_response(raw_response):
    """Parse raw model response to extract valid/invalid determination."""
    if not raw_response:
        return False  # default to invalid if empty

    raw_response = raw_response.strip().lower()

    # Extract just valid/invalid from potentially longer responses
    if 'valid' in raw_response and 'invalid' not in raw_response:
        return True  # valid
    elif 'invalid' in raw_response:
        return False  # invalid
    else:
        # Default case - if neither clear, assume invalid
        return False

def recalculate_from_raw(filename):
    """Recalculate results using only raw_response, ignoring broken predicted field."""
    correct_count = 0
    total_count = 0

    with open(filename, 'r') as f:
        for line in f:
            data = json.loads(line)

            # Use ONLY raw_response and ground_truth
            raw_response = data.get('raw_response', '')
            ground_truth = data.get('ground_truth', False)

            # Parse raw response correctly
            predicted = parse_raw_response(raw_response)
            is_correct = predicted == ground_truth

            if is_correct:
                correct_count += 1
            total_count += 1

    accuracy = correct_count / total_count if total_count > 0 else 0
    return accuracy, correct_count, total_count

def main():
    print("🔍 Recalculating 121-citation results from RAW responses only...")
    print("(Ignoring broken 'predicted' field from original parsing bug)")

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

    results = {}

    for model in models:
        filename = f"{model}_detailed_121.jsonl"
        print(f"\n📁 Recalculating: {filename}")

        try:
            accuracy, correct, total = recalculate_from_raw(filename)
            results[model] = {
                'accuracy': accuracy,
                'correct': correct,
                'total': total
            }
            print(f"✅ {model}: {accuracy:.1%} ({correct}/{total})")

        except FileNotFoundError:
            print(f"❌ File not found: {filename}")
            continue

    # Sort by accuracy
    ranking = sorted(results.items(), key=lambda x: x[1]['accuracy'], reverse=True)

    print(f"\n🏆 TRUE RESULTS FROM RAW RESPONSES:")
    print("=" * 70)
    for i, (model, data) in enumerate(ranking, 1):
        acc = data['accuracy']
        correct = data['correct']
        total = data['total']
        print(f"{i:2d}. {model:25s} → {acc:.1%} ({correct}/{total})")

    # Save corrected results
    summary = {
        'timestamp': '2025-11-07 RECALCULATED_FROM_RAW',
        'test_type': 'DETAILED_121_CITATION_TEST_RECALCULATED',
        'citations_tested': 121,
        'models_tested': 4,
        'combinations': len(ranking),
        'accuracies': {model: data['accuracy'] for model, data in results.items()},
        'ranking': [[model, data['accuracy']] for model, data in ranking]
    }

    output_file = 'detailed_121_test_summary_recalculated.json'
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n📁 True results saved: {output_file}")
    print(f"🎯 Results based on raw model responses only!")

if __name__ == "__main__":
    main()