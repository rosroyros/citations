"""Fix parsing logic to match production"""
import json

# Update parsing function
parsing_fix = '''
# Parse response - PRODUCTION LOGIC
response_text = response.choices[0].message.content.strip()

# Check for explicit "no errors" marker (valid)
if '✓ No APA 7 formatting errors detected' in response_text:
    predicted = True
# Check for error markers (invalid)
elif '❌' in response_text:
    predicted = False
# Fallback: if contains "no errors" or similar (valid)
elif 'no errors' in response_text.lower() or 'no apa 7 formatting errors' in response_text.lower():
    predicted = True
# Otherwise assume invalid
else:
    predicted = False
'''

print(parsing_fix)
