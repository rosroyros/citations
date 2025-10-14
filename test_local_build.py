#!/usr/bin/env python3
"""Test static site generation with the 5 test pages"""

import json
from pathlib import Path
from backend.pseo.builder.static_generator import StaticSiteGenerator

def test_local_build():
    """Build test pages locally"""

    # Initialize generator
    layout_path = Path("backend/pseo/builder/templates/layout.html")
    layout_content = layout_path.read_text()
    generator = StaticSiteGenerator(layout_content)

    # Test pages
    test_pages = [
        "check-apa-citations.md",
        "apa-citation-errors.md",
        "how-to-cite-journal-article-apa.md",
        "how-to-cite-book-apa.md",
        # Note: how-to-cite-website-apa.md is missing from the list
    ]

    output_dir = Path("dist_test")
    output_dir.mkdir(exist_ok=True)

    pages_built = []

    for page_file in test_pages:
        md_path = Path(f"content/test/{page_file}")

        if not md_path.exists():
            print(f"⚠️  Missing: {page_file}")
            continue

        print(f"\n📝 Processing: {page_file}")

        # Read markdown
        md_content = md_path.read_text()

        # Extract front matter
        front_matter, content = generator._extract_front_matter(md_content)

        # Convert to HTML
        html_content = generator.convert_markdown_to_html(content)

        # Map front matter to template variables
        template_metadata = {
            'meta_title': front_matter.get('title', ''),
            'meta_description': front_matter.get('description', ''),
            'url': f'/{page_file.replace(".md", "")}/',
            **front_matter
        }

        # Apply layout
        final_html = generator.apply_layout(html_content, template_metadata)

        # Generate output path
        url_slug = front_matter.get('url_slug', page_file.replace('.md', ''))
        output_path = output_dir / f"{url_slug}.html"

        # Save HTML
        output_path.write_text(final_html)

        pages_built.append({
            "file": page_file,
            "output": str(output_path),
            "words": len(content.split()),
            "chars": len(final_html)
        })

        print(f"   ✅ Built: {output_path}")
        print(f"   📊 Words: {pages_built[-1]['words']:,}")

    print(f"\n🎉 Built {len(pages_built)} pages in dist_test/")
    print("\n📋 Pages built:")
    for page in pages_built:
        print(f"   - {page['file']} → {page['output']} ({page['words']:,} words)")

    return pages_built

if __name__ == "__main__":
    test_local_build()