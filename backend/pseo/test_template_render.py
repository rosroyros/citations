#!/usr/bin/env python3
"""
Test script to render source type template with test data
"""
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

def test_source_type_template():
    """Test that the source type template renders with test data"""

    # Setup paths
    templates_dir = Path("templates")
    test_data_file = Path("test_data/source_type_test.json")
    output_file = Path("test_output/source_type_rendered.md")

    # Load template
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("source_type_template.md")

    # Load test data
    with open(test_data_file) as f:
        test_data = json.load(f)

    # Render template
    rendered_content = template.render(**test_data)

    # Save output
    output_file.parent.mkdir(exist_ok=True)
    output_file.write_text(rendered_content)

    print(f"✅ Template rendered successfully!")
    print(f"   Input: {test_data_file}")
    print(f"   Output: {output_file}")
    print(f"   Word count: {len(rendered_content.split()):,} words")

    # Check for any unrendered variables
    if "{{" in rendered_content and "}}" in rendered_content:
        print("⚠️  Warning: Found unrendered template variables")
        import re
        variables = re.findall(r'{{([^}]+)}}', rendered_content)
        print(f"   Missing variables: {variables}")
    else:
        print("✅ All template variables rendered successfully")

    return rendered_content

if __name__ == "__main__":
    test_source_type_template()