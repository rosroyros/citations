"""
LLM Review Agent for automated content quality checks

Reviews generated PSEO content for:
- Structural completeness
- Word count requirements
- Technical formatting issues
- SEO best practices
- Content quality via LLM
"""

import json
import logging
import re
from typing import Dict, List, Optional
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from generator.llm_writer import LLMWriter

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class LLMReviewer:
    """
    Automated content reviewer using LLM for quality checks
    """

    def __init__(self):
        """Initialize reviewer with LLM writer."""
        logger.info("Initializing LLMReviewer")
        self.llm = LLMWriter()
        logger.info("LLMReviewer initialized successfully")

    def review_page(self, content: str, page_type: str, metadata: Optional[Dict] = None) -> Dict:
        """
        Comprehensive review of generated content

        Args:
            content: Markdown content to review
            page_type: Type of page ('mega_guide' or 'source_type')
            metadata: Optional metadata dict with meta_title, meta_description, etc.

        Returns:
            Dict with review results:
            {
                'overall_verdict': 'PASS' or 'NEEDS_REVISION',
                'issues_found': List[Dict],
                'word_count': int,
                'uniqueness_score': float,
                'review_summary': str
            }
        """
        logger.info(f"Starting review for {page_type} page")
        logger.debug(f"Content length: {len(content)} chars")

        issues = []

        # 1. Word count check
        logger.debug("Checking word count")
        # Use metadata word_count if available, otherwise calculate
        word_count = metadata.get('word_count', len(content.split())) if metadata else len(content.split())
        min_words = 5000 if page_type == "mega_guide" else 2000
        logger.debug(f"Word count: {word_count}, minimum: {min_words}")

        if word_count < min_words:
            issues.append({
                "severity": "high",
                "issue": f"Content too short: {word_count} words (minimum {min_words})",
                "location": "Entire page",
                "suggestion": "Expand content by adding more examples and explanations"
            })
            logger.warning(f"Word count below minimum: {word_count} < {min_words}")

        # 2. Structure check
        logger.debug("Checking required sections")
        required_sections = self._get_required_sections(page_type)
        for section in required_sections:
            if f"## {section}" not in content:
                issues.append({
                    "severity": "high",
                    "issue": f"Missing required section: {section}",
                    "location": "Structure",
                    "suggestion": f"Add {section} section with appropriate content"
                })
                logger.warning(f"Missing required section: {section}")

        # 3. Technical checks
        logger.debug("Running technical checks")
        technical_issues = self._technical_checks(content, page_type)
        issues.extend(technical_issues)
        logger.debug(f"Found {len(technical_issues)} technical issues")

        # 4. SEO checks
        if metadata:
            logger.debug("Running SEO checks")
            seo_issues = self._seo_checks(content, metadata)
            issues.extend(seo_issues)
            logger.debug(f"Found {len(seo_issues)} SEO issues")

        # 5. LLM quality check (optional - only if no critical issues and enabled)
        # Skip LLM check if SKIP_LLM_REVIEW env var is set (useful for tests)
        import os
        skip_llm = os.getenv('SKIP_LLM_REVIEW', 'false').lower() == 'true'

        high_issues = [i for i in issues if i["severity"] == "high"]
        if not skip_llm and len(high_issues) == 0 and len(content) > 500:
            logger.debug("Running LLM quality check")
            try:
                quality_issues = self._llm_quality_check(content, page_type)
                issues.extend(quality_issues)
                logger.debug(f"Found {len(quality_issues)} quality issues from LLM")
            except Exception as e:
                logger.error(f"LLM quality check failed: {e}")
                # Don't fail entire review if LLM check fails
                pass
        elif skip_llm:
            logger.debug("Skipping LLM quality check (SKIP_LLM_REVIEW=true)")

        # Determine overall verdict
        high_issues = [i for i in issues if i["severity"] == "high"]
        overall_verdict = "NEEDS_REVISION" if high_issues else "PASS"
        logger.info(f"Review complete. Verdict: {overall_verdict}, Issues: {len(issues)}")

        return {
            "overall_verdict": overall_verdict,
            "issues_found": issues,
            "word_count": word_count,
            "uniqueness_score": self._check_uniqueness(content),
            "review_summary": self._generate_summary(issues)
        }

    def _technical_checks(self, content: str, page_type: str) -> List[Dict]:
        """Check technical formatting issues."""
        logger.debug("Starting technical checks")
        issues = []

        # Check for template variable failures
        if "{{" in content and "}}" in content:
            issues.append({
                "severity": "high",
                "issue": "Template variables not replaced",
                "location": "Throughout page",
                "suggestion": "Check template engine configuration"
            })
            logger.warning("Found unrendered template variables")

        # Check heading hierarchy
        lines = content.split('\n')
        h1_count = 0
        prev_h_level = 0

        for line in lines:
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                if level == 1:
                    h1_count += 1
                if prev_h_level > 0 and level > prev_h_level + 1:
                    issues.append({
                        "severity": "medium",
                        "issue": f"Heading hierarchy skip: H{prev_h_level} to H{level}",
                        "location": line.strip(),
                        "suggestion": "Use sequential heading levels"
                    })
                    logger.warning(f"Heading skip detected: {line.strip()}")
                prev_h_level = level

        if h1_count != 1:
            issues.append({
                "severity": "high",
                "issue": f"Found {h1_count} H1 headings (should be exactly 1)",
                "location": "Headings",
                "suggestion": "Use only one H1 per page"
            })
            logger.warning(f"Incorrect H1 count: {h1_count}")

        # Check for proper APA formatting in examples
        citation_pattern = r'\([^)]+,\s*\d{4}[,\)]'
        citations = re.findall(citation_pattern, content)

        if len(citations) < 5 and page_type == "mega_guide":
            issues.append({
                "severity": "medium",
                "issue": "Very few citation examples found",
                "location": "Examples",
                "suggestion": "Add more APA citation examples throughout the page"
            })
            logger.info(f"Only {len(citations)} citation examples found")

        logger.debug(f"Technical checks complete. Found {len(issues)} issues")
        return issues

    def _seo_checks(self, content: str, metadata: Dict) -> List[Dict]:
        """Check SEO best practices."""
        logger.debug("Starting SEO checks")
        issues = []

        # Check meta title length
        title = metadata.get('meta_title', '')
        if len(title) < 30 or len(title) > 60:
            issues.append({
                "severity": "medium",
                "issue": f"Meta title length: {len(title)} chars (ideal: 30-60)",
                "location": "Meta title",
                "suggestion": "Adjust title length for optimal SEO"
            })
            logger.warning(f"Meta title length suboptimal: {len(title)} chars")

        # Check meta description length
        desc = metadata.get('meta_description', '')
        if len(desc) < 120 or len(desc) > 160:
            issues.append({
                "severity": "medium",
                "issue": f"Meta description length: {len(desc)} chars (ideal: 120-160)",
                "location": "Meta description",
                "suggestion": "Adjust description length for optimal click-through rate"
            })
            logger.warning(f"Meta description length suboptimal: {len(desc)} chars")

        # Check internal links
        internal_links = re.findall(r'\[([^\]]+)\]\(/([^)]+)\)', content)
        if len(internal_links) < 8:
            issues.append({
                "severity": "low",
                "issue": f"Only {len(internal_links)} internal links found (ideal: 8-15)",
                "location": "Internal linking",
                "suggestion": "Add more internal links to related pages"
            })
            logger.info(f"Internal links count: {len(internal_links)}")

        logger.debug(f"SEO checks complete. Found {len(issues)} issues")
        return issues

    def _llm_quality_check(self, content: str, page_type: str) -> List[Dict]:
        """Use LLM to check content quality."""
        logger.info("Starting LLM quality check")

        # Truncate content for review to save tokens
        content_preview = content[:3000] if len(content) > 3000 else content

        prompt = f"""Review this {page_type} page for quality issues:

{content_preview}{"..." if len(content) > 3000 else ""}

Check for:
1. ACCURACY: Are citation rules correct per APA 7?
2. CLARITY: Is language clear and easy to understand?
3. TONE: Is tone conversational and helpful?
4. EXAMPLES: Are examples properly formatted in APA 7?
5. COMPLETENESS: Does content feel complete and valuable?
6. ORIGINALITY: Does content feel generic or copy-paste?

Return JSON format:
{{
  "issues": [
    {{
      "severity": "high/medium/low",
      "issue": "Description of issue",
      "location": "Section name or general",
      "suggestion": "How to fix it"
    }}
  ]
}}

If no issues found, return: {{"issues": []}}
"""

        try:
            logger.debug("Calling LLM for quality review")
            response = self.llm._call_openai(prompt, max_tokens=800)
            logger.debug(f"LLM response received: {response[:200]}...")

            # Parse JSON response
            result = json.loads(response)
            issues = result.get("issues", [])
            logger.info(f"LLM quality check complete. Found {len(issues)} issues")
            return issues

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Raw response: {response}")
            return []
        except Exception as e:
            logger.error(f"LLM quality check failed: {e}")
            return [{
                "severity": "medium",
                "issue": f"LLM review failed: {str(e)}",
                "location": "Review system",
                "suggestion": "Manual review recommended"
            }]

    def _get_required_sections(self, page_type: str) -> List[str]:
        """Get list of required sections for page type."""
        if page_type == "mega_guide":
            return [
                "Introduction",
                "Examples",
                "Common Errors",
                "Validation Checklist",
                "Frequently Asked Questions"
            ]
        elif page_type == "source_type":
            return [
                "Basic Format",
                "Examples",
                "Common Errors",
                "Validation Checklist"
            ]
        return []

    def _check_uniqueness(self, content: str) -> float:
        """
        Check content uniqueness (simple implementation).

        This would ideally check against existing pages.
        For now, return a placeholder score.
        """
        # TODO: Implement actual uniqueness check against existing content
        return 0.85

    def _generate_summary(self, issues: List[Dict]) -> str:
        """Generate summary of review results."""
        if not issues:
            return "No issues found. Content passes all quality checks."

        high_count = len([i for i in issues if i["severity"] == "high"])
        medium_count = len([i for i in issues if i["severity"] == "medium"])
        low_count = len([i for i in issues if i["severity"] == "low"])

        summary_parts = []
        if high_count > 0:
            summary_parts.append(f"{high_count} high")
        if medium_count > 0:
            summary_parts.append(f"{medium_count} medium")
        if low_count > 0:
            summary_parts.append(f"{low_count} low")

        return f"Found {len(issues)} issues: {', '.join(summary_parts)}"


if __name__ == "__main__":
    # Quick test
    reviewer = LLMReviewer()
    test_content = """# Test Guide

## Introduction
This is a test guide.

## Examples
Example content here.

## Common Errors
Error content here.

## Validation Checklist
Checklist here.

## Frequently Asked Questions
FAQ here.
""" + ("More content here. " * 1000)

    result = reviewer.review_page(
        test_content,
        "mega_guide",
        {
            "meta_title": "Test Guide for APA Citations and Formatting",
            "meta_description": "This is a comprehensive test guide that helps you understand APA citation formatting rules and best practices for academic writing."
        }
    )

    print(json.dumps(result, indent=2))
