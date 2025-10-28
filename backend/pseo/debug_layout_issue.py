#!/usr/bin/env python3
"""
Debug script to isolate the exact issue with layout template rendering
"""

import json
import os
from pathlib import Path
from builder.static_generator import StaticSiteGenerator
from jinja2 import Template

def main():
    # Test with capitalization.md since we know it works
    markdown_file = "/Users/roy/Documents/Projects/citations/content/test/capitalization.md"

    print("=" * 80)
    print("DEBUGGING LAYOUT TEMPLATE ISSUE")
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

    print(f"\n1. Testing markdown file: {markdown_file}")
    print(f"   File exists: {os.path.exists(markdown_file)}")

    # Extract front matter
    print("\n2. Extracting front matter...")
    try:
        with open(markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()

        front_matter, markdown_content = generator._extract_front_matter(content)
        print(f"   Front matter keys: {list(front_matter.keys())}")
        print(f"   Front matter items: {len(front_matter)}")
        print(f"   Markdown content length: {len(markdown_content)} characters")

    except Exception as e:
        print(f"   ERROR: {e}")
        return

    # Convert markdown to HTML
    print("\n3. Converting markdown to HTML...")
    try:
        html_content = generator.convert_markdown_to_html(markdown_content)
        print(f"   HTML content length: {len(html_content)} characters")
        print(f"   First 200 chars: {html_content[:200]}...")

    except Exception as e:
        print(f"   ERROR: {e}")
        return

    # Test layout template directly with Jinja2
    print("\n4. Testing layout template with Jinja2...")
    try:
        # Setup Jinja2 environment with template string
        template = Template(layout_template)

        # Prepare template context
        context = {
            'meta_title': front_matter.get('title', 'Default Title'),
            'meta_description': front_matter.get('description', 'Default Description'),
            'base_url': 'https://citationformatchecker.com',
            'url': front_matter.get('url', '/test/'),
            'page_type': front_matter.get('page_type', 'article'),
            'content': html_content,
            **front_matter  # Add all front matter variables
        }

        print(f"   Template context keys: {list(context.keys())}")
        print(f"   Content variable length: {len(context['content'])}")

        # Render template
        rendered = template.render(**context)
        print(f"   Rendered HTML length: {len(rendered)} characters")
        print(f"   First 200 chars: {rendered[:200]}...")
        print(f"   Last 200 chars: ...{rendered[-200:]}")

        # Check for specific content
        if '<html' in rendered:
            print("   ✓ Contains <html> tag")
        else:
            print("   ✗ Missing <html> tag")

        if '<title>' in rendered:
            print("   ✓ Contains <title> tag")
        else:
            print("   ✗ Missing <title> tag")

        if context['content'] in rendered:
            print("   ✓ Contains markdown content")
        else:
            print("   ✗ Missing markdown content")

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test the exact apply_layout method
    print("\n5. Testing apply_layout method...")
    try:
        final_html = generator.apply_layout(front_matter, html_content)
        print(f"   Final HTML length: {len(final_html)} characters")
        print(f"   First 200 chars: {final_html[:200]}...")
        print(f"   Last 200 chars: ...{final_html[-200:]}")

        if len(final_html) < 100:
            print(f"   ⚠️  WARNING: Final HTML is very short ({len(final_html)} chars)")
            print(f"   Full content: '{final_html}'")

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 80)
    print("DEBUGGING COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()