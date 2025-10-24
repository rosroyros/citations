#!/usr/bin/env python3
"""
Analyze component name mismatch between ground truth and predictions.
"""
import json
from pathlib import Path
from collections import Counter

# Load invalid citations to see ground truth component names
invalid_file = Path('backend/pseo/optimization/datasets/invalid_citations_enhanced.jsonl')

ground_truth_components = []

with open(invalid_file) as f:
    for line in f:
        data = json.loads(line)
        errors = data.get('errors', [])
        for error in errors:
            component = error.get('component', '')
            ground_truth_components.append(component)

print("="*80)
print("GROUND TRUTH ERROR COMPONENT NAMES")
print("="*80)
print("\nThese are the component names in our dataset:\n")

component_counts = Counter(ground_truth_components)
for component, count in component_counts.most_common():
    print(f"  '{component}': {count} occurrences")

print("\n" + "="*80)
print("PREDICTED ERROR COMPONENT NAMES (from analysis)")
print("="*80)
print("\nThese are the component names the MODEL predicted:\n")

# From the analysis output
predicted_components = [
    'monograph',
    'doi',
    'title',
    'url',
    'periodical title',
    'volume number',
    'article title',
    'volume and issue',
    'journal title',
    'spacing',
    'chapter title',
    'publisher',
]

for component in predicted_components:
    print(f"  '{component}'")

print("\n" + "="*80)
print("THE MISMATCH PROBLEM")
print("="*80)

print("""
The model and ground truth use DIFFERENT naming schemes:

EXAMPLE 1: Title errors
  Ground truth says: 'Title'
  Model predicts: 'article title', 'chapter title', 'title'
  → Sometimes matches ('title'), sometimes doesn't ('article title')

EXAMPLE 2: Journal errors
  Ground truth says: 'Journal'
  Model predicts: 'periodical title', 'journal title'
  → NEVER matches! 'Journal' ≠ 'journal title' ≠ 'periodical title'

EXAMPLE 3: DOI errors
  Ground truth says: 'DOI'
  Model predicts: 'doi', 'url'
  → Case-sensitive mismatch! 'DOI' ≠ 'doi'

EXAMPLE 4: Authors errors
  Ground truth says: 'Authors'
  Model predicts: 'authors' (sometimes), or nothing
  → Case-sensitive mismatch!

The matching code (dspy_validator.py:104-108):

    def normalize_component(comp):
        return comp.lower().strip()

    true_components = set(normalize_component(e['component']) for e in true_errors)
    pred_components = set(normalize_component(e['component']) for e in pred_errors)

This converts to lowercase, so 'Authors' → 'authors', 'DOI' → 'doi'

BUT the real problem is SEMANTIC mismatch:
  - 'Journal' vs 'journal title' vs 'periodical title'
  - 'Title' vs 'article title' vs 'chapter title'
  - 'Publisher' vs 'publisher location'

After .lower(), these STILL don't match!

Result: The model correctly identifies "there's a journal error" but uses
'journal title' while ground truth uses 'journal' → FALSE NEGATIVE + FALSE POSITIVE

This is why we have:
  - High FALSE POSITIVES (48): Model flags 'journal title', ground truth has 'journal' → FP
  - High FALSE NEGATIVES (13): Ground truth has 'journal', model says nothing → FN
  - Low RECALL: We miss matches because names don't align
""")

print("\n" + "="*80)
print("EXAMPLE FROM REAL DATA")
print("="*80)

print("""
Citation: "Schlesselmann, A. J., McNally, R. J., & Held, P. (2025)..."

Ground truth errors: [
    {"component": "Journal", "problem": "Missing journal title", ...}
]

Model prediction errors: [
    {"component": "periodical title", "problem": "...", ...}
]

Comparison:
  true_components = {'journal'}  (after .lower())
  pred_components = {'periodical title'}

  Intersection: {} (EMPTY!)
  → TP = 0, FP = 1, FN = 1

The model was RIGHT that there's a journal/periodical error, but we count it as:
  - FALSE POSITIVE: Predicted 'periodical title' error that's not in ground truth
  - FALSE NEGATIVE: Missed the 'journal' error
""")

print("\n" + "="*80)
print("SOLUTION OPTIONS")
print("="*80)

print("""
1. STANDARDIZE DATASET (recommended)
   - Decide on canonical names: 'authors', 'title', 'journal', 'doi', 'publisher', etc.
   - Update all ground truth to use these names consistently
   - Update prompt to instruct model to use exact names

2. FUZZY MATCHING
   - Map similar names: {'journal', 'journal title', 'periodical title'} → 'journal'
   - More flexible but risks false matches

3. SEMANTIC MATCHING (advanced)
   - Use embeddings to match similar component names
   - Overkill for this problem

RECOMMENDATION: Option 1 - standardize to APA component names:
  - 'authors'
  - 'title'
  - 'journal'
  - 'doi'
  - 'publisher'
  - 'volume'
  - 'issue'
  - 'pages'
  - 'date'
  - 'url'
""")
