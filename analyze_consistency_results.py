#!/usr/bin/env python3
"""
Analyze consistency test results.
Calculates consistency metrics, ensemble performance, and cost/benefit analysis.
"""
import json
from collections import Counter

def load_run_results(model_name, run_number):
    """Load results from a single test run."""
    filename = f'Checker_Prompt_Optimization/consistency_test_{model_name}_run_{run_number}.jsonl'
    results = []
    with open(filename, 'r') as f:
        for line in f:
            results.append(json.loads(line))
    return results

def analyze_model_consistency(model_name):
    """Analyze consistency for a single model across 3 runs."""
    print(f"\n{'='*80}")
    print(f"Analyzing: {model_name}")
    print(f"{'='*80}\n")

    # Load all 3 runs
    run1 = load_run_results(model_name, 1)
    run2 = load_run_results(model_name, 2)
    run3 = load_run_results(model_name, 3)

    n_citations = len(run1)
    print(f"Total citations: {n_citations}")

    # Calculate individual run accuracies
    run_accuracies = []
    for i, run in enumerate([run1, run2, run3], 1):
        correct = sum(1 for r in run if r.get('correct', False))
        accuracy = (correct / n_citations) * 100
        run_accuracies.append(accuracy)
        print(f"Run {i} Accuracy: {accuracy:.2f}% ({correct}/{n_citations})")

    avg_accuracy = sum(run_accuracies) / len(run_accuracies)
    print(f"\nAverage Single-Run Accuracy: {avg_accuracy:.2f}%")

    # Consistency analysis
    perfect_agreement = 0  # All 3 runs agree
    majority_agreement = 0  # At least 2 runs agree
    complete_disagreements = []  # All 3 runs different
    partial_disagreements = []  # 2 agree, 1 differs

    # Ensemble voting
    ensemble_correct = 0

    for i in range(n_citations):
        pred1 = run1[i].get('predicted')
        pred2 = run2[i].get('predicted')
        pred3 = run3[i].get('predicted')
        ground_truth = run1[i]['ground_truth']

        predictions = [pred1, pred2, pred3]
        unique_count = len(set(predictions))

        # Check agreement
        if pred1 == pred2 == pred3:
            perfect_agreement += 1
            majority_agreement += 1
        elif unique_count == 2:
            # Partial disagreement (2 agree, 1 differs)
            majority_agreement += 1
            partial_disagreements.append({
                'citation_index': i,
                'citation': run1[i]['citation'],
                'ground_truth': ground_truth,
                'run1': pred1,
                'run2': pred2,
                'run3': pred3
            })
        else:
            # Complete disagreement (all 3 different)
            complete_disagreements.append({
                'citation_index': i,
                'citation': run1[i]['citation'],
                'ground_truth': ground_truth,
                'run1': pred1,
                'run2': pred2,
                'run3': pred3
            })

        # Majority vote
        vote_counts = Counter(predictions)
        majority_pred = vote_counts.most_common(1)[0][0]

        if majority_pred == ground_truth:
            ensemble_correct += 1

    # Calculate metrics
    perfect_agreement_rate = (perfect_agreement / n_citations) * 100
    majority_agreement_rate = (majority_agreement / n_citations) * 100
    ensemble_accuracy = (ensemble_correct / n_citations) * 100

    print(f"\n{'─'*80}")
    print("CONSISTENCY METRICS")
    print(f"{'─'*80}")
    print(f"Perfect Agreement (all 3 runs): {perfect_agreement_rate:.2f}% ({perfect_agreement}/{n_citations})")
    print(f"Majority Agreement (≥2 runs): {majority_agreement_rate:.2f}% ({majority_agreement}/{n_citations})")
    print(f"Partial Disagreement (2/3 agree): {len(partial_disagreements)} citations")
    print(f"Complete Disagreement (all different): {len(complete_disagreements)} citations")

    print(f"\n{'─'*80}")
    print("ENSEMBLE PERFORMANCE (Majority Voting)")
    print(f"{'─'*80}")
    print(f"Ensemble Accuracy: {ensemble_accuracy:.2f}% ({ensemble_correct}/{n_citations})")
    print(f"Improvement over avg single run: {ensemble_accuracy - avg_accuracy:+.2f}%")

    # Cost/benefit analysis
    print(f"\n{'─'*80}")
    print("COST/BENEFIT ANALYSIS")
    print(f"{'─'*80}")
    print(f"Single Run: 1x cost, {avg_accuracy:.2f}% accuracy")
    print(f"Ensemble (3 runs): 3x cost, {ensemble_accuracy:.2f}% accuracy")

    accuracy_gain = ensemble_accuracy - avg_accuracy
    cost_multiplier = 3
    efficiency = accuracy_gain / cost_multiplier

    print(f"\nAccuracy gain: {accuracy_gain:+.2f}%")
    print(f"Cost multiplier: {cost_multiplier}x")
    print(f"Efficiency (gain per cost unit): {efficiency:+.2f}%")

    if efficiency < 1.0:
        print(f"\n⚠️  RECOMMENDATION: Ensemble NOT cost-effective")
        print(f"   Gain of {accuracy_gain:.2f}% does not justify 3x cost")
    else:
        print(f"\n✅ RECOMMENDATION: Ensemble is cost-effective")
        print(f"   Gain of {accuracy_gain:.2f}% justifies 3x cost")

    return {
        'model': model_name,
        'n_citations': n_citations,
        'run_accuracies': run_accuracies,
        'avg_accuracy': avg_accuracy,
        'perfect_agreement_rate': perfect_agreement_rate,
        'majority_agreement_rate': majority_agreement_rate,
        'ensemble_accuracy': ensemble_accuracy,
        'accuracy_gain': accuracy_gain,
        'cost_multiplier': cost_multiplier,
        'efficiency': efficiency,
        'partial_disagreements': partial_disagreements,
        'complete_disagreements': complete_disagreements
    }

def main():
    print("="*80)
    print("CONSISTENCY TEST ANALYSIS")
    print("="*80)

    models = ['gpt-5-mini', 'gpt-4o-mini', 'gpt-4o-mini_temp0']
    results = {}

    for model in models:
        try:
            results[model] = analyze_model_consistency(model)
        except Exception as e:
            print(f"\n❌ Error analyzing {model}: {e}")
            continue

    # Comparison
    if len(results) >= 2:
        print(f"\n{'='*80}")
        print("MODEL COMPARISON")
        print(f"{'='*80}\n")

        for model in models:
            if model in results:
                r = results[model]
                print(f"{model}:")
                print(f"  Single-run accuracy: {r['avg_accuracy']:.2f}%")
                print(f"  Ensemble accuracy: {r['ensemble_accuracy']:.2f}%")
                print(f"  Consistency rate: {r['perfect_agreement_rate']:.2f}%")
                print(f"  Cost-effectiveness: {'✅' if r['efficiency'] >= 1.0 else '❌'}")
                print()

    # Save disagreement citations for review
    print(f"\n{'='*80}")
    print("SAVING DISAGREEMENT CITATIONS FOR REVIEW")
    print(f"{'='*80}\n")

    for model in models:
        if model in results:
            r = results[model]

            # Save partial disagreements (2/3 agree)
            if r['partial_disagreements']:
                partial_file = f'Checker_Prompt_Optimization/disagreements_{model}_partial.json'
                with open(partial_file, 'w') as f:
                    json.dump(r['partial_disagreements'], f, indent=2)
                print(f"📝 {model} - Partial disagreements: {len(r['partial_disagreements'])} citations → {partial_file}")

            # Save complete disagreements (all different)
            if r['complete_disagreements']:
                complete_file = f'Checker_Prompt_Optimization/disagreements_{model}_complete.json'
                with open(complete_file, 'w') as f:
                    json.dump(r['complete_disagreements'], f, indent=2)
                print(f"⚠️  {model} - Complete disagreements: {len(r['complete_disagreements'])} citations → {complete_file}")

    # Save results
    output_file = 'Checker_Prompt_Optimization/consistency_test_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Analysis complete! Results saved to: {output_file}")

if __name__ == '__main__':
    main()
