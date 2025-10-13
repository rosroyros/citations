"""Tests for LLM review agent."""

import pytest
from backend.pseo.review.llm_reviewer import LLMReviewer


@pytest.fixture
def reviewer():
    """Create reviewer instance."""
    return LLMReviewer()


@pytest.fixture
def good_mega_guide():
    """Sample good mega guide content."""
    return {
        "content": """# Complete Guide to Checking APA Citations

## Introduction
This comprehensive guide helps you validate APA 7th edition citations...

## What Are APA Citations
APA citations follow specific formatting rules established by the American Psychological Association...

## How to Check Citations Step-by-Step
Follow these steps to validate your citations...

## Examples
Here are properly formatted citations:
- Smith, J. (2020). Article title. *Journal Name*, 15(2), 123-145. https://doi.org/10.1234/example

## Common Errors
The most frequent mistakes include:
1. Incorrect capitalization
2. Missing italics

## Validation Checklist
- [ ] Author names formatted correctly
- [ ] Date in parentheses
- [ ] Title in sentence case

## APA 6 vs 7 Changes
| Element | APA 6 | APA 7 |
|---------|-------|-------|
| DOI     | doi:  | https://doi.org/ |

## Frequently Asked Questions

**Q: How do I format author names?**
A: Use Last, F. M. format...

**Q: When do I use italics?**
A: Italicize journal names and book titles...

## Related Resources
- [How to Cite a Journal Article](/how-to-cite-journal-article-apa/)
- [How to Cite a Book](/how-to-cite-book-apa/)
- [APA Citation Errors Guide](/guide/apa-citation-errors/)

## Conclusion
By following these guidelines, you can ensure your citations are properly formatted...
""",
        "metadata": {
            "meta_title": "Complete Guide to Checking APA Citations - Validator",
            "meta_description": "Learn how to check APA 7th edition citations for formatting errors. Step-by-step guide with examples, common mistakes, and validation checklist.",
            "word_count": 5234,
            "reading_time": "26 minutes",
            "last_updated": "2024-10-13",
            "keywords": ["check APA citations", "APA validation", "citation errors"]
        },
        "page_type": "mega_guide"
    }


@pytest.fixture
def good_source_type():
    """Sample good source type page."""
    return {
        "content": """# How to Cite a Journal Article in APA

## Quick Reference
Author, A. A., & Author, B. B. (Year). Title of article. *Journal Name*, volume(issue), pages. https://doi.org/xxx

## Basic Format
Journal articles are one of the most common source types in academic writing...

## Required vs Optional Elements
**Required:**
- Author(s)
- Publication year
- Article title
- Journal name
- Volume number

## Examples
Here are 5 variations of journal article citations:

1. Single author: Smith, J. (2020). Article title. *Journal*, 15(2), 123-145.
2. Two authors: Smith, J., & Jones, A. (2020). Title. *Journal*, 15(2), 123-145.

## In-Text Citation Guidelines
When citing in text, use (Author, Year) format...

## Step-by-Step Instructions
1. Start with author's last name
2. Add first initial
3. Include year in parentheses

## Common Errors
1. Forgetting italics on journal name
2. Using title case instead of sentence case

## Validation Checklist
- [ ] Author names correct
- [ ] Year in parentheses
- [ ] Journal name italicized

## Special Cases
When citing advance online publications...

## Related Sources
- [How to Cite a Book](/how-to-cite-book-apa/)
- [How to Cite a Website](/how-to-cite-website-apa/)
""",
        "metadata": {
            "meta_title": "How to Cite a Journal Article in APA 7th Edition",
            "meta_description": "Complete guide to citing journal articles in APA format. Includes examples, step-by-step instructions, and common mistakes to avoid.",
            "word_count": 2456,
            "reading_time": "12 minutes",
            "last_updated": "2024-10-13"
        },
        "page_type": "source_type"
    }


@pytest.fixture
def bad_content_short():
    """Content that's too short."""
    return {
        "content": """# Title

## Introduction
This is too short.
""",
        "metadata": {
            "meta_title": "Title",
            "meta_description": "Description",
            "word_count": 50
        },
        "page_type": "mega_guide"
    }


@pytest.fixture
def bad_content_missing_sections():
    """Content missing required sections."""
    return {
        "content": """# How to Cite

## Introduction
Long content that meets word count requirements but is missing key sections like examples, common errors, validation checklist, and FAQ sections that are required for a complete guide.

""" + ("More content here. " * 500),  # Pad to meet word count
        "metadata": {
            "meta_title": "How to Cite",
            "meta_description": "A guide",
            "word_count": 2500
        },
        "page_type": "source_type"
    }


@pytest.fixture
def bad_content_template_vars():
    """Content with unrendered template variables."""
    return {
        "content": """# Guide

## Introduction
{{ introduction }}

## Examples
{{ examples }}

""" + ("Content here. " * 1000),
        "metadata": {
            "meta_title": "Guide",
            "meta_description": "Description",
            "word_count": 5000
        },
        "page_type": "mega_guide"
    }


@pytest.fixture
def bad_metadata():
    """Content with bad metadata."""
    return {
        "content": """# Guide

## Introduction
Complete content with all sections present and sufficient word count to pass structural checks.

## Examples
Example content here.

## Common Errors
Error content here.

## Validation Checklist
Checklist here.

## Frequently Asked Questions
FAQ here.

""" + ("More content. " * 1000),
        "metadata": {
            "meta_title": "X",  # Too short
            "meta_description": "Short",  # Too short
            "word_count": 5200
        },
        "page_type": "mega_guide"
    }


def test_review_good_mega_guide(reviewer, good_mega_guide):
    """Test that good mega guide passes review."""
    result = reviewer.review_page(
        good_mega_guide["content"],
        good_mega_guide["page_type"],
        good_mega_guide["metadata"]
    )

    # Debug output
    if result["overall_verdict"] != "PASS":
        print(f"\nVerdict: {result['overall_verdict']}")
        print(f"Word count: {result['word_count']}")
        print(f"Issues found: {len(result['issues_found'])}")
        for issue in result["issues_found"]:
            print(f"  [{issue['severity']}] {issue['issue']}")

    assert result["overall_verdict"] == "PASS"
    assert result["word_count"] >= 5000
    # Should have low/no high-severity issues
    high_issues = [i for i in result["issues_found"] if i["severity"] == "high"]
    assert len(high_issues) == 0


def test_review_good_source_type(reviewer, good_source_type):
    """Test that good source type page passes review."""
    result = reviewer.review_page(
        good_source_type["content"],
        good_source_type["page_type"],
        good_source_type["metadata"]
    )

    assert result["overall_verdict"] == "PASS"
    assert result["word_count"] >= 2000
    high_issues = [i for i in result["issues_found"] if i["severity"] == "high"]
    assert len(high_issues) == 0


def test_review_short_content(reviewer, bad_content_short):
    """Test that short content fails review."""
    result = reviewer.review_page(
        bad_content_short["content"],
        bad_content_short["page_type"],
        bad_content_short["metadata"]
    )

    assert result["overall_verdict"] == "NEEDS_REVISION"
    assert len(result["issues_found"]) > 0
    # Should flag word count
    word_count_issues = [i for i in result["issues_found"]
                        if "word" in i["issue"].lower()]
    assert len(word_count_issues) > 0


def test_review_missing_sections(reviewer, bad_content_missing_sections):
    """Test that content missing required sections fails."""
    result = reviewer.review_page(
        bad_content_missing_sections["content"],
        bad_content_missing_sections["page_type"],
        bad_content_missing_sections["metadata"]
    )

    assert result["overall_verdict"] == "NEEDS_REVISION"
    # Should flag missing sections
    section_issues = [i for i in result["issues_found"]
                     if "section" in i["issue"].lower()]
    assert len(section_issues) > 0


def test_review_template_variables(reviewer, bad_content_template_vars):
    """Test that unrendered template variables are flagged."""
    result = reviewer.review_page(
        bad_content_template_vars["content"],
        bad_content_template_vars["page_type"],
        bad_content_template_vars["metadata"]
    )

    assert result["overall_verdict"] == "NEEDS_REVISION"
    # Should flag template variables
    template_issues = [i for i in result["issues_found"]
                      if "template" in i["issue"].lower()]
    assert len(template_issues) > 0


def test_review_bad_metadata(reviewer, bad_metadata):
    """Test that bad metadata is flagged."""
    result = reviewer.review_page(
        bad_metadata["content"],
        bad_metadata["page_type"],
        bad_metadata["metadata"]
    )

    # Should flag metadata issues
    meta_issues = [i for i in result["issues_found"]
                  if "meta" in i["issue"].lower() or "title" in i["issue"].lower()
                  or "description" in i["issue"].lower()]
    assert len(meta_issues) > 0


def test_review_returns_all_fields(reviewer, good_mega_guide):
    """Test that review returns all expected fields."""
    result = reviewer.review_page(
        good_mega_guide["content"],
        good_mega_guide["page_type"],
        good_mega_guide["metadata"]
    )

    assert "overall_verdict" in result
    assert "issues_found" in result
    assert "word_count" in result
    assert "uniqueness_score" in result
    assert "review_summary" in result

    assert isinstance(result["issues_found"], list)
    assert isinstance(result["word_count"], int)
    assert isinstance(result["uniqueness_score"], float)


def test_issue_structure(reviewer, bad_content_short):
    """Test that issues have correct structure."""
    result = reviewer.review_page(
        bad_content_short["content"],
        bad_content_short["page_type"],
        bad_content_short["metadata"]
    )

    if len(result["issues_found"]) > 0:
        issue = result["issues_found"][0]
        assert "severity" in issue
        assert "issue" in issue
        assert "location" in issue
        assert "suggestion" in issue
        assert issue["severity"] in ["high", "medium", "low"]


def test_heading_hierarchy(reviewer):
    """Test heading hierarchy validation."""
    content = """# Title

#### Skipped to H4

## Normal H2
"""
    result = reviewer.review_page(content, "mega_guide", {"meta_title": "Test", "meta_description": "Test" * 20})

    # Should flag heading skip
    heading_issues = [i for i in result["issues_found"]
                     if "heading" in i["issue"].lower()]
    assert len(heading_issues) > 0


def test_multiple_h1s(reviewer):
    """Test multiple H1 detection."""
    content = """# First H1

## Content

# Second H1

## More content
""" + ("Content. " * 1000)

    result = reviewer.review_page(content, "mega_guide", {"meta_title": "Test", "meta_description": "Test" * 20})

    # Should flag multiple H1s
    h1_issues = [i for i in result["issues_found"]
                if "h1" in i["issue"].lower() or "heading" in i["issue"].lower()]
    assert len(h1_issues) > 0


def test_internal_links_check(reviewer):
    """Test internal links validation."""
    content_few_links = """# Guide

## Introduction
Content here.

[Link 1](/page1/)

""" + ("More content. " * 1000)

    result = reviewer.review_page(
        content_few_links,
        "mega_guide",
        {"meta_title": "Test Guide Title Here", "meta_description": "A" * 130}
    )

    # Should suggest more internal links (low severity)
    link_issues = [i for i in result["issues_found"]
                  if "link" in i["issue"].lower()]
    assert len(link_issues) > 0
