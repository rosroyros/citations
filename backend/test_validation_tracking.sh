#!/bin/bash

# Test validation endpoint with tracking

echo "Testing validation tracking..."
echo "=============================="

# Base URL
BASE_URL="http://localhost:5000"

echo ""
echo "1. Testing with user who has 0 credits (sync endpoint)..."
echo "--------------------------------------------------------"
curl -X POST ${BASE_URL}/api/validate \
  -H "Content-Type: application/json" \
  -H "X-Experiment-Variant: 1" \
  -d '{
    "citations": "Smith, J. (2023). Test citation.\n\nDoe, J. (2023). Another test."
  }' 2>/dev/null | jq . || echo "Request sent"

echo ""
echo "2. Testing free tier limit reached (sync endpoint)..."
echo "----------------------------------------------------"
FREE_USED_BASE64=$(echo -n "10" | base64)
curl -X POST ${BASE_URL}/api/validate \
  -H "Content-Type: application/json" \
  -H "X-Free-Used: ${FREE_USED_BASE64}" \
  -H "X-Experiment-Variant: 2" \
  -d '{
    "citations": "Smith, J. (2023). Test citation."
  }' 2>/dev/null | jq . || echo "Request sent"

echo ""
echo "3. Testing insufficient credits (partial results)..."
echo "-----------------------------------------------------"
curl -X POST ${BASE_URL}/api/validate \
  -H "Content-Type: application/json" \
  -H "X-User-Token: test_token_partial" \
  -H "X-Experiment-Variant: 2" \
  -d '{
    "citations": "Smith, J. (2023). Test citation.\n\nDoe, J. (2023). Another test.\n\nJohnson, K. (2023). Third test.\n\nBrown, L. (2023). Fourth test.\n\nDavis, M. (2023). Fifth test."
  }' 2>/dev/null | jq . || echo "Request sent"

echo ""
echo "4. Testing async endpoint with 0 credits..."
echo "--------------------------------------------"
curl -X POST ${BASE_URL}/api/validate/async \
  -H "Content-Type: application/json" \
  -H "X-User-Token: test_token_zero_credits" \
  -H "X-Experiment-Variant: 1" \
  -d '{
    "citations": "Smith, J. (2023). Test citation."
  }' 2>/dev/null | jq . || echo "Request sent"

echo ""
echo "5. Checking app.log for UPGRADE_EVENT entries..."
echo "==============================================="
tail -20 app.log | grep "UPGRADE_EVENT" | tail -10

echo ""
echo "6. Most recent UPGRADE_EVENT details:"
echo "------------------------------------"
tail -50 app.log | grep "UPGRADE_EVENT.*pricing_table_shown" | tail -1 | python3 -c "
import sys, json
import re

line = sys.stdin.read().strip()
if 'UPGRADE_EVENT:' in line:
    try:
        # Extract JSON from the line
        json_str = re.search(r'UPGRADE_EVENT: (.*)', line).group(1)
        data = json.loads(json_str)
        print(f'Event: {data.get(\"event\")}')
        print(f'Token: {data.get(\"token\")}')
        print(f'Experiment Variant: {data.get(\"experiment_variant\")}')
        print(f'Reason: {data.get(\"metadata\", {}).get(\"reason\")}')
        if 'credits_remaining' in data.get('metadata', {}):
            print(f'Credits Remaining: {data[\"metadata\"][\"credits_remaining\"]}')
        if 'free_used' in data.get('metadata', {}):
            print(f'Free Used: {data[\"metadata\"][\"free_used\"]}')
    except:
        print('Could not parse event')
else:
    print('No UPGRADE_EVENT found')
"

echo ""
echo "Done. Check output above for tracking events."