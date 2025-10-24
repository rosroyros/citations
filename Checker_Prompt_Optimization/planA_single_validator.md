# Plan A — Single-Stage APA Citation Validator (with Controlled Synthetic Expansion and F1_invalid Metric)

## Overview
A single DSPy + GEPA program that validates whether a given citation string follows **APA 7th Edition** rules.  
Includes a **controlled synthetic expansion phase** to grow the labeled dataset before optimization and uses a **custom F1_invalid metric** to prioritize catching incorrect citations.

---

## Objectives
- Evaluate citations for APA compliance in structure, punctuation, and ordering.
- Be aware of italics via Markdown (e.g., `_Journal of Cognitive Science_`).
- Use controlled synthetic generation to augment limited real examples before optimization.
- Optimize prompt performance using **F1_invalid** — the F1 score computed only for the "invalid" class.

---

## Workflow Overview
```
1. Collect ~100–200 curated examples
2. Run Synthetic Expansion Phase → generate 3–5× more diverse examples
3. Merge & clean dataset
4. Run GEPA optimization on the combined dataset
5. Evaluate & iterate using F1_invalid
```

---

## Synthetic Expansion Phase

### Purpose
To increase coverage of APA formats, punctuation variants, and source diversity without manually labeling hundreds of samples.

### Mechanism
Use the foundation model to generate new labeled examples from curated seeds under strictly guided prompts and validation heuristics.

### Expansion Prompt
> You are generating **APA 7th edition citation examples** for a validator.  
> Given a seed example, create 5 variations — mix valid and invalid.  
> Vary punctuation, italics, author counts, and presence/absence of DOIs and other key elements
> Return each as a JSON object with fields: `citation`, `is_valid`, `explanation`.  
> At least one variant per seed must be invalid.

### Controls
- Expand only from curated seed examples.
- Discard duplicates and malformed results automatically.
- Run validation to ensure JSON integrity and Markdown balance.

### Example Output
```json
{
  "citation": "Doe, A., & Lee, B. (2019). _Social networks and cognition_. Cambridge University Press.",
  "is_valid": true
},
{
  "citation": "Doe, A., Lee, B. 2019 Social networks & cognition Cambridge University Press",
  "is_valid": false
}
```

---

## GEPA Phase

| Step | Description |
|------|--------------|
| **Dataset size post-expansion** | ~500–800 examples |
| **Training/Validation split** | 80% training / 20% validation (validation unseen during optimization) |
| **Optional test set** | Additional 10% final evaluation |
| **Metric** | F1_invalid |
| **Iterations** | 20–40 |
| **Beam width** | 3–5 |

---

## Custom Metric — F1_invalid

We measure only the F1 score for the **invalid** class, which balances recall (catching invalids) and precision (avoiding false alarms).

Formula:  
\( F1_{invalid} = 2 \times \frac{Precision \times Recall}{Precision + Recall} \)

### Example Implementation
```python
def per_class_f1(preds, gold, target="invalid"):
    tp = sum((p == target) and (g == target) for p, g in zip(preds, gold))
    fp = sum((p == target) and (g != target) for p, g in zip(preds, gold))
    fn = sum((p != target) and (g == target) for p, g in zip(preds, gold))
    precision = tp / (tp + fp + 1e-8)
    recall = tp / (tp + fn + 1e-8)
    return 2 * precision * recall / (precision + recall + 1e-8)
```

### DSPy Setup Snippet
```python
train, val = dspy.split_dataset(examples, val_size=0.2, seed=42)

metric = dspy.Metric(
    name="F1_invalid",
    func=lambda preds, gold: per_class_f1(preds, gold, target="invalid")
)

gepa = dspy.GEPA(
    signature=APAValidator,
    metric=metric,
    train_examples=train,
    validation_examples=val
)

best_prompt = gepa.run()
```

---

## Model Signature
```python
class APAValidator(dspy.Signature):
    citation: str  # Markdown with _italics_
    -> is_valid: bool
    -> explanation: str
```

---

## Preprocessing
- Convert italics → `_Markdown_`
- Strip extra whitespace and normalize punctuation

## Evaluation
- Metric: F1_invalid ≥ 0.85 preferred
- Qualitative review of explanations for reasoning quality
