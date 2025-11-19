# Model Performance Comparison (Corrected Ground Truth)

## Overview

- **Test Set Size**: 121 citations
- **Models Tested**: 8
- **Ground Truth Corrections Applied**: 12
- **Invalid Citations**: 75
- **Valid Citations**: 46

## Results

| Rank | Model | Accuracy | Correct | Errors | F1 (Invalid) | F1 (Valid) |
|------|-------|----------|---------|--------|--------------|------------|
| 1 | GPT-5-mini_optimized | 82.6% | 100/121 | 21 | 87.0% | 74.1% |
| 2 | GPT-5_optimized | 80.2% | 97/121 | 24 | 85.4% | 69.2% |
| 3 | GPT-5-mini_baseline | 66.1% | 80/121 | 41 | 72.1% | 56.8% |
| 4 | GPT-4o_optimized | 65.3% | 79/121 | 42 | 74.1% | 47.5% |
| 5 | GPT-5_baseline | 62.0% | 75/121 | 46 | 69.7% | 48.9% |
| 6 | GPT-4o-mini_optimized | 57.0% | 69/121 | 52 | 54.4% | 59.4% |
| 7 | GPT-4o-mini_baseline | 52.9% | 64/121 | 57 | 41.2% | 60.7% |
| 8 | GPT-4o_baseline | 51.2% | 62/121 | 59 | 41.6% | 58.2% |

## Key Findings

- **Best Model**: GPT-5-mini_optimized with 82.6% accuracy
- **Worst Model**: GPT-4o_baseline with 51.2% accuracy
- **Accuracy Range**: 51.2% - 82.6% (31.4 percentage points)

## Baseline vs Optimized Comparison


### GPT-4o
- Baseline: 51.2%
- Optimized: 65.3%
- Improvement: +14.1 percentage points

### GPT-4o-mini
- Baseline: 52.9%
- Optimized: 57.0%
- Improvement: +4.1 percentage points

### GPT-5
- Baseline: 62.0%
- Optimized: 80.2%
- Improvement: +18.2 percentage points

### GPT-5-mini
- Baseline: 66.1%
- Optimized: 82.6%
- Improvement: +16.5 percentage points
