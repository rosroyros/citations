# {{ guide_title }}

{{ guide_description }}

---

## Table of Contents

1. [Quick Summary](#tldr---quick-summary)
2. [Introduction](#introduction)
{% for section in main_sections %}
3. [{{ section.title }}](#{{ section.slug }})
{% endfor %}
4. [Comprehensive Examples](#comprehensive-examples)
5. [Common Errors to Avoid](#common-errors-to-avoid)
6. [Validation Checklist](#validation-checklist)
7. [Frequently Asked Questions](#frequently-asked-questions)
8. [Related Resources](#related-resources)

---

## TL;DR - Quick Summary

<div class="tldr-box">
<h2>⚡ Key Points</h2>
<ul>
<li>Master APA 7th edition citation formatting</li>
<li>Identify and fix common citation errors</li>
<li>Use validation tools to ensure accuracy</li>
<li>Understand the rules that matter most</li>
<li>Save time and improve your grades</li>
</ul>
</div>

---

## Introduction

{{ introduction }}

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

## Comprehensive Examples

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

## Common Errors to Avoid

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
<p>Use this checklist to verify your citations before submission:</p>
<ul>
{% for item in validation_checklist %}
<li>{{ item.item }}</li>
{% endfor %}
</ul>
</div>

---


## Frequently Asked Questions

{% for faq in faq_questions %}
### {{ faq.question }}

{{ faq.answer }}

{% endfor %}

---

## Related Resources

{% for resource in related_resources %}
- [{{ resource.title }}]({{ resource.url }})
{% endfor %}

---

**Last Updated:** {{ last_updated }}
**Reading Time:** {{ reading_time }}

---

<div class="cta-placement">
    <h3>Need to Check Your Citations?</h3>
    <p>Use our free APA citation checker to validate your reference list instantly.</p>
    <a href="/checker/" class="cta-button">Check Citations Now</a>
</div>

---

<div class="author-info">
    <p>This guide was created to help students and researchers master APA 7th edition citation format. For more help with specific citation types, browse our complete collection of citation guides.</p>
</div>