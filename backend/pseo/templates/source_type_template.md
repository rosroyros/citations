# {{ title }}

{{ description }}

---

## Quick Reference

Use this basic format for {{ source_type_name }} citations:

```
Author, A. A. (Year). Title of work. Source Name.
```

---

## Basic Format Explanation

{{ basic_format_explanation }}

---

## Reference List Examples

{% for example in examples %}
### {{ example.metadata.title }}

**Reference List Format:**
```
{{ example.reference_citation }}
```

**In-Text Citations:**
{% for citation in example.in_text_citations %}
- **{{ citation.type|title }}**: {{ citation.citation }}
{% endfor %}

---

{% endfor %}

## Step-by-Step Instructions

{{ step_by_step_instructions }}

---

## Common Errors for {{ source_type_name }} Citations

{% for error in common_errors %}
### {{ error.error_name }}

**The Error:**
```
{{ error.wrong_example }}
```

**The Fix:**
```
{{ error.correct_example }}
```

**Why This Happens:** {{ error.why_it_happens }}

**How to Avoid It:** {{ error.fix_instructions }}

---

{% endfor %}

## Validation Checklist

Before submitting your {{ source_type_name }} citation, verify:

{% for item in validation_checklist %}
- [ ] {{ item.item }}
{% endfor %}

---

## Special Cases

{{ special_cases }}

---

## Frequently Asked Questions

{% for faq_item in faq %}
### {{ faq_item.question }}

{{ faq_item.answer }}

---

{% endfor %}

---

**Last Updated:** {{ last_updated }}
**Reading Time:** {{ reading_time }}

---

<div class="cta-placement">
    <h3>Need to Check Your Citations?</h3>
    <p>Use our free APA citation checker to validate your {{ source_type_name|lower }} citations instantly.</p>
    <a href="/checker/" class="cta-button">Check Citations Now</a>
</div>
