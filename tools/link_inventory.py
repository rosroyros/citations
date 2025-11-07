#!/usr/bin/env python3
"""
Link Inventory Tool

Extracts all internal links from HTML files and JSX components.
Outputs JSON inventory with source pages and link counts for SEO assessment.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from bs4 import BeautifulSoup
import argparse

def extract_links_from_html(html_path: str) -> List[Dict[str, str]]:
    """Extract internal links from HTML file."""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        soup = BeautifulSoup(content, 'html.parser')
        links = []

        for link in soup.find_all('a', href=True):
            href = link['href'].strip()

            # Skip external links, anchors, mailto, tel
            if (href.startswith('http') and 'citationformatchecker.com' not in href or
                href.startswith('#') or
                href.startswith('mailto:') or
                href.startswith('tel:') or
                href.startswith('javascript:')):
                continue

            # Clean up the URL
            if href.startswith('http'):
                # Extract path from full URL
                href = href.split('citationformatchecker.com/')[-1] if 'citationformatchecker.com' in href else href

            links.append({
                'url': href,
                'text': link.get_text(strip=True),
                'source_file': str(html_path)
            })

        return links

    except Exception as e:
        print(f"Error processing {html_path}: {e}", file=sys.stderr)
        return []

def extract_links_from_jsx(jsx_path: str) -> List[Dict[str, str]]:
    """Extract internal links from JSX files."""
    try:
        with open(jsx_path, 'r', encoding='utf-8') as f:
            content = f.read()

        links = []

        # Find Link components and href attributes
        # Pattern for <Link to="/path">text</Link>
        link_pattern = r'<Link\s+to=["\']([^"\']+)["\'][^>]*>(.*?)</Link>'
        for match in re.finditer(link_pattern, content, re.DOTALL):
            to = match.group(1)
            text = re.sub(r'<[^>]+>', '', match.group(2)).strip()

            if not to.startswith('http') and not to.startswith('#'):
                links.append({
                    'url': to,
                    'text': text,
                    'source_file': str(jsx_path)
                })

        # Pattern for <a href="/path">text</a>
        anchor_pattern = r'<a\s+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
        for match in re.finditer(anchor_pattern, content, re.DOTALL):
            href = match.group(1)
            text = re.sub(r'<[^>]+>', '', match.group(2)).strip()

            if (not href.startswith('http') or
                'citationformatchecker.com' in href):

                if href.startswith('http'):
                    href = href.split('citationformatchecker.com/')[-1] if 'citationformatchecker.com' in href else href

                if not href.startswith('#') and not href.startswith('mailto:') and not href.startswith('tel:'):
                    links.append({
                        'url': href,
                        'text': text,
                        'source_file': str(jsx_path)
                    })

        return links

    except Exception as e:
        print(f"Error processing {jsx_path}: {e}", file=sys.stderr)
        return []

def scan_html_files(directory: str) -> Dict[str, List[Dict[str, str]]]:
    """Scan all HTML files in directory and subdirectories."""
    results = {}
    html_count = 0

    for root, dirs, files in os.walk(directory):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for file in files:
            if file.endswith('.html'):
                html_path = os.path.join(root, file)
                rel_path = os.path.relpath(html_path, directory)

                links = extract_links_from_html(html_path)
                if links:
                    results[rel_path] = links

                html_count += 1

                if html_count % 50 == 0:
                    print(f"Processed {html_count} HTML files...")

    print(f"Scanned {html_count} HTML files")
    return results

def scan_jsx_files(directory: str) -> Dict[str, List[Dict[str, str]]]:
    """Scan all JSX files in directory and subdirectories."""
    results = {}
    jsx_count = 0

    for root, dirs, files in os.walk(directory):
        # Skip node_modules and other common exclusions
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', 'dist', 'build']]

        for file in files:
            if file.endswith('.jsx') or file.endswith('.tsx'):
                jsx_path = os.path.join(root, file)
                rel_path = os.path.relpath(jsx_path, directory)

                links = extract_links_from_jsx(jsx_path)
                if links:
                    results[rel_path] = links

                jsx_count += 1

    print(f"Scanned {jsx_count} JSX/TSX files")
    return results

def generate_inventory(html_results: Dict, jsx_results: Dict) -> Dict:
    """Generate comprehensive inventory with statistics."""
    all_links = []

    # Combine HTML and JSX results
    for source_file, links in html_results.items():
        all_links.extend(links)

    for source_file, links in jsx_results.items():
        all_links.extend(links)

    # Count unique URLs
    unique_urls = set()
    url_counts = {}

    for link in all_links:
        url = link['url']
        unique_urls.add(url)
        url_counts[url] = url_counts.get(url, 0) + 1

    # Generate statistics
    total_links = len(all_links)
    unique_link_count = len(unique_urls)

    # Group links by source type
    html_sources = len(html_results)
    jsx_sources = len(jsx_results) if jsx_results else 0

    inventory = {
        'summary': {
            'total_links': total_links,
            'unique_urls': unique_link_count,
            'html_files_with_links': html_sources,
            'jsx_files_with_links': jsx_sources,
            'scan_date': str(Path.cwd())
        },
        'all_links': all_links,
        'unique_urls': sorted(list(unique_urls)),
        'url_frequency': dict(sorted(url_counts.items(), key=lambda x: x[1], reverse=True)),
        'html_files': html_results,
        'jsx_files': jsx_results or {}
    }

    return inventory

def main():
    parser = argparse.ArgumentParser(description='Extract internal links from HTML and JSX files')
    parser.add_argument('--html-dir', required=True, help='HTML directory to scan')
    parser.add_argument('--jsx-dir', help='JSX directory to scan (optional)')
    parser.add_argument('--output', default='link_inventory.json', help='Output JSON file')

    args = parser.parse_args()

    print("Starting link inventory scan...")
    print(f"HTML directory: {args.html_dir}")
    if args.jsx_dir:
        print(f"JSX directory: {args.jsx_dir}")

    # Scan HTML files
    html_results = scan_html_files(args.html_dir)

    # Scan JSX files if provided
    jsx_results = {}
    if args.jsx_dir:
        jsx_results = scan_jsx_files(args.jsx_dir)

    # Generate inventory
    inventory = generate_inventory(html_results, jsx_results)

    # Save results
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Link inventory saved to: {args.output}")
    print(f"📊 Summary:")
    print(f"   Total links: {inventory['summary']['total_links']}")
    print(f"   Unique URLs: {inventory['summary']['unique_urls']}")
    print(f"   HTML files with links: {inventory['summary']['html_files_with_links']}")
    if inventory['summary']['jsx_files_with_links']:
        print(f"   JSX files with links: {inventory['summary']['jsx_files_with_links']}")

if __name__ == '__main__':
    main()