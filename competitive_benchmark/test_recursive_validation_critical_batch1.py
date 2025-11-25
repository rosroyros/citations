#!/usr/bin/env python3
"""
Test CRITICAL recursive validation with 1 batch (11 citations) from previous experiment.
Uses senior vs junior expert framing to encourage more critical review.
"""

import json
import os
import sys
import time
import re
from pathlib import Path
from dotenv import load_dotenv

# Force unbuffered output for monitoring
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Load OpenAI API key
ENV_PATH = os.getenv('ENV_FILE_PATH', '../backend/.env')
load_dotenv(ENV_PATH)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    print("❌ No OpenAI API key found")
    sys.exit(1)

import openai
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def load_round1_results():
    """Load Round 1 results from previous experiment."""
    results_file = Path("GPT-4o-mini_v2_batch11_round1_detailed_121.jsonl")

    if not results_file.exists():
        print(f"❌ ERROR: {results_file} not found!")
        sys.exit(1)

    round1_results = []
    with open(results_file) as f:
        for line in f:
            if line.strip():
                round1_results.append(json.loads(line))

    print(f"✅ Loaded {len(round1_results)} Round 1 results")
    return round1_results

def create_critical_recursive_prompt():
    """Create the critical recursive validation prompt with senior vs junior expert framing."""

    critical_prompt = """You are an APA 7th edition citation validation EXPERT with 20+ years of experience. Your task is to conduct a CRITICAL REVIEW of citations that were previously validated by a JUNIOR VALIDATOR.

━━━ SENIOR EXPERT REVIEW INSTRUCTIONS ━━━

You are reviewing the work of a junior validator who may have missed subtle APA 7 requirements or made systematic errors.

CRITICAL REVIEW APPROACH:
- **Be highly skeptical** of the junior validator's conclusions
- **Scrutinize every detail** - they often miss edge cases and special requirements
- **Question their reasoning** - junior validators frequently overgeneralize rules
- **Look for what they missed** - not just what they identified
- **Be extra thorough** with unusual source types (standards, anthologies, online comments, etc.)

COMMON JUNIOR VALIDATOR MISTAKES TO WATCH FOR:
❌ Missing unusual author formats (organizations, abbreviations, usernames)
❌ Incorrect handling of ISO standards and technical documents
❌ Multi-volume work formatting errors
❌ Online source specific requirements (retrieval dates, usernames, etc.)
❌ Edge case punctuation and spacing rules
❌ Over-strictness on acceptable variations
❌ Missing source-type specific requirements

━━━ EXPERT VALIDATION PRINCIPLES ━━━

PRINCIPLE 1: Format Flexibility
APA 7 allows multiple valid formats. Distinguish between actual errors vs acceptable variations.

PRINCIPLE 2: Source-Type Specific Requirements
Different sources have unique requirements (ISO standards, anthologies, online comments, etc.)

PRINCIPLE 3: Strict Ordering and Punctuation
Some elements have mandatory rules that MUST be enforced.

PRINCIPLE 4: Location Specificity
Geographic locations require specific formatting standards.

━━━ CRITICAL REVIEW FORMAT ━━━

For each citation, provide:

═══════════════════════════════════════════════════════════════════════════
SENIOR EXPERT REVIEW # [number]
═══════════════════════════════════════════════════════════════════════════

ORIGINAL CITATION:
[citation text]

JUNIOR VALIDATOR'S FINDINGS:
Decision: [VALID/INVALID]
Analysis: [junior's complete reasoning]

SENIOR EXPERT ASSESSMENT:
[CRITICAL analysis of junior's work - be thorough and skeptical]

[If you AGREE with junior:]
✅ JUNIOR CORRECT: After careful review, the junior validator's assessment is accurate
Brief confirmation: [1-2 sentence summary of why they were correct]

[If you DISAGREE with junior:]
❌ JUNIOR ERROR: The junior validator missed important APA 7 requirements
Detailed correction:
❌ [Specific error the junior missed]
   APA 7 requirement: [Correct rule/application]
❌ [Another error if applicable]
   APA 7 requirement: [Correct rule/application]

EXPERT FINAL DECISION: VALID or INVALID
EXPERT REASONING: [Comprehensive explanation of your decision and why junior was right/wrong]

───────────────────────────────────────────────────────────────────────────

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CITATIONS FOR SENIOR EXPERT REVIEW:

"""

    return critical_prompt

def extract_citations_from_round1(round1_results, batch_num=1):
    """Extract first 11 citations for batch 1 test."""
    batch_size = 11
    start_idx = (batch_num - 1) * batch_size
    end_idx = start_idx + batch_size

    if end_idx > len(round1_results):
        print(f"❌ ERROR: Not enough results for batch {batch_num}")
        sys.exit(1)

    batch_results = round1_results[start_idx:end_idx]
    citations_text = ""

    for i, result in enumerate(batch_results):
        citation_num = start_idx + i + 1
        citation_text = result['citation']
        junior_decision = "VALID" if result['predicted'] else "INVALID"
        junior_analysis = result['raw_response']

        # Clean up the analysis - make it more readable
        junior_analysis = junior_analysis.replace('\u2500', '-')
        junior_analysis = junior_analysis.replace('\u2713', '✓')
        junior_analysis = junior_analysis.replace('\u274c', '❌')

        citations_text += f"""SENIOR EXPERT REVIEW #{i+1}:

ORIGINAL CITATION:
{citation_text}

JUNIOR VALIDATOR'S FINDINGS:
Decision: {junior_decision}
Analysis: {junior_analysis}

"""

    return citations_text, batch_results

def parse_critical_response(response_text, original_results):
    """Parse the critical recursive validation response."""
    # Split by citation markers
    citations = re.split(r'SENIOR EXPERT REVIEW #(\d+)', response_text)

    parsed_results = []

    for i in range(1, len(citations), 2):
        citation_num = int(citations[i])
        citation_text = citations[i+1]

        # Extract EXPERT FINAL DECISION
        decision_match = re.search(r'EXPERT FINAL DECISION:\s*(VALID|INVALID)', citation_text)
        final_decision = decision_match.group(1) if decision_match else None

        # Extract assessment (AGREE/DISAGREE)
        agree_match = re.search(r'✅ JUNIOR CORRECT:|❌ JUNIOR ERROR:', citation_text)
        agree_disagree = "AGREE" if agree_match and "JUNIOR CORRECT" in agree_match.group(0) else ("DISAGREE" if agree_match else None)

        # Map to boolean (VALID = True, INVALID = False)
        predicted = final_decision == "VALID"

        # Get original result for comparison
        original_result = original_results[citation_num - 1]

        parsed_results.append({
            'citation_num': citation_num,
            'citation': original_result['citation'],
            'ground_truth': original_result['ground_truth'],
            'junior_predicted': original_result['predicted'],
            'senior_predicted': predicted,
            'final_decision': final_decision,
            'agree_disagree': agree_disagree,
            'correct': predicted == original_result['ground_truth'],
            'junior_correct': original_result['correct'],
            'changed_mind': predicted != original_result['predicted'],
            'raw_response': f"SENIOR EXPERT REVIEW #{citation_num}{citation_text}"
        })

    return parsed_results

def main():
    print("🔬 CRITICAL Recursive Validation Test - Batch 1")
    print("=" * 60)
    print("🎯 Testing senior vs junior expert framing")
    print("=" * 60)

    # Load data
    round1_results = load_round1_results()

    # Create critical recursive prompt
    critical_prompt = create_critical_recursive_prompt()

    # Extract batch 1 citations with previous results
    citations_text, batch_results = extract_citations_from_round1(round1_results, batch_num=1)

    # Combine prompt with citations
    full_prompt = critical_prompt + citations_text

    print(f"📝 Critical prompt length: {len(full_prompt)} characters")
    print(f"📝 Testing with {len(batch_results)} citations")

    # Save prompt for inspection
    with open("test_critical_recursive_prompt_batch1.txt", "w") as f:
        f.write(full_prompt)
    print("💾 Saved critical prompt to test_critical_recursive_prompt_batch1.txt")

    # Run critical recursive validation
    print("\n🔍 Running CRITICAL recursive validation...")
    start_time = time.time()

    try:
        api_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=4000,
            temperature=0.0
        )

        critical_response = api_response.choices[0].message.content
        elapsed = time.time() - start_time

        print(f"✅ API call completed in {elapsed:.1f} seconds")
        print(f"📄 Response length: {len(critical_response)} characters")

    except Exception as e:
        print(f"❌ API call failed: {e}")
        return

    # Parse response
    print("\n🔍 Parsing critical recursive validation response...")
    parsed_results = parse_critical_response(critical_response, batch_results)

    if len(parsed_results) != len(batch_results):
        print(f"⚠️  WARNING: Parsed {len(parsed_results)} results but expected {len(batch_results)}")

    # Calculate metrics
    junior_correct = sum(1 for r in parsed_results if r['junior_correct'])
    senior_correct = sum(1 for r in parsed_results if r['correct'])
    changed_mind_count = sum(1 for r in parsed_results if r['changed_mind'])
    disagreements = sum(1 for r in parsed_results if r['agree_disagree'] == 'DISAGREE')

    junior_accuracy = junior_correct / len(parsed_results)
    senior_accuracy = senior_correct / len(parsed_results)

    print(f"\n📊 CRITICAL REVIEW RESULTS")
    print("=" * 40)
    print(f"Junior (Round 1) Accuracy: {junior_accuracy:.1%} ({junior_correct}/{len(parsed_results)})")
    print(f"Senior (Round 2) Accuracy: {senior_accuracy:.1%} ({senior_correct}/{len(parsed_results)})")
    print(f"Improvement: {senior_accuracy - junior_accuracy:+.1%}")
    print(f"Senior disagreed with junior: {disagreements} citations")
    print(f"Senior changed decisions: {changed_mind_count} citations")

    # Show details
    print(f"\n📋 DETAILED COMPARISON")
    print("=" * 40)
    for result in parsed_results:
        junior_status = "✓" if result['junior_correct'] else "❌"
        senior_status = "✓" if result['correct'] else "❌"
        changed = "🔄" if result['changed_mind'] else " "
        disagreement = "💬" if result['agree_disagree'] == 'DISAGREE' else "  "
        print(f"{changed}{disagreement}{junior_status}→{senior_status} #{result['citation_num']}: Jr={result['junior_predicted']}, Sr={result['senior_predicted']}, Truth={result['ground_truth']}")

    # Save results
    output_file = "critical_recursive_validation_test_batch1.json"
    with open(output_file, "w") as f:
        json.dump({
            'test_info': {
                'batch_num': 1,
                'citations_tested': len(parsed_results),
                'junior_accuracy': junior_accuracy,
                'senior_accuracy': senior_accuracy,
                'improvement': senior_accuracy - junior_accuracy,
                'changed_mind_count': changed_mind_count,
                'disagreements': disagreements
            },
            'prompt_file': 'test_critical_recursive_prompt_batch1.txt',
            'results': parsed_results
        }, f, indent=2)

    print(f"\n💾 Results saved to {output_file}")

    # Analysis
    if senior_accuracy > junior_accuracy:
        print(f"\n🎉 SUCCESS: Critical review improved accuracy by {senior_accuracy - junior_accuracy:.1%}!")
        print("🔍 Senior expert caught errors junior validator missed")
        print("✅ Ready to run full 121-citation CRITICAL experiment")
    elif senior_accuracy == junior_accuracy:
        if changed_mind_count > 0:
            print(f"\n🤔 INTERESTING: Same accuracy but {changed_mind_count} corrections made")
            print("🔍 Some errors fixed, but new errors introduced")
            print("⚠️  Consider if net effect is beneficial")
        else:
            print(f"\n🤔 NO CHANGE: Critical review had same accuracy, no corrections")
            print("⚠️  Senior expert didn't identify any junior mistakes")
    else:
        print(f"\n📉 DECLINE: Critical review reduced accuracy by {junior_accuracy - senior_accuracy:.1%}")
        print("❌ Senior expert may have been overly critical or made new errors")

if __name__ == "__main__":
    main()