# Continuous Workflow Automation Hook - Design

**Date**: 2025-12-17
**Purpose**: Automate multi-stage development workflows through Claude Code hooks, enabling continuous agent operation across task lifecycle stages.

## Overview

A Stop hook that orchestrates development workflows by detecting completion markers in agent responses and injecting stage-specific instructions. The agent works naturally while the hook provides guardrails and next-step guidance, creating a continuous workflow from coding through deployment.

## Design Philosophy

- **Agent-agnostic**: Agent doesn't need special awareness beyond emitting stage markers
- **Fail-safe**: Hook failures allow normal continuation rather than breaking sessions
- **Stage-driven**: Explicit progression through quality gates (code → review → test → approval → deploy)
- **Label-scoped**: Only activates when `auto-workflow` labeled issues exist
- **Stateless**: No persistent state files; conversation transcript is the source of truth

## Workflow Stages

The hook manages 6 sequential stages:

| Stage | Purpose | Entry Marker | Exit Action |
|-------|---------|--------------|-------------|
| **CODING** | Initial implementation | Start of work | `CODING_COMPLETE` |
| **REQUIREMENTS_REVIEW** | Verify requirements satisfied | Coding complete | `REQUIREMENTS_REVIEWED` |
| **TESTING** | Ensure tests passing | Requirements verified | `TESTS_PASSING` |
| **ORACLE_REVIEW** | External code review | Tests pass | `ORACLE_APPROVED` |
| **COMMIT_CLOSE** | Finalize and close issue | Review approved | `ISSUE_CLOSED` |
| **NEXT_TASK** | Find and start next work | Issue closed | `SESSION_CLEARED` |

After `SESSION_CLEARED`, the workflow loops back to `CODING` stage with the next `auto-workflow` labeled issue.

## Stage Detection Strategy

Three-tier detection system (evaluated in order):

### 1. Explicit Markers (Primary)

Agent emits standardized tokens in responses:

```
::: WORKFLOW_STAGE: CODING_COMPLETE :::
::: WORKFLOW_STAGE: REQUIREMENTS_REVIEWED :::
::: WORKFLOW_STAGE: TESTS_PASSING :::
::: WORKFLOW_STAGE: ORACLE_APPROVED :::
::: WORKFLOW_STAGE: ISSUE_CLOSED :::
::: WORKFLOW_STAGE: SESSION_CLEARED :::
```

**Rationale**: Most reliable method when agent follows instructions.

### 2. Transcript Inference (Backup)

Hook analyzes recent tool calls and output patterns:

| Pattern | Detected Stage |
|---------|---------------|
| `bd close` or "issue closed" | `ISSUE_CLOSED` |
| `/oracle-review` + "approved"/"LGTM" | `ORACLE_APPROVED` |
| `pytest`/`vitest` + "passed"/"success" | `TESTS_PASSING` |
| `bd show` + "requirements satisfied" | `REQUIREMENTS_REVIEWED` |
| "implementation complete"/"coding complete" | `CODING_COMPLETE` |
| `/clear` command | `SESSION_CLEARED` |

**Rationale**: Provides fallback when agent forgets to emit markers.

### 3. Direct Question (Fallback)

If detection fails, hook asks agent to self-report:

```
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
```

**Rationale**: Ensures workflow never gets stuck due to ambiguous state.

## Stage-Specific Instructions

Each stage injection includes:
1. Confirmation of completed stage
2. Current stage name
3. Visual workflow progress
4. Required actions (bulleted list)
5. Marker to emit when complete

### CODING → REQUIREMENTS_REVIEW

```
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
```

### REQUIREMENTS_REVIEW → TESTING

```
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
```

### TESTING → ORACLE_REVIEW

```
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
```

### ORACLE_REVIEW → COMMIT_CLOSE

```
Code review approved.

CURRENT STAGE: COMMIT_CLOSE
WORKFLOW STAGES: CODING → REQUIREMENTS_REVIEW → TESTING → ORACLE_REVIEW → COMMIT_CLOSE → NEXT_TASK

Next step: Finalize and close the issue.
- Ensure all changes are committed and pushed
- Deploy if required: `./deploy_prod.sh`
- Close issue with summary: `bd close <id> --reason "Summary of changes"`
- Sync: `bd sync`

When issue is closed, emit:
::: WORKFLOW_STAGE: ISSUE_CLOSED :::
```

### COMMIT_CLOSE → NEXT_TASK

```
Issue closed successfully.

CURRENT STAGE: NEXT_TASK
WORKFLOW STAGES: CODING → REQUIREMENTS_REVIEW → TESTING → ORACLE_REVIEW → COMMIT_CLOSE → NEXT_TASK

Next step: Clear session and prepare for next task.
- Run `/clear` to start fresh context
- Session will automatically continue with next available task

When session is cleared, emit:
::: WORKFLOW_STAGE: SESSION_CLEARED :::
```

### NEXT_TASK → CODING (Loop)

```
Session cleared. Ready for next task.

CURRENT STAGE: CODING
WORKFLOW STAGES: CODING → REQUIREMENTS_REVIEW → TESTING → ORACLE_REVIEW → COMMIT_CLOSE → NEXT_TASK

Next step: Find and start next task with label 'auto-workflow'.
- FIRST: Read CLAUDE.md and README.md to understand the system and workflow
- Find next ready issue: `bd ready --json | jq '[.[] | select(.labels[]? == "auto-workflow")] | .[0]'`
- If no issues found, report "All auto-workflow tasks complete" and stop
- Otherwise: Start work with `/bd-start <id>`
- Follow all instructions in CLAUDE.md (beads-first workflow, TDD, verification, etc.)
- Implement the task according to project standards

When implementation is complete, emit:
::: WORKFLOW_STAGE: CODING_COMPLETE :::
```

## Implementation

### Hook Configuration

**File**: `.claude/settings.json`

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/workflow_orchestrator.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

**Rationale**:
- `Stop` event catches every agent response
- `matcher: "*"` applies to all tool uses (hook does its own filtering)
- 10-second timeout prevents hanging
- Project-relative path works across environments

### Hook Script

**File**: `.claude/hooks/workflow_orchestrator.sh`

**High-level logic**:

```bash
#!/bin/bash
set -euo pipefail

# 1. INITIALIZATION
log "Hook triggered"
INPUT=$(timeout 5s cat || echo '{}')
TRANSCRIPT_PATH=$(extract_from_input "$INPUT")

# 2. VALIDATION
if [[ ! -f "$TRANSCRIPT_PATH" ]]; then
    allow_continuation  # Fail-safe: don't break session
    exit 0
fi

if ! has_workflow_issues; then
    allow_continuation  # No auto-workflow issues, skip orchestration
    exit 0
fi

# 3. STAGE DETECTION
LAST_MESSAGE=$(extract_last_agent_message "$TRANSCRIPT_PATH")
STAGE=$(detect_stage "$LAST_MESSAGE")

# 4. INSTRUCTION INJECTION
if should_inject_instruction "$STAGE"; then
    INSTRUCTION=$(get_next_instruction "$STAGE")
    block_and_inject "$INSTRUCTION"
else
    allow_continuation  # Agent actively working, don't interrupt
fi

exit 0
```

**Key Functions**:

1. **detect_stage()**: Returns one of:
   - Stage markers: `CODING_COMPLETE`, `REQUIREMENTS_REVIEWED`, etc.
   - In-progress states: `IN_PROGRESS`, `IN_TESTING`, `IN_ORACLE_REVIEW`
   - `UNKNOWN` if detection fails

2. **get_next_instruction()**: Maps stage to instruction text
   - Returns instruction string for stage transitions
   - Returns empty (exit 1) for in-progress states

3. **Validation checks**:
   - Transcript file exists and is readable
   - `bd` command available
   - At least one `auto-workflow` labeled issue exists

4. **Logging**: All decisions written to `.claude/workflow_orchestrator.log`

### Error Handling

The hook implements multiple safety mechanisms:

| Error Condition | Handling Strategy | Rationale |
|----------------|-------------------|-----------|
| Invalid transcript path | Allow continuation | Don't break session on hook failure |
| `bd` command not found | Allow continuation | Graceful degradation in non-bd environments |
| No workflow issues | Allow continuation | Workflow only active when needed |
| Timeout on stdin read | Use empty input | Prevent hanging |
| Stage detection fails | Ask agent | Ensure workflow never stuck |
| Agent actively working | Allow continuation | Don't interrupt mid-task |

**In-Progress Detection**:

The hook recognizes intermediate states to avoid premature stage advancement:

- `IN_PROGRESS`: Agent using Edit/Write/Bash tools
- `IN_TESTING`: Tests running but not all passing yet
- `IN_ORACLE_REVIEW`: Review requested but no approval yet

These states result in `continue` decision rather than instruction injection.

## Configuration & Setup

### Initial Setup

1. **Create hook script**:
   ```bash
   mkdir -p .claude/hooks
   touch .claude/hooks/workflow_orchestrator.sh
   chmod +x .claude/hooks/workflow_orchestrator.sh
   ```

2. **Add hook configuration** to `.claude/settings.json`:
   ```json
   {
     "hooks": {
       "Stop": [
         {
           "matcher": "*",
           "hooks": [
             {
               "type": "command",
               "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/workflow_orchestrator.sh",
               "timeout": 10
             }
           ]
         }
       ]
     }
   }
   ```

3. **Label issues** for workflow:
   ```bash
   bd label add <issue-id> auto-workflow
   ```

### Workflow Activation

The workflow activates automatically when:
1. Hook is configured in settings
2. At least one issue has `auto-workflow` label
3. Agent completes a stage and hook detects transition

### Starting the Workflow

**Option A: Manual start**
```bash
# User starts session
claude

# User explicitly starts first task
/bd-start <issue-id>

# Hook takes over after first CODING_COMPLETE marker
```

**Option B: Auto-start from cleared session**
```bash
# If session is cleared and workflow issues exist:
# Hook automatically injects NEXT_TASK instruction
# Agent finds first auto-workflow issue and starts
```

### Monitoring

**Check hook execution**:
```bash
tail -f .claude/workflow_orchestrator.log
```

**Log format**:
```
[2025-12-17 10:30:15] Hook triggered
[2025-12-17 10:30:15] Detecting stage from message
[2025-12-17 10:30:15] Found explicit marker: CODING_COMPLETE
[2025-12-17 10:30:15] Getting instruction for stage: CODING_COMPLETE
[2025-12-17 10:30:15] Injecting instruction for stage: CODING_COMPLETE
```

### Disabling the Workflow

**Temporary disable** (current session):
```bash
# Remove auto-workflow label from all issues
bd label remove <issue-id> auto-workflow
```

**Permanent disable**:
Remove the `Stop` hook from `.claude/settings.json`.

## Edge Cases & Handling

### 1. Agent Forgets Marker

**Scenario**: Agent completes stage but doesn't emit marker.

**Handling**: Transcript inference detects completion pattern and advances stage.

**Example**: Agent runs `bd close` but forgets marker → Hook detects "bd close" command → Advances to `ISSUE_CLOSED`.

### 2. Tests Fail

**Scenario**: Tests run but some fail.

**Handling**: Hook detects `IN_TESTING` state (not `TESTS_PASSING`) → Allows continuation without stage advancement → Agent fixes tests → Eventually emits `TESTS_PASSING`.

### 3. Oracle Review Rejects

**Scenario**: `/oracle-review` returns feedback, not approval.

**Handling**: Hook detects `IN_ORACLE_REVIEW` state → Allows continuation → Agent addresses feedback → Runs review again → Eventually gets approval.

### 4. No More Issues

**Scenario**: Agent clears session but no `auto-workflow` issues remain.

**Handling**: Hook injects `NEXT_TASK` instruction → Agent runs `bd ready` query → Finds no issues → Agent reports "All auto-workflow tasks complete" → Hook allows continuation (no more stage transitions).

### 5. Hook Script Error

**Scenario**: Hook crashes or returns invalid JSON.

**Handling**: Claude Code's hook system allows continuation on hook errors → Session continues normally without orchestration.

### 6. Ambiguous Stage

**Scenario**: Hook cannot determine stage from transcript.

**Handling**: Hook returns `UNKNOWN` → Injects question asking agent to self-report → Agent responds with stage → Hook advances on next Stop event.

### 7. Session Interrupted

**Scenario**: User stops session mid-workflow, resumes later.

**Handling**:
- Hook analyzes transcript on first Stop after resume
- Detects most recent stage based on completed actions
- Continues from that point
- No persistent state needed - transcript is source of truth

### 8. Manual Intervention

**Scenario**: User manually runs commands outside workflow.

**Handling**: Hook only triggers on agent responses (Stop event) → Manual user commands don't trigger hook → Workflow resumes based on transcript state when agent responds.

## Benefits

1. **Quality Gates**: Enforces review and testing before deployment
2. **Consistency**: Every task follows same rigorous process
3. **Autonomous Operation**: Agent can work through multiple tasks without intervention
4. **Fail-Safe**: Hook failures don't break the session
5. **Transparent**: All stage transitions logged and visible
6. **Flexible**: Works with existing bd workflow, no schema changes
7. **Scoped**: Only affects `auto-workflow` labeled issues

## Limitations

1. **Single Epic**: Workflow processes one label at a time (can be mitigated by changing labels dynamically)
2. **Sequential Only**: No parallel task execution
3. **No Rollback**: Stage transitions are forward-only (can manually intervene)
4. **Transcript Dependency**: Very long sessions may impact inference accuracy (mitigated by markers)
5. **Command-Line Only**: Requires bash environment and bd CLI

## Future Enhancements

### Phase 2: Multi-Epic Support

Allow agent to switch between epics based on priority:

```bash
# Check all workflow labels, pick highest priority
bd ready --json | jq '[.[] | select(.labels[]? | startswith("auto-workflow:"))] | sort_by(.priority) | .[0]'
```

### Phase 3: Parallel Workflows

Support running multiple agents on different tasks:

- Each agent gets unique workflow state file
- Hook checks for conflicts before advancing stages
- Coordination via bd dependency graph

### Phase 4: Custom Stage Sequences

Define workflow stages per epic:

```json
{
  "workflows": {
    "auto-workflow:quick-fix": ["CODING", "TESTING", "COMMIT_CLOSE"],
    "auto-workflow:feature": ["CODING", "REQUIREMENTS_REVIEW", "TESTING", "ORACLE_REVIEW", "COMMIT_CLOSE"]
  }
}
```

### Phase 5: Metrics & Analytics

Track workflow metrics:

- Average time per stage
- Success rate per stage
- Bottlenecks (stages requiring multiple attempts)
- Store in SQLite for dashboard visualization

## Implementation Checklist

- [ ] Create `.claude/hooks/` directory
- [ ] Write `workflow_orchestrator.sh` script
- [ ] Add Stop hook configuration to `.claude/settings.json`
- [ ] Test stage detection logic with sample transcripts
- [ ] Test error handling (missing bd, no issues, etc.)
- [ ] Label test issues with `auto-workflow`
- [ ] Run end-to-end workflow test
- [ ] Monitor `.claude/workflow_orchestrator.log` for issues
- [ ] Document workflow in project README
- [ ] Create runbook for common issues

## Testing Strategy

### Unit Tests (Stage Detection)

Create mock transcript snippets and verify stage detection:

```bash
# Test explicit markers
echo "some text ::: WORKFLOW_STAGE: CODING_COMPLETE :::" | ./detect_stage.sh
# Expected: CODING_COMPLETE

# Test inference
echo "ran bd close with success" | ./detect_stage.sh
# Expected: ISSUE_CLOSED

# Test ambiguous
echo "working on implementation" | ./detect_stage.sh
# Expected: UNKNOWN
```

### Integration Tests (Full Workflow)

1. Create test issue with `auto-workflow` label
2. Start session, run `/bd-start <id>`
3. Complete coding, verify hook injects requirements review
4. Complete each stage, verify correct transitions
5. Verify final `/clear` and next task pickup

### Error Path Tests

1. Kill bd process mid-workflow → Verify graceful degradation
2. Remove all `auto-workflow` labels → Verify hook becomes inactive
3. Corrupt transcript file → Verify continuation allowed
4. Timeout stdin read → Verify empty input handling

## Appendix: Full Hook Script

See implementation section above for complete bash script with:
- Input validation
- Stage detection logic
- Instruction generation
- Error handling
- Logging

The script is ~300 lines and should be placed at:
`.claude/hooks/workflow_orchestrator.sh`

---

**End of Design Document**
