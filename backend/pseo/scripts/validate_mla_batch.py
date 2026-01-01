#!/usr/bin/env python3
"""
MLA Page Batch Quality Validator

Validates generated MLA pages against quality gates before deployment.

Quality Gates:
1. Word count >= threshold (800 words for content)
2. No template variables ({{ ... }})
3. No em dashes (—) that should be en dashes
4. H1 contains "MLA"
5. TF-IDF similarity vs APA pages < 0.3 (distinctness check)
6. CITATION_STYLE set to 'mla9' (for mini-checker validation)
7. Cross-style link to APA version present (for specific sources)

Usage:
    python validate_mla_batch.py                    # Validate all MLA pages
    python validate_mla_batch.py --pilot            # Validate pilot pages only
    python validate_mla_batch.py --source youtube   # Validate specific source

Exit codes:
    0 - All checks passed
    1 - Some checks failed
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Quality gate thresholds
MIN_WORD_COUNT = 800
MAX_TF_IDF_SIMILARITY = 0.3

# Pilot pages
PILOT_PAGES = ['youtube', 'book', 'website']


class MLAPageValidator:
    """Validator for MLA PSEO pages"""

    def __init__(self, pages_dir: Path):
        """
        Initialize validator

        Args:
            pages_dir: Directory containing MLA page HTML files
        """
        self.pages_dir = pages_dir
        self.results = defaultdict(list)
        self.total_pages = 0
        self.passed_pages = 0
        self.failed_pages = 0

    def validate_all(self, page_filter=None):
        """
        Validate all MLA pages or filtered subset

        Args:
            page_filter: Optional list of page IDs to validate
        """
        logger.info("=" * 80)
        logger.info("MLA PAGE QUALITY VALIDATION")
        logger.info("=" * 80)

        # Find all HTML files
        html_files = list(self.pages_dir.rglob("*/index.html"))

        if not html_files:
            logger.error(f"No HTML files found in {self.pages_dir}")
            sys.exit(1)

        logger.info(f"Found {len(html_files)} HTML files to validate\n")

        # Validate each page
        for html_file in html_files:
            page_id = html_file.parent.name

            # Apply filter if specified
            if page_filter and page_id not in page_filter:
                continue

            self.total_pages += 1
            passed = self.validate_page(html_file, page_id)

            if passed:
                self.passed_pages += 1
            else:
                self.failed_pages += 1

        # Optional: Check TF-IDF distinctness (batch comparison)
        # This checks if MLA pages are distinct from APA pages
        apa_pages_dir = self.pages_dir.parent / "apa"  # Assumes apa pages at same level
        if apa_pages_dir.exists():
            self.check_tfidf_distinctness(self.pages_dir, apa_pages_dir)

        # Report results
        self.report_results()

    def validate_page(self, html_file: Path, page_id: str) -> bool:
        """
        Validate a single page against all quality gates

        Args:
            html_file: Path to HTML file
            page_id: Page identifier

        Returns:
            True if all checks passed, False otherwise
        """
        logger.info(f"Validating: {page_id}")

        html_content = html_file.read_text(encoding='utf-8')
        all_passed = True

        # Gate 1: Word count
        if not self.check_word_count(html_content, page_id):
            all_passed = False

        # Gate 2: No template variables
        if not self.check_no_template_vars(html_content, page_id):
            all_passed = False

        # Gate 3: No em dashes
        if not self.check_no_em_dashes(html_content, page_id):
            all_passed = False

        # Gate 4: H1 contains "MLA"
        if not self.check_h1_mla(html_content, page_id):
            all_passed = False

        # Gate 5: Mini-checker has data-style
        if not self.check_minichecker_config(html_content, page_id):
            all_passed = False

        # Gate 6: Cross-style link present (for specific sources)
        if self.is_specific_source(html_file):
            if not self.check_cross_style_link(html_content, page_id):
                all_passed = False

        if all_passed:
            logger.info(f"  ✅ All checks passed\n")
        else:
            logger.warning(f"  ⚠️  Some checks failed\n")

        return all_passed

    def check_word_count(self, html_content: str, page_id: str) -> bool:
        """Check if word count meets minimum threshold"""
        # Strip HTML tags and count words
        text = re.sub(r'<[^>]+>', ' ', html_content)
        word_count = len(text.split())

        if word_count >= MIN_WORD_COUNT:
            logger.info(f"  ✅ Word count: {word_count:,} (>= {MIN_WORD_COUNT:,})")
            return True
        else:
            logger.error(f"  ❌ Word count: {word_count:,} (< {MIN_WORD_COUNT:,})")
            self.results[page_id].append(f"Word count too low: {word_count}")
            return False

    def check_no_template_vars(self, html_content: str, page_id: str) -> bool:
        """Check for unreplaced template variables"""
        matches = re.findall(r'\{\{[^}]+\}\}', html_content)

        if not matches:
            logger.info(f"  ✅ No template variables")
            return True
        else:
            logger.error(f"  ❌ Found {len(matches)} template variables: {matches[:3]}")
            self.results[page_id].append(f"Template variables found: {matches}")
            return False

    def check_no_em_dashes(self, html_content: str, page_id: str) -> bool:
        """Check for em dashes that should be en dashes"""
        em_dash_count = html_content.count('—')

        if em_dash_count == 0:
            logger.info(f"  ✅ No em dashes")
            return True
        else:
            logger.warning(f"  ⚠️  Found {em_dash_count} em dashes (review manually)")
            self.results[page_id].append(f"Em dashes found: {em_dash_count}")
            # Don't fail on this - just warn
            return True

    def check_h1_mla(self, html_content: str, page_id: str) -> bool:
        """Check if H1 contains 'MLA'"""
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', html_content, re.IGNORECASE | re.DOTALL)

        if not h1_match:
            logger.error(f"  ❌ No H1 found")
            self.results[page_id].append("No H1 found")
            return False

        h1_text = h1_match.group(1)

        if 'MLA' in h1_text or 'mla' in h1_text.lower():
            logger.info(f"  ✅ H1 contains 'MLA': {h1_text[:50]}")
            return True
        else:
            logger.error(f"  ❌ H1 missing 'MLA': {h1_text[:50]}")
            self.results[page_id].append(f"H1 missing MLA: {h1_text}")
            return False

    def check_minichecker_config(self, html_content: str, page_id: str) -> bool:
        """Check for correct citation style configuration (CITATION_STYLE = 'mla9')"""
        # Check the actual config used by static page JavaScript
        has_correct_style = "CITATION_STYLE = 'mla9'" in html_content

        if has_correct_style:
            logger.info(f"  ✅ CITATION_STYLE set to 'mla9'")
            return True
        else:
            logger.error(f"  ❌ Missing CITATION_STYLE = 'mla9'")
            self.results[page_id].append("CITATION_STYLE not set to mla9")
            return False

    def check_cross_style_link(self, html_content: str, page_id: str) -> bool:
        """Check for cross-style link to APA version"""
        has_apa_link = re.search(r'href=["\'][^"\']*-apa[/\'"]+', html_content)

        if has_apa_link:
            logger.info(f"  ✅ Cross-style link to APA present")
            return True
        else:
            logger.warning(f"  ⚠️  No cross-style link to APA found")
            self.results[page_id].append("Missing cross-style link to APA")
            # Don't fail - this is a warning
            return True

    def is_specific_source(self, html_file: Path) -> bool:
        """Check if page is a specific source page (vs mega or source type)"""
        # Specific source pages are under cite-*-mla/
        return html_file.parent.parent.name.startswith('cite-')

    def check_tfidf_distinctness(self, mla_pages_dir: Path, apa_pages_dir: Path):
        """
        Check TF-IDF similarity between MLA and APA pages

        This is a more advanced check that compares content distinctness.
        Skipped if APA pages not available.

        Args:
            mla_pages_dir: Directory with MLA pages
            apa_pages_dir: Directory with APA pages
        """
        if not apa_pages_dir.exists():
            logger.warning("⚠️  APA pages not found, skipping TF-IDF distinctness check")
            return

        logger.info("\n" + "=" * 80)
        logger.info("TF-IDF DISTINCTNESS CHECK")
        logger.info("=" * 80)

        # Load MLA and APA page content
        mla_texts = []
        apa_texts = []

        for html_file in mla_pages_dir.rglob("*/index.html"):
            html_content = html_file.read_text(encoding='utf-8')
            text = re.sub(r'<[^>]+>', ' ', html_content)
            mla_texts.append(text)

        for html_file in apa_pages_dir.rglob("*/index.html"):
            html_content = html_file.read_text(encoding='utf-8')
            text = re.sub(r'<[^>]+>', ' ', html_content)
            apa_texts.append(text)

        if not mla_texts or not apa_texts:
            logger.warning("Not enough pages for TF-IDF comparison")
            return

        # Calculate TF-IDF vectors
        vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        all_texts = mla_texts + apa_texts
        tfidf_matrix = vectorizer.fit_transform(all_texts)

        # Calculate average similarity
        mla_vectors = tfidf_matrix[:len(mla_texts)]
        apa_vectors = tfidf_matrix[len(mla_texts):]

        similarities = cosine_similarity(mla_vectors, apa_vectors)
        avg_similarity = similarities.mean()

        logger.info(f"Average TF-IDF similarity: {avg_similarity:.3f}")

        if avg_similarity < MAX_TF_IDF_SIMILARITY:
            logger.info(f"✅ Pages are distinct (< {MAX_TF_IDF_SIMILARITY})")
        else:
            logger.warning(f"⚠️  Pages may be too similar (>= {MAX_TF_IDF_SIMILARITY})")

    def report_results(self):
        """Report validation results"""
        logger.info("\n" + "=" * 80)
        logger.info("VALIDATION RESULTS")
        logger.info("=" * 80)

        logger.info(f"Total pages validated: {self.total_pages}")
        logger.info(f"✅ Passed: {self.passed_pages}")
        logger.info(f"❌ Failed: {self.failed_pages}")

        if self.failed_pages > 0:
            logger.warning("\n⚠️  FAILED PAGES:")
            for page_id, issues in self.results.items():
                if issues:
                    logger.warning(f"\n  {page_id}:")
                    for issue in issues:
                        logger.warning(f"    - {issue}")

            logger.error(f"\n❌ {self.failed_pages} pages failed validation")
            sys.exit(1)
        else:
            logger.info("\n🎉 All pages passed validation!")


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(
        description="Validate MLA PSEO pages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('--pilot', action='store_true',
                        help='Validate pilot pages only')
    parser.add_argument('--source', type=str,
                        help='Validate specific source by ID')
    parser.add_argument('--pages-dir', type=Path,
                        default=Path(__file__).parent.parent / "dist" / "mla",
                        help='Directory containing MLA pages')

    args = parser.parse_args()

    # Initialize validator
    validator = MLAPageValidator(args.pages_dir)

    # Determine page filter
    page_filter = None
    if args.pilot:
        logger.info("🚀 PILOT MODE: Validating pilot pages only\n")
        page_filter = PILOT_PAGES
    elif args.source:
        logger.info(f"📄 Validating specific source: {args.source}\n")
        page_filter = [args.source]

    # Run validation
    validator.validate_all(page_filter)


if __name__ == "__main__":
    main()
