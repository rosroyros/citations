#!/usr/bin/env python3
"""
Generate demo HTML pages to visualize the two layout types
"""
from pathlib import Path
from backend.pseo.builder.static_generator import StaticSiteGenerator

print("🎨 Generating demo pages...\n")

# Load layout template
layout_path = Path("backend/pseo/builder/templates/layout.html")
layout_template = layout_path.read_text()

# Initialize generator
generator = StaticSiteGenerator(layout_template, base_url="https://example.com")

# Sample markdown content
sample_content = """
# How to Cite a Journal Article in APA

Welcome to this comprehensive guide on citing journal articles in APA 7th edition format.

## Quick Reference

The basic format for a journal article citation is:

Author, A. A. (Year). Title of article. *Journal Name, volume*(issue), pages. https://doi.org/xxxxx

## Why APA Citation Matters

Proper citation is essential for:
- **Academic integrity** - Give credit to original authors
- **Credibility** - Show your research is well-founded
- **Reproducibility** - Allow others to find your sources

## Example Citations

### Standard Journal Article

Smith, J., & Jones, M. (2020). The effects of social media on academic performance. *Journal of Educational Psychology, 112*(4), 789-805. https://doi.org/10.1037/edu0000123

### Article with 3+ Authors

Anderson, C. A., Shibuya, A., Ihori, N., Swing, E. L., & Bushman, B. J. (2010). Violent video game effects on aggression. *Psychological Bulletin, 136*(2), 151-173.

## Common Errors to Avoid

| Error | Incorrect | Correct |
|-------|-----------|---------|
| Italics | *Journal Name*, *15*(2) | *Journal Name, 15*(2) |
| Ampersand | Smith, J. and Jones, M. | Smith, J., & Jones, M. |
| Capitalization | The Effects Of Social Media | The effects of social media |

## Step-by-Step Instructions

1. **Identify authors** - List all authors with last name first
2. **Add publication year** - Place in parentheses after authors
3. **Write article title** - Use sentence case
4. **Format journal name** - Use title case and italicize
5. **Add volume/issue** - Italicize volume, put issue in parentheses
6. **Include page numbers** - Use format: 123-145
7. **Add DOI** - Format as: https://doi.org/xxxxx

## Validation Checklist

Use this checklist before submitting:

- [ ] All authors listed correctly
- [ ] Ampersand (&) before last author
- [ ] Publication year in parentheses
- [ ] Article title in sentence case
- [ ] Journal name italicized
- [ ] Volume number italicized
- [ ] Issue number in parentheses (not italicized)
- [ ] DOI formatted correctly
- [ ] No period after DOI

## Need Help?

If you're unsure about your citation, use our citation checker tool to validate your formatting instantly.

---

*This guide follows APA 7th edition guidelines and is regularly updated to reflect the latest standards.*
"""

# Generate Source Type demo (single-column)
print("1️⃣  Generating Source Type demo (single-column layout)...")
source_metadata = {
    "page_type": "source_type",
    "meta_title": "How to Cite a Journal Article in APA | Demo",
    "meta_description": "Complete guide to citing journal articles in APA 7th edition format",
    "url": "/how-to-cite-journal-article-apa/",
    "breadcrumb_title": "How to Cite a Journal Article",
    "word_count": 856,
    "reading_time": "4 minutes",
    "last_updated": "2025-10-13",
    "related_resources": [
        {"title": "📖 How to Cite Books in APA", "url": "/how-to-cite-book-apa/"},
        {"title": "🌐 How to Cite Websites in APA", "url": "/how-to-cite-website-apa/"},
        {"title": "📰 How to Cite Newspapers", "url": "/how-to-cite-newspaper-apa/"},
        {"title": "📚 How to Cite Book Chapters", "url": "/how-to-cite-chapter-apa/"}
    ]
}

html_content = generator.convert_markdown_to_html(sample_content)
source_html = generator.apply_layout(html_content, source_metadata)

demo_dir = Path("demo_output")
demo_dir.mkdir(exist_ok=True)

source_file = demo_dir / "demo_source_type.html"
source_file.write_text(source_html)
print(f"   ✅ Saved: {source_file}")

# Generate Mega Guide demo (two-column with sidebar)
print("\n2️⃣  Generating Mega Guide demo (two-column with sidebar)...")
mega_metadata = {
    "page_type": "mega_guide",
    "meta_title": "Complete Guide to Checking APA Citations | Demo",
    "meta_description": "Master the art of verifying APA citation accuracy with our comprehensive guide",
    "url": "/guide/check-apa-citations/",
    "breadcrumb_title": "Check APA Citations",
    "word_count": 856,
    "reading_time": "4 minutes",
    "last_updated": "2025-10-13",
    "related_resources": [
        {"title": "APA 7th Edition Guide", "url": "/guide/apa-7th-edition/"},
        {"title": "Citation Errors Guide", "url": "/guide/citation-errors/"},
        {"title": "Validation Checklist", "url": "/guide/validation-checklist/"},
        {"title": "Common Mistakes", "url": "/guide/common-mistakes/"}
    ]
}

mega_html = generator.apply_layout(html_content, mega_metadata)

mega_file = demo_dir / "demo_mega_guide.html"
mega_file.write_text(mega_html)
print(f"   ✅ Saved: {mega_file}")

# Create index page
print("\n3️⃣  Generating demo index page...")
index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Layout Demos - Choose a Page Type</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #EFF6FF 0%, #F3E8FF 50%, #FCE7F3 100%);
            min-height: 100vh;
            padding: 2rem;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 2.5rem;
            color: #1f2937;
            margin-bottom: 1rem;
            text-align: center;
        }}
        .subtitle {{
            text-align: center;
            color: #6b7280;
            margin-bottom: 3rem;
            font-size: 1.125rem;
        }}
        .demo-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }}
        .demo-card {{
            background: white;
            border-radius: 1rem;
            padding: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .demo-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 12px rgba(147, 51, 234, 0.2);
        }}
        .demo-card h2 {{
            color: #9333ea;
            margin-bottom: 1rem;
            font-size: 1.5rem;
        }}
        .demo-card p {{
            color: #6b7280;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }}
        .demo-card ul {{
            list-style: none;
            margin-bottom: 1.5rem;
            color: #374151;
        }}
        .demo-card li {{
            padding: 0.5rem 0;
            padding-left: 1.5rem;
            position: relative;
        }}
        .demo-card li:before {{
            content: "✓";
            position: absolute;
            left: 0;
            color: #22c55e;
            font-weight: bold;
        }}
        .demo-link {{
            display: block;
            background: #9333ea;
            color: white;
            text-decoration: none;
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            text-align: center;
            font-weight: 600;
            transition: background 0.2s;
        }}
        .demo-link:hover {{
            background: #7c3aed;
        }}
        .info-box {{
            background: white;
            border-left: 4px solid #9333ea;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin-top: 2rem;
        }}
        .info-box h3 {{
            color: #1f2937;
            margin-bottom: 0.5rem;
        }}
        .info-box p {{
            color: #6b7280;
            line-height: 1.6;
        }}
        .badge {{
            display: inline-block;
            background: #f3e8ff;
            color: #6b21a8;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.875rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 Layout Demos</h1>
        <p class="subtitle">Compare the two page layout types matching approved mockups</p>

        <div class="demo-grid">
            <div class="demo-card">
                <span class="badge">30 pages</span>
                <h2>📄 Source Type Layout</h2>
                <p>Single-column design (900px) with related resources grid at the bottom.</p>
                <ul>
                    <li>Wider content area</li>
                    <li>No sidebar</li>
                    <li>Related-grid at bottom</li>
                    <li>Dark footer</li>
                </ul>
                <a href="demo_source_type.html" class="demo-link">View Demo →</a>
            </div>

            <div class="demo-card">
                <span class="badge">15 pages</span>
                <h2>📚 Mega Guide Layout</h2>
                <p>Two-column design (1200px) with sidebar containing page info and related guides.</p>
                <ul>
                    <li>Sidebar with navigation</li>
                    <li>Page info display</li>
                    <li>Related guides list</li>
                    <li>Dark footer</li>
                </ul>
                <a href="demo_mega_guide.html" class="demo-link">View Demo →</a>
            </div>
        </div>

        <div class="info-box">
            <h3>✅ Both layouts match approved mockups 1-to-1</h3>
            <p><strong>Source Type:</strong> Matches <code>design/mocks/source_type_mockup.html</code></p>
            <p><strong>Mega Guide:</strong> Matches <code>design/mocks/mega_guide_mockup.html</code></p>
            <p style="margin-top: 1rem;">Both use purple branding (#9333ea), gradient backgrounds, and dark footers. Layouts automatically apply based on page type during content generation.</p>
        </div>
    </div>
</body>
</html>"""

index_file = demo_dir / "index.html"
index_file.write_text(index_html)
print(f"   ✅ Saved: {index_file}")

print(f"\n✨ Demo generation complete!")
print(f"\n📂 Demo files location: {demo_dir.absolute()}")
print(f"\n🌐 To view demos:")
print(f"   1. Open: {index_file.absolute()}")
print(f"   2. Or run: open {index_file}")
print(f"\n💡 Compare these with the approved mockups:")
print(f"   • design/mocks/source_type_mockup.html")
print(f"   • design/mocks/mega_guide_mockup.html")
