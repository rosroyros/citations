#!/usr/bin/env python3
"""
Merge curated seeds with synthetic variants and deduplicate
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Set
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def citation_hash(citation_text: str) -> str:
    """Create hash of normalized citation for deduplication"""
    # Normalize: lowercase, remove extra whitespace
    normalized = ' '.join(citation_text.lower().split())
    return hashlib.md5(normalized.encode()).hexdigest()


def load_seeds(filepath: Path) -> List[Dict]:
    """Load original curated seed citations"""
    logger.info(f"Loading seed citations from {filepath}")
    seeds = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                # Convert to standard format
                entry = {
                    'citation': data['citation_text'],
                    'is_valid': True,  # All seeds are valid
                    'explanation': 'Manually curated valid APA 7th edition citation',
                    'metadata': {
                        'source': 'manual_curation',
                        'seed_id': data.get('citation_id'),
                        'source_type': data.get('source_type'),
                        'original_metadata': data.get('metadata', {})
                    }
                }
                seeds.append(entry)
    logger.info(f"Loaded {len(seeds)} seed citations")
    return seeds


def load_synthetic(filepath: Path) -> List[Dict]:
    """Load synthetic variants"""
    logger.info(f"Loading synthetic variants from {filepath}")
    variants = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                # Ensure metadata exists
                if 'metadata' not in data:
                    data['metadata'] = {}
                data['metadata']['source'] = 'synthetic_expansion'
                variants.append(data)
    logger.info(f"Loaded {len(variants)} synthetic variants")
    return variants


def deduplicate(entries: List[Dict]) -> List[Dict]:
    """Remove duplicate citations based on normalized text"""
    logger.info("Deduplicating dataset...")
    seen_hashes: Set[str] = set()
    unique_entries = []
    duplicates = 0

    for entry in entries:
        cite_hash = citation_hash(entry['citation'])
        if cite_hash not in seen_hashes:
            seen_hashes.add(cite_hash)
            unique_entries.append(entry)
        else:
            duplicates += 1

    logger.info(f"Removed {duplicates} duplicates")
    logger.info(f"Unique entries: {len(unique_entries)}")
    return unique_entries


def validate_entries(entries: List[Dict]) -> List[Dict]:
    """Validate and clean entries"""
    logger.info("Validating entries...")
    valid_entries = []
    invalid_count = 0

    for entry in entries:
        # Check required fields
        if not all(k in entry for k in ['citation', 'is_valid']):
            invalid_count += 1
            continue

        # Normalize is_valid to boolean
        if isinstance(entry['is_valid'], str):
            entry['is_valid'] = entry['is_valid'].lower() in ['true', '1', 'yes']

        # Ensure explanation exists
        if 'explanation' not in entry:
            entry['explanation'] = ''

        valid_entries.append(entry)

    logger.info(f"Validated {len(valid_entries)} entries, skipped {invalid_count} invalid")
    return valid_entries


def merge_and_clean(seed_file: Path, synthetic_file: Path, output_file: Path):
    """Merge seeds and synthetic variants, deduplicate, and save"""

    # Load both datasets
    seeds = load_seeds(seed_file)
    synthetics = load_synthetic(synthetic_file)

    # Combine
    all_entries = seeds + synthetics
    logger.info(f"Total entries before cleaning: {len(all_entries)}")

    # Validate
    validated = validate_entries(all_entries)

    # Deduplicate
    unique = deduplicate(validated)

    # Calculate stats
    valid_count = sum(1 for e in unique if e['is_valid'])
    invalid_count = len(unique) - valid_count

    seed_count = sum(1 for e in unique if e['metadata'].get('source') == 'manual_curation')
    synthetic_count = sum(1 for e in unique if e['metadata'].get('source') == 'synthetic_expansion')

    logger.info(f"📊 Final dataset stats:")
    logger.info(f"  Total entries: {len(unique)}")
    logger.info(f"  Valid: {valid_count} ({valid_count/len(unique)*100:.1f}%)")
    logger.info(f"  Invalid: {invalid_count} ({invalid_count/len(unique)*100:.1f}%)")
    logger.info(f"  From seeds: {seed_count}")
    logger.info(f"  From synthetic: {synthetic_count}")

    # Save
    logger.info(f"Saving to {output_file}")
    with open(output_file, 'w') as f:
        for entry in unique:
            f.write(json.dumps(entry) + '\n')

    logger.info("✅ Merge and clean complete!")

    return {
        'total': len(unique),
        'valid': valid_count,
        'invalid': invalid_count,
        'seed_count': seed_count,
        'synthetic_count': synthetic_count
    }


if __name__ == "__main__":
    import sys

    base_dir = Path(__file__).parent
    seed_file = base_dir / "manualy_curated_citations_raw_20251023.jsonl"
    synthetic_file = base_dir / "expanded_citations_synthetic.jsonl"
    output_file = base_dir / "final_merged_dataset.jsonl"

    # Check files
    if not seed_file.exists():
        logger.error(f"Seed file not found: {seed_file}")
        sys.exit(1)

    if not synthetic_file.exists():
        logger.error(f"Synthetic file not found: {synthetic_file}")
        logger.error("Run synthetic_expansion.py first!")
        sys.exit(1)

    # Merge and clean
    stats = merge_and_clean(seed_file, synthetic_file, output_file)

    logger.info("✨ Done!")
    sys.exit(0)
