Now let me create my structured code review based on all the evidence I've gathered:

## Code Review: citations-pw2g - REVEAL_EVENT Parsing Implementation

### Summary
The implementation successfully addresses all requirements for parsing REVEAL_EVENT logs and storing reveal status in the dashboard database. The code is well-tested, follows security best practices, and handles edge cases appropriately.

---

## 1. **Critical** Issues
None found.

---

## 2. **Important** Issues

### 2.1 Regex Pattern May Be Too Permissive
**Location:** `dashboard/log_parser.py:201`

The `extract_reveal_event` regex uses `\S+` for job_id matching:
```python
reveal_pattern = r'REVEAL_EVENT: job_id=(\S+) outcome=(\w+)'
```

**Issue:** `\S+` matches ANY non-whitespace character sequence, which could potentially capture malformed job IDs or include trailing punctuation if the log format changes.

**Recommendation:** Use the same pattern as `extract_creation` for consistency:
```python
reveal_pattern = r'REVEAL_EVENT: job_id=([a-f0-9-]+) outcome=(\w+)'
```

**Impact:** Could lead to database insertion failures or incorrect job_id matching if log format includes unexpected characters.

---

### 2.2 Potential Data Loss from Partial Records
**Location:** `dashboard/cron_parser.py:76-82`

When a REVEAL_EVENT appears without a prior job creation event, the code creates a partial record with only `job_id`:
```python
if job_id not in jobs:
    jobs[job_id] = {
        "job_id": job_id,
        # We don't have creation time, so we can't fill it yet
    }
```

**Issue:** The comment acknowledges this is a partial record that "the ingester will need to handle," but the ingester (`cron_parser.py:84-86`) handles this by calling `update_reveal_status()`, which uses `UPDATE` and will silently fail if the job doesn't exist in the database.

**Recommendation:** Add logging when `update_reveal_status` affects 0 rows:
```python
def update_reveal_status(self, job_id: str, revealed: bool, revealed_at: str):
    cursor = self.conn.cursor()
    cursor.execute("""
        UPDATE validations
        SET results_revealed = ?, results_revealed_at = ?
        WHERE job_id = ?
    """, (1 if revealed else 0, revealed_at, job_id))
    
    if cursor.rowcount == 0:
        logger.warning(f"No existing record found for job_id={job_id} during reveal update")
    
    self.conn.commit()
```

**Impact:** Silent failure when reveal events occur for jobs not in database (e.g., after log rotation).

---

## 3. **Minor** Issues

### 3.1 Boolean Storage Inconsistency Documentation
**Location:** `dashboard/database.py:204-206, 254-256`

The code correctly stores booleans as integers (1/0) for SQLite compatibility, but this convention isn't documented in the function docstring.

**Recommendation:** Add docstring note:
```python
def insert_validation(self, validation_data: Dict[str, Any]):
    """
    Insert or update a validation record (UPSERT)
    
    Note: Boolean fields (results_revealed, results_gated) are stored as 
    integers (1=True, 0=False) for SQLite compatibility.
    
    Args:
        validation_data: Dictionary with validation fields
    """
```

---

### 3.2 Test Coverage Gap for Edge Cases
**Location:** `dashboard/test_log_parser.py:390-404`

Tests verify basic REVEAL_EVENT parsing but don't test edge cases mentioned in code comments:
- Job ID with dots/colons (comment says regex handles these)
- Reveal event when job doesn't exist in parsed jobs
- Multiple reveal events for same job (last write wins)

**Recommendation:** Add tests:
```python
def test_extract_reveal_event_complex_job_id(self):
    """Test reveal event with complex job_id format (dots, colons)."""
    log_line = "2025-11-04 21:42:48 - REVEAL_EVENT: job_id=abc.123:xyz outcome=revealed"
    result = extract_reveal_event(log_line)
    self.assertIsNotNone(result)
    self.assertEqual(result[0], "abc.123:xyz")

def test_parse_reveal_event_without_job_creation(self):
    """Test reveal event creates partial record when job doesn't exist."""
    log_lines = [
        "2025-11-04 21:42:48 - REVEAL_EVENT: job_id=orphan-123 outcome=revealed"
    ]
    jobs = parse_job_events(log_lines)
    self.assertIn("orphan-123", jobs)
    self.assertEqual(jobs["orphan-123"]["results_revealed"], 1)
```

---

### 3.3 Missing Index on New Columns
**Location:** `dashboard/database.py:92-110`

The migration adds `results_revealed` column and creates an index, but doesn't index `results_gated` or `results_revealed_at`.

**Recommendation:** Add indexes if queries will filter/sort by these fields:
```python
if 'results_gated' not in columns:
    cursor.execute("ALTER TABLE validations ADD COLUMN results_gated INTEGER DEFAULT 0")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_gated ON validations(results_gated)")

if 'results_revealed_at' not in columns:
    cursor.execute("ALTER TABLE validations ADD COLUMN results_revealed_at TEXT")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_results_revealed_at ON validations(results_revealed_at)")
```

**Impact:** Minor performance degradation if dashboard queries filter by gating status.

---

### 3.4 Potential Integer Overflow in Boolean Coercion
**Location:** `dashboard/database.py:276`

The boolean conversion in `update_reveal_status` uses truthy evaluation:
```python
cursor.execute(..., (1 if revealed else 0, revealed_at, job_id))
```

This is correct, but the `insert_validation` method uses `.get()` with default 0:
```python
validation_data.get("results_revealed", 0)
```

**Issue:** If `validation_data["results_revealed"]` is already an integer > 1, it won't be normalized to 1.

**Recommendation:** Normalize to 0/1:
```python
1 if validation_data.get("results_revealed", 0) else 0
```

**Impact:** Very low (data comes from parser which already uses 1/0), but defensive programming is better.

---

## 4. **Strengths**

### 4.1 Excellent Test Coverage for New Functionality
The implementation includes comprehensive tests for:
- `extract_reveal_event()` basic parsing (`test_log_parser.py:390-404`)
- `extract_completion()` with gating parameter (`test_log_parser.py:90-102`)
- Integration test verifying end-to-end parsing (`test_log_parser.py:420-461`)

All 39 tests pass, including security sanitization tests.

---

### 4.2 Proper Handling of Breaking Changes
The `extract_completion()` signature change from returning 2-tuple to 3-tuple was properly updated in all tests:
```python
# Old: job_id, timestamp = extract_completion(log_line)
# New: job_id, timestamp, gated = extract_completion(log_line)
```

This shows careful attention to backwards compatibility in tests.

---

### 4.3 Smart Partial Update Pattern
The `cron_parser.py` correctly distinguishes between full job records and reveal-only updates:
```python
if "created_at" not in job and "results_revealed" in job:
    # Partial update - only update reveal status
    db.update_reveal_status(...)
elif "created_at" in job:
    # Full job record - insert or replace
    db.insert_validation(job)
```

This enables efficient updates when reveal events occur long after job completion.

---

### 4.4 Defensive Database Migration
The schema migration gracefully handles race conditions:
```python
try:
    cursor.execute("ALTER TABLE validations ADD COLUMN results_revealed...")
except sqlite3.Error:
    pass  # Column might already exist (race condition)
```

---

### 4.5 Consistent Boolean Storage Convention
The code consistently uses integers (1/0) throughout for SQLite compatibility:
- `log_parser.py:360, 386` - Parse to 1/0
- `database.py:276` - Store as 1/0
- `test_log_parser.py:461` - Assert on truthy integer

---

## Verification Against Requirements

✅ **Update log_parser.py to parse REVEAL_EVENT lines** - Implemented in `extract_reveal_event()` (lines 189-214)

✅ **Extract job_id, outcome, and timestamp** - All three extracted correctly

✅ **Ensure data is merged into job record** - Merged in `parse_job_events()` (lines 373-387)

✅ **Verify ingestion pipeline saves to database** - Handled by `cron_parser.py` with `update_reveal_status()` method

✅ **Tests written and passing** - 39/39 tests pass including new reveal event tests

---

## Final Recommendation

**Approve with minor follow-up recommendations.**

The implementation is production-ready and fully addresses the requirements. The **Important** issues identified are low-risk but worth addressing:

1. Tighten the `job_id` regex pattern for consistency
2. Add warning logging when reveal updates affect 0 rows

The **Minor** issues are optional improvements that enhance robustness but aren't blockers.

**Code Quality:** Excellent - follows project patterns, comprehensive tests, proper error handling  
**Security:** Good - no vulnerabilities introduced, continues existing sanitization practices  
**Performance:** Good - proper indexing on primary query column, efficient partial updates  
**Testing:** Excellent - comprehensive coverage including integration tests
