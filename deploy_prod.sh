#!/bin/bash
set -e

# Usage: ./deploy_prod.sh [user@host]
# Example: ./deploy_prod.sh deploy@178.156.161.140

SSH_TARGET="${1:-deploy@178.156.161.140}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Starting Production Deployment Pipeline${NC}"
echo "Target: $SSH_TARGET"

# 1. Push Code
echo -e "\n${GREEN}[1/3] Pushing changes to origin/main...${NC}"
git push origin main

# 2. Trigger Server Deployment
echo -e "\n${GREEN}[2/3] Triggering remote deployment...${NC}"
ssh "$SSH_TARGET" "cd /opt/citations && ./deployment/scripts/deploy.sh"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Server deployment failed! Aborting verification.${NC}"
    exit 1
fi

# 3. Run E2E Verification
echo -e "\n${GREEN}[3/3] Running E2E Verification...${NC}"
"$PROJECT_ROOT/deployment/scripts/run_remote_e2e.sh" "$SSH_TARGET"

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✅✅✅ DEPLOYMENT & VERIFICATION SUCCESSFUL! ✅✅✅${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Verification failed! Please check the site immediately.${NC}"
    exit 1
fi
