#!/usr/bin/env python3
"""
Quick validation script to check all MLA pages have correct H1 tags.
Usage: python validate_mla_production.py
"""
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import sys

BASE_URL = "https://citationformatchecker.com"

# Get all MLA URLs from sitemap
def get_mla_urls():
    resp = requests.get(f"{BASE_URL}/sitemap.xml", timeout=10)
    urls = re.findall(r'<loc>(https://citationformatchecker\.com/mla/[^<]+)</loc>', resp.text)
    return urls

def check_page(url):
    """Check a single page for correct H1"""
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return url, "FAIL", f"HTTP {resp.status_code}"
        
        # Extract H1
        h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', resp.text)
        if not h1_match:
            return url, "FAIL", "No H1 found"
        
        h1_text = h1_match.group(1).strip()
        
        # Check if H1 contains MLA
        if 'MLA' in h1_text:
            return url, "PASS", h1_text
        else:
            return url, "FAIL", f"H1 missing MLA: {h1_text}"
    except Exception as e:
        return url, "ERROR", str(e)

def main():
    print("🔍 Fetching MLA URLs from sitemap...")
    urls = get_mla_urls()
    print(f"Found {len(urls)} MLA pages to validate\n")
    
    passed = 0
    failed = 0
    
    print("Validating pages (parallel)...\n")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_page, url): url for url in urls}
        
        for future in as_completed(futures):
            url, status, message = future.result()
            short_url = url.replace(BASE_URL, "")
            
            if status == "PASS":
                passed += 1
                print(f"✅ {short_url}")
            else:
                failed += 1
                print(f"❌ {short_url} - {message}")
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All pages validated successfully!")
        return 0
    else:
        print("⚠️  Some pages need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())
