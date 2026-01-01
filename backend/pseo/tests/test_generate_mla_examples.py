#!/usr/bin/env python3
"""
Tests for MLA 9 example generator.

Tests verify that generated examples follow MLA 9th Edition rules:
- Full author names (not initials)
- "and" between two authors (not "&")
- Title Case for all titles
- Date after publisher
- "pp." for page ranges
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_mla_examples import (
    generate_authors,
    format_authors_for_mla,
    generate_book_example,
    generate_journal_article_example,
    generate_website_example,
    generate_book_chapter_example,
    generate_title
)


class TestAuthorGeneration:
    """Test author name generation."""

    def test_generate_single_author(self):
        """Single author should have full name components."""
        authors = generate_authors(1)
        assert len(authors) == 1
        assert 'first_name' in authors[0]
        assert 'last_name' in authors[0]
        assert 'full_name' in authors[0]
        # Verify full names, not initials
        assert len(authors[0]['first_name']) > 1

    def test_generate_multiple_authors(self):
        """Multiple authors should be unique."""
        authors = generate_authors(3)
        assert len(authors) == 3
        # Check uniqueness
        full_names = [a['full_name'] for a in authors]
        assert len(full_names) == len(set(full_names))


class TestAuthorFormatting:
    """Test MLA 9 author formatting rules."""

    def test_single_author_inverted(self):
        """Single author: Last, First."""
        authors = [{"last_name": "Morrison", "first_name": "Toni", "middle_name": ""}]
        formatted = format_authors_for_mla(authors)
        assert formatted == "Morrison, Toni"

    def test_single_author_with_middle(self):
        """Single author with middle name: Last, First Middle."""
        authors = [{"last_name": "Garcia", "first_name": "Maria", "middle_name": "Elena"}]
        formatted = format_authors_for_mla(authors)
        assert formatted == "Garcia, Maria Elena"

    def test_two_authors_uses_and(self):
        """Two authors: use 'and' not '&'."""
        authors = [
            {"last_name": "Garcia", "first_name": "Maria", "middle_name": ""},
            {"last_name": "Patel", "first_name": "Sanjay", "middle_name": ""}
        ]
        formatted = format_authors_for_mla(authors)
        assert ", and " in formatted
        assert "&" not in formatted

    def test_two_authors_second_not_inverted(self):
        """Two authors: second name NOT inverted."""
        authors = [
            {"last_name": "Garcia", "first_name": "Maria", "middle_name": ""},
            {"last_name": "Patel", "first_name": "Sanjay", "middle_name": ""}
        ]
        formatted = format_authors_for_mla(authors)
        # First author inverted
        assert formatted.startswith("Garcia, Maria")
        # Second author normal order
        assert "Sanjay Patel" in formatted
        assert "Patel, Sanjay" not in formatted

    def test_three_authors_uses_et_al(self):
        """Three or more authors: use 'et al.' after first."""
        authors = [
            {"last_name": "Nickels", "first_name": "William", "middle_name": ""},
            {"last_name": "Smith", "first_name": "John", "middle_name": ""},
            {"last_name": "Jones", "first_name": "Mary", "middle_name": ""}
        ]
        formatted = format_authors_for_mla(authors)
        assert formatted == "Nickels, William, et al."
        # Should NOT list other authors
        assert "Smith" not in formatted
        assert "Jones" not in formatted

    def test_et_al_no_double_period(self):
        """et al. should not create double periods."""
        authors = [
            {"last_name": "Robinson", "first_name": "Lisa", "middle_name": ""},
            {"last_name": "Smith", "first_name": "John", "middle_name": ""},
            {"last_name": "Doe", "first_name": "Jane", "middle_name": ""}
        ]
        formatted = format_authors_for_mla(authors)
        # Should end with "et al." not "et al.."
        assert formatted.endswith("et al.")
        assert not formatted.endswith("et al..")


class TestBookExamples:
    """Test book citation generation."""

    def test_book_has_required_components(self):
        """Book citation should have all required components."""
        example = generate_book_example(1)
        assert 'citation' in example
        assert 'components' in example
        assert 'authors' in example['components']
        assert 'title' in example['components']
        assert 'publisher' in example['components']
        assert 'year' in example['components']

    def test_book_title_italicized(self):
        """Book title should be italicized."""
        example = generate_book_example(1)
        citation = example['citation']
        # Check for italic markers (asterisks)
        assert "*" in citation

    def test_book_uses_full_names(self):
        """Book should use full author names, not initials."""
        example = generate_book_example(1)
        citation = example['citation']
        # Should NOT contain pattern like "Morrison, T."
        import re
        # Check for initials pattern (capital letter followed by period)
        assert not re.search(r',\s+[A-Z]\.', citation)

    def test_book_year_after_publisher(self):
        """In MLA, year comes AFTER publisher."""
        example = generate_book_example(1)
        citation = example['citation']
        # Pattern should be "Publisher, Year."
        import re
        assert re.search(r'[A-Za-z\s]+,\s+\d{4}\.', citation)

    def test_book_ends_with_period(self):
        """All citations must end with period."""
        example = generate_book_example(1)
        citation = example['citation']
        assert citation.endswith(".")


class TestJournalExamples:
    """Test journal article citation generation."""

    def test_journal_has_required_components(self):
        """Journal article should have all required components."""
        example = generate_journal_article_example(1)
        assert 'citation' in example
        assert 'article_title' in example['components']
        assert 'journal_name' in example['components']
        assert 'volume' in example['components']
        assert 'issue' in example['components']

    def test_article_title_in_quotes(self):
        """Article title should be in quotation marks."""
        example = generate_journal_article_example(1)
        citation = example['citation']
        # Should have quoted article title
        assert '"' in citation

    def test_journal_name_italicized(self):
        """Journal name should be italicized."""
        example = generate_journal_article_example(1)
        citation = example['citation']
        assert "*" in citation

    def test_volume_issue_lowercase(self):
        """Volume and issue abbreviations should be lowercase."""
        example = generate_journal_article_example(1)
        citation = example['citation']
        assert "vol." in citation
        assert "no." in citation
        # Should NOT be capitalized
        assert "Vol." not in citation
        assert "No." not in citation

    def test_pages_use_pp(self):
        """Page numbers should use 'pp.' prefix."""
        example = generate_journal_article_example(1)
        citation = example['citation']
        assert "pp." in citation or "p." in citation

    def test_no_apa_volume_format(self):
        """Should NOT use APA's volume(issue) format."""
        example = generate_journal_article_example(1)
        citation = example['citation']
        # Should not have pattern like "4(2)"
        import re
        assert not re.search(r'\d+\(\d+\)', citation)


class TestWebsiteExamples:
    """Test website citation generation."""

    def test_website_has_required_components(self):
        """Website citation should have required components."""
        example = generate_website_example(1)
        assert 'page_title' in example['components']
        assert 'website_name' in example['components']
        assert 'url' in example['components']

    def test_url_no_protocol(self):
        """URL should NOT include http:// or https:// (except DOI)."""
        example = generate_website_example(1)
        citation = example['citation']
        url = example['components']['url']

        # Regular URLs should not have protocol
        if not url.startswith("https://doi.org/"):
            assert not url.startswith("http://")
            assert not url.startswith("https://")

    def test_date_format_day_month_year(self):
        """Date should be in Day Month Year format."""
        example = generate_website_example(1)
        citation = example['citation']
        # Should have pattern like "5 Feb. 2024"
        import re
        # Check for day-month-year pattern
        assert re.search(r'\d{1,2}\s+[A-Z][a-z]+\.\s+\d{4}', citation)


class TestChapterExamples:
    """Test book chapter citation generation."""

    def test_chapter_has_required_components(self):
        """Chapter citation should have required components."""
        example = generate_book_chapter_example(1)
        assert 'chapter_title' in example['components']
        assert 'book_title' in example['components']
        assert 'editor' in example['components']
        assert 'pages' in example['components']

    def test_chapter_title_in_quotes(self):
        """Chapter title should be in quotation marks."""
        example = generate_book_chapter_example(1)
        citation = example['citation']
        assert '"' in citation

    def test_book_title_italicized(self):
        """Book title (container) should be italicized."""
        example = generate_book_chapter_example(1)
        citation = example['citation']
        assert "*" in citation

    def test_editor_not_inverted(self):
        """Editor name should be in normal order (First Last), not inverted."""
        example = generate_book_chapter_example(1)
        citation = example['citation']
        # Should have "edited by First Last"
        assert "edited by" in citation
        # Editor name should come after "edited by"
        editor_section = citation.split("edited by")[1].split(",")[0]
        # Normal order = First name comes first (starts with capital letter, not all caps)
        import re
        # Check it doesn't have inverted pattern like "Last, First" after "edited by"
        assert not re.search(r'edited by [A-Z][a-z]+,\s+[A-Z]', citation)

    def test_chapter_pages_use_pp(self):
        """Chapter pages should use 'pp.' prefix."""
        example = generate_book_chapter_example(1)
        citation = example['citation']
        assert "pp." in citation


class TestTitleCase:
    """Test Title Case generation."""

    def test_title_has_capitalized_words(self):
        """Title should have capitalized major words."""
        title = generate_title()
        # Should have multiple capital letters (Title Case)
        capitals = sum(1 for c in title if c.isupper())
        assert capitals >= 2  # At least 2 capital letters

    def test_title_not_all_caps(self):
        """Title should not be all caps."""
        title = generate_title()
        assert title != title.upper()

    def test_title_not_sentence_case(self):
        """Title should not be sentence case (first word only)."""
        title = generate_title()
        # If title has multiple words, should have more than one capital
        words = title.split()
        if len(words) > 1:
            capitals = sum(1 for word in words if word[0].isupper())
            assert capitals > 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
