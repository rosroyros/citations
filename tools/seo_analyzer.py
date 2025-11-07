#!/usr/bin/env python3
"""
SEO Link Health Analyzer

Analyzes internal link patterns for SEO insights including:
- Total internal link count
- Links per page statistics (avg/min/max)
- Most/least linked pages
- Orphaned pages (no incoming links)
- Missing pages with multiple references (build priority)
"""

import json
import sys
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple
import argparse

def analyze_link_patterns(inventory: Dict, validation_report: Dict) -> Dict:
    """Analyze link patterns for SEO insights."""

    # Get all links from inventory
    all_links = inventory.get('all_links', [])
    html_files = inventory.get('html_files', {})

    # Build link relationships
    page_links = defaultdict(list)  # page -> list of outgoing links
    incoming_links = defaultdict(set)  # page -> set of sources linking to it
    link_counts = defaultdict(int)  # page -> number of outgoing links

    # Get validation results
    broken_urls = set()
    missing_urls = set()
    if validation_report and 'detailed_results' in validation_report:
        broken_urls = {link['url'] for link in validation_report['detailed_results'].get('broken', [])}
        missing_urls = {link['url'] for link in validation_report['detailed_results'].get('missing_pages', [])}

    # Process all links
    for link in all_links:
        source_file = link['source_file']
        target_url = link['url']

        # Extract source page path
        if '/tmp/production_html/' in source_file:
            source_path = source_file.replace('/tmp/production_html/', '')
            source_path = source_path.replace('/index.html', '')
            if source_path:
                source_path = '/' + source_path + '/'
            else:
                source_path = '/'
        else:
            continue

        # Normalize target URL
        if not target_url.startswith('/'):
            continue

        # Add to outgoing links
        page_links[source_path].append({
            'url': target_url,
            'text': link['text'],
            'status': 'broken' if target_url in broken_urls else 'missing' if target_url in missing_urls else 'working'
        })
        link_counts[source_path] += 1

        # Add to incoming links
        incoming_links[target_url].add(source_path)

    # Get all pages (static pages + known routes)
    all_pages = set(html_files.keys())
    all_pages.update(page_links.keys())
    all_pages.update(incoming_links.keys())

    # Normalize page paths
    normalized_pages = set()
    for page in all_pages:
        if not page.startswith('/'):
            continue
        if not page.endswith('/') and page != '/':
            page += '/'
        normalized_pages.add(page)

    # Calculate statistics
    outgoing_counts = [len(links) for links in page_links.values()]
    incoming_counts = [len(sources) for sources in incoming_links.values()]

    stats = {
        'total_internal_links': len(all_links),
        'total_pages': len(normalized_pages),
        'outgoing_links_per_page': {
            'average': sum(outgoing_counts) / len(outgoing_counts) if outgoing_counts else 0,
            'minimum': min(outgoing_counts) if outgoing_counts else 0,
            'maximum': max(outgoing_counts) if outgoing_counts else 0,
            'median': sorted(outgoing_counts)[len(outgoing_counts)//2] if outgoing_counts else 0
        },
        'incoming_links_per_page': {
            'average': sum(incoming_counts) / len(incoming_counts) if incoming_counts else 0,
            'minimum': min(incoming_counts) if incoming_counts else 0,
            'maximum': max(incoming_counts) if incoming_counts else 0,
            'median': sorted(incoming_counts)[len(incoming_counts)//2] if incoming_counts else 0
        }
    }

    # Find most linked pages (by incoming links)
    most_linked = sorted(incoming_links.items(), key=lambda x: len(x[1]), reverse=True)[:20]

    # Find least linked pages (by incoming links)
    least_linked = sorted(incoming_links.items(), key=lambda x: len(x[1]))[:20]

    # Find orphaned pages (no incoming links)
    orphaned_pages = []
    for page in normalized_pages:
        if len(incoming_links.get(page, set())) == 0:
            orphaned_pages.append(page)

    # Find missing pages with multiple references (build priority)
    missing_page_priority = []
    for url in missing_urls:
        ref_count = len(incoming_links.get(url, set()))
        if ref_count > 0:
            missing_page_priority.append((url, ref_count))

    missing_page_priority.sort(key=lambda x: x[1], reverse=True)

    # Page distribution analysis
    page_distribution = {
        'high_outgoing': [],  # > 20 outgoing links
        'medium_outgoing': [],  # 10-20 outgoing links
        'low_outgoing': [],  # < 10 outgoing links
    }

    for page, links in page_links.items():
        count = len(links)
        if count > 20:
            page_distribution['high_outgoing'].append((page, count))
        elif count >= 10:
            page_distribution['medium_outgoing'].append((page, count))
        else:
            page_distribution['low_outgoing'].append((page, count))

    # Content gaps analysis
    broken_url_analysis = {}
    for url in broken_urls:
        ref_count = len(incoming_links.get(url, set()))
        if ref_count > 0:
            broken_url_analysis[url] = ref_count

    # Generate insights
    insights = []

    # Link health insights
    success_rate = validation_report['summary']['success_rate'] if validation_report else 0
    if success_rate < 50:
        insights.append("Critical: Link health below 50% - immediate action needed")
    elif success_rate < 80:
        insights.append("Warning: Link health below 80% - improvement needed")

    # Orphaned pages insights
    orphaned_count = len(orphaned_pages)
    if orphaned_count > 10:
        insights.append(f"High number of orphaned pages ({orphaned_count}) - consider internal linking strategy")

    # Missing pages insights
    high_priority_missing = [url for url, count in missing_page_priority if count >= 10]
    if high_priority_missing:
        insights.append(f"Found {len(high_priority_missing)} high-priority missing pages (10+ references)")

    # Link distribution insights
    if stats['outgoing_links_per_page']['maximum'] > 50:
        insights.append("Some pages have excessive outgoing links (>50) - consider user experience")

    return {
        'statistics': stats,
        'most_linked_pages': [{'page': page, 'incoming_links': len(sources)} for page, sources in most_linked],
        'least_linked_pages': [{'page': page, 'incoming_links': len(sources)} for page, sources in least_linked],
        'orphaned_pages': orphaned_pages,
        'missing_page_priority': [{'page': url, 'reference_count': count} for url, count in missing_page_priority[:20]],
        'broken_url_analysis': broken_url_analysis,
        'page_distribution': {
            'high_outgoing': [{'page': page, 'link_count': count} for page, count in page_distribution['high_outgoing']],
            'medium_outgoing': [{'page': page, 'link_count': count} for page, count in page_distribution['medium_outgoing']],
            'low_outgoing': [{'page': page, 'link_count': count} for page, count in page_distribution['low_outgoing']],
        },
        'insights': insights,
        'recommendations': generate_recommendations(stats, orphaned_pages, missing_page_priority, broken_url_analysis)
    }

def generate_recommendations(stats: Dict, orphaned_pages: List, missing_pages: List, broken_urls: Dict) -> List[str]:
    """Generate actionable SEO recommendations."""
    recommendations = []

    # Link health recommendations
    if stats['total_pages'] > 0:
        avg_links = stats['outgoing_links_per_page']['average']
        if avg_links < 5:
            recommendations.append("Increase internal linking - average links per page is very low")
        elif avg_links > 30:
            recommendations.append("Consider reducing link density - average links per page is very high")

    # Orphaned pages
    if len(orphaned_pages) > 0:
        recommendations.append(f"Link to {len(orphaned_pages)} orphaned pages from relevant content")

    # Missing pages
    if missing_pages:
        top_missing = missing_pages[:5]
        recommendations.append(f"Priority: Create {len(top_missing)} most-referenced missing pages")

    # Broken links
    if broken_urls:
        recommendations.append(f"Fix {len(broken_urls)} broken links affecting user experience")

    # Link distribution
    high_outgoing = stats['outgoing_links_per_page']['maximum']
    if high_outgoing > 50:
        recommendations.append("Review pages with excessive outgoing links for better UX")

    return recommendations

def generate_seo_report(analysis: Dict, output_file: str):
    """Generate comprehensive SEO report."""
    report = {
        'scan_date': str(Path.cwd()),
        'analysis_summary': {
            'total_internal_links': analysis['statistics']['total_internal_links'],
            'total_pages_analyzed': analysis['statistics']['total_pages'],
            'orphaned_pages_count': len(analysis['orphaned_pages']),
            'missing_pages_with_references': len(analysis['missing_page_priority']),
            'broken_urls_with_references': len(analysis['broken_url_analysis'])
        },
        'detailed_analysis': analysis,
        'action_items': {
            'immediate_fixes': [],
            'content_opportunities': [],
            'link_building_tasks': []
        }
    }

    # Categorize action items
    # Immediate fixes (broken links)
    if analysis['broken_url_analysis']:
        report['action_items']['immediate_fixes'] = [
            f"Fix broken URL: {url} (referenced by {count} pages)"
            for url, count in list(analysis['broken_url_analysis'].items())[:10]
        ]

    # Content opportunities (missing pages)
    if analysis['missing_page_priority']:
        report['action_items']['content_opportunities'] = [
            f"Create missing page: {url} (referenced by {count} pages)"
            for url, count in analysis['missing_page_priority'][:10]
        ]

    # Link building tasks (orphaned pages)
    if analysis['orphaned_pages']:
        report['action_items']['link_building_tasks'] = [
            f"Add internal links to: {page}"
            for page in analysis['orphaned_pages'][:10]
        ]

    # Save report
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report

def main():
    parser = argparse.ArgumentParser(description='Generate SEO link health report')
    parser.add_argument('--inventory', required=True, help='Link inventory JSON file')
    parser.add_argument('--validation', required=True, help='Link validation report JSON file')
    parser.add_argument('--output', default='seo_link_health_report.json', help='Output SEO report file')

    args = parser.parse_args()

    print("Generating SEO link health report...")
    print(f"Inventory file: {args.inventory}")
    print(f"Validation file: {args.validation}")

    # Load data
    with open(args.inventory, 'r', encoding='utf-8') as f:
        inventory = json.load(f)

    with open(args.validation, 'r', encoding='utf-8') as f:
        validation_report = json.load(f)

    # Analyze link patterns
    print("Analyzing link patterns...")
    analysis = analyze_link_patterns(inventory, validation_report)

    # Generate report
    print("Generating SEO report...")
    report = generate_seo_report(analysis, args.output)

    print(f"\n✅ SEO link health report saved to: {args.output}")
    print(f"📊 Key Metrics:")
    print(f"   Total internal links: {report['analysis_summary']['total_internal_links']:,}")
    print(f"   Pages analyzed: {report['analysis_summary']['total_pages_analyzed']}")
    print(f"   Orphaned pages: {report['analysis_summary']['orphaned_pages_count']}")
    print(f"   Missing pages with references: {report['analysis_summary']['missing_pages_with_references']}")
    print(f"   Broken URLs with references: {report['analysis_summary']['broken_urls_with_references']}")

    if analysis['insights']:
        print(f"\n💡 Key Insights:")
        for i, insight in enumerate(analysis['insights'], 1):
            print(f"   {i}. {insight}")

    action_count = sum(len(items) for items in report['action_items'].values())
    if action_count > 0:
        print(f"\n🎯 Action Items: {action_count} total")
        for category, items in report['action_items'].items():
            if items:
                print(f"   {category.replace('_', ' ').title()}: {len(items)}")

if __name__ == '__main__':
    main()