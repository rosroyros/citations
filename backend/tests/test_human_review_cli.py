#!/usr/bin/env python3
"""
Tests for Human Review CLI
Test-driven development approach - tests written before implementation
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
import sys
from datetime import datetime

# Add the backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "pseo"))

# Import the module directly to avoid dependency issues
import importlib.util
spec = importlib.util.spec_from_file_location(
    "human_review_cli",
    Path(__file__).parent.parent / "pseo" / "review" / "human_review_cli.py"
)
human_review_cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(human_review_cli)

HumanReviewCLI = human_review_cli.HumanReviewCLI


class TestHumanReviewCLI:
    """Test suite for Human Review CLI"""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing"""
        temp_dir = Path(tempfile.mkdtemp())
        review_dir = temp_dir / "content" / "review_queue"
        approved_dir = temp_dir / "content" / "approved"
        rejected_dir = temp_dir / "content" / "rejected"

        # Create directories
        for dir_path in [review_dir, approved_dir, rejected_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        yield temp_dir, review_dir, approved_dir, rejected_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_review_data(self):
        """Sample review data for testing"""
        return {
            "title": "How to Cite a Journal Article in APA",
            "url": "/how-to-cite-journal-article-apa/",
            "page_type": "source_type",
            "content": "# How to Cite a Journal Article in APA\n\nThis guide explains...",
            "metadata": {
                "meta_title": "How to Cite a Journal Article in APA | Complete Guide",
                "meta_description": "Learn how to properly cite journal articles in APA 7th edition format with examples",
                "word_count": 2500,
                "reading_time": "10 minutes"
            },
            "llm_review": {
                "overall_verdict": "PASS",
                "review_summary": "Content passes quality checks",
                "issues_found": [
                    {
                        "severity": "low",
                        "issue": "Only 7 internal links found (ideal: 8-15)",
                        "location": "Internal linking",
                        "suggestion": "Add more internal links to related pages"
                    }
                ]
            },
            "word_count": 2500
        }

    @pytest.fixture
    def cli_with_temp_dirs(self, temp_dirs):
        """Create CLI instance with temporary directories"""
        temp_dir, review_dir, approved_dir, rejected_dir = temp_dirs
        return HumanReviewCLI(str(review_dir))

    def test_cli_initialization(self, temp_dirs):
        """Test CLI initializes directories correctly"""
        temp_dir, review_dir, approved_dir, rejected_dir = temp_dirs

        cli = HumanReviewCLI(str(review_dir))

        assert cli.review_dir == review_dir
        assert cli.approved_dir.exists()
        assert cli.rejected_dir.exists()

    def test_get_pending_pages_empty(self, cli_with_temp_dirs):
        """Test getting pending pages when none exist"""
        pages = cli_with_temp_dirs._get_pending_pages()
        assert pages == []

    def test_get_pending_pages_with_data(self, cli_with_temp_dirs, sample_review_data):
        """Test getting pending pages with sample data"""
        # Create test file
        test_file = cli_with_temp_dirs.review_dir / "test_page.json"
        test_file.write_text(json.dumps(sample_review_data, indent=2))

        pages = cli_with_temp_dirs._get_pending_pages()

        assert len(pages) == 1
        assert pages[0]["title"] == "How to Cite a Journal Article in APA"
        assert pages[0]["type"] == "source_type"
        assert pages[0]["word_count"] == 2500
        assert pages[0]["llm_verdict"] == "PASS"
        assert pages[0]["issues_count"] == 1

    def test_get_pending_pages_ignores_invalid_json(self, cli_with_temp_dirs):
        """Test that invalid JSON files are ignored"""
        # Create invalid JSON file
        invalid_file = cli_with_temp_dirs.review_dir / "invalid.json"
        invalid_file.write_text("{ invalid json")

        # Create valid file
        valid_file = cli_with_temp_dirs.review_dir / "valid.json"
        valid_file.write_text(json.dumps({"title": "Valid Page"}))

        pages = cli_with_temp_dirs._get_pending_pages()

        # Should only return the valid page
        assert len(pages) == 1
        assert pages[0]["title"] == "Valid Page"

    def test_show_menu_displays_pages(self, cli_with_temp_dirs, sample_review_data, capsys):
        """Test menu display shows pending pages correctly"""
        # Create test files
        test_file1 = cli_with_temp_dirs.review_dir / "page1.json"
        test_file1.write_text(json.dumps(sample_review_data, indent=2))

        # Create second page with different data
        page2_data = sample_review_data.copy()
        page2_data["title"] = "APA Citation Errors Guide"
        page2_data["llm_review"]["overall_verdict"] = "NEEDS_REVISION"
        page2_data["llm_review"]["issues_found"] = [
            {"severity": "high", "issue": "Content too short"}
        ]

        test_file2 = cli_with_temp_dirs.review_dir / "page2.json"
        test_file2.write_text(json.dumps(page2_data, indent=2))

        cli_with_temp_dirs._show_menu(cli_with_temp_dirs._get_pending_pages())

        captured = capsys.readouterr()
        assert "Pages Pending Review (2 pages)" in captured.out
        assert "How to Cite a Journal Article in APA" in captured.out
        assert "APA Citation Errors Guide" in captured.out
        assert "✓ LLM: PASS" in captured.out
        assert "⚠ LLM: NEEDS_REVISION" in captured.out

    def test_approve_page_moves_file(self, cli_with_temp_dirs, sample_review_data):
        """Test approving a page moves it to approved directory"""
        # Create test file
        test_file = cli_with_temp_dirs.review_dir / "test_page.json"
        test_file.write_text(json.dumps(sample_review_data, indent=2))

        # Approve the page
        cli_with_temp_dirs._approve_page(test_file, sample_review_data)

        # File should be moved
        assert not test_file.exists()

        approved_file = cli_with_temp_dirs.approved_dir / "test_page.json"
        assert approved_file.exists()

        # Check approval metadata was added
        approved_data = json.loads(approved_file.read_text())
        assert "human_review" in approved_data
        assert approved_data["human_review"]["approved"] == True
        assert "approved_date" in approved_data["human_review"]
        assert approved_data["human_review"]["approved_by"] == "human_review"

    def test_reject_page_moves_file(self, cli_with_temp_dirs, sample_review_data):
        """Test rejecting a page moves it to rejected directory"""
        # Create test file
        test_file = cli_with_temp_dirs.review_dir / "test_page.json"
        test_file.write_text(json.dumps(sample_review_data, indent=2))

        # Mock input for rejection reason
        with patch('builtins.input', return_value='Content too short'):
            cli_with_temp_dirs._reject_page(test_file, sample_review_data)

        # File should be moved
        assert not test_file.exists()

        rejected_file = cli_with_temp_dirs.rejected_dir / "test_page.json"
        assert rejected_file.exists()

        # Check rejection metadata was added
        rejected_data = json.loads(rejected_file.read_text())
        assert "human_review" in rejected_data
        assert rejected_data["human_review"]["approved"] == False
        assert rejected_data["human_review"]["reason"] == "Content too short"
        assert "rejected_date" in rejected_data["human_review"]

    def test_view_full_content_shows_truncated(self, cli_with_temp_dirs, sample_review_data, capsys):
        """Test viewing full content shows truncated version"""
        # Create long content
        long_content = "# Test\n" + "This is test content. " * 200  # Make it long
        sample_review_data["content"] = long_content

        # Mock input to not show more
        with patch('builtins.input', return_value=''):
            cli_with_temp_dirs._view_full_content(long_content)

        captured = capsys.readouterr()
        assert "This is test content" in captured.out
        assert "more characters" in captured.out

    def test_view_llm_review_shows_details(self, cli_with_temp_dirs, sample_review_data, capsys):
        """Test viewing LLM review shows detailed information"""
        with patch('builtins.input', return_value=''):
            cli_with_temp_dirs._view_llm_review(sample_review_data["llm_review"])

        captured = capsys.readouterr()
        assert "LLM REVIEW DETAILS" in captured.out
        assert "Overall: PASS" in captured.out
        assert "Content passes quality checks" in captured.out
        assert "ONLY 7 INTERNAL LINKS FOUND" in captured.out

    def test_integration_complete_review_flow(self, cli_with_temp_dirs, sample_review_data):
        """Test complete review flow from pending to approved"""
        # Create test file
        test_file = cli_with_temp_dirs.review_dir / "test_page.json"
        test_file.write_text(json.dumps(sample_review_data, indent=2))

        # Simulate complete review workflow
        pages = cli_with_temp_dirs._get_pending_pages()
        assert len(pages) == 1

        # View page overview
        page_data = json.loads(test_file.read_text())

        # Approve the page
        cli_with_temp_dirs._approve_page(test_file, page_data)

        # Verify file moved to approved
        assert not test_file.exists()
        approved_file = cli_with_temp_dirs.approved_dir / "test_page.json"
        assert approved_file.exists()

        # Verify no pending pages remain
        remaining_pages = cli_with_temp_dirs._get_pending_pages()
        assert len(remaining_pages) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])