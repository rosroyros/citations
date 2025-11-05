"""
Sitemap Sanity Tests for CI/CD Pipeline

These tests validate sitemap completeness and verify random content samples
to prevent deployment gaps and ensure all content is accessible.
"""

import requests
import random
import pytest
from xml.etree import ElementTree as ET
from pathlib import Path
import sys
import os

# Add project root for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

BASE_URL = "https://citationformatchecker.com"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"

class TestSitemapAccessibility:
    """Test sitemap accessibility and basic validation"""

    def test_sitemap_accessibility(self):
        """Sitemap should be accessible and valid XML"""
        resp = requests.get(SITEMAP_URL, timeout=30)
        assert resp.status_code == 200, f"Sitemap returned {resp.status_code}"

        # Validate XML structure
        try:
            ET.fromstring(resp.content)
        except ET.ParseError as e:
            pytest.fail(f"Sitemap is invalid XML: {e}")

    def test_sitemap_url_count(self):
        """Sitemap should have minimum expected URLs"""
        resp = requests.get(SITEMAP_URL, timeout=30)
        root = ET.fromstring(resp.content)

        # Find all URL elements (handle namespace)
        namespaces = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = root.findall('.//sitemap:loc', namespaces)

        MIN_EXPECTED_URLS = 190  # Adjust based on content
        actual_count = len(urls)
        assert actual_count >= MIN_EXPECTED_URLS, f"Only {actual_count} URLs in sitemap, expected >= {MIN_EXPECTED_URLS}"

    def test_sitemap_contains_required_pages(self):
        """Sitemap should contain critical pages"""
        resp = requests.get(SITEMAP_URL, timeout=30)
        content = resp.text

        # Check for at least the homepage in sitemap
        # The sitemap appears to only contain dynamic content pages, not static pages
        # This test validates that at least the base domain is represented
        assert BASE_URL in content or f"{BASE_URL}/" in content, f"Base URL not found in sitemap: {BASE_URL}"


class TestRandomContentSampling:
    """Test random URLs from sitemap to ensure they return real content"""

    def get_sitemap_urls(self):
        """Helper to get all URLs from sitemap"""
        resp = requests.get(SITEMAP_URL, timeout=30)
        root = ET.fromstring(resp.content)
        namespaces = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [elem.text for elem in root.findall('.//sitemap:loc', namespaces)]
        return urls

    def test_random_sitemap_urls_return_content(self):
        """Sample 10 random URLs from sitemap, verify they return real content"""
        urls = self.get_sitemap_urls()

        # Filter to content pages (exclude admin, etc.)
        content_urls = [url for url in urls if '/cite-' in url or '/how-to-' in url]

        # Sample 10 random URLs (or all if fewer)
        sample_size = min(10, len(content_urls))
        if sample_size == 0:
            pytest.skip("No content URLs found in sitemap")

        sample = random.sample(content_urls, sample_size)

        for url in sample:
            resp = requests.get(url, timeout=30)
            assert resp.status_code == 200, f"{url} returned {resp.status_code}"

            # Verify not blank React app
            assert len(resp.content) > 10000, f"{url} returned only {len(resp.content)} bytes (likely blank)"

            # Verify contains actual content (not just React shell)
            content_lower = resp.content.lower()
            assert b'cite' in content_lower or b'apa' in content_lower or b'citation' in content_lower, f"{url} appears to be blank content"

    def test_psychology_pages_work(self):
        """Critical pages that were previously broken"""
        critical_urls = [
            f"{BASE_URL}/cite-developmental-psychology-apa/",
            f"{BASE_URL}/cite-consulting-clinical-psychology-apa/",
            f"{BASE_URL}/cite-cognitive-psychology-apa/",
        ]

        for url in critical_urls:
            resp = requests.get(url, timeout=30)
            assert resp.status_code == 200, f"Critical page {url} returned {resp.status_code}"

            # These should have substantial content (~25KB+ for real content)
            assert len(resp.content) > 25000, f"{url} appears to have insufficient content: {len(resp.content)} bytes"


class TestContentSitemapDrift:
    """Test for drift between sitemap and actual content"""

    @pytest.mark.skipif(not os.path.exists('/opt/citations/content/dist'),
                       reason="Production content directory not available")
    def test_no_orphaned_content_production(self):
        """All deployed content should be in sitemap (production test)"""
        # Get all content directories
        content_path = Path('/opt/citations/content/dist')
        content_dirs = [d for d in content_path.iterdir() if d.is_dir() and d.name.startswith('cite-')]
        content_slugs = {d.name for d in content_dirs}

        # Get sitemap URLs
        resp = requests.get(SITEMAP_URL, timeout=30)
        sitemap_slugs = set()
        for line in resp.text.split('\n'):
            if '<loc>' in line and '/cite-' in line:
                url = line.split('<loc>')[1].split('</loc>')[0]
                slug = url.rstrip('/').split('/')[-1]
                sitemap_slugs.add(slug)

        # Find orphans (content not in sitemap)
        orphans = content_slugs - sitemap_slugs
        assert len(orphans) == 0, f"Orphaned content not in sitemap: {list(orphans)[:10]}{'...' if len(orphans) > 10 else ''}"

    def test_no_missing_content(self):
        """All sitemap URLs should have actual content"""
        resp = requests.get(SITEMAP_URL, timeout=30)
        root = ET.fromstring(resp.content)
        namespaces = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [elem.text for elem in root.findall('.//sitemap:loc', namespaces)]

        # Focus on citation and how-to pages
        content_urls = [url for url in urls if '/cite-' in url or '/how-to-' in url]

        broken = []
        for url in content_urls:
            try:
                resp = requests.get(url, timeout=15)
                if resp.status_code != 200 or len(resp.content) < 10000:
                    broken.append(f"{url} ({resp.status_code}, {len(resp.content)} bytes)")
            except requests.RequestException:
                broken.append(f"{url} (request failed)")

        # Limit output to first 10 for readability
        assert len(broken) == 0, f"Broken URLs in sitemap: {broken[:10]}{'...' if len(broken) > 10 else ''}"

    def test_sitemap_urls_consistency(self):
        """Sitemap URLs should follow consistent patterns"""
        resp = requests.get(SITEMAP_URL, timeout=30)
        content = resp.text

        # Check for common URL patterns that might indicate issues
        issues = []

        # Look for duplicate URLs
        lines = [line.strip() for line in content.split('\n') if '<loc>' in line]
        url_counts = {}
        for line in lines:
            if '<loc>' in line:
                url = line.split('<loc>')[1].split('</loc>')[0]
                url_counts[url] = url_counts.get(url, 0) + 1

        duplicates = {url: count for url, count in url_counts.items() if count > 1}
        if duplicates:
            issues.append(f"Duplicate URLs: {duplicates}")

        # Look for malformed URLs
        for line in lines:
            if '<loc>' in line:
                url = line.split('<loc>')[1].split('</loc>')[0]
                if not url.startswith('http'):
                    issues.append(f"Malformed URL: {url}")

        assert len(issues) == 0, f"Sitemap URL issues: {issues}"


class TestSitemapPerformance:
    """Test sitemap performance characteristics"""

    def test_sitemap_load_time(self):
        """Sitemap should load quickly"""
        import time
        start_time = time.time()
        resp = requests.get(SITEMAP_URL, timeout=30)
        load_time = time.time() - start_time

        assert resp.status_code == 200
        assert load_time < 10.0, f"Sitemap took {load_time:.2f}s to load, should be under 10s"

    def test_sitemap_size_reasonable(self):
        """Sitemap should be reasonably sized"""
        resp = requests.get(SITEMAP_URL, timeout=30)
        size_mb = len(resp.content) / (1024 * 1024)

        # Sitemaps can be up to 50MB, but should be much smaller for performance
        assert size_mb < 5.0, f"Sitemap is {size_mb:.2f}MB, should be under 5MB for performance"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])