#!/bin/bash
set -e

# Configuration
# Usage: ./deployment/scripts/run_remote_e2e.sh <user@host>
# Example: ./deployment/scripts/run_remote_e2e.sh root@178.156.161.140

SSH_TARGET="$1"

if [ -z "$SSH_TARGET" ]; then
    echo "Error: Please provide the SSH target (user@host) as the first argument."
    echo "Example: ./deployment/scripts/run_remote_e2e.sh root@178.156.161.140"
    exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend/frontend"
TEST_ID="e2e-$(date +%s)"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "Starting Hybrid E2E Test..."
echo "Target: https://citationformatchecker.com"
echo "SSH Target: $SSH_TARGET"
echo "Test ID: $TEST_ID"

# 1. Run Frontend Test (Locally against Prod)
echo -e "\n${GREEN}[1/4] Running Frontend User Journey Test (Local -> Prod)...${NC}"
cd "$FRONTEND_DIR"
export TEST_ID="$TEST_ID"
export BASE_URL="https://citationformatchecker.com"

OUTPUT_FILE=$(mktemp)
echo "Running Playwright test... (Output captured)"
# Ensure we installed dependencies
# npm install (skip to save time, assume installed)
npm run test:e2e -- tests/e2e-full-flow.spec.cjs --project=chromium > "$OUTPUT_FILE" 2>&1
EXIT_CODE=$?

cat "$OUTPUT_FILE"

if [ $EXIT_CODE -ne 0 ]; then
    echo -e "${RED}Frontend test failed!${NC}"
    rm "$OUTPUT_FILE"
    exit 1
fi

# Extract Job ID
JOB_ID=$(grep "CAPTURED_JOB_ID:" "$OUTPUT_FILE" | cut -d':' -f2 | tr -d '\r')
rm "$OUTPUT_FILE"

if [ -z "$JOB_ID" ]; then
    echo -e "${RED}Failed to capture Job ID from frontend test!${NC}"
    exit 1
fi

echo "Captured Job ID: $JOB_ID"

# Retry loop for Log Sync and Verification
MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo -e "\n${GREEN}[Attempt $RETRY_COUNT/$MAX_RETRIES] Syncing Logs & Verifying Data...${NC}"
    
    # 2. Force Log Sync (Remote)
    # Waiting a bit for logs to flush
    if [ $RETRY_COUNT -eq 1 ]; then
        sleep 5
    else
        sleep 10
    fi
    
    echo "Executing remote log sync..."
    ssh -n "$SSH_TARGET" "cd /opt/citations && export PYTHONPATH=/opt/citations && python3 dashboard/parse_logs_cron.py"
    
    # 3. Verify Data Integrity (Remote)
    echo "Executing remote verification..."
    # Copy verification script again just in case
    scp "$PROJECT_ROOT/deployment/scripts/verify_data_integrity.py" "$SSH_TARGET:/tmp/verify_data_integrity.py"
    
    if ssh -n "$SSH_TARGET" "python3 /tmp/verify_data_integrity.py --job-id '$JOB_ID' --db-path '/opt/citations/dashboard/data/validations.db'"; then
        echo -e "\n${GREEN}✅ Data Integrity Verified!${NC}"
        break
    else
        echo -e "${RED}Verification failed.${NC}"
        if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
            echo -e "${RED}❌ Max retries reached. Test failed.${NC}"
            exit 1
        fi
        echo "Retrying..."
    fi
done

# 4. Verify Internal Dashboard UI (Local -> Internal IP)
echo -e "\n${GREEN}[4/4] Verifying Internal Dashboard UI (Local -> Internal IP)...${NC}"
cd "$FRONTEND_DIR"
npm run test:e2e -- tests/e2e-internal-dashboard.spec.cjs --project=chromium

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅ Hybrid E2E Test PASSED!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Internal Dashboard UI Verification Failed!${NC}"
    exit 1
fi
