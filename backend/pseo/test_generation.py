#!/usr/bin/env python3

import json
import sys
from pathlib import Path

# Add generator to path
sys.path.append('generator')

from content_assembler import ContentAssembler

def main():
    """Generate validation guide with new methods"""

    # Load config
    config_file = Path("configs/validation_guides.json")
    with open(config_file, 'r') as f:
        configs = json.load(f)

    config = configs[0]  # capitalization
    validation_element = config['element_focus']

    print(f"Generating validation guide for: {validation_element}")

    # Generate content
    assembler = ContentAssembler('knowledge_base', 'templates')
    result = assembler.assemble_validation_page(validation_element, config)

    print(f"✅ Generated {len(result['content'])} characters")
    print("✅ Content generation with new methods complete!")

    # Write to review queue
    output_file = Path("../../content/review_queue/validation_00_capitalization_fixed.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'config': config,
            'content': result['content'],
            'template_data': result['template_data'],
            'metadata': result['metadata']
        }, f, indent=2)

    print(f"✅ File written: {output_file}")

    # Check if before_after_examples has content
    template_data = result['template_data']
    before_after = template_data.get('before_after_examples', [])
    tools_tips = template_data.get('tools_tips', {})

    print(f"📊 Before/After examples: {len(before_after)} items")
    print(f"🔧 Tools & tips sections: {len(tools_tips)} keys")

    if before_after:
        print("✅ Before/After examples populated!")
    else:
        print("❌ Before/After examples still empty")

    if tools_tips:
        print("✅ Tools & tips populated!")
    else:
        print("❌ Tools & tips still empty")

if __name__ == "__main__":
    main()