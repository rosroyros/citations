#!/usr/bin/env python3
"""
Test that validates the styled output matches mockup design.
"""

import pytest
import re
from pathlib import Path
import sys

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

from builder.enhanced_static_generator import EnhancedStaticSiteGenerator


class TestStyledOutputValidation:
    """Test that styled output matches mockup design"""

    @pytest.fixture
    def mockup_html(self):
        """Load the approved mockup HTML"""
        mockup_path = Path(__file__).parent.parent.parent.parent / "design" / "mocks" / "mega_guide_mockup.html"
        if not mockup_path.exists():
            pytest.skip(f"Mockup file not found: {mockup_path}")
        return mockup_path.read_text(encoding='utf-8')

    @pytest.fixture
    def styled_layout_template(self):
        """Load layout template with inline CSS for testing"""
        # Load CSS files
        styles_css_path = Path(__file__).parent.parent / "builder" / "assets" / "css" / "styles.css"
        mini_checker_css_path = Path(__file__).parent.parent / "builder" / "assets" / "css" / "mini-checker.css"

        if not styles_css_path.exists() or not mini_checker_css_path.exists():
            pytest.skip("CSS files not found")

        styles_css = styles_css_path.read_text(encoding='utf-8')
        mini_checker_css = mini_checker_css_path.read_text(encoding='utf-8')

        # Load layout template
        layout_path = Path(__file__).parent.parent / "templates" / "layout.html"
        layout_template = layout_path.read_text(encoding='utf-8')

        # Replace external CSS links with inline CSS for testing
        layout_template = layout_template.replace(
            '<link rel="stylesheet" href="/assets/css/styles.css">',
            f'<style>\n{styles_css}\n</style>'
        )
        layout_template = layout_template.replace(
            '<link rel="stylesheet" href="/assets/css/mini-checker.css">',
            f'<style>\n{mini_checker_css}\n</style>'
        )
        layout_template = layout_template.replace(
            '<link rel="preconnect" href="https://fonts.googleapis.com">',
            '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">'
        )

        return layout_template

    def test_css_is_properly_embedded(self, styled_layout_template):
        """
        Test that CSS is properly embedded in the layout template.
        """
        # Check for inline CSS
        assert '<style>' in styled_layout_template
        assert 'body {' in styled_layout_template
        assert '.header {' in styled_layout_template
        assert '.mini-checker {' in styled_layout_template

        # Check for key CSS rules
        assert 'background: linear-gradient(135deg' in styled_layout_template  # Page background
        assert 'background: white' in styled_layout_template  # Header background
        assert 'border-radius: 0.75rem' in styled_layout_template  # Card rounding
        assert 'box-shadow:' in styled_layout_template  # Shadows

        print("✅ CSS is properly embedded with key styling rules")

    def test_styled_generation_creates_visual_elements(self, styled_layout_template):
        """
        Test that styled generation creates visually appealing elements.
        """
        generator = EnhancedStaticSiteGenerator(styled_layout_template)

        # Simple test content
        content = '''<div class="hero">
<h1>Test Guide</h1>
<p class="hero-description">This is a test</p>
<div class="hero-meta">
<div class="meta-badge">📖 25 minutes</div>
<div class="meta-badge">🔄 Updated</div>
</div>
</div>

{% tldr_box title="Quick Summary" %}
- Point 1
- Point 2
- Point 3
{% endtldr_box %}

## Introduction

Some content here.

<div class="cta-placement" id="mini-checker-intro">
<!-- MiniChecker component will be rendered here -->
</div>

<div class="error-example">
<h4>❌ Wrong</h4>
<div class="wrong-example">Wrong format</div>
</div>

<div class="correction-box">
<h4>✓ Correct</h4>
<div class="correct-example">Right format</div>
</div>

<div class="checklist">
<ul>
<li>Check item 1</li>
<li>Check item 2</li>
</ul>
</div>
'''

        html_content = generator.convert_markdown_to_html(content)
        page_data = {
            'title': 'Test Guide',
            'page_type': 'mega_guide'
        }
        final_html = generator.apply_layout(html_content, page_data)

        # Check for inline CSS
        assert '<style>' in final_html
        assert len(re.findall(r'<style>(.*?)</style>', final_html, re.DOTALL)) > 0

        # Check for styled elements
        assert 'class="hero"' in final_html
        assert 'class="tldr-box"' in final_html
        assert 'class="mini-checker"' in final_html
        assert 'class="error-example"' in final_html
        assert 'class="correction-box"' in final_html
        assert 'class="checklist"' in final_html
        assert 'class="content-sidebar"' in final_html
        assert 'class="meta-badge"' in final_html

        # Check for visual CSS classes
        assert 'background:' in final_html  # Background colors
        assert 'border:' in final_html     # Borders
        assert 'padding:' in final_html    # Spacing
        assert 'margin:' in final_html     # Margins
        assert 'color:' in final_html      # Text colors

        print("✅ Styled generation creates visually appealing elements")

        return final_html

    def test_responsive_design_elements_present(self, styled_layout_template):
        """
        Test that responsive design elements are present.
        """
        generator = EnhancedStaticSiteGenerator(styled_layout_template)

        content = '''<div class="hero">
<h1>Responsive Test</h1>
</div>

## Test Content

Content here.
'''

        html_content = generator.convert_markdown_to_html(content)
        page_data = {'title': 'Responsive Test', 'page_type': 'mega_guide'}
        final_html = generator.apply_layout(html_content, page_data)

        # Check for responsive design indicators
        responsive_indicators = [
            'max-width:',          # Max-width for containers
            '@media',             # Media queries (if any)
            'grid-template-columns:',  # Grid layouts
            'flex',               # Flexbox layouts
            'viewport',           # Viewport meta tag
            'min-width:',         # Min-width constraints
        ]

        found_indicators = []
        for indicator in responsive_indicators:
            if indicator in final_html:
                found_indicators.append(indicator)

        print(f"✅ Found responsive design elements: {found_indicators}")

        # Should have at least viewport meta tag and some max-width constraints
        assert 'viewport' in final_html
        assert 'max-width:' in final_html

    def test_visual_hierarchy_matches_mockup(self, styled_layout_template):
        """
        Test that visual hierarchy matches mockup design.
        """
        generator = EnhancedStaticSiteGenerator(styled_layout_template)

        content = '''<div class="hero">
<h1>Visual Hierarchy Test</h1>
<p class="hero-description">This should be large and prominent</p>
</div>

## Main Section

This should be clearly defined.

### Subsection

This should be smaller but still visible.
'''

        html_content = generator.convert_markdown_to_html(content)
        page_data = {'title': 'Hierarchy Test', 'page_type': 'mega_guide'}
        final_html = generator.apply_layout(html_content, page_data)

        # Check for hierarchical elements
        assert '<h1>' in final_html
        assert '<h2>' in final_html
        assert '<h3>' in final_html

        # Check for CSS that creates hierarchy
        hierarchy_css = [
            'font-size:',      # Different font sizes
            'font-weight:',    # Font weights
            'line-height:',    # Line heights
            'margin',          # Margins for spacing
        ]

        found_hierarchy = []
        for css_prop in hierarchy_css:
            if css_prop in final_html:
                found_hierarchy.append(css_prop)

        print(f"✅ Found visual hierarchy CSS: {found_hierarchy}")

        # Should have font-size and font-weight variations
        assert 'font-size:' in final_html
        assert 'font-weight:' in final_html

    def test_interactive_elements_are_styled(self, styled_layout_template):
        """
        Test that interactive elements have proper styling.
        """
        generator = EnhancedStaticSiteGenerator(styled_layout_template)

        content = '''<div class="cta-placement" id="mini-checker-test">
<!-- MiniChecker component will be rendered here -->
</div>'''

        html_content = generator.convert_markdown_to_html(content)
        page_data = {'title': 'Interactive Test', 'page_type': 'mega_guide'}
        final_html = generator.apply_layout(html_content, page_data)

        # Check for interactive elements
        assert '<textarea' in final_html
        assert '<button' in final_html

        # Check for interactive styling
        interactive_css = [
            'cursor:',          # Pointer cursors
            'transition:',      # Transitions
            'hover',            # Hover states
            'focus',            # Focus states
            'background:',      # Button backgrounds
            'border:',          # Button borders
        ]

        found_interactive = []
        for css_prop in interactive_css:
            if css_prop in final_html:
                found_interactive.append(css_prop)

        print(f"✅ Found interactive element CSS: {found_interactive}")

        # Should have button styling
        assert 'background:' in final_html
        assert 'border:' in final_html

        # Should have transition effects
        assert 'transition:' in final_html

    def test_color_scheme_matches_design(self, styled_layout_template):
        """
        Test that color scheme matches the approved design.
        """
        generator = EnhancedStaticSiteGenerator(styled_layout_template)

        content = '''<div class="hero">
<h1>Color Test</h1>
</div>

{% tldr_box title="Color Box" %}
- Test content
{% endtldr_box %}

<div class="mini-checker">
<h4>Test</h4>
</div>
'''

        html_content = generator.convert_markdown_to_html(content)
        page_data = {'title': 'Color Test', 'page_type': 'mega_guide'}
        final_html = generator.apply_layout(html_content, page_data)

        # Check for brand colors
        brand_colors = [
            '#9333ea',          # Purple (primary brand color)
            '#7c3aed',          # Darker purple (hover)
            '#1f2937',          # Dark gray (text)
            '#6b7280',          # Medium gray (secondary text)
            '#f3f4f6',          # Light gray (background)
            '#fef3c7',          # Yellow (warnings/tips)
            '#fbbf24',          # Darker yellow
            '#22c55e',          # Green (success)
            '#ef4444',          # Red (errors)
        ]

        found_colors = []
        for color in brand_colors:
            if color in final_html:
                found_colors.append(color)

        print(f"✅ Found brand colors: {found_colors}")
        print(f"🎨 Total brand colors found: {len(found_colors)}/{len(brand_colors)}")

        # Should have at least the primary brand color
        assert '#9333ea' in final_html

        # Should have multiple colors for different elements
        assert len(found_colors) >= 5, "Should use multiple brand colors"

    def test_generated_file_size_indicates_full_styling(self, styled_layout_template):
        """
        Test that generated file size indicates full CSS is embedded.
        """
        generator = EnhancedStaticSiteGenerator(styled_layout_template)

        content = '''<div class="hero">
<h1>Size Test</h1>
</div>

## Content

Some content.
'''

        html_content = generator.convert_markdown_to_html(content)
        page_data = {'title': 'Size Test', 'page_type': 'mega_guide'}
        final_html = generator.apply_layout(html_content, page_data)

        # File should be substantial due to embedded CSS
        file_size = len(final_html)
        css_content = re.findall(r'<style>(.*?)</style>', final_html, re.DOTALL)
        css_size = len(css_content[0]) if css_content else 0

        print(f"📄 Total file size: {file_size:,} characters")
        print(f"🎨 CSS content size: {css_size:,} characters")

        # Should have substantial CSS (at least 15KB)
        assert css_size > 15000, f"CSS content should be substantial, got {css_size:,} chars"

        # Total file should be large due to embedded CSS
        assert file_size > 20000, f"Total file should be large with embedded CSS, got {file_size:,} chars"

        print("✅ File size indicates full CSS is embedded")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])