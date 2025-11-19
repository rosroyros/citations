import json
from pathlib import Path

# Load predictions
preds_file = Path('competitive_benchmark/GPT-5-mini_optimized_detailed_121_corrected.jsonl')
predictions = []
with open(preds_file, 'r') as f:
    for line in f:
        predictions.append(json.loads(line))

# Load ground truth for source metadata
gt_file = Path('Checker_Prompt_Optimization/validation_set_CORRECTED.jsonl')
gt_map = {}
with open(gt_file, 'r') as f:
    for line in f:
        item = json.loads(line)
        gt_map[item['citation']] = item

# Extract errors
errors = []
for pred in predictions:
    if not pred.get('correct', True):
        citation = pred['citation']
        gt = gt_map.get(citation, {})
        errors.append({
            'citation': citation,
            'source': gt.get('metadata', {}).get('source', 'unknown'),
            'predicted': pred['predicted'],
            'ground_truth': pred['ground_truth'],
        })

# Separate FP and FN
false_positives = [e for e in errors if e['ground_truth'] and not e['predicted']]
false_negatives = [e for e in errors if not e['ground_truth'] and e['predicted']]

print("="*80)
print("FALSE POSITIVES (Model too strict - flags valid as invalid)")
print("="*80)
print(f"\nTotal: {len(false_positives)} cases\n")

for i, fp in enumerate(false_positives, 1):
    print(f"\n{i}. {fp['citation']}")
    print(f"   Source: {fp['source']}")

print("\n\n" + "="*80)
print("FALSE NEGATIVES (Model too lenient - approves invalid)")
print("="*80)
print(f"\nTotal: {len(false_negatives)} cases\n")

for i, fn in enumerate(false_negatives, 1):
    print(f"\n{i}. {fn['citation']}")
    print(f"   Source: {fn['source']}")

# Save to file for easier review
with open('Checker_Prompt_Optimization/ERROR_CASES_FOR_REVIEW.txt', 'w') as f:
    f.write("="*80 + "\n")
    f.write("FALSE POSITIVES (Model too strict - flags valid as invalid)\n")
    f.write("="*80 + "\n")
    f.write(f"\nTotal: {len(false_positives)} cases\n\n")

    for i, fp in enumerate(false_positives, 1):
        f.write(f"\n{i}. {fp['citation']}\n")
        f.write(f"   Source: {fp['source']}\n")

    f.write("\n\n" + "="*80 + "\n")
    f.write("FALSE NEGATIVES (Model too lenient - approves invalid)\n")
    f.write("="*80 + "\n")
    f.write(f"\nTotal: {len(false_negatives)} cases\n\n")

    for i, fn in enumerate(false_negatives, 1):
        f.write(f"\n{i}. {fn['citation']}\n")
        f.write(f"   Source: {fn['source']}\n")

print(f"\n\n✅ Saved detailed error cases to Checker_Prompt_Optimization/ERROR_CASES_FOR_REVIEW.txt")
