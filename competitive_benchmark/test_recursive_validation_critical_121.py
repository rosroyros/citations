#!/usr/bin/env python3
"""
CRITICAL Recursive Validation Test - Full 121 citations
Uses senior vs junior expert framing for comprehensive self-correction test.
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

def create_batch_prompts(round1_results, batch_size=11):
    """Create batch prompts for all 121 citations."""
    total_citations = len(round1_results)
    num_batches = (total_citations + batch_size - 1) // batch_size

    print(f"📦 Creating {num_batches} batches of {batch_size} citations each")

    base_prompt = create_critical_recursive_prompt()
    batch_prompts = []

    for batch_num in range(1, num_batches + 1):
        start_idx = (batch_num - 1) * batch_size
        end_idx = min(start_idx + batch_size, total_citations)
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

        batch_prompts.append({
            'batch_num': batch_num,
            'prompt': base_prompt + citations_text,
            'start_idx': start_idx,
            'end_idx': end_idx,
            'citations': batch_results
        })

    return batch_prompts

def parse_critical_response(response_text, batch_results, batch_num):
    """Parse the critical recursive validation response for a batch."""
    # Split by citation markers
    citations = re.split(r'SENIOR EXPERT REVIEW #(\d+)', response_text)

    parsed_results = []

    for i in range(1, len(citations), 2):
        try:
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
            original_result = batch_results[citation_num - 1]

            parsed_results.append({
                'citation_num': (batch_num - 1) * 11 + citation_num,  # Global citation number
                'batch_num': batch_num,
                'batch_citation_num': citation_num,  # Number within batch
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

        except (ValueError, IndexError) as e:
            print(f"⚠️  Error parsing citation {i//2 + 1} in batch {batch_num}: {e}")
            continue

    return parsed_results

def main():
    print("🔬 CRITICAL Recursive Validation Test - Full 121 Citations")
    print("=" * 70)
    print("🎯 Testing senior vs junior expert framing on complete dataset")
    print("=" * 70)

    # Load data
    round1_results = load_round1_results()

    # Create batch prompts
    batch_prompts = create_batch_prompts(round1_results, batch_size=11)

    # Save prompts for inspection
    os.makedirs("critical_recursive_prompts", exist_ok=True)
    for batch in batch_prompts:
        prompt_file = f"critical_recursive_prompts/batch_{batch['batch_num']}_prompt.txt"
        with open(prompt_file, "w") as f:
            f.write(batch['prompt'])

    print(f"💾 Saved {len(batch_prompts)} batch prompts to critical_recursive_prompts/")

    # Process each batch
    all_results = []
    total_api_calls = 0
    total_time = 0
    failed_batches = []

    for i, batch in enumerate(batch_prompts):
        batch_num = batch['batch_num']
        print(f"\n{'='*20} BATCH {batch_num}/{len(batch_prompts)} {'='*20}")
        print(f"📝 Processing citations {batch['start_idx']+1}-{batch['end_idx']}")
        print(f"📏 Prompt length: {len(batch['prompt']):,} characters")

        # Rate limiting
        if i > 0:
            time.sleep(0.5)

        # Run API call
        start_time = time.time()
        try:
            print(f"🔄 Calling API for batch {batch_num}...")
            api_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": batch['prompt']}
                ],
                max_tokens=8000,  # Increased for larger batches
                temperature=0.0
            )

            batch_response = api_response.choices[0].message.content
            elapsed = time.time() - start_time

            total_api_calls += 1
            total_time += elapsed

            print(f"✅ Batch {batch_num} completed in {elapsed:.1f}s")
            print(f"📄 Response length: {len(batch_response):,} characters")

            # Parse response
            batch_results = parse_critical_response(batch_response, batch['citations'], batch_num)

            if len(batch_results) != len(batch['citations']):
                print(f"⚠️  WARNING: Parsed {len(batch_results)} results but expected {len(batch['citations'])}")

            # Calculate batch metrics
            junior_correct = sum(1 for r in batch_results if r['junior_correct'])
            senior_correct = sum(1 for r in batch_results if r['correct'])
            changed_mind = sum(1 for r in batch_results if r['changed_mind'])
            disagreements = sum(1 for r in batch_results if r['agree_disagree'] == 'DISAGREE')

            junior_accuracy = junior_correct / len(batch_results) if batch_results else 0
            senior_accuracy = senior_correct / len(batch_results) if batch_results else 0
            improvement = senior_accuracy - junior_accuracy

            print(f"📊 Batch {batch_num}: Junior {junior_accuracy:.1%} → Senior {senior_accuracy:.1%} ({improvement:+.1%})")
            print(f"💬 Disagreements: {disagreements}, 🔄 Changes: {changed_mind}")

            all_results.extend(batch_results)

            # Save batch results
            batch_output_file = f"critical_recursive_batch_{batch_num}_results.json"
            with open(batch_output_file, "w") as f:
                json.dump({
                    'batch_num': batch_num,
                    'citations_processed': len(batch_results),
                    'junior_accuracy': junior_accuracy,
                    'senior_accuracy': senior_accuracy,
                    'improvement': improvement,
                    'disagreements': disagreements,
                    'changed_mind': changed_mind,
                    'response_length': len(batch_response),
                    'processing_time': elapsed,
                    'results': batch_results
                }, f, indent=2)

            print(f"💾 Batch {batch_num} results saved to {batch_output_file}")

        except Exception as e:
            print(f"❌ Batch {batch_num} failed: {e}")
            failed_batches.append(batch_num)
            continue

    # Final analysis
    print(f"\n{'='*70}")
    print("🏁 FINAL RESULTS - CRITICAL RECURSIVE VALIDATION")
    print(f"{'='*70}")

    if not all_results:
        print("❌ No results to analyze!")
        return

    # Calculate overall metrics
    total_citations = len(all_results)
    junior_correct = sum(1 for r in all_results if r['junior_correct'])
    senior_correct = sum(1 for r in all_results if r['correct'])
    changed_mind = sum(1 for r in all_results if r['changed_mind'])
    disagreements = sum(1 for r in all_results if r['agree_disagree'] == 'DISAGREE')

    junior_accuracy = junior_correct / total_citations
    senior_accuracy = senior_correct / total_citations
    improvement = senior_accuracy - junior_accuracy

    print(f"📊 OVERALL PERFORMANCE:")
    print(f"   Citations processed: {total_citations}")
    print(f"   Batches completed: {len(batch_prompts) - len(failed_batches)}/{len(batch_prompts)}")
    print(f"   Failed batches: {failed_batches}")
    print(f"   API calls made: {total_api_calls}")
    print(f"   Total processing time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"")
    print(f"🎯 ACCURACY COMPARISON:")
    print(f"   Junior (Round 1): {junior_accuracy:.1%} ({junior_correct}/{total_citations})")
    print(f"   Senior (Round 2): {senior_accuracy:.1%} ({senior_correct}/{total_citations})")
    print(f"   Improvement:       {improvement:+.1%} ({senior_correct - junior_correct:+d} citations)")
    print(f"")
    print(f"💬 CRITICAL ENGAGEMENT:")
    print(f"   Disagreements:     {disagreements} ({disagreements/total_citations:.1%})")
    print(f"   Decisions changed:  {changed_mind} ({changed_mind/total_citations:.1%})")
    print(f"   Corrections:       {sum(1 for r in all_results if r['changed_mind'] and r['correct'] and not r['junior_correct'])}")
    print(f"   New errors:         {sum(1 for r in all_results if r['changed_mind'] and not r['correct'] and r['junior_correct'])}")

    # Save final results
    final_output_file = "critical_recursive_validation_final_121.json"
    with open(final_output_file, "w") as f:
        json.dump({
            'experiment_info': {
                'total_citations': total_citations,
                'total_batches': len(batch_prompts),
                'completed_batches': len(batch_prompts) - len(failed_batches),
                'failed_batches': failed_batches,
                'api_calls_made': total_api_calls,
                'total_processing_time': total_time,
                'avg_time_per_batch': total_time / len(batch_prompts) if batch_prompts else 0
            },
            'performance_metrics': {
                'junior_accuracy': junior_accuracy,
                'senior_accuracy': senior_accuracy,
                'improvement': improvement,
                'junior_correct': junior_correct,
                'senior_correct': senior_correct,
                'disagreements': disagreements,
                'changed_mind': changed_mind,
                'net_corrections': sum(1 for r in all_results if r['changed_mind'] and r['correct'] and not r['junior_correct']),
                'new_errors': sum(1 for r in all_results if r['changed_mind'] and not r['correct'] and r['junior_correct'])
            },
            'cost_estimate': {
                'input_tokens': sum(len(batch['prompt']) // 4 for batch in batch_prompts),  # Rough estimate
                'output_tokens': 0,  # Would need actual token counts
                'model': 'gpt-4o-mini'
            },
            'all_results': all_results
        }, f, indent=2)

    print(f"\n💾 Final results saved to {final_output_file}")

    # Conclusion
    if improvement > 0:
        print(f"\n🎉 SUCCESS! Critical recursive validation improved accuracy by {improvement:.1%}!")
        print("✅ Senior expert caught errors junior validator missed")
        if improvement >= 0.05:  # 5% improvement
            print("🏆 SIGNIFICANT IMPROVEMENT - Consider implementing in production!")
    elif improvement == 0:
        if changed_mind > 0:
            print(f"\n🤔 MIXED RESULTS: Same accuracy but {changed_mind} corrections made")
            print("⚖️  Some errors fixed, but new errors introduced - net neutral effect")
        else:
            print(f"\n🤔 NO CHANGE: Critical review had same accuracy")
            print("⚠️  Senior expert didn't identify any junior mistakes")
    else:
        print(f"\n📉 DECLINE: Critical review reduced accuracy by {abs(improvement):.1%}")
        print("❌ Senior expert may have been overly critical or introduced new errors")

    print(f"\n📋 Experiment completed! See {final_output_file} for detailed analysis.")

if __name__ == "__main__":
    main()