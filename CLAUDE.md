**IMPORTANT**: You MUST read `README.md` at the start of every session to ensure understanding of the system.

**Note**: This project uses [bd (beads)](https://github.com/steveyegge/beads) for issue tracking. Use `bd` commands instead of markdown TODOs.

# Development Workflow
WHEN IMPLEMENTING A PLAN FROM A DOCUMENT OR AGREED UPON WITH THE USER - IF THERE ARE UNEXPECTED ISSUES ALWAYS STOP AND ASK FOR GUIDANCE AND NEVER CONTINUE BEFORE GETTING ANSWERS.
## Core Principles
- **Beads-first workflow**: Always `bd show <id>` before starting, update description during work, close with summary
- **One task at a time**: Focus on single task, update bd status as you progress
- **Test-driven development**: Use `superpowers:test-driven-development` skill
- **Testing best practices**: Use `superpowers:testing-anti-patterns` skill
- **Frontend visual/UX changes**: MUST include Playwright tests for visual or user interaction changes
- **Debugging**: Use `superpowers:systematic-debugging` skill
- **Verification**: Use `superpowers:verification-before-completion` before commits/PRs
- **Code review**: Use `/oracle-review` when ready
- **Meaningful commits**: One commit per logical change, easy to revert
- **No long-lived branches**: Direct commits to main with clear messages

## Task Statuses & Labels

bd supports 4 statuses: `open`, `in_progress`, `blocked`, `closed`

Quality gate labels track review workflow:
- `needs-review` - Code complete, awaiting review (use `/oracle-review`)
- `approved` - Reviewed and approved, ready to deploy

### Workflow States

- `open` - Ready to start
- `in_progress` - Developer working
- `in_progress` + label `needs-review` - Awaiting code review
- `in_progress` + label `approved` - Ready to deploy
- `blocked` - Needs architect help
- `closed` - Deployed/completed

### Commands

- Update status: `bd update <id> --status in_progress`
- Add label: `bd label add <id> needs-review`
- Remove label: `bd label remove <id> needs-review`


## Beads Workflow Integration

### Starting Any Task

**MANDATORY before starting work**:
1. `bd show <id>` - Read COMPLETE description and context
2. `bd dep tree <id>` - Check dependencies and blockers
3. `bd update <id> --status in_progress`
4. Create TodoWrite todos based on issue requirements
5. Check which superpowers skills apply (TDD, debugging, etc.)

**Alternative**: Use `/bd-start <id>` slash command to run this workflow

### During Work

**Update description with progress** (append to original):
```bash
bd update <id> -d "$(bd show <id> --format description)

## Progress - [Date][TIME]
- Implemented X
- Discovered Y issue
- Changed approach from A to B because [reason]

## Key Decisions
- Chose [option] over [alternative] because [reasoning]
"
```

**When discovering new issues/bugs**:
```bash
# Create issue
NEW_ID=$(bd create "Bug: [title]" -t bug -p 0 --json | jq -r '.id')

# Link to current work
bd dep add $NEW_ID <current-id> --type discovered-from
```

**When blocked**:
```bash
bd update <id> --status blocked
# Create blocker issue and link it
bd dep add <id> <blocker-id> --type blocks
```

### Completing Work

1. Commit all changes (oracle-review needs committed code)
2. Update description with final summary
3. Add review label: `bd label add <id> needs-review`
4. Use `/oracle-review` (external review using claude -p) and if it fails use `/zoracle-review` (external review using gemini -m pro)
   - ⚠️ **Auto-workflow mode: Skip oracle-review, use workflow hook stages instead**
5. After approval: `bd close <id> --reason "[Summary of what was done]"`
6. **Push, Deploy & Verify**:
   - Ensure all changes are pushed: `git push origin main`
   - Run `./deploy_prod.sh` to deploy to production and run E2E tests.
   - ⚠️ **Auto-workflow mode: Skip push and deploy steps**
7. Sync: `bd sync`

### Finding Work

```bash
bd ready                    # Show all ready issues
bd ready --json | jq '.[0]' # Get top priority programmatically
bd list --status open -p 0  # Show all P0 open issues
```

### Issue Description Template

When creating issues, use structured format:
```markdown
## Context
[Why this exists, background, problem statement]

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2

## Implementation Approach
[Technical approach, constraints, considerations]

## Dependencies
- Blocks: [issue-ids if any]
- Blocked by: [issue-ids if any]

## Verification Criteria
- [ ] Tests pass
- [ ] Deployed successfully
- [ ] [Other success criteria]
```

### Label Standards

**Technical areas**:
- `backend` - Python backend code
- `frontend` - React frontend code
- `pseo` - PSEO page generation
- `deployment` - Infrastructure/deployment

**Workflow**:
- `needs-review` - Code complete, awaiting review
- `approved` - Review passed, ready to deploy
- `needs-context` - Missing information to proceed

**Type** (use issue_type field, not labels):
- `bug` - Defect to fix
- `feature` - New capability
- `task` - General work item
- `epic` - Large multi-issue effort

## Update Sitemap (If New Page)

If deploying a NEW specific-source page (not an update):

```python
from pseo.utils.sitemap_generator import SitemapGenerator
import json
from pathlib import Path

# Load sitemap
sitemap_path = "/opt/citations/frontend/frontend/dist/sitemap.xml"
sitemap_gen = SitemapGenerator(sitemap_path)

# Load specific sources config
config_file = Path("pseo/configs/specific_sources.json")
with open(config_file) as f:
    sources = json.load(f)["sources"]

# Generate sitemap entries
entries = sitemap_gen.generate_specific_source_entries(sources)

# Update sitemap
sitemap_gen.add_entries_to_sitemap(entries, sitemap_path)

print(f"✅ Sitemap updated with {len(entries)} entries")
```


## Test Job Indicator
Use "testtesttest" in citations to flag test jobs. Test jobs are filtered from dashboard metrics via `is_test_job` database column.

## Python Environment
- **Virtual Environment**: Use `venv` for Python development. Activate with `source venv/bin/activate` before running Python commands.

## Model Selection
- **Production**: Gemini 3 Flash (`gemini-3-flash-preview`) as default (model_c)
- **Configuration**: Both `OPENAI_API_KEY` and `GEMINI_API_KEY` required (OpenAI for fallback)
- **Routing**: Frontend sends `X-Model-Preference: model_c` header (all users on Gemini 3)
- **Fallback**: Gemini failures automatically fall back to OpenAI
- **A/B Testing**: Infrastructure preserved in `modelPreference.js` for future experiments
- **Monitoring**: Dashboard displays provider used (model_c = Gemini 3, model_a = OpenAI fallback)

## Style Management
- **Module**: `backend/styles.py` handles style configuration and routing
- **Supported Styles**: APA 7th Edition (default), MLA 9th Edition
- **Feature Flag**: `MLA_ENABLED=true` enables MLA 9 support

## Validation Prompts
- **APA 7**: `validator_prompt_v3_no_hallucination.txt` (deployed 2025-12-27)
- **MLA 9**: `validator_prompt_mla9_v1.1.txt`
- **Features**:
  - Uses `[MISSING: ...]` placeholders for unavailable bibliographic data instead of hallucinating
  - Ignores leading numbered bullets (1., 2., etc.) in user input
- **Testing**: 
  - APA: `Checker_Prompt_Optimization/test_v3_prompt_batched.py`
  - MLA: `Checker_Prompt_Optimization/mla9_golden_set.json` (offline validation)

