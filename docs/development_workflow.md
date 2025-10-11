# Development Workflow

## Core Principles
- **One task at a time**: Mark as in_progress → complete → next task
- **Test-driven development**: Write test → implement → verify → commit
- **Meaningful commits**: One commit per logical change, easy to revert
- **No long-lived branches**: Direct commits to main with clear messages

## Task Flow
1. Mark current task as `in_progress` in todo list
2. Write test(s) for the feature/fix
3. Implement until tests pass
4. Verify in logs/output that it works
5. Commit with clear message
6. Mark task as `completed`
7. Move to next task

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

## Testing
- **Unit tests**: Core validation logic
- **Integration tests**: API endpoints
- **E2E tests**: Full flow (input → LLM → output)
- **Run tests before commit**: `python3 -m pytest`

## Model Selection Priority
- Balance performance vs cost
- Start with OpenAI (GPT-4-mini or similar)
- Support multiple providers (abstraction layer)
