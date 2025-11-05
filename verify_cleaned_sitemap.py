#!/usr/bin/env python3
"""
Verify the cleaned sitemap is properly formatted and has no issues
"""

import xml.etree.ElementTree as ET

def verify_sitemap(sitemap_path):
    """Verify sitemap has no malformed URLs or duplicates"""

    print(f"🔍 Verifying {sitemap_path}")

    try:
        tree = ET.parse(sitemap_path)
        root = tree.getroot()

        # Handle namespace
        ns = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        # Extract all URLs
        urls = []
        malformed_count = 0

        for url in root.findall('.//sitemap:url', ns):
            loc = url.find('.//sitemap:loc', ns)
            if loc is not None:
                url_text = loc.text

                # Check for malformed URLs
                if not url_text.startswith('http') or '/cite-/cite-' in url_text:
                    malformed_count += 1
                    print(f"  ❌ Malformed: {url_text}")

                urls.append(url_text)

        # Check duplicates
        unique_urls = set(urls)
        duplicate_count = len(urls) - len(unique_urls)

        print(f"  📊 Total URLs: {len(urls)}")
        print(f"  🧹 Unique URLs: {len(unique_urls)}")
        print(f"  ❌ Malformed URLs: {malformed_count}")
        print(f"  🔄 Duplicate URLs: {duplicate_count}")

        if duplicate_count > 0:
            print("\n  Duplicates found:")
            duplicates = {}
            for url in urls:
                duplicates[url] = duplicates.get(url, 0) + 1

            for url, count in duplicates.items():
                if count > 1:
                    print(f"    {url} ({count} times)")

        # Success criteria
        success = malformed_count == 0 and duplicate_count == 0
        print(f"\n  {'✅ PASSED' if success else '❌ FAILED'}: Sitemap is {'clean' if success else 'not clean'}")

        return success

    except Exception as e:
        print(f"  ❌ Error parsing sitemap: {e}")
        return False

if __name__ == "__main__":
    print("=== SITEMAP VERIFICATION ===\n")

    # Test original (backup) sitemap
    original_passed = verify_sitemap("backup/sitemap_backup_20251105_224825.xml")

    print("\n" + "="*50 + "\n")

    # Test cleaned sitemap
    cleaned_passed = verify_sitemap("backup/sitemap_cleaned.xml")

    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"  Original sitemap: {'❌ HAD ISSUES' if not original_passed else '✅ OK'}")
    print(f"  Cleaned sitemap:  {'✅ FIXED' if cleaned_passed else '❌ STILL BROKEN'}")