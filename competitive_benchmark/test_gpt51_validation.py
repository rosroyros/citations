#!/usr/bin/env python3
"""
Test GPT-5.1 (o1) with reasoning_effort='none' on all 121 citations in one batch
Goal: Check if strongest model gets 100% accuracy to enable automated labeling
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Load OpenAI API key
ENV_PATH = os.getenv('ENV_FILE_PATH', '../backend/.env')
load_dotenv(ENV_PATH)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def load_test_set():
    """Load the 121 corrected test citations."""
    # Try multiple possible locations
    test_files = [
        'Checker_Prompt_Optimization/test_set_121_corrected.jsonl',
        '../Checker_Prompt_Optimization/test_set_121_corrected.jsonl',
    ]

    for test_file in test_files:
        if Path(test_file).exists():
            citations = []
            with open(test_file) as f:
                for line in f:
                    if line.strip():
                        citations.append(json.loads(line))
            print(f"✅ Loaded {len(citations)} citations from {test_file}")
            return citations

    # If not found, try loading from baseline file
    baseline_file = 'GPT-4o-mini_v2_batch11_round1_detailed_121.jsonl'
    if Path(baseline_file).exists():
        citations = []
        with open(baseline_file) as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    citations.append({
                        'citation': data['citation'],
                        'ground_truth': data['ground_truth']
                    })
        print(f"✅ Loaded {len(citations)} citations from {baseline_file}")
        return citations

    print(f"❌ Could not find test set file")
    sys.exit(1)

def load_v1_prompt():
    """Load v1 validator prompt (better for o1 models)."""
    prompt_file = Path('../backend/prompts/validator_prompt.txt')

    if not prompt_file.exists():
        # Fallback to v2 if v1 not found
        prompt_file = Path('../backend/prompts/validator_prompt_v2.txt')

    if not prompt_file.exists():
        print(f"❌ Could not find prompt file")
        sys.exit(1)

    with open(prompt_file) as f:
        prompt = f.read()

    print(f"✅ Loaded prompt from {prompt_file}")
    return prompt

def create_batch_prompt(citations, base_prompt):
    """Create a single prompt with all 121 citations."""

    # Build citation list
    citation_list = []
    for i, cit in enumerate(citations, 1):
        citation_list.append(f"CITATION #{i}:\n{cit['citation']}\n")

    citations_text = "\n".join(citation_list)

    # Replace placeholder in prompt
    if '{citation}' in base_prompt:
        batch_prompt = base_prompt.replace('{citation}', citations_text)
    else:
        batch_prompt = f"{base_prompt}\n\n{citations_text}"

    return batch_prompt

def parse_decision(response_text, citation_num):
    """Parse VALID/INVALID from response for specific citation number."""
    # Look for citation section
    section_markers = [
        f"CITATION #{citation_num}",
        f"═══════════════════════════════════════════════════════════════════════════\nCITATION #{citation_num}",
    ]

    # Find the section for this citation
    section_start = -1
    for marker in section_markers:
        if marker in response_text:
            section_start = response_text.find(marker)
            break

    if section_start == -1:
        return None  # Could not find citation section

    # Find next citation or end of response
    next_citation = response_text.find(f"CITATION #{citation_num + 1}", section_start + 1)
    if next_citation == -1:
        section_text = response_text[section_start:]
    else:
        section_text = response_text[section_start:next_citation]

    # Clean text for parsing
    cleaned = section_text.replace('*', '').replace('_', '').lower()

    # Check for validation markers
    if '✓ no apa 7 formatting errors detected' in section_text.lower():
        return True  # VALID
    elif '✓ no major apa 7 errors detected' in section_text.lower():
        return True  # VALID (o1-high variation)
    elif '✓ no significant apa 7' in section_text.lower():
        return True  # VALID (o1-high variation)
    elif '❌' in section_text:
        return False  # INVALID
    elif 'no apa 7 formatting errors' in cleaned:
        return True  # VALID
    elif 'no major apa 7 errors' in cleaned:
        return True  # VALID
    elif 'no significant apa 7' in cleaned:
        return True  # VALID
    elif 'final decision: valid' in cleaned:
        return True  # VALID
    elif 'final decision: invalid' in cleaned:
        return False  # INVALID
    else:
        return None  # Could not parse

def main():
    print("🎯 GPT-5.1 VALIDATION TEST (Batch Mode)")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Load test set
    citations = load_test_set()

    # Load prompt
    base_prompt = load_v1_prompt()

    # Create batch prompt
    print(f"\n📝 Creating batch prompt with all {len(citations)} citations...")
    batch_prompt = create_batch_prompt(citations, base_prompt)

    print(f"   Prompt length: {len(batch_prompt)} characters")

    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)

    print(f"\n🚀 Sending batch to GPT-5.1 (o1 with reasoning_effort='high')...")
    print(f"   This may take several minutes (possibly 10-20 min with high reasoning)...")

    try:
        response = client.chat.completions.create(
            model='o1',
            messages=[
                {
                    'role': 'user',
                    'content': batch_prompt
                }
            ],
            reasoning_effort='high'
        )

        response_text = response.choices[0].message.content

        print(f"✅ Received response ({len(response_text)} characters)")

        # Save raw response
        output_file = 'gpt51_batch_response.txt'
        with open(output_file, 'w') as f:
            f.write(response_text)
        print(f"📁 Saved raw response to {output_file}")

        # Parse results
        print(f"\n🔍 Parsing results...")
        results = []
        unparseable = []

        for i, citation in enumerate(citations, 1):
            decision = parse_decision(response_text, i)

            if decision is None:
                unparseable.append(i)
                results.append({
                    'citation_num': i,
                    'citation': citation['citation'],
                    'ground_truth': citation['ground_truth'],
                    'predicted': None,
                    'correct': None,
                    'error': 'Could not parse'
                })
            else:
                is_correct = (decision == citation['ground_truth'])
                results.append({
                    'citation_num': i,
                    'citation': citation['citation'],
                    'ground_truth': citation['ground_truth'],
                    'predicted': decision,
                    'correct': is_correct
                })

        # Calculate accuracy
        parseable_results = [r for r in results if r['predicted'] is not None]
        if parseable_results:
            correct = sum(1 for r in parseable_results if r['correct'])
            accuracy = correct / len(parseable_results)

            print(f"\n{'='*70}")
            print(f"📊 RESULTS:")
            print(f"{'='*70}")
            print(f"Total citations: {len(citations)}")
            print(f"Successfully parsed: {len(parseable_results)}/{len(citations)}")
            if unparseable:
                print(f"⚠️  Unparseable: {len(unparseable)} citations: {unparseable}")
            print(f"Accuracy: {accuracy:.2%} ({correct}/{len(parseable_results)})")

            if accuracy == 1.0:
                print(f"\n🎉 PERFECT SCORE! GPT-5.1 got all citations correct!")
                print(f"✅ This model can be used for automated labeling of new data")
            else:
                errors = [r for r in parseable_results if not r['correct']]
                print(f"\n❌ {len(errors)} errors detected:")
                for err in errors[:5]:
                    gt = "VALID" if err['ground_truth'] else "INVALID"
                    pred = "VALID" if err['predicted'] else "INVALID"
                    print(f"   Citation #{err['citation_num']}: GT={gt}, Predicted={pred}")
                    print(f"   {err['citation'][:100]}...")

        # Save detailed results
        results_file = 'gpt51_batch_results.json'
        with open(results_file, 'w') as f:
            json.dump({
                'metadata': {
                    'model': 'o1',
                    'reasoning_effort': 'high',
                    'timestamp': datetime.now().isoformat(),
                    'total_citations': len(citations),
                    'parseable': len(parseable_results),
                    'accuracy': accuracy if parseable_results else None
                },
                'results': results
            }, f, indent=2)

        print(f"\n📁 Saved detailed results to {results_file}")

        print(f"\n✅ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"\n❌ Error during API call: {e}")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
