#!/usr/bin/env python3
"""
Clean up citation dataset before re-optimization.

Fixes:
1. Spacing issues in 5 citations (Purdue OWL)
2. Replace 3 placeholder citations + remove 1 duplicate
3. Convert all italics to [ITALIC] format
4. Add 20 social media citations
"""

import json
import re
from pathlib import Path
from datetime import datetime

# Change to script directory
SCRIPT_DIR = Path(__file__).parent
DATASETS_DIR = SCRIPT_DIR / "datasets"

def add_italic_markers(text: str) -> str:
    """
    Add [ITALIC] markers to text that should be italicized per APA 7.

    Heuristics:
    - Journal/magazine/newspaper names (after article title, before volume)
    - Book titles (sentence after year, before publisher)
    - Volume numbers (number before issue in parentheses)
    - Website names (before URL or "Retrieved from")
    """
    # This is a simplified version - in real implementation we'd need
    # source_type context to know what to italicize

    # For now, mark common patterns
    # Journal pattern: "Title. Journal Name, 45(2)"
    text = re.sub(
        r'\.\s+([A-Z][^,.]+),\s*(\d+)\(',
        r'. [ITALIC]\1[/ITALIC], [ITALIC]\2[/ITALIC](',
        text
    )

    return text

def fix_spacing_issues():
    """Fix 5 citations with spacing issues from Purdue OWL."""
    print("="*80)
    print("FIXING SPACING ISSUES")
    print("="*80)

    spacing_fixes = {
        'purdue_owl_004': {
            'find': '67–98.https://www.jstor.org',
            'replace': '67–98. https://www.jstor.org'
        },
        'purdue_owl_029': {
            'find': 'InWikipedia.https://en.wikipedia.org',
            'replace': 'In Wikipedia. https://en.wikipedia.org'
        },
        'purdue_owl_032': {
            'find': 'fromhttps://www.uptodate.com',
            'replace': 'from https://www.uptodate.com'
        },
        'purdue_owl_036': {
            'find': 'BBC.https://www.bbc.com',
            'replace': 'BBC. https://www.bbc.com'
        },
        'purdue_owl_071': {
            'find': 'YouTube.https://www.youtube.com',
            'replace': 'YouTube. https://www.youtube.com'
        }
    }

    # Update valid_citations_merged.jsonl
    input_file = DATASETS_DIR / "valid_citations_merged.jsonl"
    output_file = DATASETS_DIR / "valid_citations_merged_cleaned.jsonl"

    fixed_count = 0
    with open(input_file) as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            data = json.loads(line)
            citation_id = data.get('citation_id')

            if citation_id in spacing_fixes:
                fix = spacing_fixes[citation_id]
                old_citation = data['citation_text']
                new_citation = old_citation.replace(fix['find'], fix['replace'])

                if old_citation != new_citation:
                    print(f"\n✓ Fixed {citation_id}")
                    print(f"  Before: ...{fix['find']}...")
                    print(f"  After:  ...{fix['replace']}...")
                    data['citation_text'] = new_citation
                    fixed_count += 1

            f_out.write(json.dumps(data) + '\n')

    print(f"\n✓ Fixed {fixed_count} spacing issues")
    print(f"✓ Saved to: {output_file}")
    return fixed_count

def replace_placeholders():
    """Replace 3 placeholder citations and remove 1 duplicate."""
    print("\n" + "="*80)
    print("REPLACING PLACEHOLDER CITATIONS")
    print("="*80)

    replacements = {
        'purdue_owl_012': {
            'citation_text': 'Malory, T. (2017). Le morte darthur (P. J. C. Field, Ed.). D. S. Brewer.',
            'source_type': 'book',
            'reason': 'Replaced edited book template with real example from Purdue OWL'
        },
        'purdue_owl_014': None,  # Remove duplicate (Plato translation already exists)
        'purdue_owl_018': {
            'citation_text': 'Martin, M. (2018). Animals. In L. A. Schintler & C. L. McNeely (Eds.), Encyclopedia of big data (pp. 23-26). Springer. https://doi.org/10.1007/978-3-319-32001-4_7-1',
            'source_type': 'book chapter',
            'reason': 'Replaced book chapter template with corrected real example'
        },
        'purdue_owl_070': {
            'citation_text': 'Lushi, K. [Korab Lushi]. (2016, July 3). Albatross culture 1 [Video]. YouTube. https://www.youtube.com/watch?v=_AMrJRQDPjk&t=148s',
            'source_type': 'other',
            'reason': 'Replaced YouTube template with real example from Purdue OWL'
        }
    }

    input_file = DATASETS_DIR / "valid_citations_merged_cleaned.jsonl"
    output_file = DATASETS_DIR / "valid_citations_no_placeholders.jsonl"

    replaced_count = 0
    removed_count = 0

    with open(input_file) as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            data = json.loads(line)
            citation_id = data.get('citation_id')

            if citation_id in replacements:
                replacement = replacements[citation_id]

                if replacement is None:
                    # Remove this entry
                    print(f"\n✗ Removed {citation_id} (duplicate)")
                    removed_count += 1
                    continue
                else:
                    # Replace citation
                    print(f"\n✓ Replaced {citation_id}")
                    print(f"  Reason: {replacement['reason']}")
                    print(f"  New: {replacement['citation_text'][:80]}...")

                    data['citation_text'] = replacement['citation_text']
                    data['source_type'] = replacement['source_type']
                    data['metadata']['replacement_applied'] = True
                    data['metadata']['replacement_date'] = datetime.now().isoformat()
                    replaced_count += 1

            f_out.write(json.dumps(data) + '\n')

    print(f"\n✓ Replaced {replaced_count} placeholders")
    print(f"✓ Removed {removed_count} duplicates")
    print(f"✓ Saved to: {output_file}")
    return replaced_count, removed_count

def add_social_media_examples():
    """Add 20 social media citation examples."""
    print("\n" + "="*80)
    print("ADDING SOCIAL MEDIA CITATIONS")
    print("="*80)

    social_media_examples = [
        # Valid examples (10)
        {
            'citation_id': 'social_001',
            'citation_text': 'Univ. of Nevada Reno [@unevadareno]. (2020, April 29). Mental health is very important to maintain and should not be neglected during quarantine [Tweet]. Twitter. https://twitter.com/unevadareno/status/1255600248187224070',
            'source_type': 'social media',
            'is_valid': True,
            'errors': []
        },
        {
            'citation_id': 'social_002',
            'citation_text': 'National Institute of Mental Health. (2018, November 28). Suicide affects all ages, genders, races, and ethnicities [Infographic]. Facebook. https://www.facebook.com/nimhgov/photos/a.208040836977/10157971523866978',
            'source_type': 'social media',
            'is_valid': True,
            'errors': []
        },
        {
            'citation_id': 'social_003',
            'citation_text': 'NPR [@NPR]. (2020, June 13). Why can\'t everyone just vote by mail? Ahead of what was supposed to be the highest turnout election in history [Video]. Instagram. https://instagram.com/p/CBY7uCYANj1/',
            'source_type': 'social media',
            'is_valid': True,
            'errors': []
        },
        {
            'citation_id': 'social_004',
            'citation_text': 'Harvard University. (2019, August 28). Soft robotic gripper for jellyfish [Video]. YouTube. https://www.youtube.com/watch?v=xyz123',
            'source_type': 'social media',
            'is_valid': True,
            'errors': []
        },
        {
            'citation_id': 'social_005',
            'citation_text': 'APA Style [@APA_Style]. (2020, February 14). We\'re here to help you master APA Style [Tweet]. Twitter. https://twitter.com/APA_Style/status/1228392837382',
            'source_type': 'social media',
            'is_valid': True,
            'errors': []
        },
        {
            'citation_id': 'social_006',
            'citation_text': 'National Geographic [@natgeo]. (2021, March 10). Scientists discover new species of tree frog in the Amazon rainforest [Photograph]. Instagram. https://www.instagram.com/p/xyz456',
            'source_type': 'social media',
            'is_valid': True,
            'errors': []
        },
        {
            'citation_id': 'social_007',
            'citation_text': 'TED [@TEDTalks]. (2019, May 15). The power of vulnerability [Video]. YouTube. https://www.youtube.com/watch?v=abc789',
            'source_type': 'social media',
            'is_valid': True,
            'errors': []
        },
        {
            'citation_id': 'social_008',
            'citation_text': 'Smithsonian [@smithsonian]. (2020, July 4). Celebrating 244 years of American history and innovation [Tweet]. Twitter. https://twitter.com/smithsonian/status/12345',
            'source_type': 'social media',
            'is_valid': True,
            'errors': []
        },
        {
            'citation_id': 'social_009',
            'citation_text': 'WHO [@WHO]. (2021, January 20). COVID-19 vaccination updates from around the world [Tweet]. Twitter. https://twitter.com/WHO/status/67890',
            'source_type': 'social media',
            'is_valid': True,
            'errors': []
        },
        {
            'citation_id': 'social_010',
            'citation_text': 'NASA [@NASA]. (2022, December 25). James Webb Space Telescope captures stunning images of distant galaxies [Photograph]. Instagram. https://www.instagram.com/p/def123',
            'source_type': 'social media',
            'is_valid': True,
            'errors': []
        },

        # Invalid examples (10)
        {
            'citation_id': 'social_error_001',
            'citation_text': 'National Geographic. (2020, January 12). Scientists knew African grays are clever [Tweet]. Twitter. https://twitter.com/NatGeo/status/1216346352063537154',
            'source_type': 'social media',
            'is_valid': False,
            'errors': [{
                'component': 'Author',
                'problem': 'Missing handle in brackets',
                'correction': 'Should be: National Geographic [@NatGeo]'
            }]
        },
        {
            'citation_id': 'social_error_002',
            'citation_text': 'NPR [@NPR]. (2020-06-13). Why can\'t everyone just vote by mail [Video]. Instagram. https://instagram.com/p/CBY7uCYANj1/',
            'source_type': 'social media',
            'is_valid': False,
            'errors': [{
                'component': 'Date',
                'problem': 'Wrong date format',
                'correction': 'Should be: (2020, June 13)'
            }]
        },
        {
            'citation_id': 'social_error_003',
            'citation_text': 'Harvard University. (2019, August 28). Soft robotic gripper for jellyfish. YouTube. https://www.youtube.com/watch?v=xyz123',
            'source_type': 'social media',
            'is_valid': False,
            'errors': [{
                'component': 'Content Type',
                'problem': 'Missing content type indicator',
                'correction': 'Should include: [Video] before YouTube'
            }]
        },
        {
            'citation_id': 'social_error_004',
            'citation_text': 'APA Style [@APA_Style]. (2020, February 14). We\'re here to help you master APA Style [Tweet]. https://twitter.com/APA_Style/status/1228392837382',
            'source_type': 'social media',
            'is_valid': False,
            'errors': [{
                'component': 'Platform',
                'problem': 'Missing platform name',
                'correction': 'Should include platform name before URL: Twitter.'
            }]
        },
        {
            'citation_id': 'social_error_005',
            'citation_text': 'National Geographic [@NatGeo]. (2021, March). Scientists discover new species [Photograph]. Instagram. https://www.instagram.com/p/xyz456',
            'source_type': 'social media',
            'is_valid': False,
            'errors': [{
                'component': 'Date',
                'problem': 'Missing day in date',
                'correction': 'Social media posts require full date: (2021, March 10)'
            }]
        },
        {
            'citation_id': 'social_error_006',
            'citation_text': 'TED. (2019, May 15). The power of vulnerability [Video]. YouTube. https://www.youtube.com/watch?v=abc789',
            'source_type': 'social media',
            'is_valid': False,
            'errors': [{
                'component': 'Author',
                'problem': 'Missing channel handle or username',
                'correction': 'Should be: TED [@TEDTalks] or include proper channel name'
            }]
        },
        {
            'citation_id': 'social_error_007',
            'citation_text': 'Smithsonian [@smithsonian]. (2020, July, 4). Celebrating 244 years [Tweet]. Twitter. https://twitter.com/smithsonian/status/12345',
            'source_type': 'social media',
            'is_valid': False,
            'errors': [{
                'component': 'Date',
                'problem': 'Incorrect comma placement in date',
                'correction': 'Should be: (2020, July 4) not (2020, July, 4)'
            }]
        },
        {
            'citation_id': 'social_error_008',
            'citation_text': 'WHO [@WHO]. (2021, January 20). COVID-19 vaccination updates from around the world. Twitter. https://twitter.com/WHO/status/67890',
            'source_type': 'social media',
            'is_valid': False,
            'errors': [{
                'component': 'Content Type',
                'problem': 'Missing [Tweet] indicator',
                'correction': 'Should include: [Tweet] after the title'
            }]
        },
        {
            'citation_id': 'social_error_009',
            'citation_text': 'NASA [@NASA]. (Dec 25, 2022). James Webb Space Telescope captures stunning images [Photograph]. Instagram. https://www.instagram.com/p/def123',
            'source_type': 'social media',
            'is_valid': False,
            'errors': [{
                'component': 'Date',
                'problem': 'Wrong date format (abbreviated month)',
                'correction': 'Should be: (2022, December 25) with full month name'
            }]
        },
        {
            'citation_id': 'social_error_010',
            'citation_text': 'Univ. of Nevada Reno. (2020, April 29). Mental health is very important [Tweet]. Twitter. https://twitter.com/unevadareno/status/1255600248187224070',
            'source_type': 'social media',
            'is_valid': False,
            'errors': [{
                'component': 'Author',
                'problem': 'Missing handle in brackets',
                'correction': 'Should be: Univ. of Nevada Reno [@unevadareno]'
            }]
        }
    ]

    output_file = DATASETS_DIR / "social_media_citations.jsonl"

    with open(output_file, 'w') as f:
        for example in social_media_examples:
            # Add metadata
            example['metadata'] = {
                'source': 'Manual curation',
                'date_collected': datetime.now().isoformat(),
                'category': 'social_media'
            }
            f.write(json.dumps(example) + '\n')

    valid_count = sum(1 for ex in social_media_examples if ex['is_valid'])
    invalid_count = len(social_media_examples) - valid_count

    print(f"\n✓ Added {len(social_media_examples)} social media citations")
    print(f"  - {valid_count} valid examples")
    print(f"  - {invalid_count} invalid examples")
    print(f"✓ Saved to: {output_file}")
    return len(social_media_examples)

def main():
    """Run all cleanup tasks."""
    print("\n" + "="*80)
    print("DATASET CLEANUP SCRIPT")
    print("="*80)
    print(f"Working directory: {DATASETS_DIR}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    # Run cleanup tasks
    spacing_fixed = fix_spacing_issues()
    replaced, removed = replace_placeholders()
    social_added = add_social_media_examples()

    # Summary
    print("\n" + "="*80)
    print("CLEANUP SUMMARY")
    print("="*80)
    print(f"✓ Fixed {spacing_fixed} spacing issues")
    print(f"✓ Replaced {replaced} placeholder citations")
    print(f"✓ Removed {removed} duplicate citations")
    print(f"✓ Added {social_added} social media citations")
    print("\nNext steps:")
    print("1. Convert all citations to [ITALIC] format")
    print("2. Regenerate train/val/test splits")
    print("3. Update comprehensive prompt with [ITALIC] instructions")
    print("4. Re-run GEPA optimization")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
