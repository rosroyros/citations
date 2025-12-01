#!/usr/bin/env python3
"""
Fix log parser to extract citations from "Citations to validate:" pattern
"""
import re

# Read the current log parser
with open('/opt/citations/dashboard/log_parser.py', 'r') as f:
    content = f.read()

# Add the new extraction function after the existing extract_citations_preview function
new_function = '''
def extract_citations_to_validate(log_line: str) -> Optional[tuple[str, bool]]:
    """
    Extract citation text from "Citations to validate:" log pattern.

    Args:
        log_line: The log line to extract citation text from

    Returns:
        tuple of (extracted_text, was_truncated) if found, None otherwise
    """
    # Pattern matches: Citations to validate: <text>
    pattern = r'Citations to validate: (.+?)(?:\.{3})?$'
    match = re.search(pattern, log_line)

    if match:
        raw_text = match.group(1).strip()
        # Remove trailing dots and clean up
        raw_text = raw_text.rstrip('.')
        sanitized_text, was_truncated = sanitize_text(raw_text, 5000)
        return sanitized_text, was_truncated

    return None


'''

# Find the location to insert the new function (after extract_citations_preview function)
insert_pos = content.find('def extract_full_citations(log_lines:')
if insert_pos == -1:
    print("Error: Could not find insertion point")
    exit(1)

# Insert the new function
modified_content = content[:insert_pos] + new_function + content[insert_pos:]

# Write the modified content back
with open('/opt/citations/dashboard/log_parser.py', 'w') as f:
    f.write(modified_content)

print("✅ Added extract_citations_to_validate function to log_parser.py")

# Now we need to update the cron parser to use this new function
cron_parser_content = '''
# Add citations extraction using the new "Citations to validate:" pattern
preview_result = extract_citations_preview(line)
if not preview_result:
    preview_result = extract_citations_to_validate(line)

if preview_result:
'''

# Read cron_parser.py
with open('/opt/citations/dashboard/cron_parser.py', 'r') as f:
    cron_content = f.read()

# Find and replace the existing preview extraction
old_pattern = '''preview_result = extract_citations_preview(line)
            if preview_result:'''

new_pattern = '''# Add citations extraction using the new "Citations to validate:" pattern
            preview_result = extract_citations_preview(line)
            if not preview_result:
                preview_result = extract_citations_to_validate(line)

            if preview_result:'''

if old_pattern in cron_content:
    modified_cron = cron_content.replace(old_pattern, new_pattern)

    with open('/opt/citations/dashboard/cron_parser.py', 'w') as f:
        f.write(modified_cron)

    print("✅ Updated cron_parser.py to use new citation extraction")
else:
    print("❌ Could not find the pattern to replace in cron_parser.py")
    print("Looking for pattern:", repr(old_pattern[:100]) + "...")