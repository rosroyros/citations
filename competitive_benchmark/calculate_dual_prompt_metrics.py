"""
Calculate comprehensive metrics for dual prompt competitive benchmark.

Analyzes 5 models × 2 prompts = 10 variations with:
- Prompt effectiveness analysis
- Model performance comparison
- Cost-performance insights
- Marketing recommendations
"""
import json
from pathlib import Path
from typing import Dict, List, Any


def load_dual_prompt_data() -> Dict[str, Any]:
    """Load dual prompt benchmark data."""
    with open('dual_prompt_summary.json', 'r') as f:
        return json.load(f)


def calculate_comprehensive_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate comprehensive metrics for dual prompt analysis."""

    results_summary = data['results_summary']
    prompt_effectiveness = data['prompt_effectiveness']
    model_performance = data['model_performance']

    # Model rankings by different criteria
    rankings = {
        'overall_best': sorted(results_summary.items(), key=lambda x: x[1]['accuracy'], reverse=True),
        'baseline_best': sorted(model_performance['baseline'], key=lambda x: x[1]['accuracy'], reverse=True),
        'optimized_best': sorted(model_performance['optimized'], key=lambda x: x[1]['accuracy'], reverse=True)
    }

    # Prompt effectiveness analysis
    prompt_analysis = {}
    for model, effectiveness in prompt_effectiveness.items():
        prompt_analysis[model] = {
            'baseline_accuracy': effectiveness['baseline_accuracy'],
            'optimized_accuracy': effectiveness['optimized_accuracy'],
            'absolute_improvement': effectiveness['improvement'],
            'relative_improvement': effectiveness['improvement_percentage'],
            'roi_category': categorize_prompt_roi(effectiveness['improvement_percentage'])
        }

    # Cost-performance analysis (estimated costs)
    # Assuming relative costs (normalized to GPT-4o = 1.0)
    estimated_costs = {
        'DSPy Optimized': 0.1,      # Local, essentially free
        'Claude Sonnet 4.5': 3.0,    # Expensive
        'GPT-4o': 1.0,              # Baseline
        'GPT-5': 10.0,              # Very expensive
        'GPT-5-mini': 0.2           # Very cheap
    }

    cost_performance = {}
    for model, effectiveness in prompt_effectiveness.items():
        best_accuracy = max(effectiveness['baseline_accuracy'], effectiveness['optimized_accuracy'])
        cost = estimated_costs.get(model, 1.0)
        cost_performance[model] = {
            'best_accuracy': best_accuracy,
            'estimated_cost': cost,
            'accuracy_per_cost': best_accuracy / cost,
            'cost_effectiveness_rank': None  # Will be calculated below
        }

    # Rank by cost-effectiveness
    cost_effectiveness_ranking = sorted(
        cost_performance.items(),
        key=lambda x: x[1]['accuracy_per_cost'],
        reverse=True
    )

    for i, (model, _) in enumerate(cost_effectiveness_ranking, 1):
        cost_performance[model]['cost_effectiveness_rank'] = i

    # Business insights
    business_insights = {
        'best_value_model': cost_effectiveness_ranking[0][0],
        'best_performance_model': rankings['overall_best'][0][0],
        'most_prompt_responsive': max(prompt_effectiveness.items(), key=lambda x: x[1]['improvement_percentage'])[0],
        'prompt_optimization_value': calculate_prompt_optimization_value(prompt_effectiveness, estimated_costs)
    }

    # Marketing recommendations
    recommendations = generate_marketing_recommendations(
        rankings, prompt_analysis, cost_performance, business_insights
    )

    return {
        'dataset_info': data['dataset_info'],
        'rankings': rankings,
        'prompt_analysis': prompt_analysis,
        'cost_performance': cost_performance,
        'business_insights': business_insights,
        'marketing_recommendations': recommendations,
        'detailed_results': results_summary
    }


def categorize_prompt_roi(improvement_percentage: float) -> str:
    """Categorize prompt optimization ROI."""
    if improvement_percentage >= 5.0:
        return "Excellent - Highly Responsive"
    elif improvement_percentage >= 3.0:
        return "Good - Responsive"
    elif improvement_percentage >= 1.0:
        return "Moderate - Some Benefit"
    else:
        return "Low - Minimal Impact"


def calculate_prompt_optimization_value(prompt_effectiveness: Dict, costs: Dict) -> Dict:
    """Calculate the business value of prompt optimization."""
    total_value = 0
    optimization_values = {}

    for model, effectiveness in prompt_effectiveness.items():
        baseline_acc = effectiveness['baseline_accuracy']
        optimized_acc = effectiveness['optimized_accuracy']
        improvement = optimized_acc - baseline_acc

        cost = costs.get(model, 1.0)
        # Value = improvement * (1/cost) * 100 (normalized)
        value = improvement * (100 / cost) if cost > 0 else 0

        optimization_values[model] = {
            'improvement': improvement,
            'cost': cost,
            'value_score': value,
            'value_per_dollar': value / cost if cost > 0 else 0
        }
        total_value += value

    return {
        'individual_values': optimization_values,
        'total_optimization_value': total_value,
        'best_roi_model': max(optimization_values.items(), key=lambda x: x[1]['value_per_dollar'])[0] if optimization_values else None
    }


def generate_marketing_recommendations(rankings, prompt_analysis, cost_performance, insights) -> Dict:
    """Generate actionable marketing recommendations."""

    recommendations = {
        'primary_recommendation': '',
        'cost_effective_solution': '',
        'prompt_optimization_strategy': '',
        'competitive_positioning': [],
        'roi_messages': []
    }

    # Primary recommendation (best overall performance)
    best_overall = rankings['overall_best'][0]
    recommendations['primary_recommendation'] = f"""
    Use {best_overall[0]} ({best_overall[1]['accuracy']:.1%} accuracy) for maximum performance.
    This model delivers the highest accuracy across all prompt variations.
    """

    # Cost-effective solution
    cost_effectiveness_ranking = sorted(
        cost_performance.items(),
        key=lambda x: x[1]['accuracy_per_cost'],
        reverse=True
    )
    best_value = cost_effectiveness_ranking[0]
    recommendations['cost_effective_solution'] = f"""
    For budget-conscious deployments, use {best_value[0]} ({best_value[1]['best_accuracy']:.1%} accuracy).
    Delivers excellent performance at {best_value[1]['estimated_cost']}x the cost of baseline models.
    """

    # Prompt optimization strategy
    best_prompt_responsive = insights['most_prompt_responsive']
    prompt_improvement = prompt_analysis[best_prompt_responsive]['improvement_percentage']
    recommendations['prompt_optimization_strategy'] = f"""
    Focus prompt optimization efforts on {best_prompt_responsive} (+{prompt_improvement:.1f}% improvement).
    This model shows the highest responsiveness to enhanced prompting strategies.
    """

    # Competitive positioning messages
    if 'DSPy Optimized' in cost_performance:
        dspy_data = cost_performance['DSPy Optimized']
        recommendations['competitive_positioning'].append(
            f"Local DSPy solution offers {dsipy_data['best_accuracy']:.1%} accuracy at negligible cost"
        )

    gpt5mini_data = cost_performance.get('GPT-5-mini', {})
    if gpt5mini_data:
        recommendations['competitive_positioning'].append(
            f"GPT-5-mini achieves {gpt5mini_data['best_accuracy']:.1%} accuracy at 20% of GPT-4o cost"
        )

    # ROI messages
    for model, analysis in prompt_analysis.items():
        if analysis['improvement_percentage'] > 3.0:
            cost = cost_performance.get(model, {}).get('estimated_cost', 1.0)
            recommendations['roi_messages'].append(
                f"{model}: +{analysis['improvement_percentage']:.1f}% accuracy with optimized prompt (cost multiplier: {cost}x)"
            )

    return recommendations


def main():
    print("="*80)
    print("CALCULATING DUAL PROMPT COMPREHENSIVE METRICS")
    print("="*80)

    # Load data
    print("📁 Loading dual prompt benchmark data...")
    data = load_dual_prompt_data()

    # Calculate comprehensive metrics
    print("🔍 Analyzing prompt effectiveness and performance...")
    metrics = calculate_comprehensive_metrics(data)

    # Save comprehensive metrics
    with open('dual_prompt_comprehensive_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)

    print("✅ Comprehensive metrics calculated and saved")

    # Display key insights
    print(f"\n🎯 DUAL PROMPT ANALYSIS INSIGHTS:")
    print(f"")
    print(f"📊 PERFORMANCE RANKINGS:")
    print(f"   Overall Best: {metrics['rankings']['overall_best'][0][0]} ({metrics['rankings']['overall_best'][0][1]['accuracy']:.1%})")
    print(f"   Baseline Best: {metrics['rankings']['baseline_best'][0][0]} ({metrics['rankings']['baseline_best'][0][1]['accuracy']:.1%})")
    print(f"   Optimized Best: {metrics['rankings']['optimized_best'][0][0]} ({metrics['rankings']['optimized_best'][0][1]['accuracy']:.1%})")
    print(f"")
    print(f"💰 COST-EFFECTIVENESS:")
    cost_best = metrics['cost_performance']['cost_effectiveness_rank'][0]
    print(f"   Best Value: {cost_best[0]} ({cost_best[1]['best_accuracy']:.1%} accuracy, {cost_best[1]['estimated_cost']}x cost)")
    print(f"   Accuracy per Cost Ratio: {cost_best[1]['accuracy_per_cost']:.1f}")
    print(f"")
    print(f"🔧 PROMPT OPTIMIZATION IMPACT:")
    for model, analysis in metrics['prompt_analysis'].items():
        print(f"   {model}: +{analysis['relative_improvement']:.1f}% ({analysis['roi_category']})")
    print(f"")
    print(f"🎯 BUSINESS INSIGHTS:")
    insights = metrics['business_insights']
    print(f"   Best Performance: {insights['best_performance_model']}")
    print(f"   Best Value: {insights['best_value_model']}")
    print(f"   Most Responsive: {insights['most_prompt_responsive']}")
    print(f"")
    print(f"📈 MARKETING RECOMMENDATIONS:")
    recs = metrics['marketing_recommendations']
    print(f"   {recs['primary_recommendation'].strip()}")
    print(f"   {recs['cost_effective_solution'].strip()}")

    # Create summary for next phase
    summary_for_html = {
        'timestamp': '2025-11-06 23:15:00',
        'analysis_type': 'dual_prompt_competitive_benchmark',
        'total_combinations': len(metrics['detailed_results']),
        'key_findings': {
            'best_overall': metrics['rankings']['overall_best'][0],
            'best_cost_effective': cost_best,
            'prompt_optimization_benefit': sum(analysis['relative_improvement'] for analysis in metrics['prompt_analysis'].values()) / len(metrics['prompt_analysis']),
            'cost_performance_leader': metrics['business_insights']['best_value_model']
        },
        'detailed_metrics': metrics,
        'marketing_insights': recs
    }

    with open('holistic_benchmark_summary.json', 'w') as f:
        json.dump(summary_for_html, f, indent=2)

    print(f"")
    print(f"✅ DUAL PROMPT ANALYSIS COMPLETE!")
    print(f"📁 Files created:")
    print(f"   • dual_prompt_comprehensive_metrics.json - Detailed analysis")
    print(f"   • holistic_benchmark_summary.json - Summary for HTML report")
    print(f"")
    print(f"🚀 Ready for final holistic HTML report generation!")


if __name__ == "__main__":
    main()