#!/usr/bin/env python3
"""
Improved batch generation script for mega guides with fully topic-specific content.
Uses enhanced static generator for consistent design and leverages all configuration data.
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

def create_topic_specific_content(llm_writer, config):
    """Generate fully topic-specific content using all configuration data"""
    print(f"  📝 Generating topic-specific content for: {config['title']}")
    print(f"    Target audience: {config['target_audience']}")
    print(f"    Pain points: {', '.join(config['pain_points'])}")

    try:
        # Generate topic-specific introduction
        introduction = llm_writer.generate_introduction(
            topic=config["topic"],
            keywords=config["keywords"],
            rules={"description": "APA 7 citation format rules"},
            pain_points=config["pain_points"]
        )
        print(f"    ✅ Introduction: {len(introduction.split())} words")

        # Generate topic-specific main explanation
        main_content = llm_writer.generate_explanation(
            concept=f"comprehensive guide to {config['topic']} for {config['target_audience']}",
            rules={"description": "APA 7 citation format rules"},
            examples=[]
        )
        print(f"    ✅ Main content: {len(main_content.split())} words")

        # Generate topic-specific "Why this matters" section
        why_matters_prompt = f"""
        Generate a section titled "Why {config['topic'].title()} Matters" specifically for {config['target_audience']}.

        Focus on these pain points: {', '.join(config['pain_points'])}
        Use these keywords: {', '.join(config['keywords'])}

        Target audience: {config['target_audience']}

        Write 300-400 words explaining why this topic is specifically important for this audience.
        Use conversational tone with "you" language.
        Include specific examples relevant to {config['target_audience']}.
        """

        why_matters_content = llm_writer._call_openai(
            prompt=why_matters_prompt,
            max_tokens=600,
            temperature=0.7
        )
        print(f"    ✅ Why it matters: {len(why_matters_content.split())} words")

        # Generate topic-specific common errors
        errors_prompt = f"""
        Generate a section titled "Common {config['topic'].title()} Errors" specifically for {config['target_audience']}.

        Focus on these pain points: {', '.join(config['pain_points'])}
        Target audience: {config['target_audience']}

        Write 400-500 words covering the most common errors this audience makes.
        Include 2-3 specific error examples with corrections.
        Use conversational tone with "you" language.
        Make the errors highly relevant to {config['topic']} and {config['target_audience']}.
        """

        common_errors = llm_writer._call_openai(
            prompt=errors_prompt,
            max_tokens=800,
            temperature=0.7
        )
        print(f"    ✅ Common errors: {len(common_errors.split())} words")

        # Generate topic-specific examples
        examples_prompt = f"""
        Generate a section titled "{config['topic'].title()} Examples" specifically for {config['target_audience']}.

        Keywords: {', '.join(config['keywords'])}
        Target audience: {config['target_audience']}
        Pain points: {', '.join(config['pain_points'])}

        Write 300-400 words providing 3-4 specific examples relevant to this audience.
        Include properly formatted APA citations for each example.
        Focus on real scenarios {config['target_audience']} would encounter.
        Use conversational tone with "you" language.
        """

        examples_content = llm_writer._call_openai(
            prompt=examples_prompt,
            max_tokens=600,
            temperature=0.7
        )
        print(f"    ✅ Examples: {len(examples_content.split())} words")

        # Generate topic-specific validation checklist
        checklist_prompt = f"""
        Generate a section titled "{config['topic'].title()} Validation Checklist" specifically for {config['target_audience']}.

        Target audience: {config['target_audience']}
        Pain points: {', '.join(config['pain_points'])}

        Create a checklist of 6-8 specific items this audience should check.
        Make each item actionable and relevant to {config['topic']}.
        Use clear, concise language.
        Format as a bullet point list.
        """

        checklist_content = llm_writer._call_openai(
            prompt=checklist_prompt,
            max_tokens=400,
            temperature=0.7
        )
        print(f"    ✅ Checklist: {len(checklist_content.split())} words")

        # Generate topic-specific FAQ items
        faq_items = llm_writer.generate_faq(config["topic"], num_questions=8)
        print(f"    ✅ FAQ: {len(faq_items)} items")

        # Create TL;DR section specific to this topic and audience
        tldr_prompt = f"""
        Generate a TL;DR (Quick Summary) section for {config['title']} specifically for {config['target_audience']}.

        Focus on these pain points: {', '.join(config['pain_points'])}
        Keywords: {', '.join(config['keywords'])}

        Create 4-5 bullet points that summarize the most important takeaways.
        Make them specific to {config['topic']} and {config['target_audience']}.
        Include relevant statistics or facts if applicable.
        Use action-oriented language.
        """

        tldr_content = llm_writer._call_openai(
            prompt=tldr_prompt,
            max_tokens=300,
            temperature=0.7
        )
        print(f"    ✅ TL;DR: {len(tldr_content.split())} words")

        # Create complete content with topic-specific sections
        total_word_count = (
            len(introduction.split()) +
            len(main_content.split()) +
            len(why_matters_content.split()) +
            len(common_errors.split()) +
            len(examples_content.split()) +
            len(checklist_content.split()) +
            500  # FAQ and other sections
        )

        full_content = f"""---
title: {config["title"]}
description: {config["description"]}
date: 2025-10-15
reading_time: {max(20, total_word_count // 200)} minutes
word_count: {total_word_count}
page_type: mega_guide
url_slug: {config["url_slug"]}
meta_title: {config["title"]}
meta_description: {config["description"]}
breadcrumb_title: {config["title"].replace("Complete ", "").replace("APA Citation Guide for ", "")}
last_updated: December 2024
---

# {config["title"]}

{config["description"]}

**Reading time:** {max(20, total_word_count // 200)} minutes
**Last updated:** December 2024
**APA Edition:** 7th Edition
**Target Audience:** {config['target_audience'].title()}

## 📑 Table of Contents

1. [Quick Summary](#tldr)
2. [Introduction](#introduction)
3. [Why {config['topic'].title()} Matters](#why-it-matters)
4. [Common {config['topic'].title()} Errors](#common-errors)
5. [{config['topic'].title()} Examples](#examples)
6. [Validation Checklist](#validation-checklist)
7. [Frequently Asked Questions](#frequently-asked-questions)

## ⚡ TL;DR - Quick Summary

{tldr_content}

## Introduction

{introduction}

<div class="cta-placement" id="mini-checker-intro">
<h4>🔍 Quick Check Your Citation</h4>
<p>Paste a single citation to instantly validate APA formatting</p>
<!-- MiniChecker component will be mounted here -->
</div>

## Why {config['topic'].title()} Matters

{why_matters_content}

## Common {config['topic'].title()} Errors

{common_errors}

## {config['topic'].title()} Examples

{examples_content}

## {config['topic'].title()} Validation Checklist

{checklist_content}

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

Mastering """ + config['topic'].lower() + """ doesn't have to be overwhelming. With the right approach and tools, you can ensure your APA citations are accurate and professional, demonstrating attention to detail and academic rigor.

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
                "word_count": total_word_count,
                "reading_time": f"{max(20, total_word_count // 200)} minutes",
                "last_updated": "2025-10-15",
                "target_audience": config["target_audience"]
            },
            "word_count": total_word_count
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
    parser = argparse.ArgumentParser(description="Generate mega guides with fully topic-specific content")
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
            print(f"      Topic: {config['topic']}")
            print(f"      Audience: {config['target_audience']}")
            print(f"      Pain points: {', '.join(config['pain_points'])}")
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
            print(f"      Topic: {config['topic']}")
            print(f"      Audience: {config['target_audience']}")
        return True

    # Initialize LLM writer
    print("\n🤖 Initializing LLM writer...")
    llm_writer = LLMWriter()

    # Create output directory
    output_dir = Path(__file__).parent / "dist" / "mega-guides-improved"
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
        print(f"    Audience: {config['target_audience']}")
        print(f"    Pain points: {', '.join(config['pain_points'])}")

        # Generate content
        guide_data = create_topic_specific_content(llm_writer, config)
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
            html_filename = f"mega_guide_{i+1:02d}_{config['url_slug']}-improved.html"
            html_file = output_dir / html_filename
            with open(html_file, 'w') as f:
                f.write(html_content)

            # Save JSON
            json_filename = f"mega_guide_{i+1:02d}_{config['url_slug']}-improved.json"
            json_file = output_dir / json_filename
            with open(json_file, 'w') as f:
                json.dump(guide_data, f, indent=2)

            print(f"    ✅ Generated successfully!")
            print(f"    📁 HTML: {html_filename}")
            print(f"    📁 JSON: {json_filename}")
            print(f"    📊 Words: {guide_data['word_count']:,}")
            print(f"    🌐 URL: http://localhost:8081/mega-guides-improved/{html_filename}")

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
            print(f"    http://localhost:8081/mega-guides-improved/{result['html_file']}")

    if results['failed']:
        print(f"\n❌ Failed guides:")
        for result in results['failed']:
            print(f"  • {result['title']} - {result['error']}")

    return len(results['failed']) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)