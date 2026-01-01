# {{ title }}

{{ description }}

---

<div class="quick-ref-box">
<h2>📋 Quick Reference</h2>
<div class="template-box">
{{ quick_reference_template }}
</div>
<p style="margin-top: 1rem; font-size: 0.875rem; color: #6b7280;"><strong>Tip:</strong> Copy this template and replace with your source details.</p>
</div>

---

<div class="mini-checker" data-style="mla9">
<h4>🔍 Try It Out</h4>
<p>Paste a {{ source_type_name|lower }} citation to check your formatting</p>
<textarea placeholder="Author Last, First Name. Title of Work. Publisher, Year."></textarea>
<button onclick="checkCitation(this)">Check Citation</button>
</div>


---

{{ basic_format_explanation }}

---

{% if examples %}
## Reference List Examples

<p>Here are correctly formatted examples for common {{ source_type_name|lower }} variations:</p>

{% for example in examples %}
<div class="example-box">
{% if example.metadata %}
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
{% else %}
<div class="example-variation">{{ example.source_type|title }} Example</div>
<div class="citation-example">
{{ example.citation }}
</div>

{% if example.validation_notes %}
<strong>Key Points:</strong>
<ul>
{% for note in example.validation_notes %}
<li>{{ note }}</li>
{% endfor %}
</ul>
{% endif %}
{% endif %}
</div>

{% endfor %}

---

{% endif %}

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
<p>{{ error.explanation }}</p>
<strong>How to Avoid It:</strong>
<ul>
{% for instruction in error.fix_instructions %}
<li>{{ instruction }}</li>
{% endfor %}
</ul>
</div>

---

{% endfor %}

<div class="mini-checker">
<h4>✨ Ready to Check Your Full Reference List?</h4>
<p>Validate your entire bibliography at once with our citation checker</p>
<button style="background: #22c55e;">Check Full Reference List →</button>
</div>

---

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
