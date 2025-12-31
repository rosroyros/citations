#!/usr/bin/env python3
"""Merge MLA PSEO pages into main sitemap.

Creates a backup before merging and auto-detects all MLA pages.
Runs during deployment before Vite build.
"""
import sys
import shutil
from pathlib import Path
from datetime import datetime

# Setup paths
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.pseo.utils.sitemap_generator import SitemapGenerator

BASE_URL = "https://citationformatchecker.com"
SITEMAP_PATH = project_root / "frontend/frontend/public/sitemap.xml"
MLA_DIST = project_root / "content/dist/mla"


def backup_sitemap():
    """Create timestamped backup of sitemap before modification."""
    if not SITEMAP_PATH.exists():
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = SITEMAP_PATH.parent / f"sitemap.xml.backup.{timestamp}"
    shutil.copy2(SITEMAP_PATH, backup_path)
    print(f"📦 Backup created: {backup_path.name}")
    return backup_path


def scan_mla_pages():
    """Scan MLA dist folder and generate sitemap entries."""
    entries = []
    today = datetime.now().strftime("%Y-%m-%d")
    
    if not MLA_DIST.exists():
        return entries
    
    for page_dir in MLA_DIST.iterdir():
        if not page_dir.is_dir():
            continue
        
        name = page_dir.name
        
        # Handle /mla/guide/* subdirectories
        if name == "guide":
            for subdir in page_dir.iterdir():
                if subdir.is_dir() and (subdir / "index.html").exists():
                    entries.append({
                        "url": f"{BASE_URL}/mla/guide/{subdir.name}/",
                        "lastmod": today,
                        "changefreq": "weekly",
                        "priority": "0.9"
                    })
        # Handle /mla/cite-* and /mla/how-to-cite-* pages
        elif (page_dir / "index.html").exists():
            entries.append({
                "url": f"{BASE_URL}/mla/{name}/",
                "lastmod": today,
                "changefreq": "weekly",
                "priority": "0.8"
            })
    
    return entries


def main():
    print("🗺️  MLA Sitemap Merge")
    print("=" * 40)
    
    # Scan for MLA pages
    entries = scan_mla_pages()
    
    if not entries:
        print("ℹ️  No MLA pages found in content/dist/mla/")
        return
    
    print(f"📍 Found {len(entries)} MLA pages")
    
    # Create backup before modifying
    backup_sitemap()
    
    # Merge entries into sitemap
    generator = SitemapGenerator(str(SITEMAP_PATH), BASE_URL)
    success = generator.add_entries_to_sitemap(entries)
    
    if success:
        print(f"✅ Sitemap updated with {len(entries)} MLA entries")
    else:
        print("❌ Failed to update sitemap")
        sys.exit(1)


if __name__ == "__main__":
    main()
