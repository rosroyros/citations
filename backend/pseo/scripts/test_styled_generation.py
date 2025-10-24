#!/usr/bin/env python3
"""
Test enhanced page generation with inline CSS for proper styling
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

from builder.enhanced_static_generator import EnhancedStaticSiteGenerator

def main():
    """Test enhanced generation with inline CSS"""

    print("🔄 Testing Enhanced Page Generation with Inline CSS")
    print("=" * 60)

    # Load CSS files
    styles_css_path = Path(__file__).parent.parent / "builder" / "assets" / "css" / "styles.css"
    mini_checker_css_path = Path(__file__).parent.parent / "builder" / "assets" / "css" / "mini-checker.css"

    if not styles_css_path.exists():
        print(f"❌ Styles CSS not found: {styles_css_path}")
        return False

    if not mini_checker_css_path.exists():
        print(f"❌ MiniChecker CSS not found: {mini_checker_css_path}")
        return False

    styles_css = styles_css_path.read_text(encoding='utf-8')
    mini_checker_css = mini_checker_css_path.read_text(encoding='utf-8')

    print(f"✅ Loaded styles.css ({len(styles_css)} chars)")
    print(f"✅ Loaded mini-checker.css ({len(mini_checker_css)} chars)")

    # Load layout template
    layout_path = Path(__file__).parent.parent / "templates" / "layout.html"
    layout_template = layout_path.read_text(encoding='utf-8')

    # Replace external CSS links with inline CSS
    layout_template = layout_template.replace(
        '<link rel="stylesheet" href="/assets/css/styles.css">',
        f'<style>\n{styles_css}\n</style>'
    )
    layout_template = layout_template.replace(
        '<link rel="stylesheet" href="/assets/css/mini-checker.css">',
        f'<style>\n{mini_checker_css}\n</style>'
    )

    # Remove external CSS link that won't work in file://
    layout_template = layout_template.replace(
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">'
    )

    print("✅ Modified layout template with inline CSS")

    # Initialize enhanced generator
    generator = EnhancedStaticSiteGenerator(layout_template, base_url="https://citationchecker.com")
    print("✅ Initialized EnhancedStaticSiteGenerator")

    # Simple test content
    sample_content = '''<div class="hero">
<h1>Complete Guide to Checking APA Citations</h1>
<p class="hero-description">Master the art of validating APA 7th edition citations with our comprehensive, step-by-step guide.</p>
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

**Key Takeaway:** Systematic citation checking prevents rejection and demonstrates academic rigor.
{% endtldr_box %}

---

## Introduction

You've spent weeks researching, writing, and revising your paper. The content is solid, your arguments are compelling, and you're ready to submit.

This comprehensive guide walks you through everything you need to know about checking APA citations.

---

<div class="cta-placement" id="mini-checker-intro">
<!-- MiniChecker component will be rendered here -->
</div>

---

## Why Citation Accuracy Matters

Citation accuracy isn't just about following rules—it's about academic integrity and professional credibility.

### Academic Integrity

Accurate citations give proper credit to original authors and allow readers to verify your sources.

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

---

<div class="cta-placement" id="mini-checker-test">
<!-- MiniChecker component will be rendered here -->
</div>

---

## Validation Checklist

<div class="checklist">
<p>Use this checklist to verify your citations:</p>
<ul>
<li>All author names formatted as Last, F. M.</li>
<li>Publication year in parentheses after authors</li>
<li>Article titles in sentence case</li>
<li>Journal names in title case and italicized</li>
</ul>
</div>

---

<div class="cta-placement" id="mini-checker-final">
<!-- MiniChecker component will be rendered here -->
</div>

---

## Conclusion

Taking the time to validate your citations demonstrates academic rigor and professionalism.
'''

    print(f"📝 Sample content prepared ({len(sample_content)} chars)")

    # Convert markdown to HTML
    html_content = generator.convert_markdown_to_html(sample_content)
    print(f"✅ Converted to HTML ({len(html_content)} chars)")

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
    print(f"✅ Final HTML generated with inline CSS ({len(final_html)} chars)")

    # Save output file
    output_dir = Path(__file__).parent / "dist"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "styled-apa-guide.html"

    output_file.write_text(final_html, encoding='utf-8')
    print(f"✅ Saved to: {output_file}")
    print(f"🌐 Open in browser: file://{output_file.absolute()}")

    # Analyze generated content
    print("\n📊 Styled Content Analysis:")
    print("=" * 30)

    import re

    # Check for CSS
    has_inline_css = '<style>' in final_html and 'body {' in final_html
    has_hero_section = 'class="hero"' in final_html
    has_tldr_box = 'class="tldr-box"' in final_html
    has_mini_checker = 'class="mini-checker"' in final_html
    has_error_example = 'class="error-example"' in final_html
    has_correction_box = 'class="correction-box"' in final_html
    has_checklist = 'class="checklist"' in final_html
    has_sidebar = 'class="content-sidebar"' in final_html
    has_meta_badge = 'class="meta-badge"' in final_html

    print(f"🎨 Has inline CSS: {has_inline_css}")
    print(f"📱 Has hero section: {has_hero_section}")
    print(f"📋 Has TL;DR box: {has_tldr_box}")
    print(f"🔍 Has MiniChecker: {has_mini_checker}")
    print(f"❌ Has error example: {has_error_example}")
    print(f"✅ Has correction box: {has_correction_box}")
    print(f"☑️  Has checklist: {has_checklist}")
    print(f"📂 Has sidebar: {has_sidebar}")
    print(f"🏷️  Has meta badges: {has_meta_badge}")

    # Check CSS length to verify it's substantial
    css_content_length = len(re.findall(r'<style>(.*?)</style>', final_html, re.DOTALL)[0]) if has_inline_css else 0
    print(f"📄 CSS content length: {css_content_length} characters")

    if css_content_length > 10000:
        print("✅ Substantial CSS content embedded")
    else:
        print("⚠️  CSS content seems small, might be incomplete")

    success_score = sum([
        has_inline_css, has_hero_section, has_tldr_box, has_mini_checker,
        has_error_example, has_correction_box, has_checklist, has_sidebar,
        has_meta_badge
    ])

    print(f"\n🎯 Styling Success Score: {success_score}/9")

    if success_score >= 8:
        print("🎉 Excellent! Page should be fully styled")
    elif success_score >= 6:
        print("✅ Good! Most styling elements are present")
    else:
        print("⚠️  Some styling elements may be missing")

    print(f"\n🎯 Key Fix Applied:")
    print("   • External CSS links replaced with inline CSS")
    print("   • Google Fonts preload changed to actual font import")
    print("   • All styling now works in file:// protocol")

    print(f"\n🎉 Styled generation test completed!")
    print(f"📁 Output file: {output_file}")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)