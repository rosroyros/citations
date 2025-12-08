External code review using `gemini` with iterative refinement (up to 3 rounds).

**IMPORTANT**: This is an **external review**, NOT a standard code-reviewer subagent review.
- Do NOT launch the `superpowers:code-reviewer` subagent
- Do NOT use the Task tool to dispatch code reviewers
- Instead, follow the external review process below which uses `gemini`

## Prerequisites

**COMMIT YOUR CHANGES FIRST**: This process reviews committed changes. Uncommitted work will not be reviewed.
```bash
git status  # Verify clean state or commit pending changes
```

## Step 1: Determine Issue ID

- Check conversation context - what issue are we working on?
- Check git status and recent commits if needed
- If unclear, ask the user
- **Once determined, use this issue ID consistently throughout the review process**

## Step 2: Prepare Review Request

**Read the `superpowers:requesting-code-review` skill** to understand:
- When and how to request reviews
- What information to gather
- How to structure the review prompt
- Review checklist categories
- Output format requirements

Use the Skill tool to load it if needed.

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

Following the template from `superpowers:requesting-code-review` skill, save to `./tmp/<issue-id>-review-request-round-<N>.md`:

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
- **Frontend visual/UX changes: Playwright tests REQUIRED for any visual or user interaction changes**

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

**3. Send to Gemini for review:**

Pipe the prompt to a fresh  session and save the response:

```bash
cat ./tmp/<issue-id>-review-request-round-<N>.md | gemini -y -m "pro" 2>&1 | tee ./tmp/<issue-id>-review-response-round-<N>.md
```

Note: Use `tee` instead of `>` redirect to properly capture streaming output.

**IMPORTANT**:
- Use Bash tool with `timeout: 300000` (5 minutes) when running this command
- Wait for the review to complete (may take several minutes)
- After completion, verify output is not truncated:

```bash
RESPONSE_FILE="./tmp/<issue-id>-review-response-round-<N>.md"
LINE_COUNT=$(wc -l < "$RESPONSE_FILE")

if [ ! -s "$RESPONSE_FILE" ] || [ "$LINE_COUNT" -lt 10 ]; then
  echo "⚠️  Review output seems truncated ($LINE_COUNT lines). Retry the gemini command."
else
  echo "✓ Review complete ($LINE_COUNT lines)"
fi
```

If truncated, re-run the command.

**4. Process feedback:**

**Read the `superpowers:receiving-code-review` skill** for detailed methodology on:
- 6-step verification pattern (READ → UNDERSTAND → VERIFY → EVALUATE → RESPOND → IMPLEMENT)
- How to verify technical claims against codebase
- When and how to push back with technical reasoning
- Handling unclear feedback (stop and clarify first)
- Implementation order (one at a time, test each)
- YAGNI checks

Then apply to the review response:
- Read `./tmp/<issue-id>-review-response-round-<N>.md`
- Follow the receiving-code-review methodology
- Categorize issues: Critical (must fix), Important (should fix), Minor (nice to have)
- Document disagreements clearly if pushing back

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

- Use `superpowers:requesting-code-review` skill for structuring review requests
- Use `superpowers:receiving-code-review` skill for processing feedback
- Create fresh review prompt each round (captures new changes)
- Verify reviewer claims (they can be wrong)
- Stop after 3 rounds max
- Stop early if no actionable issues or disagreement
- Document all review artifacts in `./tmp/` for traceability
