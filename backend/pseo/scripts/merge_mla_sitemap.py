#!/usr/bin/env python3
"""Merge MLA PSEO pages into main sitemap.

Creates a backup before merging and auto-detects all MLA pages.
Runs during deployment before Vite build.

Note: Uses custom XML parsing because SitemapGenerator has a namespace bug.
"""
import sys
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from xml.dom import minidom

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

BASE_URL = "https://citationformatchecker.com"
SITEMAP_PATH = project_root / "frontend/frontend/public/sitemap.xml"
MLA_DIST = project_root / "content/dist/mla"
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


def backup_sitemap():
    """Create timestamped backup of sitemap before modification."""
    if not SITEMAP_PATH.exists():
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = SITEMAP_PATH.parent / f"sitemap.xml.backup.{timestamp}"
    shutil.copy2(SITEMAP_PATH, backup_path)
    print(f"📦 Backup created: {backup_path.name}")
    return backup_path


def parse_existing_sitemap():
    """Parse existing sitemap using correct namespace handling."""
    entries = []
    if not SITEMAP_PATH.exists():
        return entries
    
    try:
        tree = ET.parse(SITEMAP_PATH)
        root = tree.getroot()
        
        # Use full namespace format that ElementTree requires
        for url in root.findall(f'{{{NS}}}url'):
            loc = url.find(f'{{{NS}}}loc')
            if loc is None or not loc.text:
                continue
            
            lastmod = url.find(f'{{{NS}}}lastmod')
            changefreq = url.find(f'{{{NS}}}changefreq')
            priority = url.find(f'{{{NS}}}priority')
            
            entries.append({
                'url': loc.text,
                'lastmod': lastmod.text if lastmod is not None else None,
                'changefreq': changefreq.text if changefreq is not None else 'weekly',
                'priority': priority.text if priority is not None else '0.5'
            })
        
        print(f"📖 Parsed {len(entries)} existing entries")
    except Exception as e:
        print(f"⚠️  Could not parse existing sitemap: {e}")
    
    return entries


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
        
        if name == "guide":
            for subdir in page_dir.iterdir():
                if subdir.is_dir() and (subdir / "index.html").exists():
                    entries.append({
                        "url": f"{BASE_URL}/mla/guide/{subdir.name}/",
                        "lastmod": today,
                        "changefreq": "weekly",
                        "priority": "0.9"
                    })
        elif (page_dir / "index.html").exists():
            entries.append({
                "url": f"{BASE_URL}/mla/{name}/",
                "lastmod": today,
                "changefreq": "weekly",
                "priority": "0.8"
            })
    
    return entries


def deduplicate(entries):
    """Remove duplicates, keeping last occurrence."""
    seen = {}
    for entry in entries:
        seen[entry['url']] = entry
    return list(seen.values())


def generate_sitemap_xml(entries):
    """Generate sitemap XML from entries."""
    urlset = ET.Element('urlset', {
        'xmlns': NS,
        'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xsi:schemaLocation': f'{NS} {NS}/sitemap.xsd'
    })
    
    for entry in entries:
        url = ET.SubElement(urlset, 'url')
        ET.SubElement(url, 'loc').text = entry['url']
        if entry.get('lastmod'):
            ET.SubElement(url, 'lastmod').text = entry['lastmod']
        if entry.get('changefreq'):
            ET.SubElement(url, 'changefreq').text = entry['changefreq']
        if entry.get('priority'):
            ET.SubElement(url, 'priority').text = entry['priority']
    
    rough = ET.tostring(urlset, encoding='unicode')
    return minidom.parseString(rough).toprettyxml(indent="  ")


def main():
    print("🗺️  MLA Sitemap Merge")
    print("=" * 40)
    
    # Scan for MLA pages
    mla_entries = scan_mla_pages()
    if not mla_entries:
        print("ℹ️  No MLA pages found")
        return
    
    print(f"📍 Found {len(mla_entries)} MLA pages")
    
    # Backup before modifying
    backup_sitemap()
    
    # Parse existing entries
    existing = parse_existing_sitemap()
    
    # Merge and deduplicate
    all_entries = existing + mla_entries
    unique = deduplicate(all_entries)
    
    print(f"📊 Total unique entries: {len(unique)}")
    
    # Generate and write
    xml = generate_sitemap_xml(unique)
    SITEMAP_PATH.write_text(xml, encoding='utf-8')
    
    print(f"✅ Sitemap updated ({len(existing)} existing + {len(mla_entries)} MLA)")


if __name__ == "__main__":
    main()
