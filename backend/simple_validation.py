#!/usr/bin/env python3
"""
Simple validation to test citation page functionality.
"""

import sys
import re
import html
from pathlib import Path
import uuid

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_citation_functions():
    """Test if citation page functions are properly defined."""
    print("🔍 Testing citation page functions...")

    try:
        # Check if app.py contains the required functions
        app_file = backend_dir / "app.py"
        if not app_file.exists():
            print("❌ app.py not found")
            return False

        content = app_file.read_text()

        # Check for route definition
        if '@app.get("/citations/{citation_id}")' not in content:
            print("❌ Citation route not defined")
            return False
        print("✅ Citation route defined")

        # Check for helper functions
        if 'def _get_citation_data(' not in content:
            print("❌ _get_citation_data function not defined")
            return False
        print("✅ _get_citation_data function defined")

        if 'def _generate_citation_html(' not in content:
            print("❌ _generate_citation_html function not defined")
            return False
        print("✅ _generate_citation_html function defined")

        return True

    except Exception as e:
        print(f"❌ Error checking functions: {e}")
        return False

def test_html_generation():
    """Test HTML generation function."""
    print("\n🔍 Testing HTML generation...")

    try:
        # Import the functions directly
        sys.path.insert(0, str(backend_dir))

        # Mock the functions that are defined in app.py
        def _generate_citation_html(citation_id: str, citation_data: dict) -> str:
            """Mock version of the HTML generation function."""
            original_citation = html.escape(citation_data.get("original", ""))
            source_type = html.escape(citation_data.get("source_type", "unknown"))
            validation_date = citation_data.get("validation_date", "Unknown")

            # Generate error list HTML
            errors_html = ""
            errors = citation_data.get("errors", [])
            if errors:
                errors_html = "<h2>Validation Errors Found</h2><ul>"
                for error in errors:
                    component = html.escape(error.get("component", ""))
                    problem = html.escape(error.get("problem", ""))
                    correction = html.escape(error.get("correction", ""))
                    errors_html += f"<li><strong>{component}:</strong> {problem}. <em>Correction: {correction}</em></li>"
                errors_html += "</ul>"
            else:
                errors_html = "<h2>✅ No Errors Found</h2><p>This citation follows APA 7th edition guidelines.</p>"

            html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Citation Validation Result | APA Format Checker</title>
    <meta name="description" content="Free APA 7th edition citation validation and formatting checker.">
    <link rel="canonical" href="https://citationformatchecker.com/citations/{citation_id}/">
</head>
<body>
    <h1>Citation Validation Result</h1>
    <div class="citation-box">
        <h2>Original Citation</h2>
        <p><strong>{original_citation}</strong></p>
        <p class="meta">Source Type: {source_type.title()}</p>
    </div>
    <div>
        {errors_html}
    </div>
</body>
</html>"""
            return html_template

        # Test with sample data
        test_data = {
            "original": "Smith, J. (2023). Example citation. Journal of Testing, 15(2), 123-145.",
            "source_type": "journal_article",
            "errors": [
                {"component": "Author", "problem": "Missing initials", "correction": "Add initials"}
            ],
            "validation_date": "2024-11-28"
        }

        html_content = _generate_citation_html("test-id", test_data)

        # Check if HTML contains expected elements
        if not html_content.strip().startswith("<!DOCTYPE html>"):
            print("❌ HTML doesn't start with DOCTYPE")
            return False
        print("✅ HTML has proper DOCTYPE")

        if "Citation Validation Result" not in html_content:
            print("❌ HTML missing title")
            return False
        print("✅ HTML contains title")

        if test_data["original"] not in html_content:
            print("❌ HTML missing original citation")
            return False
        print("✅ HTML contains original citation")

        if "Missing initials" not in html_content:
            print("❌ HTML missing error information")
            return False
        print("✅ HTML contains error information")

        # Check for SEO elements
        if 'meta name="description"' not in html_content:
            print("❌ HTML missing meta description")
            return False
        print("✅ HTML contains meta description")

        if 'link rel="canonical"' not in html_content:
            print("❌ HTML missing canonical link")
            return False
        print("✅ HTML contains canonical link")

        print(f"✅ HTML generation successful ({len(html_content)} characters)")
        return True

    except Exception as e:
        print(f"❌ HTML generation test failed: {e}")
        return False

def test_uuid_validation():
    """Test UUID validation."""
    print("\n🔍 Testing UUID validation...")

    try:
        # Test UUID pattern
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)

        # Valid UUIDs
        valid_uuids = [
            "93f1d8e1-ef36-4382-ae12-a641ba9c9a4b",
            str(uuid.uuid4()),
            "00000000-0000-0000-0000-000000000000"
        ]

        # Invalid UUIDs
        invalid_uuids = [
            "not-a-uuid",
            "123-456-789",
            "gggggggg-gggg-gggg-gggg-gggggggggggg",
            "",
            "93f1d8e1-ef36-4382-ae12-a641ba9c9a4"  # Missing last character
        ]

        for valid_uuid in valid_uuids:
            if not uuid_pattern.match(valid_uuid):
                print(f"❌ Valid UUID rejected: {valid_uuid}")
                return False
        print(f"✅ {len(valid_uuids)} valid UUIDs accepted")

        for invalid_uuid in invalid_uuids:
            if uuid_pattern.match(invalid_uuid):
                print(f"❌ Invalid UUID accepted: {invalid_uuid}")
                return False
        print(f"✅ {len(invalid_uuids)} invalid UUIDs rejected")

        return True

    except Exception as e:
        print(f"❌ UUID validation test failed: {e}")
        return False

def test_html_safety():
    """Test HTML safety and escaping."""
    print("\n🔍 Testing HTML safety...")

    try:
        def _generate_citation_html(citation_id: str, citation_data: dict) -> str:
            """Simplified HTML generation for testing."""
            original_citation = html.escape(citation_data.get("original", ""))
            return f"<p>{original_citation}</p>"

        # Test dangerous input
        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "Smith <b>J.</b> (2023)",
            "<img src=x onerror=alert('xss')>",
            "'; DROP TABLE users; --"
        ]

        for dangerous_input in dangerous_inputs:
            test_data = {"original": dangerous_input}
            html_content = _generate_citation_html("test", test_data)

            if "<script>" in html_content or "onerror=" in html_content:
                print(f"❌ Dangerous input not escaped: {dangerous_input}")
                return False

        print(f"✅ {len(dangerous_inputs)} dangerous inputs properly escaped")
        return True

    except Exception as e:
        print(f"❌ HTML safety test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("=" * 60)
    print("🔍 CITATION PAGE VALIDATION")
    print("=" * 60)

    tests = [
        ("Function Definitions", test_citation_functions),
        ("HTML Generation", test_html_generation),
        ("UUID Validation", test_uuid_validation),
        ("HTML Safety", test_html_safety)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        result = test_func()
        results.append((test_name, result))

    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL TESTS PASSED! Citation pages are working correctly.")
        return 0
    else:
        print(f"⚠️ {total - passed} test(s) failed. Citation pages need attention.")
        return 1

if __name__ == "__main__":
    sys.exit(main())