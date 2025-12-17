# Continuous Workflow Hook - Usage Guide

## Quick Start

The workflow orchestrator hook is now configured and ready to use.

### How It Works

1. **Automatic Activation**: Hook activates when issues with `auto-workflow` label exist
2. **Stage Detection**: Monitors your responses for completion markers or infers from actions
3. **Instruction Injection**: Injects next-stage instructions after each completion
4. **Continuous Operation**: Loops through all `auto-workflow` labeled issues

### Workflow Stages

```
CODING → REQUIREMENTS_REVIEW → TESTING → ORACLE_REVIEW → COMMIT_CLOSE → NEXT_TASK
```

## Using the Hook

### Enable Workflow for an Issue

```bash
# Add label to enable automated workflow
bd label add <issue-id> auto-workflow
```

### Start Working

```bash
# Option 1: Manual start
/bd-start <issue-id>

# Option 2: Let hook find next task
# (After clearing session with auto-workflow issues pending)
```

### Stage Markers

Emit these markers when completing each stage:

```
::: WORKFLOW_STAGE: CODING_COMPLETE :::
::: WORKFLOW_STAGE: REQUIREMENTS_REVIEWED :::
::: WORKFLOW_STAGE: TESTS_PASSING :::
::: WORKFLOW_STAGE: ORACLE_APPROVED :::
::: WORKFLOW_STAGE: ISSUE_CLOSED :::
::: WORKFLOW_STAGE: SESSION_CLEARED :::
```

**Note**: Markers are optional - the hook can infer stages from your actions.

## Current Setup

- **Hook Script**: `.claude/hooks/workflow_orchestrator.sh`
- **Configuration**: `.claude/settings.json`
- **Test Issue**: `citations-5rww` (labeled with `auto-workflow`)
- **Log File**: `.claude/workflow_orchestrator.log` (created on first hook execution)

## Testing

Run the test suite:

```bash
./.claude/test_hook.sh
```

Expected output: All 4 tests passing ✓

## Monitoring

View hook activity:

```bash
# Watch in real-time
tail -f .claude/workflow_orchestrator.log

# View recent activity
tail -20 .claude/workflow_orchestrator.log
```

Log format:
```
[2025-12-17 14:50:00] Hook triggered
[2025-12-17 14:50:00] Detecting stage from message
[2025-12-17 14:50:00] Found explicit marker: CODING_COMPLETE
[2025-12-17 14:50:00] Getting instruction for stage: CODING_COMPLETE
[2025-12-17 14:50:00] Injecting instruction for stage: CODING_COMPLETE
```

## Disabling the Hook

### Temporarily (current session)

```bash
# Remove auto-workflow label from issues
bd label remove <issue-id> auto-workflow
```

### Permanently

Remove or comment out the Stop hook in `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": []
  }
}
```

## Troubleshooting

### Hook Not Triggering

1. Check if `auto-workflow` labeled issues exist:
   ```bash
   bd list --json | jq '[.[] | select(.labels[]? == "auto-workflow")]'
   ```

2. Verify hook is executable:
   ```bash
   ls -l .claude/hooks/workflow_orchestrator.sh
   # Should show: -rwxr-xr-x
   ```

3. Check hook configuration:
   ```bash
   cat .claude/settings.json
   ```

### Hook Errors

Check the log file for error messages:

```bash
grep ERROR .claude/workflow_orchestrator.log
```

Common issues:
- `bd command not found`: Install bd or ensure it's in PATH
- `Invalid transcript path`: Hook input malformed (rare, report as bug)
- `No auto-workflow issues`: No issues have the label

### Stage Detection Issues

If hook can't detect stage, it will ask you directly. Respond with:

- `CODING_COMPLETE`
- `REQUIREMENTS_REVIEWED`
- `TESTS_PASSING`
- `ORACLE_APPROVED`
- `ISSUE_CLOSED`
- `SESSION_CLEARED`

Then emit the marker: `::: WORKFLOW_STAGE: <stage> :::`

## Example Workflow

```bash
# 1. Create and label issue
bd create "Feature: Add user preferences" -p 1
bd label add citations-abcd auto-workflow

# 2. Start working (in Claude Code session)
/bd-start citations-abcd

# 3. Implement feature
# ... write code ...

# 4. Signal completion
"Implementation complete!
::: WORKFLOW_STAGE: CODING_COMPLETE :::"

# 5. Hook injects requirements review instruction
# ... verify requirements ...

# 6. Continue through stages
# Hook automatically guides through:
# - Testing
# - Oracle review
# - Commit/close
# - Next task pickup

# 7. Hook finds next auto-workflow issue and starts it
# Cycle repeats until all auto-workflow issues complete
```

## Advanced Usage

### Multiple Issues

Label multiple issues with `auto-workflow`:

```bash
bd label add citations-abc1 auto-workflow
bd label add citations-abc2 auto-workflow
bd label add citations-abc3 auto-workflow
```

Hook will process them in priority order (from `bd ready`).

### Skipping Stages

**Not recommended**, but you can force stage transitions by emitting markers even if work isn't complete. Hook trusts your markers.

### Custom Workflow Label

Edit `.claude/hooks/workflow_orchestrator.sh`:

```bash
# Change this line:
WORKFLOW_LABEL="auto-workflow"

# To your custom label:
WORKFLOW_LABEL="my-custom-workflow"
```

## Files Created

```
.claude/
├── hooks/
│   └── workflow_orchestrator.sh    # Hook script
├── settings.json                   # Hook configuration
├── workflow_orchestrator.log       # Execution log (created on first run)
├── test_hook.sh                    # Test suite
└── WORKFLOW_HOOK_USAGE.md         # This file
```

## Next Steps

1. Try running the hook with test issue `citations-5rww`
2. Monitor `.claude/workflow_orchestrator.log` to see stage detection
3. Create real issues and label them with `auto-workflow`
4. Let the hook orchestrate your workflow!

## Support

For issues or questions:
- Check the design document: `docs/plans/2025-12-17-continuous-workflow-hook-design.md`
- Review hook logs: `.claude/workflow_orchestrator.log`
- Test with: `./.claude/test_hook.sh`
