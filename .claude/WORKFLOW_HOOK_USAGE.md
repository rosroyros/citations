# Continuous Workflow Hook - Usage Guide

## Quick Start

The workflow orchestrator hook is configured for opt-in use via the `--settings` flag.

### How It Works

1. **Opt-in Activation**: Start Claude with `claude --settings .claude/settings.auto-workflow.json`
2. **Stage Detection**: Monitors your responses for completion markers or infers from actions
3. **Instruction Injection**: Injects next-stage instructions after each completion
4. **Continuous Operation**: Loops through all `auto-workflow` labeled issues

### Workflow Stages

```
CODING → REQUIREMENTS_REVIEW → TESTING → ORACLE_REVIEW → COMMIT_CLOSE → NEXT_TASK
```

## Using the Hook

### Start Auto-Workflow Session

```bash
# Start Claude with workflow hook enabled
claude --settings .claude/settings.auto-workflow.json

# Or create an alias for convenience
alias claude-auto="claude --settings .claude/settings.auto-workflow.json"
```

**Important**: Regular `claude` sessions will NOT have the hook active.

### Set Epic for Workflow

```bash
# In your auto-workflow session, set the epic to work on
/set-epic <epic-id>

# Example:
/set-epic citations-epic1
```

This creates `.claude/auto_workflow_epic.txt` with the epic ID. The hook will then process all open child issues of this epic in priority order.

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
- **Configuration**: `.claude/settings.auto-workflow.json` (opt-in via --settings flag)
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
[2025-12-17 15:08:51] Hook triggered
[2025-12-17 15:08:51] Transcript path: /Users/roy/.claude/projects/.../session.jsonl
[2025-12-17 15:08:51] Detecting stage from message
[2025-12-17 15:08:51] Found explicit marker: CODING_COMPLETE
[2025-12-17 15:08:51] Injecting instruction for stage: CODING_COMPLETE
```

## Disabling the Hook

### For Current Session

Just exit the session - the hook only runs in sessions started with `--settings .claude/settings.auto-workflow.json`.

### For Specific Issues

```bash
# Remove auto-workflow label
bd label remove <issue-id> auto-workflow
```

### Permanent Removal

Delete or move the settings file:

```bash
mv .claude/settings.auto-workflow.json .claude/settings.auto-workflow.json.disabled
```

## Troubleshooting

### Hook Running in Wrong Sessions

**Problem**: Hook runs in regular `claude` sessions or oracle-review sessions.

**Solution**: Make sure you're NOT loading the settings file in those sessions. Only use `claude --settings .claude/settings.auto-workflow.json` for auto-workflow sessions.

### Hook Not Triggering

1. Verify you started with the settings flag:
   ```bash
   # Check process
   ps aux | grep claude
   # Should show --settings flag in arguments
   ```

2. Check if `auto-workflow` labeled issues exist:
   ```bash
   bd list --json | jq '[.[] | select(.labels[]? == "auto-workflow")]'
   ```

3. Verify hook is executable:
   ```bash
   ls -l .claude/hooks/workflow_orchestrator.sh
   # Should show: -rwxr-xr-x
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
# 1. Create epic and child issues
bd create "Epic: User Settings Features" -t epic -p 1
# Returns: citations-epic1

bd create "Feature: Add user preferences" -p 1
bd dep add citations-abc1 citations-epic1 --type child-of

bd create "Feature: Export settings" -p 1
bd dep add citations-abc2 citations-epic1 --type child-of

# 2. Start auto-workflow session
claude --settings .claude/settings.auto-workflow.json

# 3. Set the epic to work on
/set-epic citations-epic1

# 4. Implement feature
# ... write code ...

# 5. Signal completion
"Implementation complete!
::: WORKFLOW_STAGE: CODING_COMPLETE :::"

# 6. Hook guides through stages automatically:
# - Requirements review
# - Testing
# - Oracle review
# - Commit/close
# - Session clear
# - Picks up next auto-workflow issue (citations-efgh)
# - Repeats until all complete

# 7. Hook reports when done
"All auto-workflow tasks complete"
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

### Convenience Alias

Add to your `.bashrc` or `.zshrc`:

```bash
alias claude-auto='claude --settings .claude/settings.auto-workflow.json'
```

Then simply:
```bash
claude-auto  # Starts session with workflow hook enabled
```

### Custom Workflow Label

Edit `.claude/hooks/workflow_orchestrator.sh`:

```bash
# Change this line:
WORKFLOW_LABEL="auto-workflow"

# To your custom label:
WORKFLOW_LABEL="my-custom-workflow"
```

### Running in Background

For truly autonomous operation:

```bash
# Start headless session with workflow
nohup claude --settings .claude/settings.auto-workflow.json -m "Find next auto-workflow task and complete it" > auto-workflow.log 2>&1 &

# Monitor progress
tail -f auto-workflow.log
tail -f .claude/workflow_orchestrator.log
```

## Files Created

```
.claude/
├── hooks/
│   └── workflow_orchestrator.sh       # Hook script
├── settings.auto-workflow.json        # Hook configuration (opt-in)
├── workflow_orchestrator.log          # Execution log
├── test_hook.sh                       # Test suite
└── WORKFLOW_HOOK_USAGE.md            # This file
```

## Next Steps

1. Start auto-workflow session: `claude --settings .claude/settings.auto-workflow.json`
2. Try with test issue `citations-5rww`
3. Monitor `.claude/workflow_orchestrator.log` to see stage detection
4. Create real issues and label them with `auto-workflow`
5. Let the hook orchestrate your workflow!

## Support

For issues or questions:
- Check the design document: `docs/plans/2025-12-17-continuous-workflow-hook-design.md`
- Review hook logs: `.claude/workflow_orchestrator.log`
- Test with: `./.claude/test_hook.sh`

## Important Notes

⚠️ **Session Isolation**: The hook ONLY runs in sessions started with `--settings .claude/settings.auto-workflow.json`. Regular `claude` sessions, oracle-review sessions, and other tool sessions will NOT be affected.

✅ **Best Practice**: Use `claude-auto` alias for workflow sessions, and regular `claude` for manual work and reviews.
