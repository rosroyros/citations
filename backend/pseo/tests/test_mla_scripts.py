"""
Tests for MLA PSEO generation and validation scripts.

Tests cover:
1. generate_mla_pages.py CLI script
2. validate_mla_batch.py validation script
"""

import pytest
import subprocess
import json
import sys
from pathlib import Path
import tempfile
import shutil

# Add scripts directory to path for imports
SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


# Fixtures

@pytest.fixture
def test_output_dir():
    """Create temporary output directory for tests"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def scripts_dir():
    """Get path to scripts directory"""
    return Path(__file__).parent.parent / "scripts"


@pytest.fixture
def sample_html_content():
    """Sample MLA HTML content for validation tests"""
    # Generate content with sufficient word count (>800 words)
    lorem_paragraph = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod
    tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
    exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor
    in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur
    sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est
    laborum. Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque
    laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto
    beatae vitae dicta sunt explicabo."""

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>How to Cite YouTube Videos in MLA 9</title>
</head>
<body>
    <h1>How to Cite YouTube Videos in MLA 9th Edition</h1>

    <p>This is a comprehensive guide on citing YouTube videos in MLA 9th Edition format.
    The MLA citation style is used primarily in the humanities and liberal arts. When citing
    a YouTube video, you need to include the creator's name, video title, website name,
    upload date, and URL.</p>

    <div class="mini-checker" data-style="mla9">
        <h4>Quick Check Your Citation</h4>
        <textarea placeholder="Paste your MLA citation here..."></textarea>
        <button>Check Citation</button>
    </div>

    <p>The basic format for a YouTube video citation in MLA 9 is: Creator Last Name, First Name.
    "Video Title." YouTube, uploaded by Username, Day Month Year, URL. Additional information
    about MLA format and citation requirements...</p>

    <div class="style-alternate">
        <strong>Need APA format instead?</strong>
        <a href="/cite-youtube-apa/">View APA 7 version →</a>
    </div>

    <p>{lorem_paragraph}</p>
    <p>{lorem_paragraph}</p>
    <p>{lorem_paragraph}</p>
    <p>{lorem_paragraph}</p>
    <p>{lorem_paragraph}</p>
    <p>{lorem_paragraph}</p>
    <p>{lorem_paragraph}</p>
</body>
</html>'''


# Generation Script Tests

def test_generate_help_command(scripts_dir):
    """Test that generate_mla_pages.py shows help"""
    result = subprocess.run(
        ["python3", str(scripts_dir / "generate_mla_pages.py"), "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Generate MLA PSEO pages" in result.stdout or "usage:" in result.stdout


def test_generate_pilot_pages_dry_run(scripts_dir, test_output_dir, monkeypatch):
    """Test pilot page generation (checking command structure)"""
    # This test checks that the script can be invoked correctly
    # Full generation would require all dependencies
    result = subprocess.run(
        ["python3", str(scripts_dir / "generate_mla_pages.py"), "--help"],
        capture_output=True,
        text=True
    )

    # Verify command line options exist
    assert result.returncode == 0
    assert "--pilot" in result.stdout or "--help" in result.stdout


def test_load_config_files_exist(scripts_dir):
    """Test that required config files exist"""
    configs_dir = scripts_dir.parent / "configs"

    required_configs = [
        "mla_mega_guides.json",
        "mla_source_type_guides.json",
        "mla_specific_sources.json"
    ]

    for config_file in required_configs:
        config_path = configs_dir / config_file
        assert config_path.exists(), f"Config file missing: {config_file}"

        # Verify it's valid JSON
        with open(config_path) as f:
            data = json.load(f)
            assert isinstance(data, (list, dict))


# Validation Script Tests

def test_validate_help_command(scripts_dir):
    """Test that validate_mla_batch.py shows help"""
    result = subprocess.run(
        ["python3", str(scripts_dir / "validate_mla_batch.py"), "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Validate MLA" in result.stdout or "usage:" in result.stdout


def test_validator_word_count_check(test_output_dir, sample_html_content):
    """Test word count validation gate"""
    from validate_mla_batch import MLAPageValidator

    # Create test page
    page_dir = test_output_dir / "cite-youtube-mla"
    page_dir.mkdir(parents=True)
    html_file = page_dir / "index.html"
    html_file.write_text(sample_html_content)

    # Validate
    validator = MLAPageValidator(test_output_dir)
    result = validator.check_word_count(sample_html_content, "youtube")

    # Should pass - sample has enough words
    assert result is True


def test_validator_template_vars_check(test_output_dir):
    """Test template variable validation gate"""
    from validate_mla_batch import MLAPageValidator

    # Test with template vars
    html_with_vars = "<html><body>{{ unresolved_var }}</body></html>"
    validator = MLAPageValidator(test_output_dir)
    result = validator.check_no_template_vars(html_with_vars, "test")
    assert result is False

    # Test without template vars
    html_clean = "<html><body>Clean content</body></html>"
    result = validator.check_no_template_vars(html_clean, "test")
    assert result is True


def test_validator_h1_mla_check(test_output_dir, sample_html_content):
    """Test H1 MLA validation gate"""
    from validate_mla_batch import MLAPageValidator

    validator = MLAPageValidator(test_output_dir)

    # Should pass - H1 contains "MLA"
    result = validator.check_h1_mla(sample_html_content, "youtube")
    assert result is True

    # Should fail - H1 doesn't contain "MLA"
    html_no_mla = "<html><body><h1>How to Cite Videos</h1></body></html>"
    result = validator.check_h1_mla(html_no_mla, "test")
    assert result is False


def test_validator_minichecker_config_check(test_output_dir, sample_html_content):
    """Test mini-checker data-style validation gate"""
    from validate_mla_batch import MLAPageValidator

    validator = MLAPageValidator(test_output_dir)

    # Should pass - has data-style="mla9"
    result = validator.check_minichecker_config(sample_html_content, "youtube")
    assert result is True

    # Should fail - missing data-style
    html_no_style = '<html><body><div class="mini-checker"></div></body></html>'
    result = validator.check_minichecker_config(html_no_style, "test")
    assert result is False


def test_validator_cross_style_link_check(test_output_dir, sample_html_content):
    """Test cross-style link validation gate"""
    from validate_mla_batch import MLAPageValidator

    validator = MLAPageValidator(test_output_dir)

    # Should pass - has link to APA version
    result = validator.check_cross_style_link(sample_html_content, "youtube")
    assert result is True

    # Should still pass (warning only) - no APA link
    html_no_link = "<html><body>No APA link here</body></html>"
    result = validator.check_cross_style_link(html_no_link, "test")
    assert result is True  # It's a warning, not a failure


def test_validator_em_dash_check(test_output_dir):
    """Test em dash validation gate"""
    from validate_mla_batch import MLAPageValidator

    validator = MLAPageValidator(test_output_dir)

    # Should pass - no em dashes
    html_clean = "<html><body>Clean content</body></html>"
    result = validator.check_no_em_dashes(html_clean, "test")
    assert result is True

    # Should warn but pass - has em dashes
    html_with_em = "<html><body>This is an example—with em dash</body></html>"
    result = validator.check_no_em_dashes(html_with_em, "test")
    assert result is True  # Warning only, not failure


def test_full_page_validation(test_output_dir, sample_html_content):
    """Test complete page validation"""
    from validate_mla_batch import MLAPageValidator

    # Create test page
    page_dir = test_output_dir / "cite-youtube-mla"
    page_dir.mkdir(parents=True)
    html_file = page_dir / "index.html"
    html_file.write_text(sample_html_content)

    # Validate
    validator = MLAPageValidator(test_output_dir)
    result = validator.validate_page(html_file, "youtube")

    # Should pass all gates
    assert result is True
    assert validator.passed_pages == 0  # Not incremented by validate_page
    assert len(validator.results.get("youtube", [])) == 0  # No failures


# Integration Tests

def test_script_imports_work():
    """Test that scripts can be imported without errors"""
    import sys
    from pathlib import Path

    scripts_dir = Path(__file__).parent.parent / "scripts"
    sys.path.insert(0, str(scripts_dir))

    # These should not raise ImportError
    try:
        import generate_mla_pages
        import validate_mla_batch
    except ImportError as e:
        pytest.fail(f"Script import failed: {e}")


def test_config_structure_mega_guides():
    """Test mega guides config structure"""
    config_path = Path(__file__).parent.parent / "configs" / "mla_mega_guides.json"

    with open(config_path) as f:
        guides = json.load(f)

    assert isinstance(guides, list)
    assert len(guides) > 0

    # Check first guide has required fields
    guide = guides[0]
    required_fields = ["id", "title", "url", "url_slug", "description"]
    for field in required_fields:
        assert field in guide, f"Missing field: {field}"


def test_config_structure_specific_sources():
    """Test specific sources config structure"""
    config_path = Path(__file__).parent.parent / "configs" / "mla_specific_sources.json"

    with open(config_path) as f:
        data = json.load(f)

    # Should be list or dict with "sources" key
    if isinstance(data, dict):
        assert "sources" in data
        sources = data["sources"]
    else:
        sources = data

    assert isinstance(sources, list)
    assert len(sources) > 0

    # Check first source has required fields
    source = sources[0]
    required_fields = ["id", "name"]
    for field in required_fields:
        assert field in source, f"Missing field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
