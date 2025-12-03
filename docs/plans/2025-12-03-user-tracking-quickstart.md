# User Tracking Implementation - Quick Start Guide

**Epic:** citations-euzm
**Created:** 2025-12-03

---

## For Developers: Getting Started

### Step 1: Understand the Structure

**You have 3 types of issues:**

1. **Epic** (citations-euzm) - Top-level container, tracks overall progress
2. **Phase containers** (citations-x7g2, citations-oi0l, etc.) - Organize related tasks
3. **Implementation tasks** (citations-ncxy, citations-6aoz, etc.) - Actual work

**You work on implementation tasks, NOT containers.**

### Step 2: Read the Context

Before starting, read these docs (in order):

1. **Design Document** - `docs/plans/2025-12-03-user-tracking-design.md`
   - Complete technical specs
   - Edge cases
   - Testing strategy
   - ~30 minute read

2. **Task Summary** - `docs/plans/2025-12-03-user-tracking-tasks-summary.md`
   - Task hierarchy
   - Time estimates
   - Dependencies
   - ~10 minute read

3. **This Guide** - You're reading it now
   - How to execute
   - Commands to use
   - ~5 minutes

**Total prep time:** 45 minutes (worth it to avoid mistakes)

---

## Step 3: Start with Phase 0 (Database Migration)

### View Phase 0

```bash
bd show citations-x7g2
```

This shows the phase container. It will tell you which subtasks to work on.

### Work Through Phase 0 Subtasks

```bash
# View all subtasks
bd list --json | jq -r '.[] | select(.id == "citations-ncxy" or .id == "citations-61xp" or .id == "citations-grva") | "\(.id): \(.title) [\(.status)]"'

# Start first subtask
bd show citations-ncxy
bd update citations-ncxy --status in_progress

# Read the task description carefully
# It has all implementation details

# Do the work...

# When complete
bd close citations-ncxy --reason "Migration script created and tested locally"

# Move to next subtask
bd show citations-61xp
# ... repeat process
```

### Critical: Run Migration on Production

**Task:** citations-grva

This must be done ON THE VPS before deploying any code:

```bash
# SSH to VPS
ssh deploy@178.156.161.140

# Run migration (following task instructions)
cd /opt/citations/dashboard/migrations
./backup.sh  # Create backup first!
python3 add_user_id_columns.py

# Verify success
# Close task
bd close citations-grva --reason "Migration successful, columns verified"
```

### Close Phase 0

```bash
bd close citations-x7g2 --reason "Database migration complete"
```

---

## Step 4: Continue Through Phases 1-4

### Phase 1: Frontend (citations-oi0l)

```bash
bd show citations-oi0l  # Read phase instructions
# Work through 4 subtasks (6aoz → x227, xgl1, v0rf)
bd close citations-oi0l --reason "Frontend implementation complete"
```

### Phase 2: Backend (citations-gyu8)

```bash
bd show citations-gyu8  # Read phase instructions
# Work through 4 subtasks (4lds → peav, h5dg, 8hfj)
bd close citations-gyu8 --reason "Backend implementation complete"
```

### Phase 3: Dashboard & Testing (citations-wii5)

```bash
bd show citations-wii5  # Read phase instructions
# Work through 5 subtasks (sowc → e3py, yyu4, w5h3, 8p2l)
bd close citations-wii5 --reason "Dashboard and testing complete"
```

### Phase 4: Deployment (citations-yupw)

```bash
bd show citations-yupw  # Read phase instructions
# Work through 3 subtasks (rpr3 → 5jfg → svyw)
bd close citations-yupw --reason "Deployed and verified in production"
```

---

## Step 5: Close the Epic

```bash
bd close citations-euzm --reason "User tracking fully implemented - all phases complete"
```

---

## Common Commands

### View Tasks

```bash
# View a specific task
bd show citations-ncxy

# View all open tasks
bd list --status open

# View dependency tree
bd dep tree citations-euzm
```

### Update Task Status

```bash
# Start working on task
bd update citations-ncxy --status in_progress

# Mark as blocked (if stuck)
bd update citations-ncxy --status blocked

# Close task when complete
bd close citations-ncxy --reason "Clear description of what was done"
```

### Track Progress

```bash
# Update phase description with progress
bd update citations-x7g2 -d "$(bd show citations-x7g2 --format description)

## Progress Update - $(date +%Y-%m-%d)
- Completed citations-ncxy (migration script)
- Completed citations-61xp (backup procedures)
- In progress: citations-grva (running on VPS)
"
```

---

## Tips for Success

### 1. Read Task Descriptions Carefully

Each implementation task has:
- Purpose and context
- Detailed implementation steps
- Code examples
- Testing checklist
- Verification criteria
- Reference to design doc section

**Don't skip reading!** All the info you need is in the task description.

### 2. Follow Dependencies

Tasks have dependencies. bd will show you:
- **"Blocked by"** - can't start until these complete
- **"Blocks"** - these tasks wait for you

Example:
```
citations-x227: Update App.jsx
  Blocked by: citations-6aoz
```

Means: Complete citations-6aoz before starting citations-x227.

### 3. Test Before Closing

Don't close a task until:
- Code works
- Tests pass
- Manual testing done (if applicable)
- No console errors

Better to stay "in_progress" longer than close prematurely.

### 4. Use Verification Criteria

Each task has a checklist. Example:

```markdown
### Verification Criteria
- [ ] Script created at correct path
- [ ] Tested on local database copy
- [ ] Idempotent behavior verified
- [ ] Clear success/failure messages
```

Check every box before closing the task.

### 5. Ask for Help

If stuck or unsure:
- Re-read the task description
- Check the design doc section referenced
- Ask in team chat
- Use `/oracle-ask` for technical guidance

Better to ask than make wrong assumptions.

---

## Parallel Work Opportunities

To speed up implementation, some tasks can be done in parallel:

### Phase 1 (after citations-6aoz):
- citations-x227, citations-xgl1, citations-v0rf can all run in parallel

### Phase 2 (after citations-4lds):
- citations-peav and citations-h5dg can run in parallel

### Phase 3 (after citations-sowc):
- citations-e3py and citations-w5h3 can run in parallel

**How to coordinate:**
If working solo, do sequentially. If team of 2-3, assign parallel tasks to different people.

---

## Time Estimates

**Sequential (one person):** ~17 hours
**With parallel work:** ~12-13 hours
**Recommended schedule:** 6 sessions over 2-3 days

### Session Breakdown

**Session 1 (2.5 hours):**
- Phase 0 - Database migration prep and execution

**Session 2 (3 hours):**
- Phase 1 - Frontend implementation

**Session 3 (4.5 hours):**
- Phase 2 - Backend implementation

**Session 4 (3 hours):**
- Phase 3 tasks 1-3 (parser, database, UI)

**Session 5 (3.5 hours):**
- Phase 3 tasks 4-5 (parser tests, E2E tests)

**Session 6 (2.5 hours):**
- Phase 4 - Deployment and verification

---

## Troubleshooting

### "Task shows no description"

Some tasks were created without full descriptions. If you encounter this:

1. Check if parent phase has instructions
2. Refer to design doc section for that task
3. Check task summary doc for overview

### "Dependencies confusing"

Use `bd dep tree` to visualize:

```bash
bd dep tree citations-euzm
```

Shows full hierarchy and dependencies.

### "Not sure what to work on"

Follow this priority:

1. Phase 0 first (always)
2. Within a phase, check "blocked by" - do those first
3. If multiple tasks ready, pick shortest/easiest
4. If really stuck, start with tests (usually safest)

---

## Success Criteria

You're done when:

- [ ] All 15 implementation tasks closed
- [ ] All 4 phase containers closed
- [ ] Epic (citations-euzm) closed
- [ ] Code deployed to production
- [ ] Post-deployment verification passed
- [ ] Dashboard shows user IDs for new validations
- [ ] Can query analytics (see design doc examples)

---

## Resources

- **Design Doc:** `docs/plans/2025-12-03-user-tracking-design.md`
- **Task Summary:** `docs/plans/2025-12-03-user-tracking-tasks-summary.md`
- **Code Base:** `/Users/roy/Documents/Projects/citations/`

---

## Questions?

- Check design doc first
- Then task descriptions
- Then ask team/use oracle
- Update this guide if you find gaps!

---

**Last Updated:** 2025-12-03
**Epic ID:** citations-euzm
**Total Tasks:** 20
