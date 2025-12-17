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

# Check if bd is available
if ! command -v bd &> /dev/null; then
    log "WARNING: bd command not found, skipping bootstrap"
    exit 0
fi

# Check if epic has any open child issues
# Use bd list to find children with pattern matching
NEXT_TASK=$(bd list --json 2>/dev/null | jq -r --arg epic "$EPIC_ID" '.[] | select(.id | startswith($epic + ".")) | select(.status == "open") | .id' | head -1 || echo "")

if [[ -z "$NEXT_TASK" ]]; then
    log "No open issues in epic $EPIC_ID"
    # Inject message that epic is complete
    cat << EOF
{
  "additionalContext": "========================================\nAUTO-WORKFLOW SESSION STARTED\n========================================\n\nAll tasks in epic ${EPIC_ID} are complete.\n\nNo further work to do. Session ready for manual commands."
}
EOF
    exit 0
fi

log "Next task: $NEXT_TASK"

# Inject bootstrap instructions
cat << EOF
{
  "additionalContext": "========================================\nAUTO-WORKFLOW SESSION STARTED\n========================================\n\nEpic: ${EPIC_ID}\nNext task: ${NEXT_TASK}\n\nCURRENT STAGE: CODING (Fresh Session)\nWORKFLOW STAGES: CODING → REQUIREMENTS_REVIEW → TESTING → ORACLE_REVIEW → COMMIT_CLOSE → NEXT_TASK\n\nStarting fresh session for next task.\n\n1. FIRST: Read CLAUDE.md and README.md to understand the system and workflow\n2. Start work on task ${NEXT_TASK} with: /bd-start ${NEXT_TASK}\n3. Follow ALL instructions in CLAUDE.md (beads-first workflow, TDD, verification, etc.)\n4. Implement the task according to project standards\n\nWhen implementation is complete, emit:\n::: WORKFLOW_STAGE: CODING_COMPLETE :::"
}
EOF

log "Bootstrap complete, injected instructions for task: $NEXT_TASK"
exit 0
