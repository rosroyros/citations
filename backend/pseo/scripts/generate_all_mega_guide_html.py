#!/usr/bin/env python3
"""Generate HTML for all available mega guide JSON files"""

import json
import sys
from pathlib import Path

# Add the parent directory to the path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

from builder.enhanced_static_generator import EnhancedStaticSiteGenerator

def find_mega_guide_files():
    """Find all JSON files with page_type = mega_guide"""
    base_dirs = [
        Path(__file__).parent.parent.parent / "content" / "test",
        Path(__file__).parent.parent / "content" / "review_queue",
        Path(__file__).parent.parent.parent / "content",
        Path(__file__).parent.parent / "content" / "test"
    ]

    mega_guides = []

    for base_dir in base_dirs:
        if not base_dir.exists():
            continue

        for json_file in base_dir.glob("**/*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)

                # Check if it's a mega guide
                if isinstance(data, dict):
                    page_type = data.get('page_type') or data.get('metadata', {}).get('page_type')
                    if page_type == 'mega_guide':
                        mega_guides.append(json_file)
                        print(f"Found mega guide: {json_file}")

            except (json.JSONDecodeError, KeyError) as e:
                continue  # Skip invalid files

    return mega_guides

def convert_json_to_guide_data(json_file):
    """Convert JSON file to guide data format expected by preview script"""
    with open(json_file, 'r') as f:
        data = json.load(f)

    # Handle different JSON structures
    if 'config' in data:
        # Stats format
        config = data['config']
        content = data.get('content', '')
        metadata = data.get('metadata', {})
    else:
        # Direct format
        config = data
        content = data.get('content', '')
        metadata = data.get('metadata', {})

    return {
        "title": config.get('title', 'Untitled Guide'),
        "content": content,
        "metadata": {
            "page_type": "mega_guide",
            "meta_title": config.get('title', 'Untitled Guide'),
            "meta_description": config.get('description', ''),
            "last_updated": "2025-10-14",
            "reading_time": "25 minutes",
            "word_count": len(content.split())
        },
        "word_count": len(content.split())
    }

def main():
    """Generate HTML for all mega guides"""

    print("🔍 Finding all mega guide JSON files...")
    mega_guides = find_mega_guide_files()

    if not mega_guides:
        print("❌ No mega guide files found")
        return False

    print(f"✅ Found {len(mega_guides)} mega guide(s)")

    # Load layout template
    layout_file = Path(__file__).parent.parent / "templates" / "layout.html"
    if not layout_file.exists():
        print(f"❌ Layout template not found: {layout_file}")
        return False

    with open(layout_file, 'r') as f:
        layout_template = f.read()

    # Initialize generator
    generator = EnhancedStaticSiteGenerator(layout_template, base_url="https://citationchecker.com")

    # Create output directory
    output_dir = Path(__file__).parent / "dist" / "mega-guides"
    output_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0

    for json_file in mega_guides:
        try:
            print(f"\n📝 Processing: {json_file.name}")

            # Convert JSON to guide data
            guide_data = convert_json_to_guide_data(json_file)

            # Convert markdown to HTML
            html_content = generator.convert_markdown_to_html(guide_data["content"])

            # Create page data for layout
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

            # Apply layout
            full_html = generator.apply_layout(html_content, page_data)

            # Save HTML file
            output_filename = f"{json_file.stem}.html"
            output_file = output_dir / output_filename

            with open(output_file, 'w') as f:
                f.write(full_html)

            print(f"  ✅ Generated: {output_filename}")
            print(f"  📄 Word count: {guide_data['word_count']:,}")
            print(f"  🌐 Open: http://localhost:8080/mega-guides/{output_filename}")

            success_count += 1

        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"\n🎉 Complete! Generated {success_count}/{len(mega_guides)} HTML files")
    print(f"📁 Output directory: {output_dir}")
    print(f"\n📖 Available guides at:")

    for html_file in sorted(output_dir.glob("*.html")):
        print(f"  - http://localhost:8080/mega-guides/{html_file.name}")

    return success_count > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)