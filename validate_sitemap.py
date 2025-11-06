#!/usr/bin/env python3
"""
Sitemap URL Validator

Validates all URLs in sitemap.xml are accessible and serve proper content.
Checks for:
- HTTP 200 status
- No redirects to homepage
- Contains meaningful content (not blank/homepage)
- Proper page structure
"""

import sys
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Tuple
import json
import time
from datetime import datetime
import re

class SitemapValidator:
    def __init__(self, sitemap_url: str = "https://citationformatchecker.com/sitemap.xml", sitemap_file: str = None):
        """
        Initialize the validator

        Args:
            sitemap_url: URL to the sitemap.xml
            sitemap_file: Local path to sitemap.xml file
        """
        self.sitemap_url = sitemap_url
        self.sitemap_file = sitemap_file
        self.base_domain = "https://citationformatchecker.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; SitemapValidator/1.0)'
        })

    def fetch_sitemap(self) -> List[str]:
        """
        Fetch and parse sitemap to extract URLs

        Returns:
            List of URLs from sitemap
        """
        # If local file is provided, use it
        if self.sitemap_file:
            try:
                with open(self.sitemap_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                root = ET.fromstring(content)
                return self._extract_urls_from_root(root)
            except Exception as e:
                print(f"Error reading local sitemap file: {str(e)}")
                return []

        # Otherwise fetch from URL
        try:
            response = self.session.get(self.sitemap_url, timeout=30)
            response.raise_for_status()

            root = ET.fromstring(response.content)

            return self._extract_urls_from_root(root)

        except Exception as e:
            print(f"Error fetching sitemap: {str(e)}")
            return []

    def _extract_urls_from_root(self, root) -> List[str]:
        """
        Extract URLs from parsed sitemap root

        Args:
            root: Parsed XML root element

        Returns:
            List of URLs
        """
        # Handle both sitemap index and urlset
        if root.tag.endswith('sitemapindex'):
            # Sitemap index - fetch all child sitemaps
            urls = []
            for sitemap in root.findall('sitemap'):
                loc = sitemap.find('loc')
                if loc is not None:
                    child_urls = self.fetch_child_sitemap(loc.text)
                    urls.extend(child_urls)
            return urls
        elif root.tag.endswith('urlset'):
            # URL set - extract URLs directly
            urls = []
            # Handle namespace
            ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            if '}' in root.tag:
                # Has namespace
                for url in root.findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                    loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    if loc is not None:
                        urls.append(loc.text.strip())
            else:
                # No namespace
                for url in root.findall('url'):
                    loc = url.find('loc')
                    if loc is not None:
                        urls.append(loc.text.strip())
            return urls
        else:
            print(f"Unknown sitemap format: {root.tag}")
            return []

    def fetch_child_sitemap(self, sitemap_url: str) -> List[str]:
        """
        Fetch a child sitemap and extract URLs

        Args:
            sitemap_url: URL of child sitemap

        Returns:
            List of URLs from child sitemap
        """
        try:
            response = self.session.get(sitemap_url, timeout=30)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            urls = []

            for url in root.findall('url'):
                loc = url.find('loc')
                if loc is not None:
                    urls.append(loc.text.strip())

            return urls

        except Exception as e:
            print(f"Warning: Could not fetch child sitemap {sitemap_url}: {str(e)}")
            return []

    def validate_url(self, url: str) -> Dict:
        """
        Validate a single URL

        Args:
            url: URL to validate

        Returns:
            Dictionary with validation results
        """
        result = {
            'url': url,
            'status_code': None,
            'final_url': None,
            'redirect_count': 0,
            'content_length': 0,
            'has_title': False,
            'has_content': False,
            'is_homepage': False,
            'error': None,
            'issues': []
        }

        try:
            # Make request with redirect tracking
            response = self.session.get(
                url,
                timeout=30,
                allow_redirects=True,
                stream=True  # Don't download full content immediately
            )

            result['status_code'] = response.status_code
            result['final_url'] = response.url
            result['redirect_count'] = len(response.history)

            # Check if redirected to homepage
            if response.url.rstrip('/') == self.base_domain.rstrip('/'):
                result['is_homepage'] = True
                result['issues'].append('Redirects to homepage')

            # Only check content if we get a 200 OK
            if response.status_code == 200:
                # Get content
                content = response.text
                result['content_length'] = len(content)

                # Check for HTML title
                if '<title>' in content and '</title>' in content:
                    title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
                    if title_match and title_match.group(1).strip():
                        result['has_title'] = True

                # Check for meaningful content (not just navigation/blank page)
                # Look for substantive content patterns
                content_patterns = [
                    r'<h[1-6][^>]*>.*?</h[1-6]>',  # Headers
                    r'<p[^>]*>.*?</p>',           # Paragraphs
                    r'data-citation-',           # Citation-specific content
                    r'citation-form',            # Citation form
                    r'guide-section',            # Guide content
                ]

                has_meaningful = False
                for pattern in content_patterns:
                    if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                        # Additional check that paragraph/header has actual text
                        if pattern.startswith(r'<h'):
                            header_text = re.search(r'<h[1-6][^>]*>([^<]+)', content, re.IGNORECASE)
                            if header_text and len(header_text.group(1).strip()) > 3:
                                has_meaningful = True
                                break
                        elif pattern.startswith(r'<p'):
                            para_text = re.search(r'<p[^>]*>([^<]+)', content, re.IGNORECASE)
                            if para_text and len(para_text.group(1).strip()) > 10:
                                has_meaningful = True
                                break
                        else:
                            has_meaningful = True
                            break

                result['has_content'] = has_meaningful

                if not has_meaningful:
                    result['issues'].append('No meaningful content detected')

                # Check for common error indicators
                error_indicators = [
                    '404 not found',
                    'page not found',
                    'error 404',
                    'redirecting...',
                    'access denied',
                    'internal server error'
                ]

                content_lower = content.lower()
                for indicator in error_indicators:
                    if indicator in content_lower:
                        result['issues'].append(f'Error indicator in content: {indicator}')

            else:
                result['issues'].append(f'HTTP {response.status_code}')

        except requests.exceptions.Timeout:
            result['error'] = 'Timeout'
            result['issues'].append('Request timeout')
        except requests.exceptions.ConnectionError:
            result['error'] = 'Connection error'
            result['issues'].append('Connection failed')
        except Exception as e:
            result['error'] = str(e)
            result['issues'].append(f'Validation error: {str(e)}')

        return result

    def validate_all_urls(self, max_urls: int = None, delay: float = 0.5) -> Dict:
        """
        Validate all URLs in sitemap

        Args:
            max_urls: Maximum number of URLs to validate (None for all)
            delay: Delay between requests in seconds

        Returns:
            Dictionary with validation summary and results
        """
        print("Fetching sitemap URLs...")
        urls = self.fetch_sitemap()

        if not urls:
            return {
                'success': False,
                'error': 'Could not fetch sitemap',
                'results': []
            }

        if max_urls:
            urls = urls[:max_urls]

        print(f"Validating {len(urls)} URLs...")

        results = []
        issues_by_type = {}

        for i, url in enumerate(urls, 1):
            print(f"Validating {i}/{len(urls)}: {url}")

            result = self.validate_url(url)
            results.append(result)

            # Categorize issues
            if result['issues']:
                for issue in result['issues']:
                    if issue not in issues_by_type:
                        issues_by_type[issue] = []
                    issues_by_type[issue].append(url)

            # Rate limiting
            if delay > 0 and i < len(urls):
                time.sleep(delay)

        # Calculate summary
        summary = {
            'total_urls': len(results),
            'successful': len([r for r in results if r['status_code'] == 200 and not r['issues']]),
            'http_errors': len([r for r in results if r['status_code'] and r['status_code'] >= 400]),
            'redirect_to_home': len([r for r in results if r['is_homepage']]),
            'no_content': len([r for r in results if not r['has_content'] and r['status_code'] == 200]),
            'other_issues': len([r for r in results if r['issues'] and r['status_code'] == 200]),
            'issues_by_type': issues_by_type
        }

        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'summary': summary,
            'results': results
        }

    def generate_report(self, validation_result: Dict, output_file: str = None) -> str:
        """
        Generate a validation report

        Args:
            validation_result: Result from validate_all_urls
            output_file: Optional file to save report

        Returns:
            Report as string
        """
        if not validation_result['success']:
            report = f"Validation failed: {validation_result['error']}"
        else:
            summary = validation_result['summary']

            report = f"""
# Sitemap Validation Report
Generated: {validation_result['timestamp']}

## Summary
- Total URLs: {summary['total_urls']}
- Successful: {summary['successful']}
- HTTP Errors: {summary['http_errors']}
- Redirect to Homepage: {summary['redirect_to_home']}
- No Meaningful Content: {summary['no_content']}
- Other Issues: {summary['other_issues']}

## Issues by Type
"""

            for issue_type, urls in summary['issues_by_type'].items():
                report += f"\n### {issue_type} ({len(urls)} URLs)\n"
                for url in urls[:10]:  # Show first 10
                    report += f"- {url}\n"
                if len(urls) > 10:
                    report += f"- ... and {len(urls) - 10} more\n"

            # Add detailed results for problematic URLs
            report += "\n## Detailed Issues\n"
            for result in validation_result['results']:
                if result['issues'] or (result['status_code'] and result['status_code'] >= 400):
                    report += f"\n### {result['url']}\n"
                    report += f"- Status: {result['status_code']}\n"
                    if result['final_url'] != result['url']:
                        report += f"- Redirected to: {result['final_url']}\n"
                    if result['issues']:
                        report += f"- Issues: {', '.join(result['issues'])}\n"

        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            print(f"Report saved to: {output_file}")

        return report


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description='Validate sitemap URLs')
    parser.add_argument('--sitemap', default='https://citationformatchecker.com/sitemap.xml',
                       help='Sitemap URL to validate')
    parser.add_argument('--sitemap-file', help='Local sitemap file to validate')
    parser.add_argument('--max-urls', type=int, help='Maximum URLs to validate')
    parser.add_argument('--delay', type=float, default=0.5,
                       help='Delay between requests (seconds)')
    parser.add_argument('--output', help='Output file for report')
    parser.add_argument('--json', help='Output JSON file for detailed results')

    args = parser.parse_args()

    validator = SitemapValidator(args.sitemap, args.sitemap_file)

    # Run validation
    result = validator.validate_all_urls(
        max_urls=args.max_urls,
        delay=args.delay
    )

    # Generate text report
    report = validator.generate_report(result, args.output)
    print("\n" + "="*50)
    print(report)

    # Save JSON results if requested
    if args.json:
        with open(args.json, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nDetailed results saved to: {args.json}")

    # Exit with error code if issues found
    if result['success'] and result['summary']['http_errors'] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()