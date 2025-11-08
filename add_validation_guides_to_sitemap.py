#!/usr/bin/env python3
"""
Add 11 new validation guides to sitemap.xml
Run this locally before deploying
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from pseo.utils.sitemap_generator import SitemapGenerator

def main():
    # Path to local sitemap
    sitemap_path = Path("frontend/frontend/public/sitemap.xml")

    if not sitemap_path.exists():
        print(f"❌ Sitemap not found at {sitemap_path}")
        return False

    # Initialize sitemap generator
    sitemap_gen = SitemapGenerator(
        sitemap_path=str(sitemap_path),
        base_url="https://citationformatchecker.com"
    )

    # Get current entries
    existing_entries = sitemap_gen._parse_existing_sitemap()
    print(f"📊 Current sitemap has {len(existing_entries)} URLs")

    # 11 new validation guides
    new_guides = [
        "how-to-check-ampersand-apa",
        "how-to-check-citation-consistency-apa",
        "how-to-check-et-al-apa",
        "how-to-check-publisher-apa",
        "how-to-check-reference-list-apa",
        "how-to-check-volume-issue-apa",
        "how-to-validate-date-formatting-apa",
        "how-to-validate-hanging-indents-apa",
        "how-to-validate-in-text-citations-apa",
        "how-to-validate-url-apa",
        "how-to-verify-alphabetization-apa"
    ]

    # Create entries
    entries = [{
        "url": f"https://citationformatchecker.com/{guide}/",
        "lastmod": "2025-11-07",
        "changefreq": "monthly",
        "priority": "0.7"
    } for guide in new_guides]

    print(f"\n📝 Adding {len(entries)} new validation guides to sitemap...")
    for entry in entries:
        print(f"   • {entry['url']}")

    # Add to sitemap
    success = sitemap_gen.add_entries_to_sitemap(entries, str(sitemap_path))

    if success:
        print(f"\n✅ Successfully added {len(entries)} guides to sitemap.xml")

        # Verify they were added
        updated_entries = sitemap_gen._parse_existing_sitemap()
        print(f"✅ Sitemap now has {len(updated_entries)} URLs (was {len(existing_entries)})")

        added_count = len(updated_entries) - len(existing_entries)
        if added_count == len(entries):
            print(f"✅ Verified: All {len(entries)} guides were added successfully")
            return True
        else:
            print(f"⚠️  Warning: Expected {len(entries)} new entries, but got {added_count}")
            return False
    else:
        print("❌ Failed to update sitemap")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
