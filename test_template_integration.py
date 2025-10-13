#!/usr/bin/env python3
"""Integration test for template engine with existing templates."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from pseo.generator.template_engine import TemplateEngine
from pathlib import Path

def test_existing_templates():
    """Test template engine with existing mega guide and source type templates."""

    # Initialize template engine
    templates_dir = Path("backend/pseo/templates")
    engine = TemplateEngine(str(templates_dir))

    # Test mega guide template
    print("Testing mega guide template...")
    mega_template = engine.load_template("mega_guide_template.md")

    # Test data for mega guide
    mega_data = {
        "guide_title": "Test Mega Guide",
        "guide_description": "A comprehensive test guide",
        "target_keywords": ["test", "guide", "citation"],
        "tldr_bullets": ["Point 1", "Point 2", "Point 3"],
        "introduction": "This is the introduction to our comprehensive test guide.",
        "main_sections": [
            {"title": "Section 1", "content": "Content for section 1"},
            {"title": "Section 2", "content": "Content for section 2"}
        ],
        "examples": [{"citation": "Smith, J. (2020). Test article. Test Journal, 1(1), 1-10."}],
        "common_errors": [{"error": "Test error", "solution": "Test solution"}],
        "validation_checklist": ["Check 1", "Check 2"],
        "apa6_vs_7": {"change": "Test change", "impact": "Test impact"},
        "faq_questions": [
            {"question": "Test question 1", "answer": "Test answer 1"},
            {"question": "Test question 2", "answer": "Test answer 2"}
        ],
        "related_resources": [
            {"title": "Related Guide 1", "url": "/guide/test/"},
            {"title": "Related Guide 2", "url": "/guide/test2/"}
        ],
        "last_updated": "2024-01-01",
        "reading_time": "10 minutes",
        "cta_placements": ["Placement 1", "Placement 2", "Placement 3", "Placement 4", "Placement 5"]
    }

    # Render mega guide
    mega_content = engine.inject_variables(mega_template, mega_data)
    print(f"Mega guide content length: {len(mega_content)} chars")
    print(f"Mega guide word count: {len(mega_content.split())} words")

    # Validate mega guide content
    mega_valid = engine.validate_output(mega_content, min_words=5000)
    print(f"Mega guide validation (min 5000 words): {'PASS' if mega_valid else 'FAIL'}")

    # Save test output
    engine.save_markdown(mega_content, "content/test/test_mega_guide.md")
    print("Saved test mega guide to content/test/test_mega_guide.md")

    print("\n" + "="*50 + "\n")

    # Test source type template
    print("Testing source type template...")
    source_template = engine.load_template("source_type_template.md")

    # Test data for source type
    source_data = {
        "source_type_name": "Journal Article",
        "source_description": "A scholarly article published in a peer-reviewed journal",
        "quick_reference_template": "Author, A. A. (Year). Title of article. Journal Name, Volume(Issue), Pages.",
        "basic_format_explanation": "Journal articles follow a specific format in APA style.",
        "element_breakdown": {
            "author": "Author names with initials",
            "year": "Publication year in parentheses",
            "title": "Article title in sentence case",
            "journal": "Journal name in italics",
            "volume": "Volume number in italics",
            "issue": "Issue number in parentheses",
            "pages": "Page range"
        },
        "required_vs_optional": {
            "required": ["Author", "Year", "Title", "Journal", "Volume", "Pages"],
            "optional": ["DOI", "URL"]
        },
        "reference_examples": [
            "Smith, J. (2020). Article title. Journal Name, 15(2), 123-145.",
            "Doe, J. (2021). Another article. Different Journal, 10(1), 1-15."
        ],
        "in_text_guidelines": "Use author-date format: (Smith, 2020)",
        "step_by_step_instructions": [
            "Step 1: Identify the author",
            "Step 2: Find the publication year",
            "Step 3: Format the article title",
            "Step 4: Add journal information"
        ],
        "common_errors": [
            {"error": "Incorrect capitalization", "solution": "Use sentence case for article title"}
        ],
        "validation_checklist": ["Check author format", "Check year format", "Check title capitalization"],
        "special_cases": {
            "no_doi": "When no DOI is available",
            "advance_online": "For advance online publications"
        },
        "faq": [
            {"question": "How to cite without DOI?", "answer": "Include URL if available"},
            {"question": "What if there are many authors?", "answer": "Use et al. after 20 authors"}
        ],
        "related_sources": [
            {"name": "Book citations", "url": "/how-to-cite-book-apa/"},
            {"name": "Website citations", "url": "/how-to-cite-website-apa/"}
        ]
    }

    # Render source type
    source_content = engine.inject_variables(source_template, source_data)
    print(f"Source type content length: {len(source_content)} chars")
    print(f"Source type word count: {len(source_content.split())} words")

    # Validate source type content
    source_valid = engine.validate_output(source_content, min_words=2000)
    print(f"Source type validation (min 2000 words): {'PASS' if source_valid else 'FAIL'}")

    # Save test output
    engine.save_markdown(source_content, "content/test/test_source_type.md")
    print("Saved test source type to content/test/test_source_type.md")

    print("\n" + "="*50)
    print("Integration test completed!")
    print(f"Both templates rendered successfully")
    print(f"Mega guide: {len(mega_content.split())} words")
    print(f"Source type: {len(source_content.split())} words")

if __name__ == "__main__":
    test_existing_templates()