#!/usr/bin/env python3
"""
Clean sitemap by removing duplicates and malformed URLs using existing SitemapGenerator
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from pseo.utils.sitemap_generator import SitemapGenerator
from pathlib import Path
import xml.etree.ElementTree as ET

def manual_parse_sitemap(sitemap_file):
    """Manually parse sitemap with namespace handling"""
    try:
        tree = ET.parse(sitemap_file)
        root = tree.getroot()

        # Handle namespace
        ns = {'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        entries = []
        for url in root.findall('.//sitemap:url', ns):
            loc = url.find('.//sitemap:loc', ns)
            if loc is not None:
                lastmod = url.find('.//sitemap:lastmod', ns)
                changefreq = url.find('.//sitemap:changefreq', ns)
                priority = url.find('.//sitemap:priority', ns)

                entry = {
                    'url': loc.text,
                    'lastmod': lastmod.text if lastmod is not None else None,
                    'changefreq': changefreq.text if changefreq is not None else 'monthly',
                    'priority': priority.text if priority is not None else '0.5'
                }
                entries.append(entry)

        return entries
    except Exception as e:
        print(f"Error parsing sitemap: {e}")
        return []

def clean_sitemap():
    """Clean the current sitemap by removing duplicates and malformed URLs"""

    # Backup path and current sitemap path
    backup_file = "backup/sitemap_backup_20251105_224825.xml"
    current_sitemap_path = "frontend/frontend/dist/sitemap.xml"

    print("🧹 Cleaning sitemap...")

    # Initialize SitemapGenerator with correct base URL
    sitemap_gen = SitemapGenerator(
        sitemap_path=current_sitemap_path,
        base_url="https://citationformatchecker.com"
    )

    # Load the backup sitemap (current live version)
    sitemap_gen.sitemap_path = Path(backup_file)

    # Parse existing entries
    print("📖 Parsing existing sitemap entries...")
    existing_entries = sitemap_gen._parse_existing_sitemap()
    print(f"   Found {len(existing_entries)} total entries")

    # If parsing failed, try manual parsing
    if len(existing_entries) == 0:
        print("⚠️  Standard parsing failed, trying manual parsing...")
        existing_entries = manual_parse_sitemap(backup_file)
        print(f"   Manual parsing found {len(existing_entries)} entries")

    # Show issues before cleaning
    print("\n🔍 Issues found:")

    # Count malformed URLs
    malformed_count = sum(1 for entry in existing_entries
                         if '/cite-/cite-' in entry['url'] or not entry['url'].startswith('http'))
    print(f"   - Malformed URLs: {malformed_count}")

    # Show specific malformed URLs
    malformed_urls = [entry['url'] for entry in existing_entries if '/cite-/cite-' in entry['url']]
    for url in malformed_urls:
        print(f"     {url}")

    # Count duplicates
    urls = [entry['url'] for entry in existing_entries]
    unique_urls = set(urls)
    duplicate_count = len(urls) - len(unique_urls)
    print(f"   - Duplicate URLs: {duplicate_count}")

    # Remove malformed entries
    print("\n🗑️  Removing malformed URLs...")
    clean_entries = [entry for entry in existing_entries
                    if '/cite-/cite-' not in entry['url']
                    and entry['url'].startswith('http')]
    print(f"   Removed {len(existing_entries) - len(clean_entries)} malformed entries")

    # Deduplicate entries
    print("🔧 Removing duplicate URLs...")
    unique_entries = sitemap_gen._deduplicate_entries(clean_entries)
    print(f"   Deduplicated {len(clean_entries)} entries to {len(unique_entries)} unique entries")

    # Generate cleaned sitemap
    print("📝 Generating cleaned sitemap...")
    sitemap_xml = sitemap_gen._generate_sitemap_xml(unique_entries)

    # Write cleaned sitemap to new file
    cleaned_sitemap_path = "backup/sitemap_cleaned.xml"
    with open(cleaned_sitemap_path, 'w', encoding='utf-8') as f:
        f.write(sitemap_xml)

    print(f"\n✅ Cleaned sitemap saved to: {cleaned_sitemap_path}")
    print(f"   Original entries: {len(existing_entries)}")
    print(f"   Cleaned entries:  {len(unique_entries)}")
    print(f"   Removed:          {len(existing_entries) - len(unique_entries)}")

    return cleaned_sitemap_path

if __name__ == "__main__":
    cleaned_file = clean_sitemap()
    print(f"\n🎯 Next step: Replace live sitemap with {cleaned_file}")