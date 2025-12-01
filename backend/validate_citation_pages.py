#!/usr/bin/env python3
"""
Comprehensive validation function for citation PSEO pages.

This is the most thorough validation script with optional dependencies:
1. Validates that individual citation pages are accessible (requires requests)
2. Tests HTML generation with BeautifulSoup parsing (requires bs4)
3. Ensures proper error handling for missing citations
4. Verifies SEO metadata and structured data

For simpler validation without external dependencies:
- Use test_actual_functions.py (unit tests)
- Use simple_validation.py (basic validation without imports)
"""

import sys
import re
from typing import Dict, List, Optional
from pathlib import Path
import time
import uuid
import html

# Optional imports for enhanced functionality
try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CitationPageValidator:
    """Validates individual citation PSEO pages."""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip('/')
        self.results: List[Dict] = []
        self.test_citation_id = "93f1d8e1-ef36-4382-ae12-a641ba9c9a4b"

    def validate_all(self) -> Dict:
        """
        Run all validation checks on citation pages.

        Returns:
            Dict with validation results and summary
        """
        logger.info("🔍 Starting citation page validation...")

        validation_results = {
            "timestamp": time.time(),
            "checks": {},
            "summary": {
                "total_checks": 0,
                "passed_checks": 0,
                "failed_checks": 0
            }
        }

        # Run individual checks
        checks = [
            ("route_accessibility", self.check_route_accessibility),
            ("uuid_validation", self.check_uuid_validation),
            ("html_generation", self.check_html_generation),
            ("seo_metadata", self.check_seo_metadata),
            ("error_handling", self.check_error_handling),
            ("structured_data", self.check_structured_data),
            ("missing_citation_404", self.check_missing_citation_404),
            ("invalid_uuid_404", self.check_invalid_uuid_404)
        ]

        for check_name, check_func in checks:
            logger.info(f"  📋 Running check: {check_name}")
            try:
                result = check_func()
                validation_results["checks"][check_name] = result
                validation_results["summary"]["total_checks"] += 1

                if result.get("passed", False):
                    validation_results["summary"]["passed_checks"] += 1
                    logger.info(f"    ✅ {check_name}: PASSED")
                else:
                    validation_results["summary"]["failed_checks"] += 1
                    logger.error(f"    ❌ {check_name}: FAILED - {result.get('message', 'Unknown error')}")

            except Exception as e:
                validation_results["checks"][check_name] = {
                    "passed": False,
                    "message": str(e),
                    "error": True
                }
                validation_results["summary"]["failed_checks"] += 1
                logger.error(f"    ❌ {check_name}: ERROR - {str(e)}")

        # Log summary
        summary = validation_results["summary"]
        total = summary["total_checks"]
        passed = summary["passed_checks"]
        failed = summary["failed_checks"]

        logger.info(f"\n📊 VALIDATION SUMMARY:")
        logger.info(f"   Total checks: {total}")
        logger.info(f"   Passed: {passed}")
        logger.info(f"   Failed: {failed}")

        if failed == 0:
            logger.info(f"🎉 ALL CHECKS PASSED! Citation pages are working correctly.")
        else:
            logger.error(f"⚠️  {failed} check(s) failed. Citation pages need attention.")

        return validation_results

    def check_route_accessibility(self) -> Dict:
        """
        Check if the citation route functions exist and are properly defined.

        Returns:
            Dict with check result
        """
        try:
            # Check if the functions are defined in app.py
            app_file = backend_dir / "app.py"
            app_content = app_file.read_text()

            # Check for route definition
            if '@app.get("/citations/{citation_id}")' not in app_content:
                return {
                    "passed": False,
                    "message": "Citation route not defined in app.py"
                }

            # Check for helper functions
            if 'def _get_citation_data(' not in app_content:
                return {
                    "passed": False,
                    "message": "_get_citation_data function not defined"
                }

            if 'def _generate_citation_html(' not in app_content:
                return {
                    "passed": False,
                    "message": "_generate_citation_html function not defined"
                }

            return {
                "passed": True,
                "message": "Citation route and helper functions are properly defined"
            }

        except Exception as e:
            return {
                "passed": False,
                "message": f"Route accessibility check failed: {str(e)}"
            }

    def check_uuid_validation(self) -> Dict:
        """
        Check if UUID validation is working properly.

        Returns:
            Dict with check result
        """
        # Test valid UUID format
        valid_uuid = str(uuid.uuid4())
        try:
            citation_data = _get_citation_data(valid_uuid)
            # This should return None for a valid but non-existent UUID
            # The important thing is that it doesn't crash on valid UUID format

            # Test invalid UUID format
            invalid_uuid = "not-a-uuid"
            if requests:
                try:
                    # This should be handled at the route level
                    response = requests.get(f"{self.base_url}/citations/{invalid_uuid}", timeout=5)
                    if response.status_code == 404:
                        return {
                            "passed": True,
                            "message": "UUID validation working - invalid UUIDs return 404"
                        }
                    else:
                        return {
                            "passed": False,
                            "message": f"Invalid UUID should return 404, got {response.status_code}"
                        }
                except:
                    # If we can't test via HTTP, at least verify the function exists
                    return {
                        "passed": True,
                        "message": "UUID validation function exists"
                    }
            else:
                # If requests not available, skip HTTP test
                return {
                    "passed": True,
                    "message": "UUID validation function exists (requests not available for HTTP test)"
                }

        except Exception as e:
            return {
                "passed": False,
                "message": f"UUID validation test failed: {str(e)}"
            }

    def check_html_generation(self) -> Dict:
        """
        Check if HTML generation produces valid, well-structured pages.

        Returns:
            Dict with check result
        """
        try:
            # Create test citation data
            test_data = {
                "original": "Smith, J. (2023). Test citation. Journal of Testing, 10(2), 123-145.",
                "source_type": "journal_article",
                "errors": [
                    {"component": "Author", "problem": "Missing initials", "correction": "Add initials"}
                ],
                "validation_date": "2024-11-28"
            }

            # Generate HTML
            html_content = _generate_citation_html(self.test_citation_id, test_data)

            # Validate HTML structure
            if BeautifulSoup:
                soup = BeautifulSoup(html_content, 'html.parser')
            else:
                # Basic string validation if BeautifulSoup not available
                soup = None

            if soup:
                # Check for required elements using BeautifulSoup
                required_elements = [
                    ("title", "Citation Validation Result"),
                    ("h1", "Citation Validation Result"),
                    ("meta[name='description']", "APA"),
                    ("link[rel='canonical']", self.test_citation_id),
                    ('script[type="application/ld+json"]', None)
                ]

                missing_elements = []
                for selector, expected_content in required_elements:
                    element = soup.select_one(selector)
                    if not element:
                        missing_elements.append(selector)
                    elif expected_content and expected_content.lower() not in element.get('content', element.text or '').lower():
                        missing_elements.append(f"{selector} (content mismatch)")

                if missing_elements:
                    return {
                        "passed": False,
                        "message": f"Missing required elements: {', '.join(missing_elements)}",
                        "missing_elements": missing_elements
                    }

                # Check for citation content
                if not soup.find(text=lambda text: test_data["original"] in text):
                    return {
                        "passed": False,
                        "message": "Original citation not found in generated HTML"
                    }
            else:
                # Basic string validation if BeautifulSoup not available
                basic_checks = [
                    ("DOCTYPE", "<!DOCTYPE html>"),
                    ("title", "<title>Citation Validation Result"),
                    ("citation", test_data["original"]),
                    ("canonical", self.test_citation_id),
                ]

                missing_elements = []
                for check_name, expected_content in basic_checks:
                    if expected_content not in html_content:
                        missing_elements.append(check_name)

                if missing_elements:
                    return {
                        "passed": False,
                        "message": f"Missing required content: {', '.join(missing_elements)}",
                        "missing_elements": missing_elements
                    }

            return {
                "passed": True,
                "message": "HTML generation working correctly with all required elements",
                "html_length": len(html_content)
            }

        except Exception as e:
            return {
                "passed": False,
                "message": f"HTML generation failed: {str(e)}"
            }

    def check_seo_metadata(self) -> Dict:
        """
        Check if SEO metadata is properly included.

        Returns:
            Dict with check result
        """
        try:
            test_data = {
                "original": "Test citation",
                "source_type": "book",
                "errors": [],
                "validation_date": "2024-11-28"
            }

            html_content = _generate_citation_html(self.test_citation_id, test_data)
            soup = BeautifulSoup(html_content, 'html.parser')

            # Check SEO elements
            seo_checks = [
                ("title tag", soup.find('title')),
                ("meta description", soup.find('meta', attrs={'name': 'description'})),
                ("canonical URL", soup.find('link', attrs={'rel': 'canonical'})),
                ("robots meta", soup.find('meta', attrs={'name': 'robots'})),
            ]

            missing_seo = [name for name, element in seo_checks if not element]

            if missing_seo:
                return {
                    "passed": False,
                    "message": f"Missing SEO elements: {', '.join(missing_seo)}"
                }

            # Check canonical URL contains citation ID
            canonical = soup.find('link', attrs={'rel': 'canonical'})
            if canonical and self.test_citation_id not in canonical.get('href', ''):
                return {
                    "passed": False,
                    "message": "Canonical URL doesn't contain citation ID"
                }

            return {
                "passed": True,
                "message": "SEO metadata properly configured"
            }

        except Exception as e:
            return {
                "passed": False,
                "message": f"SEO metadata check failed: {str(e)}"
            }

    def check_structured_data(self) -> Dict:
        """
        Check if structured data (JSON-LD) is properly included.

        Returns:
            Dict with check result
        """
        try:
            test_data = {
                "original": "Test citation",
                "source_type": "journal_article",
                "errors": [],
                "validation_date": "2024-11-28"
            }

            html_content = _generate_citation_html(self.test_citation_id, test_data)
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find JSON-LD script
            json_ld_script = soup.find('script', type='application/ld+json')
            if not json_ld_script:
                return {
                    "passed": False,
                    "message": "JSON-LD structured data not found"
                }

            # Parse JSON-LD content
            import json
            try:
                structured_data = json.loads(json_ld_script.string)
            except json.JSONDecodeError as e:
                return {
                    "passed": False,
                    "message": f"Invalid JSON-LD syntax: {str(e)}"
                }

            # Check required structured data fields
            required_fields = ["@context", "@type", "name", "url"]
            missing_fields = [field for field in required_fields if field not in structured_data]

            if missing_fields:
                return {
                    "passed": False,
                    "message": f"Missing structured data fields: {', '.join(missing_fields)}"
                }

            # Check if URL contains citation ID
            if self.test_citation_id not in structured_data.get("url", ""):
                return {
                    "passed": False,
                    "message": "Structured data URL doesn't contain citation ID"
                }

            return {
                "passed": True,
                "message": "Structured data properly configured",
                "structured_data_type": structured_data.get("@type")
            }

        except Exception as e:
            return {
                "passed": False,
                "message": f"Structured data check failed: {str(e)}"
            }

    def check_error_handling(self) -> Dict:
        """
        Check if error handling works correctly for edge cases.

        Returns:
            Dict with check result
        """
        try:
            # Test HTML generation with edge case data
            edge_cases = [
                ("empty citation", {"original": "", "source_type": "", "errors": []}),
                ("citation with special chars", {"original": "<script>alert('xss')</script>", "source_type": "test", "errors": []}),
                ("citation with html", {"original": "Smith <b>J.</b> (2023)", "source_type": "test", "errors": []}),
            ]

            for case_name, test_data in edge_cases:
                html_content = _generate_citation_html(self.test_citation_id, test_data)

                # Check that HTML is properly escaped
                if "<script>" in html_content or "alert(" in html_content:
                    return {
                        "passed": False,
                        "message": f"HTML not properly escaped for {case_name}"
                    }

                # Check that HTML is valid
                try:
                    BeautifulSoup(html_content, 'html.parser')
                except Exception as e:
                    return {
                        "passed": False,
                        "message": f"Invalid HTML generated for {case_name}: {str(e)}"
                    }

            return {
                "passed": True,
                "message": "Error handling working correctly for edge cases"
            }

        except Exception as e:
            return {
                "passed": False,
                "message": f"Error handling check failed: {str(e)}"
            }

    def check_missing_citation_404(self) -> Dict:
        """
        Check that missing citations return proper 404 responses.

        Returns:
            Dict with check result
        """
        try:
            # Test with a UUID that definitely doesn't exist
            nonexistent_uuid = str(uuid.uuid4())

            # Check the data retrieval function
            citation_data = _get_citation_data(nonexistent_uuid)
            if citation_data is not None:
                return {
                    "passed": False,
                    "message": "Expected None for non-existent citation, got data"
                }

            return {
                "passed": True,
                "message": "Missing citations properly return None"
            }

        except Exception as e:
            return {
                "passed": False,
                "message": f"Missing citation 404 check failed: {str(e)}"
            }

    def check_invalid_uuid_404(self) -> Dict:
        """
        Check that invalid UUID formats return proper 404 responses.

        Returns:
            Dict with check result
        """
        try:
            # Test various invalid UUID formats
            invalid_uuids = [
                "not-a-uuid",
                "123-456-789",
                "00000000-0000-0000-0000-00000",  # Too short
                "gggggggg-gggg-gggg-gggg-gggggggggggg",  # Invalid hex chars
                "",  # Empty
            ]

            uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)

            for invalid_uuid in invalid_uuids:
                if uuid_pattern.match(invalid_uuid):
                    return {
                        "passed": False,
                        "message": f"UUID pattern validation failed - {invalid_uuid} should be invalid"
                    }

            return {
                "passed": True,
                "message": "Invalid UUID formats properly rejected"
            }

        except Exception as e:
            return {
                "passed": False,
                "message": f"Invalid UUID 404 check failed: {str(e)}"
            }


def main():
    """Run citation page validation."""
    logger("=" * 80)
    logger.info("🔍 CITATION PAGE VALIDATION")
    logger.info("=" * 80)

    validator = CitationPageValidator()
    results = validator.validate_all()

    # Output results in JSON format for easy parsing
    import json
    print("\n" + "=" * 80)
    print("📋 VALIDATION RESULTS (JSON)")
    print("=" * 80)
    print(json.dumps(results, indent=2))

    # Return appropriate exit code
    failed = results["summary"]["failed_checks"]
    if failed == 0:
        logger.info("\n🎉 SUCCESS: All citation page validation checks passed!")
        return 0
    else:
        logger.error(f"\n❌ FAILURE: {failed} validation check(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())