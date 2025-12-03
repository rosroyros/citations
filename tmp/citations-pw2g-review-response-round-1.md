Perfect! Now I have all the information I need. Let me provide my structured code review:

---

## Code Review: REVEAL_EVENT Implementation (citations-pw2g)

### Overview
Implementation adds support for parsing "click to reveal" events from backend logs and storing them in the dashboard database. Changes span database schema, log parser, and cron ingestion logic.

---

## 1. **Critical Issues**

### ❌ **CRITICAL: Breaking Change in `extract_completion()` - Test Failure**
**Location:** `dashboard/log_parser.py:60-86`

**Issue:** The `extract_completion()` function signature changed from returning 2 values to 3 values:
```python
# Old signature (expected by tests)
return job_id, timestamp

# New signature (actual implementation)  
return job_id, timestamp, gated  # Line 84
```

**Impact:** 
- Test `test_extract_completion_valid` is failing (line 84 in test_log_parser.py expects 2 values)
- Any external code calling this function will break

**Evidence:**
```
dashboard/test_log_parser.py::TestLogParser::test_extract_completion_valid FAILED
ValueError: too many values to unpack (expected 2)
```

**Fix Required:**
```python
# Update test to handle the new return value:
def test_extract_completion_valid(self):
    log_line = "..."
    job_id, timestamp, gated = extract_completion(log_line)  # Add 'gated'
    self.assertEqual(gated, None)  # Verify default case
```

---

### ⚠️ **IMPORTANT: Missing Test Coverage for REVEAL_EVENT Parsing**
**Location:** `dashboard/test_log_parser.py`

**Issue:** No tests exist for the new `extract_reveal_event()` function or REVEAL_EVENT integration.

**What's Missing:**
1. Unit test for `extract_reveal_event()` function
2. Integration test showing REVEAL_EVENT data flows through parse_logs()
3. Test for partial job updates (reveal-only events)
4. Test for gating status extraction from completion logs

**Required Tests:**
```python
def test_extract_reveal_event_valid(self):
    line = "2025-12-02 15:30:00 - app - INFO - REVEAL_EVENT: job_id=abc-123 outcome=revealed"
    result = extract_reveal_event(line)
    self.assertIsNotNone(result)
    job_id, timestamp, outcome = result
    self.assertEqual(job_id, "abc-123")
    self.assertEqual(outcome, "revealed")

def test_parse_logs_with_reveal_event(self):
    # Test that reveal events create/update job records correctly
    ...
```

---

### ⚠️ **IMPORTANT: Partial Job Creation Logic Risk**
**Location:** `dashboard/log_parser.py:376-386`

**Issue:** When a REVEAL_EVENT is seen without prior job creation, the parser creates a partial job record with missing required fields:

```python
if job_id not in jobs:
    jobs[job_id] = {
        "job_id": job_id,
        # We don't have creation time, so we can't fill it yet
        # The ingester will need to handle this partial record
    }
```

**Problem:** 
- The comment says "The ingester will need to handle this" but there's no guarantee
- `created_at` is marked `NOT NULL` in the database schema (database.py:48)
- `user_type` is marked `NOT NULL` in the database schema (database.py:55)
- If `cron_parser.py` line 84-86 doesn't catch this case, the database insert will fail

**Current Mitigation:** 
Lines 76-89 in `cron_parser.py` do handle this with the partial update logic, but this creates tight coupling and fragility.

**Better Approach:**
```python
# In log_parser.py - Don't create incomplete records
if job_id not in jobs:
    # Log warning about orphaned reveal event
    logger.warning(f"REVEAL_EVENT for unknown job {job_id}, skipping")
    continue  # Skip this reveal event
```

Or update `_finalize_job_data()` to filter out incomplete records before returning.

---

## 2. **Important Issues (Should Fix Before Merge)**

### Database Migration Not Documented
**Location:** `dashboard/database.py:92-110`

**Issue:** Column additions (`results_revealed`, `results_revealed_at`, `results_gated`) use `ALTER TABLE` with silent failure handling:

```python
try:
    cursor.execute("ALTER TABLE validations ADD COLUMN results_revealed INTEGER DEFAULT 0")
except sqlite3.Error:
    pass  # Column might already exist (race condition)
```

**Problems:**
1. Silent failures hide actual errors (not just "column exists")
2. No migration documentation or version tracking
3. Production database migration not mentioned in commit message

**Recommendation:**
- Document the schema change in commit message or migration notes
- Add logging instead of silent `pass`:
```python
except sqlite3.OperationalError as e:
    if "duplicate column name" not in str(e).lower():
        logger.warning(f"Could not add column results_revealed: {e}")
```

---

### Inconsistent Boolean Storage
**Location:** `dashboard/log_parser.py:385`, `dashboard/database.py:204-206`

**Issue:** Boolean values stored inconsistently:
- Line 385 in log_parser.py stores Python bool: `jobs[job_id]["results_revealed"] = (outcome == "revealed")`
- Line 204-256 in database.py expects int: `validation_data.get("results_revealed", 0)`
- Line 581-583 in log_parser.py defaults to int: `job.setdefault("results_revealed", 0)`

**Risk:** Type confusion could cause bugs. Python's bool is subclass of int, so this works, but it's implicit.

**Recommendation:** Be explicit about conversion in one place:
```python
jobs[job_id]["results_revealed"] = 1 if outcome == "revealed" else 0
```

---

### REVEAL_EVENT Regex Pattern May Be Too Restrictive
**Location:** `dashboard/log_parser.py:200`

**Issue:** Pattern only matches alphanumeric + hyphen + underscore in job_id:
```python
reveal_pattern = r'REVEAL_EVENT: job_id=([a-f0-9-_]+) outcome=(\w+)'
```

**Problem:** If backend changes job_id format (e.g., includes dots, colons), parser will silently fail.

**Recommendation:** Match the same pattern used in `extract_creation` and `extract_completion`:
```python
reveal_pattern = r'REVEAL_EVENT: job_id=([a-f0-9-]+) outcome=(\w+)'  # Current
# Should be:
reveal_pattern = r'REVEAL_EVENT: job_id=(\S+) outcome=(\w+)'  # More flexible
```

---

## 3. **Minor Issues (Nice to Have)**

### Missing Input Validation in extract_reveal_event
**Location:** `dashboard/log_parser.py:189-213`

**Issue:** No validation of `outcome` value. Should it only be "revealed" or "not_revealed"?

**Recommendation:**
```python
if match:
    job_id = match.group(1)
    outcome = match.group(2)
    
    # Validate outcome
    if outcome not in ("revealed", "not_revealed"):
        logger.warning(f"Unexpected reveal outcome: {outcome}")
        return None
```

---

### update_reveal_status Could Be Safer
**Location:** `dashboard/database.py:261-277`

**Issue:** Method silently succeeds even if job_id doesn't exist (UPDATE affects 0 rows).

**Recommendation:**
```python
cursor.execute("""
    UPDATE validations
    SET results_revealed = ?, results_revealed_at = ?
    WHERE job_id = ?
""", (1 if revealed else 0, revealed_at, job_id))

if cursor.rowcount == 0:
    logger.warning(f"update_reveal_status: job_id {job_id} not found")

self.conn.commit()
```

---

### Test for Gating Status from Completion Log
**Location:** `dashboard/log_parser.py:72`

**Issue:** The regex captures optional gating parameter but no test verifies it:
```python
completion_pattern = r'Job ([a-f0-9-]+): Completed successfully(?: with gating=(True|False))?'
```

**Missing Test:**
```python
def test_extract_completion_with_gating_true(self):
    line = "2025-12-02 15:30:00 - app - INFO - Job abc-123: Completed successfully with gating=True"
    job_id, timestamp, gated = extract_completion(line)
    self.assertTrue(gated)

def test_extract_completion_with_gating_false(self):
    line = "2025-12-02 15:30:00 - app - INFO - Job abc-123: Completed successfully with gating=False"
    job_id, timestamp, gated = extract_completion(line)
    self.assertFalse(gated)
```

---

## 4. **Strengths**

✅ **Good Architecture:** Three-phase parsing (events → metrics → citations) is well-designed and maintainable

✅ **Proper Separation:** Database migration logic correctly placed in `_create_schema()` with existing pattern

✅ **Backward Compatibility:** Database code handles both old (`validation_status`) and new (`status`) column names elegantly

✅ **Partial Update Pattern:** `cron_parser.py` correctly distinguishes between full job records and reveal-only updates (lines 76-89)

✅ **Default Values:** `_finalize_job_data()` properly initializes all new fields with safe defaults (lines 581-583)

✅ **Type Conversion:** Datetime objects properly converted to ISO format strings (line 590-591)

---

## Summary

| Category | Count | Status |
|----------|-------|--------|
| **Critical** | 1 | ❌ Must fix (breaking test) |
| **Important** | 4 | ⚠️ Should fix before merge |
| **Minor** | 3 | ✅ Nice to have |
| **Strengths** | 6 | ✅ Well done |

---

## Recommendations

### Before Merge:
1. ✅ **Fix breaking test** - Update `test_extract_completion_valid` to handle 3 return values
2. ✅ **Add REVEAL_EVENT tests** - Minimum 4 tests for new functionality
3. ✅ **Handle orphaned reveal events** - Either filter them out or document the dependency on cron_parser
4. ⚠️ **Document schema change** - Add migration notes

### Consider for Follow-up:
- Add validation for `outcome` values in extract_reveal_event
- Add logging in database schema migration error handling
- Make job_id regex pattern more flexible
- Add rowcount check in update_reveal_status

---

## Verification Checklist

- [ ] All existing tests passing
- [ ] New tests added for REVEAL_EVENT parsing
- [ ] Schema migration documented
- [ ] Partial job record handling verified
- [ ] Integration test with real REVEAL_EVENT log line
