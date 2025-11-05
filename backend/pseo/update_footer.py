#!/usr/bin/env python3
"""
Script to update footer HTML in existing content/dist files.
Updates footer links and copyright year to match new template.
"""

import os
import re
import glob
from pathlib import Path

def update_footer_in_file(file_path):
    """Update the footer section in a single HTML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if file needs updating (look for 2024 copyright)
        if '&copy; 2024 Citation Checker' in content:
            # Simple approach: replace 2024 with 2025 and add footer links
            # First update the copyright year
            content = content.replace('&copy; 2024 Citation Checker', '&copy; 2025 Citation Checker')

            # Find the footer section and add links
            footer_pattern = r'(<footer class="site-footer">\s*<div class="site-footer-content">\s*<p>&copy; 2025 Citation Checker\. Last updated: [^<]*</p>)(\s*<p class="footer-tagline">Built for researchers, by researchers</p>)'

            new_footer_content = r'\1\n            <p class="footer-links">\n                <a href="/privacy">Privacy Policy</a> |\n                <a href="/terms">Terms of Service</a> |\n                <a href="/contact">Contact Us</a>\n            </p>\2'

            updated_content = re.sub(
                footer_pattern,
                new_footer_content,
                content,
                flags=re.MULTILINE | re.DOTALL
            )

            if updated_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                return True
        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Update all HTML files in content/dist directory."""
    content_dist_dir = Path("/Users/roy/Documents/Projects/citations/content/dist")

    if not content_dist_dir.exists():
        print(f"Error: Directory {content_dist_dir} does not exist")
        return

    # Find all HTML files recursively
    html_files = list(content_dist_dir.rglob("*.html"))

    print(f"Found {len(html_files)} HTML files to process")

    updated_count = 0
    for html_file in html_files:
        if update_footer_in_file(html_file):
            updated_count += 1
            print(f"Updated: {html_file}")
        else:
            print(f"No update needed: {html_file}")

    print(f"\n✅ Completed. Updated {updated_count} out of {len(html_files)} files.")

if __name__ == "__main__":
    main()