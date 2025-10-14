#!/usr/bin/env python3
"""
Tests for HTML Layout Template
Test that the template renders correctly with sample data
"""

import pytest
from pathlib import Path
import sys

# Add the backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "pseo"))

from builder.static_generator import StaticSiteGenerator


class TestLayoutTemplate:
    """Test suite for HTML Layout Template"""

    @pytest.fixture
    def layout_template(self):
        """Load the layout template"""
        template_path = Path(__file__).parent.parent / "pseo" / "builder" / "templates" / "layout.html"
        return template_path.read_text()

    @pytest.fixture
    def generator(self, layout_template):
        """Create StaticSiteGenerator instance with layout template"""
        return StaticSiteGenerator(layout_template)

    @pytest.fixture
    def sample_content(self):
        """Sample markdown content"""
        return """
# How to Cite a Journal Article in APA

This guide explains how to properly cite journal articles in APA 7th edition format.

## Basic Format

The basic format for a journal article is:

Author, A. A. (Year). Title of article. *Journal Name, volume*(issue), pages.

## Examples

Smith, J. (2020). Article title. *Journal Name, 15*(2), 123-145.

Johnson, M., & Williams, B. (2021). Another article. *Science Journal, 10*(3), 456-789.
        """.strip()

    @pytest.fixture
    def sample_metadata(self):
        """Sample metadata for a page"""
        return {
            "meta_title": "How to Cite a Journal Article in APA | Complete Guide",
            "meta_description": "Learn how to properly cite journal articles in APA 7th edition format with examples",
            "url": "/how-to-cite-journal-article-apa/",
            "breadcrumb_title": "How to Cite a Journal Article",
            "word_count": 2500,
            "reading_time": "10 minutes",
            "last_updated": "2025-10-13",
            "related_resources": [
                {"title": "APA 7th Edition Guide", "url": "/guide/apa-7th-edition/"},
                {"title": "How to Cite Books in APA", "url": "/how-to-cite-book-apa/"}
            ]
        }

    def test_template_exists(self, layout_template):
        """Test that the layout template file exists and has content"""
        assert layout_template is not None
        assert len(layout_template) > 0
        assert "<!DOCTYPE html>" in layout_template
        assert "{{ content | safe }}" in layout_template
        assert "{{ meta_title }}" in layout_template

    def test_generator_initialization(self, generator):
        """Test that StaticSiteGenerator initializes with the template"""
        assert generator is not None
        assert generator.layout is not None

    def test_markdown_conversion(self, generator, sample_content):
        """Test that markdown is converted to HTML correctly"""
        html = generator.convert_markdown_to_html(sample_content)

        assert "<h1" in html  # Allow for id attributes
        assert "How to Cite a Journal Article in APA" in html
        assert "<h2" in html  # Allow for id attributes
        assert "Basic Format" in html
        assert "<em>Journal Name" in html  # Italics for journal name (may include volume)
        assert "&amp;" in html  # HTML entity encoding

    def test_layout_application(self, generator, sample_content, sample_metadata):
        """Test that layout template is applied correctly"""
        # Convert markdown to HTML
        html_content = generator.convert_markdown_to_html(sample_content)

        # Apply layout
        final_html = generator.apply_layout(html_content, sample_metadata)

        # Check that layout elements are present
        assert "<!DOCTYPE html>" in final_html
        assert "<html lang=\"en\">" in final_html
        assert "<title>" in final_html
        assert sample_metadata["meta_title"] in final_html
        assert sample_metadata["meta_description"] in final_html
        assert "Citation Checker" in final_html  # Logo text

        # Check that content is included
        assert "How to Cite a Journal Article in APA" in final_html
        assert "<em>Journal Name" in final_html  # Allow for volume info

    def test_seo_elements(self, generator, sample_content, sample_metadata):
        """Test that SEO elements are correctly included"""
        html_content = generator.convert_markdown_to_html(sample_content)
        final_html = generator.apply_layout(html_content, sample_metadata)

        # Check meta tags
        assert f'<meta name="description" content="{sample_metadata["meta_description"]}">' in final_html
        assert f'<title>{sample_metadata["meta_title"]}</title>' in final_html

        # Check canonical URL
        assert f'<link rel="canonical" href="https://yoursite.com{sample_metadata["url"]}">' in final_html

        # Check schema.org markup
        assert '"@context": "https://schema.org"' in final_html
        assert '"@type": "HowTo"' in final_html

    def test_responsive_design(self, layout_template):
        """Test that responsive design elements are present"""
        # Template uses external CSS, so check for viewport meta tag and CSS link
        assert '<meta name="viewport" content="width=device-width, initial-scale=1.0">' in layout_template
        assert '<link rel="stylesheet" href="/assets/css/styles.css">' in layout_template

    def test_minichecker_placeholder(self, layout_template):
        """Test that MiniChecker placeholder is present"""
        assert "mini-checker-1" in layout_template
        assert "mountMiniChecker" in layout_template
        assert "Quick Check Your Citation" in layout_template

    def test_breadcrumb_generation(self, generator, sample_content, sample_metadata):
        """Test that breadcrumbs are correctly generated"""
        html_content = generator.convert_markdown_to_html(sample_content)
        final_html = generator.apply_layout(html_content, sample_metadata)

        assert "<nav class=\"breadcrumbs\">" in final_html
        assert "<a href=\"/\">Home</a>" in final_html
        assert "<a href=\"/guides/\">Citation Guides</a>" in final_html
        assert sample_metadata["breadcrumb_title"] in final_html

    def test_related_resources(self, generator, sample_content, sample_metadata):
        """Test that related resources are displayed correctly for both page types"""
        html_content = generator.convert_markdown_to_html(sample_content)

        # Test mega_guide: shows sidebar with "Related Guides"
        mega_metadata = {**sample_metadata, 'page_type': 'mega_guide'}
        final_html_mega = generator.apply_layout(html_content, mega_metadata)
        assert "Related Guides" in final_html_mega
        for resource in sample_metadata["related_resources"]:
            assert resource["title"] in final_html_mega
            assert resource["url"] in final_html_mega

        # Test source_type: shows related-grid with "Related Source Types"
        source_metadata = {**sample_metadata, 'page_type': 'source_type'}
        final_html_source = generator.apply_layout(html_content, source_metadata)
        assert "Related Source Types" in final_html_source
        # Check that related resources are shown as links
        for resource in sample_metadata["related_resources"]:
            assert resource["url"] in final_html_source

    def test_page_info_display(self, generator, sample_content, sample_metadata):
        """Test that page information is displayed in sidebar for mega_guide pages"""
        html_content = generator.convert_markdown_to_html(sample_content)

        # Page info only shown in sidebar for mega_guide pages
        mega_metadata = {**sample_metadata, 'page_type': 'mega_guide'}
        final_html = generator.apply_layout(html_content, mega_metadata)

        assert "Page Info" in final_html
        assert f"<strong>Word count:</strong> {sample_metadata['word_count']}" in final_html
        assert f"<strong>Reading time:</strong> {sample_metadata['reading_time']}" in final_html
        assert f"<strong>Last updated:</strong> {sample_metadata['last_updated']}" in final_html

        # Source type pages don't show page info in sidebar
        source_metadata = {**sample_metadata, 'page_type': 'source_type'}
        source_html = generator.apply_layout(html_content, source_metadata)
        assert "Page Info" not in source_html

    def test_styling_and_branding(self, layout_template):
        """Test that the template uses correct branding and styling"""
        # Template uses external CSS, so check for CSS link and brand name
        assert '<link rel="stylesheet" href="/assets/css/styles.css">' in layout_template
        assert "Citation Checker" in layout_template  # Brand name

        # Verify the external CSS file exists and contains purple styling
        css_path = Path(__file__).parent.parent.parent / "assets" / "css" / "styles.css"
        if css_path.exists():
            css_content = css_path.read_text()
            assert "#9333ea" in css_content  # Primary purple
            assert "background: linear-gradient" in css_content  # Gradient background

    def test_accessibility_features(self, layout_template):
        """Test for accessibility features"""
        assert '<html lang="en">' in layout_template  # Language attribute
        assert 'role="navigation"' in layout_template or 'nav' in layout_template  # Navigation landmarks
        assert 'role="main"' in layout_template or 'main' in layout_template  # Main content landmark

    def test_configurable_base_url(self, layout_template, sample_content, sample_metadata):
        """Test that base_url can be configured"""
        # Create generator with custom base URL
        custom_base_url = "https://example.com"
        generator = StaticSiteGenerator(layout_template, base_url=custom_base_url)

        html_content = generator.convert_markdown_to_html(sample_content)
        final_html = generator.apply_layout(html_content, sample_metadata)

        # Check that custom base URL is used in canonical link
        assert f'<link rel="canonical" href="{custom_base_url}{sample_metadata["url"]}">' in final_html

        # Verify sitemap uses custom base URL
        test_pages = [
            {'url': '/test-page/', 'lastmod': '2024-01-01', 'priority': '0.7'}
        ]
        sitemap = generator.generate_sitemap(test_pages)
        assert f'<loc>{custom_base_url}/test-page/</loc>' in sitemap


if __name__ == "__main__":
    pytest.main([__file__, "-v"])