#!/usr/bin/env python3
"""
Generate 5 test pages for Task 3.4

This script generates:
- 2 mega guides (5000+ words each)
- 3 source type pages (2000+ words each)

Tracks token usage and costs for each page.
"""
import json
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from backend.pseo.generator.content_assembler import ContentAssembler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Test configurations for all 5 pages
TEST_CONFIGS = {
    # Mega Guide 1: Complete Guide to Checking APA Citations
    "check_citations": {
        "title": "Complete Guide to Checking APA Citations in 2024",
        "description": "Learn how to validate APA 7th edition citations with our comprehensive guide. Discover common errors, validation tools, and expert tips.",
        "keywords": [
            "check APA citations",
            "APA validation",
            "citation checker",
            "APA 7 formatting"
        ],
        "pain_points": [
            "90.9% of papers have citation errors",
            "Manual checking is time-consuming and error-prone",
            "APA 7 introduced many formatting changes",
            "Professors deduct points for formatting errors"
        ],
        "page_type": "mega_guide",
        "url_slug": "check-apa-citations"
    },

    # Mega Guide 2: APA Citation Errors Guide
    "error_guide": {
        "title": "The Ultimate APA Citation Errors Guide: Common Mistakes & How to Fix Them",
        "description": "Master APA citations by learning the 50 most common errors students make. Includes examples, fixes, and prevention strategies.",
        "keywords": [
            "APA citation errors",
            "common APA mistakes",
            "fix APA formatting",
            "APA style errors"
        ],
        "pain_points": [
            "Students repeat the same citation mistakes",
            "Unclear which rules matter most",
            "Database citations confuse students",
            "Inconsistent formatting across sources"
        ],
        "page_type": "mega_guide",
        "url_slug": "apa-citation-errors"
    },

    # Source Type 1: Journal Article
    "journal_article": {
        "title": "How to Cite a Journal Article in APA Format (7th Edition)",
        "description": "Complete guide to citing journal articles in APA 7. Includes format rules, examples for different article types, and common error fixes.",
        "keywords": [
            "cite journal article APA",
            "APA journal citation",
            "journal article reference",
            "scholarly article citation"
        ],
        "page_type": "source_type",
        "url_slug": "how-to-cite-journal-article-apa"
    },

    # Source Type 2: Book
    "book": {
        "title": "How to Cite a Book in APA Format (7th Edition)",
        "description": "Learn how to cite books in APA 7 format. Covers print books, ebooks, edited books, chapters, and multiple editions with examples.",
        "keywords": [
            "cite book APA",
            "APA book citation",
            "book reference APA",
            "cite textbook APA"
        ],
        "page_type": "source_type",
        "url_slug": "how-to-cite-book-apa"
    },

    # Source Type 3: Website
    "website": {
        "title": "How to Cite a Website in APA Format (7th Edition)",
        "description": "Complete guide to citing websites in APA 7. Includes webpage citations, online articles, blog posts, and social media references.",
        "keywords": [
            "cite website APA",
            "APA website citation",
            "online source citation",
            "webpage reference APA"
        ],
        "page_type": "source_type",
        "url_slug": "how-to-cite-website-apa"
    }
}


def save_page(result: dict, config: dict, output_dir: Path):
    """
    Save generated page content and metadata to files

    Args:
        result: Dict with 'content', 'metadata', 'token_usage' from assembler
        config: Original config dict
        output_dir: Directory to save files to
    """
    # Create filename from URL slug
    filename = config["url_slug"]

    # Add YAML front matter with metadata
    metadata = result["metadata"]
    front_matter = f"""---
title: "{metadata.get('meta_title', config.get('title', ''))}"
description: "{metadata.get('meta_description', config.get('description', ''))}"
date: {metadata.get('last_updated', datetime.now().strftime("%Y-%m-%d"))}
reading_time: {metadata.get('reading_time', '')}
word_count: {metadata.get('word_count', 0)}
---

"""

    # Combine front matter with content
    full_content = front_matter + result["content"]

    # Save markdown content with front matter
    content_file = output_dir / f"{filename}.md"
    content_file.write_text(full_content, encoding='utf-8')
    logger.info(f"  Saved content: {content_file}")

    # Save metadata + token usage
    stats = {
        "config": config,
        "metadata": result["metadata"],
        "token_usage": result["token_usage"],
        "generated_at": datetime.now().isoformat()
    }

    stats_file = output_dir / f"{filename}_stats.json"
    stats_file.write_text(json.dumps(stats, indent=2), encoding='utf-8')
    logger.info(f"  Saved stats: {stats_file}")

    return stats


def main():
    """Generate all 5 test pages"""
    logger.info("=" * 80)
    logger.info("GENERATING 5 TEST PAGES FOR TASK 3.4")
    logger.info("=" * 80)

    # Initialize assembler
    kb_dir = Path(__file__).parent.parent / "knowledge_base"
    templates_dir = Path(__file__).parent.parent / "templates"
    output_dir = Path(__file__).parent.parent.parent.parent / "content" / "test"

    logger.info(f"Knowledge base: {kb_dir}")
    logger.info(f"Templates: {templates_dir}")
    logger.info(f"Output: {output_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    assembler = ContentAssembler(str(kb_dir), str(templates_dir))

    # Track cumulative statistics
    cumulative_stats = {
        "total_pages": 0,
        "total_words": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_cost": 0.0,
        "pages": []
    }

    # Generate mega guides
    logger.info("\n" + "=" * 80)
    logger.info("GENERATING MEGA GUIDES")
    logger.info("=" * 80)

    for key in ["check_citations", "error_guide"]:
        config = TEST_CONFIGS[key]
        logger.info(f"\n[{cumulative_stats['total_pages'] + 1}/5] {config['title']}")

        try:
            result = assembler.assemble_mega_guide(
                topic=key.replace("_", " "),
                config=config
            )

            # Save to files
            stats = save_page(result, config, output_dir)

            # Update cumulative stats
            cumulative_stats["total_pages"] += 1
            cumulative_stats["total_words"] += result["metadata"]["word_count"]
            cumulative_stats["total_input_tokens"] += result["token_usage"]["total_input_tokens"]
            cumulative_stats["total_output_tokens"] += result["token_usage"]["total_output_tokens"]
            cumulative_stats["total_cost"] += result["token_usage"]["total_cost_usd"]
            cumulative_stats["pages"].append({
                "title": config["title"],
                "type": "mega_guide",
                "words": result["metadata"]["word_count"],
                "tokens": result["token_usage"]["total_tokens"],
                "cost": result["token_usage"]["total_cost_usd"]
            })

            logger.info(f"  ✓ Success: {result['metadata']['word_count']} words")
            logger.info(f"  ✓ Cost: ${result['token_usage']['total_cost_usd']:.6f}")

        except Exception as e:
            logger.error(f"  ✗ Failed: {str(e)}")
            raise

    # Generate source type pages
    logger.info("\n" + "=" * 80)
    logger.info("GENERATING SOURCE TYPE PAGES")
    logger.info("=" * 80)

    for key in ["journal_article", "book", "website"]:
        config = TEST_CONFIGS[key]
        logger.info(f"\n[{cumulative_stats['total_pages'] + 1}/5] {config['title']}")

        try:
            result = assembler.assemble_source_type_page(
                source_type=key.replace("_", " "),
                config=config
            )

            # Save to files
            stats = save_page(result, config, output_dir)

            # Update cumulative stats
            cumulative_stats["total_pages"] += 1
            cumulative_stats["total_words"] += result["metadata"]["word_count"]
            cumulative_stats["total_input_tokens"] += result["token_usage"]["total_input_tokens"]
            cumulative_stats["total_output_tokens"] += result["token_usage"]["total_output_tokens"]
            cumulative_stats["total_cost"] += result["token_usage"]["total_cost_usd"]
            cumulative_stats["pages"].append({
                "title": config["title"],
                "type": "source_type",
                "words": result["metadata"]["word_count"],
                "tokens": result["token_usage"]["total_tokens"],
                "cost": result["token_usage"]["total_cost_usd"]
            })

            logger.info(f"  ✓ Success: {result['metadata']['word_count']} words")
            logger.info(f"  ✓ Cost: ${result['token_usage']['total_cost_usd']:.6f}")

        except Exception as e:
            logger.error(f"  ✗ Failed: {str(e)}")
            raise

    # Print final summary
    logger.info("\n" + "=" * 80)
    logger.info("GENERATION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total pages generated: {cumulative_stats['total_pages']}")
    logger.info(f"Total words: {cumulative_stats['total_words']:,}")
    logger.info(f"Total input tokens: {cumulative_stats['total_input_tokens']:,}")
    logger.info(f"Total output tokens: {cumulative_stats['total_output_tokens']:,}")
    logger.info(f"Total cost: ${cumulative_stats['total_cost']:.6f}")
    logger.info(f"\nAverage per page:")
    logger.info(f"  Words: {cumulative_stats['total_words'] // cumulative_stats['total_pages']:,}")
    logger.info(f"  Cost: ${cumulative_stats['total_cost'] / cumulative_stats['total_pages']:.6f}")

    # Save cumulative stats
    summary_file = output_dir / "_generation_summary.json"
    summary_file.write_text(json.dumps(cumulative_stats, indent=2), encoding='utf-8')
    logger.info(f"\nSummary saved: {summary_file}")

    logger.info("\n" + "=" * 80)
    logger.info("✓ All files saved to: content/test/")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
