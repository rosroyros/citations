# DSPy + GEPA Optimization Plan for Citation Validator
## Complete Strategy with Knowledge Base Integration

---

## Current State Confirmed
- **Output Format:** ✅ Validated
  - Returns `citation_number`, `original`, `source_type`, `errors[]`
  - Each error: `{component, problem, correction}`
  - Empty `errors[]` = valid citation
- **Current Prompt:** Simplified (~15 core rules)
- **Knowledge Base:** 47 detailed rules across 5 categories (excellent resource!)

---

## Phase 1: Environment Setup

### 1.1 Install Dependencies
```bash
# Add to requirements.txt
dspy-ai>=2.4.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
```

### 1.2 Configure DSPy
- Use existing OpenAI API key from `.env`
- Set up DSPy with `gpt-4o-mini` (cost-effective for optimization)

---

## Phase 2: Enhanced Prompt Creation from Knowledge Base

### 2.1 Build Comprehensive Prompt Template
**Goal:** Transform 47 rules in `citation_rules.json` into structured validation prompt

**Implementation:**
```python
# backend/pseo/optimization/prompt_builder.py

def build_comprehensive_prompt(knowledge_base_path):
    """
    Generate validation prompt from citation_rules.json

    Structure:
    - Universal rules (author/date formatting)
    - Source-type specific rules (journal/book/webpage/chapter)
    - Common errors from common_errors.json
    - Output format specification
    """
```

**Output:** New comprehensive starter prompt with all 47 rules organized by:
- Category (author, title, DOI, italics, dates)
- Source type (journal, book, chapter, webpage)
- Common error patterns

### 2.2 Knowledge Base Usage Strategy
- **Prompt construction:** ✅ Use all 47 rules to build initial prompt
- **Training data:** ❌ Do NOT use knowledge base examples
- **Error injection patterns:** ✅ Use `common_errors.json` for programmatic error creation
- **Reference/validation:** ✅ Use to verify our collected citations are truly correct

---

## Phase 3: Dataset Creation (50-80 valid → 200+ total)

### 3.1 Valid Citations Collection (Real Citations Only)

**Method 1: Official APA Style Blog Scraper**
```python
# backend/pseo/optimization/data_collection/apa_scraper.py

def scrape_apa_blog():
    """
    Scrape: https://apastyle.apa.org/style-grammar-guidelines/references/examples
    Extract: All citation examples across source types
    """
```

**Method 2: Purdue OWL Scraper**
```python
def scrape_purdue_owl():
    """
    Scrape APA 7 reference pages for:
    - Journal articles
    - Books
    - Book chapters
    - Webpages
    """
```

**Metadata Schema:**
```python
{
    "citation_id": "apa_blog_001",
    "citation_text": "Smith, J. (2020)...",
    "source_type": "journal article",
    "is_valid": true,
    "metadata": {
        "source": "APA Style Blog",
        "url": "https://apastyle.apa.org/...",
        "section": "Journal Articles",
        "date_collected": "2025-10-17",
        "verified_against_kb": true  # Cross-check with knowledge base
    }
}
```

**Target:** 50-80 real valid citations

### 3.2 Invalid Citations Generation

**Strategy 1: Programmatic Error Injection** (~80-120 variants)
```python
# backend/pseo/optimization/data_collection/error_injector.py

def inject_errors(valid_citation, error_patterns):
    """
    Take valid citation → create variants with errors

    Error patterns from common_errors.json:
    - cap001: Title case in article titles
    - ital001: Missing italics on journal/book
    - doi001: Old DOI format (dx.doi.org)
    - auth001: "and" instead of "&"
    - pub001: Publisher location (APA 6 style)

    Create 2-3 variants per valid citation:
    - Single error (test precision on specific issues)
    - Multiple errors (test complex validation)
    """
```

**Strategy 2: LLM-Generated Edge Cases** (~30-50 examples)
```python
def generate_llm_error_variants():
    """
    Prompt GPT-4: "Create APA 7 citation with [specific violation]"

    Focus on:
    - Edge cases not in programmatic patterns
    - Subtle errors (wrong capitalization after colon)
    - Mixed source type confusion

    Manual review: Ensure realistic & diverse
    """
```

**Metadata for Invalid Citations:**
```python
{
    "citation_id": "error_001",
    "citation_text": "Smith, J. (2020). Wrong Title Case...",
    "source_type": "journal article",
    "is_valid": false,
    "errors": [
        {
            "component": "Title",
            "problem": "Using title case instead of sentence case",
            "correction": "Should be: Wrong title case..."
        }
    ],
    "metadata": {
        "derived_from": "apa_blog_001",
        "error_injection_method": "programmatic",
        "error_types": ["cap001"],
        "knowledge_base_rule_violated": "article_title_sentence_case",
        "date_created": "2025-10-17"
    }
}
```

### 3.3 Dataset Split
- **Training:** 70% (~140 examples)
- **Validation:** 15% (~30 examples) - used during optimization
- **Test (holdout):** 15% (~30 examples) - final evaluation only

**Export Format:** JSONL files in `backend/pseo/optimization/datasets/`

---

## Phase 4: DSPy Implementation

### 4.1 Create DSPy Module
```python
# backend/pseo/optimization/dspy_validator.py

import dspy

class CitationValidator(dspy.Signature):
    """Validate APA 7th edition citations against comprehensive rules"""
    citation = dspy.InputField(desc="Citation text to validate")
    validation_result = dspy.OutputField(
        desc="JSON: {source_type: str, errors: [{component, problem, correction}]}"
    )

class ValidatorModule(dspy.Module):
    def __init__(self, comprehensive_prompt):
        super().__init__()
        self.comprehensive_rules = comprehensive_prompt
        self.validate = dspy.ChainOfThought(CitationValidator)

    def forward(self, citation):
        return self.validate(citation=citation)
```

### 4.2 Define Evaluation Metrics
```python
def validator_metrics(example, prediction, trace=None):
    """
    Calculate precision, recall, F1 for error detection

    Precision: Of all errors flagged, how many are real?
    - TP: Correctly identified errors
    - FP: Incorrectly flagged (false alarms)
    - Precision = TP / (TP + FP)

    Recall: Of all real errors, how many did we catch?
    - FN: Missed errors (false negatives)
    - Recall = TP / (TP + FN)

    F1 Score: Harmonic mean = 2 * (P * R) / (P + R)

    Component-level scoring:
    - Track per-category accuracy (author, title, DOI, etc.)
    - Weight critical errors higher (DOI format > missing period)
    """

    true_errors = set(example.errors)
    pred_errors = set(prediction.errors)

    tp = len(true_errors & pred_errors)
    fp = len(pred_errors - true_errors)
    fn = len(true_errors - pred_errors)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return f1  # GEPA optimizes for this
```

### 4.3 Optimize with GEPA
```python
from dspy.teleprompt import GEPA

# Initialize with comprehensive prompt from knowledge base
comprehensive_prompt = build_comprehensive_prompt('backend/pseo/knowledge_base/citation_rules.json')
student_module = ValidatorModule(comprehensive_prompt)

# Configure GEPA optimizer
optimizer = GEPA(
    metric=validator_metrics,
    breadth=5,    # Try 5 prompt variations per iteration
    depth=3,      # Run 3 optimization rounds
    init_temperature=1.0
)

# Run optimization
optimized_module = optimizer.compile(
    student=student_module,
    trainset=train_examples,
    valset=val_examples,
    max_bootstrapped_demos=4,  # Use 4 few-shot examples in prompt
    max_labeled_demos=2        # Include 2 labeled examples
)
```

---

## Phase 5: Evaluation & Integration

### 5.1 Benchmark Testing
**Compare on holdout test set:**
- Current simplified prompt (15 rules) vs. Optimized comprehensive prompt (47 rules)

**Metrics:**
- ✅ Precision (avoid false positives)
- ✅ Recall (catch all errors)
- ✅ F1 score (primary target)
- ✅ Token usage (cost per validation)
- ✅ Per-category accuracy (author vs. title vs. DOI)

**Success Criteria:**
- F1 ≥ 0.85 (strong performance)
- Recall ≥ 0.90 (catch 90%+ of real errors)
- Precision ≥ 0.80 (limit false alarms to 20%)

### 5.2 Extract Optimized Prompt
```python
# DSPy stores optimized prompt internally
optimized_prompt_text = optimized_module.validate.extended_signature

# Save as new validator prompt
with open('backend/prompts/validator_prompt_optimized.txt', 'w') as f:
    f.write(optimized_prompt_text)
```

### 5.3 Integration Strategy
**Option A: Direct replacement**
- Update `validator_prompt.txt` with optimized version
- Deploy to production

**Option B: A/B testing**
- Run both prompts in parallel
- Track real user validation accuracy
- Gradual rollout based on performance

### 5.4 API Response Format
**No changes needed!** Output remains:
```python
{
    "results": [
        {
            "citation_number": int,
            "original": str,
            "source_type": str,
            "errors": [
                {"component": str, "problem": str, "correction": str}
            ]
        }
    ]
}
```

---

## Phase 6: Iteration & Improvement

### 6.1 Failure Analysis
- If F1 < 0.85: Analyze test set failures
- Identify systematic error patterns (e.g., "always misses subtitle capitalization")
- Add targeted examples to training set
- Re-run GEPA optimization

### 6.2 Dataset Expansion
- Track false positives → add more valid examples in that category
- Track false negatives → add more error examples of that type
- Expand to 300+ examples if needed for robustness

### 6.3 Production Monitoring
- Log validation results in production
- Track user feedback (did they agree with errors flagged?)
- Use real corrections as additional training data

---

## Implementation Order

1. ✅ **Install DSPy/beautifulsoup4** (Phase 1)
2. ✅ **Build comprehensive prompt from knowledge base** (Phase 2.1)
3. ✅ **Create web scrapers** for APA Blog + Purdue OWL (Phase 3.1)
4. ✅ **Collect 50-80 valid citations** with metadata (Phase 3.1)
5. ✅ **Verify citations against knowledge base** (cross-check)
6. ✅ **Build error injection system** from `common_errors.json` (Phase 3.2)
7. ✅ **Generate invalid variants** (~150 total) (Phase 3.2)
8. ✅ **Split dataset** train/val/test (Phase 3.3)
9. ✅ **Implement DSPy module + metrics** (Phase 4)
10. ✅ **Run GEPA optimization** (Phase 4.3)
11. ✅ **Evaluate on test set** (Phase 5.1)
12. ✅ **Extract & deploy optimized prompt** (Phase 5.2-5.3)

---

## Key Decisions Confirmed

✅ **Target:** Citation validator (`validator_prompt.txt`)
✅ **Scope:** Comprehensive (all 47 rules from knowledge base)
✅ **Goals:** Maximize precision + recall (F1 score)
✅ **Valid data:** Real citations from APA Blog + Purdue OWL (50-80)
✅ **Invalid data:** Programmatic error injection + LLM edge cases
✅ **Knowledge base role:** Build prompt, guide error patterns (NOT training examples)
✅ **Output format:** Same as current (no API changes)
✅ **Metrics:** Precision, Recall, F1, per-component accuracy
