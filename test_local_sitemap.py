#!/usr/bin/env python3
"""
Test our local cleaned sitemap to verify it meets all requirements
"""

import requests
import xml.etree.ElementTree as ET
import random

def test_local_sitemap():
    """Test the local cleaned sitemap"""

    # Load local sitemap
    with open('frontend/frontend/dist/sitemap.xml', 'r') as f:
        content = f.read()

    # Parse XML
    try:
        root = ET.fromstring(content)
        ns = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [elem.text for elem in root.findall('.//sitemap:loc', ns)]
    except ET.ParseError as e:
        print(f"❌ Sitemap XML parsing failed: {e}")
        return False

    print(f"🔍 Testing local sitemap with {len(urls)} URLs")
    print("="*50)

    # Test 1: Minimum URL count
    MIN_EXPECTED = 180
    print(f"1. URL count test: {len(urls)} >= {MIN_EXPECTED} {'✅' if len(urls) >= MIN_EXPECTED else '❌'}")

    # Test 2: Malformed URLs
    malformed = [url for url in urls if '/cite-/cite-' in url or not url.startswith('http')]
    print(f"2. Malformed URLs: {len(malformed)} {'✅' if len(malformed) == 0 else '❌'}")

    # Test 3: Duplicates
    unique = set(urls)
    duplicates = len(urls) - len(unique)
    print(f"3. Duplicate URLs: {duplicates} {'✅' if duplicates == 0 else '❌'}")

    # Test 4: Sample content URLs work
    content_urls = [url for url in urls if '/cite-' in url]
    sample_size = min(5, len(content_urls))
    sample = random.sample(content_urls, sample_size)

    working_count = 0
    for url in sample:
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200 and len(resp.content) > 10000:
                working_count += 1
        except:
            pass

    print(f"4. Sample content URLs: {working_count}/{sample_size} working {'✅' if working_count >= sample_size * 0.8 else '❌'}")

    # Test 5: Critical pages exist
    critical_urls = [
        'https://citationformatchecker.com/cite-developmental-psychology-apa/',
        'https://citationformatchecker.com/cite-consulting-clinical-psychology-apa/',
        'https://citationformatchecker.com/cite-cognitive-psychology-apa/',
    ]

    critical_in_sitemap = [url for url in critical_urls if url in urls]
    print(f"5. Critical pages: {len(critical_in_sitemap)}/{len(critical_urls)} found {'✅' if len(critical_in_sitemap) == len(critical_urls) else '❌'}")

    # Overall result
    all_passed = (
        len(urls) >= MIN_EXPECTED and
        len(malformed) == 0 and
        duplicates == 0 and
        working_count >= sample_size * 0.8 and
        len(critical_in_sitemap) == len(critical_urls)
    )

    print("="*50)
    print(f"🎯 Overall result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

    return all_passed

if __name__ == "__main__":
    test_local_sitemap()