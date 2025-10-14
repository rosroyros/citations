# {{ title }}

{{ description }}

---

<div class="quick-ref-box">
<h2>📋 Quick Reference</h2>
<div class="template-box">
Author, A. A. (Year). <em>Title of work</em>. <em>Source Name</em>, <em>volume</em>(issue), pages. https://doi.org/xxxxx
</div>
<p style="margin-top: 1rem; font-size: 0.875rem; color: #6b7280;"><strong>Tip:</strong> Copy this template and replace with your source details.</p>
</div>

---

## Basic Format Explanation

{{ basic_format_explanation }}

---

## Reference List Examples

{% for example in examples %}
<div class="example-box">
<div class="example-variation">{{ example.metadata.title }}</div>
<div class="citation-example">
{{ example.reference_citation }}
</div>

<strong>In-Text Citations:</strong>
<ul>
{% for citation in example.in_text_citations %}
<li><strong>{{ citation.type|title }}:</strong> {{ citation.citation }}</li>
{% endfor %}
</ul>
</div>

{% endfor %}

## Step-by-Step Instructions

{{ step_by_step_instructions }}

---

## Common Errors for {{ source_type_name }} Citations

{% for error in common_errors %}
<div class="error-example">
<strong>❌ {{ error.error_name }}</strong>
<div style="font-family: 'Courier New', monospace; margin-top: 0.5rem;">
{{ error.wrong_example }}
</div>
</div>

<div class="correction-box">
<strong>✓ Correct Format:</strong>
<div style="font-family: 'Courier New', monospace; margin-top: 0.5rem;">
{{ error.correct_example }}
</div>
</div>

<div class="note-box">
<strong>Why This Happens:</strong>
<p>{{ error.why_it_happens }}</p>
<strong>How to Avoid It:</strong>
<p>{{ error.fix_instructions }}</p>
</div>

---

{% endfor %}

## Validation Checklist

<div class="checklist">
<p>Before submitting your {{ source_type_name }} citation, verify:</p>
<ul>
{% for item in validation_checklist %}
<li>{{ item.item }}</li>
{% endfor %}
</ul>
</div>

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
