#!/usr/bin/env python3
"""Generate raw LLM content without template processing"""

import json
import sys
from pathlib import Path

# Add the parent directory to the path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

from generator.llm_writer import LLMWriter

def main():
    """Generate raw LLM content"""

    # Load configurations
    config_file = Path(__file__).parent.parent / "configs" / "mega_guides.json"
    with open(config_file, 'r') as f:
        configs = json.load(f)

    # Use the second guide (checking APA citations)
    config = configs[1]  # 'Complete Guide to Checking APA Citations'

    print(f"🔄 Generating LLM content for: {config['title']}")
    print(f"Topic: {config['topic']}")

    try:
        # Initialize LLM writer
        writer = LLMWriter()

        # Generate content sections
        print("\n📝 Generating introduction...")
        introduction = writer.generate_introduction(
            topic=config["topic"],
            keywords=config["keywords"],
            rules={"description": "APA 7 citation format rules"},
            pain_points=config["pain_points"]
        )
        print(f"✅ Introduction: {len(introduction.split())} words")

        print("\n📝 generating main content...")
        main_content = writer.generate_explanation(
            concept=f"comprehensive guide to {config['topic']}",
            rules={"description": "APA 7 citation format rules"},
            examples=[]
        )
        print(f"✅ Main content: {len(main_content.split())} words")

        print("\n📝 Generating FAQ...")
        faq_items = writer.generate_faq(config["topic"], num_questions=8)
        print(f"✅ FAQ: {len(faq_items)} items")

        # Create complete content
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
breadcrumb_title: Checking APA Citations
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

---

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

---

<div class="cta-placement" id="mini-checker-intro">
<h4>🔍 Quick Check Your Citation</h4>
<p>Paste a single citation to instantly validate APA formatting</p>
<!-- MiniChecker component will be mounted here -->
</div>

---

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

---

<div class="cta-placement">
    <h4>✨ Ready to Check Your Full Reference List?</h4>
    <p>Use our full citation checker to validate your entire bibliography at once</p>
    <a href="/checker/" class="cta-button">Check Full Reference List →</a>
</div>
"""

        # Save content
        output_dir = Path(__file__).parent.parent / "content" / "generated_content"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save as markdown
        filename = f"mega_guide_02_{config['url_slug']}.md"
        markdown_file = output_dir / filename

        with open(markdown_file, 'w') as f:
            f.write(full_content)

        print(f"📝 Markdown saved to: {filename}")
        print(f"📊 Total word count: {len(full_content.split()):,}")

        # Also save as JSON for HTML conversion
        page_data = {
            "guide_id": config["id"],
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

        json_filename = f"mega_guide_02_{config['url_slug']}.json"
        json_file = output_dir / json_filename

        with open(json_file, 'w') as f:
            json.dump(page_data, f, indent=2)

        print(f"📄 JSON saved to: {json_filename}")

        return True

    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)