#!/usr/bin/env python3
"""
Debug script to test the apply_layout method specifically
"""

import os
from builder.static_generator import StaticSiteGenerator

def main():
    print("=" * 80)
    print("DEBUGGING APPLY_LAYOUT METHOD")
    print("=" * 80)

    # Read the layout template
    template_path = "/Users/roy/Documents/Projects/citations/backend/pseo/builder/templates/layout.html"
    with open(template_path, 'r') as f:
        layout_template = f.read()

    # Initialize the generator
    generator = StaticSiteGenerator(
        layout_template=layout_template,
        base_url="https://citationformatchecker.com"
    )

    # Test data
    test_metadata = {
        'title': 'Test Page',
        'description': 'Test Description',
        'page_type': 'article',
        'url_slug': 'test-page'
    }
    test_html = "<h1>Test Content</h1><p>This is test content.</p>"

    print(f"\n1. Test data prepared:")
    print(f"   Metadata type: {type(test_metadata)}")
    print(f"   Metadata keys: {list(test_metadata.keys())}")
    print(f"   HTML type: {type(test_html)}")
    print(f"   HTML length: {len(test_html)} characters")

    print(f"\n2. Testing apply_layout with correct parameters...")
    try:
        result = generator.apply_layout(test_html, test_metadata)
        print(f"   SUCCESS: Result length: {len(result)} characters")
        print(f"   First 100 chars: {result[:100]}...")
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n3. Testing apply_layout with swapped parameters...")
    try:
        result = generator.apply_layout(test_metadata, test_html)  # WRONG ORDER
        print(f"   SUCCESS: Result length: {len(result)} characters")
        print(f"   First 100 chars: {result[:100]}...")
    except Exception as e:
        print(f"   ERROR: {e}")
        print(f"   This confirms the issue - parameters are swapped somewhere!")

    print(f"\n4. Testing what build_site is actually doing...")

    # Simulate what build_site does
    markdown_file = "/Users/roy/Documents/Projects/citations/content/test/capitalization.md"

    if os.path.exists(markdown_file):
        print(f"   Reading: {markdown_file}")
        with open(markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()

        front_matter, markdown_content = generator._extract_front_matter(content)
        print(f"   Front matter type: {type(front_matter)}")
        print(f"   Front matter keys: {list(front_matter.keys()) if isinstance(front_matter, dict) else 'NOT A DICT'}")

        html_content = generator.convert_markdown_to_html(markdown_content)
        print(f"   HTML content type: {type(html_content)}")
        print(f"   HTML content length: {len(html_content)}")

        print(f"   Calling apply_layout as build_site does...")
        try:
            final_html = generator.apply_layout(html_content, front_matter)
            print(f"   SUCCESS: Final HTML length: {len(final_html)} characters")
            if len(final_html) < 100:
                print(f"   WARNING: Very short output: '{final_html}'")
        except Exception as e:
            print(f"   ERROR in build_site simulation: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("DEBUGGING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()