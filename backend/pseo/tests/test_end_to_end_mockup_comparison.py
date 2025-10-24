#!/usr/bin/env python3
"""
End-to-end tests comparing generated output to approved mockup.
This test validates the complete page generation pipeline.
"""

import pytest
import json
import re
from pathlib import Path
import sys
import os

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

from builder.enhanced_static_generator import EnhancedStaticSiteGenerator


class TestEndToEndMockupComparison:
    """End-to-end comparison with approved mockup"""

    @pytest.fixture
    def mockup_html(self):
        """Load the approved mockup HTML"""
        mockup_path = Path(__file__).parent.parent.parent.parent / "design" / "mocks" / "mega_guide_mockup.html"
        if not mockup_path.exists():
            pytest.skip(f"Mockup file not found: {mockup_path}")
        return mockup_path.read_text(encoding='utf-8')

    @pytest.fixture
    def enhanced_layout_template(self):
        """Load enhanced layout template"""
        layout_path = Path(__file__).parent.parent / "templates" / "layout.html"
        if not layout_path.exists():
            pytest.skip(f"Layout template not found: {layout_path}")
        return layout_path.read_text(encoding='utf-8')

    @pytest.fixture
    def sample_mega_guide_content(self):
        """Sample mega guide content matching mockup topic"""
        return '''<div class="hero">
<h1>Complete Guide to Checking APA Citations</h1>
<p class="hero-description">Master the art of validating APA 7th edition citations with our comprehensive, step-by-step guide. Learn how to catch errors before submission.</p>
<div class="hero-meta">
<div class="meta-badge">📖 Reading time: 25 minutes</div>
<div class="meta-badge">🔄 Last updated: December 2024</div>
<div class="meta-badge">✅ APA 7th Edition</div>
</div>
</div>

---

{% tldr_box title="TL;DR - Quick Summary" %}
- 90.9% of academic papers contain at least one citation error
- Author name formatting errors are the #1 most common mistake
- Always check: author names, dates, titles, DOIs, and punctuation
- Use automated tools first, then manually verify critical citations
- APA 7th edition has simplified several rules from 6th edition

**Key Takeaway:** Systematic citation checking prevents rejection and demonstrates academic rigor.
{% endtldr_box %}

---

## Introduction

You've spent weeks researching, writing, and revising your paper. The content is solid, your arguments are compelling, and you're ready to submit. But there's one critical step that many researchers overlook: thoroughly checking their citations.

Research shows that over 90% of academic papers contain citation errors. These mistakes range from minor formatting issues to serious problems like incorrect author names or missing publication years. While they might seem trivial, citation errors can undermine your credibility, delay publication, and in some cases, lead to rejection.

This comprehensive guide walks you through everything you need to know about checking APA citations. Whether you're a first-year student or an experienced researcher, you'll learn practical strategies to catch errors before they become problems.

---

<div class="cta-placement" id="mini-checker-intro">
<!-- MiniChecker component will be rendered here -->
</div>

---

## Why Checking Citations Matters

Citation accuracy isn't just about following rules—it's about academic integrity and professional credibility. Here's why it matters:

### Academic Integrity

Accurate citations give proper credit to original authors and allow readers to verify your sources. Errors can inadvertently misrepresent someone's work or make sources impossible to locate.

### Publication Requirements

Most journals and academic institutions have strict citation requirements. Papers with numerous formatting errors are often returned for revision before peer review even begins.

### Professional Reputation

Consistent citation errors signal carelessness. Taking the time to validate your references demonstrates attention to detail and professional rigor.

<div class="citation-example">
"Citation formatting is often the first thing reviewers notice. It sets the tone for how they'll evaluate the rest of your work." — Journal Editor Survey, 2023
</div>

---

## Most Common Citation Errors

Based on analysis of thousands of academic papers, these are the most frequent citation mistakes:

### 1. Author Name Formatting (45% of errors)

The most common mistake is incorrectly formatting author names, especially with multiple authors or organizational authors.

<div class="error-example">
<h4>❌ Incorrect:</h4>
<div class="wrong-example">
John Smith, Mary Jones, and Robert Lee (2020)...
</div>
</div>

<div class="correction-box">
<h4>✓ Correct Format:</h4>
<div class="correct-example">
Smith, J., Jones, M., & Lee, R. (2020)...
</div>
</div>

### 2. Title Capitalization (25% of errors)

Article titles should use sentence case (only first word capitalized), while journal names use title case.

<div class="error-example">
<h4>❌ Incorrect:</h4>
<div class="wrong-example">
The Effects Of Social Media On Student Learning
</div>
</div>

<div class="correction-box">
<h4>✓ Correct Format:</h4>
<div class="correct-example">
The effects of social media on student learning
</div>
</div>

---

<div class="cta-placement" id="mini-checker-test">
<!-- MiniChecker component will be rendered here -->
</div>

---

## Validation Checklist

Use this checklist to systematically review your citations:

<div class="checklist">
<p>Use this checklist to verify your citations before submission:</p>
<ul>
<li>All author names formatted as Last, F. M.</li>
<li>Ampersand (&) used before last author in reference list</li>
<li>Publication year in parentheses after authors</li>
<li>Article titles in sentence case</li>
<li>Journal names in title case and italicized</li>
<li>Volume numbers italicized</li>
<li>Issue numbers in parentheses (not italicized)</li>
<li>Page ranges formatted correctly (e.g., 123-145)</li>
<li>DOIs formatted as https://doi.org/...</li>
<li>No periods after DOIs or URLs</li>
<li>Reference list alphabetized by first author's last name</li>
<li>Hanging indent for all references</li>
<li>All in-text citations have corresponding references</li>
<li>All references cited in text</li>
</ul>
</div>

---

## Frequently Asked Questions

<div class="faq-item">
<div class="faq-question">How do I cite a source with no author?</div>
<div class="faq-answer">Start the citation with the title of the work. Move the publication date to after the title. Alphabetize by the first significant word of the title (ignore "A," "An," "The").</div>
</div>

<div class="faq-item">
<div class="faq-question">What if the publication date is unknown?</div>
<div class="faq-answer">Use (n.d.) which stands for "no date" in place of the year.</div>
</div>

<div class="faq-item">
<div class="faq-question">Should I include page numbers for online articles?</div>
<div class="faq-answer">Include page numbers if they are available in the PDF version. If the article only exists online without page numbers, you can omit them.</div>
</div>

---

<div class="cta-placement" id="mini-checker-final">
<!-- MiniChecker component will be rendered here -->
</div>

---

## Conclusion

Checking citations doesn't have to be overwhelming. With a systematic approach and the right tools, you can ensure your references are accurate and properly formatted. Remember:

- Start by using automated tools to catch obvious errors
- Follow up with manual verification of key citations
- Use the checklist to ensure nothing is missed
- When in doubt, consult the APA Manual or official APA Style resources

Taking the time to validate your citations demonstrates academic rigor and professionalism. Your future self—and your reviewers—will thank you.

---

**Last Updated:** December 2024
**Reading Time:** 25 minutes

---

<div class="author-info">
    <p>This guide was created to help students and researchers master APA 7th edition citation format. For more help with specific citation types, browse our complete collection of citation guides.</p>
</div>'''

    def test_enhanced_generator_creates_semantic_structure(self, enhanced_layout_template, sample_mega_guide_content):
        """
        Test that enhanced generator creates semantic HTML structure matching mockup.
        """
        generator = EnhancedStaticSiteGenerator(enhanced_layout_template)

        # Convert markdown to HTML
        html_content = generator.convert_markdown_to_html(sample_mega_guide_content)

        # Apply layout
        page_data = {
            'title': 'Complete Guide to Checking APA Citations',
            'meta_title': 'Complete Guide to Checking APA Citations',
            'meta_description': 'Master the art of validating APA 7th edition citations',
            'url': '/guide/complete-apa-citation-guide/',
            'page_type': 'mega_guide',
            'last_updated': 'December 2024',
            'reading_time': '25 minutes',
            'word_count': '2500'
        }

        final_html = generator.apply_layout(html_content, page_data)

        # Check semantic structure
        assert '<section class="content-section" id="introduction">' in final_html
        assert '<section class="content-section" id="why-checking-citations-matters">' in final_html
        assert '<section class="content-section" id="most-common-citation-errors">' in final_html

        # Check TL;DR box
        assert '<div class="tldr-box">' in final_html
        assert 'TL;DR - Quick Summary' in final_html

        # Check MiniChecker components
        mini_checker_count = len(re.findall(r'<div class="mini-checker">', final_html))
        assert mini_checker_count >= 3, f"Should have at least 3 MiniChecker components, got {mini_checker_count}"

        # Check sidebar content
        assert '<aside class="content-sidebar">' in final_html
        assert 'Related Guides' in final_html
        assert 'Quick Tools' in final_html
        assert 'Pro Tip' in final_html

        # Check error/correction boxes
        assert '<div class="error-example">' in final_html
        assert '<div class="correction-box">' in final_html

        # Check checklist
        assert '<div class="checklist">' in final_html

        # Check FAQ items
        assert '<div class="faq-item">' in final_html

        print(f"✅ Enhanced HTML generated successfully ({len(final_html)} chars)")
        print(f"✅ Found {mini_checker_count} MiniChecker components")
        print(f"✅ Semantic sections created")

        return final_html

    def test_generated_html_matches_mockup_structure(self, mockup_html, enhanced_layout_template, sample_mega_guide_content):
        """
        Test that generated HTML structure matches mockup structure.
        """
        generator = EnhancedStaticSiteGenerator(enhanced_layout_template)

        # Generate HTML
        html_content = generator.convert_markdown_to_html(sample_mega_guide_content)
        page_data = {
            'title': 'Complete Guide to Checking APA Citations',
            'meta_title': 'Complete Guide to Checking APA Citations',
            'meta_description': 'Master the art of validating APA 7th edition citations',
            'url': '/guide/complete-apa-citation-guide/',
            'page_type': 'mega_guide',
            'last_updated': 'December 2024',
            'reading_time': '25 minutes',
            'word_count': '2500'
        }
        generated_html = generator.apply_layout(html_content, page_data)

        print("\n=== Structure Comparison ===")

        # Compare semantic elements
        mockup_sections = len(re.findall(r'<section[^>]*class="content-section"', mockup_html))
        generated_sections = len(re.findall(r'<section[^>]*class="content-section"', generated_html))

        print(f"Mockup sections: {mockup_sections}")
        print(f"Generated sections: {generated_sections}")

        # Compare component types
        mockup_components = {
            'tldr-box': len(re.findall(r'class="tldr-box"', mockup_html)),
            'mini-checker': len(re.findall(r'class="mini-checker"', mockup_html)),
            'error-example': len(re.findall(r'class="error-example"', mockup_html)),
            'correction-box': len(re.findall(r'class="correction-box"', mockup_html)),
            'checklist': len(re.findall(r'class="checklist"', mockup_html)),
            'faq-item': len(re.findall(r'class="faq-item"', mockup_html))
        }

        generated_components = {
            'tldr-box': len(re.findall(r'class="tldr-box"', generated_html)),
            'mini-checker': len(re.findall(r'class="mini-checker"', generated_html)),
            'error-example': len(re.findall(r'class="error-example"', generated_html)),
            'correction-box': len(re.findall(r'class="correction-box"', generated_html)),
            'checklist': len(re.findall(r'class="checklist"', generated_html)),
            'faq-item': len(re.findall(r'class="faq-item"', generated_html))
        }

        print("Component comparison:")
        for component_type in mockup_components:
            mockup_count = mockup_components[component_type]
            generated_count = generated_components[component_type]
            print(f"  {component_type}: {mockup_count} -> {generated_count}")

        # Assert we have the right structure
        assert generated_sections > 0, "Should have semantic sections"
        assert generated_components['tldr-box'] > 0, "Should have TL;DR box"
        assert generated_components['mini-checker'] >= 3, "Should have multiple MiniChecker components"
        assert generated_components['error-example'] > 0, "Should have error examples"
        assert generated_components['correction-box'] > 0, "Should have correction boxes"

        # Check CSS classes from mockup exist in generated HTML
        mockup_classes = set(re.findall(r'class="([^"]+)"', mockup_html))
        generated_classes = set(re.findall(r'class="([^"]+)"', generated_html))

        # Critical classes that should exist
        critical_classes = {
            'tldr-box', 'mini-checker', 'content-section', 'hero',
            'toc', 'faq-item', 'error-example', 'correction-box',
            'checklist', 'content-sidebar', 'meta-badge'
        }

        missing_classes = critical_classes - generated_classes
        print(f"Missing critical CSS classes: {missing_classes}")

        assert len(missing_classes) == 0, f"Missing critical CSS classes: {missing_classes}"

        print("✅ Generated HTML structure matches mockup expectations")

    def test_css_classes_apply_correctly(self, enhanced_layout_template, sample_mega_guide_content):
        """
        Test that CSS classes can be applied correctly to generated HTML.
        """
        generator = EnhancedStaticSiteGenerator(enhanced_layout_template)

        # Generate HTML
        html_content = generator.convert_markdown_to_html(sample_mega_guide_content)
        page_data = {
            'title': 'Test Guide',
            'page_type': 'mega_guide'
        }
        generated_html = generator.apply_layout(html_content, page_data)

        # Check for specific CSS class patterns
        assert 'class="content-wrapper mega_guide"' in generated_html
        assert 'class="main-content"' in generated_html
        assert 'class="content-sidebar"' in generated_html

        # Check responsive classes
        assert 'meta-badge' in generated_html

        print("✅ CSS classes applied correctly")

    def test_minichecker_functionality_works(self, enhanced_layout_template):
        """
        Test that MiniChecker components have the right structure and functionality.
        """
        generator = EnhancedStaticSiteGenerator(enhanced_layout_template)

        # Test simple content with MiniChecker placeholder
        simple_content = '''
# Test Guide

Some content here.

<div class="cta-placement" id="mini-checker-intro">
<!-- MiniChecker component will be rendered here -->
</div>

More content.
        '''

        html_content = generator.convert_markdown_to_html(simple_content)
        page_data = {'page_type': 'source_type'}
        final_html = generator.apply_layout(html_content, page_data)

        # Check MiniChecker structure
        assert '<div class="mini-checker">' in final_html
        assert '<textarea' in final_html
        assert 'placeholder=' in final_html
        assert '<button' in final_html
        assert 'onclick="checkCitation' in final_html

        # Check form elements
        assert 'name="citation"' in final_html
        assert 'Check Citation' in final_html

        print("✅ MiniChecker functionality structure is correct")

    def test_sidebar_content_is_rich(self, enhanced_layout_template, sample_mega_guide_content):
        """
        Test that sidebar has rich content matching mockup.
        """
        generator = EnhancedStaticSiteGenerator(enhanced_layout_template)

        # Generate HTML
        html_content = generator.convert_markdown_to_html(sample_mega_guide_content)
        page_data = {
            'title': 'Test Guide',
            'page_type': 'mega_guide',
            'word_count': '2500',
            'reading_time': '25 minutes',
            'last_updated': 'December 2024'
        }
        final_html = generator.apply_layout(html_content, page_data)

        # Check sidebar sections
        assert 'Related Guides' in final_html
        assert 'Quick Tools' in final_html
        assert 'Pro Tip' in final_html
        assert 'Page Info' in final_html

        # Check sidebar links
        assert 'How to Cite Journal Articles' in final_html
        assert 'Citation Checker' in final_html

        # Check page info
        assert '2500' in final_html or '2,500' in final_html
        assert '25 minutes' in final_html
        assert 'December 2024' in final_html

        # Count sidebar sections
        sidebar_sections = len(re.findall(r'<div class="related-resources">', final_html))
        assert sidebar_sections >= 4, f"Should have at least 4 sidebar sections, got {sidebar_sections}"

        print(f"✅ Rich sidebar content with {sidebar_sections} sections")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])