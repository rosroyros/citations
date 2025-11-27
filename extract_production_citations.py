#!/usr/bin/env python3
"""
Extract and analyze real user citations from production logs.
This script pulls citation data from the last 7 days of application logs.
"""

import re
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import sys

def extract_citations_from_logs(log_file_path, days_back=7):
    """Extract citations from application logs."""

    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=days_back)

    citations = []

    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Parse log line to get timestamp
                timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                if not timestamp_match:
                    continue

                timestamp_str = timestamp_match.group(1)
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue

                # Skip if older than cutoff date
                if timestamp < cutoff_date:
                    continue

                # Look for citation validation lines
                if 'Citations to validate:' in line:
                    # Extract the citation text
                    citation_match = re.search(r'Citations to validate: (.+)', line)
                    if citation_match:
                        citation_text = citation_match.group(1).strip()

                        # Skip test/obvious citations
                        if is_test_citation(citation_text):
                            continue

                        # Try to get additional context from surrounding lines
                        citations.append({
                            'timestamp': timestamp_str,
                            'text': citation_text,
                            'length': len(citation_text),
                            'has_url': bool(re.search(r'https?://', citation_text)),
                            'has_doi': bool(re.search(r'doi\.org|10\.\d+/', citation_text.lower())),
                            'line': line.strip()
                        })

    except FileNotFoundError:
        print(f"Log file not found: {log_file_path}")
        return []
    except Exception as e:
        print(f"Error reading log file: {e}")
        return []

    return citations

def is_test_citation(citation_text):
    """Filter out obvious test citations."""
    test_indicators = [
        'Test citation',
        'test citation',
        'Smith, J. (2023)',
        'Johnson, A.',
        '**References**',  # Empty references section
        'Sample citation',
        'Example citation'
    ]

    return any(indicator in citation_text for indicator in test_indicators)

def classify_citation_type(citation_text):
    """Simple classification of citation type based on content."""
    citation_lower = citation_text.lower()

    # Priority order for classification
    if 'doi.org' in citation_lower or '10.' in citation_lower:
        return 'journal_article'
    elif re.search(r'\.pdf\s*\[', citation_text) or '[pdf]' in citation_lower:
        return 'pdf_document'
    elif 'university' in citation_lower or 'lecture' in citation_lower or 'slides' in citation_lower:
        return 'academic_material'
    elif 'government' in citation_lower or '.gov' in citation_lower or '.ca' in citation_lower:
        return 'government_document'
    elif 'book' in citation_lower or 'in _' in citation_lower:
        return 'book'
    elif 'wikipedia' in citation_lower or 'encycloped' in citation_lower:
        return 'reference_work'
    elif re.search(r'https?://', citation_text):
        return 'webpage'
    else:
        return 'other'

def analyze_citations(citations):
    """Analyze extracted citations."""

    if not citations:
        return {
            'total_citations': 0,
            'error': 'No citations found'
        }

    # Basic stats
    analysis = {
        'total_citations': len(citations),
        'date_range': {
            'start': min(c['timestamp'] for c in citations),
            'end': max(c['timestamp'] for c in citations)
        }
    }

    # Type distribution
    type_counts = Counter()
    for citation in citations:
        citation_type = classify_citation_type(citation['text'])
        citation['type'] = citation_type
        type_counts[citation_type] += 1

    analysis['type_distribution'] = dict(type_counts)

    # Length statistics
    lengths = [c['length'] for c in citations]
    analysis['length_stats'] = {
        'mean': sum(lengths) / len(lengths),
        'min': min(lengths),
        'max': max(lengths),
        'median': sorted(lengths)[len(lengths) // 2]
    }

    # URL/DOI statistics
    analysis['url_stats'] = {
        'with_url': sum(1 for c in citations if c['has_url']),
        'with_doi': sum(1 for c in citations if c['has_doi'])
    }

    # Sample citations by type
    samples_by_type = defaultdict(list)
    for citation in citations:
        samples_by_type[citation['type']].append(citation)

    analysis['samples'] = {}
    for citation_type, type_citations in samples_by_type.items():
        # Get 2-3 representative samples
        analysis['samples'][citation_type] = [
            {
                'text': c['text'][:200] + '...' if len(c['text']) > 200 else c['text'],
                'length': c['length'],
                'timestamp': c['timestamp']
            }
            for c in type_citations[:3]
        ]

    return analysis

def compare_with_test_set(production_analysis, test_set_path=None):
    """Compare production data with our test set."""

    # Load our test set for comparison
    test_set_citations = []
    if test_set_path:
        try:
            with open(test_set_path, 'r', encoding='utf-8') as f:
                test_set_citations = json.load(f)
        except FileNotFoundError:
            print(f"Test set file not found: {test_set_path}")
        except Exception as e:
            print(f"Error loading test set: {e}")

    comparison = {
        'production_stats': production_analysis,
        'test_set_stats': {
            'total_citations': len(test_set_citations),
            'type_distribution': 'N/A - would need manual classification'
        }
    }

    # Basic comparison metrics
    if production_analysis['total_citations'] > 0:
        comparison['coverage_analysis'] = {
            'production_types': list(production_analysis['type_distribution'].keys()),
            'most_common_production_type': max(production_analysis['type_distribution'].items(), key=lambda x: x[1]) if production_analysis['type_distribution'] else None,
            'production_diversity': len(production_analysis['type_distribution'])
        }

    return comparison

def main():
    """Main execution function."""

    log_file_path = '/opt/citations/logs/app.log'

    # Test both 7-day and 30-day ranges to see data availability
    print("🔍 Extracting citations from production logs (last 30 days)...")
    citations = extract_citations_from_logs(log_file_path, days_back=30)

    if not citations:
        print("❌ No citations found in the last 30 days")
        return

    print(f"✅ Found {len(citations)} citations from the last 30 days")

    print("\n📊 Analyzing citations...")
    analysis = analyze_citations(citations)

    print(f"📈 Analysis Results:")
    print(f"   Total citations: {analysis['total_citations']}")
    print(f"   Date range: {analysis['date_range']['start']} to {analysis['date_range']['end']}")
    print(f"   Average length: {analysis['length_stats']['mean']:.1f} characters")
    print(f"   With URLs: {analysis['url_stats']['with_url']}/{analysis['total_citations']} ({analysis['url_stats']['with_url']/analysis['total_citations']*100:.1f}%)")
    print(f"   With DOIs: {analysis['url_stats']['with_doi']}/{analysis['total_citations']} ({analysis['url_stats']['with_doi']/analysis['total_citations']*100:.1f}%)")

    # Additional quality metrics
    very_short = sum(1 for c in citations if c['length'] < 50)
    very_long = sum(1 for c in citations if c['length'] > 190)  # Near max of 203
    print(f"   Very short (<50 chars): {very_short} ({very_short/analysis['total_citations']*100:.1f}%)")
    print(f"   Very long (>190 chars): {very_long} ({very_long/analysis['total_citations']*100:.1f}%)")

    print(f"\n📋 Type Distribution:")
    for citation_type, count in sorted(analysis['type_distribution'].items(), key=lambda x: x[1], reverse=True):
        percentage = (count / analysis['total_citations']) * 100
        print(f"   {citation_type}: {count} ({percentage:.1f}%)")

    print(f"\n📝 Sample Citations by Type:")
    for citation_type, samples in analysis['samples'].items():
        print(f"\n   {citation_type.replace('_', ' ').title()}:")
        for i, sample in enumerate(samples, 1):
            print(f"     {i}. {sample['text']}")

    # Save results to file
    output_file = '/tmp/production_citations_analysis.json'
    result = {
        'extraction_date': datetime.now().isoformat(),
        'analysis': analysis,
        'raw_citations': citations[:50]  # First 50 citations for reference
    }

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {output_file}")
    except Exception as e:
        print(f"❌ Error saving results: {e}")

if __name__ == '__main__':
    main()