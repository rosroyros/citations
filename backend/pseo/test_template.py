#!/usr/bin/env python3
"""
Test script to validate Mega Guide template rendering
"""
import json
from pathlib import Path
from jinja2 import Template

def test_mega_guide_template():
    """Test that the mega guide template renders correctly with test data"""

    # Load template
    template_path = Path("templates/mega_guide_template.md")
    if not template_path.exists():
        print("❌ Template file not found")
        return False

    template_content = template_path.read_text()
    template = Template(template_content)

    # Load test data
    test_data_path = Path("test_data/mega_guide_test.json")
    if not test_data_path.exists():
        print("❌ Test data file not found")
        return False

    test_data = json.loads(test_data_path.read_text())

    # Render template
    try:
        rendered = template.render(**test_data)
        print("✅ Template rendered successfully")

        # Check for required sections
        required_sections = [
            "Table of Contents",
            "TL;DR - Quick Summary",
            "Introduction",
            "Comprehensive Examples",
            "Common Errors to Avoid",
            "Validation Checklist",
            "APA 6 vs 7 Changes",
            "Frequently Asked Questions",
            "Related Resources",
            "Conclusion"
        ]

        missing_sections = []
        for section in required_sections:
            if section not in rendered:
                missing_sections.append(section)

        if missing_sections:
            print(f"❌ Missing sections: {missing_sections}")
            return False
        else:
            print("✅ All required sections present")

        # Check word count
        word_count = len(rendered.split())
        if word_count < 5000:
            print(f"⚠️  Content seems short: {word_count} words (target: 5000+)")
        else:
            print(f"✅ Good length: {word_count} words")

        # Check variable substitution
        if "{{" in rendered or "}}" in rendered:
            print("❌ Unresolved template variables found")
            return False
        else:
            print("✅ All template variables resolved")

        # Save rendered output for inspection
        output_path = Path("test_data/rendered_mega_guide.md")
        output_path.write_text(rendered)
        print(f"✅ Rendered output saved to {output_path}")

        return True

    except Exception as e:
        print(f"❌ Template rendering failed: {e}")
        return False

def count_template_variables():
    """Count unique variables in the template"""
    template_path = Path("templates/mega_guide_template.md")
    template_content = template_path.read_text()

    import re
    variables = re.findall(r'\{\{\s*([^}]+)\s*\}\}', template_content)
    unique_vars = set(var.strip() for var in variables)

    print(f"✅ Template contains {len(unique_vars)} unique variables")
    print("Variables found:")
    for var in sorted(unique_vars):
        print(f"  - {var}")

    return len(unique_vars)

if __name__ == "__main__":
    print("Testing Mega Guide Template...")
    print("=" * 50)

    var_count = count_template_variables()
    if var_count >= 15:
        print(f"✅ Minimum variable count met: {var_count} >= 15")
    else:
        print(f"❌ Not enough variables: {var_count} < 15")

    print()
    if test_mega_guide_template():
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Tests failed")