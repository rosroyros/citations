"""Tests for StaticSiteGenerator"""
import pytest
from pathlib import Path
import tempfile
import shutil
from backend.pseo.builder.static_generator import StaticSiteGenerator


@pytest.fixture
def temp_dirs():
    """Create temporary input/output directories"""
    temp_input = tempfile.mkdtemp()
    temp_output = tempfile.mkdtemp()
    yield temp_input, temp_output
    shutil.rmtree(temp_input)
    shutil.rmtree(temp_output)


@pytest.fixture
def layout_template():
    """Simple layout template for testing"""
    return """<!DOCTYPE html>
<html>
<head><title>{{ title }}</title></head>
<body>{{ content | safe }}</body>
</html>"""


def test_markdown_conversion():
    """Test basic markdown to HTML conversion"""
    generator = StaticSiteGenerator("<html>{{ content | safe }}</html>")

    md_content = """# Heading

This is **bold** text and *italic* text.

## Subheading

- List item 1
- List item 2
"""

    html = generator.convert_markdown_to_html(md_content)

    assert "<h1" in html and ">Heading</h1>" in html
    assert "<h2" in html and ">Subheading</h2>" in html
    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html
    assert "<li>List item 1</li>" in html


def test_markdown_with_tables():
    """Test markdown table conversion"""
    generator = StaticSiteGenerator("<html>{{ content | safe }}</html>")

    md_content = """| Column 1 | Column 2 |
|----------|----------|
| Data 1   | Data 2   |
"""

    html = generator.convert_markdown_to_html(md_content)

    assert "<table>" in html
    assert "<th>Column 1</th>" in html
    assert "<td>Data 1</td>" in html


def test_markdown_with_code_blocks():
    """Test markdown code block conversion"""
    generator = StaticSiteGenerator("<html>{{ content | safe }}</html>")

    md_content = """```python
def example():
    return True
```"""

    html = generator.convert_markdown_to_html(md_content)

    assert "<code" in html
    assert "def example():" in html


def test_layout_application(layout_template):
    """Test applying layout template to content"""
    generator = StaticSiteGenerator(layout_template)

    html_content = "<h1>Test</h1><p>Content</p>"
    metadata = {"title": "Test Page"}

    result = generator.apply_layout(html_content, metadata)

    assert "<title>Test Page</title>" in result
    assert "<h1>Test</h1>" in result
    assert "<p>Content</p>" in result


def test_url_generation_mega_guide():
    """Test URL generation for mega guide pages"""
    generator = StaticSiteGenerator("<html></html>")

    url = generator.generate_url_structure("mega_guide", "apa-citations")

    assert url == "/guide/apa-citations/"


def test_url_generation_source_type():
    """Test URL generation for source type pages"""
    generator = StaticSiteGenerator("<html></html>")

    url = generator.generate_url_structure("source_type", "journal-article")

    assert url == "/how-to-cite-journal-article-apa/"


def test_url_generation_other():
    """Test URL generation for other page types"""
    generator = StaticSiteGenerator("<html></html>")

    url = generator.generate_url_structure("other", "about")

    assert url == "/about/"


def test_sitemap_generation():
    """Test XML sitemap generation"""
    generator = StaticSiteGenerator("<html></html>")

    pages = [
        {
            'url': '/guide/apa-citations/',
            'lastmod': '2024-10-13',
            'priority': '0.7'
        },
        {
            'url': '/how-to-cite-journal-article-apa/',
            'lastmod': '2024-10-13',
            'priority': '0.6'
        }
    ]

    sitemap = generator.generate_sitemap(pages)

    assert '<?xml version="1.0" encoding="UTF-8"?>' in sitemap
    assert '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' in sitemap
    assert '<loc>https://yoursite.com/guide/apa-citations/</loc>' in sitemap
    assert '<lastmod>2024-10-13</lastmod>' in sitemap
    assert '<priority>0.7</priority>' in sitemap
    assert '</urlset>' in sitemap


def test_extract_front_matter():
    """Test front matter extraction from markdown"""
    generator = StaticSiteGenerator("<html></html>")

    md_content = """---
title: Test Page
page_type: mega_guide
url_slug: test-page
last_updated: 2024-10-13
---

# Content Here

Body content."""

    front_matter, content = generator._extract_front_matter(md_content)

    assert front_matter['title'] == 'Test Page'
    assert front_matter['page_type'] == 'mega_guide'
    assert front_matter['url_slug'] == 'test-page'
    assert '# Content Here' in content
    assert 'Body content.' in content
    assert '---' not in content


def test_build_site(temp_dirs, layout_template):
    """Test full site build process"""
    input_dir, output_dir = temp_dirs

    # Create test markdown file
    test_md = Path(input_dir) / "test-page.md"
    test_md.write_text("""---
title: Test Page
page_type: mega_guide
url_slug: test-page
last_updated: 2024-10-13
---

# Test Heading

Test content here.""")

    generator = StaticSiteGenerator(layout_template)
    generator.build_site(input_dir, output_dir)

    # Check output file exists
    output_file = Path(output_dir) / "guide" / "test-page" / "index.html"
    assert output_file.exists()

    # Check content
    html_content = output_file.read_text()
    assert "<title>Test Page</title>" in html_content
    assert "<h1" in html_content and ">Test Heading</h1>" in html_content

    # Check sitemap exists
    sitemap_file = Path(output_dir) / "sitemap.xml"
    assert sitemap_file.exists()

    sitemap_content = sitemap_file.read_text()
    assert "/guide/test-page/" in sitemap_content


def test_build_site_multiple_pages(temp_dirs, layout_template):
    """Test building site with multiple pages"""
    input_dir, output_dir = temp_dirs

    # Create multiple test files
    pages = [
        {
            'filename': 'mega-guide.md',
            'content': """---
title: Mega Guide
page_type: mega_guide
url_slug: mega-guide
last_updated: 2024-10-13
---

# Mega Guide"""
        },
        {
            'filename': 'journal-article.md',
            'content': """---
title: Journal Article
page_type: source_type
url_slug: journal-article
last_updated: 2024-10-13
---

# Journal Article"""
        }
    ]

    for page in pages:
        (Path(input_dir) / page['filename']).write_text(page['content'])

    generator = StaticSiteGenerator(layout_template)
    generator.build_site(input_dir, output_dir)

    # Check both files exist
    assert (Path(output_dir) / "guide" / "mega-guide" / "index.html").exists()
    assert (Path(output_dir) / "how-to-cite-journal-article-apa" / "index.html").exists()

    # Check sitemap has both pages
    sitemap = (Path(output_dir) / "sitemap.xml").read_text()
    assert "/guide/mega-guide/" in sitemap
    assert "/how-to-cite-journal-article-apa/" in sitemap


def test_markdown_no_front_matter():
    """Test handling markdown without front matter"""
    generator = StaticSiteGenerator("<html></html>")

    md_content = """# Just Content

No front matter here."""

    front_matter, content = generator._extract_front_matter(md_content)

    assert front_matter == {}
    assert '# Just Content' in content
