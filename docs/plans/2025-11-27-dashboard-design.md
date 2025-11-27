# Internal Operational Dashboard - Design Document

**Date:** 2025-11-27
**Issue:** citations-xyov
**Status:** Design Complete, Ready for Implementation

---

## 1. Overview

Build internal operational dashboard to monitor citation validation activity on production VPS using existing log data.

**Key Goals:**
- Track validation volume and patterns
- Monitor system health (API latency, errors)
- Understand user behavior (free vs paid)
- Drill down into specific validations

---

## 2. Architecture

### Component Structure

```
/opt/citations/dashboard/
├── log_parser.py          # Parse logs → extract validations (two-pass)
├── database.py            # SQLite setup + queries
├── api.py                 # FastAPI app + endpoints
├── parse_logs_cron.py     # Script called by cron every 5 min
├── requirements.txt       # Dependencies (FastAPI already installed)
├── static/
│   ├── index.html         # Main dashboard UI
│   ├── style.css          # Styling with main site color palette
│   └── app.js             # Fetch data, render table, interactions
├── data/
│   └── validations.db     # SQLite database
└── README.md              # Setup instructions
```

### Data Flow

```
app.log → Log Parser (two-pass) → SQLite DB ← API Endpoints ← Web UI
              ↓                         ↑
         (cron every 5 min)      (query on request)
```

### Technology Stack

- **Backend:** FastAPI (already installed), uvicorn, Python 3.10+
- **Database:** SQLite (stdlib sqlite3 module)
- **Frontend:** Vanilla HTML/CSS/JS, no frameworks
- **Deployment:**
  - Systemd service: `citations-dashboard`
  - Port: 4646, bind to 0.0.0.0
  - Cron job: every 5 minutes

---

## 3. Data Model

### SQLite Schema

```sql
CREATE TABLE validations (
    job_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    duration_seconds REAL,
    citation_count INTEGER,
    token_usage_prompt INTEGER,
    token_usage_completion INTEGER,
    token_usage_total INTEGER,
    user_type TEXT NOT NULL,      -- 'free' or 'paid'
    status TEXT NOT NULL,          -- 'completed', 'failed', 'pending'
    error_message TEXT
);

CREATE INDEX idx_created_at ON validations(created_at);
CREATE INDEX idx_status ON validations(status);
CREATE INDEX idx_user_type ON validations(user_type);

-- Metadata table for tracking parser state
CREATE TABLE parser_metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);
-- Stores: last_parsed_timestamp, last_parsed_line_number, last_parse_error

-- Parser errors table (for dashboard visibility)
CREATE TABLE parser_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    error_message TEXT NOT NULL,
    log_line TEXT
);
```

### Data Currently Available in Logs

✅ Job ID, timestamps (creation, completion)
✅ User type (free/paid)
✅ Citation count
✅ Token usage (prompt + completion)
✅ LLM API call duration
✅ Success/failure status
✅ Error messages for failed jobs

### Data NOT Yet Available (Future Enhancements)

❌ User IP/identifier → Issue: citations-08wk
❌ Credits before/after → Issue: citations-wekx
❌ Valid/invalid counts → Issue: citations-oaci
❌ Full citation details → Issue: citations-6b51

---

## 4. Log Parsing Strategy

### Two-Pass Parsing Approach

**Why two-pass:**
- Logs are small (7.6MB currently, ~20-30MB for 30 days)
- Correctness over speed (easier to verify)
- Simple debugging (inspect state between passes)
- Easy to add new metrics without complex state management

**Pass 1 - Build job lifecycle:**
```python
# Extract job creation, completion, failure events
# Build: {job_id: {created_at, completed_at, status, user_type}}
```

**Pass 2 - Match metrics to jobs:**
```python
# Find LLM metrics between creation/completion timestamps
# Add: duration, token_usage, citation_count to each job
```

### Log Event Patterns

**Job Creation:**
```
2025-11-27 07:57:46 - citation_validator - INFO - app.py:590 - Creating async job {job_id} for {free|paid} user
```

**Job Completion:**
```
2025-11-27 07:58:33 - citation_validator - INFO - app.py:539 - Job {job_id}: Completed successfully
```

**Job Failure:**
```
2025-11-26 16:01:41 - citation_validator - ERROR - app.py:542 - Job {job_id}: Failed with error: {error_msg}
```

**LLM Metrics:**
```
2025-11-27 07:58:33 - openai_provider - INFO - openai_provider.py:101 - OpenAI API call completed in {duration}s
2025-11-27 07:58:33 - openai_provider - INFO - openai_provider.py:108 - Token usage: {prompt} prompt + {completion} completion = {total} total
2025-11-27 07:58:33 - openai_provider - INFO - openai_provider.py:119 - Found {count} citation result(s)
```

### Incremental Parsing

**Cron job (every 5 minutes):**
```python
def parse_new_events():
    last_parsed = get_metadata('last_parsed_timestamp')
    # Parse only log lines after last_parsed
    # Insert new validations into DB
    # Update last_parsed_timestamp
```

**Initial setup:**
```python
# Parse last 3 days of logs (configurable)
# Populate DB from scratch
# Provides real data for testing
```

### Error Handling

- If parsing fails: log error to `parser_errors` table
- Dashboard shows recent parse errors in a banner/section
- Continue processing (don't block on single parse error)

---

## 5. API Endpoints

### Authentication

- **None for MVP** (network security via VPN/SSH sufficient)
- Run on 0.0.0.0:4646

### Endpoints

```python
# Get validations with filtering
GET /api/validations?limit=100&offset=0&from=2025-11-20&to=2025-11-27&status=completed&user_type=free
Response: {
  "validations": [...],
  "total": 1523,
  "limit": 100,
  "offset": 0
}

# Get single validation details
GET /api/validations/{job_id}
Response: {
  "job_id": "abc-123",
  "created_at": "2025-11-27T07:57:46Z",
  "completed_at": "2025-11-27T07:58:33Z",
  "duration_seconds": 47.0,
  "citation_count": 1,
  "token_usage": {
    "prompt": 700,
    "completion": 3259,
    "total": 3959
  },
  "user_type": "free",
  "status": "completed",
  "error_message": null
}

# Get summary stats
GET /api/stats?from=2025-11-20&to=2025-11-27
Response: {
  "total_validations": 245,
  "completed": 220,
  "failed": 25,
  "total_citations": 1234,
  "free_users": 180,
  "paid_users": 65,
  "avg_duration_seconds": 35.2,
  "avg_citations_per_validation": 5.1
}

# Get parser health
GET /api/health
Response: {
  "status": "ok",
  "last_parsed": "2025-11-27T08:00:00Z",
  "recent_errors": [...]  // Last 5 parse errors if any
}

# Serve static files
GET /
GET /static/{file}
```

### Data Freshness

- **Strategy:** Serve from DB only
- **Update frequency:** Cron job every 5 minutes
- **Acceptable delay:** Up to 5 minutes for new validations
- **Trade-off:** Fast responses > real-time updates

---

## 6. User Interface

### Single Page Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Internal Dashboard - Citation Validations                  │
│  [Manual Refresh Button]                    Last: 08:05:23  │
├─────────────────────────────────────────────────────────────┤
│  Filters:                                                    │
│  [Last 7 days ▼] [Status: All ▼] [User: All ▼] [Search___] │
├─────────────────────────────────────────────────────────────┤
│  Stats: 245 total | 220 ✓ | 25 ✗ | Avg: 35.2s | 5.1 cites │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Job ID      Time      Duration  Cites  Tokens   User  Stat │
│  ─────────────────────────────────────────────────────────  │
│  abc-123    07:58     47.0s      1      3,959    Free   ✓   │
│  def-456    07:55     32.1s      5      8,234    Paid   ✓   │
│  ghi-789    07:50     -          -      -        Free   ✗   │
│                                                              │
│  [< Prev]  Page 1 of 5  [Next >]  [50|100|200 per page]    │
└─────────────────────────────────────────────────────────────┘
```

### Table Features

**Columns:**
- Job ID (clickable to expand)
- Timestamp (sortable)
- Duration (sortable, color-coded if >30s)
- Citations (sortable)
- Tokens (sortable)
- User Type (Free/Paid)
- Status (✓ Completed / ✗ Failed)

**Interactions:**
- Click column header to sort (ascending/descending)
- Click job ID to expand row with full details
- Manual refresh button (no auto-refresh)
- Pagination: 50/100/200 rows per page

**Expanded Row Details:**
```
Job Details: abc-123
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Created:    2025-11-27 07:57:46
Completed:  2025-11-27 07:58:33
Duration:   47.0 seconds

Citations:  1
Tokens:     700 prompt + 3,259 completion = 3,959 total
User Type:  Free
Status:     Completed

[For failed jobs, show error message here]
```

### Color Coding (Main Site Palette)

```css
/* Brand colors */
--color-brand: #9333ea;           /* Primary purple */
--color-brand-hover: #7c3aed;

/* Status colors */
--color-success: #047857;         /* Green - completed */
--color-success-bg: #ecfdf5;

--color-error: #b45309;           /* Amber - failed */
--color-error-bg: #fffbeb;

--color-warning: #d97706;         /* Orange - slow (>30s) */
--color-warning-bg: #fef3c7;

/* Text */
--color-text-primary: #1a1f36;
--color-text-secondary: #4a5568;

/* Backgrounds */
--color-bg-primary: #ffffff;
--color-bg-secondary: #fafbfc;
--border-color: #e5e7eb;
```

**Application:**
- ✓ Completed jobs: Green text/background
- ✗ Failed jobs: Amber text/background
- ⚠ Slow requests (>30s): Orange highlight
- Hover states: Purple brand color
- Table borders: Light gray (#e5e7eb)

### Filters

**Date Range:**
- Last 24 hours
- Last 7 days (default)
- Last 30 days
- Custom range (date picker)

**Status:**
- All (default)
- Completed only
- Failed only

**User Type:**
- All (default)
- Free only
- Paid only

**Search:**
- Free text search on job ID

---

## 7. Deployment

### Systemd Service

**File:** `/etc/systemd/system/citations-dashboard.service`

```ini
[Unit]
Description=Citations Internal Dashboard
After=network.target

[Service]
Type=simple
User=deploy
WorkingDirectory=/opt/citations/dashboard
ExecStart=/opt/citations/venv/bin/uvicorn api:app --host 0.0.0.0 --port 4646
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Commands:**
```bash
sudo systemctl enable citations-dashboard
sudo systemctl start citations-dashboard
sudo systemctl status citations-dashboard
```

### Cron Job

**File:** `/etc/cron.d/citations-dashboard`

```cron
# Parse logs every 5 minutes
*/5 * * * * deploy /opt/citations/venv/bin/python3 /opt/citations/dashboard/parse_logs_cron.py >> /opt/citations/logs/dashboard-cron.log 2>&1
```

### Access

**From local machine (via SSH tunnel):**
```bash
ssh -L 4646:localhost:4646 deploy@178.156.161.140
# Then browse to http://localhost:4646
```

**From VPN (direct access):**
```bash
# Connect to VPN first, then:
http://178.156.161.140:4646
```

---

## 8. Implementation Plan

### Phase 1: Core Infrastructure

1. **Log Parser Module** (`log_parser.py`)
   - Implement two-pass parsing
   - Extract job lifecycle events
   - Match LLM metrics to jobs
   - Handle edge cases (incomplete jobs, missing metrics)

2. **Database Module** (`database.py`)
   - SQLite schema setup
   - CRUD operations
   - Query helpers (filters, pagination, stats)

3. **Cron Script** (`parse_logs_cron.py`)
   - Incremental parsing (only new log lines)
   - Error handling and logging
   - Metadata tracking (last_parsed_timestamp)

### Phase 2: API Layer

4. **FastAPI Application** (`api.py`)
   - All endpoints defined in Section 5
   - Static file serving
   - CORS if needed (probably not)

### Phase 3: Frontend

5. **Web UI** (`static/`)
   - `index.html`: Page structure
   - `style.css`: Styling with brand colors
   - `app.js`:
     - Fetch data from API
     - Render table dynamically
     - Handle sorting, filtering, pagination
     - Expand/collapse row details
     - Manual refresh

### Phase 4: Deployment

6. **Systemd Service Setup**
   - Create service file
   - Enable and start service
   - Verify access

7. **Cron Job Setup**
   - Create cron file
   - Initial data load (parse last 3 days)
   - Verify cron runs successfully

### Phase 5: Testing

8. **Validation**
   - Test with real logs from production
   - Verify all metrics parsed correctly
   - Test edge cases (failed jobs, missing data)
   - Performance check (query speed with 30 days data)

---

## 9. Success Criteria

✅ Dashboard accessible at http://VPS_IP:4646
✅ Shows last 100 validations correctly
✅ Can filter by date range, status, user type
✅ Can search by job ID
✅ Click job ID shows full details
✅ Color coding works (green/amber/orange)
✅ Sorting works on all columns
✅ Pagination works (50/100/200 per page)
✅ Stats summary accurate
✅ Manual refresh updates data
✅ Data updates within 5 minutes of log entry
✅ Parse errors visible in dashboard
✅ Performance acceptable (queries <500ms)

---

## 10. Future Enhancements (Separate Issues)

**Related Issues:**
- citations-08wk: Add user IP/identifier logging
- citations-wekx: Add credits before/after logging
- citations-oaci: Add valid/invalid counts logging
- citations-6b51: Persist full citation results for drill-down
- citations-au4u: Set up log rotation to prevent disk space issues

**Potential Future Features:**
- Charts/graphs for trends over time
- Email alerts for high error rates
- Export data to CSV
- Filter by IP/user (once logged)
- Auto-refresh toggle (optional)
- Dark mode (use brand colors)
- Mobile responsive design

---

## 11. Dependencies & Prerequisites

### Already Installed
- FastAPI ✓ (in requirements.txt)
- uvicorn ✓ (in requirements.txt)
- Python 3.10+ ✓
- SQLite ✓ (stdlib)

### New Dependencies
**None!** All required libraries already present.

### Environment Requirements
- VPS access (SSH)
- Port 4646 available
- Cron access for deploy user
- Systemd access (sudo for setup)

---

## 12. Risk Mitigation

**Risk: Log rotation breaks parser**
- Mitigation: Parser handles compressed logs (.gz)
- Track last_parsed_line_number as fallback
- Related issue: citations-au4u (log rotation setup)

**Risk: Database grows too large**
- Mitigation: Retention policy (keep 90 days, configurable)
- Vacuum DB monthly (cron job)
- Monitor disk usage

**Risk: Parsing performance degrades**
- Mitigation: Current approach handles 30 days easily
- If needed, switch to stream parsing or structured logs
- Index on created_at for fast queries

**Risk: Port 4646 conflicts**
- Mitigation: Check port availability before deployment
- Make port configurable via environment variable

---

## 13. Notes

- **YAGNI applied:** No features beyond requirements (no charts, alerts, etc.)
- **Simple over complex:** Two-pass parsing, vanilla JS, no framework
- **Build for data available today:** Don't block on future logging enhancements
- **Operational utility first:** Polish comes later if needed
- **Easy to extend:** Clean separation (parser, DB, API, UI)

---

## End of Design Document

**Next Steps:**
1. Review and approve this design
2. Create implementation plan with detailed tasks
3. Begin Phase 1 implementation (log parser + DB)
