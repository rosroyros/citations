"""
Generate comprehensive metrics report for the competitive benchmark.

Creates a readable summary of all metrics and analysis results.
"""
import json
from pathlib import Path


def generate_metrics_report():
    """Generate a comprehensive metrics report."""

    # Load metrics summary
    with open('metrics_summary.json', 'r') as f:
        metrics = json.load(f)

    # Load citation analysis
    with open('citation_analysis.json', 'r') as f:
        citation_data = json.load(f)

    print("="*80)
    print("COMPETITIVE BENCHMARK METRICS REPORT")
    print("="*80)

    print(f"\n📊 Dataset Overview:")
    dataset = metrics['dataset_info']
    print(f"   • Total citations: {dataset['total_citations']}")
    print(f"   • Models tested: {', '.join(dataset['models_tested'])}")

    print(f"\n🏆 Model Performance Ranking:")
    for i, model_data in enumerate(metrics['model_ranking'], 1):
        model = model_data['model']
        acc = model_data['accuracy']
        f1 = model_data['f1']
        precision = model_data['precision']
        recall = model_data['recall']

        print(f"   {i}. {model}")
        print(f"      Accuracy: {acc:.1%}")
        print(f"      F1 Score: {f1:.3f}")
        print(f"      Precision: {precision:.1%}")
        print(f"      Recall: {recall:.1%}")
        print(f"      TP: {model_data['tp']}, FP: {model_data['fp']}, TN: {model_data['tn']}, FN: {model_data['fn']}")
        print()

    print(f"📈 Model Comparison Matrix:")
    agreement_matrix = metrics['citation_analysis']['model_agreement_matrix']
    models = list(agreement_matrix.keys())

    # Print agreement matrix
    print(" " * 20, end="")
    for model in models:
        print(f"{model[:15]:>15}", end="")
    print()

    for model1 in models:
        print(f"{model1[:18]:>18} ", end="")
        for model2 in models:
            agreement = agreement_matrix[model1][model2]
            print(f"{agreement:>15.1%}", end="")
        print()

    print(f"\n🔍 Citation-Level Insights:")
    citation_analysis = metrics['citation_analysis']
    print(f"   • Universal success (all models correct): {citation_analysis['universal_success_count']} citations")
    print(f"   • Universal failure (all models wrong): {citation_analysis['universal_failure_count']} citations")

    # Agreement distribution
    print(f"\n📋 Agreement Distribution:")
    for agreement, count in citation_analysis['agreement_distribution'].items():
        percentage = count / dataset['total_citations'] * 100
        print(f"   • {agreement} models correct: {count} citations ({percentage:.1f}%)")

    print(f"\n🎯 Key Insights:")
    insights = metrics['insights']
    print(f"   • Best performer: {insights['best_model']}")
    print(f"   • Accuracy range: {insights['accuracy_range'][0]:.1%} - {insights['accuracy_range'][1]:.1%}")
    print(f"   • Average model agreement: {insights['average_agreement']:.1%}")

    # Error analysis
    print(f"\n❌ Error Analysis:")
    error_analysis = metrics['error_analysis']
    for model, error_count in error_analysis.items():
        error_rate = error_count / dataset['total_citations'] * 100
        print(f"   • {model}: {error_count} errors ({error_rate:.1f}%)")

    print(f"\n" + "="*80)
    print("DETAILED ANALYSIS")
    print("="*80)

    # Show some examples of disagreements
    disagreements = [
        c for c in citation_data['citation_analysis']
        if not c['all_models_agree'] and 0 < c['correct_count'] < len(models)
    ]

    if disagreements:
        print(f"\n🔄 Examples of Model Disagreements:")
        for i, citation in enumerate(disagreements[:3], 1):
            print(f"\n   {i}. {citation['citation'][:80]}...")
            print(f"      Ground truth: {citation['ground_truth']}")

            for model in models:
                pred_data = citation['model_predictions'][model]
                predicted = pred_data['predicted']
                correct = pred_data['correct']
                status = "✓" if correct else "✗"
                print(f"      {status} {model}: {predicted} - {pred_data['explanation'][:50]}...")

    # Show error patterns for worst model
    worst_model = metrics['model_ranking'][-1]['model']
    error_patterns = citation_data['error_patterns'][worst_model]

    if error_patterns:
        print(f"\n🔍 Error Patterns for {worst_model} (lowest performing):")
        for i, error in enumerate(error_patterns[:3], 1):
            print(f"\n   {i}. {error['citation']}")
            print(f"      Ground truth: {error['ground_truth']}")
            print(f"      Predicted: {error['predicted']}")
            print(f"      Explanation: {error['explanation']}")

    # Performance gaps
    best_f1 = metrics['model_ranking'][0]['f1']
    worst_f1 = metrics['model_ranking'][-1]['f1']
    gap = best_f1 - worst_f1

    print(f"\n📊 Performance Gap Analysis:")
    print(f"   • F1 Score gap: {gap:.3f} points ({gap/worst_f1*100:.1f}% relative improvement)")
    print(f"   • Best model vs worst model: {metrics['model_ranking'][0]['model']} vs {metrics['model_ranking'][-1]['model']}")

    # Statistical significance
    print(f"\n📈 Statistical Notes:")
    print(f"   • Sample size: {dataset['total_citations']} citations")
    print(f"   • Confidence: Results based on mock data for demonstration")
    print(f"   • Next step: Run with real API calls for actual performance metrics")

    print(f"\n✅ Report generated successfully!")
    print(f"📁 Data files available:")
    print(f"   • metrics_summary.json - Complete metrics data")
    print(f"   • citation_analysis.json - Detailed citation-level analysis")
    print(f"   • *_results.jsonl - Raw model results")


if __name__ == "__main__":
    generate_metrics_report()