#!/bin/bash
set -euo pipefail

# Session bootstrap for auto-workflow
# Runs at the start of each session to inject initial instructions

# Logging
LOG_DIR="${CLAUDE_PROJECT_DIR}/.claude"
LOG_FILE="$LOG_DIR/workflow_orchestrator.log"
mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [BOOTSTRAP] $*" >> "$LOG_FILE"
}

log "SessionStart hook triggered"

# Read hook input
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')

log "Session ID: $SESSION_ID"
log "CWD: $CWD"

# Configuration
WORKFLOW_EPIC_FILE="${CLAUDE_PROJECT_DIR}/.claude/auto_workflow_epic.txt"

# Check if epic is set
if [[ ! -f "$WORKFLOW_EPIC_FILE" ]]; then
    log "No epic configured, skipping bootstrap"
    # No epic set - just allow session to start normally
    exit 0
fi

EPIC_ID=$(cat "$WORKFLOW_EPIC_FILE" | tr -d '[:space:]')
log "Epic ID: $EPIC_ID"

# Inject bootstrap instructions - let agent find the next task
log "Injecting bootstrap instructions for epic: $EPIC_ID"

# Output JSON with proper formatting
jq -n \
  --arg epic "$EPIC_ID" \
  '{
    "hookSpecificOutput": {
      "hookEventName": "SessionStart",
      "additionalContext": ("========================================\nAUTO-WORKFLOW SESSION STARTED\n========================================\n\nEpic: " + $epic + "\n\nCURRENT STAGE: CODING (Fresh Session)\nWORKFLOW STAGES: CODING → REQUIREMENTS_REVIEW → TESTING → ORACLE_REVIEW → COMMIT_CLOSE → NEXT_TASK\n\nStarting fresh session for next task from epic " + $epic + ".\n\n1. FIRST: Read CLAUDE.md and README.md to understand the system and workflow\n2. Use bd to find the next open issue from epic " + $epic + "\n   Command: bd dep tree " + $epic + "\n   Or: bd show " + $epic + " (shows children)\n3. If no open issues found, report '\''All tasks in epic " + $epic + " complete'\'' and STOP\n4. Start work on the next task with: /bd-start <issue-id>\n5. Follow ALL instructions in CLAUDE.md (beads-first workflow, TDD, verification, etc.)\n6. Implement the task according to project standards\n\nWhen implementation is complete, emit:\n::: WORKFLOW_STAGE: CODING_COMPLETE :::")
    }
  }'

log "Bootstrap complete"
exit 0
