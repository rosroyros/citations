#!/usr/bin/env python3
"""Generate just one mega guide with the working approach"""

import json
import sys
from pathlib import Path

# Add the parent directory to the path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

from generator.content_assembler import ContentAssembler

def main():
    """Generate a single mega guide"""

    # Load configurations
    config_file = Path(__file__).parent.parent / "configs" / "mega_guides.json"
    with open(config_file, 'r') as f:
        configs = json.load(f)

    # Use the second guide (checking APA citations)
    config = configs[1]  # 'Complete Guide to Checking APA Citations'

    print(f"🔄 Generating: {config['title']}")
    print(f"Topic: {config['topic']}")

    # Initialize
    knowledge_base_dir = Path(__file__).parent.parent / "knowledge_base"
    templates_dir = Path(__file__).parent.parent / "templates"

    try:
        assembler = ContentAssembler(str(knowledge_base_dir), str(templates_dir))

        # Prepare config
        assembler_config = {
            "title": config["title"],
            "description": config["description"],
            "keywords": config["keywords"],
            "pain_points": config["pain_points"],
            "target_audience": config["target_audience"],
            "url_slug": config["url_slug"]
        }

        # Generate content
        result = assembler.assemble_mega_guide(config["topic"], assembler_config)
        print(f"✅ Generated {result['metadata']['word_count']} words")

        # Save the content for manual conversion
        output_dir = Path(__file__).parent.parent / "content" / "generated_content"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save as markdown file for conversion
        filename = f"mega_guide_02_{config['url_slug']}.md"
        markdown_file = output_dir / filename

        with open(markdown_file, 'w') as f:
            f.write(result["content"])

        print(f"📝 Markdown saved to: {filename}")

        # Also save as JSON for our HTML generator
        page_data = {
            "guide_id": config["id"],
            "title": config["title"],
            "content": result["content"],
            "metadata": result["metadata"],
            "word_count": result["metadata"]["word_count"]
        }

        json_filename = f"mega_guide_02_{config['url_slug']}.json"
        json_file = output_dir / json_filename

        with open(json_file, 'w') as f:
            json.dump(page_data, f, indent=2)

        print(f"📄 JSON saved to: {json_filename}")
        print(f"📊 Word count: {result['metadata']['word_count']:,}")

        return True

    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)