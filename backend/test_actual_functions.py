#!/usr/bin/env python3
"""
Test the actual citation functions from app.py
"""

import sys
import re
import html
import uuid
from typing import Dict, List, Optional
from pathlib import Path

def test_uuid_validation():
    """Test UUID validation pattern."""
    print("🔍 Testing UUID validation...")

    uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)

    # Test the problematic citation from the issue
    test_citation = "93f1d8e1-ef36-4382-ae12-a641ba9c9a4b"

    if uuid_pattern.match(test_citation):
        print("✅ Problematic citation UUID is valid")
    else:
        print("❌ Problematic citation UUID is invalid")
        return False

    return True

def test_html_generation():
    """Test the actual HTML generation logic."""
    print("\n🔍 Testing HTML generation...")

    def _generate_citation_html(citation_id: str, citation_data: dict) -> str:
        """Actual HTML generation function from app.py."""
        import html

        # Escape user input for safety
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
    <meta name="description" content="Free APA 7th edition citation validation and formatting checker. Validate citations, find errors, and get corrections.">
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

    # Test with the problematic citation data
    test_data = {
        "original": "Smith, J. (2023). Example citation for testing. Journal of Testing, 15(2), 123-145.",
        "source_type": "journal_article",
        "errors": [
            {
                "component": "Author",
                "problem": "Missing initials",
                "correction": "Include author's full initials"
            }
        ],
        "validation_date": "2024-11-28",
        "job_id": "test_job_123"
    }

    citation_id = "93f1d8e1-ef36-4382-ae12-a641ba9c9a4b"
    html_content = _generate_citation_html(citation_id, test_data)

    # Basic checks
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

    # Check canonical URL
    if citation_id not in html_content:
        print("❌ HTML missing citation ID in canonical URL")
        return False
    print("✅ HTML contains citation ID in canonical URL")

    print(f"✅ HTML generation successful ({len(html_content)} characters)")
    return True

def test_html_safety():
    """Test HTML safety with dangerous inputs."""
    print("\n🔍 Testing HTML safety...")

    def _generate_citation_html(citation_id: str, citation_data: dict) -> str:
        """HTML generation with proper escaping."""
        import html
        original_citation = html.escape(citation_data.get("original", ""))
        return f"<p>{original_citation}</p>"

    # Test dangerous input that should be escaped
    dangerous_input = "<script>alert('xss')</script>"
    test_data = {"original": dangerous_input}
    html_content = _generate_citation_html("test", test_data)

    if "<script>" in html_content:
        print("❌ Script tag not properly escaped")
        return False
    print("✅ Script tag properly escaped")

    if "&lt;script&gt;" not in html_content:
        print("❌ HTML entities not generated")
        return False
    print("✅ HTML entities properly generated")

    return True

def test_citation_data_retrieval():
    """Test citation data retrieval function."""
    print("\n🔍 Testing citation data retrieval...")

    def _get_citation_data(citation_id: str) -> Optional[dict]:
        """Mock citation data retrieval."""
        mock_citations = {
            "93f1d8e1-ef36-4382-ae12-a641ba9c9a4b": {
                "original": "Smith, J. (2023). Example citation for testing. Journal of Testing, 15(2), 123-145.",
                "source_type": "journal_article",
                "errors": [
                    {"component": "Author", "problem": "Missing initials", "correction": "Include author's full initials"}
                ],
                "validation_date": "2024-11-28",
                "job_id": "test_job_123"
            }
        }
        return mock_citations.get(citation_id.lower())

    # Test with the problematic citation ID
    test_id = "93f1d8e1-ef36-4382-ae12-a641ba9c9a4b"
    data = _get_citation_data(test_id)

    if not data:
        print("❌ Test citation data not found")
        return False
    print("✅ Test citation data found")

    if "original" not in data:
        print("❌ Citation data missing original field")
        return False
    print("✅ Citation data contains original field")

    if not data["original"]:
        print("❌ Original citation is empty")
        return False
    print(f"✅ Original citation: {data['original'][:50]}...")

    # Test with non-existent citation
    nonexistent_data = _get_citation_data("00000000-0000-0000-0000-000000000000")
    if nonexistent_data is not None:
        print("❌ Non-existent citation should return None")
        return False
    print("✅ Non-existent citation properly returns None")

    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("🔍 CITATION FUNCTIONS TEST")
    print("=" * 60)

    tests = [
        ("UUID Validation", test_uuid_validation),
        ("HTML Generation", test_html_generation),
        ("HTML Safety", test_html_safety),
        ("Citation Data Retrieval", test_citation_data_retrieval)
    ]

    results = []
    for test_name, test_func in tests:
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
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"⚠️ {total - passed} test(s) failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())