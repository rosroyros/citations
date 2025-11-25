#!/usr/bin/env python3
"""
Test recursive validation with 1 batch (11 citations) from previous experiment.
This will validate if the recursive approach works before running full 121 citations.
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

def load_v2_prompt():
    """Load the original v2 prompt."""
    prompt_file = Path("backend/prompts/validator_prompt_v2.txt")

    if not prompt_file.exists():
        print(f"❌ ERROR: {prompt_file} not found!")
        sys.exit(1)

    with open(prompt_file) as f:
        v2_prompt = f.read()

    print(f"✅ Loaded v2 prompt ({len(v2_prompt)} chars)")
    return v2_prompt

def create_recursive_prompt():
    """Create the recursive validation prompt."""

    recursive_prompt = """You are an APA 7th edition citation validator. Your task is to validate whether a given citation adheres to the APA 7th edition format rules.

━━━ INSTRUCTIONS ━━━

1. Analyze the components of the given citation to determine if they follow APA 7th edition guidelines. Different types of sources may have different formatting requirements.

2. For a web page citation, ensure it includes:
   - The author, which can be an organization like Wikipedia if no specific author is listed.
   - The date of publication in the order: year, month day.
   - The title of the page in italics.
   - The website name and then the URL.

3. For a book citation, verify:
   - The authors' last names followed by their initials.
   - The publication year in parentheses.
   - The title of the work in italics.
   - The publisher's name included at the end.

4. For an unpublished doctoral dissertation, ensure:
   - The author's last name and initials are provided.
   - The year of publication is in parentheses.
   - The title of the dissertation is in italics.
   - It is specified as an unpublished doctoral dissertation.
   - The institution's name is included where the dissertation was completed.

5. For a journal article, verify:
   - The authors' last names followed by their initials.
   - The publication year in parentheses.
   - The article title (not italicized).
   - The journal name in italics.
   - Volume number (italicized) and issue number (in parentheses, not italicized).
   - Page numbers and DOI or URL.

━━━ APA 7 PRINCIPLES ━━━

PRINCIPLE 1: Format Flexibility

APA 7 allows multiple valid formats for many elements. Do not flag a citation as
invalid solely because it uses an acceptable alternative format.

**DOIs:**
- Both formats are acceptable:
  • doi:10.xxxx/suffix
  • https://doi.org/10.xxxx/suffix
- Suffixes vary and all are valid:
  • Numeric: 10.1234/5678
  • Alphanumeric: 10.1234/abcd.5678
  • Complex: 10.1371/journal.pone.0193972

**Dates:**
- Classical/ancient works: Date ranges are acceptable (e.g., "385-378 BCE")
- Classical/ancient works: Original publication date is optional
- Modern works: Standard (YYYY) format required

**International Elements:**
- Non-English publisher names are valid
- International domains are acceptable (.uk, .dk, .de, .au, etc.)
- Journal name abbreviations in any language (e.g., USA, UK) should be
  italicized with the journal name

**Bracketed Descriptions:**
- Can contain longer contextual information when needed for clarity
- Length is not a criterion for validity
- Examples: [Comment on the blog post "..."], [Fact sheet], [Conference presentation]

**Article Numbers:**
- "Article XXXXXX" format is the CORRECT and PREFERRED format when journals
  use article numbers instead of page ranges
- Examples: Article e0193972, Article 123456
- Do NOT flag this as an error

PRINCIPLE 2: Source-Type Specific Requirements

Different source types have special formatting requirements that are correct for that type.

**Retrieval Dates:**
- REQUIRED for frequently updated sources:
  • Medical databases (UpToDate, Cochrane)
  • Wikis and reference works
  • Social media content
- Format: "Retrieved Month DD, YYYY, from URL"
- Do not flag these as errors when appropriate for the source type

**Government Publications:**
- Multi-level agency hierarchies are correct
- List from specific to general: Institute > Department > Agency
- Publication numbers in format "(Agency Publication No. XX-XXXX)" are standard
- (n.d.) is acceptable when no publication date is given
- Example: National Institute on Drug Abuse > U.S. Department of Health and Human Services

**Book Series:**
- Numbered series include series title and volume before book title
- Format: "Series title: Vol. XXX. Book title"
- Example: "Lecture notes in computer science: Vol. 9562."

**Edition Information:**
- Standard abbreviations are acceptable:
  • ed. (edition)
  • Rev. ed. (revised edition)
  • text rev. (text revision)
  • Abr. ed. (abridged edition)

PRINCIPLE 3: Strict Ordering and Punctuation

Certain elements have mandatory ordering and punctuation rules that MUST be enforced.

**Dissertation Publication Numbers:**
- MUST appear AFTER the bracketed description, not before
- WRONG: (Publication No. X) [Doctoral dissertation, University]
- CORRECT: [Doctoral dissertation, University]. (Publication No. X)

**URLs:**
- NO punctuation immediately before a URL
- The character before "http" must be a space, not a period or comma
- WRONG: Source name. https://...
- CORRECT: Source name https://...

**Journal Formatting:**
- Volume number must be visually separate from journal name
- Journal name: italicized
- Volume: italicized
- Issue: in parentheses, not italicized
- Volume should NOT appear within the same italic span as journal name followed
  by just a comma

PRINCIPLE 4: Location Specificity

Geographic locations require specific formatting standards.

**Conference Locations:**
- State names MUST be spelled out in full, not abbreviated
- Format: City, State (full name), Country
- WRONG: Chicago, IL, United States
- CORRECT: Chicago, Illinois, United States

━━━ FORMATTING NOTES ━━━

IMPORTANT: In the input citations, italic formatting is indicated using markdown underscores.
Example: _Journal of Studies_ means the text should be italicized.

━━━ RECURSIVE VALIDATION INSTRUCTIONS ━━━

You are conducting a second-pass validation of citations that were previously validated by another model. For each citation, you will be provided with:
1. The original citation
2. The previous validation result (VALID/INVALID)
3. The previous model's complete analysis

Your task is to review the previous validation and either AGREE or DISAGREE with their assessment.

━━━ OUTPUT FORMAT ━━━

For each citation, provide:

═══════════════════════════════════════════════════════════════════════════
REVIEW OF CITATION #[number]
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
[citation text]

PREVIOUS VALIDATION:
Decision: [VALID/INVALID]
Analysis: [previous model's complete reasoning]

YOUR REVIEW:
[AGREE/DISAGREE] with previous validation

[If AGREE:]
✓ I agree with the previous validation

[If DISAGREE:]
❌ [Component]: [What's wrong with previous analysis]
   Should be: [Correct assessment]

FINAL_DECISION: VALID or INVALID
REASONING: [Why you agree/disagree with previous validation]

───────────────────────────────────────────────────────────────────────────

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CITATIONS TO REVIEW:

"""

    return recursive_prompt

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
        round1_decision = "VALID" if result['predicted'] else "INVALID"
        round1_analysis = result['raw_response']

        # Clean up the analysis - make it more readable
        round1_analysis = round1_analysis.replace('\u2500', '-')
        round1_analysis = round1_analysis.replace('\u2713', '✓')
        round1_analysis = round1_analysis.replace('\u274c', '❌')

        citations_text += f"""CITATION #{i+1}:
ORIGINAL: {citation_text}
PREVIOUS VALIDATION:
Decision: {round1_decision}
Analysis: {round1_analysis}

"""

    return citations_text, batch_results

def parse_recursive_response(response_text, original_results):
    """Parse the recursive validation response."""
    # Split by citation markers
    citations = re.split(r'REVIEW OF CITATION #(\d+)', response_text)

    parsed_results = []

    for i in range(1, len(citations), 2):
        citation_num = int(citations[i])
        citation_text = citations[i+1]

        # Extract FINAL_DECISION
        decision_match = re.search(r'FINAL_DECISION:\s*(VALID|INVALID)', citation_text)
        final_decision = decision_match.group(1) if decision_match else None

        # Extract AGREE/DISAGREE
        agree_match = re.search(r'YOUR REVIEW:\s*\n(AGREE|DISAGREE)', citation_text)
        agree_disagree = agree_match.group(1) if agree_match else None

        # Map to boolean (VALID = True, INVALID = False)
        predicted = final_decision == "VALID"

        # Get original result for comparison
        original_result = original_results[citation_num - 1]

        parsed_results.append({
            'citation_num': citation_num,
            'citation': original_result['citation'],
            'ground_truth': original_result['ground_truth'],
            'round1_predicted': original_result['predicted'],
            'round2_predicted': predicted,
            'final_decision': final_decision,
            'agree_disagree': agree_disagree,
            'correct': predicted == original_result['ground_truth'],
            'round1_correct': original_result['correct'],
            'changed_mind': predicted != original_result['predicted'],
            'raw_response': f"REVIEW OF CITATION #{citation_num}{citation_text}"
        })

    return parsed_results

def main():
    print("🧪 Recursive Validation Test - Batch 1")
    print("=" * 50)

    # Load data
    round1_results = load_round1_results()

    # Create recursive prompt
    recursive_prompt = create_recursive_prompt()

    # Extract batch 1 citations with previous results
    citations_text, batch_results = extract_citations_from_round1(round1_results, batch_num=1)

    # Combine prompt with citations
    full_prompt = recursive_prompt + citations_text

    print(f"📝 Full prompt length: {len(full_prompt)} characters")
    print(f"📝 Testing with {len(batch_results)} citations")

    # Save prompt for inspection
    with open("test_recursive_prompt_batch1.txt", "w") as f:
        f.write(full_prompt)
    print("💾 Saved test prompt to test_recursive_prompt_batch1.txt")

    # Auto-run the test (no interactive input needed)
    print("\n🚀 Running recursive validation test automatically...")

    # Run recursive validation
    print("\n🔄 Running recursive validation...")
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

        recursive_response = api_response.choices[0].message.content
        elapsed = time.time() - start_time

        print(f"✅ API call completed in {elapsed:.1f} seconds")
        print(f"📄 Response length: {len(recursive_response)} characters")

    except Exception as e:
        print(f"❌ API call failed: {e}")
        return

    # Parse response
    print("\n🔍 Parsing recursive validation response...")
    parsed_results = parse_recursive_response(recursive_response, batch_results)

    if len(parsed_results) != len(batch_results):
        print(f"⚠️  WARNING: Parsed {len(parsed_results)} results but expected {len(batch_results)}")

    # Calculate metrics
    round1_correct = sum(1 for r in parsed_results if r['round1_correct'])
    round2_correct = sum(1 for r in parsed_results if r['correct'])
    changed_mind_count = sum(1 for r in parsed_results if r['changed_mind'])

    round1_accuracy = round1_correct / len(parsed_results)
    round2_accuracy = round2_correct / len(parsed_results)

    print(f"\n📊 RESULTS SUMMARY")
    print("=" * 30)
    print(f"Round 1 Accuracy: {round1_accuracy:.1%} ({round1_correct}/{len(parsed_results)})")
    print(f"Round 2 Accuracy: {round2_accuracy:.1%} ({round2_correct}/{len(parsed_results)})")
    print(f"Improvement: {round2_accuracy - round1_accuracy:+.1%}")
    print(f"Changed mind: {changed_mind_count} citations")

    # Show details
    print(f"\n📋 DETAILED RESULTS")
    print("=" * 30)
    for result in parsed_results:
        status = "✓" if result['correct'] else "❌"
        changed = "🔄" if result['changed_mind'] else " "
        print(f"{changed}{status} #{result['citation_num']}: R1={result['round1_predicted']}, R2={result['round2_predicted']}, Truth={result['ground_truth']}")

    # Save results
    output_file = "recursive_validation_test_batch1.json"
    with open(output_file, "w") as f:
        json.dump({
            'test_info': {
                'batch_num': 1,
                'citations_tested': len(parsed_results),
                'round1_accuracy': round1_accuracy,
                'round2_accuracy': round2_accuracy,
                'improvement': round2_accuracy - round1_accuracy,
                'changed_mind_count': changed_mind_count
            },
            'prompt_file': 'test_recursive_prompt_batch1.txt',
            'results': parsed_results
        }, f, indent=2)

    print(f"\n💾 Results saved to {output_file}")

    # Analysis
    if round2_accuracy > round1_accuracy:
        print(f"🎉 SUCCESS: Recursive validation improved accuracy by {round2_accuracy - round1_accuracy:.1%}!")
        print("✅ Ready to run full 121-citation experiment")
    elif round2_accuracy == round1_accuracy:
        print("🤔 NO CHANGE: Recursive validation had same accuracy")
        print("⚠️  Consider if improvement is worth the 2x cost")
    else:
        print(f"📉 DECLINE: Recursive validation reduced accuracy by {round1_accuracy - round2_accuracy:.1%}")
        print("❌ Recursive approach may not be beneficial")

if __name__ == "__main__":
    main()