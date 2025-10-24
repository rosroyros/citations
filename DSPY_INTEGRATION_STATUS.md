# DSPy Validator Integration Status

Date: 2025-10-24

## Summary

Integration of the optimized DSPy validator V2 is **90% complete** with one blocking issue preventing production deployment.

## ✅ Completed

### 1. Provider Architecture
- Created `backend/providers/dspy_provider.py` extending `CitationValidator` base class
- Loads optimized prompt from `Checker_Prompt_Optimization/optimized_output_v2/optimized_validator_v2.json`
- Implements all required methods:
  - `validate_citations()` - main async validation method
  - `_load_optimized_predictor()` - loads optimized instructions and creates DSPy predictor
  - `_markdown_to_html()` - converts `_text_` to `<em>text</em>` for frontend compatibility
  - `_html_to_text()` - converts HTML citations to plain text
  - `_split_citations()` - splits multiple citations
  - `_parse_prediction()` - parses DSPy output to API format

### 2. Configuration Management
- Moved DSPy config from `backend/pseo/optimization/dspy_config.py` to `backend/dspy_config.py`
- Added singleton pattern to prevent duplicate DSPy configuration in async contexts
- Integrated into app initialization with `VALIDATOR_PROVIDER` env variable

### 3. App Integration
- Updated `backend/app.py` to support provider switching
- Env variable `VALIDATOR_PROVIDER`:
  - `"openai"` (default) - uses existing OpenAI provider
  - `"dspy"` - uses new DSPy provider
- Both providers return identical response structure

### 4. Testing
- Created unit tests (`backend/tests/test_dspy_provider.py`) for utility functions:
  - ✅ Markdown to HTML conversion
  - ✅ HTML to text conversion
  - ✅ Citation splitting
  - ✅ Provider initialization
- Created manual test script (`test_dspy_manual.py`):
  - ✅ **DSPy predictor works perfectly in isolation**
  - ✅ Sync predictor calls successful
  - ✅ Async validation successful in standalone script

## ❌ Blocking Issue

### DSPy Crashes in FastAPI/Uvicorn Context

**Symptoms:**
- Server starts successfully and loads DSPy provider
- Logs show: "Optimized predictor created successfully"
- API request causes server to crash with "Empty reply from server"
- No error logs captured (crashes before logging)

**Root Cause (Suspected):**
- DSPy's OpenAI client may have issues with FastAPI's multiprocessing/async context
- Despite wrapping predictor call in `loop.run_in_executor()`, still crashes
- May be related to DSPy's global configuration state or threading

**Evidence:**
```bash
# Manual test (standalone script) - WORKS ✅
$ python3 test_dspy_manual.py
✅ All tests passed!

# FastAPI server - CRASHES ❌
$ curl http://localhost:8000/api/validate
curl: (52) Empty reply from server
```

## Files Created/Modified

### New Files:
- `backend/providers/dspy_provider.py` - DSPy provider implementation
- `backend/dspy_config.py` - DSPy configuration (moved from pseo/optimization/)
- `backend/tests/test_dspy_provider.py` - Unit tests
- `test_dspy_manual.py` - Manual isolation test

### Modified Files:
- `backend/app.py` - Added provider switching logic

## Next Steps to Fix

### Option 1: Debug FastAPI Integration
1. Add exception handling with full stack traces around predictor call
2. Test with different FastAPI/uvicorn workers (`--workers 1 --loop asyncio`)
3. Try running uvicorn without reload mode
4. Check if DSPy has FastAPI-specific integration requirements

### Option 2: Use HTTP Wrapper
1. Run DSPy predictor in separate microservice
2. FastAPI calls DSPy service via HTTP
3. Avoids multiprocessing issues entirely

### Option 3: Use Different DSPy Pattern
1. Instead of `ChainOfThought`, try `Predict` directly
2. Simplify signature creation
3. Test if issue is with specific DSPy module type

## How to Test Locally

### Test DSPy in Isolation (Works):
```bash
source venv/bin/activate
python3 test_dspy_manual.py
```

### Test via FastAPI (Crashes):
```bash
# Enable DSPy provider
echo "VALIDATOR_PROVIDER=dspy" >> .env

# Start server
source venv/bin/activate
PYTHONPATH=. python3 -m uvicorn backend.app:app --reload --port 8000

# Test (in another terminal)
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

### Use OpenAI Provider (Current Fallback):
```bash
# Remove DSPy config (uses OpenAI by default)
sed -i '' '/^VALIDATOR_PROVIDER=/d' .env

# Start server
source venv/bin/activate
PYTHONPATH=. python3 -m uvicorn backend.app:app --reload --port 8000
```

## Deployment Strategy

Until the FastAPI issue is resolved, recommend:
1. **Deploy with OpenAI provider** (current stable implementation)
2. **Keep DSPy code in repo** (ready for future use)
3. **Continue debugging FastAPI integration** in development

The architecture is sound and the DSPy predictor works perfectly - just needs the FastAPI compatibility issue resolved.

## Architecture Diagram

```
┌─────────────────────────┐
│   Frontend (React)      │
│   - App.jsx (main)      │
│   - MiniChecker.jsx     │
└───────────┬─────────────┘
            │ POST /api/validate
            ▼
┌─────────────────────────┐
│   FastAPI Backend       │
│   backend/app.py        │
└───────────┬─────────────┘
            │
     ┌──────┴──────┐
     ▼             ▼
┌─────────────┐  ┌─────────────┐
│  OpenAI     │  │   DSPy      │
│  Provider   │  │  Provider   │
│  (stable)   │  │ (90% done)  │
└─────────────┘  └─────────────┘
                       │
                       ▼
              ┌───────────────────┐
              │ Optimized Prompt  │
              │  V2 (JSON)        │
              └───────────────────┘
```

## Contact

For questions about this integration:
- Check `test_dspy_manual.py` for working example
- Review `backend/providers/dspy_provider.py` for implementation
- See `backend/app.py` line 19-26 for provider switching logic
