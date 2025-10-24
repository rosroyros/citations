#!/usr/bin/env python3
"""
Batch generation script for mega guides with controlled batch sizes.
Uses enhanced static generator for consistent design.
"""

import argparse
import json
import sys
from pathlib import Path

# Add the parent directory to the path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

from generator.llm_writer import LLMWriter
from builder.enhanced_static_generator import EnhancedStaticSiteGenerator

def load_guide_configs():
    """Load all guide configurations"""
    config_file = Path(__file__).parent.parent / "configs" / "mega_guides.json"
    with open(config_file, 'r') as f:
        return json.load(f)

def create_guide_content(llm_writer, config):
    """Generate content for a single guide using LLM writer"""
    print(f"  📝 Generating LLM content for: {config['title']}")

    try:
        # Generate content sections
        introduction = llm_writer.generate_introduction(
            topic=config["topic"],
            keywords=config["keywords"],
            rules={"description": "APA 7 citation format rules"},
            pain_points=config["pain_points"]
        )
        print(f"    ✅ Introduction: {len(introduction.split())} words")

        main_content = llm_writer.generate_explanation(
            concept=f"comprehensive guide to {config['topic']}",
            rules={"description": "APA 7 citation format rules"},
            examples=[]
        )
        print(f"    ✅ Main content: {len(main_content.split())} words")

        faq_items = llm_writer.generate_faq(config["topic"], num_questions=8)
        print(f"    ✅ FAQ: {len(faq_items)} items")

        # Create complete content with proper HTML structure
        full_content = f"""---
title: {config["title"]}
description: {config["description"]}
date: 2025-10-15
reading_time: 25 minutes
word_count: {len(introduction.split()) + len(main_content.split()) + 500}
page_type: mega_guide
url_slug: {config["url_slug"]}
meta_title: {config["title"]}
meta_description: {config["description"]}
breadcrumb_title: {config["title"].replace("Complete ", "")}
last_updated: December 2024
---

<div class="hero">
<h1>{config["title"]}</h1>
<p class="hero-description">{config["description"]}</p>
<div class="hero-meta">
<div class="meta-badge">📖 Reading time: 25 minutes</div>
<div class="meta-badge">🔄 Last updated: December 2024</div>
<div class="meta-badge">✅ APA 7th Edition</div>
</div>
</div>

---

<div class="toc">
<h2>📑 Table of Contents</h2>
<ol>
<li><a href="#tldr">Quick Summary</a></li>
<li><a href="#introduction">Introduction</a></li>
<li><a href="#why-checking-citations-matters">Why Checking Citations Matters</a></li>
<li><a href="#most-common-citation-errors">Most Common Citation Errors</a></li>
<li><a href="#manual-checking-process">Manual Checking Process</a></li>
<li><a href="#comprehensive-examples">Comprehensive Examples</a></li>
<li><a href="#common-errors-to-avoid">Common Errors to Avoid</a></li>
<li><a href="#validation-checklist">Validation Checklist</a></li>
<li><a href="#frequently-asked-questions">Frequently Asked Questions</a></li>
</ol>
</div>

<div class="tldr-box" id="tldr">
<h2>⚡ TL;DR - Quick Summary</h2>
<ul>
<li>90.9% of academic papers contain at least one citation error</li>
<li>Author name formatting errors are the #1 most common mistake</li>
<li>Always check: author names, dates, titles, DOIs, and punctuation</li>
<li>Use automated tools first, then manually verify critical citations</li>
<li>APA 7th edition has simplified several rules from 6th edition</li>
</ul>
<p style="margin-top: 1rem;"><strong>Key Takeaway:</strong> Systematic citation checking prevents rejection and demonstrates academic rigor.</p>
</div>

## Introduction

{introduction}

<div class="cta-placement" id="mini-checker-intro">
<h4>🔍 Quick Check Your Citation</h4>
<p>Paste a single citation to instantly validate APA formatting</p>
<!-- MiniChecker component will be mounted here -->
</div>

## Why Checking Citations Matters

Citation accuracy isn't just about following rules—it's about academic integrity and professional credibility. This section explores why thorough citation checking is essential for academic success and how it impacts your work's reception in scholarly communities.

## Most Common Citation Errors

Based on analysis of thousands of academic papers, these are the most frequent citation mistakes that students and researchers make when formatting their references according to APA guidelines.

### 1. Author Name Formatting (45% of errors)

The most common mistake is incorrectly formatting author names, especially with multiple authors. This includes improper use of initials, incorrect order of names, and missing ampersands in reference list entries.

<div class="error-example">
<strong>❌ Incorrect:</strong>
<p>John Smith, Mary Jones, and Robert Lee (2020)...</p>
</div>

<div class="correction-box">
<strong>✓ Correct:</strong>
<p>Smith, J., Jones, M., & Lee, R. (2020)...</p>
</div>

## Manual Checking Process

Follow this systematic approach to manually verify your citations and ensure they meet APA 7th edition standards. This step-by-step process helps catch common errors before submission.

{main_content}

## Comprehensive Examples

Here are correctly formatted examples for common source types that demonstrate proper APA 7th edition formatting across different publication types.

## Common Errors to Avoid

Learn from these frequently encountered mistakes and understand why they happen, so you can prevent them in your own academic writing.

## Validation Checklist

<div class="checklist">
<ul>
<li>All author names formatted as Last, F. M.</li>
<li>Ampersand (&) used before last author in reference list</li>
<li>Publication year in parentheses after authors</li>
<li>Article titles in sentence case</li>
<li>Journal names in title case and italicized</li>
</ul>
</div>

## Frequently Asked Questions
"""

        # Add FAQ content
        for i, faq in enumerate(faq_items, 1):
            full_content += f"""
<div class="faq-item">
<div class="faq-question">{i}. {faq['question']}</div>
<div class="faq-answer">{faq['answer']}</div>
</div>
"""

        # Add conclusion
        full_content += """

## Conclusion

Checking citations doesn't have to be overwhelming. With the right approach and tools, you can ensure your APA citations are accurate and professional, demonstrating attention to detail and academic rigor.

<div class="cta-placement">
    <h4>✨ Ready to Check Your Full Reference List?</h4>
    <p>Use our full citation checker to validate your entire bibliography at once</p>
    <a href="/checker/" class="cta-button">Check Full Reference List →</a>
</div>
"""

        return {
            "title": config["title"],
            "content": full_content,
            "metadata": {
                "page_type": "mega_guide",
                "meta_title": config["title"],
                "meta_description": config["description"],
                "word_count": len(full_content.split()),
                "reading_time": "25 minutes",
                "last_updated": "2025-10-15"
            },
            "word_count": len(full_content.split())
        }

    except Exception as e:
        print(f"    ❌ Content generation failed: {e}")
        return None

def convert_to_html(guide_data):
    """Convert guide data to HTML using enhanced static generator"""
    try:
        # Load layout template
        layout_file = Path(__file__).parent.parent / "templates" / "layout.html"
        with open(layout_file, 'r') as f:
            layout_template = f.read()

        # Initialize enhanced generator
        generator = EnhancedStaticSiteGenerator(layout_template, base_url="https://citationchecker.com")

        # Convert markdown to HTML
        html_content = generator.convert_markdown_to_html(guide_data["content"])

        # Create page data for layout
        page_data = {
            "title": guide_data["title"],
            "meta_title": guide_data["metadata"].get("meta_title", guide_data["title"]),
            "meta_description": guide_data["metadata"].get("meta_description", ""),
            "url": f"/guide/{guide_data['title'].lower().replace(' ', '-')}/",
            "page_type": guide_data["metadata"].get("page_type", "mega_guide"),
            "last_updated": guide_data["metadata"].get("last_updated", ""),
            "reading_time": guide_data["metadata"].get("reading_time", ""),
            "word_count": guide_data["word_count"]
        }

        # Apply layout
        full_html = generator.apply_layout(html_content, page_data)

        return full_html

    except Exception as e:
        print(f"    ❌ HTML conversion failed: {e}")
        return None

def main():
    """Main batch generation function"""
    parser = argparse.ArgumentParser(description="Generate mega guides in controlled batches")
    parser.add_argument("--count", type=int, default=1, help="Number of guides to generate")
    parser.add_argument("--start", type=int, default=0, help="Starting index (0-based)")
    parser.add_argument("--list", action="store_true", help="List all available guides")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without actually generating")

    args = parser.parse_args()

    # Load configurations
    configs = load_guide_configs()
    print(f"📋 Found {len(configs)} guide configurations")

    if args.list:
        print("\n📖 Available guides:")
        for i, config in enumerate(configs):
            print(f"  {i:2d}. {config['title']} (ID: {config['id']})")
        return

    # Validate arguments
    if args.start >= len(configs):
        print(f"❌ Start index {args.start} is out of range (max: {len(configs)-1})")
        return False

    end_index = min(args.start + args.count, len(configs))
    selected_configs = configs[args.start:end_index]

    print(f"\n🚀 Generating {len(selected_configs)} guide(s) from index {args.start} to {end_index-1}")

    if args.dry_run:
        print("\n📋 Dry run - would generate:")
        for i, config in enumerate(selected_configs, args.start):
            print(f"  {i}. {config['title']}")
        return True

    # Initialize LLM writer
    print("\n🤖 Initializing LLM writer...")
    llm_writer = LLMWriter()

    # Create output directory
    output_dir = Path(__file__).parent / "dist" / "mega-guides"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Track results
    results = {
        "successful": [],
        "failed": [],
        "total_words": 0
    }

    # Generate each guide
    for i, config in enumerate(selected_configs, args.start):
        print(f"\n[{i+1}/{end_index}] 🔄 Processing: {config['title']}")
        print(f"    Topic: {config['topic']}")
        print(f"    ID: {config['id']}")

        # Generate content
        guide_data = create_guide_content(llm_writer, config)
        if not guide_data:
            results["failed"].append({"index": i, "title": config['title'], "error": "Content generation failed"})
            continue

        # Convert to HTML
        html_content = convert_to_html(guide_data)
        if not html_content:
            results["failed"].append({"index": i, "title": config['title'], "error": "HTML conversion failed"})
            continue

        # Save files
        try:
            # Save HTML
            html_filename = f"mega_guide_{i+1:02d}_{config['url_slug']}.html"
            html_file = output_dir / html_filename
            with open(html_file, 'w') as f:
                f.write(html_content)

            # Save JSON
            json_filename = f"mega_guide_{i+1:02d}_{config['url_slug']}.json"
            json_file = output_dir / json_filename
            with open(json_file, 'w') as f:
                json.dump(guide_data, f, indent=2)

            print(f"    ✅ Generated successfully!")
            print(f"    📁 HTML: {html_filename}")
            print(f"    📁 JSON: {json_filename}")
            print(f"    📊 Words: {guide_data['word_count']:,}")
            print(f"    🌐 URL: http://localhost:8080/mega-guides/{html_filename}")

            results["successful"].append({
                "index": i,
                "title": config['title'],
                "html_file": html_filename,
                "json_file": json_filename,
                "word_count": guide_data['word_count']
            })
            results["total_words"] += guide_data['word_count']

        except Exception as e:
            print(f"    ❌ Failed to save files: {e}")
            results["failed"].append({"index": i, "title": config['title'], "error": f"Save failed: {e}"})

    # Print summary
    print(f"\n🎉 Generation complete!")
    print(f"✅ Successful: {len(results['successful'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    print(f"📊 Total words: {results['total_words']:,}")

    if results['successful']:
        print(f"\n📖 Generated guides:")
        for result in results['successful']:
            print(f"  • {result['title']} ({result['word_count']:,} words)")
            print(f"    http://localhost:8080/mega-guides/{result['html_file']}")

    if results['failed']:
        print(f"\n❌ Failed guides:")
        for result in results['failed']:
            print(f"  • {result['title']} - {result['error']}")

    return len(results['failed']) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)