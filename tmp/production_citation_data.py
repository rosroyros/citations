#!/usr/bin/env python3
"""
Generate complete CSV from production citation data with proper escaping.
"""

import json
import csv

def main():
    # Load production analysis
    with open('/tmp/production_citations_analysis.json', 'r') as f:
        data = json.load(f)

    # Generate CSV with all 1,026 citations
    with open('/tmp/production_citation_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow(['citation_text', 'type', 'length', 'has_url', 'has_doi', 'timestamp'])

        # Process ALL citations from raw_citations
        for citation in data.get('raw_citations', []):
            text = citation.get('text', '')
            citation_type = citation.get('type', 'other')
            length = len(text)
            has_url = citation.get('has_url', False)
            has_doi = citation.get('has_doi', False)
            timestamp = citation.get('timestamp', '')

            # Escape quotes and newlines for CSV
            text_escaped = text.replace('"', '""')
            text_escaped = text_escaped.replace('\n', ' ').replace(',', ';')

            # Write CSV row
            writer.writerow([text_escaped, citation_type, length, has_url, has_doi, timestamp])

    print(f"✅ Generated complete CSV with {len(data.get('raw_citations', []))} citations")
    print(f"📁 File: /tmp/production_citation_data.csv")

if __name__ == '__main__':
    main()