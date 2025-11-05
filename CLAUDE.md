**Note**: This project uses [bd (beads)](https://github.com/steveyegge/beads) for issue tracking. Use `bd` commands instead of markdown TODOs. See AGENTS.md for workflow details.

# Development Workflow
WHEN IMPLEMENTING A PLAN FROM A DOCUMENT OR AGREED UPON WITH THE USER - IF THERE ARE UNEXPECTED ISSUES ALWAYS STOP AND ASK FOR GUIDANCE AND NEVER CONTINUE BEFORE GETTING ANSWERS.
## Core Principles
- **One task at a time**: Focus on single task, update status as you progress
- **Test-driven development**: Write test → implement → verify → commit
- **Meaningful commits**: One commit per logical change, easy to revert
- **No long-lived branches**: Direct commits to main with clear messages

## Task Statuses & Labels

bd supports 4 statuses: `open`, `in_progress`, `blocked`, `closed`

Quality gate labels track review workflow:
- `needs-review` - Code complete, awaiting review
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

Use `/dev-start` to begin work on a task. Other workflow commands: `/architect`, `/dev-review`, `/deploy`

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


## Git Commit Format
```
<type>: <description>

Examples:
- feat: add citation parser for journal articles
- test: add validation tests for book chapters
- fix: correct DOI format validation
- refactor: extract author name parsing logic
```

## Environment Setup
- **Always use virtual environment**: `source venv/bin/activate`
- **Python 3**: Use `python3` for all commands
- **Dependencies**: Keep `requirements.txt` updated

### Production Environment
- **VPS Access**: `ssh deploy@178.156.161.140`
- **App Directory**: `/opt/citations`
- **Backend Service**: systemd service `citations-backend`
- **Frontend**: Nginx serving React build from `/opt/citations/frontend/frontend/dist`

### Deployment Process
1. Test locally: `python3 -m pytest`
2. Push to GitHub: `git push origin main`
3. SSH to VPS: `ssh deploy@178.156.161.140`
4. Deploy: `cd /opt/citations && ./deployment/scripts/deploy.sh`

### Deployment Commands Clarification
- **Agent commands** (`/deploy`, `/restart-backend`) are for me to execute via SSH
- **Manual deployment**: Run `./deployment/scripts/deploy.sh` directly on VPS
- Both approaches accomplish the same thing - updating production

## Logging
- **Verbose logging throughout**: Use Python logging module
- **Log levels**: DEBUG for detailed flow, INFO for key steps, ERROR for issues
- **Help with debugging**: Makes it easy to troubleshoot issues

## Testing
- **Unit tests**: Core validation logic
- **Integration tests**: API endpoints with real functionality (no mocking internal code)
- **E2E tests**: Full flow (input � LLM � output)
- **Run tests before commit**: `python3 -m pytest`
- **Mock only external services**: External APIs can be mocked in tests to avoid costs/rate limits

## Model Selection Priority
- Balance performance vs cost
- Start with OpenAI (GPT-4o-mini or similar)
- Support multiple providers (abstraction layer)
