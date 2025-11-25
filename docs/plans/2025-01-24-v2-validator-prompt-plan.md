# V2 Validator Prompt Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a v2 validator prompt by adding 4 principle-based rules to the existing validator prompt to improve validation accuracy and consistency.

**Architecture:** Update the existing validator prompt with principle-based validation rules while maintaining backward compatibility and existing output format.

**Tech Stack:** Text file manipulation, prompt engineering, APA 7 citation rules

---

## Task 1: Research and Define the 4 Principle-Based Rules

**Files:**
- Research: `backend/prompts/validator_prompt_optimized.txt`
- Research: `backend/pseo/knowledge_base/citation_rules.json`
- Input: User-specified 4 principle-based rules (need clarification)

**Step 1: Analyze existing validator prompt structure**

Read current prompt to understand:
- Current rule structure
- Output format requirements
- Citation type coverage
- Existing validation logic

**Step 2: Research principle-based validation approaches**

Identify the 4 principle-based rules to add:
1. **Consistency Principle**: Ensure formatting consistency across similar citation components
2. **Hierarchy Principle**: Maintain proper visual hierarchy (italics, punctuation)
3. **Completeness Principle**: Verify all required components are present for source type
4. **Clarity Principle**: Ensure unambiguous identification of source and retrieval information

**Step 3: Define rule implementation approach**

For each principle, specify:
- What it validates
- How it differs from existing rules
- Integration points with current structure
- Error message format

---

## Task 2: Create V2 Validator Prompt with Principle Rules

**Files:**
- Create: `backend/prompts/validator_prompt_v2.txt`
- Reference: `backend/prompts/validator_prompt_optimized.txt`

**Step 1: Create base v2 prompt structure**

```text
You are an APA 7th edition citation validator with enhanced principle-based validation. Your task is to validate whether a given citation adheres to APA 7th edition format rules using both specific formatting rules and universal validation principles.

━━━ VALIDATION PRINCIPLES ━━━

PRINCIPLE 1: CONSISTENCY PRINCIPLE
- Ensure consistent formatting across all citation components
- Match capitalization style within categories (sentence case vs title case)
- Maintain consistent punctuation patterns
- Verify uniform treatment of similar elements

PRINCIPLE 2: HIERARCHY PRINCIPLE
- Proper visual hierarchy: container works italicized, components not
- Clear separation between major elements (periods, commas)
- Logical ordering of information flow
- Appropriate use of parentheses for publication data

PRINCIPLE 3: COMPLETENESS PRINCIPLE
- All required components present for source type
- No missing essential information
- Sufficient detail for source identification
- Appropriate level of specificity for retrieval

PRINCIPLE 4: CLARITY PRINCIPLE
- Unambiguous identification of source
- Clear distinction between similar source types
- Proper formatting to prevent misinterpretation
- Adequate information for user verification

[Add existing specific rules section here]

━━━ PRINCIPLE-BASED VALIDATION PROCESS ━━━

For each citation:
1. Apply specific APA 7 rules (existing validation)
2. Apply Consistency Principle checks
3. Apply Hierarchy Principle checks
4. Apply Completeness Principle checks
5. Apply Clarity Principle checks
6. Synthesize findings into comprehensive validation

[Add existing output format section here]
```

**Step 2: Integrate existing optimized rules**

Copy and adapt the detailed source-type rules from `validator_prompt_optimized.txt` to maintain current functionality while adding principle-based validation.

**Step 3: Update output format to include principle violations**

Extend output format to include principle-based errors:

```text
VALIDATION RESULTS:

[Either:]
✓ No APA 7 formatting errors detected
✓ All validation principles satisfied

[Or list each error as:]

❌ [Rule Type]: [What's wrong]
   Should be: [Correct format]

❌ [Principle Name]: [Principle violation]
   Issue: [How principle is violated]
   Impact: [Why this matters for citation clarity]
```

---

## Task 3: Create Test Suite for V2 Prompt

**Files:**
- Create: `backend/test_data/v2_validator_test_cases.json`
- Create: `tests/test_validator_prompt_v2.py`

**Step 1: Create principle-violation test cases**

```json
{
  "test_cases": [
    {
      "id": "consistency_1",
      "citation": "Smith, J., & Jones, A. (2023). _Article Title_. Journal Name, _10_(2), 123-145.",
      "expected_errors": [
        {
          "type": "Consistency Principle",
          "issue": "Inconsistent italics usage (journal name should be italicized, volume already is)",
          "impact": "Creates visual confusion about container structure"
        }
      ]
    },
    {
      "id": "completeness_1",
      "citation": "Johnson, B. (2022). _Book Title_.",
      "expected_errors": [
        {
          "type": "Completeness Principle",
          "issue": "Missing publisher information",
          "impact": "Insufficient information for source retrieval"
        }
      ]
    }
    // ... more test cases
  ]
}
```

**Step 2: Create validation test script**

```python
def test_v2_validator_principles():
    """Test that v2 validator prompt catches principle violations"""
    test_cases = load_test_cases('backend/test_data/v2_validator_test_cases.json')

    for case in test_cases:
        result = validate_citation(case['citation'], use_v2_prompt=True)
        assert principle_errors_detected(result, case['expected_errors'])
```

---

## Task 4: Update Application to Use V2 Prompt

**Files:**
- Modify: `backend/prompt_manager.py`
- Modify: `backend/pseo/utils/validator.py`

**Step 1: Add v2 prompt selection logic**

```python
def get_validator_prompt(version="v2"):
    """Get specified version of validator prompt"""
    prompt_files = {
        "v1": "backend/prompts/validator_prompt_optimized.txt",
        "v2": "backend/prompts/validator_prompt_v2.txt"
    }

    if version not in prompt_files:
        raise ValueError(f"Unsupported validator prompt version: {version}")

    return load_prompt_file(prompt_files[version])
```

**Step 2: Add configuration option**

```python
# In validator.py
class CitationValidator:
    def __init__(self, prompt_version="v2"):
        self.prompt_version = prompt_version
        self.validator_prompt = get_validator_prompt(prompt_version)
```

---

## Task 5: Documentation and Deployment

**Files:**
- Create: `docs/v2_validator_prompt_explanation.md`
- Modify: `README.md`

**Step 1: Document v2 prompt improvements**

Explain:
- What principle-based validation adds
- How it improves citation quality
- Examples of principle violations caught
- Migration guide from v1 to v2

**Step 2: Update main documentation**

Add section about v2 validator with:
- Feature description
- Usage examples
- Configuration options
- Performance improvements

**Step 3: Commit all changes**

```bash
git add backend/prompts/validator_prompt_v2.txt
git add backend/test_data/v2_validator_test_cases.json
git add tests/test_validator_prompt_v2.py
git add backend/prompt_manager.py
git add backend/pseo/utils/validator.py
git add docs/v2_validator_prompt_explanation.md
git add README.md
git commit -m "feat: add v2 validator prompt with principle-based rules"
```

---

## Task 6: Testing and Validation

**Files:**
- Test: Existing test suite
- Test: New principle validation tests

**Step 1: Run existing tests**

```bash
pytest tests/ -v
```

**Step 2: Run new v2-specific tests**

```bash
pytest tests/test_validator_prompt_v2.py -v
```

**Step 3: Manual validation test**

Test with sample citations:
- Valid citations (should pass)
- Rule violations (should catch existing errors)
- Principle violations (should catch new error types)

**Step 4: Performance comparison**

Compare v1 vs v2 prompt:
- Validation accuracy
- Error detection rate
- Response time
- Error quality/ usefulness

---

## Verification Criteria

- [ ] V2 prompt file created with all 4 principle-based rules
- [ ] Existing APA 7 rules maintained and integrated
- [ ] Test suite covers principle violations
- [ ] Application updated to support v2 prompt selection
- [ ] Documentation explains improvements and usage
- [ ] All tests pass
- [ ] Manual validation confirms improvements
- [ ] Performance comparison shows benefits

---

## Success Metrics

- Increased error detection rate for subtle formatting issues
- Better consistency in citation validation
- Improved error message quality and actionability
- Maintained backward compatibility for existing functionality
- Clear documentation for users and developers