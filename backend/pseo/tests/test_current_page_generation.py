#!/usr/bin/env python3
"""
Test current page generation reality - these tests should initially FAIL
to document the gap between current output and approved mockup.
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

from builder.static_generator import StaticSiteGenerator


class TestCurrentPageGeneration:
    """Test current reality - what our system actually produces vs mockup expectations"""

    @pytest.fixture
    def mockup_html(self):
        """Load the approved mockup HTML"""
        mockup_path = Path(__file__).parent.parent.parent.parent / "design" / "mocks" / "mega_guide_mockup.html"
        if not mockup_path.exists():
            pytest.skip(f"Mockup file not found: {mockup_path}")
        return mockup_path.read_text(encoding='utf-8')

    @pytest.fixture
    def current_generated_html(self):
        """Load current generated HTML for comparison"""
        # Try to find recently generated HTML
        generated_paths = [
            Path(__file__).parent.parent / "scripts" / "dist" / "apa-7th-edition-guide.html",
            Path(__file__).parent.parent.parent.parent / "content" / "dist" / "guide" / "apa-7th-edition" / "index.html",
            Path(__file__).parent.parent.parent.parent / "backend" / "pseo" / "scripts" / "dist" / "apa-7th-edition-guide.html"
        ]

        for path in generated_paths:
            if path.exists():
                return path.read_text(encoding='utf-8')

        pytest.skip("No generated HTML file found for testing")

    @pytest.fixture
    def layout_template(self):
        """Load current layout template"""
        layout_path = Path(__file__).parent.parent / "templates" / "layout.html"
        if not layout_path.exists():
            pytest.skip(f"Layout template not found: {layout_path}")
        return layout_path.read_text(encoding='utf-8')

    def test_current_html_structure_matches_mockup(self, mockup_html, current_generated_html):
        """
        Test that current generated HTML matches mockup structure.
        This test should FAIL initially, documenting the gap.
        """
        print("\n=== HTML Structure Comparison ===")

        # Count semantic elements
        mockup_sections = len(re.findall(r'<section[^>]*class="content-section"', mockup_html))
        generated_sections = len(re.findall(r'<section[^>]*class="content-section"', current_generated_html))

        print(f"Mockup content-section elements: {mockup_sections}")
        print(f"Generated content-section elements: {generated_sections}")

        # This should fail - our current output doesn't use semantic sections
        assert mockup_sections > 0, "Mockup should have semantic sections"
        assert generated_sections == mockup_sections, f"Expected {mockup_sections} sections, got {generated_sections}"

    def test_css_classes_preserved(self, mockup_html, current_generated_html):
        """
        Test that critical CSS classes from mockup exist in generated HTML.
        This test should FAIL initially.
        """
        print("\n=== CSS Class Comparison ===")

        # Extract CSS classes from mockup
        mockup_classes = set(re.findall(r'class="([^"]+)"', mockup_html))
        generated_classes = set(re.findall(r'class="([^"]+)"', current_generated_html))

        # Critical classes that should exist
        critical_classes = {
            'tldr-box', 'mini-checker', 'content-section', 'hero',
            'toc', 'faq-item', 'error-example', 'correction-box',
            'checklist', 'sidebar-section', 'meta-badge'
        }

        missing_classes = critical_classes - generated_classes
        print(f"Missing critical CSS classes: {missing_classes}")

        # This should fail - we're missing these classes
        assert len(missing_classes) == 0, f"Missing critical CSS classes: {missing_classes}"

    def test_minichecker_components_present(self, current_generated_html):
        """
        Test that MiniChecker components are properly rendered.
        This test should FAIL - we only have placeholder divs.
        """
        print("\n=== MiniChecker Component Check ===")

        # Look for actual MiniChecker HTML, not just placeholders
        has_textarea = 'textarea' in current_generated_html.lower()
        has_button = 'button' in current_generated_html.lower()
        has_placeholder = 'placeholder=' in current_generated_html.lower()

        # Count MiniChecker instances
        mini_checker_divs = len(re.findall(r'<div[^>]*class="[^"]*mini-checker[^"]*"', current_generated_html, re.IGNORECASE))
        placeholder_divs = len(re.findall(r'<div[^>]*id="mini-checker-', current_generated_html))

        print(f"Actual mini-checker divs: {mini_checker_divs}")
        print(f"Placeholder divs: {placeholder_divs}")
        print(f"Has textarea: {has_textarea}")
        print(f"Has button: {has_button}")
        print(f"Has placeholder: {has_placeholder}")

        # This should fail - we need actual MiniChecker components
        assert mini_checker_divs >= 3, "Should have at least 3 MiniChecker instances"
        assert has_textarea, "Should have textarea elements for citation input"
        assert has_button, "Should have buttons for checking citations"

    def test_sidebar_content_completeness(self, mockup_html, current_generated_html):
        """
        Test that sidebar contains all mockup elements.
        This test should FAIL - current sidebar is basic.
        """
        print("\n=== Sidebar Content Check ===")

        # Look for sidebar elements
        has_pro_tip = 'pro tip' in current_generated_html.lower()
        has_related_guides = 'related guides' in current_generated_html.lower()
        has_quick_tools = 'quick tools' in current_generated_html.lower()

        # Count sidebar sections
        sidebar_sections = len(re.findall(r'<div[^>]*class="[^"]*sidebar-section[^"]*"', current_generated_html, re.IGNORECASE))

        print(f"Has Pro Tip: {has_pro_tip}")
        print(f"Has Related Guides: {has_related_guides}")
        print(f"Has Quick Tools: {has_quick_tools}")
        print(f"Sidebar sections: {sidebar_sections}")

        # This should fail - sidebar needs rich content
        assert has_pro_tip, "Sidebar should have Pro Tip section"
        assert has_related_guides, "Sidebar should have Related Guides section"
        assert has_quick_tools, "Sidebar should have Quick Tools section"
        assert sidebar_sections >= 3, "Should have at least 3 sidebar sections"

    def test_markdown_conversion_preserves_structure(self, layout_template):
        """
        Test that markdown conversion preserves the structure we need.
        This test should FAIL - current conversion is too basic.
        """
        print("\n=== Markdown Conversion Test ===")

        # Initialize current generator
        generator = StaticSiteGenerator(layout_template)

        # Test markdown with custom HTML
        test_markdown = '''<div class="tldr-box">
<h2>TL;DR</h2>
<ul>
<li>Test point 1</li>
<li>Test point 2</li>
</ul>
</div>

## Introduction

This is the introduction content.'''

        result = generator.convert_markdown_to_html(test_markdown)

        # Check if CSS classes are preserved
        has_tldr_class = 'class="tldr-box"' in result
        has_proper_header = '<h2 id="introduction">Introduction</h2>' in result

        print(f"Preserves tldr-box class: {has_tldr_class}")
        print(f"Proper header format: {has_proper_header}")
        print(f"Converted HTML length: {len(result)}")
        print(f"Sample output: {result[:200]}...")

        # This might partially pass but will show limitations
        assert has_tldr_class, "Should preserve CSS classes in HTML"
        assert 'id="introduction"' in result, "Should create proper IDs for headers"


if __name__ == "__main__":
    # Run tests to document current failures
    pytest.main([__file__, "-v", "-s"])