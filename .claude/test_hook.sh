#!/bin/bash
# Test script for workflow_orchestrator.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SCRIPT="$SCRIPT_DIR/hooks/workflow_orchestrator.sh"

# Create temporary transcript files for testing
TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

echo "Testing workflow_orchestrator.sh..."
echo "===================================="

# Test 1: Explicit marker detection
echo -e "\nTest 1: Explicit marker detection (CODING_COMPLETE)"
cat > "$TMP_DIR/transcript1.txt" << 'EOF'
user: implement feature X
assistant: I've implemented the feature with the following changes:
- Added new function foo()
- Updated tests
::: WORKFLOW_STAGE: CODING_COMPLETE :::
EOF

INPUT=$(jq -n \
  --arg transcript "$TMP_DIR/transcript1.txt" \
  --arg cwd "$SCRIPT_DIR" \
  '{transcript_path: $transcript, cwd: $cwd}')

RESULT=$(echo "$INPUT" | CLAUDE_PROJECT_DIR="$SCRIPT_DIR" "$HOOK_SCRIPT")
CONTINUE=$(echo "$RESULT" | jq -r '.continue')
echo "Continue: $CONTINUE"
if [ "$CONTINUE" = "false" ] && echo "$RESULT" | jq -r '.systemMessage' | grep -q "REQUIREMENTS_REVIEW"; then
    echo "✓ Correctly detected CODING_COMPLETE and injected REQUIREMENTS_REVIEW"
else
    echo "✗ Failed to inject correct instruction"
fi

# Test 2: Transcript inference (bd close)
echo -e "\nTest 2: Transcript inference (bd close)"
cat > "$TMP_DIR/transcript2.txt" << 'EOF'
user: close the issue
assistant: I'll close the issue now.
Tool: Bash
Command: bd close citations-5rww --reason "Completed feature X"
Output: ✓ Closed issue citations-5rww
EOF

INPUT=$(jq -n \
  --arg transcript "$TMP_DIR/transcript2.txt" \
  --arg cwd "$SCRIPT_DIR" \
  '{transcript_path: $transcript, cwd: $cwd}')

RESULT=$(echo "$INPUT" | CLAUDE_PROJECT_DIR="$SCRIPT_DIR" "$HOOK_SCRIPT")
CONTINUE=$(echo "$RESULT" | jq -r '.continue')
echo "Continue: $CONTINUE"
if [ "$CONTINUE" = "false" ] && echo "$RESULT" | jq -r '.systemMessage' | grep -q "NEXT_TASK"; then
    echo "✓ Correctly inferred ISSUE_CLOSED and injected NEXT_TASK"
else
    echo "✗ Failed to infer correctly"
fi

# Test 3: In-progress detection
echo -e "\nTest 3: In-progress detection (should allow continuation)"
cat > "$TMP_DIR/transcript3.txt" << 'EOF'
user: implement feature Y
assistant: I'm implementing the feature now.
Tool: Edit
File: backend/app.py
Changes made successfully.
EOF

INPUT=$(jq -n \
  --arg transcript "$TMP_DIR/transcript3.txt" \
  --arg cwd "$SCRIPT_DIR" \
  '{transcript_path: $transcript, cwd: $cwd}')

RESULT=$(echo "$INPUT" | CLAUDE_PROJECT_DIR="$SCRIPT_DIR" "$HOOK_SCRIPT")
CONTINUE=$(echo "$RESULT" | jq -r '.continue')
echo "Continue: $CONTINUE"
if [ "$CONTINUE" = "true" ]; then
    echo "✓ Correctly detected in-progress and allowed continuation"
else
    echo "✗ Should have allowed continuation"
fi

# Test 4: Session cleared (next task)
echo -e "\nTest 4: Session cleared detection"
cat > "$TMP_DIR/transcript4.txt" << 'EOF'
user: clear the session
assistant: I'll clear the session now.
Tool: SlashCommand
Command: /clear
::: WORKFLOW_STAGE: SESSION_CLEARED :::
EOF

INPUT=$(jq -n \
  --arg transcript "$TMP_DIR/transcript4.txt" \
  --arg cwd "$SCRIPT_DIR" \
  '{transcript_path: $transcript, cwd: $cwd}')

RESULT=$(timeout 3s bash -c "echo '$INPUT' | CLAUDE_PROJECT_DIR='$SCRIPT_DIR' '$HOOK_SCRIPT'") || echo '{"continue": true}'
CONTINUE=$(echo "$RESULT" | jq -r '.continue')
echo "Continue: $CONTINUE"
if [ "$CONTINUE" = "false" ] && echo "$RESULT" | jq -r '.systemMessage' | grep -q "Find and start next task"; then
    echo "✓ Correctly detected SESSION_CLEARED and injected CODING stage"
else
    echo "✗ Failed to detect session cleared"
fi

echo -e "\n===================================="
echo "Test suite complete!"
echo "Check .claude/workflow_orchestrator.log for detailed logs"
