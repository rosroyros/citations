#!/usr/bin/env python3
"""Generate just one guide to test the process."""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from generator.content_assembler import ContentAssembler
from review.llm_reviewer import LLMReviewer

def main():
    # Load configurations
    config_file = Path(__file__).parent.parent / "configs" / "mega_guides.json"
    with open(config_file, 'r') as f:
        configs = json.load(f)

    config = configs[0]  # First guide

    print(f"Generating: {config['title']}")

    # Initialize
    knowledge_base_dir = Path(__file__).parent.parent / "knowledge_base"
    templates_dir = Path(__file__).parent.parent / "templates"

    assembler = ContentAssembler(str(knowledge_base_dir), str(templates_dir))
    reviewer = LLMReviewer()

    # Prepare config
    assembler_config = {
        "title": config["title"],
        "description": config["description"],
        "keywords": config["keywords"],
        "pain_points": config["pain_points"],
        "target_audience": config["target_audience"],
        "url_slug": config["url_slug"]
    }

    # Generate
    result = assembler.assemble_mega_guide(config["topic"], assembler_config)
    print(f"Generated {result['metadata']['word_count']} words")

    # Save without LLM review for now
    output_dir = Path(__file__).parent.parent.parent / "content" / "review_queue"
    output_dir.mkdir(parents=True, exist_ok=True)

    page_data = {
        "guide_id": config["id"],
        "title": config["title"],
        "content": result["content"],
        "metadata": result["metadata"],
        "word_count": result["metadata"]["word_count"]
    }

    filename = f"test_{config['url_slug']}.json"
    with open(output_dir / filename, 'w') as f:
        json.dump(page_data, f, indent=2)

    print(f"Saved to: {filename}")

if __name__ == "__main__":
    main()