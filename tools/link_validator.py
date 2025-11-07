#!/usr/bin/env python3
"""
Link Validation Tool

Validates internal links against known valid URLs from:
- sitemap.xml
- React routes
- Static HTML pages

Categorizes links as: working, broken (404), missing pages (future content)
"""

import json
import os
import re
import sys
import requests
from pathlib import Path
from typing import Dict, List, Set, Tuple
from bs4 import BeautifulSoup
import argparse
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse

def extract_urls_from_sitemap(sitemap_path: str, base_url: str = "https://citationformatchecker.com") -> Set[str]:
    """Extract URLs from sitemap.xml."""
    urls = set()

    try:
        tree = ET.parse(sitemap_path)
        root = tree.getroot()

        # Handle different XML namespaces
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        if root.tag.startswith('{http://www.sitemaps.org'):
            pass  # Use namespace
        else:
            namespace = None  # No namespace

        for url_elem in root.findall('.//url', namespace) if namespace else root.findall('.//url'):
            loc_elem = url_elem.find('loc', namespace) if namespace else url_elem.find('loc')
            if loc_elem is not None:
                full_url = loc_elem.text
                # Extract path from full URL
                parsed = urlparse(full_url)
                path = parsed.path
                if not path.endswith('/'):
                    path += '/'
                urls.add(path)

    except Exception as e:
        print(f"Error parsing sitemap {sitemap_path}: {e}", file=sys.stderr)

    return urls

def extract_react_routes(jsx_dir: str) -> Set[str]:
    """Extract React routes from JSX files."""
    routes = set()

    # Common route patterns in React
    route_patterns = [
        r'path=["\']([^"\']+)["\']',
        r'to=["\']([^"\']+)["\']',
        r'href=["\']([^"\']+)["\']',
    ]

    for root, dirs, files in os.walk(jsx_dir):
        # Skip node_modules and other common exclusions
        dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', 'dist', 'build']]

        for file in files:
            if file.endswith('.jsx') or file.endswith('.tsx') or file.endswith('.js'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    for pattern in route_patterns:
                        for match in re.finditer(pattern, content):
                            route = match.group(1)
                            # Normalize route
                            if not route.startswith('/'):
                                continue
                            if route.startswith('http'):
                                continue
                            if not route.endswith('/'):
                                route += '/'
                            routes.add(route)

                except Exception as e:
                    print(f"Error processing {file_path}: {e}", file=sys.stderr)

    return routes

def extract_static_page_paths(html_dir: str) -> Set[str]:
    """Extract paths from static HTML files."""
    paths = set()

    for root, dirs, files in os.walk(html_dir):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for file in files:
            if file == 'index.html':
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, html_dir)
                dir_path = os.path.dirname(rel_path)

                if dir_path == '':
                    path = '/'
                else:
                    path = '/' + dir_path + '/'

                paths.add(path)

    return paths

def validate_links_http(inventory: Dict, valid_urls: Set[str], base_url: str = "https://citationformatchecker.com") -> Dict:
    """Validate links against valid URLs with HTTP checks."""
    results = {
        'working': [],
        'broken': [],
        'missing_pages': [],
        'invalid_format': [],
        'summary': {}
    }

    # Convert valid_urls to include both with and without trailing slashes
    normalized_valid_urls = set()
    for url in valid_urls:
        normalized_valid_urls.add(url)
        if url.endswith('/') and url != '/':
            normalized_valid_urls.add(url.rstrip('/'))
        elif not url.endswith('/') and url != '/':
            normalized_valid_urls.add(url + '/')

    all_links = inventory.get('all_links', [])

    for i, link in enumerate(all_links):
        url = link['url']
        source_file = link['source_file']
        text = link['text']

        # Skip if it's not an internal link
        if url.startswith('http') and base_url not in url:
            continue

        # Normalize URL
        if url.startswith(base_url):
            url = url.split(base_url)[-1]

        # Basic validation
        if not url.startswith('/'):
            if url not in ['/', '#'] and not url.startswith('mailto:') and not url.startswith('tel:'):
                results['invalid_format'].append({
                    'url': url,
                    'source_file': source_file,
                    'text': text,
                    'error': 'Invalid URL format - must start with /'
                })
            continue

        # Check if URL exists in valid URLs
        if url in normalized_valid_urls:
            results['working'].append({
                'url': url,
                'source_file': source_file,
                'text': text,
                'method': 'sitemap_valid'
            })
        else:
            # Try HTTP validation for missing URLs
            full_url = urljoin(base_url, url)
            try:
                response = requests.head(full_url, timeout=10, allow_redirects=True)
                if response.status_code == 200:
                    results['working'].append({
                        'url': url,
                        'source_file': source_file,
                        'text': text,
                        'method': 'http_valid',
                        'status_code': response.status_code
                    })
                else:
                    results['broken'].append({
                        'url': url,
                        'source_file': source_file,
                        'text': text,
                        'status_code': response.status_code,
                        'error': f'HTTP {response.status_code}'
                    })
            except requests.RequestException as e:
                # Check if this looks like a future content page
                if any(keyword in url.lower() for keyword in ['how-to-', 'cite-', 'guide/']):
                    results['missing_pages'].append({
                        'url': url,
                        'source_file': source_file,
                        'text': text,
                        'potential': True,
                        'error': f'Future content page? (HTTP error: {str(e)})'
                    })
                else:
                    results['broken'].append({
                        'url': url,
                        'source_file': source_file,
                        'text': text,
                        'error': f'HTTP request failed: {str(e)}'
                    })

        # Progress indicator
        if (i + 1) % 500 == 0:
            print(f"Validated {i + 1}/{len(all_links)} links...")

    # Generate summary
    results['summary'] = {
        'total_links': len(all_links),
        'working': len(results['working']),
        'broken': len(results['broken']),
        'missing_pages': len(results['missing_pages']),
        'invalid_format': len(results['invalid_format']),
        'success_rate': len(results['working']) / len(all_links) * 100 if all_links else 0
    }

    return results

def generate_validation_report(results: Dict, output_file: str):
    """Generate comprehensive validation report."""
    report = {
        'scan_date': str(Path.cwd()),
        'summary': results['summary'],
        'detailed_results': results,
        'recommendations': []
    }

    # Generate recommendations
    if results['broken']:
        report['recommendations'].append(f"Fix {len(results['broken'])} broken links to improve user experience")

    if results['missing_pages']:
        report['recommendations'].append(f"Consider creating {len(results['missing_pages'])} missing content pages")

    if results['invalid_format']:
        report['recommendations'].append(f"Fix {len(results['invalid_format'])} links with invalid URL format")

    if results['summary']['success_rate'] < 95:
        report['recommendations'].append("Overall link health needs improvement (success rate < 95%)")

    # Add top broken links
    if results['broken']:
        report['top_broken_links'] = results['broken'][:10]

    # Add top missing pages (high potential)
    if results['missing_pages']:
        report['top_missing_pages'] = [p for p in results['missing_pages'] if p.get('potential')][:10]

    # Save report
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report

def main():
    parser = argparse.ArgumentParser(description='Validate internal links')
    parser.add_argument('--inventory', required=True, help='Link inventory JSON file')
    parser.add_argument('--html-dir', required=True, help='HTML directory for static page detection')
    parser.add_argument('--sitemap', help='Sitemap.xml file path')
    parser.add_argument('--jsx-dir', help='JSX directory for route extraction')
    parser.add_argument('--base-url', default='https://citationformatchecker.com', help='Base URL for HTTP validation')
    parser.add_argument('--output', default='link_validation_report.json', help='Output report file')
    parser.add_argument('--no-http', action='store_true', help='Skip HTTP validation (faster)')

    args = parser.parse_args()

    print("Starting link validation...")
    print(f"Inventory file: {args.inventory}")
    print(f"HTML directory: {args.html_dir}")
    print(f"Base URL: {args.base_url}")

    # Load inventory
    with open(args.inventory, 'r', encoding='utf-8') as f:
        inventory = json.load(f)

    # Build valid URLs list
    valid_urls = set()

    # Extract from sitemap
    if args.sitemap:
        print(f"Extracting URLs from sitemap: {args.sitemap}")
        sitemap_urls = extract_urls_from_sitemap(args.sitemap, args.base_url)
        valid_urls.update(sitemap_urls)
        print(f"Found {len(sitemap_urls)} URLs in sitemap")

    # Extract static page paths
    print(f"Extracting static page paths from: {args.html_dir}")
    static_paths = extract_static_page_paths(args.html_dir)
    valid_urls.update(static_paths)
    print(f"Found {len(static_paths)} static page paths")

    # Extract React routes
    if args.jsx_dir:
        print(f"Extracting React routes from: {args.jsx_dir}")
        react_routes = extract_react_routes(args.jsx_dir)
        valid_urls.update(react_routes)
        print(f"Found {len(react_routes)} React routes")

    print(f"Total valid URLs: {len(valid_urls)}")

    # Validate links
    if args.no_http:
        print("Skipping HTTP validation (faster mode)")
        # Just check against valid_urls list
        results = {'working': [], 'broken': [], 'missing_pages': [], 'invalid_format': [], 'summary': {}}
        all_links = inventory.get('all_links', [])

        normalized_valid_urls = set()
        for url in valid_urls:
            normalized_valid_urls.add(url)
            if url.endswith('/') and url != '/':
                normalized_valid_urls.add(url.rstrip('/'))
            elif not url.endswith('/') and url != '/':
                normalized_valid_urls.add(url + '/')

        for link in all_links:
            url = link['url']
            if url.startswith(args.base_url):
                url = url.split(args.base_url)[-1]

            if not url.startswith('/'):
                if url not in ['/', '#'] and not url.startswith('mailto:') and not url.startswith('tel:'):
                    results['invalid_format'].append({
                        'url': url,
                        'source_file': link['source_file'],
                        'text': link['text'],
                        'error': 'Invalid URL format - must start with /'
                    })
            elif url in normalized_valid_urls:
                results['working'].append({
                    'url': url,
                    'source_file': link['source_file'],
                    'text': link['text'],
                    'method': 'sitemap_valid'
                })
            else:
                if any(keyword in url.lower() for keyword in ['how-to-', 'cite-', 'guide/']):
                    results['missing_pages'].append({
                        'url': url,
                        'source_file': link['source_file'],
                        'text': link['text'],
                        'potential': True,
                        'error': 'Missing from sitemap/static pages'
                    })
                else:
                    results['broken'].append({
                        'url': url,
                        'source_file': link['source_file'],
                        'text': link['text'],
                        'error': 'Not found in valid URLs'
                    })

        results['summary'] = {
            'total_links': len(all_links),
            'working': len(results['working']),
            'broken': len(results['broken']),
            'missing_pages': len(results['missing_pages']),
            'invalid_format': len(results['invalid_format']),
            'success_rate': len(results['working']) / len(all_links) * 100 if all_links else 0
        }
    else:
        print("Performing HTTP validation (slower but more accurate)...")
        results = validate_links_http(inventory, valid_urls, args.base_url)

    # Generate report
    print("Generating validation report...")
    report = generate_validation_report(results, args.output)

    print(f"\n✅ Link validation report saved to: {args.output}")
    print(f"📊 Summary:")
    print(f"   Total links: {report['summary']['total_links']}")
    print(f"   Working: {report['summary']['working']} ({report['summary']['success_rate']:.1f}%)")
    print(f"   Broken: {report['summary']['broken']}")
    print(f"   Missing pages: {report['summary']['missing_pages']}")
    print(f"   Invalid format: {report['summary']['invalid_format']}")

    if report['recommendations']:
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"   {i}. {rec}")

if __name__ == '__main__':
    main()