#!/usr/bin/env python3
"""
Simple CSV generator from production citation data.
"""

import json
import csv

def main():
    # Load the production data
    with open('/tmp/production_citations_analysis.json', 'r') as f:
        data = json.load(f)

    # Generate CSV
    with open('/tmp/production_citations_sample.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow(['citation_text', 'type', 'length', 'has_url', 'has_doi', 'timestamp'])

        # Process citations from raw_citations
        for citation in data.get('raw_citations', [])[:100]:  # First 100 for sample
            text = citation.get('text', '').replace('"', '""').replace('\n', ' ')
            citation_type = citation.get('type', 'other')
            length = len(text)
            has_url = citation.get('has_url', False)
            has_doi = citation.get('has_doi', False)
            timestamp = citation.get('timestamp', '')

            # Write CSV row
            writer.writerow([text, citation_type, length, has_url, has_doi, timestamp])

    print(f"✅ Generated CSV with {len(data.get('raw_citations', []))} citations")
    print(f"📁 File: /tmp/production_citations_sample.csv")

if __name__ == '__main__':
    main()