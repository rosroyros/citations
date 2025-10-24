#!/usr/bin/env python3
"""
Test enhanced markdown converter with CSS preservation and semantic HTML.
These tests define the desired behavior we need to implement.
"""

import pytest
import re
from pathlib import Path
import sys

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))


class TestEnhancedMarkdownConverter:
    """Test the enhanced markdown converter we need to build"""

    def test_preserves_css_classes_in_html(self):
        """
        Test that custom HTML with CSS classes is preserved during markdown conversion.
        This test will drive implementation of enhanced markdown processing.
        """
        # This test will initially fail until we implement the enhanced converter
        from builder.enhanced_static_generator import EnhancedStaticSiteGenerator

        generator = EnhancedStaticSiteGenerator("<html>{{ content }}</html>")

        markdown_with_html = '''<div class="tldr-box">
<h2>Quick Summary</h2>
<p>This is important content</p>
</div>'''

        result = generator.convert_markdown_to_html(markdown_with_html)

        # Should preserve the CSS class
        assert 'class="tldr-box"' in result, "CSS classes should be preserved"
        assert '<h2>Quick Summary</h2>' in result, "HTML structure should be preserved"

    def test_converts_markdown_headers_to_semantic_sections(self):
        """
        Test that markdown ## headers become semantic <section> elements.
        This drives implementation of semantic HTML generation.
        """
        from builder.enhanced_static_generator import EnhancedStaticSiteGenerator

        generator = EnhancedStaticSiteGenerator("<html>{{ content }}</html>")

        markdown_headers = """## Introduction

This is the introduction content.

## Common Errors

These are the common errors."""

        result = generator.convert_markdown_to_html(markdown_headers)

        # Should create semantic sections
        assert '<section class="content-section" id="introduction">' in result
        assert '<section class="content-section" id="common-errors">' in result
        assert '<h2>Introduction</h2>' in result
        assert '<h2>Common Errors</h2>' in result

    def test_processes_custom_template_components(self):
        """
        Test that custom template syntax like {% tldr_box %} gets converted.
        This drives implementation of component processing.
        """
        from builder.enhanced_static_generator import EnhancedStaticSiteGenerator

        generator = EnhancedStaticSiteGenerator("<html>{{ content }}</html>")

        template_with_components = '''{% tldr_box title="TL;DR" %}
- Point 1
- Point 2
{% endtldr_box %}

## Main Content

Regular markdown content here.'''

        result = generator.convert_markdown_to_html(template_with_components)

        # Should convert template components to HTML
        assert '<div class="tldr-box">' in result
        assert '<h2>TL;DR</h2>' in result
        assert 'Point 1' in result
        assert 'Point 2' in result

    def test_minichecker_placeholder_conversion(self):
        """
        Test that MiniChecker placeholders become actual interactive components.
        This drives implementation of MiniChecker component rendering.
        """
        from builder.enhanced_static_generator import EnhancedStaticSiteGenerator

        generator = EnhancedStaticSiteGenerator("<html>{{ content }}</html>")

        markdown_with_placeholder = '''Some content here.

<div class="cta-placement" id="mini-checker-intro">
<!-- MiniChecker component will be mounted here -->
</div>

More content here.'''

        result = generator.convert_markdown_to_html(markdown_with_placeholder)

        # Should convert placeholder to actual MiniChecker
        assert '<div class="mini-checker">' in result
        assert '<textarea' in result
        assert 'placeholder=' in result
        assert '<button' in result
        assert 'Check Citation' in result

    def test_preserves_citation_example_formatting(self):
        """
        Test that citation examples maintain proper formatting.
        This drives implementation of citation component processing.
        """
        from builder.enhanced_static_generator import EnhancedStaticSiteGenerator

        generator = EnhancedStaticSiteGenerator("<html>{{ content }}</html>")

        citation_content = '''<div class="citation-example">
Smith, J. A., & Jones, M. B. (2020). <em>The effects of social media</em>. Journal Name, 15(2), 123-145. https://doi.org/10.1234/example
</div>'''

        result = generator.convert_markdown_to_html(citation_content)

        # Should preserve citation example structure
        assert 'class="citation-example"' in result
        assert '<em>' in result
        assert 'https://doi.org/' in result

    def test_error_correction_box_formatting(self):
        """
        Test that error/correction boxes maintain proper structure.
        This drives implementation of error component processing.
        """
        from builder.enhanced_static_generator import EnhancedStaticSiteGenerator

        generator = EnhancedStaticSiteGenerator("<html>{{ content }}</html>")

        error_content = '''<div class="error-example">
<strong>❌ Incorrect:</strong>
<p>Wrong format here</p>
</div>

<div class="correction-box">
<strong>✓ Correct:</strong>
<p>Right format here</p>
</div>'''

        result = generator.convert_markdown_to_html(error_content)

        # Should preserve error/correction structure
        assert 'class="error-example"' in result
        assert 'class="correction-box"' in result
        assert '❌ Incorrect:' in result
        assert '✓ Correct:' in result

    def test_table_of_contents_generation(self):
        """
        Test that automatic table of contents is generated from headers.
        This drives implementation of TOC generation.
        """
        from builder.enhanced_static_generator import EnhancedStaticSiteGenerator

        generator = EnhancedStaticSiteGenerator("<html>{{ content }}</html>")

        content_with_headers = '''## Introduction

Intro content.

## Common Errors

Error content.

## Validation Checklist

Checklist content.'''

        result = generator.convert_markdown_to_html(content_with_headers)

        # Should generate TOC
        assert '<div class="toc">' in result
        assert '<h2>📑 Table of Contents</h2>' in result
        assert '<a href="#introduction">Introduction</a>' in result
        assert '<a href="#common-errors">Common Errors</a>' in result
        assert '<a href="#validation-checklist">Validation Checklist</a>' in result

    def test_responsive_class_preservation(self):
        """
        Test that responsive design classes are preserved.
        This drives implementation of responsive class handling.
        """
        from builder.enhanced_static_generator import EnhancedStaticSiteGenerator

        generator = EnhancedStaticSiteGenerator("<html>{{ content }}</html>")

        responsive_content = '''<div class="content-wrapper mega_guide">
<div class="main-content">
<div class="hero">
Responsive content here
</div>
</div>
</div>'''

        result = generator.convert_markdown_to_html(responsive_content)

        # Should preserve responsive classes
        assert 'class="content-wrapper mega_guide"' in result
        assert 'class="main-content"' in result
        assert 'class="hero"' in result


class TestComponentRegistry:
    """Test the component registry system we need to implement"""

    def test_component_registration(self):
        """
        Test that components can be registered and retrieved.
        """
        from builder.components import ComponentRegistry

        registry = ComponentRegistry()

        # Should have default components
        assert 'tldr_box' in registry.components
        assert 'mini_checker' in registry.components
        assert 'citation_example' in registry.components

    def test_component_rendering(self):
        """
        Test that components render correctly with given parameters.
        """
        from builder.components import TLDRBoxComponent

        component = TLDRBoxComponent()
        result = component.render(
            title="TL;DR",
            content=["Point 1", "Point 2"]
        )

        assert '<div class="tldr-box">' in result
        assert '<h2>TL;DR</h2>' in result
        assert 'Point 1' in result
        assert 'Point 2' in result

    def test_minichecker_component_rendering(self):
        """
        Test that MiniChecker component renders with correct structure.
        """
        from builder.components import MiniCheckerComponent

        component = MiniCheckerComponent()
        result = component.render(
            placeholder="Enter citation here...",
            context_type="mega-guide"
        )

        assert 'class="mini-checker"' in result
        assert 'placeholder="Enter citation here..."' in result
        assert 'Check Citation' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])