# {{ title }}

{{ description }}

---

<div class="quick-ref-box">
<h2>🔍 What to Look For</h2>
<div class="template-box">
{{ quick_reference_template }}
</div>
<p style="margin-top: 1rem; font-size: 0.875rem; color: #6b7280;"><strong>Quick Check:</strong> Scan your citations for these key indicators of correct {{ validation_element|replace('_', ' ') }} formatting.</p>
</div>

---

<div class="mini-checker">
<h4>🔍 Try It Out</h4>
<p>Paste a citation to check its {{ validation_element|replace('_', ' ') }} formatting</p>
<textarea placeholder="Author, A. A. (Year). Title of work..."></textarea>
<button>Check {{ validation_element|replace('_', ' ')|title }}</button>
</div>

---

## Why {{ validation_element|replace('_', ' ')|title }} Matters in APA Citations

### Impact on Readability
Proper {{ validation_element|replace('_', ' ') }} formatting ensures your reference list is professional and easy to read. When {{ validation_element|replace('_', ' ') }} is formatted correctly, readers can quickly identify the key components of each citation and locate the sources themselves.

### Impact on Credibility
{{ validation_element|replace('_', ' ')|title }} errors can undermine your academic credibility. Instructors and journal editors often view formatting mistakes as a lack of attention to detail, which may affect how they evaluate the quality of your research.

### Common Consequences
- **Grade deductions:** Typical penalties range from 1-5 points per error
- **Journal rejections:** Many journals reject papers with formatting issues without review
- **Reader confusion:** Incorrect {{ validation_element|replace('_', ' ') }} can make sources difficult to identify

---

## What Correct {{ validation_element|replace('_', ' ')|title }} Formatting Looks Like

### The Rule
{{ what_to_look_for_rules }}

**Official APA Guidance:**
> {{ apa_official_guidance }}

### Visual Examples

**Correct Format:**
✅ {{ correct_example }}

**Incorrect Format:**
❌ {{ incorrect_example }}

### Key Rules to Remember

{{ key_rules }}

---

## Step-by-Step: How to Check {{ validation_element|replace('_', ' ')|title }}

Follow this systematic process to validate {{ validation_element|replace('_', ' ') }} in your citations:

### Preparation (1-2 minutes)

**Step 1: Gather your citations**
- [ ] Open your reference list
- [ ] Have APA manual or guide available
- [ ] Note which source types you have

**Step 2: Understand what to check**
- [ ] Review {{ validation_element|replace('_', ' ') }} rules
- [ ] Note differences by source type
- [ ] Identify your high-risk citations

### Checking Process (3-5 minutes per citation)

{{ step_by_step_instructions }}

### Verification (1-2 minutes)

**Step {{ verification_step_number }}: Cross-check all citations**
- [ ] Compare similar citations for consistency
- [ ] Verify against official APA examples
- [ ] Use automated checker for verification

**Step {{ final_step_number }}: Document changes**
- [ ] Track which citations were corrected
- [ ] Note patterns in your errors
- [ ] Save corrected version

### Time-Saving Tips

💡 **Batch similar source types:** Check all journal articles together, then all books, etc.

💡 **Use Find & Replace:** {{ find_replace_strategy }}

💡 **Create a checklist:** Print the validation checklist and check off as you go

---

## Common {{ validation_element|replace('_', ' ')|title }} Errors

These are the most frequent {{ validation_element|replace('_', ' ') }} errors found in APA citations:

{% for error in common_errors %}
### {{ error.error_name }}

**How common:** Appears in {{ error.frequency }}% of citations

**What it looks like:**
❌ {{ error.wrong_example }}

**Why it's wrong:**
{{ error.explanation }}

**How to spot it:**
{{ error.detection_method }}

**How to fix:**
✅ {{ error.correct_example }}

**Quick fix:** {{ error.quick_fix }}

---

{% endfor %}

## Error Frequency Chart

| Error Type | Frequency | Severity | Easy to Spot? |
|------------|-----------|----------|---------------|
{% for error in common_errors %}
| {{ error.error_name }} | {{ error.frequency }} | {{ error.severity }} | {{ error.easy_to_spot }} |
{% endfor %}

**Severity Key:**
- **High:** Affects citation accuracy or findability
- **Medium:** Formatting issue that doesn't affect meaning
- **Low:** Style preference

---

## How {{ validation_element|replace('_', ' ')|title }} Varies by Source Type

Different source types have different {{ validation_element|replace('_', ' ') }} requirements:

{% for source_type in affected_source_types %}
### {{ source_type.name|title }}
**{{ validation_element|replace('_', ' ')|title }} format:** {{ source_type.format_description }}
**What to check:** {{ source_type.check_items }}
**Example:** {{ source_type.example }}

{% endfor %}

## Quick Reference Table

| Source Type | {{ validation_element|replace('_', ' ')|title }} Format | Key Rule | Common Error |
|-------------|------------------|----------|--------------|
{% for source_type in affected_source_types %}
| {{ source_type.name|title }} | {{ source_type.format }} | {{ source_type.rule }} | {{ source_type.error }} |
{% endfor %}

---

## {{ validation_element|replace('_', ' ')|title }} Validation Checklist

Use this checklist to systematically validate {{ validation_element|replace('_', ' ') }}:

### Pre-Check Setup
- [ ] Reference list open and visible
- [ ] APA guide available
- [ ] Highlighter or tracking system ready

### Check Each Citation For:

{{ validation_checklist_items }}

### Post-Check Verification
- [ ] All citations checked
- [ ] Corrections made
- [ ] Consistency across similar citations
- [ ] Cross-checked problematic citations

### Final Check
- [ ] Run automated validation
- [ ] Review any flagged items
- [ ] Document completion date

**Citations Checked:** ___ / ___
**Errors Found:** ___
**Errors Fixed:** ___

---

## Tools & Tips for Checking {{ validation_element|replace('_', ' ')|title }}

### Word Processing Features

**Microsoft Word:**
- **Find feature:** {{ word_find_instructions }}
- **Find & Replace:** {{ word_find_replace_instructions }}
- **Styles panel:** {{ word_styles_instructions }}

**Google Docs:**
- **Find feature:** {{ docs_find_instructions }}
- **Add-ons:** {{ docs_addons_instructions }}

### Keyboard Shortcuts
- `Ctrl+F` (Windows) or `Cmd+F` (Mac): Find
- `Ctrl+H` (Windows) or `Cmd+Shift+H` (Mac): Find & Replace

### Search Strategies

**To find potential errors:**
{{ search_strategies }}

### Time-Saving Techniques

{% for technique in time_saving_techniques %}
💡 **{{ technique.name }}:** {{ technique.description }}
- When to use: {{ technique.when_to_use }}
- How to do it: {{ technique.how_to_do }}
- Time saved: {{ technique.time_saved }}

{% endfor %}

### Common Pitfalls to Avoid
{% for pitfall in common_pitfalls %}
- ⚠️ {{ pitfall }}
{% endfor %}

---

## Before & After Examples

These examples show common {{ validation_element|replace('_', ' ') }} errors and their corrections:

{% for example in before_after_examples %}
### Example {{ loop.index }}: {{ example.scenario }}

**Context:** {{ example.context }}

**Before (Incorrect):**
❌ {{ example.incorrect_citation }}

**Problem identified:**
```
{{ example.problem_highlighted }}
```

**After (Correct):**
✅ {{ example.correct_citation }}

**What changed:**
{% for change in example.changes %}
- {{ change }}
{% endfor %}

**Rule applied:** {{ example.rule_applied }}

---

{% endfor %}

### Example Summary

| Example | Error Type | Fix Applied | Difficulty |
|---------|------------|-------------|------------|
{% for example in before_after_examples %}
| {{ loop.index }} | {{ example.error_type }} | {{ example.fix_applied }} | {{ example.difficulty }} |
{% endfor %}

---

## Related Validation Guides

### Check Other Elements:
{% for related in related_validation_guides %}
- **{{ related.title }}** - {{ related.description }} → [{{ related.link }}]
{% endfor %}

### Complete Checking Guides:
- **Complete Citation Checking Guide** → [Link]
- **Reference List Validation** → [Link]

### Related Errors:
{% for error in related_errors %}
- **{{ error.name }}** → [{{ error.link }}]
{% endfor %}

### Source-Specific Guides:
{% for source in relevant_source_guides %}
- **Check {{ source.source_type }} Citations** → [{{ source.link }}]
{% endfor %}

---

<div class="cta-section">
<h3>🚀 Automate Your {{ validation_element|replace('_', ' ')|title }} Validation</h3>
<p>Save time and ensure accuracy with our automated citation checker. Instantly validate {{ validation_element|replace('_', ' ') }} and all other APA formatting elements.</p>
<a href="#" class="cta-button">Check {{ validation_element|replace('_', ' ')|title }} Automatically</a>
</div>

---

**Last Updated:** {{ last_updated }}
**Reading Time:** {{ reading_time }} minutes

---

## Frequently Asked Questions

{% for faq in faq_items %}
### {{ faq.question }}
{{ faq.answer }}

---
{% endfor %}