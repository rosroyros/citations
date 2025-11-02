"""
Sitemap Generator for PSEO Pages

Generates and updates sitemap.xml with all PSEO pages including:
- Mega guides
- Source type pages
- Validation guides
- Specific source pages
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

logger = logging.getLogger(__name__)


class SitemapGenerator:
    """
    Generates and maintains sitemap.xml for PSEO content
    """

    def __init__(self, sitemap_path: str, base_url: str = "https://citations.com"):
        """
        Initialize sitemap generator

        Args:
            sitemap_path: Path to sitemap.xml file
            base_url: Base URL for the site
        """
        self.sitemap_path = Path(sitemap_path)
        self.base_url = base_url.rstrip('/')
        logger.info(f"Initialized SitemapGenerator for {base_url}")

    def generate_specific_source_entries(self, sources_config: List[Dict]) -> List[Dict]:
        """
        Generate sitemap entries for specific source pages

        Args:
            sources_config: List of source configurations

        Returns:
            List of sitemap entry dictionaries
        """
        entries = []

        for source in sources_config:
            entry = {
                "url": f"{self.base_url}{source['url_slug'].lstrip('/')}",
                "lastmod": datetime.now().strftime("%Y-%m-%d"),
                "changefreq": "monthly",
                "priority": "0.7"
            }
            entries.append(entry)

        logger.info(f"Generated {len(entries)} sitemap entries for specific sources")
        return entries

    def add_entries_to_sitemap(self, new_entries: List[Dict], output_path: str = None) -> bool:
        """
        Add new entries to existing sitemap or create new one

        Args:
            new_entries: List of new sitemap entries
            output_path: Optional custom output path

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing sitemap if it exists
            existing_entries = []
            if self.sitemap_path.exists():
                existing_entries = self._parse_existing_sitemap()

            # Combine existing and new entries
            all_entries = existing_entries + new_entries

            # Remove duplicates (keep newest)
            unique_entries = self._deduplicate_entries(all_entries)

            # Generate XML
            sitemap_xml = self._generate_sitemap_xml(unique_entries)

            # Write to file
            output_file = Path(output_path) if output_path else self.sitemap_path
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(sitemap_xml)

            logger.info(f"Sitemap updated with {len(new_entries)} new entries")
            logger.info(f"Total entries in sitemap: {len(unique_entries)}")
            return True

        except Exception as e:
            logger.error(f"Error updating sitemap: {str(e)}")
            return False

    def _parse_existing_sitemap(self) -> List[Dict]:
        """
        Parse existing sitemap.xml to extract entries

        Returns:
            List of existing sitemap entries
        """
        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(self.sitemap_path)
            root = tree.getroot()

            entries = []
            for url in root.findall('url'):
                loc = url.find('loc').text
                lastmod = url.find('lastmod').text if url.find('lastmod') is not None else None
                changefreq = url.find('changefreq').text if url.find('changefreq') is not None else 'monthly'
                priority = url.find('priority').text if url.find('priority') is not None else '0.5'

                entries.append({
                    'url': loc,
                    'lastmod': lastmod,
                    'changefreq': changefreq,
                    'priority': priority
                })

            logger.info(f"Parsed {len(entries)} entries from existing sitemap")
            return entries

        except Exception as e:
            logger.warning(f"Could not parse existing sitemap: {str(e)}")
            return []

    def _deduplicate_entries(self, entries: List[Dict]) -> List[Dict]:
        """
        Remove duplicate entries, keeping the most recent

        Args:
            entries: List of sitemap entries

        Returns:
            Deduplicated list of entries
        """
        seen_urls = set()
        unique_entries = []

        for entry in entries:
            url = entry['url']
            if url not in seen_urls:
                seen_urls.add(url)
                unique_entries.append(entry)
            else:
                # Update existing entry if this one is newer
                existing_index = next(i for i, e in enumerate(unique_entries) if e['url'] == url)
                if entry.get('lastmod') and unique_entries[existing_index].get('lastmod'):
                    if entry['lastmod'] > unique_entries[existing_index]['lastmod']:
                        unique_entries[existing_index] = entry

        logger.info(f"Deduplicated {len(entries)} entries to {len(unique_entries)} unique entries")
        return unique_entries

    def _generate_sitemap_xml(self, entries: List[Dict]) -> str:
        """
        Generate sitemap XML from entries

        Args:
            entries: List of sitemap entries

        Returns:
            Formatted sitemap XML string
        """
        # Create root element
        urlset = Element('urlset', {
            'xmlns': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:schemaLocation': 'http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd'
        })

        # Add entries
        for entry in entries:
            url = SubElement(urlset, 'url')

            # URL (required)
            loc = SubElement(url, 'loc')
            loc.text = entry['url']

            # Last modified (optional)
            if entry.get('lastmod'):
                lastmod = SubElement(url, 'lastmod')
                lastmod.text = entry['lastmod']

            # Change frequency (optional)
            if entry.get('changefreq'):
                changefreq = SubElement(url, 'changefreq')
                changefreq.text = entry['changefreq']

            # Priority (optional)
            if entry.get('priority'):
                priority = SubElement(url, 'priority')
                priority.text = entry['priority']

        # Format XML
        rough_string = tostring(urlset, encoding='unicode')
        reparsed = minidom.parseString(rough_string)

        # Return pretty-formatted XML
        return reparsed.toprettyxml(indent="  ")

    def generate_full_sitemap(self, pseo_content_dir: str) -> bool:
        """
        Generate complete sitemap from all PSEO content

        Args:
            pseo_content_dir: Directory containing PSEO markdown files

        Returns:
            True if successful, False otherwise
        """
        try:
            content_dir = Path(pseo_content_dir)
            all_entries = []

            # Scan for markdown files
            for md_file in content_dir.rglob('*.md'):
                try:
                    # Extract front matter to determine page type and priority
                    entry = self._extract_entry_from_markdown(md_file)
                    if entry:
                        all_entries.append(entry)
                except Exception as e:
                    logger.warning(f"Could not process {md_file}: {str(e)}")

            # Sort by priority (high to low)
            priority_order = {'1.0': 0, '0.9': 1, '0.8': 2, '0.7': 3, '0.6': 4, '0.5': 5}
            all_entries.sort(key=lambda x: priority_order.get(x['priority'], 6))

            # Generate sitemap
            sitemap_xml = self._generate_sitemap_xml(all_entries)

            # Write sitemap
            with open(self.sitemap_path, 'w', encoding='utf-8') as f:
                f.write(sitemap_xml)

            logger.info(f"Generated complete sitemap with {len(all_entries)} entries")
            return True

        except Exception as e:
            logger.error(f"Error generating full sitemap: {str(e)}")
            return False

    def _extract_entry_from_markdown(self, md_file: Path) -> Dict:
        """
        Extract sitemap entry from markdown file front matter

        Args:
            md_file: Path to markdown file

        Returns:
            Sitemap entry dictionary or None
        """
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract front matter
            if content.startswith('---'):
                front_matter_end = content.find('---', 3)
                if front_matter_end > 0:
                    front_matter = content[3:front_matter_end]

                    # Parse YAML front matter (simple key-value extraction)
                    entry = {'url': f"{self.base_url}/"}  # Default

                    for line in front_matter.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')

                            if key == 'url':
                                entry['url'] = f"{self.base_url}{value.lstrip('/')}"
                            elif key == 'last_updated':
                                entry['lastmod'] = value
                            elif key == 'page_type':
                                # Set priority based on page type
                                priority_map = {
                                    'mega_guide': '0.9',
                                    'source_type': '0.8',
                                    'specific_source': '0.7',
                                    'validation': '0.6'
                                }
                                entry['priority'] = priority_map.get(value, '0.5')

                    # Set defaults
                    if 'lastmod' not in entry:
                        entry['lastmod'] = datetime.now().strftime("%Y-%m-%d")
                    if 'changefreq' not in entry:
                        entry['changefreq'] = 'monthly'
                    if 'priority' not in entry:
                        entry['priority'] = '0.5'

                    return entry

        except Exception as e:
            logger.warning(f"Could not extract entry from {md_file}: {str(e)}")
            return None

    def validate_sitemap(self, sitemap_path: str = None) -> Dict:
        """
        Validate sitemap structure and content

        Args:
            sitemap_path: Optional custom sitemap path

        Returns:
            Validation results dictionary
        """
        try:
            sitemap_file = Path(sitemap_path) if sitemap_path else self.sitemap_path

            if not sitemap_file.exists():
                return {"valid": False, "errors": ["Sitemap file does not exist"]}

            # Parse XML
            import xml.etree.ElementTree as ET
            tree = ET.parse(sitemap_file)
            root = tree.getroot()

            # Basic validation
            validation_results = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "entry_count": len(root.findall('url')),
                "lastmod": datetime.fromtimestamp(sitemap_file.stat().st_mtime).isoformat()
            }

            # Check required elements
            if root.tag != 'urlset':
                validation_results["valid"] = False
                validation_results["errors"].append("Root element must be 'urlset'")

            # Check namespace
            expected_ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
            if root.get('xmlns') != expected_ns:
                validation_results["warnings"].append(f"Unexpected namespace: {root.get('xmlns')}")

            # Validate entries
            for i, url in enumerate(root.findall('url')):
                loc = url.find('loc')
                if loc is None or not loc.text:
                    validation_results["valid"] = False
                    validation_results["errors"].append(f"Entry {i+1} missing required 'loc' element")
                elif not loc.text.startswith('http'):
                    validation_results["warnings"].append(f"Entry {i+1} URL may not be absolute: {loc.text}")

            return validation_results

        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "entry_count": 0
            }