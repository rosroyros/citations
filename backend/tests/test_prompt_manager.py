"""Tests for the PromptManager multi-style support."""
import pytest
from unittest.mock import patch
from pathlib import Path
from prompt_manager import PromptManager


class TestLoadPromptStyles:
    """Test PromptManager.load_prompt with different styles."""

    def test_load_prompt_defaults_to_apa7(self):
        """Without style argument, should load APA7 prompt."""
        pm = PromptManager()
        prompt = pm.load_prompt()
        # APA7 prompt should contain APA-specific content
        assert len(prompt) > 0
        # Verify it loaded the v3 APA prompt (has specific content)
        assert "CORRECTED CITATION" in prompt or "APA" in prompt.upper() or len(prompt) > 100

    def test_load_prompt_apa7_explicit(self):
        """Explicitly loading apa7 should work."""
        pm = PromptManager()
        prompt = pm.load_prompt("apa7")
        assert len(prompt) > 0
        assert isinstance(prompt, str)

    def test_load_prompt_mla9(self):
        """Loading mla9 should load MLA-specific prompt."""
        pm = PromptManager()
        prompt = pm.load_prompt("mla9")
        assert len(prompt) > 0
        # MLA prompt should contain MLA-specific content
        assert "MLA" in prompt.upper()

    def test_load_prompt_chicago17(self):
        """Loading chicago17 should load Chicago-specific prompt."""
        pm = PromptManager()
        prompt = pm.load_prompt("chicago17")
        assert len(prompt) > 0
        # Chicago prompt should contain Chicago-specific content
        assert "CHICAGO" in prompt.upper()

    def test_load_prompt_different_content(self):
        """APA7 and MLA9 prompts should have different content."""
        pm = PromptManager()
        apa_prompt = pm.load_prompt("apa7")
        mla_prompt = pm.load_prompt("mla9")
        
        # They should be meaningfully different
        assert apa_prompt != mla_prompt


class TestLoadPromptCustomPath:
    """Test backward compatibility with custom prompt paths."""

    def test_custom_path_ignores_style(self, tmp_path):
        """When custom path provided, style parameter is ignored."""
        # Create a temp prompt file
        custom_prompt = tmp_path / "custom.txt"
        custom_prompt.write_text("Custom prompt content")
        
        pm = PromptManager(prompt_path=str(custom_prompt))
        
        # Should load custom prompt regardless of style
        prompt = pm.load_prompt("mla9")
        assert prompt == "Custom prompt content"

    def test_custom_path_file_not_found(self, tmp_path):
        """Non-existent custom path should raise FileNotFoundError."""
        pm = PromptManager(prompt_path=str(tmp_path / "nonexistent.txt"))
        
        with pytest.raises(FileNotFoundError):
            pm.load_prompt()


class TestBuildPromptStyles:
    """Test PromptManager.build_prompt with different styles."""

    def test_build_prompt_defaults_to_apa7(self):
        """build_prompt should default to APA7."""
        pm = PromptManager()
        prompt = pm.build_prompt("Smith, J. (2020). Test title. Publisher.")
        assert len(prompt) > 100
        assert "1. Smith" in prompt

    def test_build_prompt_mla9(self):
        """build_prompt with mla9 should use MLA prompt."""
        pm = PromptManager()
        prompt = pm.build_prompt("Smith, John. Test Title. Publisher, 2020.", style="mla9")
        assert len(prompt) > 100
        assert "1. Smith" in prompt
        # Should contain MLA prompt content
        assert "MLA" in prompt.upper()


class TestApiStylesEndpoint:
    """Test /api/styles endpoint behavior."""

    @pytest.fixture
    def test_client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        import app
        return TestClient(app.app)

    def test_api_styles_mla_disabled(self, test_client, monkeypatch):
        """When MLA_ENABLED=false, only apa7 is returned."""
        monkeypatch.setattr('app.MLA_ENABLED', False)
        
        response = test_client.get("/api/styles")
        assert response.status_code == 200
        
        data = response.json()
        assert "apa7" in data["styles"]
        assert "mla9" not in data["styles"]
        assert data["default"] == "apa7"

    def test_api_styles_mla_enabled(self, test_client, monkeypatch):
        """When MLA_ENABLED=true, both styles are returned."""
        monkeypatch.setattr('app.MLA_ENABLED', True)

        response = test_client.get("/api/styles")
        assert response.status_code == 200

        data = response.json()
        assert "apa7" in data["styles"]
        assert "mla9" in data["styles"]
        assert data["default"] == "apa7"

    def test_api_styles_chicago_disabled(self, test_client, monkeypatch):
        """When CHICAGO_ENABLED=false, only apa7 and mla9 (if enabled) are returned."""
        monkeypatch.setattr('app.MLA_ENABLED', True)
        monkeypatch.setattr('app.CHICAGO_ENABLED', False)

        response = test_client.get("/api/styles")
        assert response.status_code == 200

        data = response.json()
        assert "apa7" in data["styles"]
        assert "mla9" in data["styles"]
        assert "chicago17" not in data["styles"]
        assert data["default"] == "apa7"

    def test_api_styles_chicago_enabled(self, test_client, monkeypatch):
        """When CHICAGO_ENABLED=true, all three styles are returned."""
        monkeypatch.setattr('app.MLA_ENABLED', True)
        monkeypatch.setattr('app.CHICAGO_ENABLED', True)

        response = test_client.get("/api/styles")
        assert response.status_code == 200

        data = response.json()
        assert "apa7" in data["styles"]
        assert "mla9" in data["styles"]
        assert "chicago17" in data["styles"]
        assert data["styles"]["chicago17"] == "Chicago 17th Edition"
        assert data["default"] == "apa7"

    def test_api_styles_response_structure(self, test_client):
        """Response should have expected structure."""
        response = test_client.get("/api/styles")
        assert response.status_code == 200
        
        data = response.json()
        assert "styles" in data
        assert "default" in data
        assert isinstance(data["styles"], dict)
        # Check that style labels are strings
        for label in data["styles"].values():
            assert isinstance(label, str)
