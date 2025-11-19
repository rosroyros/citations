#!/usr/bin/env python3
"""
Recalculate accuracy for all models using corrected ground truth.
Task: citations-wzc
"""

import json
from pathlib import Path
from glob import glob
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

# Step 1: Identify all tested models
print("="*80)
print("STEP 1: Identifying All Tested Models")
print("="*80)

result_files = glob("competitive_benchmark/*_detailed_121_corrected.jsonl")
models = []

for file in result_files:
    filename = Path(file).name
    # Remove both suffixes to get model name
    model_name = filename.replace("_detailed_121_corrected.jsonl", "")
    models.append({
        "name": model_name,
        "file": file
    })

# Sort for consistent ordering
models = sorted(models, key=lambda x: x['name'])

print(f"\nFound {len(models)} models to recompute:")
for m in models:
    print(f"  - {m['name']:<40} {m['file']}")

# Step 2: Load corrected ground truth corrections
print("\n" + "="*80)
print("STEP 2: Loading Corrected Ground Truth")
print("="*80)

corrections_file = Path("Checker_Prompt_Optimization/ALL_GROUND_TRUTH_CORRECTIONS.json")
with open(corrections_file, 'r') as f:
    corrections_data = json.load(f)

# Create a map of citation -> corrected ground truth
corrections_map = {}
for correction in corrections_data['ground_truth_corrections']:
    citation = correction['citation']
    corrected_gt = correction['corrected_ground_truth']
    # Convert string labels to boolean
    corrected_gt_bool = (corrected_gt == "VALID")
    corrections_map[citation] = corrected_gt_bool

print(f"Loaded {len(corrections_map)} ground truth corrections")
print(f"Corrections changing VALID->INVALID: {sum(1 for c in corrections_data['ground_truth_corrections'] if c['corrected_ground_truth'] == 'INVALID')}")
print(f"Corrections changing INVALID->VALID: {sum(1 for c in corrections_data['ground_truth_corrections'] if c['corrected_ground_truth'] == 'VALID')}")

# Step 3: Recompute metrics for each model
print("\n" + "="*80)
print("STEP 3: Recomputing Metrics for All Models")
print("="*80)

all_results = []

for model_info in models:
    print(f"\nProcessing: {model_info['name']}")

    # Load predictions (which now include corrected ground truth)
    with open(model_info['file'], 'r') as f:
        predictions = [json.loads(line) for line in f]

    print(f"  Loaded {len(predictions)} predictions")

    # Extract ground truth and predictions
    y_true = []
    y_pred = []

    for pred in predictions:
        citation = pred['citation']
        # Use the ground truth from the file (which has been corrected)
        y_true.append(pred['ground_truth'])
        y_pred.append(pred['predicted'])

    # Verify we have all citations
    print(f"  Test set size: {len(y_true)}")

    # Compute metrics
    accuracy = accuracy_score(y_true, y_pred)
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, average=None, labels=[False, True]
    )
    cm = confusion_matrix(y_true, y_pred, labels=[False, True])

    # Count errors
    errors = sum(1 for t, p in zip(y_true, y_pred) if t != p)
    correct = len(y_true) - errors

    results = {
        "model": model_info['name'],
        "test_set_size": len(y_true),
        "accuracy": round(accuracy * 100, 2),
        "correct": correct,
        "errors": errors,
        "metrics": {
            "invalid": {
                "precision": round(precision[0] * 100, 2),
                "recall": round(recall[0] * 100, 2),
                "f1": round(f1[0] * 100, 2),
                "support": int(support[0])
            },
            "valid": {
                "precision": round(precision[1] * 100, 2),
                "recall": round(recall[1] * 100, 2),
                "f1": round(f1[1] * 100, 2),
                "support": int(support[1])
            }
        },
        "confusion_matrix": {
            "true_negative": int(cm[0,0]),
            "false_positive": int(cm[0,1]),
            "false_negative": int(cm[1,0]),
            "true_positive": int(cm[1,1])
        }
    }

    all_results.append(results)
    print(f"  ✓ Corrected Accuracy: {results['accuracy']}% ({correct}/{len(y_true)} correct, {errors} errors)")

# Step 4: Save corrected results
print("\n" + "="*80)
print("STEP 4: Saving Corrected Results")
print("="*80)

output_dir = Path("Checker_Prompt_Optimization/corrected_results")
output_dir.mkdir(exist_ok=True)

# Save individual model results
for result in all_results:
    output_file = output_dir / f"{result['model']}_corrected.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"  ✓ Saved {output_file.name}")

# Save summary comparison
summary_file = output_dir / "all_models_corrected_summary.json"
with open(summary_file, 'w') as f:
    json.dump({
        "task": "citations-wzc",
        "description": "Recalculated accuracy for all models using corrected ground truth",
        "models_tested": len(all_results),
        "test_set_size": 121,
        "corrections_applied": len(corrections_map),
        "results": all_results
    }, f, indent=2)
print(f"\n  ✓ Saved summary: {summary_file.name}")

# Step 5: Generate comparison table
print("\n" + "="*80)
print("STEP 5: Model Comparison (Corrected Ground Truth)")
print("="*80)

# Sort by corrected accuracy
sorted_results = sorted(all_results, key=lambda x: x['accuracy'], reverse=True)

# Print table
print(f"\n{'Model':<40} {'Accuracy':<12} {'Correct':<10} {'Errors':<8} {'F1 Invalid':<12} {'F1 Valid':<12}")
print("-"*100)

for r in sorted_results:
    model = r['model']
    acc = f"{r['accuracy']:.1f}%"
    correct = f"{r['correct']}/{r['test_set_size']}"
    errors = str(r['errors'])
    f1_inv = f"{r['metrics']['invalid']['f1']:.1f}%"
    f1_val = f"{r['metrics']['valid']['f1']:.1f}%"
    print(f"{model:<40} {acc:<12} {correct:<10} {errors:<8} {f1_inv:<12} {f1_val:<12}")

print("="*100)

# Save comparison table to markdown
markdown_file = output_dir / "model_comparison.md"
with open(markdown_file, 'w') as f:
    f.write("# Model Performance Comparison (Corrected Ground Truth)\n\n")
    f.write("## Overview\n\n")
    f.write(f"- **Test Set Size**: {all_results[0]['test_set_size']} citations\n")
    f.write(f"- **Models Tested**: {len(all_results)}\n")
    f.write(f"- **Ground Truth Corrections Applied**: {len(corrections_map)}\n")
    f.write(f"- **Invalid Citations**: {all_results[0]['metrics']['invalid']['support']}\n")
    f.write(f"- **Valid Citations**: {all_results[0]['metrics']['valid']['support']}\n\n")

    f.write("## Results\n\n")
    f.write("| Rank | Model | Accuracy | Correct | Errors | F1 (Invalid) | F1 (Valid) |\n")
    f.write("|------|-------|----------|---------|--------|--------------|------------|\n")
    for i, r in enumerate(sorted_results, 1):
        f.write(f"| {i} | {r['model']} | {r['accuracy']:.1f}% | {r['correct']}/{r['test_set_size']} | {r['errors']} | {r['metrics']['invalid']['f1']:.1f}% | {r['metrics']['valid']['f1']:.1f}% |\n")

    f.write("\n## Key Findings\n\n")
    best = sorted_results[0]
    worst = sorted_results[-1]
    f.write(f"- **Best Model**: {best['model']} with {best['accuracy']:.1f}% accuracy\n")
    f.write(f"- **Worst Model**: {worst['model']} with {worst['accuracy']:.1f}% accuracy\n")
    f.write(f"- **Accuracy Range**: {worst['accuracy']:.1f}% - {best['accuracy']:.1f}% ({best['accuracy'] - worst['accuracy']:.1f} percentage points)\n")

    # Compare baseline vs optimized for each model family
    f.write("\n## Baseline vs Optimized Comparison\n\n")

    model_families = {}
    for r in all_results:
        # Extract model family (e.g., "GPT-4o-mini" from "GPT-4o-mini_baseline")
        if '_baseline' in r['model']:
            family = r['model'].replace('_baseline', '')
            if family not in model_families:
                model_families[family] = {}
            model_families[family]['baseline'] = r
        elif '_optimized' in r['model']:
            family = r['model'].replace('_optimized', '')
            if family not in model_families:
                model_families[family] = {}
            model_families[family]['optimized'] = r

    for family in sorted(model_families.keys()):
        data = model_families[family]
        if 'baseline' in data and 'optimized' in data:
            baseline_acc = data['baseline']['accuracy']
            optimized_acc = data['optimized']['accuracy']
            improvement = optimized_acc - baseline_acc
            f.write(f"\n### {family}\n")
            f.write(f"- Baseline: {baseline_acc:.1f}%\n")
            f.write(f"- Optimized: {optimized_acc:.1f}%\n")
            f.write(f"- Improvement: {improvement:+.1f} percentage points\n")

print(f"\n✓ Saved comparison table: {markdown_file.name}")

print("\n" + "="*80)
print("✅ COMPLETE: All models recalculated with corrected ground truth")
print("="*80)
print(f"\nOutput files:")
print(f"  - {output_dir}/")
print(f"    - <model>_corrected.json (8 files)")
print(f"    - all_models_corrected_summary.json")
print(f"    - model_comparison.md")
