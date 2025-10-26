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

<div class="mini-checker">
<h4>🔍 Try It Out</h4>
<p>Paste a {{ source_type_name|lower }} citation to check your formatting</p>
<textarea placeholder="Author, A. A. (Year). Title of work..."></textarea>
<button>Check Citation</button>
</div>

---

{{ basic_format_explanation }}

---

## Reference List Examples

<p>Here are correctly formatted examples for common {{ source_type_name|lower }} variations:</p>

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

<div class="step-box">
{{ step_by_step_instructions }}
</div>

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

<div class="related-box">
<h3>Related Source Types</h3>
<div class="related-grid">
<a href="/how-to-cite-book-apa/" class="related-link">📖 How to Cite Books</a>
<a href="/how-to-cite-website-apa/" class="related-link">🌐 How to Cite Websites</a>
<a href="/how-to-cite-conference-paper-apa/" class="related-link">📄 How to Cite Conference Papers</a>
<a href="/how-to-cite-book-chapter-apa/" class="related-link">📚 How to Cite Book Chapters</a>
<a href="/how-to-cite-dissertation-apa/" class="related-link">🎓 How to Cite Dissertations</a>
<a href="/how-to-cite-dataset-apa/" class="related-link">📊 How to Cite Datasets</a>
</div>
</div>

---

**Last Updated:** {{ last_updated }}
**Reading Time:** {{ reading_time }}
