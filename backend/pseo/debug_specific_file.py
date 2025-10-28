#!/usr/bin/env python3
"""
Debug script to test the specific capitalization.md file conversion
"""

import os
from builder.static_generator import StaticSiteGenerator
from pathlib import Path

def main():
    print("=" * 80)
    print("DEBUGGING SPECIFIC CAPITALIZATION.MD FILE")
    print("=" * 80)

    # Read the layout template
    template_path = "/Users/roy/Documents/Projects/citations/backend/pseo/builder/templates/layout.html"
    with open(template_path, 'r') as f:
        layout_template = f.read()

    # Initialize generator exactly as the script does
    generator = StaticSiteGenerator(layout_template)

    # Test the specific file
    markdown_file = "/Users/roy/Documents/Projects/citations/content/test/capitalization.md"
    output_dir = "/tmp/debug_specific_file"

    print(f"\n1. Testing file: {markdown_file}")
    print(f"   File exists: {os.path.exists(markdown_file)}")

    if not os.path.exists(markdown_file):
        print("   ERROR: File does not exist!")
        return

    # Read the file directly
    with open(markdown_file, 'r') as f:
        content = f.read()

    print(f"   Content length: {len(content)} characters")
    print(f"   First 100 chars: {content[:100]}...")

    # Extract front matter manually
    print(f"\n2. Extracting front matter...")
    try:
        front_matter, markdown_content = generator._extract_front_matter(content)
        print(f"   Front matter type: {type(front_matter)}")
        print(f"   Front matter keys: {list(front_matter.keys()) if isinstance(front_matter, dict) else 'NOT A DICT'}")
        print(f"   Markdown content length: {len(markdown_content)}")
        print(f"   Required fields present: page_type={front_matter.get('page_type')}, url_slug={front_matter.get('url_slug')}")
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test the full build_site method
    print(f"\n3. Testing build_site method...")
    try:
        content_dir = Path(markdown_file).parent
        generator.build_site(str(content_dir), output_dir)
        print(f"   build_site completed")

        # Check the output
        output_file = Path(output_dir) / "capitalization" / "index.html"
        if output_file.exists():
            size = output_file.stat().st_size
            content = output_file.read_text()
            print(f"   Output file size: {size} characters")
            print(f"   First 100 chars: {content[:100]}...")

            if content.startswith('---'):
                print("   ❌ ERROR: Output is still markdown, not HTML!")
            elif content.startswith('<!DOCTYPE'):
                print("   ✅ SUCCESS: Output is proper HTML!")
            else:
                print(f"   ⚠️  WARNING: Unexpected output format")
        else:
            print(f"   ERROR: Output file not found: {output_file}")

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("DEBUGGING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()