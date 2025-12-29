#!/usr/bin/env python3
"""
Test 2: Placeholder Verification Test

Verify that the v3 prompt correctly uses [MISSING: ...] placeholders
instead of hallucinating fake DOIs, URLs, or other bibliographic data.

Test cases:
1. Citation missing a DOI → should output [MISSING: DOI - lookup required]
2. Citation missing a URL → should output [MISSING: URL]
3. Citation missing page numbers → should output [MISSING: page numbers]
"""

import os
import json
import asyncio
import re
import sys
from google import genai as new_genai
from google.genai import types
from dotenv import load_dotenv

sys.stdout.reconfigure(line_buffering=True)

# Get project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, "backend/.env"))

# Configuration
MODEL_NAME = "gemini-2.5-flash"
PROMPT_V2_PATH = os.path.join(PROJECT_ROOT, "backend/prompts/validator_prompt_v2_corrected.txt")
PROMPT_V3_PATH = os.path.join(PROJECT_ROOT, "backend/prompts/validator_prompt_v3_no_hallucination.txt")
TEMPERATURE = 0.0
THINKING_BUDGET = 1024
MAX_OUTPUT_TOKENS = 10000

# Test cases: citations with MISSING elements (not malformed, but absent)
MISSING_ELEMENT_TEST_CASES = [
    {
        "id": 1,
        "description": "Journal article missing DOI",
        "citation": "Hickey, R. (2016). An exploration into occupational therapists' use of creativity within psychiatric intensive care units. _Journal of Psychiatric Intensive Care_, _12_(2), 89–107.",
        "missing_element": "DOI",
        "should_contain_placeholder": True
    },
    {
        "id": 2,
        "description": "Journal article missing DOI (Smith example)",
        "citation": "Smith, J. A. (2020). The effects of climate change on urban planning. _Environmental Studies Quarterly_, _45_(3), 234-256.",
        "missing_element": "DOI",
        "should_contain_placeholder": True
    },
    {
        "id": 3,
        "description": "Web page missing URL",
        "citation": "World Health Organization. (2023, March 15). _Mental health in the workplace_.",
        "missing_element": "URL",
        "should_contain_placeholder": True
    },
    {
        "id": 4,
        "description": "Journal article with DOI (should NOT have placeholder)",
        "citation": "Drollinger, T., Comer, L. B., & Warrington, P. T. (2006). Development and validation of the active empathetic listening scale. _Psychology & Marketing_, _23_(2), 161-180. https://doi.org/10.1002/mar.20105",
        "missing_element": None,
        "should_contain_placeholder": False
    },
    {
        "id": 5,
        "description": "Book chapter with no DOI needed",
        "citation": "Dillard, J. P. (2020). Currents in the study of persuasion. In M. B. Oliver, A. A. Raney, & J. Bryant (Eds.), _Media effects: Advances in theory and research_ (4th ed., pp. 115–129). Routledge.",
        "missing_element": None,
        "should_contain_placeholder": False
    },
    {
        "id": 6,
        "description": "Leading numbered bullet (minor fix)",
        "citation": "1. Smith, J. (2020). Article title. _Journal Name_, _10_(2), 1-10.",
        "missing_element": "DOI",
        "should_contain_placeholder": True,
        "should_not_flag_bullet": True
    },
    {
        "id": 7,
        "description": "Leading bullet with dash",
        "citation": "- Garcia, M. (2019). Research findings. _Data Science_, _5_(1), 45-67.",
        "missing_element": "DOI", 
        "should_contain_placeholder": True,
        "should_not_flag_bullet": True
    }
]


def load_prompt(path: str) -> str:
    with open(path, 'r') as f:
        return f.read()


def extract_corrected_citation(response_text: str) -> str:
    """Extract CORRECTED CITATION: line from LLM response"""
    pattern = r'CORRECTED CITATION:\s*\n?(.*?)(?:\n─|$)'
    match = re.search(pattern, response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    pattern2 = r'CORRECTED CITATION:\s*(.+?)(?:\n\n|$)'
    match2 = re.search(pattern2, response_text, re.DOTALL)
    if match2:
        return match2.group(1).strip()
    
    return None


def check_for_hallucinated_data(corrected: str, response_text: str) -> dict:
    """Check if the response contains hallucinated DOIs/URLs"""
    issues = []
    
    # Look for DOI patterns (real DOIs start with 10.)
    doi_pattern = r'https?://doi\.org/10\.\d+/[^\s\]\)]+|doi:10\.\d+/[^\s\]\)]+'
    found_dois = re.findall(doi_pattern, corrected or "", re.IGNORECASE)
    found_dois += re.findall(doi_pattern, response_text, re.IGNORECASE)
    
    # Check if DOIs look suspicious (very short or containing "fake", "example", etc.)
    for doi in found_dois:
        if any(x in doi.lower() for x in ['example', 'fake', 'test', 'sample']):
            issues.append(f"Suspicious DOI: {doi}")
        # Flag any DOI that wasn't in the original citation
        issues.append(f"Found DOI (may be hallucinated): {doi[:50]}")
    
    return {
        "found_dois": found_dois,
        "issues": issues
    }


def check_for_placeholder(corrected: str, response_text: str) -> bool:
    """Check if [MISSING: ...] placeholder is present"""
    placeholder_pattern = r'\[MISSING:[^\]]+\]'
    return bool(re.search(placeholder_pattern, corrected or "")) or \
           bool(re.search(placeholder_pattern, response_text))


def check_bullet_flagged(response_text: str) -> bool:
    """Check if the LLM incorrectly flagged a leading bullet as an error"""
    # Look for errors about numbering or bullets
    bullet_error_patterns = [
        r'❌.*\b(number|bullet|list|1\.)\b',
        r'❌.*leading.*\d',
        r'Should be:.*remove.*1\.'
    ]
    for pattern in bullet_error_patterns:
        if re.search(pattern, response_text, re.IGNORECASE):
            return True
    return False


async def test_citation(client, prompt_template: str, test_case: dict, prompt_label: str):
    """Test a single citation for placeholder/hallucination behavior"""
    full_prompt = prompt_template + f"\n\nCITATION TO VALIDATE 1: {test_case['citation']}"
    
    config = types.GenerateContentConfig(
        temperature=TEMPERATURE,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        thinking_config=types.ThinkingConfig(thinking_budget=THINKING_BUDGET)
    )
    
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=full_prompt,
            config=config
        )
        
        corrected = extract_corrected_citation(response.text)
        has_placeholder = check_for_placeholder(corrected, response.text)
        hallucination_check = check_for_hallucinated_data(corrected, response.text)
        bullet_flagged = check_bullet_flagged(response.text)
        
        # Determine if test passed
        passed = True
        issues = []
        
        if test_case["should_contain_placeholder"]:
            if not has_placeholder:
                passed = False
                issues.append("Expected placeholder but none found")
            if hallucination_check["found_dois"]:
                passed = False
                issues.append(f"Found hallucinated DOI(s): {hallucination_check['found_dois']}")
        else:
            if has_placeholder:
                # Not necessarily a failure, but note it
                issues.append("Placeholder found (may be unnecessary)")
        
        if test_case.get("should_not_flag_bullet") and bullet_flagged:
            passed = False
            issues.append("Incorrectly flagged leading bullet as error")
        
        return {
            "test_id": test_case["id"],
            "description": test_case["description"],
            "prompt": prompt_label,
            "passed": passed,
            "issues": issues,
            "has_placeholder": has_placeholder,
            "hallucination_check": hallucination_check,
            "bullet_flagged": bullet_flagged,
            "corrected_citation": corrected,
            "raw_response": response.text[:1500] if response.text else None
        }
    except Exception as e:
        return {
            "test_id": test_case["id"],
            "description": test_case["description"],
            "prompt": prompt_label,
            "passed": False,
            "issues": [f"Error: {str(e)}"],
            "error": str(e)
        }


async def run_test_suite(client, prompt_path: str, prompt_label: str):
    """Run all test cases with a specific prompt"""
    prompt_template = load_prompt(prompt_path)
    results = []
    
    print(f"\n{'='*70}")
    print(f"Testing: {prompt_label}")
    print(f"{'='*70}")
    
    for test_case in MISSING_ELEMENT_TEST_CASES:
        result = await test_citation(client, prompt_template, test_case, prompt_label)
        results.append(result)
        
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"\n{status} Test {test_case['id']}: {test_case['description']}")
        
        if result.get("has_placeholder"):
            print(f"   📝 Placeholder: YES")
        else:
            print(f"   📝 Placeholder: NO")
        
        if result.get("hallucination_check", {}).get("found_dois"):
            print(f"   ⚠️  DOIs found: {result['hallucination_check']['found_dois']}")
        
        if result.get("issues"):
            for issue in result["issues"]:
                print(f"   ⚠️  {issue}")
        
        if result.get("corrected_citation"):
            print(f"   📋 Corrected: {result['corrected_citation'][:100]}...")
        
        await asyncio.sleep(1)  # Rate limiting
    
    return results


async def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return
    
    client = new_genai.Client(api_key=api_key)
    
    print("🧪 Placeholder Verification Test")
    print(f"🔧 Config: model={MODEL_NAME}, temp={TEMPERATURE}")
    print(f"📋 Testing {len(MISSING_ELEMENT_TEST_CASES)} cases")
    print("="*70)
    
    # Test both prompts
    v2_results = await run_test_suite(client, PROMPT_V2_PATH, "V2 (Current)")
    v3_results = await run_test_suite(client, PROMPT_V3_PATH, "V3 (No Hallucination)")
    
    # Summary
    v2_passed = sum(1 for r in v2_results if r["passed"])
    v3_passed = sum(1 for r in v3_results if r["passed"])
    total = len(MISSING_ELEMENT_TEST_CASES)
    
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"V2 (Current):         {v2_passed}/{total} passed ({v2_passed/total:.0%})")
    print(f"V3 (No Hallucination): {v3_passed}/{total} passed ({v3_passed/total:.0%})")
    
    # Test for improvement in placeholder usage
    print("\n" + "="*70)
    if v3_passed > v2_passed:
        print(f"✅ V3 shows improvement: +{v3_passed - v2_passed} tests passing")
    elif v3_passed == v2_passed:
        print("➡️ V3 same as V2")
    else:
        print(f"⚠️ V3 regression: -{v2_passed - v3_passed} tests")
    
    # Check for hallucination in v3
    v3_hallucinations = sum(1 for r in v3_results 
                           if r.get("hallucination_check", {}).get("found_dois") 
                           and any("should_contain_placeholder" in tc and tc["should_contain_placeholder"] 
                                  for tc in MISSING_ELEMENT_TEST_CASES if tc["id"] == r["test_id"]))
    
    if v3_hallucinations == 0:
        print("✅ V3 shows no hallucinated DOIs for missing-element citations")
    else:
        print(f"⚠️ V3 still hallucinating in {v3_hallucinations} cases")
    print("="*70)
    
    # Save results
    output = {
        "v2_results": v2_results,
        "v3_results": v3_results,
        "v2_passed": v2_passed,
        "v3_passed": v3_passed,
        "total": total
    }
    output_path = os.path.join(PROJECT_ROOT, "Checker_Prompt_Optimization/placeholder_verification_v3_test.json")
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\n💾 Results saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
