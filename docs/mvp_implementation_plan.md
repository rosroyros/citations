# MVP Implementation Plan - Citation Validator

## Project Overview
Build a local web app where users paste citations, submit them to an LLM for APA 7th validation, and receive error reports.

## Tech Stack
- **Backend**: Python (Flask or FastAPI)
- **Frontend**: React
- **LLM Provider**: OpenAI (multi-provider support built in)
- **Model**: GPT-4o-mini (cost-effective, performant)
- **Storage**: None (in-memory for MVP)
- **Input**: Paste text only
- **Dev**: Virtual environment, no database

## Scope
- **Citation styles**: APA 7th edition only
- **Source types**: Journal articles, books, book chapters, webpages
- **Output**: Simple error list per citation
- **No auth/rate limiting** for local MVP

---

## Implementation Tasks

### Phase 1: Project Setup
**Task 1: Initialize project structure** ✅ DONE
- TDD: N/A (infrastructure setup)
- Create venv, requirements.txt
- Set up Git repo with initial commit
- Create folder structure (backend/, frontend/, tests/)
- Add verbose logging setup (Python logging module configured)
- Commit: `init: project structure with venv and logging` ✅

**Task 2: Backend foundation** ✅ DONE
- TDD: Write test first - test health check endpoint returns 200
- Choose framework (Flask or FastAPI - recommend FastAPI for speed)
- Implement health check endpoint that passes test
- Add CORS for frontend communication
- Add logging for all requests (INFO level)
- Commit: `feat: basic API with health check endpoint and request logging` ✅

**Task 3: Frontend foundation** ✅ DONE
- TDD: Write test - component renders textarea and button
- Initialize React app (Vite recommended)
- Implement basic UI (paste textarea + submit button)
- Add console logging for user actions
- Commit: `feat: basic React UI with citation input form` ✅

### Phase 2: LLM Integration Layer
**Task 4: Create LLM provider abstraction** ✅ DONE
- TDD: Write test - provider interface has validate_citations method, returns expected structure
- Define provider interface/abstract class
- Implement OpenAI provider (note: can mock OpenAI API in tests to avoid costs)
- Add config for API keys (.env file)
- Add verbose logging: API calls, token usage, response times
- Commit: `feat: LLM provider abstraction with OpenAI implementation` ✅

**Task 5: Prompt management** ✅ DONE
- TDD: Write test - prompt loader returns correct text, formats citations correctly
- Load validation prompt from file (use draft_validator_prompt.md)
- Create function to format citations as input to prompt
- Log prompt construction (DEBUG level)
- Commit: `feat: prompt management with citation formatting` ✅

### Phase 3: Backend API
**Task 6: Create validation endpoint** ✅ DONE
- TDD: Write test - POST /api/validate accepts JSON, returns 200, parses citations
- Implement POST /api/validate endpoint
- Accept JSON: { "citations": "text", "style": "apa7" }
- Parse citations (split by double newlines)
- Log: received citations count, parsing results
- Commit: `feat: validation endpoint with citation parsing`

**Task 7: Connect to LLM provider** ✅ DONE
- TDD: Write test - endpoint calls LLM, returns structured errors for known bad citation
- Call OpenAI API with prompt + citations
- Parse LLM response into structured format
- Log: LLM request/response, parsing steps
- Test with REAL OpenAI API (integration test)
- Commit: `feat: integrate LLM validation into endpoint` ✅

**Task 8: Error handling** ✅ DONE
- TDD: Write tests - API errors handled, empty input rejected, timeouts handled
- Handle LLM API errors (rate limits, timeouts, invalid keys)
- Validate input (non-empty citations)
- Return appropriate error messages
- Log all errors (ERROR level)
- Commit: `feat: comprehensive error handling with logging` ✅

### Phase 4: Frontend Integration
**Task 9: Connect frontend to API** ✅ DONE
- TDD: Write test - form submission calls API endpoint
- Add form submission handler
- Call backend /api/validate endpoint
- Display loading state during validation
- Log: API calls, responses
- Commit: `feat: connect frontend to validation API` ✅

**Task 10: Display validation results** ✅ DONE
- TDD: Write test - results component displays errors correctly
- Parse API response
- Show original citations with errors listed below each
- Format errors (❌ indicator, what's wrong, should be)
- Commit: `feat: display validation results with error formatting` ✅

**Task 11: Error state handling** ✅ DONE
- TDD: Write test - API errors display user-friendly messages
- Display API errors to user
- Handle empty input
- Log: user-facing errors
- Commit: `feat: user-friendly error handling in UI` ✅

**Task 12: Add basic styling**
- TDD: N/A (visual polish)
- Implement mockup design (colors, layout, responsive)
- Add feature pills from mockup
- Improve readability of error messages
- Commit: `style: implement mockup design`

### Phase 5: Final Testing & Sample Data
**Task 13: Create comprehensive test fixtures**
- TDD: This IS the test creation
- Create test_fixtures.py with sample citations:
  - ✅ Correct APA 7th (journal, book, chapter, webpage)
  - ❌ Common errors (title case, "and" vs "&", old DOI, etc.)
- Run all citations through system, verify results
- Document any issues found
- Commit: `test: add comprehensive citation test fixtures`

**Task 14: Manual validation session**
- TDD: N/A (manual verification)
- Test with 10+ real citations from academic papers
- Verify LLM output matches APA 7th rules
- Check logs for any issues
- Fix any bugs found (new commits as needed)
- Commit: `docs: document manual validation results`

---

## Test Strategy

### Test-Driven Development Flow
**EVERY task follows this pattern:**
1. Write failing test FIRST
2. Implement feature until test passes
3. Verify in logs
4. Refactor if needed
5. Commit

### Testing Approach
- **No mocking internal code** - Test real functionality
- **Mock only external APIs** - OpenAI calls can be mocked in some tests to avoid costs
- **Verbose logging** - Every component logs its operations for debugging
- **Real integration tests** - At least some tests hit real OpenAI API to verify end-to-end

### Sample Test Citations (Task 13)
Create fixtures with:
- ✅ Correct APA 7th citations (should pass)
- ❌ Common errors (title case, "and" vs "&", old DOI format, publisher location, etc.)
- Edge cases (missing authors, no date, long author lists)

---

## Git Workflow

### Commit Strategy
- **Atomic commits**: One logical change per commit
- **Clear messages**: `type: description` format
- **Commit frequency**: After each passing test + implementation
- **No branches**: Direct commits to main (local solo dev)

### Example Commit Flow
```
git init
git add .
git commit -m "init: project structure and venv setup"

git add backend/app.py tests/test_app.py
git commit -m "feat: basic Flask app with health check endpoint"

git add backend/providers/
git commit -m "feat: LLM provider abstraction with OpenAI implementation"
```

---

## Environment Variables
```bash
# .env file
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-4o-mini
MAX_TOKENS=2000
TEMPERATURE=0.1
```

---

## Success Criteria
MVP is complete when:
- ✅ User can paste citations and submit
- ✅ Backend calls LLM with validation prompt
- ✅ Results display clearly with specific errors
- ✅ Tests pass (following TDD for each task)
- ✅ Handles common APA 7th source types (journal, book, chapter, webpage)
- ✅ Works reliably for 10+ citation batches
- ✅ Verbose logging throughout for debugging

---

## Future Enhancements (Post-MVP)
- File upload (.docx, .pdf)
- Multiple citation styles (MLA, Chicago)
- User accounts and history
- Rate limiting
- Better error messages with examples
- Citation correction suggestions
- Batch processing optimization
- Alternative LLM providers (Claude, local models)

---

## Notes
- Start with simplest possible implementation
- Prefer library solutions over custom code
- Focus on core validation accuracy over features
- Keep UI minimal but functional
- Test with real academic citations from papers
