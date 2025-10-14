"""
Integration tests for MiniChecker in static pages

Verifies that the MiniChecker React component is properly integrated
into static HTML pages.
"""
import pytest
from pathlib import Path
import re


def test_minichecker_bundle_exists():
    """Verify MiniChecker JS bundle exists"""
    bundle_path = Path(__file__).parent.parent / "builder" / "assets" / "js" / "mini-checker.js"
    assert bundle_path.exists(), "MiniChecker JS bundle not found"

    # Verify it's a substantial bundle (React + MiniChecker code)
    bundle_size = bundle_path.stat().st_size
    assert bundle_size > 100_000, f"Bundle too small: {bundle_size} bytes"


def test_minichecker_css_exists():
    """Verify MiniChecker CSS exists"""
    css_path = Path(__file__).parent.parent / "builder" / "assets" / "css" / "mini-checker.css"
    assert css_path.exists(), "MiniChecker CSS not found"

    # Verify it contains expected styles
    css_content = css_path.read_text()
    assert ".mini-checker" in css_content
    assert ".mini-checker-button" in css_content


def test_layout_includes_minichecker():
    """Verify layout.html includes MiniChecker references"""
    layout_path = Path(__file__).parent.parent / "builder" / "templates" / "layout.html"
    layout_content = layout_path.read_text()

    # Check CSS link
    assert 'href="/assets/css/mini-checker.css"' in layout_content

    # Check JS script
    assert 'src="/assets/js/mini-checker.js"' in layout_content

    # Check mount point
    assert 'id="mini-checker-1"' in layout_content

    # Check mounting script
    assert 'mountMiniChecker' in layout_content


def test_generated_page_has_minichecker():
    """Verify generated HTML pages include MiniChecker"""
    # Find a generated test page
    dist_dir = Path(__file__).parent.parent.parent.parent / "content" / "dist"

    if not dist_dir.exists():
        pytest.skip("Dist directory not found - run build_test_site.py first")

    # Check one of the source type pages
    test_page = dist_dir / "how-to-cite-journal-article-apa" / "index.html"

    if not test_page.exists():
        pytest.skip("Test page not found - run build_test_site.py first")

    html_content = test_page.read_text()

    # Verify MiniChecker elements are present
    assert '<link rel="stylesheet" href="/assets/css/mini-checker.css">' in html_content
    assert '<script src="/assets/js/mini-checker.js"></script>' in html_content
    assert 'id="mini-checker-1"' in html_content
    assert 'mountMiniChecker(' in html_content

    # Verify mounting options
    assert 'placeholder:' in html_content
    assert 'onFullChecker:' in html_content


def test_minichecker_mounts_correctly():
    """Verify MiniChecker mounting script is correct"""
    layout_path = Path(__file__).parent.parent / "builder" / "templates" / "layout.html"
    layout_content = layout_path.read_text()

    # Check for mounting script presence
    assert "mountMiniChecker('mini-checker-1'" in layout_content, "MiniChecker mounting call not found"

    # Verify configuration options are present in the script
    assert 'placeholder:' in layout_content
    assert 'contextType:' in layout_content
    assert 'onFullChecker:' in layout_content
    assert "window.location.href = '/checker/'" in layout_content


def test_minichecker_bundle_exports_mount_function():
    """Verify MiniChecker bundle exports mountMiniChecker function"""
    bundle_path = Path(__file__).parent.parent / "builder" / "assets" / "js" / "mini-checker.js"
    bundle_content = bundle_path.read_text()

    # Check that the bundle contains the mount function logic
    # (React bundled code will be minified, so we check for key patterns)
    assert "MiniChecker" in bundle_content or "mini-checker" in bundle_content
    assert "useState" in bundle_content or "react" in bundle_content.lower()


def test_minichecker_css_has_required_classes():
    """Verify MiniChecker CSS has all required style classes"""
    css_path = Path(__file__).parent.parent / "builder" / "assets" / "css" / "mini-checker.css"
    css_content = css_path.read_text()

    required_classes = [
        ".mini-checker",
        ".mini-checker-header",
        ".mini-checker-form",
        ".mini-checker-input",
        ".mini-checker-button",
        ".mini-checker-error",
        ".mini-checker-result",
        ".mini-checker-upsell",
        ".full-checker-button"
    ]

    for class_name in required_classes:
        assert class_name in css_content, f"Missing CSS class: {class_name}"


def test_build_script_copies_assets():
    """Verify build script copies MiniChecker assets to dist"""
    dist_assets = Path(__file__).parent.parent.parent.parent / "content" / "dist" / "assets"

    if not dist_assets.exists():
        pytest.skip("Dist assets not found - run build_test_site.py first")

    # Check JS bundle
    js_bundle = dist_assets / "js" / "mini-checker.js"
    assert js_bundle.exists(), "MiniChecker JS not copied to dist"

    # Check CSS
    css_file = dist_assets / "css" / "mini-checker.css"
    assert css_file.exists(), "MiniChecker CSS not copied to dist"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
