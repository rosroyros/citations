#!/usr/bin/env python3
"""
Tests for JSON schema validation.
"""

import json
import tempfile
import unittest
from pathlib import Path
import sys

# Add the schemas directory to the path
schemas_dir = Path(__file__).parent.parent / "knowledge_base" / "schemas"
sys.path.insert(0, str(schemas_dir))

from validate_schema import SchemaValidator


class TestSchemaValidation(unittest.TestCase):
    """Test schema validation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = SchemaValidator(str(schemas_dir))
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_valid_citation_rule(self):
        """Test validation of valid citation rule."""
        valid_rule = {
            "rule_id": "article_title_capitalization",
            "source": "APA Manual Section 6.14, p. 165",
            "description": "Article titles use sentence case in APA 7th edition, meaning only the first word and proper nouns are capitalized.",
            "examples": [
                {
                    "type": "correct",
                    "example": "Smith, J. (2020). The effects of sleep deprivation on cognitive performance. Journal of Sleep Research, 29(2), 123-145.",
                    "explanation": "Only 'The' is capitalized as it's the first word"
                },
                {
                    "type": "incorrect",
                    "example": "Smith, J. (2020). The Effects of Sleep Deprivation on Cognitive Performance. Journal of Sleep Research, 29(2), 123-145.",
                    "explanation": "Words like 'Effects', 'Sleep', 'Deprivation' should not be capitalized"
                }
            ],
            "category": "title_capitalization",
            "apa6_vs_7": {
                "changed_in_7": False,
                "apa6_rule": "Same as APA 6",
                "change_explanation": "No change in this rule"
            },
            "required_elements": ["title", "sentence case"],
            "optional_elements": ["subtitle with colon"]
        }

        # Write to temp file
        temp_file = Path(self.temp_dir) / "valid_rule.json"
        temp_file.write_text(json.dumps(valid_rule))

        result = self.validator.validate_file(str(temp_file), "citation_rule")
        self.assertTrue(result['valid'], f"Valid rule should pass: {result.get('errors', [])}")

    def test_invalid_citation_rule(self):
        """Test validation of invalid citation rule."""
        invalid_rule = {
            "rule_id": "test",  # Too short, doesn't match pattern
            "source": "APA Manual Section 6.14",  # Missing page number
            "description": "Too short",  # Too short
            "examples": [
                {
                    "type": "correct",
                    "example": "Short"  # Too short
                }
            ],
            "category": "invalid_category"  # Not in enum
        }

        temp_file = Path(self.temp_dir) / "invalid_rule.json"
        temp_file.write_text(json.dumps(invalid_rule))

        result = self.validator.validate_file(str(temp_file), "citation_rule")
        self.assertFalse(result['valid'], "Invalid rule should fail validation")
        self.assertGreater(len(result['errors']), 0, "Should have validation errors")

    def test_valid_example(self):
        """Test validation of valid citation example."""
        valid_example = {
            "example_id": "journal_article_1",
            "source_type": "journal_article",
            "reference_citation": "Smith, J. D., Johnson, A. B., & Williams, C. (2020). The impact of remote work on employee productivity and well-being. Journal of Organizational Psychology, 45(3), 234-251. https://doi.org/10.1037/jop0000123",
            "in_text_citations": [
                {
                    "type": "parenthetical",
                    "citation": "(Smith et al., 2020)",
                    "context": "Research has shown (Smith et al., 2020) that remote work can increase productivity."
                },
                {
                    "type": "narrative",
                    "citation": "Smith et al. (2020)",
                    "context": "Smith et al. (2020) found that remote work can increase productivity."
                }
            ],
            "metadata": {
                "title": "The impact of remote work on employee productivity and well-being",
                "year": 2020,
                "authors": [
                    {
                        "last_name": "Smith",
                        "initials": "J. D.",
                        "full_name": "John David Smith"
                    },
                    {
                        "last_name": "Johnson",
                        "initials": "A. B."
                    },
                    {
                        "last_name": "Williams",
                        "initials": "C."
                    }
                ],
                "source": {
                    "name": "Journal of Organizational Psychology",
                    "volume": "45",
                    "issue": "3",
                    "pages": "234-251",
                    "doi": "10.1037/jop0000123"
                },
                "verification": {
                    "doi_resolves": True,
                    "url_active": True,
                    "verified_date": "2024-01-15"
                }
            },
            "tags": ["remote work", "productivity", "employee well-being", "organizational psychology"],
            "special_features": ["doi_present", "many_authors"],
            "field": "psychology"
        }

        temp_file = Path(self.temp_dir) / "valid_example.json"
        temp_file.write_text(json.dumps(valid_example))

        result = self.validator.validate_file(str(temp_file), "example")
        self.assertTrue(result['valid'], f"Valid example should pass: {result.get('errors', [])}")

    def test_valid_error(self):
        """Test validation of valid error entry."""
        valid_error = {
            "error_id": "title_case_error",
            "error_name": "Article title capitalization error",
            "category": "capitalization",
            "description": "Students often capitalize every word in article titles, when APA requires sentence case",
            "wrong_example": "Smith, J. (2020). The Effects of Sleep Deprivation on Cognitive Performance. Journal Name, 15(2), 123-145.",
            "correct_example": "Smith, J. (2020). The effects of sleep deprivation on cognitive performance. Journal Name, 15(2), 123-145.",
            "explanation": "Students are used to MLA or Chicago style which title capitalizes major words, but APA uses sentence case for article titles.",
            "fix_instructions": [
                "Identify the article title (after the period and year)",
                "Capitalize only the first word of the title",
                "Capitalize proper nouns (names, places, specific terms)",
                "Capitalize the first word after a colon in the title",
                "Leave all other words in lowercase"
            ],
            "affected_source_types": ["journal_article", "magazine_article", "newspaper_article"],
            "frequency": {
                "estimated_frequency": "very_common",
                "research_basis": "University writing center statistics"
            },
            "rule_violated": "article_title_capitalization",
            "difficulty_to_fix": "easy",
            "prevention_tips": [
                "Remember: APA uses sentence case for article and chapter titles",
                "Double-check title capitalization during proofreading",
                "Use a citation manager to avoid manual formatting errors"
            ]
        }

        temp_file = Path(self.temp_dir) / "valid_error.json"
        temp_file.write_text(json.dumps(valid_error))

        result = self.validator.validate_file(str(temp_file), "error")
        self.assertTrue(result['valid'], f"Valid error should pass: {result.get('errors', [])}")

    def test_invalid_json(self):
        """Test validation of invalid JSON."""
        invalid_json = '{"rule_id": "test", invalid json}'

        temp_file = Path(self.temp_dir) / "invalid.json"
        temp_file.write_text(invalid_json)

        result = self.validator.validate_file(str(temp_file), "citation_rule")
        self.assertFalse(result['valid'], "Invalid JSON should fail")
        self.assertTrue(any("Invalid JSON" in error for error in result['errors']))

    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        incomplete_rule = {
            "rule_id": "test_rule",
            # Missing required fields: source, description, examples, category
        }

        temp_file = Path(self.temp_dir) / "incomplete.json"
        temp_file.write_text(json.dumps(incomplete_rule))

        result = self.validator.validate_file(str(temp_file), "citation_rule")
        self.assertFalse(result['valid'], "Incomplete rule should fail")
        self.assertTrue(any("required" in error.lower() for error in result['errors']))

    def test_custom_validations(self):
        """Test custom validation rules."""
        # Rule that violates custom validation (wrong and right examples are the same)
        rule_same_examples = {
            "rule_id": "test_rule_same",
            "source": "APA Manual Section 6.14, p. 165",
            "description": "A test rule that is long enough to meet minimum requirements and provides sufficient detail about the rule being described.",
            "examples": [
                {
                    "type": "correct",
                    "example": "Smith, J. (2020). Same citation example. Journal Name, 15(2), 123-145.",
                    "explanation": "This is correct"
                },
                {
                    "type": "incorrect",
                    "example": "Smith, J. (2020). Same citation example. Journal Name, 15(2), 123-145.",
                    "explanation": "This is incorrect"
                }
            ],
            "category": "title_capitalization"
        }

        temp_file = Path(self.temp_dir) / "same_examples.json"
        temp_file.write_text(json.dumps(rule_same_examples))

        result = self.validator.validate_file(str(temp_file), "citation_rule")
        self.assertTrue(result['valid'], "Rule with same examples should still be valid")
        self.assertTrue(any("different" in warning.lower() for warning in result['warnings']))

    def test_doi_format_validation(self):
        """Test DOI format validation in examples."""
        # Example with valid DOI
        example_valid_doi = {
            "example_id": "test_example",
            "source_type": "journal_article",
            "reference_citation": "Smith, J. (2020). Test article. Journal Name, 15(2), 123-145. https://doi.org/10.1037/test1234",
            "in_text_citations": [
                {
                    "type": "parenthetical",
                    "citation": "(Smith, 2020)"
                }
            ],
            "metadata": {
                "title": "Test article",
                "year": 2020,
                "authors": [{"last_name": "Smith", "initials": "J."}],
                "source": {
                    "name": "Journal Name",
                    "doi": "10.1037/test1234"
                }
            },
            "tags": ["test", "article"]
        }

        temp_file = Path(self.temp_dir) / "valid_doi.json"
        temp_file.write_text(json.dumps(example_valid_doi))

        result = self.validator.validate_file(str(temp_file), "example")
        self.assertTrue(result['valid'], "Example with valid DOI should be valid")


if __name__ == '__main__':
    unittest.main()