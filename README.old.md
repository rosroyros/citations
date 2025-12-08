# Citation Validator MVP

APA 7th edition citation validator using LLM.

## Setup

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

4. Run backend:
```bash
cd backend
python3 -m uvicorn app:app --reload
```

5. Run frontend (separate terminal):
```bash
cd frontend
npm install
npm run dev
```

## Architecture

### Async Polling Architecture (Nov 2025)

Decouples HTTP timeout from LLM processing time:

```
User → Frontend → POST /api/validate/async → Background Worker
                          ↓                          ↓
                       Job ID                  LLM Processing
                          ↓                          ↓
                   Polling Loop ← GET /api/jobs/{job_id} ← Job Storage
                          ↓
                      Results
```

**Flow:**
1. Frontend submits citations to `/api/validate/async`
2. Backend creates job, returns job ID immediately
3. Background worker processes citations with LLM (45-60s)
4. Frontend polls `/api/jobs/{job_id}` every 2s (3min max timeout)
5. Job expires after 30min or server restart

**Benefits:**
- No HTTP timeouts during long LLM processing
- Progressive UI updates as results arrive
- Automatic recovery from page refresh
- Better error handling and retry logic

## API Endpoints

### Async Validation (Current)

**Create validation job:**
```bash
POST /api/validate/async
Content-Type: application/json

{
  "citations": ["Smith, J. (2020). Book title. Publisher."]
}

Response:
{
  "job_id": "uuid-string",
  "status": "processing"
}
```

**Poll job status:**
```bash
GET /api/jobs/{job_id}

Responses:
- 200: {"status": "processing", "results": [...partial...]}
- 200: {"status": "completed", "results": [...all...]}
- 404: Job not found (expired or invalid ID)
```

### Legacy Endpoint

`POST /api/validate` - Deprecated, kept for backward compatibility. Use `/api/validate/async` instead.

## Recent Updates

### Async Polling Implementation (Nov 2025)

**Features:**
- Background job processing with in-memory storage
- 30-minute job TTL with automatic cleanup
- Partial results streaming during processing
- Page refresh recovery with localStorage
- OpenAI retry logic with exponential backoff (up to 3 attempts)
- Button disabled during polling to prevent duplicate jobs

**Design Documentation:**
- Architecture: `docs/plans/2025-11-21-async-polling-timeout-fix-design.md`
- Implementation details in individual issue docs

**Testing:**
- E2E tests: `frontend/frontend/tests/e2e/async-polling-validation.spec.js`

### Validation UX Improvements (Nov 2025)

Enhanced citation validation experience:

**New Features:**
- Progressive loading state with text reveal animation
- Rotating status messages during validation
- Table-based results with expand/collapse functionality
- Invalid citations expanded by default for quick scanning
- Keyboard navigation (Tab, Enter, Space)
- Full accessibility support (ARIA, screen readers)
- Mobile responsive layout
- Smooth error state transitions

**Design Documentation:**
- Design spec: `docs/plans/2025-11-19-validation-latency-ux-design.md`
- Implementation: `docs/plans/2025-11-19-validation-latency-ux-implementation.md`
- Mockup: `docs/plans/validation-table-mockup.html`
- Component docs: `frontend/frontend/src/components/README.md`

**Key Components:**
- `ValidationLoadingState` - Progressive reveal with status messages
- `ValidationTable` - Interactive results table with expand/collapse

## Troubleshooting

### Async Polling Issues

**Job stuck in "processing" state:**
- Check backend logs: `tail -f logs/app.log` (local) or `journalctl -u citations-backend -f` (production)
- May need to restart backend if worker thread crashed
- Job will auto-expire after 30 minutes

**Job not found (404 error):**
- Job expired after 30min TTL
- Server restarted (in-memory storage cleared)
- Invalid job ID
- Solution: Retry validation with new job

**Polling timeout (3min) without results:**
- Batch too large (>50 citations)
- OpenAI API slow/degraded
- Check network connectivity
- Solution: Retry with smaller batch or wait and retry

**Partial results not appearing:**
- Normal - results stream in as citations complete
- Check browser console for polling errors
- Verify `/api/jobs/{job_id}` endpoint accessible

**Page refresh loses job:**
- Should auto-recover via localStorage
- If not, check browser console for errors
- Verify `job_id` in localStorage matches URL

## Monitoring

### Key Metrics to Track

**Job lifecycle:**
- Job creation rate: Monitor POST /api/validate/async requests
- Job completion time: Track time from creation to completed status
- Job failure rate: Count jobs ending in "failed" status

**System health:**
- In-memory job count: Check active jobs in backend memory
- Cleanup effectiveness: Monitor jobs deleted by 30min TTL
- Backend worker health: Check for stuck "processing" jobs

**User experience:**
- Polling success rate: Track 404s on GET /api/jobs/{job_id}
- Timeout rate: Count jobs hitting 3min frontend timeout

**Logs:**
- Local: `tail -f logs/app.log`
- Production: `journalctl -u citations-backend -f`
- Key patterns: "Creating async job", "Job completed", "Job failed"

## Project Structure
```
citations/
├── backend/       # FastAPI backend
├── frontend/      # React frontend
│   └── src/
│       └── components/  # See README.md for component docs
├── tests/         # Test files
├── docs/          # Documentation and design specs
└── logs/          # Application logs
```
