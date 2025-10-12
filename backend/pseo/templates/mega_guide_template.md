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
7. [APA 6 vs 7 Changes](#apa-6-vs-7-changes)
8. [Frequently Asked Questions](#frequently-asked-questions)
9. [Related Resources](#related-resources)
10. [Conclusion](#conclusion)

---

## TL;DR - Quick Summary

{% for bullet in tldr_bullets %}
- {{ bullet }}
{% endfor %}

**Key Takeaway**: {{ primary_takeaway }}

---

## Introduction

{{ introduction }}

{{ importance_statement }}

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
### {{ example.title }}

**Reference List Format:**
{{ example.reference_citation }}

**In-Text Citation:**
{{ example.in_text_citation }}

{% if example.explanation %}
**Explanation:** {{ example.explanation }}
{% endif %}

{% if example.variation_note %}
**Note:** {{ example.variation_note }}
{% endif %}

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

{% for item in validation_checklist %}
- [ ] {{ item }}
{% endfor %}

**Quick Test:** {{ quick_validation_tip }}

---

## APA 6 vs 7 Changes

{% for change in apa6_vs_7 %}
### {{ change.element }}

**APA 6:** {{ change.apa6_format }}

**APA 7:** {{ change.apa7_format }}

**Why the Change:** {{ change.reason }}

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
- [{{ resource.title }}]({{ resource.url }}) - {{ resource.description }}
{% endfor %}

**Recommended Next Step:** {{ next_step_recommendation }}

---

## Conclusion

{{ conclusion_summary }}

{{ final_advice }}

{{ encouragement_message }}

---

## Quick Reference Guide

{{ quick_reference_content }}

---

**Last Updated:** {{ last_updated }}
**Reading Time:** {{ reading_time }}
**Word Count:** {{ word_count }} words

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