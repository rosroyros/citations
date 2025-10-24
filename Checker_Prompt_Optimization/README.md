# APA Citation Validator - Prompt Optimization

Optimizing a DSPy+GEPA prompt for validating APA 7th Edition citations using Plan A (single-stage validator with synthetic expansion).

## Overview

This project implements a systematic approach to optimize an LLM prompt for detecting invalid APA citations:

1. **Synthetic Expansion** - Generate diverse variants from 124 curated examples
2. **Merge & Clean** - Combine seeds + synthetics, deduplicate
3. **GEPA Optimization** - Optimize prompt using F1_invalid metric
4. **Evaluation** - Test on held-out validation set
5. **Reporting** - Comprehensive HTML report with all predictions

## Files

### Data Files
- `manualy_curated_citations_raw_20251023.jsonl` - 124 manually curated citations (all valid)
- `expanded_citations_synthetic.jsonl` - ~620 synthetic variants (generated)
- `final_merged_dataset.jsonl` - Combined & deduplicated dataset

### Scripts
- `synthetic_expansion.py` - Generate 5 variants per seed using GPT-4o
- `merge_and_clean_dataset.py` - Merge seeds + synthetics, deduplicate
- `run_gepa_optimization.py` - GEPA optimization with F1_invalid metric
- `generate_html_report.py` - Generate comprehensive HTML report
- `run_full_optimization.sh` - Master script to run entire pipeline

### Outputs
- `optimized_output/optimized_validator.json` - Optimized DSPy module
- `optimized_output/optimization_metrics.json` - Validation metrics
- `optimized_output/optimization_report.html` - **Interactive HTML report**

## Quick Start

### Prerequisites
```bash
# Activate virtual environment
source ../venv/bin/activate

# Set OpenAI API key
export OPENAI_API_KEY="your-key-here"

# Install dependencies (if not already installed)
pip install dspy-ai openai tqdm
```

### Run Full Pipeline
```bash
cd Checker_Prompt_Optimization
./run_full_optimization.sh
```

This will:
1. Generate ~620 synthetic variants (15-30 min)
2. Merge and clean dataset (< 1 min)
3. Run GEPA optimization with 30 iterations (30-60 min)
4. Generate HTML report (5-10 min)

**Total time: ~1-2 hours**

### Run Individual Steps

```bash
# Step 1: Synthetic expansion
python3 synthetic_expansion.py

# Step 2: Merge and clean
python3 merge_and_clean_dataset.py

# Step 3: GEPA optimization
python3 run_gepa_optimization.py

# Step 4: Generate report
python3 generate_html_report.py
```

## Configuration

### Model Settings
- **Synthetic expansion**: GPT-4o (higher quality variants)
- **GEPA candidates**: GPT-4o-mini (matches production)
- **GEPA reflection**: GPT-4o (higher quality reasoning)

### Optimization Parameters
- **Iterations**: 30
- **Beam width**: 4
- **Train/Val split**: 80/20
- **Metric**: F1_invalid (F1 score for invalid class)

### Synthetic Expansion
- **Variants per seed**: 5
- **Min invalid per seed**: 2
- **Min valid per seed**: 2
- **Variation types**: punctuation, italics, author format, DOI, spacing

## Output Report

The HTML report includes:

### Metrics Dashboard
- Overall accuracy
- F1 score (invalid) - primary metric
- Precision & recall for both classes
- Confusion matrix

### Interactive Table
- All test set predictions with ground truth
- Color-coded validity badges
- Explanation for each prediction
- Metadata (source type, curated vs synthetic)
- **Filterable** by status, source, correctness

### Filters
- All results
- Correct predictions only
- Incorrect predictions only
- Curated citations only
- Synthetic citations only

## Metrics Explained

### F1_invalid
The F1 score computed only for the "invalid" class. This balances:
- **Precision**: Of citations flagged as invalid, how many are truly invalid?
- **Recall**: Of truly invalid citations, how many did we catch?

Formula: `F1 = 2 × (Precision × Recall) / (Precision + Recall)`

**Target**: F1_invalid ≥ 0.85

### Why F1_invalid?
We prioritize catching invalid citations (recall) while minimizing false alarms (precision). Standard accuracy can be misleading if the dataset is imbalanced.

## Dataset Structure

### Curated Seeds (124 citations)
```json
{
  "citation": "Jackson, L. M. (2019). _The psychology of prejudice_...",
  "is_valid": true,
  "explanation": "Manually curated valid APA 7th edition citation",
  "metadata": {
    "source": "manual_curation",
    "seed_id": "manual_1761230294238",
    "source_type": "book"
  }
}
```

### Synthetic Variants
```json
{
  "citation": "Jackson L.M. 2019 The psychology of prejudice...",
  "is_valid": false,
  "explanation": "Missing punctuation and improper name formatting",
  "metadata": {
    "source": "synthetic_expansion",
    "seed_id": "manual_1761230294238",
    "model": "gpt-4o"
  }
}
```

## Plan A Reference

This implementation follows `planA_single_validator.md`:
- Single-stage validator (not multi-stage)
- Controlled synthetic expansion before optimization
- F1_invalid as optimization metric
- DSPy + GEPA for prompt optimization
- Markdown italics support (`_text_`)

## Troubleshooting

### "OPENAI_API_KEY not set"
```bash
export OPENAI_API_KEY="sk-..."
```

### "Dataset not found"
Run steps in order (expansion → merge → optimization → report)

### Optimization takes too long
Reduce `num_iterations` in `run_gepa_optimization.py` (line 227)

### Out of API credits
Expansion generates ~123 × 5 = ~615 GPT-4o calls
Optimization generates many GPT-4o-mini calls over 30 iterations

## Next Steps

After optimization:
1. Review HTML report for accuracy and failure modes
2. Examine F1_invalid score - target ≥ 0.85
3. Analyze incorrect predictions to identify gaps
4. If needed: add more diverse seed examples and re-run
5. Extract optimized prompt from `optimized_validator.json`
6. Deploy to production citation checker

## License

Part of the Citations project.
