# Auto-Workflow Setup Guide

Complete guide for setting up continuous autonomous agent workflow.

## Overview

The auto-workflow system consists of:
1. **Agent pane**: Runs Claude Code with workflow hook
2. **Monitor pane**: Watches for session clear requests and executes them
3. **Hook orchestrator**: Guides agent through workflow stages

## Setup Steps

### 1. Start tmux session

```bash
tmux new-session -s auto-workflow
```

### 2. Split into two panes

```bash
# Split horizontally (monitor on bottom)
tmux split-window -v

# Or split vertically (monitor on right)
tmux split-window -h
```

### 3. Start agent in pane 0

```bash
# Switch to pane 0
tmux select-pane -t 0

# Start Claude with auto-workflow settings
claude --settings .claude/settings.auto-workflow.json
```

### 4. Start monitor in pane 1

```bash
# Switch to pane 1
tmux select-pane -t 1

# Start monitoring pane 0
./.claude/monitor_and_clear.sh 0
```

### 5. Configure epic in agent pane

```bash
# In pane 0 (agent), set the epic to work on
/set-epic citations-your-epic-id
```

### 6. Start first task

```bash
# Agent will show available tasks, start with:
/bd-start <first-task-id>
```

## How It Works

### Workflow Loop

1. **Session starts** → SessionStart hook finds next task and injects instructions
2. **Agent implements task** → Guided through stages by Stop hook
3. **Agent completes task** → Emits `::: WORKFLOW_STAGE: ISSUE_CLOSED :::`
4. **Agent emits clear marker** → `::: END_SESSION_CLEAR_REQUESTED :::`
5. **Monitor detects marker** → Sends `/clear` to agent pane
6. **Session clears and restarts** → Back to step 1
7. **Repeat** until epic complete

### Pane Layout

```
┌─────────────────────────────────┐
│                                 │
│  Pane 0: Agent                  │
│  claude --settings ...          │
│                                 │
├─────────────────────────────────┤
│                                 │
│  Pane 1: Monitor                │
│  ./monitor_and_clear.sh 0       │
│                                 │
└─────────────────────────────────┘
```

## Finding Pane Numbers

```bash
# List all panes with numbers
tmux list-panes

# Output example:
# 0: [170x42] [history 1000/1000, 50000 bytes] %0
# 1: [170x20] [history 500/1000, 25000 bytes] %1
```

## Monitoring

### Agent Pane (Pane 0)
Watch the agent work through tasks automatically.

### Monitor Pane (Pane 1)
You'll see:
```
Monitoring pane 0 for session clear marker...
Marker: ::: END_SESSION_CLEAR_REQUESTED :::
Press Ctrl+C to stop monitoring

[2025-12-17 15:30:45] Detected END_SESSION_CLEAR_REQUESTED marker!
Sending /clear command to pane 0...
Clear command sent successfully
Waiting 5 seconds before resuming monitoring...
```

### Hook Logs
```bash
# In another terminal/pane
tail -f .claude/workflow_orchestrator.log
```

## Troubleshooting

### Monitor not detecting marker

Check pane number:
```bash
tmux list-panes
# If agent is in pane 1, run: ./monitor_and_clear.sh 1
```

### Clear not working

Monitor script sends:
```bash
tmux send-keys -t <pane> "/clear" C-m
```

If this doesn't work, check:
1. Agent pane is responsive
2. No other process intercepting input
3. Pane number is correct

### Agent not continuing after clear

Check hook is active:
```bash
# Should show recent entries
tail .claude/workflow_orchestrator.log
```

Verify epic is set:
```bash
cat .claude/auto_workflow_epic.txt
```

### Monitor false triggers

The script tracks content to avoid duplicate clears. Only triggers when NEW content contains the marker.

## Stopping the Workflow

### Graceful Stop

In agent pane (pane 0):
- Let current task complete
- When it emits clear marker, monitor will trigger
- In monitor pane (pane 1): Press Ctrl+C
- Agent will stop after clear

### Immediate Stop

```bash
# Stop monitor
tmux send-keys -t 1 C-c

# Stop agent
tmux send-keys -t 0 C-c
```

## Advanced Usage

### Different Pane Layout

```bash
# Agent in pane 2, monitor in pane 5
./.claude/monitor_and_clear.sh 2
```

### Multiple Agent Workflows

Run separate tmux sessions:
```bash
# Session 1: Epic A
tmux new-session -s epic-a
# ... setup agent + monitor for epic A

# Session 2: Epic B
tmux new-session -s epic-b
# ... setup agent + monitor for epic B
```

### Background Operation

```bash
# Detach from session
tmux detach

# Reattach later
tmux attach -t auto-workflow
```

## Files

- `.claude/settings.auto-workflow.json` - Hook configuration
- `.claude/hooks/workflow_orchestrator.sh` - Hook script
- `.claude/monitor_and_clear.sh` - Monitor script
- `.claude/auto_workflow_epic.txt` - Current epic ID
- `.claude/workflow_orchestrator.log` - Hook execution log

## Example Full Setup

```bash
# 1. Start tmux
tmux new-session -s my-epic

# 2. Create monitor pane
tmux split-window -v

# 3. In pane 0 (top)
claude --settings .claude/settings.auto-workflow.json

# 4. In pane 1 (bottom)
./.claude/monitor_and_clear.sh 0

# 5. Back in pane 0
/set-epic citations-my-epic
/bd-start <first-task>

# 6. Watch it work!
```

## Tips

- **Monitor pane size**: Keep it small, you just need to see status messages
- **Agent pane size**: Give it most of the screen for context
- **tmux mouse mode**: Enable for easy pane switching: `tmux set -g mouse on`
- **Scrollback**: Agent pane will have full history, use tmux scroll mode (Ctrl+b [)
