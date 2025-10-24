#!/usr/bin/env python3
"""
Test enhanced page generation and compare to mockup
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

from builder.enhanced_static_generator import EnhancedStaticSiteGenerator

def main():
    """Test enhanced generation with mockup-style content"""

    print("🔄 Testing Enhanced Page Generation")
    print("=" * 50)

    # Load enhanced layout template
    layout_path = Path(__file__).parent.parent / "templates" / "layout.html"
    if not layout_path.exists():
        print(f"❌ Layout template not found: {layout_path}")
        return False

    layout_template = layout_path.read_text(encoding='utf-8')
    print(f"✅ Loaded layout template ({len(layout_template)} chars)")

    # Initialize enhanced generator
    generator = EnhancedStaticSiteGenerator(layout_template, base_url="https://citationchecker.com")
    print("✅ Initialized EnhancedStaticSiteGenerator")

    # Sample mega guide content matching mockup structure
    sample_content = '''<div class="hero">
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
'''

    print(f"📝 Sample content prepared ({len(sample_content)} chars)")

    # Convert markdown to HTML using enhanced generator
    print("\n🔄 Converting markdown to enhanced HTML...")
    html_content = generator.convert_markdown_to_html(sample_content)
    print(f"✅ Converted to HTML ({len(html_content)} chars)")

    # Apply layout template
    page_data = {
        'title': 'Complete Guide to Checking APA Citations',
        'meta_title': 'Complete Guide to Checking APA Citations',
        'meta_description': 'Master the art of validating APA 7th edition citations with our comprehensive, step-by-step guide',
        'url': '/guide/complete-apa-citation-guide/',
        'page_type': 'mega_guide',
        'last_updated': 'December 2024',
        'reading_time': '25 minutes',
        'word_count': '2500'
    }

    print("\n🔄 Applying layout template...")
    final_html = generator.apply_layout(html_content, page_data)
    print(f"✅ Final HTML generated ({len(final_html)} chars)")

    # Save output file
    output_dir = Path(__file__).parent / "dist"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "enhanced-apa-guide.html"

    output_file.write_text(final_html, encoding='utf-8')
    print(f"✅ Saved to: {output_file}")
    print(f"🌐 Open in browser: file://{output_file.absolute()}")

    # Analyze generated content
    print("\n📊 Generated Content Analysis:")
    print("=" * 30)

    import re

    # Count semantic sections
    sections = len(re.findall(r'<section[^>]*class="content-section"', final_html))
    print(f"📄 Semantic sections: {sections}")

    # Count components
    tldr_boxes = len(re.findall(r'class="tldr-box"', final_html))
    mini_checkers = len(re.findall(r'class="mini-checker"', final_html))
    error_examples = len(re.findall(r'class="error-example"', final_html))
    correction_boxes = len(re.findall(r'class="correction-box"', final_html))
    checklists = len(re.findall(r'class="checklist"', final_html))
    faq_items = len(re.findall(r'class="faq-item"', final_html))

    print(f"📋 TL;DR boxes: {tldr_boxes}")
    print(f"🔍 MiniCheckers: {mini_checkers}")
    print(f"❌ Error examples: {error_examples}")
    print(f"✅ Correction boxes: {correction_boxes}")
    print(f"☑️  Checklists: {checklists}")
    print(f"❓ FAQ items: {faq_items}")

    # Check for key features
    has_sidebar = 'content-sidebar' in final_html
    has_toc = 'class="toc"' in final_html
    has_responsive = 'meta-badge' in final_html

    print(f"📱 Has responsive design: {has_responsive}")
    print(f"📑 Has table of contents: {has_toc}")
    print(f"📂 Has sidebar: {has_sidebar}")

    # Load mockup for comparison
    mockup_path = Path(__file__).parent.parent.parent.parent / "design" / "mocks" / "mega_guide_mockup.html"
    if mockup_path.exists():
        mockup_html = mockup_path.read_text(encoding='utf-8')

        mockup_sections = len(re.findall(r'<section[^>]*class="content-section"', mockup_html))
        mockup_mini_checkers = len(re.findall(r'class="mini-checker"', mockup_html))

        print(f"\n🎯 Mockup Comparison:")
        print(f"   Mockup sections: {mockup_sections}, Generated: {sections}")
        print(f"   Mockup MiniCheckers: {mockup_mini_checkers}, Generated: {mini_checkers}")

        # Check if we're getting closer to mockup
        improvement_score = 0
        if sections > 0:
            improvement_score += 1
        if mini_checkers >= 3:
            improvement_score += 1
        if has_sidebar:
            improvement_score += 1
        if tldr_boxes > 0:
            improvement_score += 1

        print(f"🚀 Improvement Score: {improvement_score}/4")

        if improvement_score >= 3:
            print("✅ Great progress! Generated page is much closer to mockup")
        else:
            print("⚠️  More work needed to match mockup structure")

    print(f"\n🎉 Enhanced generation test completed!")
    print(f"📁 Output file: {output_file}")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)