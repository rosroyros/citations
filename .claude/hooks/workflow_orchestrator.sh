#!/bin/bash
set -euo pipefail

# Logging for debugging
LOG_DIR="${CLAUDE_PROJECT_DIR}/.claude"
LOG_FILE="$LOG_DIR/workflow_orchestrator.log"
mkdir -p "$LOG_DIR"
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

log "Hook triggered"

# Read hook input with timeout protection
INPUT=$(cat)
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // empty')
CWD=$(echo "$INPUT" | jq -r '.cwd // empty')

# Validate inputs
if [[ -z "$TRANSCRIPT_PATH" ]] || [[ ! -f "$TRANSCRIPT_PATH" ]]; then
    log "ERROR: Invalid transcript path: $TRANSCRIPT_PATH"
    # Allow continuation if hook fails
    jq -n '{"continue": true}'
    exit 0
fi

# Configuration
WORKFLOW_LABEL="auto-workflow"
MARKER_PATTERN="::: WORKFLOW_STAGE: ([A-Z_]+) :::"
MAX_TAIL_LINES=100

# Check if bd is available
if ! command -v bd &> /dev/null; then
    log "WARNING: bd command not found, workflow disabled"
    jq -n '{"continue": true}'
    exit 0
fi

# Check if any auto-workflow issues exist
WORKFLOW_ISSUES=$(bd list --json 2>/dev/null | jq '[.[] | select(.labels[]? == "auto-workflow")] | length' || echo "0")
if [[ "$WORKFLOW_ISSUES" -eq 0 ]]; then
    log "No auto-workflow issues found, skipping orchestration"
    jq -n '{"continue": true}'
    exit 0
fi

# Extract last agent message safely
LAST_MESSAGE=$(tail -n "$MAX_TAIL_LINES" "$TRANSCRIPT_PATH" 2>/dev/null | grep -A 50 "^assistant:" | tail -n 50 || echo "")

if [[ -z "$LAST_MESSAGE" ]]; then
    log "WARNING: Could not extract last message from transcript"
    jq -n '{"continue": true}'
    exit 0
fi

# Stage detection function
detect_stage() {
    log "Detecting stage from message"

    # 1. Check for explicit marker (most reliable)
    if echo "$LAST_MESSAGE" | grep -qE "$MARKER_PATTERN"; then
        STAGE=$(echo "$LAST_MESSAGE" | grep -oE "$MARKER_PATTERN" | tail -1 | sed -E 's/::: WORKFLOW_STAGE: ([A-Z_]+) :::/\1/')
        log "Found explicit marker: $STAGE"
        echo "$STAGE"
        return 0
    fi

    # 2. Infer from transcript patterns (order matters - most specific first)

    # Check for /clear command (SESSION_CLEARED)
    if echo "$LAST_MESSAGE" | grep -q "/clear"; then
        log "Detected /clear command"
        echo "SESSION_CLEARED"
        return 0
    fi

    # Check for bd close (ISSUE_CLOSED)
    if echo "$LAST_MESSAGE" | grep -qE "bd close|issue.*closed"; then
        log "Detected issue close"
        echo "ISSUE_CLOSED"
        return 0
    fi

    # Check for oracle review approval (ORACLE_APPROVED)
    if echo "$LAST_MESSAGE" | grep -qE "/oracle-review|/zoracle-review"; then
        if echo "$LAST_MESSAGE" | grep -qiE "approved|looks good|LGTM"; then
            log "Detected oracle approval"
            echo "ORACLE_APPROVED"
            return 0
        else
            log "Detected oracle review in progress"
            # Still in review stage, don't advance
            echo "IN_ORACLE_REVIEW"
            return 0
        fi
    fi

    # Check for test completion (TESTS_PASSING)
    if echo "$LAST_MESSAGE" | grep -qE "pytest|vitest|test:e2e|playwright"; then
        if echo "$LAST_MESSAGE" | grep -qiE "passed|success|all tests pass|\d+ passed"; then
            log "Detected passing tests"
            echo "TESTS_PASSING"
            return 0
        else
            log "Detected failing tests"
            # Tests running but not passing, stay in testing
            echo "IN_TESTING"
            return 0
        fi
    fi

    # Check for requirements review completion (REQUIREMENTS_REVIEWED)
    if echo "$LAST_MESSAGE" | grep -qiE "bd show|requirements.*satisfied|requirements.*met|verified.*requirements"; then
        log "Detected requirements review"
        echo "REQUIREMENTS_REVIEWED"
        return 0
    fi

    # Check for coding activity (CODING_COMPLETE)
    # This is tricky - only mark as complete if agent explicitly says so
    if echo "$LAST_MESSAGE" | grep -qiE "implementation.*complete|coding.*complete|finished implementing"; then
        log "Detected coding completion"
        echo "CODING_COMPLETE"
        return 0
    fi

    # 3. Check if actively working (don't interrupt)
    if echo "$LAST_MESSAGE" | grep -qE "Edit|Write|NotebookEdit|Bash.*command"; then
        log "Agent actively working, no stage transition"
        echo "IN_PROGRESS"
        return 0
    fi

    # 4. Fallback: Unknown
    log "Could not detect stage, will ask agent"
    echo "UNKNOWN"
    return 1
}

# Get next stage instructions
get_next_instruction() {
    local current_stage=$1
    log "Getting instruction for stage: $current_stage"

    case "$current_stage" in
        "IN_PROGRESS"|"IN_TESTING"|"IN_ORACLE_REVIEW")
            # Agent is actively working, don't interrupt
            log "Agent in progress, allowing continuation"
            return 1  # Signal to continue without injection
            ;;
        "CODING_COMPLETE")
            cat << 'EOF'
You've completed initial coding implementation.

CURRENT STAGE: REQUIREMENTS_REVIEW
WORKFLOW STAGES: CODING → REQUIREMENTS_REVIEW → TESTING → ORACLE_REVIEW → COMMIT_CLOSE → NEXT_TASK

Next step: Review the original issue requirements carefully.
- Re-read the issue description with `bd show <id>`
- Verify every requirement is satisfied
- Check for edge cases or missed scenarios
- Confirm implementation matches the planned approach

When you've confirmed everything is complete, emit:
::: WORKFLOW_STAGE: REQUIREMENTS_REVIEWED :::
EOF
            ;;
        "REQUIREMENTS_REVIEWED")
            cat << 'EOF'
Requirements review complete.

CURRENT STAGE: TESTING
WORKFLOW STAGES: CODING → REQUIREMENTS_REVIEW → TESTING → ORACLE_REVIEW → COMMIT_CLOSE → NEXT_TASK

Next step: Verify all tests are passing.
- Run relevant test suites (pytest for backend, vitest/playwright for frontend)
- Fix any failing tests
- Ensure new code has appropriate test coverage
- Confirm no regressions introduced

When all tests pass, emit:
::: WORKFLOW_STAGE: TESTS_PASSING :::
EOF
            ;;
        "TESTS_PASSING")
            cat << 'EOF'
All tests passing.

CURRENT STAGE: ORACLE_REVIEW
WORKFLOW STAGES: CODING → REQUIREMENTS_REVIEW → TESTING → ORACLE_REVIEW → COMMIT_CLOSE → NEXT_TASK

Next step: Request code review.
- Ensure all changes are committed
- Update issue description with implementation summary
- Add `needs-review` label: `bd label add <id> needs-review`
- Run `/oracle-review` command
- Address any feedback from review

When review is approved, emit:
::: WORKFLOW_STAGE: ORACLE_APPROVED :::
EOF
            ;;
        "ORACLE_APPROVED")
            cat << 'EOF'
Code review approved.

CURRENT STAGE: COMMIT_CLOSE
WORKFLOW STAGES: CODING → REQUIREMENTS_REVIEW → TESTING → ORACLE_REVIEW → COMMIT_CLOSE → NEXT_TASK

Next step: Finalize and close the issue.
- Ensure all changes are committed and pushed
- Deploy if required: `./deploy_prod.sh`
- Close issue with summary: `bd close <id> --reason "[Summary of what was done]"`
- Sync: `bd sync`

When issue is closed, emit:
::: WORKFLOW_STAGE: ISSUE_CLOSED :::
EOF
            ;;
        "ISSUE_CLOSED")
            cat << 'EOF'
Issue closed successfully.

CURRENT STAGE: NEXT_TASK
WORKFLOW STAGES: CODING → REQUIREMENTS_REVIEW → TESTING → ORACLE_REVIEW → COMMIT_CLOSE → NEXT_TASK

Next step: Clear session and prepare for next task.
- Run `/clear` to start fresh context
- Session will automatically continue with next available task

When session is cleared, emit:
::: WORKFLOW_STAGE: SESSION_CLEARED :::
EOF
            ;;
        "SESSION_CLEARED")
            cat << 'EOF'
Session cleared. Ready for next task.

CURRENT STAGE: CODING
WORKFLOW STAGES: CODING → REQUIREMENTS_REVIEW → TESTING → ORACLE_REVIEW → COMMIT_CLOSE → NEXT_TASK

Next step: Find and start next task with label 'auto-workflow'.
- Find next ready issue: `bd ready --json | jq '[.[] | select(.labels[]? == "auto-workflow")] | .[0]'`
- If no issues found, report "All auto-workflow tasks complete" and stop
- Otherwise: Start work with `/bd-start <id>`
- Implement the task following beads-first workflow

When implementation is complete, emit:
::: WORKFLOW_STAGE: CODING_COMPLETE :::
EOF
            ;;
        "UNKNOWN")
            cat << 'EOF'
Unable to determine current workflow stage.

WORKFLOW STAGES: CODING → REQUIREMENTS_REVIEW → TESTING → ORACLE_REVIEW → COMMIT_CLOSE → NEXT_TASK

Which stage are you at? Respond with ONE of:
- CODING_COMPLETE (finished implementing)
- REQUIREMENTS_REVIEWED (verified requirements)
- TESTS_PASSING (all tests pass)
- ORACLE_APPROVED (code review approved)
- ISSUE_CLOSED (issue closed and deployed)
- SESSION_CLEARED (ready for next task)

Then emit: ::: WORKFLOW_STAGE: <YOUR_STAGE> :::
EOF
            ;;
        *)
            log "ERROR: Unknown stage: $current_stage"
            return 1
            ;;
    esac
    return 0
}

# Main logic
STAGE=$(detect_stage)
log "Detected stage: $STAGE"

# Get instruction (may return 1 if no injection needed)
if INSTRUCTION=$(get_next_instruction "$STAGE"); then
    log "Injecting instruction for stage: $STAGE"

    # Block stop and inject system message with next stage instruction
    jq -n \
      --arg msg "$INSTRUCTION" \
      '{
        "continue": false,
        "stopReason": "Workflow stage transition",
        "systemMessage": $msg
      }'
else
    log "No instruction needed, continuing"
    # Allow normal continuation
    jq -n '{"continue": true}'
fi

exit 0
