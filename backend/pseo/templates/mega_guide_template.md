<div class="hero">
<h1>{{ guide_title }}</h1>
<p class="hero-description">{{ guide_description }}</p>
<div class="hero-meta">
<div class="meta-badge">📖 Reading time: {{ reading_time }}</div>
<div class="meta-badge">🔄 Last updated: {{ last_updated }}</div>
<div class="meta-badge">✅ {{ citation_style or 'APA 7th Edition' }}</div>
</div>
</div>

---

<div class="toc">
<h2>📑 Table of Contents</h2>
<ol>
<li><a href="#tldr---quick-summary">Quick Summary</a></li>
<li><a href="#introduction">Introduction</a></li>
{% for section in main_sections %}
<li><a href="#{{ section.slug }}">{{ section.title }}</a></li>
{% endfor %}
<li><a href="#comprehensive-examples">Comprehensive Examples</a></li>
<li><a href="#common-errors-to-avoid">Common Errors to Avoid</a></li>
<li><a href="#validation-checklist">Validation Checklist</a></li>
<li><a href="#frequently-asked-questions">Frequently Asked Questions</a></li>
<li><a href="#related-resources">Related Resources</a></li>
</ol>
</div>

---

## ⚡ TL;DR - Quick Summary

<div class="tldr-box">
<h3>⚡ Key Points</h3>
<ul>
<li>Master APA 7th edition citation formatting</li>
<li>Identify and fix common citation errors</li>
<li>Use validation tools to ensure accuracy</li>
<li>Understand the rules that matter most</li>
<li>Save time and improve your grades</li>
</ul>
<p style="margin-top: 1rem;"><strong>Key Takeaway:</strong> Systematic citation checking prevents rejection and demonstrates academic rigor.</p>
</div>

---

## Introduction

{{ introduction }}

---

<div class="cta-placement" id="mini-checker-intro">
<!-- MiniChecker component will be rendered here -->
</div>

---

{% for section in main_sections %}
## {{ section.title }}

{{ section.content }}

{% if section.examples %}
**Examples:**
{% for example in section.examples %}
{{ example }}
{% endfor %}
{% endif %}

{% endfor %}

---

## 📚 Comprehensive Examples

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

<p><strong>Source Type:</strong> {{ example.source_type }}</p>
</div>

{% endfor %}

---

<div class="cta-placement" id="mini-checker-test">
<!-- MiniChecker component will be rendered here -->
</div>

---

## ❌ Common Errors to Avoid

{% for error in common_errors %}
<div class="error-example">
<h4>❌ {{ error.error_name }}</h4>
<div class="wrong-example">
{{ error.wrong_example }}
</div>
</div>

<div class="correction-box">
<h4>✓ Correct Format:</h4>
<div class="correct-example">
{{ error.correct_example }}
</div>
</div>

<div class="explanation-box">
<h4>Why This Happens:</h4>
<p>{{ error.why_it_happens }}</p>
<h4>How to Avoid It:</h4>
<p>{{ error.fix_instructions }}</p>
</div>

---

{% endfor %}

## ✅ Validation Checklist

<div class="checklist">
<p>Use this checklist to verify your citations before submission:</p>
<ul>
{% for item in validation_checklist %}
<li>{{ item.item }}</li>
{% endfor %}
</ul>
</div>

---


## 🙋 Frequently Asked Questions

{% for faq in faq_questions %}
<div class="faq-item">
<div class="faq-question">{{ faq.question }}</div>
<div class="faq-answer">{{ faq.answer }}</div>
</div>

{% endfor %}

---

## 🔗 Related Resources

{% for resource in related_resources %}
- [{{ resource.title }}]({{ resource.url }})
{% endfor %}

---

## ✨ Conclusion

This guide provides you with comprehensive knowledge to master APA 7th edition citation format. By following the guidelines and examples provided, you'll be able to create accurate citations that demonstrate academic rigor and professionalism.

Remember to:
- Always double-check author names and publication dates
- Use sentence case for article titles and title case for journal names
- Include DOIs whenever available
- Validate your citations before submission

Taking the time to ensure citation accuracy shows attention to detail and respect for academic standards.

---

<div class="cta-placement" id="mini-checker-final">
<!-- MiniChecker component will be rendered here -->
</div>

---

**Last Updated:** {{ last_updated }}
**Reading Time:** {{ reading_time }}

---

<div class="author-info">
    <p>This guide was created to help students and researchers master APA 7th edition citation format. For more help with specific citation types, browse our complete collection of citation guides.</p>
</div>