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
<li><a href="#tldr">Quick Summary</a></li>
<li><a href="#introduction">Introduction</a></li>
{% for section in main_sections %}
<li><a href="#{{ section.slug }}">{{ section.title }}</a></li>
{% endfor %}
<li><a href="#examples">Comprehensive Examples</a></li>
<li><a href="#errors">Common Errors to Avoid</a></li>
<li><a href="#checklist">Validation Checklist</a></li>
<li><a href="#faq">Frequently Asked Questions</a></li>
<li><a href="#resources">Related Resources</a></li>
</ol>
</div>

<div class="tldr-box" id="tldr">
<h2>⚡ TL;DR - Quick Summary</h2>
<ul>
<li>Master APA 7th edition citation formatting</li>
<li>Identify and fix common citation errors</li>
<li>Use validation tools to ensure accuracy</li>
<li>Understand the rules that matter most</li>
<li>Save time and improve your grades</li>
</ul>
<p style="margin-top: 1rem;"><strong>Key Takeaway:</strong> Systematic citation checking prevents rejection and demonstrates academic rigor.</p>
</div>

<section class="content-section" id="introduction">
<h2>Introduction</h2>
{{ introduction }}
</section>

<div class="cta-placement" id="mini-checker-intro">
<!-- MiniChecker component will be rendered here -->
</div>

{% for section in main_sections %}
<section class="content-section" id="{{ section.slug }}">
<h2>{{ section.title }}</h2>
{{ section.content }}

{% if section.examples %}
**Examples:**
{% for example in section.examples %}
{{ example }}
{% endfor %}
{% endif %}
</section>

{% endfor %}

<section class="content-section" id="examples">
<h2>📚 Comprehensive Examples</h2>

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
</section>

<div class="cta-placement" id="mini-checker-test">
<!-- MiniChecker component will be rendered here -->
</div>

<section class="content-section" id="errors">
<h2>❌ Common Errors to Avoid</h2>

{% for error in common_errors %}
<h3>{{ error.error_name }}</h3>

<div class="error-example">
<strong>❌ Incorrect:</strong>
<p>{{ error.wrong_example }}</p>
</div>

<div class="correction-box">
<strong>✓ Correct:</strong>
<p>{{ error.correct_example }}</p>
</div>

<p>{{ error.why_it_happens }}</p>
<p><strong>How to Avoid:</strong> {{ error.fix_instructions }}</p>

{% endfor %}
</section>

<section class="content-section" id="checklist">
<h2>✅ Validation Checklist</h2>

<div class="checklist">
<p>Use this checklist to verify your citations before submission:</p>
<ul>
{% for item in validation_checklist %}
<li>{{ item.item }}</li>
{% endfor %}
</ul>
</div>
</section>

<section class="content-section" id="faq">
<h2>🙋 Frequently Asked Questions</h2>

{% for faq in faq_questions %}
<div class="faq-item">
<div class="faq-question">{{ faq.question }}</div>
<div class="faq-answer">{{ faq.answer }}</div>
</div>

{% endfor %}
</section>

<div class="cta-placement" id="mini-checker-final">
<!-- MiniChecker component will be rendered here -->
</div>

<section class="content-section" id="resources">
<h2>🔗 Related Resources</h2>

{% for resource in related_resources %}
- [{{ resource.title }}]({{ resource.url }})
{% endfor %}
</section>