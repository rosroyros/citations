#!/bin/bash
set -euo pipefail

# UserPromptSubmit hook to inject bootstrap as first user message
# This makes it visible in the conversation

# Logging
LOG_DIR="${CLAUDE_PROJECT_DIR}/.claude"
LOG_FILE="$LOG_DIR/workflow_orchestrator.log"
mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [USER_BOOTSTRAP] $*" >> "$LOG_FILE"
}

# Read hook input
INPUT=$(cat)
USER_PROMPT=$(echo "$INPUT" | jq -r '.user_prompt // empty')

log "UserPromptSubmit triggered"
log "User prompt: ${USER_PROMPT:0:50}..."

# Only bootstrap on FIRST user prompt of session (empty or very short)
if [[ ${#USER_PROMPT} -gt 20 ]]; then
    log "Not first prompt, skipping bootstrap"
    exit 0
fi

# Configuration
WORKFLOW_EPIC_FILE="${CLAUDE_PROJECT_DIR}/.claude/auto_workflow_epic.txt"

# Check if epic is set
if [[ ! -f "$WORKFLOW_EPIC_FILE" ]]; then
    log "No epic configured, skipping bootstrap"
    exit 0
fi

EPIC_ID=$(cat "$WORKFLOW_EPIC_FILE" | tr -d '[:space:]')
log "Epic ID: $EPIC_ID"
log "Injecting bootstrap context"

# Inject bootstrap as additional context (prepended to user prompt)
jq -n \
  --arg epic "$EPIC_ID" \
  '{
    "hookSpecificOutput": {
      "hookEventName": "UserPromptSubmit",
      "additionalContext": ("========================================\nAUTO-WORKFLOW SESSION\n========================================\n\nEpic: " + $epic + "\n\nCURRENT STAGE: CODING (Fresh Session)\nWORKFLOW STAGES: CODING → REQUIREMENTS_REVIEW → TESTING → ORACLE_REVIEW → COMMIT_CLOSE → NEXT_TASK\n\nInstructions:\n1. FIRST: Read CLAUDE.md and README.md to understand the system and workflow\n2. Use bd to find the next open issue from epic " + $epic + "\n   Command: bd show " + $epic + " (shows children)\n3. If no open issues, report 'All tasks in epic " + $epic + " complete' and STOP\n4. Start work on next task with: /bd-start <issue-id>\n5. Follow ALL instructions in CLAUDE.md (beads-first workflow, TDD, verification, etc.)\n\nWhen implementation complete, emit: ::: WORKFLOW_STAGE: CODING_COMPLETE :::\n\n========================================\n")
    }
  }'

log "Bootstrap context injected"
exit 0
