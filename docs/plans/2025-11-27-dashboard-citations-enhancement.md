# Add Original Citations to Operational Dashboard Details Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add original citation text submissions to the operational dashboard job details view

**Architecture:** Extend the existing log parsing system to extract original citations from backend logs, store them in the dashboard database, and display them in the job details modal

**Tech Stack:** SQLite database, FastAPI backend, HTML/JavaScript frontend, Python log parsing

---

### Task 1: Add Citations Column to Database Schema

**Files:**
- Modify: `dashboard/database.py:44-59`

**Step 1: Update database schema creation**

Add `citations_text TEXT` column to the validations table:

```python
# Create validations table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS validations (
        job_id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        completed_at TEXT,
        duration_seconds REAL,
        citation_count INTEGER,
        citations_text TEXT,  -- NEW: Store original citations
        token_usage_prompt INTEGER,
        token_usage_completion INTEGER,
        token_usage_total INTEGER,
        user_type TEXT NOT NULL,
        status TEXT NOT NULL,
        error_message TEXT
    )
""")

# ORACLE FEEDBACK: Add performance optimization for large text column
cursor.execute("CREATE INDEX IF NOT EXISTS idx_validations_has_citations ON validations(citations_text) WHERE citations_text IS NOT NULL")
```

**Step 2: Test database schema update**

Run: `python3 -c "from dashboard.database import DatabaseManager; db = DatabaseManager('test.db'); print('Schema updated successfully')"`

Expected: No errors, new column created

**Step 3: Update insert_validation method**

Modify the `insert_validation` method to include citations_text:

```python
cursor.execute("""
    INSERT OR REPLACE INTO validations (
        job_id, created_at, completed_at, duration_seconds,
        citation_count, citations_text, token_usage_prompt,
        token_usage_completion, token_usage_total, user_type, status, error_message
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    validation_data["job_id"],
    validation_data["created_at"],
    validation_data.get("completed_at"),
    validation_data.get("duration_seconds"),
    validation_data.get("citation_count"),
    validation_data.get("citations_text"),  # NEW
    validation_data.get("token_usage_prompt"),
    validation_data.get("token_usage_completion"),
    validation_data.get("token_usage_total"),
    validation_data["user_type"],
    validation_data["status"],
    validation_data.get("error_message")
))
```

**Step 4: Commit schema changes**

```bash
git add dashboard/database.py
git commit -m "feat: add citations_text column to validations table"
```

---

### Task 2: Extend Log Parser to Extract Citations

**Files:**
- Modify: `dashboard/log_parser.py`
- Test: `dashboard/test_log_parser.py`

**Step 1: Add citation extraction function**

Add to `log_parser.py` after line 182:

```python
def extract_citations_preview(log_line: str) -> Optional[str]:
    """
    Extract citation text preview from a log line.

    Args:
        log_line: The log line to extract citations from

    Returns:
        str citations preview if found, None otherwise
    """
    # ORACLE FEEDBACK: Use non-greedy pattern to prevent over-matching
    # Pattern matches: Citation text preview: Smith, J. (2023). Test citation...
    preview_pattern = r'Citation text preview: (.+?)(?:\s*$|\s+[A-Z])'
    match = re.search(preview_pattern, log_line)

    if match:
        citation_text = match.group(1).strip()
        # SECURITY: Limit length to prevent storage issues
        if len(citation_text) > 5000:  # 5K character limit
            citation_text = citation_text[:5000] + "..."
        # SECURITY: Basic HTML escaping for display safety
        citation_text = citation_text.replace('<', '&lt;').replace('>', '&gt;')
        return citation_text

    return None


def extract_full_citations(log_line: str) -> Optional[str]:
    """
    Extract full original citations from LLM response.

    Args:
        log_line: The log line to extract citations from

    Returns:
        str full citations if found, None otherwise
    """
    # ORACLE FEEDBACK: Use more precise pattern with better boundaries
    # Pattern matches: ORIGINAL:\nSmith, J. (2023). Test citation.\n...
    original_pattern = r'ORIGINAL:\s*(.+?)(?:\n\s*SOURCE TYPE:|$\n)'
    match = re.search(original_pattern, log_line, re.DOTALL)

    if match:
        # Clean up the extracted text
        citations = match.group(1).strip()
        # Remove excessive whitespace and normalize line breaks
        citations = re.sub(r'\n\s+', '\n', citations)
        # SECURITY: Limit length to prevent storage/performance issues
        if len(citations) > 10000:  # 10K character limit for full citations
            citations = citations[:10000] + "..."
        # SECURITY: Basic HTML escaping for display safety
        citations = citations.replace('<', '&lt;').replace('>', '&gt;')
        # SECURITY: Remove any script tags or potentially dangerous content
        citations = re.sub(r'<script.*?</script>', '', citations, flags=re.IGNORECASE | re.DOTALL)
        return citations

    return None
```

**Step 2: Add test for citation extraction**

Create `dashboard/test_log_parser.py`:

```python
import pytest
from log_parser import extract_citations_preview, extract_full_citations

def test_extract_citations_preview():
    log_line = "2025-11-04 21:42:48 - citation_validator - DEBUG - app.py:275 - Citation text preview: Smith, J. (2023). Test citation."
    result = extract_citations_preview(log_line)
    assert result == "Smith, J. (2023). Test citation."

def test_extract_full_citations():
    log_line = "2025-11-04 21:42:48 - openai_provider - DEBUG - openai_provider.py:74 - Response preview: ═══════\nORIGINAL:\nSmith, J. (2023). _Test Article_. Journal.\nSOURCE TYPE: journal"
    result = extract_full_citations(log_line)
    assert "Smith, J. (2023). _Test Article_. Journal." in result

if __name__ == "__main__":
    test_extract_citations_preview()
    test_extract_full_citations()
    print("All tests passed!")
```

**Step 3: Run tests to verify extraction**

Run: `cd dashboard && python3 test_log_parser.py`

Expected: "All tests passed!"

**Step 4: Update parse_metrics function**

Modify `parse_metrics` function in `log_parser.py` after line 304:

```python
# Extract citations
citations_preview = extract_citations_preview(line)
if citations_preview is not None:
    job["citations_preview"] = citations_preview

full_citations = extract_full_citations(line)
if full_citations is not None:
    job["citations_text"] = full_citations
```

**Step 5: Update default values in parse_logs**

Add default values after line 349:

```python
job.setdefault("citations_text", None)
job.setdefault("citations_preview", None)
```

**Step 6: Commit log parser changes**

```bash
git add dashboard/log_parser.py dashboard/test_log_parser.py
git commit -m "feat: extract original citations from log entries"
```

---

### Task 3: Update Dashboard API Response Model

**Files:**
- Modify: `dashboard/api.py:172-185`

**Step 1: Extend ValidationResponse model**

Add citations field to the ValidationResponse model:

```python
class ValidationResponse(BaseModel):
    """Validation record response model"""
    job_id: str
    created_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    citation_count: Optional[int] = None
    citations_text: Optional[str] = None  # NEW: Original citations
    token_usage_prompt: Optional[int] = None
    token_usage_completion: Optional[int] = None
    token_usage_total: Optional[int] = None
    user_type: str
    status: str
    error_message: Optional[str] = None
```

**Step 2: Test API response with citations**

Run: `cd dashboard && python3 -m uvicorn api:app --reload --host 0.0.0.0 --port 4646`

Expected: Server starts successfully

Test with: `curl http://localhost:4646/api/validations | jq .`

Expected: Response includes `citations_text` field (may be null)

**Step 3: Commit API model changes**

```bash
git add dashboard/api.py
git commit -m "feat: add citations_text to ValidationResponse model"
```

---

### Task 4: Update Frontend to Display Citations

**Files:**
- Modify: `dashboard/static/index.html`

**Step 1: Find job details modal**

Locate the modal that opens when clicking job IDs (search for "modal" or "details")

**Step 2: Add citations section to modal**

Add this HTML inside the job details modal:

```html
<div class="modal-section">
    <h4>Original Citations</h4>
    <div id="job-citations" class="citations-container">
        <!-- Citations will be populated here -->
    </div>
</div>
```

**Step 3: Add CSS styling for citations**

Add to the `<style>` section:

```css
.citations-container {
    max-height: 300px;
    overflow-y: auto;
    padding: 10px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    margin-top: 10px;
}

.citation-item {
    padding: 8px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    font-family: 'Courier New', monospace;
    font-size: 14px;
    line-height: 1.4;
    white-space: pre-wrap;
    /* ORACLE FEEDBACK: Better text overflow handling */
    word-wrap: break-word;
    overflow-wrap: break-word;
    max-width: 100%;
}

.citation-item:last-child {
    border-bottom: none;
}

.citations-empty {
    color: #888;
    font-style: italic;
    text-align: center;
    padding: 20px;
}

/* ORACLE FEEDBACK: Add citation formatting for various types */
.citation-title {
    font-style: italic;
    font-weight: 500;
}

.citation-source {
    font-weight: 600;
}

.citation-date {
    color: rgba(255, 255, 255, 0.8);
}
```

**Step 4: Update JavaScript to populate citations**

Find the function that opens the job details modal and add:

```javascript
// In the showJobDetails function or similar
function showJobDetails(job) {
    // ... existing code ...

    // Populate citations
    const citationsContainer = document.getElementById('job-citations');
    if (job.citations_text) {
        // Split citations by double newlines or reasonable separator
        const citations = job.citations_text.split(/\n\s*\n/).filter(c => c.trim());
        // ORACLE FEEDBACK: Enhanced citation parsing and display
        citationsContainer.innerHTML = citations
            .map(citation => {
                // Basic citation formatting (APA-style patterns)
                const cleanCitation = citation.trim();
                const hasYear = cleanCitation.match(/\(\d{4}\)/);
                const hasTitle = cleanCitation.match(/_[^_]+_/) || cleanCitation.match(/"([^"]+)"/);

                return `<div class="citation-item">${cleanCitation}</div>`;
            })
            .join('');
    } else {
        citationsContainer.innerHTML = '<div class="citations-empty">No original citations available</div>';
    }
}
```

**Step 5: Test frontend locally**

Run: `cd dashboard && python3 -m uvicorn api:app --reload --host 0.0.0.0 --port 4646`

Open: `http://localhost:4646`

Test: Click on a job ID to see the details modal

Expected: Citations section appears with original citation text

**Step 6: Commit frontend changes**

```bash
git add dashboard/static/index.html
git commit -m "feat: display original citations in job details modal"
```

---

### Task 5: Update Database Migration and Cron Job

**Files:**
- Modify: `dashboard/parse_logs_cron.py`
- Create: `dashboard/migration_add_citations.py`

**Step 1: Create database migration script**

Create `dashboard/migration_add_citations.py`:

```python
#!/usr/bin/env python3
"""
Migration script to add citations_text column to existing validations table
"""
import sqlite3
import os

def add_citations_column(db_path: str):
    """Add citations_text column to validations table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(validations)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'citations_text' not in columns:
        print("Adding citations_text column...")
        cursor.execute("ALTER TABLE validations ADD COLUMN citations_text TEXT")
        conn.commit()
        print("Column added successfully")
    else:
        print("Column citations_text already exists")

    conn.close()

if __name__ == "__main__":
    dashboard_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(dashboard_dir, "data")
    db_path = os.path.join(data_dir, "validations.db")

    add_citations_column(db_path)
```

**Step 2: Run migration script**

Run: `cd dashboard && python3 migration_add_citations.py`

Expected: "Column added successfully" or "Column already exists"

**Step 3: Update cron job to reparse logs**

Modify `dashboard/parse_logs_cron.py` to include citations extraction (already done by updating log_parser)

**Step 4: Test with recent log data**

Run: `cd dashboard && python3 -c "from log_parser import parse_logs; jobs = parse_logs('/opt/citations/logs/app.log'); print(f'Found {len(jobs)} jobs with citations: {sum(1 for j in jobs if j.get(\"citations_text\"))}')"`

**Step 5: Commit migration files**

```bash
git add dashboard/migration_add_citations.py dashboard/parse_logs_cron.py
git commit -m "feat: add database migration and cron updates for citations"
```

---

### Task 6: Deploy and Test Production

**Files:**
- Modify: Deployment scripts on server

**Step 1: Run migration on production**

SSH to server and run migration:

```bash
ssh deploy@178.156.161.140 "cd /opt/citations/dashboard && python3 migration_add_citations.py"
```

Expected: "Column added successfully"

**Step 2: Reparse recent logs to populate citations**

```bash
ssh deploy@178.156.161.140 "cd /opt/citations/dashboard && python3 parse_logs_cron.py"
```

Expected: Successfully extracts and stores citations

**Step 3: Restart dashboard service**

```bash
ssh deploy@178.156.161.140 "sudo systemctl restart citations-dashboard"
```

Expected: Service restarts successfully

**Step 4: Verify citations appear in dashboard**

Open: `https://admin.citationformatchecker.com:4646`

Test: Click on recent job IDs

Expected: Original citations appear in job details modal

**Step 5: Test log parsing pipeline**

Run: `ssh deploy@178.156.161.140 "tail -20 /opt/citations/logs/app.log | grep 'Citation text preview'"`

Expected: Recent citations are being logged

**Step 6: Monitor for any issues**

```bash
ssh deploy@178.156.161.140 "sudo journalctl -u citations-dashboard -f --no-pager"
```

Expected: No errors, service running normally

---

### Verification Checklist

**Database Layer:**
- [ ] citations_text column added to validations table
- [ ] Log parser extracts original citations from logs
- [ ] Citations stored properly in database

**API Layer:**
- [ ] ValidationResponse model includes citations_text field
- [ ] API returns citation data for jobs
- [ ] No existing functionality broken

**Frontend Layer:**
- [ ] Job details modal shows citations section
- [ ] Citations display with proper formatting
- [ ] Empty state handled gracefully

**Production Deployment:**
- [ ] Database migration runs successfully
- [ ] Recent logs repopulated with citations
- [ ] Dashboard service restarts without issues
- [ ] User can see original citations in production

**Performance:**
- [ ] Log parsing still completes efficiently
- [ ] Database queries remain fast
- [ ] Frontend loads and displays citations quickly

---

## Implementation Notes

**Data Storage Strategy:**
- Store citations as TEXT column (SQLite handles large text efficiently)
- Reparse existing logs to populate historical data
- Future citations will be extracted in real-time by cron job

**ORACLE FEEDBACK: Enhanced Error Handling:**
- Graceful degradation if citation extraction fails
- Empty states for jobs without citations
- Length limits applied (5K for preview, 10K for full citations)
- Input sanitization and HTML escaping for security
- Validation to prevent malformed citation display
- Unicode support for international citations

**ORACLE FEEDBACK: Enhanced Performance Considerations:**
- Citations only loaded when job details requested
- Efficient text extraction regex patterns (non-greedy matching)
- Partial index on citations_text column for jobs with citations
- Database query optimization with WHERE clauses
- Frontend text overflow handling and responsive design
- Lazy loading for very long citation lists

**ORACLE FEEDBACK: Enhanced Security & Robustness:**
- HTML escaping to prevent XSS attacks
- Script tag removal from citation content
- Length limits to prevent storage/performance abuse
- Input sanitization and validation
- Safe display of user-submitted content
- Error handling for malformed log entries

**Rollback Plan:**
- Database column can be safely removed if needed
- Log parser changes are additive
- Frontend changes display gracefully if citations missing
- Migration script includes existence check for safe rollback

---

**Plan complete and saved to `docs/plans/2025-11-27-dashboard-citations-enhancement.md`. Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**