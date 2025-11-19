# Testing Validation UX

## Mock Mode (Frontend Testing Without Backend)

To test the new validation UX components without running the backend:

### Enable Mock Mode

1. The `.env.local` file is already configured with `VITE_MOCK_MODE=true`
2. Restart the dev server if it was already running:
   ```bash
   cd frontend/frontend
   npm run dev
   ```

### Test the Flow

1. Open http://localhost:5174/
2. Paste some citations in the editor
3. Click "Check My Citations"

**What you should see:**

1. **Loading State** (3 seconds):
   - Citations appear line-by-line with 250ms delay
   - After all revealed, status messages rotate every 5s
   - Spinner animation in status column

2. **Results Table**:
   - Summary header with citation counts
   - Table with 5 sample citations
   - Citations #1, #3, #5 are valid (truncated to 2 lines)
   - Citations #2, #4 have errors (expanded by default)
   - Click chevron buttons to expand/collapse

### Disable Mock Mode

To test with real backend:

1. Edit `.env.local` and set:
   ```
   VITE_MOCK_MODE=false
   ```
2. Start backend:
   ```bash
   cd backend
   python3 -m uvicorn main:app --reload
   ```
3. Restart dev server

## Manual Testing Checklist

See issue `citations-378` for complete end-to-end test cases.
