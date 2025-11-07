"""
Create mock results for the competitive benchmark to demonstrate the workflow.

This script generates sample results for all 4 models to show what the output
would look like. It simulates model performance with realistic accuracy levels.
"""
import json
import random
from pathlib import Path
from typing import List, Dict, Any


def load_validation_set() -> List[Dict]:
    """Load the validation set."""
    dataset = []
    with open('validation_set.jsonl', 'r') as f:
        for line in f:
            dataset.append(json.loads(line.strip()))
    return dataset


def simulate_model_results(dataset: List[Dict], model_name: str, accuracy: float) -> List[Dict]:
    """
    Simulate model results with specified accuracy.

    Args:
        dataset: Validation set
        model_name: Name of the model
        accuracy: Target accuracy (0.0 to 1.0)

    Returns:
        List of results with predicted_valid and explanation
    """
    results = []

    # Set seed for reproducible results per model
    random.seed(hash(model_name) % 1000)

    for i, example in enumerate(dataset):
        ground_truth = example['is_valid']

        # Simulate prediction with target accuracy
        if random.random() < accuracy:
            predicted_valid = ground_truth  # Correct prediction
        else:
            predicted_valid = not ground_truth  # Incorrect prediction

        # Generate realistic explanation based on prediction
        if predicted_valid:
            explanations = [
                "Citation follows APA 7th edition guidelines correctly",
                "All required elements are present and properly formatted",
                "No formatting errors detected",
                "Citation structure meets APA standards",
                "All components are correctly formatted"
            ]
        else:
            explanations = [
                "Missing italics for title",
                "Incorrect date format",
                "DOI formatting error",
                "Author name formatting issue",
                "Punctuation errors in citation",
                "Publisher location missing",
                "Capitalization error in title"
            ]

        explanation = random.choice(explanations)

        result = {
            'citation_id': example.get('citation_id', f"cit_{i}"),
            'citation': example['citation'],
            'ground_truth': ground_truth,
            'predicted_valid': predicted_valid,
            'explanation': explanation,
            'model': model_name
        }

        results.append(result)

    return results


def main():
    print("="*80)
    print("CREATING MOCK BENCHMARK RESULTS")
    print("="*80)

    # Load validation set
    dataset = load_validation_set()
    print(f"Loaded {len(dataset)} citations from validation set")

    # Count valid/invalid
    valid_count = sum(1 for ex in dataset if ex['is_valid'])
    invalid_count = len(dataset) - valid_count
    print(f"Valid: {valid_count}, Invalid: {invalid_count}")

    # Simulate results for each model with realistic accuracies
    models = [
        ("DSPy Optimized", 0.89),      # High accuracy (optimized)
        ("Claude Sonnet 4.5", 0.91),   # Very high accuracy
        ("GPT-4o", 0.87),              # Good accuracy
        ("GPT-5", 0.94),               # Best accuracy (future model)
        ("GPT-5-mini", 0.88)           # Good accuracy, cost-effective
    ]

    all_results = {}

    for model_name, accuracy in models:
        print(f"\n🤖 Simulating {model_name} (target accuracy: {accuracy:.1%})...")
        results = simulate_model_results(dataset, model_name, accuracy)
        all_results[model_name] = results

        # Calculate actual accuracy
        correct = sum(1 for r in results if r['predicted_valid'] == r['ground_truth'])
        actual_accuracy = correct / len(results)

        print(f"   Actual accuracy: {actual_accuracy:.1%} ({correct}/{len(results)})")

        # Save results
        filename = f"{model_name.lower().replace(' ', '_')}_results.jsonl"
        with open(filename, 'w') as f:
            for result in results:
                f.write(json.dumps(result) + '\n')
        print(f"   Saved to {filename}")

    # Create summary report
    summary = {
        'timestamp': '2025-11-06 20:45:00',
        'dataset_size': len(dataset),
        'valid_citations': valid_count,
        'invalid_citations': invalid_count,
        'models_tested': list(all_results.keys()),
        'model_accuracies': {
            model: sum(1 for r in results if r['predicted_valid'] == r['ground_truth']) / len(results)
            for model, results in all_results.items()
        },
        'notes': 'Mock results generated for demonstration purposes'
    }

    with open('mock_benchmark_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n📊 Summary saved to mock_benchmark_summary.json")
    print("\n🏆 Model Ranking (by accuracy):")

    # Sort models by accuracy
    sorted_models = sorted(
        summary['model_accuracies'].items(),
        key=lambda x: x[1],
        reverse=True
    )

    for i, (model, acc) in enumerate(sorted_models, 1):
        print(f"   {i}. {model}: {acc:.1%}")

    print(f"\n✅ Mock benchmark complete!")
    print(f"📁 Results ready for metrics calculation phase")

    # Show sample results
    print(f"\n📋 Sample Results (first 3 citations):")
    for i in range(min(3, len(dataset))):
        citation = dataset[i]['citation'][:60] + "..."
        ground_truth = dataset[i]['is_valid']

        print(f"\nCitation {i+1}: {citation}")
        print(f"Ground Truth: {ground_truth}")

        for model_name in [name for name, _ in models]:
            result = all_results[model_name][i]
            predicted = result['predicted_valid']
            status = "✓" if predicted == ground_truth else "✗"
            print(f"  {status} {model_name}: {predicted} - {result['explanation']}")


if __name__ == "__main__":
    main()