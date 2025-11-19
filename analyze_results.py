import json
from pathlib import Path
from glob import glob

# Task 1: Load All Corrected Results
print("="*80)
print("LOADING CORRECTED RESULTS")
print("="*80)

result_files = glob("Checker_Prompt_Optimization/corrected_results/*_corrected.json")
results = []

for file in result_files:
    if "all_models" not in file:  # Skip summary file
        with open(file, 'r') as f:
            results.append(json.load(f))

# Sort by accuracy
results.sort(key=lambda x: x['accuracy'], reverse=True)

print(f"Loaded {len(results)} model results\n")

# Task 2: Identify Top Performers
print("="*80)
print("TOP 5 MODELS (Corrected Ground Truth)")
print("="*80)

for i, r in enumerate(results[:5], 1):
    print(f"\n{i}. {r['model']}")
    print(f"   Accuracy: {r['accuracy']}%")
    print(f"   F1 (Invalid): {r['metrics']['invalid']['f1']}%")
    print(f"   F1 (Valid): {r['metrics']['valid']['f1']}%")
    print(f"   Errors: {r['test_set_size'] - (r['confusion_matrix']['true_negative'] + r['confusion_matrix']['true_positive'])}")
    print(f"   FP (too strict): {r['confusion_matrix']['false_negative']}")
    print(f"   FN (too lenient): {r['confusion_matrix']['false_positive']}")

print("="*80)

# Task 3: Analyze GPT-5-mini Performance
gpt5_mini = [r for r in results if 'gpt-5-mini' in r['model'].lower() or 'gpt5-mini' in r['model'].lower()]

if gpt5_mini:
    print("\n" + "="*80)
    print("GPT-5-MINI ANALYSIS")
    print("="*80)

    for r in gpt5_mini:
        print(f"\nVariant: {r['model']}")
        print(f"  Corrected Accuracy: {r['accuracy']}%")
        print(f"  Original Reported: 77.7%")
        print(f"  Improvement: +{r['accuracy'] - 77.7:.1f} percentage points")
        print(f"  Distance to 95% goal: {95 - r['accuracy']:.1f} percentage points")
        print(f"  Remaining errors: {r['test_set_size'] - (r['confusion_matrix']['true_negative'] + r['confusion_matrix']['true_positive'])}")

# Task 4: Error Pattern Analysis
best_model = results[0]
print(f"\n" + "="*80)
print(f"ERROR BREAKDOWN: {best_model['model']}")
print("="*80)

cm = best_model['confusion_matrix']
total_errors = cm['false_positive'] + cm['false_negative']

print(f"\nTotal Errors: {total_errors}")
print(f"  False Positives (model too strict): {cm['false_negative']} ({cm['false_negative']/total_errors*100:.1f}%)")
print(f"  False Negatives (model too lenient): {cm['false_positive']} ({cm['false_positive']/total_errors*100:.1f}%)")

print("\nInterpretation:")
if cm['false_negative'] > cm['false_positive']:
    print("  Model is TOO STRICT - flags valid citations as invalid")
    print("  → Need to relax prompt rules or add examples of valid edge cases")
else:
    print("  Model is TOO LENIENT - misses invalid citations")
    print("  → Need to strengthen prompt rules or add validation checks")

# Task 5: Cost vs Performance Analysis
cost_map = {
    'gpt-5-mini': 0.001,
    'gpt-4o-mini': 0.002,
    'gpt-4o': 0.01,
    'claude-sonnet': 0.015,
    'claude-opus': 0.075
}

print("\n" + "="*80)
print("COST vs PERFORMANCE")
print("="*80)

for r in results[:10]:
    model_name = r['model'].lower()
    cost = next((v for k, v in cost_map.items() if k in model_name), None)

    if cost:
        print(f"\n{r['model']}")
        print(f"  Accuracy: {r['accuracy']}%")
        print(f"  Cost/validation: approx ${cost:.4f}")
        print(f"  Cost for 10K validations: approx ${cost * 10000:.2f}")

# Task 6: Path to 95% Analysis
print("\n" + "="*80)
print("PATH TO 95% ACCURACY")
print("="*80)

best = results[0]
current_acc = best['accuracy']
errors_remaining = best['test_set_size'] - (best['confusion_matrix']['true_negative'] + best['confusion_matrix']['true_positive'])
errors_allowed_at_95 = int(best['test_set_size'] * 0.05)
errors_to_fix = errors_remaining - errors_allowed_at_95

print(f"\nCurrent Best: {best['model']}")
print(f"  Current Accuracy: {current_acc}%")
print(f"  Current Errors: {errors_remaining}/{best['test_set_size']}")
print(f"  Errors allowed at 95%: {errors_allowed_at_95}/{best['test_set_size']}")
print(f"  Errors to fix: {errors_to_fix}")
print(f"  Success rate needed: {errors_to_fix}/{errors_remaining} = {errors_to_fix/errors_remaining*100:.1f}%")

print("\nRecommended Next Steps:")
if current_acc >= 95:
    print("  ✅ GOAL ACHIEVED! Consider:")
    print("     - Deploying to production")
    print("     - Monitoring edge cases")
    print("     - Incremental improvements")
elif current_acc >= 90:
    print("  📍 Close to goal. Focus on:")
    print("     - Manual review of remaining errors")
    print("     - Targeted prompt refinements")
    print("     - Few-shot examples for edge cases")
elif current_acc >= 85:
    print("  📍 Making progress. Consider:")
    print("     - Adding source-specific rules to prompt")
    print("     - Ensemble approach (3x validation)")
    print("     - Testing higher reasoning models")
else:
    print("  📍 Significant gap. Recommend:")
    print("     - Full prompt redesign")
    print("     - Different model architecture")
    print("     - Hybrid rule-based + LLM approach")

# Task 7: Save Analysis Report
analysis = {
    "summary": {
        "total_models_tested": len(results),
        "best_model": best['model'],
        "best_accuracy": best['accuracy'],
        "gap_to_goal": 95 - best['accuracy'],
        "errors_to_fix": errors_to_fix
    },
    "top_5_models": [
        {
            "model": r['model'],
            "accuracy": r['accuracy'],
            "f1_invalid": r['metrics']['invalid']['f1'],
            "f1_valid": r['metrics']['valid']['f1']
        }
        for r in results[:5]
    ],
    "error_analysis": {
        "total_errors": total_errors,
        "false_positives": cm['false_negative'],
        "false_negatives": cm['false_positive'],
        "bias": "too_strict" if cm['false_negative'] > cm['false_positive'] else "too_lenient"
    }
}

output_file = Path("Checker_Prompt_Optimization/corrected_results/analysis_report.json")
with open(output_file, 'w') as f:
    json.dump(analysis, f, indent=2)

print(f"\n✅ Saved analysis report to {output_file}")
