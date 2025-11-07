#!/usr/bin/env python3
"""
Add /guides/ entry to sitemap.xml
Run this on the VPS after deploying the guides page
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from pseo.utils.sitemap_generator import SitemapGenerator

def main():
    # Path to production sitemap
    sitemap_path = Path("/opt/citations/content/dist/sitemap.xml")

    if not sitemap_path.exists():
        print(f"❌ Sitemap not found at {sitemap_path}")
        return False

    # Initialize sitemap generator
    sitemap_gen = SitemapGenerator(
        sitemap_path=str(sitemap_path),
        base_url="https://citationformatchecker.com"
    )

    # Create entry for /guides/ page
    guides_entry = {
        "url": "https://citationformatchecker.com/guides/",
        "lastmod": "2025-11-07",
        "changefreq": "monthly",
        "priority": "1.0"  # High priority - 249 incoming links
    }

    print("📝 Adding /guides/ to sitemap...")
    print(f"   URL: {guides_entry['url']}")
    print(f"   Priority: {guides_entry['priority']} (249 incoming links)")

    # Add to sitemap
    success = sitemap_gen.add_entries_to_sitemap([guides_entry])

    if success:
        print("✅ Successfully added /guides/ to sitemap.xml")

        # Verify it was added
        entries = sitemap_gen._parse_existing_sitemap()
        guides_in_sitemap = any(e['url'] == guides_entry['url'] for e in entries)

        if guides_in_sitemap:
            print(f"✅ Verified: /guides/ is now in sitemap ({len(entries)} total entries)")
            return True
        else:
            print("⚠️  Warning: Could not verify /guides/ was added")
            return False
    else:
        print("❌ Failed to update sitemap")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
