#!/usr/bin/env python3
"""
Convert existing citation datasets from [ITALIC] tags to markdown underscores.
"""
import json
import re
import uuid
from pathlib import Path


def convert_italic_tags_to_markdown(text: str) -> str:
    """
    Convert [ITALIC]text[/ITALIC] to _text_ with proper escaping.
    
    Steps:
    1. Escape existing underscores (literal)
    2. Replace [ITALIC] tags with underscores
    """
    # First escape literal underscores
    text = text.replace('_', r'\_')
    
    # Replace [ITALIC] tags with markdown underscores
    text = text.replace('[ITALIC]', '_')
    text = text.replace('[/ITALIC]', '_')
    
    return text


def convert_file(input_path: Path, output_path: Path):
    """Convert a JSONL file from [ITALIC] to markdown."""
    count = 0
    converted = 0
    
    with open(input_path, 'r') as infile, open(output_path, 'w') as outfile:
        for line in infile:
            count += 1
            data = json.loads(line)
            
            original = data['citation_text']
            markdown = convert_italic_tags_to_markdown(original)
            
            if markdown != original:
                converted += 1
                data['citation_text'] = markdown
            
            outfile.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    return count, converted


def main():
    print("="*80)
    print("CONVERTING [ITALIC] TAGS TO MARKDOWN")
    print("="*80)
    
    datasets_dir = Path('backend/pseo/optimization/datasets')
    
    files_to_convert = [
        ('valid_citations_clean_final.jsonl', 'valid_citations_markdown.jsonl'),
        ('invalid_citations_standardized.jsonl', 'invalid_citations_markdown.jsonl')
    ]
    
    for input_name, output_name in files_to_convert:
        input_path = datasets_dir / input_name
        output_path = datasets_dir / output_name
        
        if not input_path.exists():
            print(f"\n⚠️  Skipping {input_name} (not found)")
            continue
        
        print(f"\n{input_name}:")
        total, converted = convert_file(input_path, output_path)
        print(f"  Total: {total}")
        print(f"  Converted: {converted}")
        print(f"  Output: {output_name}")
        
        # Replace original
        output_path.replace(input_path)
        print(f"  ✓ Replaced original")
    
    print("\n" + "="*80)
    print("CONVERSION COMPLETE")
    print("="*80)
    print("\nExample transformation:")
    print("  [ITALIC]Journal Name[/ITALIC] → _Journal Name_")
    print("  Word_with_underscore → Word\_with\_underscore")


if __name__ == "__main__":
    main()
