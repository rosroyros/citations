#!/usr/bin/env python3
"""
Synthetic Expansion Phase for APA Citation Validator
Generates 5 variants (mix of valid/invalid) from each seed citation
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Dict
import openai
from tqdm import tqdm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OpenAI setup
openai.api_key = os.environ.get("OPENAI_API_KEY")

EXPANSION_PROMPT = """You are generating **APA 7th edition citation examples** for training a citation validator.

Given this seed citation, create 5 variations — mix valid and invalid examples.

**Seed Citation:**
{{seed_citation}}

**Instructions:**
- Generate exactly 5 variations
- At least 2 must be INVALID (have APA formatting errors)
- At least 2 must be VALID (perfectly formatted)
- Vary: punctuation, italics (use _markdown_), author counts, DOI presence/format, capitalization, spacing
- Preserve the general source type (book/journal/webpage/etc)
- Invalid examples should have realistic mistakes students make

**Output Format:**
Return a JSON object with a "variants" key containing an array of 5 objects, each with:
- "citation": the citation string (use _markdown_ for italics)
- "is_valid": true or false
- "explanation": brief reason why it's valid/invalid

Example output structure:
{{
  "variants": [
    {{
      "citation": "Doe, A., & Lee, B. (2019). _Social networks_. Cambridge.",
      "is_valid": true,
      "explanation": "Correct APA format with proper punctuation and italics"
    }},
    {{
      "citation": "Doe A. Lee B. (2019) Social networks Cambridge",
      "is_valid": false,
      "explanation": "Missing punctuation, no italics, improper name formatting"
    }}
  ]
}}

Generate 5 variations now:"""


def load_seed_citations(filepath: Path) -> List[Dict]:
    """Load seed citations from JSONL file"""
    logger.info(f"Loading seed citations from {filepath}")
    seeds = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                seeds.append(json.loads(line))
    logger.info(f"Loaded {len(seeds)} seed citations")
    return seeds


def generate_variants(seed: Dict, model: str = "gpt-4o") -> List[Dict]:
    """Generate 5 variants from a seed citation using GPT-4o"""
    prompt = EXPANSION_PROMPT.replace('{{seed_citation}}', seed['citation_text'])

    try:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert in APA 7th edition citation formatting."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        # Try to extract JSON array from the response
        variants_data = json.loads(content)

        # Handle both direct array and wrapped in object
        if isinstance(variants_data, dict):
            variants = variants_data.get('variants', variants_data.get('citations', []))
        else:
            variants = variants_data

        # Validate structure
        if not isinstance(variants, list) or len(variants) != 5:
            logger.warning(f"Expected 5 variants, got {len(variants) if isinstance(variants, list) else 'invalid'}")
            return []

        # Add metadata
        for variant in variants:
            if all(k in variant for k in ['citation', 'is_valid', 'explanation']):
                variant['metadata'] = {
                    'source': 'synthetic_expansion',
                    'seed_id': seed['citation_id'],
                    'model': model
                }
            else:
                logger.warning(f"Variant missing required fields: {variant}")
                return []

        return variants

    except Exception as e:
        logger.error(f"Failed to generate variants for {seed['citation_id']}: {e}")
        return []


def expand_dataset(seed_file: Path, output_file: Path, model: str = "gpt-4o"):
    """Expand entire dataset by generating variants for each seed"""
    seeds = load_seed_citations(seed_file)

    logger.info(f"Starting expansion with model: {model}")
    logger.info(f"Target: ~{len(seeds) * 5} variants from {len(seeds)} seeds")

    all_variants = []
    failed_seeds = []

    for seed in tqdm(seeds, desc="Expanding dataset"):
        variants = generate_variants(seed, model=model)

        if variants:
            all_variants.extend(variants)
        else:
            failed_seeds.append(seed['citation_id'])

    logger.info(f"✅ Generated {len(all_variants)} variants")
    logger.info(f"❌ Failed seeds: {len(failed_seeds)}")

    if failed_seeds:
        logger.warning(f"Failed seed IDs: {failed_seeds[:10]}...")

    # Save expanded dataset
    logger.info(f"Saving to {output_file}")
    with open(output_file, 'w') as f:
        for variant in all_variants:
            f.write(json.dumps(variant) + '\n')

    # Stats
    valid_count = sum(1 for v in all_variants if v['is_valid'])
    invalid_count = len(all_variants) - valid_count

    logger.info(f"📊 Dataset stats:")
    logger.info(f"  Total variants: {len(all_variants)}")
    logger.info(f"  Valid: {valid_count} ({valid_count/len(all_variants)*100:.1f}%)")
    logger.info(f"  Invalid: {invalid_count} ({invalid_count/len(all_variants)*100:.1f}%)")

    return all_variants


if __name__ == "__main__":
    import sys

    # Paths
    base_dir = Path(__file__).parent
    seed_file = base_dir / "manualy_curated_citations_raw_20251023.jsonl"
    output_file = base_dir / "expanded_citations_synthetic.jsonl"

    if not seed_file.exists():
        logger.error(f"Seed file not found: {seed_file}")
        sys.exit(1)

    # Check API key
    if not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    # Run expansion
    expand_dataset(seed_file, output_file, model="gpt-4o")

    logger.info("✨ Expansion complete!")
