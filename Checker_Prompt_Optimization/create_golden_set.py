#!/usr/bin/env python3
"""
Create a golden set for testing correction quality.

Methodology:
1. Extract valid citations from test_set_121_corrected.jsonl
2. Apply controlled REVERSIBLE mutations to introduce specific errors
3. Ensure good distribution across mutation types
4. Save as correction_golden_set.jsonl
"""

import json
import re

INPUT_PATH = "Checker_Prompt_Optimization/test_set_121_corrected.jsonl"
OUTPUT_PATH = "Checker_Prompt_Optimization/correction_golden_set.jsonl"


def remove_italics(citation: str) -> tuple[str, str]:
    """Remove _underscores_ around italicized text."""
    italics_pattern = r'_([^_]+)_'
    matches = re.findall(italics_pattern, citation)
    if not matches:
        return None, None
    
    mutated = re.sub(r'_([^_]+)_', r'\1', citation)
    return mutated, "removed_italics"


def wrong_ampersand(citation: str) -> tuple[str, str]:
    """Replace & with 'and'."""
    if ', &' in citation:
        mutated = citation.replace(', &', ', and')
        return mutated, "ampersand_to_and"
    return None, None


def remove_comma_before_ampersand(citation: str) -> tuple[str, str]:
    """Remove Oxford comma before &."""
    if ', &' in citation:
        mutated = citation.replace(', &', ' &', 1)
        return mutated, "missing_oxford_comma"
    return None, None


def main():
    # Load valid citations
    with open(INPUT_PATH, 'r') as f:
        all_data = [json.loads(line) for line in f if line.strip()]
    
    valid_citations = [d for d in all_data if d.get('ground_truth') == True]
    print(f"Found {len(valid_citations)} valid citations")
    
    golden_set = []
    
    # First, collect candidates for each mutation type
    italics_candidates = []
    ampersand_candidates = []
    comma_candidates = []
    
    for item in valid_citations:
        original = item['citation']
        
        # Check which mutations are applicable
        if re.search(r'_[^_]+_', original):
            italics_candidates.append(item)
        if ', &' in original:
            ampersand_candidates.append(item)
            comma_candidates.append(item)
    
    print(f"\nCandidates: italics={len(italics_candidates)}, ampersand={len(ampersand_candidates)}, comma={len(comma_candidates)}")
    
    # Build golden set with good distribution
    # Target: 10 removed_italics, 5 ampersand_to_and, 5 missing_oxford_comma
    
    # removed_italics (10)
    for item in italics_candidates[:10]:
        mutated, mt = remove_italics(item['citation'])
        golden_set.append({
            "original_valid": item['citation'],
            "mutated": mutated,
            "mutation_type": mt
        })
        print(f"✓ {mt}: {item['citation'][:60]}...")
    
    # ampersand_to_and (5) - skip ones already used for italics
    used_citations = {g['original_valid'] for g in golden_set}
    count = 0
    for item in ampersand_candidates:
        if item['citation'] not in used_citations and count < 5:
            mutated, mt = wrong_ampersand(item['citation'])
            if mutated:
                golden_set.append({
                    "original_valid": item['citation'],
                    "mutated": mutated,
                    "mutation_type": mt
                })
                used_citations.add(item['citation'])
                count += 1
                print(f"✓ {mt}: {item['citation'][:60]}...")
    
    # missing_oxford_comma (5) - skip ones already used
    count = 0
    for item in comma_candidates:
        if item['citation'] not in used_citations and count < 5:
            mutated, mt = remove_comma_before_ampersand(item['citation'])
            if mutated:
                golden_set.append({
                    "original_valid": item['citation'],
                    "mutated": mutated,
                    "mutation_type": mt
                })
                used_citations.add(item['citation'])
                count += 1
                print(f"✓ {mt}: {item['citation'][:60]}...")
    
    # Save golden set
    with open(OUTPUT_PATH, 'w') as f:
        for item in golden_set:
            f.write(json.dumps(item) + '\n')
    
    # Summary
    mutation_counts = {}
    for item in golden_set:
        mt = item['mutation_type']
        mutation_counts[mt] = mutation_counts.get(mt, 0) + 1
    
    print(f"\n✅ Created golden set with {len(golden_set)} entries")
    print(f"📄 Saved to {OUTPUT_PATH}")
    print(f"\nMutation distribution:")
    for mt, count in sorted(mutation_counts.items(), key=lambda x: -x[1]):
        print(f"  {mt}: {count}")


if __name__ == "__main__":
    main()
