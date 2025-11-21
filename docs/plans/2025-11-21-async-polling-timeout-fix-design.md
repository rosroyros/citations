# Async Polling Architecture for Cloudflare Timeout Fix

**Date:** 2025-11-21
**Status:** Design Complete
**Related Issue:** citations-ry7
**Author:** Claude Code (brainstorming session)

## Problem Statement

### Current Issue
- Large citation batches (50+ citations) exceed Cloudflare's 100s timeout limit
- gpt-5-mini with medium reasoning takes ~20s for 8-9 citations
- Extrapolated: 50 citations = ~120s processing time
- Results in 504 Gateway Timeout errors for users

### Root Cause
- Single synchronous HTTP request holds connection open during entire LLM processing
- Cloudflare free plan: 100s hard limit (cannot be increased)
- Model choice (gpt-5-mini) cannot be changed due to accuracy requirements

### Why Not Batching?
- Citation boundary detection is non-trivial without another LLM call
- Parsing errors would introduce additional complexity and failure modes
- Async polling solves the root issue more elegantly

## Solution Overview

### Architecture: Async Job Processing with Polling

**Key Principle:** Decouple HTTP request timeout from LLM processing time.

**Flow:**
```
User submits → Backend creates job (returns immediately)
              ↓
              Background worker processes validation (no timeout)
              ↓
              Frontend polls every 2s for results
              ↓
              Results ready → Display to user
```

**Benefits:**
- No HTTP timeout (request completes immediately)
- Backend can take 150s+ to process without errors
- User sees progress via existing loading animation
- Works with existing credit system
- No infrastructure changes needed

## Detailed Design

### Backend Implementation

#### 1. Job Storage (In-Memory)

```python
# Global dict to track jobs
jobs: Dict[str, Dict[str, Any]] = {}

Job structure:
{
    "job-uuid-123": {
        "status": "pending" | "processing" | "completed" | "failed",
        "created_at": 1234567890.0,
        "results": {...},           # Populated when status=completed
        "error": "...",              # Populated when status=failed
        "token": "user-token-xyz",  # For credit tracking (None for free users)
        "free_used": 5,             # For free tier tracking (None for paid users)
        "citation_count": 50        # Number of citations submitted
    }
}
```

**Why in-memory?**
- Simple implementation (no DB schema changes)
- Jobs are ephemeral (results viewed once, then gone)
- Lost on server restart = acceptable tradeoff
- 30min TTL means bounded memory usage

#### 2. New API Endpoints

**POST /api/validate/async**
```python
@app.post("/api/validate/async")
async def validate_citations_async(http_request: Request, request: ValidationRequest, background_tasks: BackgroundTasks):
    """
    Create async validation job.

    Returns immediately with job_id.
    Background worker processes validation.
    """
    # Generate job ID
    job_id = str(uuid.uuid4())

    # Extract token/free_used from headers
    token = http_request.headers.get('X-User-Token')
    free_used_header = http_request.headers.get('X-Free-Used', '')

    try:
        free_used = int(base64.b64decode(free_used_header).decode('utf-8'))
    except:
        free_used = 0

    # Check credits BEFORE starting job (fail fast)
    if token:
        from database import get_credits
        user_credits = get_credits(token)
        if user_credits == 0:
            raise HTTPException(
                status_code=402,
                detail="You have 0 Citation Credits remaining. Purchase more to continue."
            )
    else:
        # Free tier - check limit
        FREE_LIMIT = 10
        affordable = FREE_LIMIT - free_used
        if affordable <= 0:
            raise HTTPException(
                status_code=402,
                detail="Free tier limit reached. Purchase credits to continue."
            )

    # Convert HTML to text
    citations_text = html_to_text_with_formatting(request.citations)

    # Create job entry
    jobs[job_id] = {
        "status": "pending",
        "created_at": time.time(),
        "results": None,
        "error": None,
        "token": token,
        "free_used": free_used,
        "citation_count": 0  # Will be updated after validation
    }

    # Start background processing
    background_tasks.add_task(process_validation_job, job_id, citations_text, request.style)

    logger.info(f"Created job {job_id} for {'paid' if token else 'free'} user")

    return {"job_id": job_id, "status": "pending"}
```

**GET /api/jobs/{job_id}**
```python
@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Get job status and results.

    Returns:
    - pending: Still processing
    - processing: LLM call in progress
    - completed: Results ready
    - failed: Error occurred
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] == "completed":
        return {
            "status": "completed",
            "results": job["results"]
        }
    elif job["status"] == "failed":
        return {
            "status": "failed",
            "error": job["error"]
        }
    else:
        return {
            "status": job["status"]
        }
```

#### 3. Background Worker

```python
async def process_validation_job(job_id: str, citations: str, style: str):
    """
    Background task to process validation.
    No HTTP timeout applies here.
    """
    try:
        # Update status
        jobs[job_id]["status"] = "processing"
        logger.info(f"Job {job_id}: Starting validation")

        # Call LLM (can take 120s+)
        validation_results = await llm_provider.validate_citations(
            citations=citations,
            style=style
        )

        results = validation_results["results"]
        citation_count = len(results)
        jobs[job_id]["citation_count"] = citation_count

        # Handle credit/free tier logic (same as existing /api/validate)
        token = jobs[job_id]["token"]

        if not token:
            # Free tier
            free_used = jobs[job_id]["free_used"]
            FREE_LIMIT = 10
            affordable = max(0, FREE_LIMIT - free_used)

            if affordable >= citation_count:
                # Return all results
                jobs[job_id]["results"] = {
                    "results": results,
                    "free_used_total": free_used + citation_count
                }
            else:
                # Partial results
                jobs[job_id]["results"] = {
                    "results": results[:affordable],
                    "partial": True,
                    "citations_checked": affordable,
                    "citations_remaining": citation_count - affordable,
                    "free_used_total": FREE_LIMIT
                }
        else:
            # Paid tier
            from database import get_credits, deduct_credits
            user_credits = get_credits(token)

            if user_credits >= citation_count:
                # Can afford all
                success = deduct_credits(token, citation_count)
                if not success:
                    raise Exception("Failed to deduct credits")

                jobs[job_id]["results"] = {
                    "results": results,
                    "credits_remaining": user_credits - citation_count
                }
            else:
                # Partial results
                affordable = user_credits
                success = deduct_credits(token, affordable)
                if not success:
                    raise Exception("Failed to deduct credits")

                jobs[job_id]["results"] = {
                    "results": results[:affordable],
                    "partial": True,
                    "citations_checked": affordable,
                    "citations_remaining": citation_count - affordable,
                    "credits_remaining": 0
                }

        jobs[job_id]["status"] = "completed"
        logger.info(f"Job {job_id}: Completed successfully")

    except Exception as e:
        logger.error(f"Job {job_id}: Failed with error: {str(e)}", exc_info=True)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
```

#### 4. Job Cleanup

```python
@app.on_event("startup")
async def start_cleanup_task():
    """Start background task to cleanup old jobs."""
    import asyncio
    asyncio.create_task(cleanup_old_jobs())

async def cleanup_old_jobs():
    """Delete jobs older than 30 minutes."""
    while True:
        await asyncio.sleep(300)  # Run every 5 minutes

        now = time.time()
        threshold = 30 * 60  # 30 minutes

        jobs_to_delete = [
            job_id for job_id, job in jobs.items()
            if now - job["created_at"] > threshold
        ]

        for job_id in jobs_to_delete:
            del jobs[job_id]
            logger.info(f"Cleaned up old job: {job_id}")
```

#### 5. Retry Logic for OpenAI

Update `backend/providers/openai_provider.py`:

```python
async def validate_citations(self, citations: str, style: str = "apa7") -> Dict[str, Any]:
    """
    Validate citations using OpenAI API with retry logic.
    """
    max_retries = 3
    retry_delay = 2  # seconds

    for attempt in range(max_retries):
        try:
            # Existing OpenAI API call logic
            response = await self.client.chat.completions.create(**completion_kwargs)
            # ... parse response ...
            return {"results": results}

        except (APITimeoutError, RateLimitError) as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"OpenAI API error (attempt {attempt+1}/{max_retries}): {str(e)}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"OpenAI API failed after {max_retries} attempts")
                raise ValueError("Request timed out after multiple retries. Please try again later.") from e

        except (AuthenticationError, APIError) as e:
            # Don't retry on auth/API errors
            raise
```

### Frontend Implementation

#### 1. Submit Handler Changes

**File:** `frontend/frontend/src/App.jsx`

```javascript
const handleSubmit = async (e) => {
  e.preventDefault()

  if (!editor) return

  // Clear abandonment timer
  if (abandonmentTimerRef.current) {
    clearTimeout(abandonmentTimerRef.current)
    abandonmentTimerRef.current = null
  }

  const token = getToken()
  const freeUsed = getFreeUsage()

  // Check free tier limit (existing logic)
  if (!token && freeUsed >= 10) {
    trackEvent('upgrade_modal_shown', { trigger: 'free_limit' })
    setShowUpgradeModal(true)
    return
  }

  const htmlContent = editor.getHTML()
  const textContent = editor.getText()

  // Capture submitted text for loading state
  setSubmittedText(htmlContent)
  setLoading(true)
  setError(null)
  setResults(null)

  try {
    // Build headers
    const headers = { 'Content-Type': 'application/json' }
    if (token) {
      headers['X-User-Token'] = token
    } else {
      // Free tier - send usage count
      const freeUsed = getFreeUsage()
      headers['X-Free-Used'] = btoa(String(freeUsed))
    }

    // Call async endpoint
    const response = await fetch('/api/validate/async', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        citations: htmlContent,
        style: 'apa7',
      }),
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Failed to create validation job')
    }

    const { job_id } = await response.json()

    // Store job_id for page refresh recovery
    localStorage.setItem('current_job_id', job_id)

    // Start polling
    pollForResults(job_id)

  } catch (err) {
    console.error('Job creation error:', err)
    setError(err.message)
    setLoading(false)
  }
}
```

#### 2. Polling Logic

```javascript
const pollForResults = async (jobId) => {
  const maxAttempts = 90  // 3 minutes (90 * 2s = 180s)
  let attempts = 0

  const poll = async () => {
    if (attempts++ >= maxAttempts) {
      setError('Processing is taking longer than expected. Please try again.')
      setLoading(false)
      localStorage.removeItem('current_job_id')
      return
    }

    try {
      const response = await fetch(`/api/jobs/${jobId}`)

      if (!response.ok) {
        if (response.status === 404) {
          setError('Job not found. It may have expired.')
        } else {
          setError('Failed to check job status. Please try again.')
        }
        setLoading(false)
        localStorage.removeItem('current_job_id')
        return
      }

      const data = await response.json()

      if (data.status === 'completed') {
        // Success! Clear job_id and display results
        localStorage.removeItem('current_job_id')

        // Sync localStorage with backend's authoritative count
        if (data.results.free_used_total !== undefined) {
          localStorage.setItem('citation_checker_free_used', String(data.results.free_used_total))
        }

        // Handle response (same as existing logic)
        if (data.results.partial) {
          setResults({ ...data.results, isPartial: true })
        } else {
          setResults(data.results)

          // Track analytics
          const citationsCount = data.results.results.length
          const errorsFound = data.results.results.reduce((sum, result) => sum + (result.errors?.length || 0), 0)
          const perfectCount = data.results.results.filter(result => !result.errors || result.errors.length === 0).length
          const userType = token ? 'paid' : 'free'

          trackEvent('citation_validated', {
            citations_count: citationsCount,
            errors_found: errorsFound,
            perfect_count: perfectCount,
            user_type: userType
          })

          // Increment free counter if no token
          if (!token) {
            incrementFreeUsage(data.results.results.length)
          }
        }

        // Refresh credits for paid users
        if (token) {
          setTimeout(() => {
            refreshCredits().catch(err =>
              console.error('Failed to refresh credits:', err)
            )
          }, 100)
        }

        setLoading(false)

      } else if (data.status === 'failed') {
        // Job failed
        localStorage.removeItem('current_job_id')
        setError(data.error || 'Validation failed. Please try again.')
        setLoading(false)

      } else {
        // Still processing (pending or processing)
        // Poll again in 2 seconds
        setTimeout(poll, 2000)
      }

    } catch (err) {
      console.error('Polling error:', err)
      // Retry once on network error, then fail
      if (attempts < maxAttempts) {
        setTimeout(poll, 2000)
      } else {
        setError('Network error. Please check your connection and try again.')
        setLoading(false)
        localStorage.removeItem('current_job_id')
      }
    }
  }

  // Start polling
  poll()
}
```

#### 3. Page Refresh Recovery

```javascript
// Add to component (after existing useEffect hooks)
useEffect(() => {
  // On component mount - recover job if page was refreshed
  const existingJobId = localStorage.getItem('current_job_id')
  if (existingJobId) {
    console.log('Recovering job from page refresh:', existingJobId)
    setLoading(true)
    pollForResults(existingJobId)
  }
}, [])
```

#### 4. Loading State Warning

Update the loading state component to show warning:

```javascript
// In ValidationLoadingState component or wherever loading UI is shown
<div className="loading-container">
  <div className="loading-spinner">Processing...</div>
  <div className="loading-warning">
    ⚠️ This can take up to 3 minutes. Please don't refresh the page.
  </div>
  {/* Existing loading table animation */}
</div>
```

## Testing Strategy

### 1. Unit Tests (Local, Mocked LLM)

**File:** `tests/test_async_jobs.py`

Tests:
- ✅ Job creation returns valid job_id
- ✅ Job status transitions (pending → processing → completed)
- ✅ Job polling returns results when complete
- ✅ Job cleanup after 30 minutes
- ✅ Credit check before job creation (402 if zero credits)
- ✅ Free tier limit enforcement

**Run:** `pytest tests/test_async_jobs.py -v` (fast, <5s)

### 2. Integration Tests (Local, Real LLM)

**File:** `tests/test_async_jobs_integration.py`

Tests:
- ✅ Small batch (2 citations) completes in ~30s
- ✅ Paid user with X-User-Token header (credits deducted)
- ✅ Free user with X-Free-Used header (partial results)
- ✅ Retry logic on OpenAI timeout
- ✅ Page refresh recovery (store/retrieve job_id)

**Run:** `pytest tests/test_async_jobs_integration.py -m integration -v` (slow, 2-5min)

**Prerequisites:**
- Set `OPENAI_API_KEY` in environment
- Create test user token with credits in local database

### 3. Manual Testing (Local)

**Environment:**
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

**Test cases:**
1. Free user (5 citations) - completes in ~20s ✅
2. Free user (15 citations) - gets 10 results + paywall ✅
3. Page refresh during polling - recovers and shows results ✅
4. Submit button disabled during polling ✅
5. Large batch (50 citations) - completes in ~120s without timeout ✅

### 4. Production Smoke Test (After Deploy)

**Test:**
- Submit 1 citation as free user
- Verify completes correctly
- Don't do extensive testing (costs money)

**Monitor logs:**
```bash
ssh deploy@178.156.161.140
tail -f /opt/citations/logs/app.log
```

Look for:
- Job creation/completion logs
- OpenAI API timing
- Credit deduction success
- Any errors

## Implementation Checklist

### Backend Tasks
- [ ] Add job storage dict to `backend/app.py`
- [ ] Implement POST `/api/validate/async` endpoint
- [ ] Implement GET `/api/jobs/{job_id}` endpoint
- [ ] Implement background worker `process_validation_job()`
- [ ] Add job cleanup task with 30min TTL
- [ ] Add retry logic to `OpenAIProvider.validate_citations()`
- [ ] Update `ValidationResponse` schema (if needed)

### Frontend Tasks
- [ ] Update `handleSubmit()` to call `/api/validate/async`
- [ ] Implement `pollForResults()` function
- [ ] Add page refresh recovery in `useEffect()`
- [ ] Add warning message to loading state ("Don't refresh page")
- [ ] Store job_id in localStorage
- [ ] Clean up job_id after completion
- [ ] Handle polling timeout (3min max)
- [ ] Handle 402 errors (out of credits)

### Testing Tasks
- [ ] Write unit tests (`tests/test_async_jobs.py`)
- [ ] Write integration tests (`tests/test_async_jobs_integration.py`)
- [ ] Create test fixtures (small/medium/large batches)
- [ ] Manual testing checklist (5 scenarios)
- [ ] Document testing procedure in README

### Deployment Tasks
- [ ] Test locally with real LLM
- [ ] Commit to git with clear message
- [ ] Push to GitHub
- [ ] Deploy to production VPS
- [ ] Run smoke test (1 citation)
- [ ] Monitor logs for 30 minutes
- [ ] Update documentation

## Deployment Notes

### Deployment Procedure
```bash
# 1. Local testing
pytest tests/test_async_jobs.py -v
pytest tests/test_async_jobs_integration.py -m integration -v
# Manual testing with npm run dev

# 2. Commit and push
git add .
git commit -m "feat: implement async polling to fix Cloudflare timeout (citations-ry7)"
git push origin main

# 3. Deploy to production
ssh deploy@178.156.161.140
cd /opt/citations
./deployment/scripts/deploy.sh

# 4. Monitor
tail -f /opt/citations/logs/app.log

# 5. Smoke test
# Open browser, submit 1 citation, verify works
```

### Rollback Plan
If async implementation causes issues:

```bash
ssh deploy@178.156.161.140
cd /opt/citations
git revert HEAD
./deployment/scripts/deploy.sh
```

The old synchronous `/api/validate` endpoint remains unchanged, so rolling back is safe.

### Monitoring Metrics

**Success criteria:**
- Job completion rate: >99%
- Average processing time: 20-120s (depending on batch size)
- Failed jobs: <1%
- Memory usage: Stable (jobs cleaned up after 30min)

**Warning signs:**
- Jobs stuck in "processing" state
- Memory growing unbounded
- 402 errors for users with credits
- Polling timeouts (>3min)

## Future Enhancements (Out of Scope)

- WebSocket/SSE for real-time updates (instead of polling)
- Progress percentage during processing
- Database persistence for job recovery after restart
- Job queue with worker pool for better scalability
- Rate limiting per user to prevent abuse

## References

- Original issue: citations-ry7
- Related issues: citations-qmf (free tier enforcement), citations-dzy (frontend paywall sync)
- Design inspiration: 2025-11-19-validation-latency-ux-design.md
