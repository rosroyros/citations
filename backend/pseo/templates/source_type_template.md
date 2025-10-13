# How to Cite {{ source_type_name }} in APA 7th Edition

{{ source_description }}

---

## Quick Reference Template

{{ quick_reference_template }}

**Copy and paste this template, then replace the placeholder information with your source details.**

---

## Basic Format Explanation

{{ basic_format_explanation }}

**Key Elements to Remember:**
{% for element in key_elements %}
- {{ element }}
{% endfor %}

---

## Required vs Optional Elements

### Required Elements
{% for element in required_elements %}
- **{{ element.name }}**: {{ element.description }}
{% endfor %}

### Optional Elements
{% for element in optional_elements %}
- **{{ element.name }}**: {{ element.description }} (include when available)
{% endfor %}

**Missing Elements Rule:** {{ missing_elements_guidance }}

---

## Reference List Examples

{% for example in reference_examples %}
### {{ example.variation_title }}

{% if example.special_note %}
**Note:** {{ example.special_note }}
{% endif %}

**Reference List Format:**
{{ example.citation }}

{% if example.in_text_citation %}
**In-Text Citation:** {{ example.in_text_citation }}
{% endif %}

{% if example.breakdown %}
**Format Breakdown:**
{% for part in example.breakdown %}
- {{ part.element }}: {{ part.value }}
{% endfor %}
{% endif %}

{% if example.doi_note %}
**DOI Information:** {{ example.doi_note }}
{% endif %}

---

{% endfor %}

## In-Text Citation Guidelines

{{ in_text_guidelines }}

**Narrative Citations:**
{% for narrative in narrative_examples %}
- {{ narrative }}
{% endfor %}

**Parenthetical Citations:**
{% for parenthetical in parenthetical_examples %}
- {{ parenthetical }}
{% endfor %}

**Multiple Authors:** {{ multiple_authors_guidance }}

**No Author/Datetime:** {{ special_cases_guidance }}

---

## Step-by-Step Instructions

{{ step_by_step_instructions }}

**What You'll Need:**
{% for item in what_you_need %}
- {{ item }}
{% endfor %}

**Time Estimate:** {{ time_estimate }}

**Pro Tip:** {{ pro_tip }}

---

## Common Errors for {{ source_type_name }} Citations

{% for error in common_errors %}
### {{ error.error_name }}

**The Error:**
{{ error.wrong_example }}

**The Fix:**
{{ error.correct_example }}

**Why Students Make This Error:** {{ error.why_it_happens }}

**Quick Fix:** {{ error.fix_instructions }}

**Frequency:** {{ error.frequency }}% of {{ source_type_name|lower }} citations have this error

---

{% endfor %}

## Validation Checklist

### Before Submitting Your Citation:
{% for item in validation_checklist %}
- [ ] {{ item }}
{% endfor %}

**Quick Self-Test:** {{ quick_validation_tip }}

**Common Red Flags:**
{% for flag in red_flags %}
- {{ flag }}
{% endfor %}

**Final Check:** Read your citation aloud to catch awkward phrasing or missing elements.

---

{% if special_cases %}
## Special Cases for {{ source_type_name }}

{% for case in special_cases %}
### {{ case.title }}

**When This Applies:** {{ case.when_applies }}

**How to Format:** {{ case.formatting }}

**Example:** {{ case.example }}

{% if case.additional_note %}
**Additional Note:** {{ case.additional_note }}
{% endif %}

---

{% endfor %}
{% endif %}

## Related Source Types

Looking for help with other source types? Browse our comprehensive guides:

{% for related in related_sources %}
- [How to Cite {{ related.name }} in APA]({{ related.url }}) - {{ related.description }}
{% endfor %}

**Next Steps:** {{ next_steps_recommendation }}

---

## Frequently Asked Questions

{% for faq in faq %}
### {{ faq.question }}

{{ faq.answer }}

{% if faq.example %}
**Example:** {{ faq.example }}
{% endif %}

---

{% endfor %}

## Expert Tips for {{ source_type_name }} Citations

{% for tip in expert_tips %}
### {{ tip.title }}

{{ tip.content }}

{% endfor %}

**Best Practice:** {{ best_practice_summary }}

---

## Bottom Line

{{ bottom_line_summary }}

**Remember the 3 Most Important Rules:**
{% for rule in three_important_rules %}
{{ loop.index }}. {{ rule }}
{% endfor %}

---

<div class="practice-section">
    <h3>Practice Your {{ source_type_name }} Citation Skills</h3>
    <p>Use our free citation checker to validate your {{ source_type_name|lower }} citations instantly. Get immediate feedback on formatting, punctuation, and APA 7th edition compliance.</p>
    <div class="cta-button-container">
        <a href="/checker/" class="cta-button primary">Check {{ source_type_name }} Citations</a>
        <a href="/guide/{{ practice_guide_slug }}/" class="cta-button secondary">Practice with Examples</a>
    </div>
</div>

---

**Last Updated:** {{ last_updated }}
**Reading Time:** {{ reading_time }}
**Word Count:** {{ word_count }} words
**APA Edition:** 7th Edition

---

<div class="citation-help-reminder">
    <h4>Still Confused About {{ source_type_name }} Citations?</h4>
    <p>APA citation formatting doesn't have to be stressful. Our comprehensive tools and guides cover every source type you'll encounter in academic writing.</p>
    <ul>
        <li><a href="/guide/complete-apa-citation-guide/">Complete APA 7th Edition Guide</a></li>
        <li><a href="/guide/common-apa-citation-errors/">Common Citation Errors to Avoid</a></li>
        <li><a href="/checker/">Free Citation Validation Tool</a></li>
    </ul>
</div>

<div class="mini-checker-placement">
    <!-- MiniChecker component will be embedded here -->
    <p><strong>Quick Check:</strong> Paste your {{ source_type_name|lower }} citation below to instantly verify APA 7th edition formatting.</p>
</div>