#!/usr/bin/env python3
"""
Generate HTML report for ScraperAPI extracted citations with source type categorization
"""

import json
import os
import re
from collections import defaultdict
from datetime import datetime

def detect_source_type(citation_text):
    """Detect source type from citation text"""

    text = citation_text.lower()

    # Journal article indicators
    if re.search(r'\d+\(\d+\),\s*\d+-\d+', text) or 'doi:' in text:
        return 'journal'

    # Book indicators
    if re.search(r'\([^)]*ed\.\)|\d+nd ed\.|\d+rd ed\.|\d+th ed\.', text) or \
       re.search(r'[A-Z][a-z]+ [A-Z][a-z]+:\s*[A-Z][a-z]+', citation_text):
        if 'press' in text or 'university' in text:
            return 'book'

    # Website indicators
    if 'retrieved from' in text or 'http' in text:
        return 'website'

    # Chapter indicators
    if 'in ' in text and re.search(r'[A-Z][a-z]+\s*\([A-Z][a-z]+\)', citation_text):
        return 'chapter'

    # Default
    return 'other'

def categorize_citations(citations):
    """Categorize citations by source type"""

    categorized = defaultdict(list)

    for citation in citations:
        source_type = detect_source_type(citation['text'])
        citation['source_type'] = source_type
        categorized[source_type].append(citation)

    return categorized

def generate_html_report(categorized_citations, output_filename):
    """Generate HTML report with source type categorization"""

    total_citations = sum(len(citations) for citations in categorized_citations.values())

    # Sort categories by count (descending)
    sorted_categories = sorted(categorized_citations.items(),
                             key=lambda x: len(x[1]), reverse=True)

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ScraperAPI Citation Extraction Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            display: block;
        }}
        .category {{
            margin-bottom: 30px;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            overflow: hidden;
        }}
        .category-header {{
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
            color: white;
            padding: 15px 20px;
            font-weight: bold;
            font-size: 1.1em;
        }}
        .citations {{
            padding: 20px;
        }}
        .citation {{
            background: #f8f9fa;
            margin: 10px 0;
            padding: 15px;
            border-left: 4px solid #007bff;
            border-radius: 4px;
            font-size: 0.95em;
        }}
        .citation-id {{
            color: #6c757d;
            font-size: 0.85em;
            margin-bottom: 5px;
        }}
        .citation-text {{
            margin-bottom: 8px;
        }}
        .citation-text em {{
            font-style: italic;
            color: #333;
        }}
        .citation-meta {{
            color: #6c757d;
            font-size: 0.85em;
        }}
        .source-type-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: bold;
            margin-right: 10px;
        }}
        .book {{ background: #28a745; color: white; }}
        .journal {{ background: #17a2b8; color: white; }}
        .website {{ background: #ffc107; color: black; }}
        .chapter {{ background: #6f42c1; color: white; }}
        .other {{ background: #6c757d; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 ScraperAPI Citation Extraction Report</h1>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <span class="stat-number">{total_citations}</span>
                <span>Total Citations</span>
            </div>
            <div class="stat-card">
                <span class="stat-number">{len(sorted_categories)}</span>
                <span>Source Categories</span>
            </div>
        </div>
'''

    # Add categories
    for category_name, citations in sorted_categories:
        html_content += f'''
        <div class="category">
            <div class="category-header">
                <span class="source-type-badge {category_name}">{category_name.upper()}</span>
                {len(citations)} citations
            </div>
            <div class="citations">
'''

        for i, citation in enumerate(citations, 1):
            html_content += f'''
                <div class="citation">
                    <div class="citation-id">#{i} - ID: {citation['id']}</div>
                    <div class="citation-text">{markdown_to_html(citation['text'])}</div>
                    <div class="citation-meta">
                        Source: {citation['source']} |
                        Extracted: {citation['extracted_at'][:10]} |
                        URL: <a href="{citation['url']}" target="_blank">{citation['page_category']}</a>
                    </div>
                </div>
'''

        html_content += '''
            </div>
        </div>
'''

    html_content += '''
    </div>
</body>
</html>'''

    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return output_filename

def markdown_to_html(citation_text):
    """Convert markdown underscores in citation text to HTML <em> tags for display"""
    # Convert _text_ to <em>text</em>
    return re.sub(r'_(.*?)_', r'<em>\1</em>', citation_text)

def main():
    """Generate HTML report for clean ScraperAPI citations"""

    # Find the most recent cleaned ScraperAPI file
    scrpbee_dir = 'datasets/scrpbee'
    scraperapi_files = [f for f in os.listdir(scrpbee_dir) if f.startswith('scraperapi_') and f.endswith('.jsonl')]

    if not scraperapi_files:
        print("❌ No ScraperAPI data files found")
        return

    # Prioritize cleaned files over raw files
    cleaned_files = [f for f in scraperapi_files if 'cleaned' in f]
    raw_files = [f for f in scraperapi_files if 'cleaned' not in f]

    # Use the most recent cleaned file if available
    if cleaned_files:
        latest_file = sorted(cleaned_files)[-1]
        print(f"✅ Using cleaned file: {latest_file}")
    else:
        latest_file = sorted(raw_files)[-1]
        print(f"⚠️  No cleaned file found, using: {latest_file}")

    file_path = os.path.join(scrpbee_dir, latest_file)

    print(f"📂 Loading citations from: {latest_file}")

    # Load citations with new schema
    citations = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                citation_data = json.loads(line)
                # Convert to format expected by categorize_citations
                citation = {
                    'text': citation_data['citation_text'],
                    'source_type': citation_data['source_type'],
                    'id': citation_data['citation_id'],
                    'source': citation_data['metadata']['source'],
                    'url': citation_data['metadata']['url'],
                    'page_category': citation_data['metadata']['category'],
                    'extracted_at': citation_data['metadata']['date_collected']
                }
                citations.append(citation)

    print(f"📊 Loaded {len(citations)} citations")

    # Categorize by source type (use detected source_type)
    categorized = {}
    for citation in citations:
        source_type = citation['source_type']
        if source_type not in categorized:
            categorized[source_type] = []
        categorized[source_type].append(citation)

    # Show category breakdown
    print("\n📋 Citation breakdown by source type:")
    for source_type, cit_list in sorted(categorized.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  • {source_type}: {len(cit_list)} citations")

    # Generate HTML report
    output_filename = f'scraperapi_citation_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
    report_path = os.path.join(scrpbee_dir, output_filename)

    generate_html_report(categorized, report_path)

    print(f"\n🎉 HTML report generated: {report_path}")
    print(f"📈 Total citations: {len(citations)}")
    print(f"🏷️  Categories: {len(categorized)}")

    return report_path

if __name__ == "__main__":
    main()