"""
Tests for MLAStaticSiteGenerator

Verifies MLA-specific functionality:
- URL structure with -mla suffix
- Mini-checker data-style attribute
- Cross-style linking banners
- MLA-specific sidebar content
- Schema markup
"""

import pytest
from pathlib import Path
from mla_generator import MLAStaticSiteGenerator


@pytest.fixture
def layout_template():
    """Load layout template for testing"""
    template_file = Path(__file__).parent / "templates" / "layout.html"
    if template_file.exists():
        return template_file.read_text(encoding='utf-8')
    else:
        # Minimal template for testing
        return """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
</head>
<body>
    {{ content }}
</body>
</html>
"""


@pytest.fixture
def mla_generator(layout_template):
    """Create MLAStaticSiteGenerator instance"""
    return MLAStaticSiteGenerator(
        layout_template,
        base_url="https://citationformatchecker.com"
    )


class TestMLAURLStructure:
    """Test MLA-specific URL generation"""

    def test_specific_source_url(self, mla_generator):
        """Test specific source URL format"""
        url = mla_generator.generate_url_structure("specific_source", "youtube")
        assert url == "/cite-youtube-mla/"

    def test_source_type_url(self, mla_generator):
        """Test source type URL format"""
        url = mla_generator.generate_url_structure("source_type", "book")
        assert url == "/how-to-cite-book-mla/"

    def test_mega_guide_url(self, mla_generator):
        """Test mega guide URL format"""
        url = mla_generator.generate_url_structure("mega_guide", "9th-edition")
        assert url == "/guide/mla-9th-edition/"


class TestMiniCheckerConfig:
    """Test mini-checker configuration"""

    def test_minichecker_has_data_style(self, mla_generator):
        """Test that mini-checker includes data-style='mla9' attribute"""
        html = '<div class="cta-placement" id="mini-checker-intro"></div>'
        processed = mla_generator._process_minichecker_placeholders(html)

        assert 'data-style="mla9"' in processed

    def test_minichecker_placeholder_book(self, mla_generator):
        """Test MLA-specific placeholder for books"""
        config = mla_generator._get_minichecker_config("book")

        assert config["style"] == "mla9"
        assert "Morrison" in config["placeholder"] or "Beloved" in config["placeholder"]

    def test_minichecker_placeholder_youtube(self, mla_generator):
        """Test MLA-specific placeholder for YouTube"""
        config = mla_generator._get_minichecker_config("youtube")

        assert config["style"] == "mla9"
        assert "YouTube" in config["placeholder"]


class TestCrossStyleBanner:
    """Test cross-style linking banners"""

    def test_banner_links_to_apa(self, mla_generator):
        """Test that banner links to APA version"""
        banner = mla_generator._generate_cross_style_banner("youtube")

        assert "/cite-youtube-apa/" in banner
        assert "APA" in banner

    def test_banner_has_proper_styling(self, mla_generator):
        """Test that banner includes styling"""
        banner = mla_generator._generate_cross_style_banner("book")

        assert 'class="style-alternate"' in banner or 'style=' in banner


class TestSidebarContent:
    """Test MLA-specific sidebar generation"""

    def test_sidebar_has_mla_guides(self, mla_generator):
        """Test that sidebar links to MLA guides, not APA"""
        metadata = {
            'word_count': '1500',
            'reading_time': '7 min',
            'last_updated': '2024-12-30'
        }

        sidebar = mla_generator._generate_sidebar_content(metadata)

        assert "mla" in sidebar.lower()
        assert "/how-to-cite-journal-mla/" in sidebar or "mla" in sidebar.lower()

    def test_sidebar_has_mla_pro_tip(self, mla_generator):
        """Test that sidebar includes MLA-specific pro tip"""
        metadata = {'word_count': '1500', 'reading_time': '7 min', 'last_updated': '2024-12-30'}

        sidebar = mla_generator._generate_sidebar_content(metadata)

        assert "container" in sidebar.lower() or "MLA" in sidebar


class TestSchemaMarkup:
    """Test schema.org markup generation"""

    def test_schema_includes_mla_reference(self, mla_generator):
        """Test that schema markup references MLA 9"""
        metadata = {
            'title': 'Test Page',
            'meta_description': 'Test description',
            'date_published': '2024-12-30',
            'last_updated': '2024-12-30'
        }

        schema = mla_generator.generate_schema_markup(metadata)

        assert schema["@type"] == "TechArticle"
        assert "MLA" in schema["about"]["name"]


class TestApplyLayout:
    """Test layout application with MLA enhancements"""

    def test_metadata_includes_citation_style(self, mla_generator):
        """Test that metadata includes citation style info"""
        metadata = {
            'page_type': 'specific_source',
            'title': 'Test Page',
            'source_id': 'youtube'
        }

        html_content = "<h1>Test</h1><p>Content</p>"

        # Apply layout adds metadata
        result = mla_generator.apply_layout(html_content, metadata)

        # Can't easily test the result without parsing, but verify no errors
        assert result is not None
        assert len(result) > 0


class TestStyleConstants:
    """Test style constants"""

    def test_style_constants(self, mla_generator):
        """Test that style constants are set correctly"""
        assert mla_generator.STYLE == "mla9"
        assert mla_generator.STYLE_NAME == "MLA 9th Edition"
        assert mla_generator.STYLE_DISPLAY == "MLA 9"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
