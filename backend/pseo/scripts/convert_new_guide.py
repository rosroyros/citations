#!/usr/bin/env python3
"""Convert the newly generated guide to HTML"""

import json
import sys
from pathlib import Path

# Add the parent directory to the path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

from builder.static_generator import StaticSiteGenerator

def main():
    """Convert the newly generated guide to HTML"""

    # Load the newly generated content
    content_file = Path(__file__).parent.parent / "content" / "generated_content" / "mega_guide_02_check-apa-citations.json"

    if not content_file.exists():
        print(f"❌ Content file not found: {content_file}")
        return False

    with open(content_file, 'r') as f:
        guide_data = json.load(f)

    print(f"🔄 Converting to HTML: {guide_data['title']}")

    # Load layout template
    layout_file = Path(__file__).parent.parent / "templates" / "layout.html"
    if not layout_file.exists():
        print(f"❌ Layout template not found: {layout_file}")
        return False

    with open(layout_file, 'r') as f:
        layout_template = f.read()

    # Initialize generator
    generator = StaticSiteGenerator(layout_template, base_url="https://citationchecker.com")

    # Convert markdown to HTML
    html_content = generator.convert_markdown_to_html(guide_data["content"])

    # Create full page with layout
    page_data = {
        "title": guide_data["title"],
        "meta_title": guide_data["metadata"].get("meta_title", guide_data["title"]),
        "meta_description": guide_data["metadata"].get("meta_description", ""),
        "url": f"/guide/{guide_data['title'].lower().replace(' ', '-')}/",
        "page_type": guide_data["metadata"].get("page_type", "mega_guide"),
        "last_updated": guide_data["metadata"].get("last_updated", ""),
        "reading_time": guide_data["metadata"].get("reading_time", ""),
        "word_count": guide_data["word_count"]
    }

    full_html = generator.apply_layout(html_content, page_data)

    # Save HTML file
    output_dir = Path(__file__).parent / "dist" / "mega-guides"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "mega_guide_02_check-apa-citations.html"
    with open(output_file, 'w') as f:
        f.write(full_html)

    print(f"✅ HTML saved to: {output_file}")
    print(f"📄 Word count: {guide_data['word_count']:,}")
    print(f"🌐 Open in browser: http://localhost:8080/mega-guides/mega_guide_02_check-apa-citations.html")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)