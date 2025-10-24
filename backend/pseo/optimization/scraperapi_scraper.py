"""
Simple ScraperAPI integration for citation extraction
"""
import requests
import os
from typing import Optional
import logging
from dotenv import load_dotenv

# Load environment variables from project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

logger = logging.getLogger(__name__)

class ScraperAPIClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('SCRAPERAPI_API_KEY')
        self.base_url = 'http://api.scraperapi.com'

        
        if not self.api_key:
            raise ValueError("ScraperAPI key required. Set SCRAPERAPI_API_KEY environment variable or pass api_key parameter")

    def scrape_url(self, url: str, **kwargs) -> str:
        """
        Scrape a URL using ScraperAPI

        Args:
            url: URL to scrape
            **kwargs: Additional parameters (render_js, country_code, etc.)

        Returns:
            Raw HTML content as string
        """
        params = {
            'api_key': self.api_key,
            'url': url,
            **kwargs
        }

        try:
            logger.info(f"Scraping URL with ScraperAPI: {url}")
            response = requests.get(self.base_url, params=params, timeout=60)
            response.raise_for_status()

            html_content = response.text
            logger.info(f"Successfully scraped {len(html_content)} characters from {url}")
            return html_content

        except requests.exceptions.RequestException as e:
            logger.error(f"Error scraping {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
            raise

    def scrape_with_render(self, url: str) -> str:
        """
        Scrape URL with JavaScript rendering enabled
        """
        return self.scrape_url(url, render_js=1)