#!/usr/bin/env python3
"""
Test ScrapingBee API connectivity and Purdue OWL accessibility
"""

import os
from scrapingbee import ScrapingBeeClient

def test_scrapingbee_api():
    """Test ScrapingBee API with provided key"""

    # API key from user
    api_key = "LIBY0CW5QYMS826LW2M3YPF97V3RT7H7I89EFIISANIKDV5LWYF27N8K4JNPZA9AURXUJVRZYYQWARUR"

    # Initialize client
    client = ScrapingBeeClient(api_key=api_key)

    # Test URL - Purdue OWL main page
    test_url = "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_articles_in_periodicals.html"

    print("Testing ScrapingBee API connectivity...")
    print(f"API Key: {api_key[:20]}...")
    print(f"Test URL: {test_url}")

    try:
        # Make request
        response = client.get(
            test_url,
            params={
                'render_js': True,
                'premium_proxy': True,
                'country_code': 'us'
            }
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response Size: {len(response.content)} bytes")

        if response.status_code == 200:
            # Check for expected content
            content = response.text
            if "APA Style" in content and "Reference List" in content:
                print("✅ SUCCESS: Purdue OWL content retrieved successfully")

                # Look for citation examples
                if "Author, A. A." in content or "doi:" in content:
                    print("✅ SUCCESS: Citation examples found in content")
                else:
                    print("⚠️  WARNING: Citation examples not immediately visible")

                return True
            else:
                print("❌ ERROR: Expected APA content not found")
                return False
        else:
            print(f"❌ ERROR: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            return False

    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        return False

def test_multiple_pages():
    """Test accessibility of multiple Purdue OWL pages"""

    api_key = "LIBY0CW5QYMS826LW2M3YPF97V3RT7H7I89EFIISANIKDV5LWYF27N8K4JNPZA9AURXUJVRZYYQWARUR"
    client = ScrapingBeeClient(api_key=api_key)

    # Target pages for expansion (correct URLs)
    test_urls = [
        "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_articles_in_periodicals.html",
        "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_books.html",
        "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_electronic_sources.html",
        "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_audiovisual_media.html",
        "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_other_print_sources.html",
        "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/reference_list_other_non_print_sources.html"
    ]

    print("\nTesting multiple Purdue OWL pages...")

    results = {}
    for url in test_urls:
        try:
            response = client.get(
                url,
                params={
                    'render_js': True,
                    'premium_proxy': True,
                    'country_code': 'us'
                }
            )

            page_name = url.split('/')[-1].replace('.html', '')
            results[page_name] = {
                'status': response.status_code,
                'size': len(response.content),
                'success': response.status_code == 200 and "APA" in response.text
            }

            print(f"  {page_name}: {'✅' if results[page_name]['success'] else '❌'} ({response.status_code})")

        except Exception as e:
            page_name = url.split('/')[-1].replace('.html', '')
            results[page_name] = {
                'status': 'ERROR',
                'size': 0,
                'success': False,
                'error': str(e)
            }
            print(f"  {page_name}: ❌ ERROR - {e}")

    return results

if __name__ == "__main__":
    # Test basic connectivity
    basic_test = test_scrapingbee_api()

    if basic_test:
        # Test multiple pages
        multi_test = test_multiple_pages()
        print(f"\n✅ Setup complete - {sum(1 for r in multi_test.values() if r['success'])}/{len(multi_test)} pages accessible")
    else:
        print("\n❌ Basic connectivity failed - check API key or network")