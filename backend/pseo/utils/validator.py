#!/usr/bin/env python3
"""
Validation utilities to prevent deployment issues
"""

import re
import os
from typing import Dict, List, Any

class DeploymentValidator:
    """Validates critical elements before deployment"""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_google_analytics(self, template_content: str) -> bool:
        """Check if Google Analytics uses real ID (not placeholder)"""

        # Check for placeholder GA IDs
        placeholder_patterns = [
            r'GA_MEASUREMENT_ID',
            r'GA_MEASUREMENT_ID_HERE',
            r'YOUR_GA_ID',
            r'google-analytics-id'
        ]

        for pattern in placeholder_patterns:
            if re.search(pattern, template_content, re.IGNORECASE):
                self.errors.append(f"Google Analytics placeholder found: {pattern}")
                return False

        # Check for valid GA format (G-XXXXXXXXXX or UA-XXXXXXXX-X)
        ga_pattern = r"['\"](G-\w{10}|UA-\d{4}-\d)['\"]"
        matches = re.findall(ga_pattern, template_content)

        if not matches:
            self.warnings.append("No valid Google Analytics ID format found")
            return False

        return True

    def validate_url_format(self, url: str, expected_pattern: str = None) -> bool:
        """Validate URL format follows expected pattern"""

        # Basic URL validation
        url_pattern = r'^https?://[^/]+/.*'
        if not re.match(url_pattern, url):
            self.errors.append(f"Invalid URL format: {url}")
            return False

        # Check for expected pattern if provided
        if expected_pattern and not re.match(expected_pattern, url):
            self.errors.append(f"URL doesn't match expected pattern {expected_pattern}: {url}")
            return False

        return True

    def validate_sitemap_urls(self, sitemap_content: str, deployed_urls: List[str]) -> bool:
        """Check if sitemap URLs match deployed URLs"""

        # Extract URLs from sitemap
        sitemap_urls = re.findall(r'<loc>(https://[^<]+)</loc>', sitemap_content)

        missing_in_sitemap = []
        missing_in_deployment = []

        deployed_set = set(deployed_urls)
        sitemap_set = set(sitemap_urls)

        missing_in_sitemap = deployed_set - sitemap_set
        missing_in_deployment = sitemap_set - deployed_set

        if missing_in_sitemap:
            self.errors.append(f"Deployed URLs missing from sitemap: {missing_in_sitemap}")

        if missing_in_deployment:
            self.warnings.append(f"Sitemap URLs not deployed: {missing_in_deployment}")

        return len(missing_in_sitemap) == 0

    def validate_specific_source_config(self, config: Dict[str, Any]) -> bool:
        """Validate specific source configuration"""

        required_fields = ['id', 'name', 'url_slug', 'url', 'category']

        for field in required_fields:
            if field not in config:
                self.errors.append(f"Missing required field in config: {field}")
                return False

        # Validate url_slug format (should be simple, not full URL)
        url_slug = config['url_slug']
        if url_slug.startswith('/') or url_slug.startswith('http'):
            self.errors.append(f"url_slug should be simple identifier, not full URL: {url_slug}")
            return False

        return True

    def validate_template_placeholders(self, template_content: str) -> bool:
        """Check for remaining placeholder values in templates"""

        placeholder_patterns = [
            r'YOUR_.*_HERE',
            r'PLACEHOLDER_.*',
            r'XXX_.*',
            r'EXAMPLE_.*'
        ]

        issues_found = False
        for pattern in placeholder_patterns:
            matches = re.findall(pattern, template_content, re.IGNORECASE)
            if matches:
                self.errors.append(f"Template placeholders found: {matches}")
                issues_found = True

        return not issues_found

    def run_validation(self,
                      template_path: str = None,
                      sitemap_path: str = None,
                      config_path: str = None,
                      deployed_urls: List[str] = None) -> bool:
        """Run all validation checks"""

        self.errors = []
        self.warnings = []

        # Validate template if provided
        if template_path and os.path.exists(template_path):
            with open(template_path, 'r') as f:
                template_content = f.read()

            self.validate_google_analytics(template_content)
            self.validate_template_placeholders(template_content)

        # Validate sitemap if provided
        if sitemap_path and os.path.exists(sitemap_path):
            with open(sitemap_path, 'r') as f:
                sitemap_content = f.read()

            if deployed_urls:
                self.validate_sitemap_urls(sitemap_content, deployed_urls)

        # Validate config if provided
        if config_path and os.path.exists(config_path):
            import json
            with open(config_path, 'r') as f:
                config = json.load(f)

            if 'sources' in config:
                for source in config['sources']:
                    self.validate_specific_source_config(source)

        # Print results
        if self.errors:
            print("❌ VALIDATION ERRORS:")
            for error in self.errors:
                print(f"   • {error}")

        if self.warnings:
            print("⚠️  VALIDATION WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")

        if not self.errors and not self.warnings:
            print("✅ All validations passed!")

        return len(self.errors) == 0

# Example usage
if __name__ == '__main__':
    validator = DeploymentValidator()

    # Validate layout template
    template_path = '/Users/roy/Documents/Projects/citations/backend/pseo/templates/layout.html'

    # Validate specific sources config
    config_path = '/Users/roy/Documents/Projects/citations/backend/pseo/configs/specific_sources.json'

    # Validate sitemap
    sitemap_path = '/Users/roy/Documents/Projects/citations/clean_hybrid_sitemap.xml'

    # List of deployed specific source URLs
    deployed_urls = [
        'https://citationformatchecker.com/cite-new-york-times-apa/',
        'https://citationformatchecker.com/cite-washington-post-apa/',
        'https://citationformatchecker.com/cite-wall-street-journal-apa/',
        'https://citationformatchecker.com/cite-the-guardian-apa/',
        'https://citationformatchecker.com/cite-bbc-news-apa/'
    ]

    success = validator.run_validation(
        template_path=template_path,
        config_path=config_path,
        sitemap_path=sitemap_path,
        deployed_urls=deployed_urls
    )

    exit(0 if success else 1)