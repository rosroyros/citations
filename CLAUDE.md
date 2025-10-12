# Development Workflow

## Core Principles
- **One task at a time**: Mark as in_progress � complete � next task
- **Test-driven development**: Write test � implement � verify � commit
- **Meaningful commits**: One commit per logical change, easy to revert
- **No long-lived branches**: Direct commits to main with clear messages
- **ALWAYS mark tasks as completed**: Immediately after finishing each task, mark it as completed in the todo list. Never batch completions.

## Task Flow
1. Mark current task as `in_progress` in todo list
2. Write test(s) for the feature/fix (FIRST!)
3. Implement until tests pass
4. Verify in logs/output that it works
5. Commit with clear message
6. **IMMEDIATELY update implementation plan (docs/mvp_implementation_plan.md) with ✅ DONE**
7. Mark task as `completed` in todo list
8. Commit the plan update
9. Move to next task

**CRITICAL**: Step 6 is NON-NEGOTIABLE. Never skip updating the implementation plan document.

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
