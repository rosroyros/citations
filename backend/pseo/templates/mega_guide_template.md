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

**Key Points:**
- Master APA 7th edition citation formatting
- Identify and fix common citation errors
- Use validation tools to ensure accuracy
- Understand the rules that matter most
- Save time and improve your grades

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
### {{ example.metadata.title }}

**Reference List Format:**
```
{{ example.reference_citation }}
```

**In-Text Citations:**
{% for citation in example.in_text_citations %}
- **{{ citation.type|title }}**: {{ citation.citation }}
  - Example: {{ citation.context }}
{% endfor %}

**Source Type:** {{ example.source_type }}

---

{% endfor %}

---

## Common Errors to Avoid

{% for error in common_errors %}
### {{ error.error_name }}

**The Error:**
{{ error.wrong_example }}

**The Fix:**
{{ error.correct_example }}

**Why This Happens:** {{ error.why_it_happens }}

**How to Avoid It:** {{ error.fix_instructions }}

**Frequency:** {{ error.frequency }}% of students make this error

---

{% endfor %}

## Validation Checklist

Use this checklist to verify your citations before submission:

{% for item in validation_checklist %}
- [ ] {{ item.item }}
{% endfor %}

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