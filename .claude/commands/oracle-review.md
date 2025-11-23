External code review using `claude -p` with iterative refinement (up to 3 rounds).

**IMPORTANT**: This is an **external review**, NOT a standard code-reviewer subagent review.
- Do NOT launch the `superpowers:code-reviewer` subagent
- Do NOT use the Task tool to dispatch code reviewers
- Instead, follow the external review process below which uses `claude -p`

## Step 1: Determine Issue ID

- Check conversation context - what issue are we working on?
- Check git status and recent commits if needed
- If unclear, ask the user
- **Once determined, use this issue ID consistently throughout the review process**

## Step 2: Understand Review Format

Read the `superpowers:requesting-code-review` skill to understand how to structure the review request. You'll create a prompt similar to what the code-reviewer subagent would receive.

## Step 3: Execute Review Loop (max 3 rounds)

Start with ROUND=1, increment after each iteration.

### For Each Round:

**1. Gather information:**
- Get BASE_SHA: `git rev-parse HEAD~1` (or appropriate base commit)
- Get HEAD_SHA: `git rev-parse HEAD`
- Get task context: `bd show <issue-id>`
- Identify what was implemented (2-3 sentence summary)
- Extract key requirements from the task description

**2. Create review prompt:**

Save to `./tmp/<issue-id>-review-request-round-<N>.md` with content similar to code-reviewer subagent format:

```
You are conducting a code review.

## Task Context

### Beads Issue ID: <issue-id>

<output from bd show>

### What Was Implemented

<Your 2-3 sentence summary of what was actually built/changed>

### Requirements/Plan

<Key requirements from task description - what should have been implemented>

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: <base-sha>
- HEAD_SHA: <head-sha>

Use git commands (git diff, git show, git log, etc.) to examine the changes.

## Review Criteria

Evaluate the implementation against these criteria:

**Adherence to Task:**
- Does implementation match task requirements?
- Were all requirements addressed?
- Any scope creep or missing functionality?

**Security:**
- SQL injection, XSS, command injection vulnerabilities
- Hardcoded secrets or credentials
- Input validation and sanitization

**Code Quality:**
- Follows project standards and patterns
- Clear naming and structure
- Appropriate error handling
- Edge cases covered

**Testing:**
- Tests written and passing
- Coverage adequate
- Tests verify actual behavior

**Performance & Documentation:**
- No obvious performance issues
- Code is self-documenting or commented

## Required Output Format

Provide structured feedback in these categories:

1. **Critical**: Must fix immediately (security, broken functionality, data loss)
2. **Important**: Should fix before merge (bugs, missing requirements, poor patterns)
3. **Minor**: Nice to have (style, naming, optimization opportunities)
4. **Strengths**: What was done well

**IMPORTANT**: Verify implementation matches task requirements above.

Be specific with file:line references for all issues.
```

**3. Send to Claude for review:**

Pipe the prompt to a fresh Claude session and save the response:

```
cat ./tmp/<issue-id>-review-request-round-<N>.md | claude -p --dangerously-skip-permissions > ./tmp/<issue-id>-review-response-round-<N>.md &
CLAUDE_PID=$!
( sleep 600; kill $CLAUDE_PID 2>/dev/null ) &
TIMEOUT_PID=$!
wait $CLAUDE_PID 2>/dev/null
kill $TIMEOUT_PID 2>/dev/null
```

**4. Process feedback:**

- Read `./tmp/<issue-id>-review-response-round-<N>.md`
- Use `superpowers:receiving-code-review` skill to process the feedback
- Verify technical claims (don't blindly accept)
- Categorize and prioritize issues
- Push back with reasoning if reviewer is wrong

**5. Apply fixes for Critical and Important issues:**

- Make code changes
- Commit with clear message
- Update HEAD_SHA: run `git rev-parse HEAD` again

**6. Decide next action:**

- **No issues or only Minor issues**: Go to Completion step
- **Disagreement with reviewer**: Document disagreement and go to Completion
- **Round < 3 and issues fixed**: Increment ROUND and repeat from step 1
- **Round == 3**: Stop, document remaining issues, go to Completion

## Completion

When review is satisfactory:

1. Remove needs-review label: `bd label remove <issue-id> needs-review`
2. Add approved label: `bd label add <issue-id> approved`
3. Report completion with artifact locations:
   - `./tmp/<issue-id>-review-request-round-*.md` (review prompts sent)
   - `./tmp/<issue-id>-review-response-round-*.md` (reviewer responses)

## Key Principles

- Use requesting-code-review and receiving-code-review skills for process
- Create fresh review prompt each round (captures new changes)
- Verify reviewer claims (they can be wrong)
- Stop after 3 rounds max
- Stop early if no actionable issues or disagreement
