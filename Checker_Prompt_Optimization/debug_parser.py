#!/usr/bin/env python3
import re
import json

# Load the actual response
with open('Checker_Prompt_Optimization/gemini_system_instructions_121_results.json', 'r') as f:
    data = json.load(f)

response_text = data['results']['response_text']

print('DEBUGGING PARSER')
print('=' * 30)
print(f'Response length: {len(response_text)}')
print()

# Test our regex
citation_pattern = r'(?:═+\s+)?CITATION #(\d+)\s*\n\s*═+(.+?)(?=(?:═+\s+)?CITATION #\d+|$)'
matches = re.finditer(citation_pattern, response_text, re.DOTALL)
match_count = 0

for match in matches:
    match_count += 1
    citation_num = int(match.group(1))
    block_content = match.group(2)

    # Check if it's valid
    is_valid = False
    if '✓ No APA 7 formatting errors detected' in block_content or 'No APA 7 formatting errors' in block_content:
        is_valid = True

    print(f'Match {match_count}: CITATION #{citation_num}')
    print(f'  Valid: {is_valid}')
    print(f'  Content preview: {block_content[:100]}...')
    print()

print(f'Total regex matches: {match_count}')

# Check for raw CITATION # occurrences
raw_citations = response_text.count('CITATION #')
print(f'Raw "CITATION #" occurrences: {raw_citations}')

# Check for pattern differences
print()
print('PATTERN ANALYSIS:')
print('Looking for: "CITATION #11"')
if 'CITATION #11' in response_text:
    idx = response_text.find('CITATION #11')
    context = response_text[max(0, idx-50):idx+150]
    print(f'Found context: {repr(context)}')
else:
    print('Not found')

# Test with a simpler pattern
simple_pattern = r'CITATION #(\d+)'
simple_matches = re.findall(simple_pattern, response_text)
print(f'Simple pattern matches: {len(simple_matches)}')
print(f'First 10 matches: {simple_matches[:10]}')