"""Tests for the styles module."""
import pytest
from styles import (
    SUPPORTED_STYLES,
    StyleType,
    DEFAULT_STYLE,
    is_valid_style,
    get_style_config,
)


class TestSupportedStylesStructure:
    """Test the SUPPORTED_STYLES dictionary structure."""

    def test_supported_styles_has_expected_keys(self):
        """Verify SUPPORTED_STYLES contains expected style keys."""
        assert "apa7" in SUPPORTED_STYLES
        assert "mla9" in SUPPORTED_STYLES
        assert "chicago17" in SUPPORTED_STYLES

    def test_each_style_has_required_fields(self):
        """Verify each style config has label, prompt_file, and success_message."""
        required_fields = {"label", "prompt_file", "success_message"}
        for style_key, config in SUPPORTED_STYLES.items():
            for field in required_fields:
                assert field in config, f"Style '{style_key}' missing field '{field}'"

    def test_prompt_files_have_txt_extension(self):
        """Verify all prompt files end with .txt."""
        for style_key, config in SUPPORTED_STYLES.items():
            assert config["prompt_file"].endswith(".txt"), (
                f"Style '{style_key}' prompt_file should end with .txt"
            )


class TestIsValidStyle:
    """Test the is_valid_style function."""

    def test_valid_style_apa7(self):
        """APA7 should be a valid style."""
        assert is_valid_style("apa7") is True

    def test_valid_style_mla9(self):
        """MLA9 should be a valid style."""
        assert is_valid_style("mla9") is True

    def test_valid_style_chicago17(self):
        """Chicago17 should be a valid style."""
        assert is_valid_style("chicago17") is True

    def test_invalid_style_empty_string(self):
        """Empty string should be invalid."""
        assert is_valid_style("") is False

    def test_invalid_style_unknown(self):
        """Unknown style should be invalid."""
        assert is_valid_style("chicago") is False

    def test_invalid_style_case_sensitive(self):
        """Style validation should be case-sensitive."""
        assert is_valid_style("APA7") is False
        assert is_valid_style("MLA9") is False


class TestGetStyleConfig:
    """Test the get_style_config function."""

    def test_get_apa7_config(self):
        """Get APA7 config should return correct values."""
        config = get_style_config("apa7")
        assert config["label"] == "APA 7th Edition"
        assert config["prompt_file"] == "validator_prompt_v3_no_hallucination.txt"
        assert config["success_message"] == "No APA 7 formatting errors detected"

    def test_get_mla9_config(self):
        """Get MLA9 config should return correct values."""
        config = get_style_config("mla9")
        assert config["label"] == "MLA 9th Edition"
        assert config["prompt_file"] == "validator_prompt_mla9_v1.1.txt"
        assert config["success_message"] == "No MLA 9 formatting errors detected"

    def test_get_chicago17_config(self):
        """Get Chicago17 config should return correct values."""
        config = get_style_config("chicago17")
        assert config["label"] == "Chicago 17th Edition"
        assert config["prompt_file"] == "validator_prompt_chicago17_v1.2.txt"
        assert config["success_message"] == "No Chicago 17 formatting errors detected"


class TestDefaultStyle:
    """Test the DEFAULT_STYLE constant."""

    def test_default_style_is_valid(self):
        """DEFAULT_STYLE should be a valid style in SUPPORTED_STYLES."""
        assert DEFAULT_STYLE in SUPPORTED_STYLES

    def test_default_style_is_apa7(self):
        """DEFAULT_STYLE should be apa7 for backward compatibility."""
        assert DEFAULT_STYLE == "apa7"
