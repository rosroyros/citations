#!/usr/bin/env python3
"""
Compare MLA9 v1 prompt with APA v3 prompt to identify structural differences
and extra rules that may be causing false negatives.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
APA_PROMPT = PROJECT_ROOT / "backend/prompts/validator_prompt_v3_no_hallucination.txt"
MLA_PROMPT = PROJECT_ROOT / "backend/prompts/validator_prompt_mla9_v1.txt"

def extract_rules(content: str) -> list:
    """Extract bullet points and numbered rules from prompt content."""
    rules = []
    lines = content.split('\n')
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Match numbered items, bullet points, or lines starting with specific keywords
        if re.match(r'^[\d]+\.?\s+', stripped) or \
           re.match(r'^[-•]\s+', stripped) or \
           stripped.startswith('- ') or \
           stripped.startswith('CRITICAL:') or \
           stripped.startswith('IMPORTANT:') or \
           stripped.startswith('NOTE:'):
            rules.append((i+1, stripped))
    return rules

def extract_sections(content: str) -> dict:
    """Extract major sections from the prompt."""
    sections = {}
    current_section = "HEADER"
    section_content = []
    
    for line in content.split('\n'):
        # Check for section headers (━━━ or === patterns)
        if re.match(r'^[━═]+\s+\w+', line) or '━━━' in line:
            if section_content:
                sections[current_section] = '\n'.join(section_content)
            # Extract section name
            match = re.search(r'[━═]+\s+(.+?)\s+[━═]+', line)
            if match:
                current_section = match.group(1).strip()
            else:
                current_section = line.replace('━', '').strip()
            section_content = []
        else:
            section_content.append(line)
    
    if section_content:
        sections[current_section] = '\n'.join(section_content)
    
    return sections

def main():
    apa_content = APA_PROMPT.read_text()
    mla_content = MLA_PROMPT.read_text()
    
    print("=" * 70)
    print("PROMPT COMPARISON: MLA9 v1 vs APA v3 (Production)")
    print("=" * 70)
    
    # Basic stats
    print(f"\n📊 BASIC STATISTICS:")
    print(f"   APA v3: {len(apa_content)} bytes, {len(apa_content.splitlines())} lines")
    print(f"   MLA v1: {len(mla_content)} bytes, {len(mla_content.splitlines())} lines")
    print(f"   Difference: +{len(mla_content) - len(apa_content)} bytes, +{len(mla_content.splitlines()) - len(apa_content.splitlines())} lines")
    
    # Extract sections
    apa_sections = extract_sections(apa_content)
    mla_sections = extract_sections(mla_content)
    
    print(f"\n📑 SECTIONS IN APA v3:")
    for s in apa_sections:
        print(f"   - {s}")
    
    print(f"\n📑 SECTIONS IN MLA v1:")
    for s in mla_sections:
        print(f"   - {s}")
    
    # Find MLA-only sections
    print(f"\n🔴 SECTIONS IN MLA v1 NOT IN APA v3:")
    mla_only_sections = set(mla_sections.keys()) - set(apa_sections.keys())
    for s in mla_only_sections:
        print(f"   - {s}")
    
    # Count specific rule patterns
    print("\n" + "=" * 70)
    print("📋 DETAILED RULE ANALYSIS")
    print("=" * 70)
    
    # MLA-specific rules that don't appear in APA  
    mla_unique_patterns = [
        ("Full first name requirement", r"(FULL first name|full first name|Full first name)", "MLA requires full first names, APA uses initials"),
        ("'et al.' usage", r"et al\.", "Both have this, but MLA is stricter"),
        ("Title Case requirement", r"Title Case", "MLA heavily emphasizes Title Case"),
        ("'and' vs '&'", r'"and".*not.*"&"|"and" \(not "\&"\)', "MLA requires 'and', APA uses '&'"),
        ("Lowercase 'vol.' and 'no.'", r'(lowercase|"vol\.".*"no\.")', "MLA specific: lowercase vol./no."),
        ("'pp.' prefix", r'"pp\."', "MLA requires pp. prefix for pages"),
        ("Date format Day Month Year", r"Day Month Year", "MLA uses Day Month Year, APA uses Year, Month Day"),
        ("No parentheses around year", r"NOT in parentheses|not in parentheses", "MLA year without parentheses"),
        ("URL without protocol", r"without http|without https", "MLA omits http(s)://"),
        ("'edited by' format", r'"edited by"', "MLA specifies exact format"),
        ("'Directed by' format", r'"Directed by"|Directed by', "MLA film format"),
        ("Edition abbreviation", r'"ed\.".*not.*"edition"', "MLA uses 'ed.' not 'edition'"),
        ("University Press abbreviation", r'"UP".*University Press', "MLA abbreviates to UP"),
        ("Comma placement rules", r"Comma.*BETWEEN|comma.*between", "Detailed comma rules"),
        ("Period placement rules", r"Period.*AFTER|period.*after", "Detailed period rules"),
    ]
    
    print("\n🔎 MLA-SPECIFIC RULE PATTERNS:")
    mla_rule_count = 0
    for name, pattern, desc in mla_unique_patterns:
        mla_matches = len(re.findall(pattern, mla_content, re.IGNORECASE))
        apa_matches = len(re.findall(pattern, apa_content, re.IGNORECASE))
        if mla_matches > apa_matches:
            mla_rule_count += 1
            print(f"   ✓ {name}")
            print(f"     MLA: {mla_matches} occurrences, APA: {apa_matches}")
            print(f"     Impact: {desc}")
            print()
    
    print(f"\n📊 SUMMARY: MLA v1 has {mla_rule_count} rule categories not present or less emphasized in APA v3")
    
    # Analyze the "CRITICAL MLA 9 RULES" section specifically
    print("\n" + "=" * 70)
    print("🔴 'CRITICAL MLA 9 RULES' SECTION ANALYSIS")
    print("=" * 70)
    
    critical_section = ""
    in_critical = False
    for line in mla_content.split('\n'):
        if 'CRITICAL MLA 9 RULES' in line:
            in_critical = True
        elif in_critical and '━━━' in line:
            break
        elif in_critical:
            critical_section += line + '\n'
    
    print("\nThis entire section is MLA-specific and NOT in the APA prompt:")
    print("-" * 50)
    print(critical_section[:1500])
    if len(critical_section) > 1500:
        print("... [truncated]")
    
    # Extract specific bullet points from CRITICAL section
    critical_rules = []
    for line in critical_section.split('\n'):
        line = line.strip()
        if line.startswith('- ') or line.startswith('AUTHOR') or line.startswith('TITLE') or \
           line.startswith('DATE') or line.startswith('PUNCTUATION'):
            if line and not line.startswith('DATE FORMATTING'):
                critical_rules.append(line)
    
    print(f"\n📋 CRITICAL RULES COUNT: {len(critical_rules)} items in this section")
    
    # Correlation analysis with false negatives
    print("\n" + "=" * 70)
    print("🎯 CORRELATION WITH FALSE NEGATIVES")
    print("=" * 70)
    
    print("""
Based on baseline test results (28 false negatives), the problematic rules are:

1. **DOI/URL Requirements** (10+ FNs)
   - MLA prompt: "DOI or URL if available (DOI preferred)"
   - Causes: Flagging database-only citations as missing DOI
   - RECOMMENDATION: Remove DOI/URL requirement for database sources

2. **Entry Point Format for Films** (2+ FNs)  
   - MLA prompt: "Capra, Frank, director" being corrected to "Directed by"
   - Both formats are valid in MLA 9
   - RECOMMENDATION: Accept both entry point formats

3. **Missing Information Warnings** (5+ FNs)
   - MLA prompt overly eager to add [MISSING: ...] placeholders
   - Example: Webinars without URLs
   - RECOMMENDATION: Only flag truly REQUIRED missing info

4. **Punctuation Pattern Strictness** (3+ FNs)
   - Comma rules being over-applied
   - RECOMMENDATION: Review punctuation section
""")
    
    print("\n" + "=" * 70)
    print("✅ RECOMMENDATIONS FOR MLA v1.1")
    print("=" * 70)
    
    print("""
1. REMOVE or soften the entire "CRITICAL MLA 9 RULES" section
   - This 30+ line section has no equivalent in APA prompt
   - Move essential rules into the source-type sections
   
2. Simplify DOI/URL handling:
   - Change: "DOI or URL if available (DOI preferred)" 
   - To: "Include DOI or URL only if present in the original citation"

3. Accept alternative valid formats:
   - "Capra, Frank, director." AND "Directed by Frank Capra,"
   - Both are valid MLA 9

4. Remove lines about what NOT to do:
   - APA prompt doesn't have extensive "DO NOT" examples
   - This may be confusing the model

5. Match APA prompt length (~115 lines vs current ~161 lines)
   - Shorter, more focused prompts often perform better
""")

if __name__ == "__main__":
    main()
