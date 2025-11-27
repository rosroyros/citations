#!/usr/bin/env python3
"""
Extract ALL citations from the existing JSON analysis file and convert to CSV.
This script processes the complete citation dataset, not just samples.
"""

import json
import csv
from datetime import datetime

def extract_all_citations_from_json(json_file_path):
    """Extract all citations from the JSON analysis file."""

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"📊 Analysis from {data['extraction_date']}")
        print(f"   Total citations analyzed: {data['analysis']['total_citations']}")
        print(f"   Raw citations in file: {len(data['raw_citations'])}")

        return data['raw_citations']

    except FileNotFoundError:
        print(f"❌ JSON file not found: {json_file_path}")
        return []
    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        return []

def citations_to_csv(citations, output_file):
    """Convert citations to CSV with triple pipes delimiter."""

    if not citations:
        print("❌ No citations to convert")
        return

    # Header
    header = ['timestamp', 'text', 'length', 'has_url', 'has_doi', 'type']

    # Convert to CSV format
    csv_lines = ['|||'.join(header)]

    for citation in citations:
        # Clean the text to escape any triple pipes that might exist in the original text
        text = citation['text'].replace('|||', '||')

        line = f"{citation['timestamp']}|||{text}|||{citation['length']}|||{citation['has_url']}|||{citation['has_doi']}|||{citation['type']}"
        csv_lines.append(line)

    # Write to file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(csv_lines))

        print(f"✅ Successfully exported {len(citations)} citations to {output_file}")

        # Show statistics
        type_counts = {}
        url_count = 0
        doi_count = 0

        for citation in citations:
            citation_type = citation['type']
            type_counts[citation_type] = type_counts.get(citation_type, 0) + 1
            if citation['has_url']:
                url_count += 1
            if citation['has_doi']:
                doi_count += 1

        print(f"\n📈 Export Statistics:")
        print(f"   Total citations: {len(citations)}")
        print(f"   With URLs: {url_count} ({url_count/len(citations)*100:.1f}%)")
        print(f"   With DOIs: {doi_count} ({doi_count/len(citations)*100:.1f}%)")
        print(f"\n📋 Type Distribution:")
        for citation_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(citations)) * 100
            print(f"   {citation_type}: {count} ({percentage:.1f}%)")

    except Exception as e:
        print(f"❌ Error writing CSV file: {e}")

def main():
    """Main execution function."""

    json_file_path = './tmp/production_citations_analysis.json'
    output_file = './tmp/production_citation_data.csv'

    print("🔍 Extracting ALL citations from JSON analysis file...")
    citations = extract_all_citations_from_json(json_file_path)

    if not citations:
        print("❌ No citations found in JSON file")
        return

    print(f"\n📝 Converting {len(citations)} citations to CSV format...")
    citations_to_csv(citations, output_file)

    print(f"\n💾 Complete citation dataset saved to: {output_file}")

if __name__ == '__main__':
    main()