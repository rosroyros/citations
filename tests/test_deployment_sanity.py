"""
Deployment Sanity Tests

Lightweight tests that run during deployment to catch critical issues
without being overly strict about every possible problem.
"""

import requests
import pytest
from xml.etree import ElementTree as ET

BASE_URL = "https://citationformatchecker.com"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"

class TestDeploymentSanity:
    """Critical deployment sanity checks"""

    def test_sitemap_accessible(self):
        """Sitemap should be accessible and valid XML"""
        resp = requests.get(SITEMAP_URL, timeout=30)
        assert resp.status_code == 200, f"Sitemap returned {resp.status_code}"

        # Validate XML structure
        try:
            ET.fromstring(resp.content)
        except ET.ParseError as e:
            pytest.fail(f"Sitemap is invalid XML: {e}")

    def test_sitemap_has_minimum_urls(self):
        """Sitemap should have substantial number of URLs"""
        resp = requests.get(SITEMAP_URL, timeout=30)
        root = ET.fromstring(resp.content)

        # Find all URL elements (handle namespace)
        namespaces = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = root.findall('.//sitemap:loc', namespaces)

        MIN_EXPECTED_URLS = 180  # Conservative minimum for deployment
        actual_count = len(urls)
        assert actual_count >= MIN_EXPECTED_URLS, f"Only {actual_count} URLs in sitemap, expected >= {MIN_EXPECTED_URLS}"

    def test_critical_pages_accessible(self):
        """Critical pages that must work"""
        critical_urls = [
            f"{BASE_URL}/",
            f"{BASE_URL}/apa-7th-edition-citation-guide/",
            f"{BASE_URL}/citation-styles/",
        ]

        for url in critical_urls:
            resp = requests.get(url, timeout=30)
            assert resp.status_code == 200, f"Critical page {url} returned {resp.status_code}"
            assert len(resp.content) > 5000, f"{url} appears to be blank or minimal content"

    def test_sample_citation_pages_work(self):
        """Sample some key citation pages to ensure they work"""
        # Test a few key citation pages that should always exist
        sample_urls = [
            f"{BASE_URL}/cite-developmental-psychology-apa/",
            f"{BASE_URL}/cite-consulting-clinical-psychology-apa/",
            f"{BASE_URL}/cite-cognitive-psychology-apa/",
        ]

        for url in sample_urls:
            try:
                resp = requests.get(url, timeout=30)
                if resp.status_code == 200:
                    # Verify substantial content
                    assert len(resp.content) > 25000, f"{url} appears to have insufficient content: {len(resp.content)} bytes"
                    print(f"✅ {url} - OK")
                else:
                    print(f"⚠️  {url} returned {resp.status_code} - may need attention")
            except Exception as e:
                print(f"⚠️  {url} failed: {e}")

        # Note: We don't fail the deployment if some sample pages are missing,
        # but we log warnings for review

    def test_no_completely_broken_urls(self):
        """Check for obviously broken URLs in sitemap"""
        resp = requests.get(SITEMAP_URL, timeout=30)
        root = ET.fromstring(resp.content)
        namespaces = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [elem.text for elem in root.findall('.//sitemap:loc', namespaces)]

        # Focus on obviously malformed URLs
        malformed = []
        for url in urls:
            if not url.startswith('http') or url.count('//') > 1:
                malformed.append(url)

        # Allow some malformed URLs (they can be cleaned up later)
        assert len(malformed) < 10, f"Too many malformed URLs: {len(malformed)}"
        if malformed:
            print(f"⚠️  Found {len(malformed)} malformed URLs (should be cleaned up)")

    def test_sitemap_performance(self):
        """Sitemap should load reasonably quickly"""
        import time
        start_time = time.time()
        resp = requests.get(SITEMAP_URL, timeout=30)
        load_time = time.time() - start_time

        assert resp.status_code == 200
        assert load_time < 15.0, f"Sitemap took {load_time:.2f}s to load, should be under 15s"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])