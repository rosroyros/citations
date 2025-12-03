# User Identification and Tracking - Design Document

**Date:** 2025-12-03
**Issue:** citations-08wk (parent epic)
**Status:** Design Complete, Ready for Implementation

---

## Executive Summary

Add user identification to validation requests to enable user behavior analysis and journey tracking. This allows us to understand how users interact with the citation validator across multiple validations within their session.

**Key Goal:** Track user behavior patterns, especially for free tier users, to inform product decisions.

**Approach:** Generate persistent user IDs for all users (free and paid), send via headers, log in backend, parse into dashboard for analytics.

---

## 1. Problem Statement

### Current State

Today we can see:
- Total validation volume
- Free vs paid user counts (aggregate)
- Individual validation metrics (duration, tokens, errors)

Today we CANNOT see:
- "This user did 5 validations in one session"
- "User validated APA, then switched to MLA, then back to APA"
- "How many users convert from free to paid?"
- "What's the typical free user journey before upgrade?"

### Why This Matters

**Product Decisions:**
- Which citation styles are most popular with which user segments?
- Where do free users drop off in their journey?
- What validation patterns indicate upgrade intent?

**User Behavior Understanding:**
- Do users iterate on same citations (refining)?
- Do users validate multiple different citation sets?
- How long between validations for same user?

### Non-Goals (Explicit Scope Limits)

- ❌ Real-time user tracking (5-minute delay acceptable)
- ❌ Cross-device tracking (each device = separate user ID)
- ❌ User authentication/accounts
- ❌ Personally identifiable information (PII)
- ❌ Marketing analytics / conversion funnels (analytics only)
- ❌ Abuse detection / rate limiting (though data enables it later)

---

## 2. Design Overview

### High-Level Architecture

```
┌─────────────┐
│  Frontend   │ Generates UUID for free users
│  (React)    │ Stores in localStorage
└──────┬──────┘
       │ HTTP Headers:
       │ - X-User-Token (paid)
       │ - X-Free-User-ID (free)
       │ - X-Free-Used (free, existing)
       ▼
┌─────────────┐
│  Backend    │ Extracts user ID
│  (FastAPI)  │ Logs: paid_user_id or free_user_id
└──────┬──────┘
       │ Logs written to app.log
       ▼
┌─────────────┐
│  Dashboard  │ Parser extracts user IDs
│  Parser     │ Stores in SQLite
└──────┬──────┘
       │ Database with user_id columns
       ▼
┌─────────────┐
│  Dashboard  │ Display user IDs
│  UI         │ Filter by user, see journeys
└─────────────┘
```

### Key Design Decisions

**Decision 1: Separate Fields for Free vs Paid**
- **Rationale:** Avoids edge cases and confusion
- **Alternative considered:** Reuse `X-User-Token` for both (too many edge cases)
- **Trade-off:** Slightly more complexity, but cleaner separation of concerns

**Decision 2: localStorage + Headers (not cookies)**
- **Rationale:** Matches existing paid user pattern (`X-User-Token`)
- **Alternative considered:** Backend-set cookies (inconsistent with paid users)
- **Trade-off:** Requires frontend code, but consistent architecture

**Decision 3: Accept History Break on Free→Paid Conversion**
- **Rationale:** Most users convert early (< 5 validations), minimal data loss
- **Alternative considered:** Link old UUID to new token (complex, over-engineered)
- **Trade-off:** Can't track full journey across conversion, but simple implementation

**Decision 4: Base64 Encoding for Free User IDs**
- **Rationale:** Consistency (X-Free-Used already base64 encoded)
- **Alternative considered:** Plain UUID (inconsistent)
- **Trade-off:** Encoding/decoding overhead, but maintains consistency

**Decision 5: Dashboard Database Schema (Two Columns)**
- **Rationale:** Explicit schema, clear which ID belongs to which user type
- **Alternative considered:** Single column with prefix (harder to query/index)
- **Trade-off:** Two columns vs one, but better query performance and clarity

---

## 3. Detailed Design

### 3.1 Frontend Implementation

**File:** `frontend/frontend/src/utils/creditStorage.js`

**New Functions:**
```javascript
const FREE_USER_ID_KEY = 'citation_checker_free_user_id'

// Get existing free user ID from localStorage
export const getFreeUserId = () => {
  try {
    return localStorage.getItem(FREE_USER_ID_KEY)
  } catch (e) {
    console.error('Failed to get free user ID:', e)
    return null
  }
}

// Ensure user has a free user ID (generate if needed)
export const ensureFreeUserId = () => {
  let userId = getFreeUserId()
  if (!userId) {
    userId = crypto.randomUUID() // Browser-native UUID generation
    localStorage.setItem(FREE_USER_ID_KEY, userId)
  }
  return userId
}

// Clear free user ID (called when user upgrades to paid)
export const clearFreeUserId = () => {
  try {
    localStorage.removeItem(FREE_USER_ID_KEY)
  } catch (e) {
    console.error('Failed to clear free user ID:', e)
  }
}
```

**File:** `frontend/frontend/src/App.jsx`

**Update validation request:**
```javascript
const handleSubmit = async () => {
  const token = getToken()
  const headers = { 'Content-Type': 'application/json' }

  if (token) {
    // Paid user - send token only
    headers['X-User-Token'] = token
  } else {
    // Free user - send user ID and usage count
    const freeUserId = ensureFreeUserId()
    headers['X-Free-User-ID'] = btoa(freeUserId) // Base64 encode
    headers['X-Free-Used'] = btoa(String(getFreeUsage()))
  }

  // ... rest of validation logic
}
```

**File:** `frontend/frontend/src/pages/Success.jsx` (or wherever token is received)

**Update after receiving paid token:**
```javascript
// When user completes payment and receives token
const handlePaymentSuccess = (paidToken) => {
  clearFreeUserId() // Remove free user ID
  saveToken(paidToken) // Store paid token
  // ... rest of success handling
}
```

**localStorage Keys:**
- `citation_checker_user_id` → REMOVED (not used)
- `citation_checker_free_user_id` → NEW (free users only)
- `citation_checker_token` → EXISTING (paid users only)
- `citation_checker_free_used` → EXISTING (free users only)

**Header Summary:**
| User Type | X-User-Token | X-Free-User-ID | X-Free-Used |
|-----------|--------------|----------------|-------------|
| Paid      | ✓ (token)    | ✗              | ✗           |
| Free      | ✗            | ✓ (UUID)       | ✓ (count)   |
| Anonymous | ✗            | ✗              | ✗           |

---

### 3.2 Backend Implementation

**File:** `backend/app.py`

**New helper function:**
```python
def extract_user_id(request: Request) -> tuple[Optional[str], Optional[str], str]:
    """
    Extract user identification from request headers.

    This function determines user type and extracts the appropriate user ID
    for tracking and analytics purposes.

    Args:
        request: FastAPI Request object containing headers

    Returns:
        tuple: (paid_user_id, free_user_id, user_type)
            - paid_user_id: First 8 chars of token (for privacy) or None
            - free_user_id: Full UUID from header or None
            - user_type: 'paid' or 'free'

    Examples:
        Paid user: ('abc12345', None, 'paid')
        Free user: (None, '550e8400-e29b-41d4-a716-446655440000', 'free')
        Anonymous: (None, None, 'free')
    """
    # Check paid user first (takes precedence)
    token = request.headers.get('X-User-Token')
    if token:
        # Only log first 8 chars for privacy/security
        return token[:8], None, 'paid'

    # Check free user ID
    free_user_id_header = request.headers.get('X-Free-User-ID')
    if free_user_id_header:
        try:
            # Decode base64-encoded UUID
            decoded = base64.b64decode(free_user_id_header).decode('utf-8')
            return None, decoded, 'free'
        except Exception as e:
            # Invalid encoding - log warning but don't fail request
            logger.warning(f"Failed to decode X-Free-User-ID header: {e}")

    # Anonymous user (no ID yet, first validation)
    return None, None, 'free'
```

**Update validation endpoints:**

Both `/api/validate` (sync) and `/api/validate/async` need updates:

```python
@app.post("/api/validate/async")
async def validate_async(http_request: Request, request: ValidationRequest):
    """Validate citations asynchronously."""

    # Extract user identification (NEW)
    paid_user_id, free_user_id, user_type = extract_user_id(http_request)

    # Log validation request with user IDs (NEW)
    logger.info(
        f"Validation request - "
        f"user_type={user_type}, "
        f"paid_user_id={paid_user_id or 'N/A'}, "
        f"free_user_id={free_user_id or 'N/A'}, "
        f"style={request.style}"
    )

    # ... rest of existing validation logic
```

**Log Format Examples:**
```
# Paid user
2025-12-03 10:15:00 - citation_validator - INFO - Validation request - user_type=paid, paid_user_id=abc12345, free_user_id=N/A, style=apa7

# Free user
2025-12-03 10:16:00 - citation_validator - INFO - Validation request - user_type=free, paid_user_id=N/A, free_user_id=550e8400-e29b-41d4-a716-446655440000, style=apa7

# Anonymous (first validation before UUID generated)
2025-12-03 10:17:00 - citation_validator - INFO - Validation request - user_type=free, paid_user_id=N/A, free_user_id=N/A, style=apa7
```

**Integration with Existing Code:**
- `get_user_type()` in `gating.py` continues to work (doesn't depend on new headers)
- Credit enforcement unchanged (uses `X-User-Token` for paid, `X-Free-Used` for free)
- Webhook unchanged (generates token same way)

---

### 3.3 Dashboard Database Schema

**File:** `dashboard/database.py`

**Schema changes (migration needed):**
```sql
-- Add new columns to existing validations table
ALTER TABLE validations ADD COLUMN paid_user_id TEXT;
ALTER TABLE validations ADD COLUMN free_user_id TEXT;

-- Add indexes for query performance
CREATE INDEX idx_paid_user_id ON validations(paid_user_id);
CREATE INDEX idx_free_user_id ON validations(free_user_id);
```

**Updated schema (relevant fields):**
```sql
CREATE TABLE validations (
    job_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    user_type TEXT NOT NULL,         -- 'paid' or 'free' (existing)
    paid_user_id TEXT,                -- NEW: token[:8] for paid users
    free_user_id TEXT,                -- NEW: UUID for free users
    status TEXT NOT NULL,
    citation_count INTEGER,
    duration_seconds REAL,
    -- ... other existing columns
)
```

**Query patterns enabled:**
```sql
-- All validations for a specific paid user
SELECT * FROM validations
WHERE paid_user_id = 'abc12345'
ORDER BY created_at DESC;

-- All validations for a specific free user
SELECT * FROM validations
WHERE free_user_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY created_at DESC;

-- User journey (either type) - useful for seeing behavior over time
SELECT job_id, created_at, citation_count, status
FROM validations
WHERE paid_user_id = ? OR free_user_id = ?
ORDER BY created_at ASC;

-- Count distinct users by type
SELECT
  COUNT(DISTINCT paid_user_id) as paid_users,
  COUNT(DISTINCT free_user_id) as free_users
FROM validations
WHERE created_at >= date('now', '-7 days');
```

**Backward compatibility:**
- Old validations (before deployment) have `paid_user_id = NULL` and `free_user_id = NULL`
- Queries must handle NULL values gracefully
- Dashboard UI must display "unknown" or "N/A" for old records

---

### 3.4 Dashboard Parser Updates

**File:** `dashboard/log_parser.py`

**Add extraction logic:**
```python
# Pattern to match user ID logging
USER_ID_PATTERN = re.compile(
    r'user_type=(\w+), paid_user_id=([\w-]+|N/A), free_user_id=([\w-]+|N/A)'
)

def extract_user_ids(log_line: str) -> tuple[Optional[str], Optional[str]]:
    """
    Extract user IDs from validation request log line.

    Args:
        log_line: Log line containing user ID information

    Returns:
        tuple: (paid_user_id, free_user_id)
            Returns (None, None) if pattern not found
    """
    match = USER_ID_PATTERN.search(log_line)
    if match:
        user_type = match.group(1)
        paid_user_id = match.group(2) if match.group(2) != 'N/A' else None
        free_user_id = match.group(3) if match.group(3) != 'N/A' else None
        return paid_user_id, free_user_id
    return None, None

# In main parsing loop:
if "Validation request" in log_line:
    paid_user_id, free_user_id = extract_user_ids(log_line)
    job_data['paid_user_id'] = paid_user_id
    job_data['free_user_id'] = free_user_id
```

**Error handling:**
- If pattern doesn't match (old logs), set both IDs to None
- Log parser errors to `parser_errors` table for monitoring
- Continue processing (don't fail entire parse on one bad line)

---

### 3.5 Dashboard UI Updates

**File:** `dashboard/static/index.html` and `dashboard/static/app.js`

**Add User ID column to table:**
```html
<th>User ID</th>

<!-- Display logic in JavaScript -->
<td class="user-id">
  ${row.user_type === 'paid'
    ? (row.paid_user_id || 'unknown') + ' (paid)'
    : (row.free_user_id
        ? row.free_user_id.substring(0, 8) + '... (free)'
        : 'unknown'
      )
  }
</td>
```

**Add filter by user ID:**
```html
<input type="text" id="userIdFilter" placeholder="Search by user ID..." />
```

**Filter logic:**
```javascript
function filterByUserId(validations, searchTerm) {
  if (!searchTerm) return validations;

  const term = searchTerm.toLowerCase();
  return validations.filter(v => {
    const userId = v.paid_user_id || v.free_user_id || '';
    return userId.toLowerCase().includes(term);
  });
}
```

**Display examples:**
```
| User ID           | Type | Citations | Status |
|-------------------|------|-----------|--------|
| abc12345 (paid)   | paid | 5         | ✓      |
| 550e8400... (free)| free | 3         | ✓      |
| unknown           | free | 2         | ✓      |  ← old record
```

---

## 4. Edge Cases & Handling

### Edge Case 1: Free → Paid Conversion

**Scenario:** User starts as free, then buys credits.

**What happens:**
1. Free user has `550e8400-...` stored in localStorage
2. User validates 3 times → dashboard shows 3 validations with `free_user_id=550e8400-...`
3. User buys credits → receives token `paid-abc-xyz`
4. Frontend stores token, clears `free_user_id`
5. Next validation → sends `X-User-Token=paid-abc-xyz`
6. Dashboard shows new validations with `paid_user_id=paid-abc`

**Result:** Looks like two different users in dashboard.

**Handling:** Accept the break. Document as known limitation. Most users convert within first 5 validations, so minimal history loss.

**Future enhancement (NOT in scope):** Link old `free_user_id` to new `paid_user_id` via conversion tracking table.

---

### Edge Case 2: Anonymous First Validation

**Scenario:** User's first validation request before UUID is generated.

**What happens:**
1. User lands on site, immediately pastes citations and submits
2. `ensureFreeUserId()` generates UUID synchronously before request
3. Request includes `X-Free-User-ID`

**Result:** Should not occur (UUID generated before request sent).

**Fallback:** If somehow occurs, backend logs `paid_user_id=N/A, free_user_id=N/A`, marked as anonymous.

---

### Edge Case 3: Invalid Base64 in Header

**Scenario:** Corrupted or malicious `X-Free-User-ID` header.

**Handling:**
```python
try:
    decoded = base64.b64decode(free_user_id_header).decode('utf-8')
    return None, decoded, 'free'
except Exception as e:
    logger.warning(f"Failed to decode X-Free-User-ID header: {e}")
    return None, None, 'free'  # Treat as anonymous
```

**Result:** Validation proceeds, logged as anonymous free user.

---

### Edge Case 4: User Clears localStorage

**Scenario:** User clears browser data or uses incognito.

**What happens:**
1. Previous validations have `free_user_id=550e8400-...`
2. User clears localStorage
3. Next validation generates new UUID `abc-def-123`
4. Dashboard shows two different users

**Handling:** Accept limitation. Can't prevent localStorage clearing. This is inherent to client-side storage.

---

### Edge Case 5: Multiple Browsers/Devices

**Scenario:** User validates on laptop, then on phone.

**What happens:**
1. Laptop generates `UUID-A`
2. Phone generates `UUID-B`
3. Dashboard sees two users

**Handling:** Accept limitation. Document as "device/browser sessions, not unique users." This is expected behavior for localStorage-based tracking.

---

### Edge Case 6: Old Logs (Before Deployment)

**Scenario:** Parser processes logs from before user ID logging was added.

**What happens:**
1. Parser regex doesn't match (no user ID fields in log)
2. `extract_user_ids()` returns `(None, None)`
3. Database stores `NULL` for both `paid_user_id` and `free_user_id`
4. Dashboard UI shows "unknown"

**Handling:** Graceful degradation. Old records simply don't have user IDs.

---

## 5. Testing Strategy

### 5.1 Unit Tests (Backend)

**File:** `backend/tests/test_user_identification.py` (NEW)

```python
def test_extract_user_id_paid():
    """Test extraction of paid user ID from X-User-Token header."""
    # Mock request with X-User-Token
    # Assert returns (token[:8], None, 'paid')

def test_extract_user_id_free():
    """Test extraction of free user ID from X-Free-User-ID header."""
    # Mock request with base64-encoded UUID
    # Assert returns (None, decoded_uuid, 'free')

def test_extract_user_id_invalid_base64():
    """Test handling of invalid base64 in X-Free-User-ID."""
    # Mock request with invalid base64
    # Assert returns (None, None, 'free') and logs warning

def test_extract_user_id_anonymous():
    """Test handling of request with no user ID headers."""
    # Mock request with no headers
    # Assert returns (None, None, 'free')

def test_paid_user_precedence():
    """Test that X-User-Token takes precedence over X-Free-User-ID."""
    # Mock request with BOTH headers (shouldn't happen, but test it)
    # Assert returns paid user ID, ignores free user ID
```

---

### 5.2 Integration Tests (Backend)

**Update existing test files:**

14 test files currently send `X-User-Token` or `X-Free-Used` headers:
- `test_async_jobs.py`
- `test_credit_enforcement.py`
- `test_async_jobs_integration.py`
- `test_free_tier.py`
- ... others

**Required changes:**
1. Verify tests still pass (headers unchanged)
2. Add assertions to check logs include user IDs:
   ```python
   # After validation request
   assert "paid_user_id=test-tok" in captured_logs
   # OR
   assert "free_user_id=" in captured_logs
   ```

**New integration tests:**
```python
def test_free_user_validation_logs_user_id():
    """Test that free user validation includes free_user_id in logs."""
    # Send validation with X-Free-User-ID header
    # Check logs contain "free_user_id=<uuid>"

def test_paid_user_validation_logs_user_id():
    """Test that paid user validation includes paid_user_id in logs."""
    # Send validation with X-User-Token header
    # Check logs contain "paid_user_id=<token[:8]>"
```

---

### 5.3 Unit Tests (Frontend)

**File:** `frontend/frontend/src/utils/creditStorage.test.js` (UPDATE)

```javascript
describe('Free User ID Management', () => {
  test('ensureFreeUserId generates UUID on first call', () => {
    // Clear localStorage
    // Call ensureFreeUserId()
    // Assert UUID returned and stored in localStorage
  });

  test('ensureFreeUserId returns same UUID on subsequent calls', () => {
    // Generate UUID
    // Call ensureFreeUserId() twice
    // Assert both calls return same UUID
  });

  test('clearFreeUserId removes UUID from localStorage', () => {
    // Generate UUID
    // Call clearFreeUserId()
    // Assert localStorage no longer has free_user_id
  });

  test('getFreeUserId returns null when not set', () => {
    // Clear localStorage
    // Call getFreeUserId()
    // Assert returns null
  });
});
```

---

### 5.4 E2E Tests (Frontend)

**File:** `frontend/frontend/tests/user-tracking.spec.js` (NEW)

```javascript
test('Free user validation sends X-Free-User-ID header', async ({ page }) => {
  // Intercept network request
  // Validate on site (as free user)
  // Assert request includes X-Free-User-ID header (base64 encoded)
  // Assert request includes X-Free-Used header
});

test('Paid user validation sends X-User-Token header only', async ({ page }) => {
  // Set token in localStorage
  // Validate on site (as paid user)
  // Assert request includes X-User-Token header
  // Assert request does NOT include X-Free-User-ID header
});

test('Free user ID persists across page refresh', async ({ page }) => {
  // Validate as free user
  // Get UUID from localStorage
  // Refresh page
  // Validate again
  // Assert same UUID used
});

test('Converting to paid clears free user ID', async ({ page }) => {
  // Validate as free user (generates UUID)
  // Simulate payment success (receive token)
  // Assert free_user_id removed from localStorage
  // Assert token stored in localStorage
  // Next validation sends X-User-Token, not X-Free-User-ID
});
```

---

### 5.5 Dashboard Tests

**File:** `dashboard/test_log_parser.py` (UPDATE)

```python
def test_extract_user_ids_paid():
    """Test extraction of paid user ID from log line."""
    log_line = "2025-12-03 10:15:00 - citation_validator - INFO - Validation request - user_type=paid, paid_user_id=abc12345, free_user_id=N/A, style=apa7"
    paid_id, free_id = extract_user_ids(log_line)
    assert paid_id == 'abc12345'
    assert free_id is None

def test_extract_user_ids_free():
    """Test extraction of free user ID from log line."""
    log_line = "2025-12-03 10:16:00 - citation_validator - INFO - Validation request - user_type=free, paid_user_id=N/A, free_user_id=550e8400-e29b-41d4-a716-446655440000, style=apa7"
    paid_id, free_id = extract_user_ids(log_line)
    assert paid_id is None
    assert free_id == '550e8400-e29b-41d4-a716-446655440000'

def test_extract_user_ids_old_log():
    """Test handling of old log line without user IDs."""
    log_line = "2025-12-01 10:00:00 - citation_validator - INFO - Validation request for apa7"
    paid_id, free_id = extract_user_ids(log_line)
    assert paid_id is None
    assert free_id is None
```

**File:** `dashboard/test_database.py` (UPDATE)

```python
def test_insert_validation_with_paid_user_id():
    """Test inserting validation with paid user ID."""
    # Create validation data with paid_user_id
    # Insert into database
    # Query and verify paid_user_id stored correctly

def test_insert_validation_with_free_user_id():
    """Test inserting validation with free user ID."""
    # Create validation data with free_user_id
    # Insert into database
    # Query and verify free_user_id stored correctly

def test_query_by_paid_user_id():
    """Test querying validations by paid user ID."""
    # Insert multiple validations for same paid user
    # Query by paid_user_id
    # Assert returns correct validations

def test_query_by_free_user_id():
    """Test querying validations by free user ID."""
    # Insert multiple validations for same free user
    # Query by free_user_id
    # Assert returns correct validations
```

---

## 6. Database Migration

### 6.1 Migration Script

**File:** `dashboard/migrations/add_user_id_columns.py` (NEW)

```python
#!/usr/bin/env python3
"""
Database migration: Add user ID columns to validations table.

Purpose: Add paid_user_id and free_user_id columns to existing validations table
         to support user tracking and journey analysis.

When to run: BEFORE deploying code changes that log user IDs.
             Run directly on VPS at /opt/citations/dashboard/

Safety: Idempotent (checks if columns exist before adding).
        Non-destructive (only adds columns, doesn't modify data).
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = '/opt/citations/dashboard/data/validations.db'

def check_column_exists(cursor, table, column):
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns

def migrate():
    """Add user ID columns to validations table."""

    # Check if database exists
    if not Path(DB_PATH).exists():
        print(f"❌ Database not found at {DB_PATH}")
        print("   Dashboard must be deployed first.")
        return False

    print(f"📂 Opening database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check and add paid_user_id column
        if check_column_exists(cursor, 'validations', 'paid_user_id'):
            print("✓ paid_user_id column already exists")
        else:
            print("➕ Adding paid_user_id column...")
            cursor.execute("ALTER TABLE validations ADD COLUMN paid_user_id TEXT")
            print("✓ Added paid_user_id column")

        # Check and add free_user_id column
        if check_column_exists(cursor, 'validations', 'free_user_id'):
            print("✓ free_user_id column already exists")
        else:
            print("➕ Adding free_user_id column...")
            cursor.execute("ALTER TABLE validations ADD COLUMN free_user_id TEXT")
            print("✓ Added free_user_id column")

        # Add indexes for performance
        print("➕ Adding indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_paid_user_id
            ON validations(paid_user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_free_user_id
            ON validations(free_user_id)
        """)
        print("✓ Added indexes")

        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")

        # Verify migration
        print("\n📊 Verification:")
        cursor.execute("PRAGMA table_info(validations)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"   Columns in validations table: {len(columns)}")
        print(f"   - paid_user_id present: {('paid_user_id' in columns)}")
        print(f"   - free_user_id present: {('free_user_id' in columns)}")

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("User ID Columns Migration")
    print("=" * 60)
    print()

    success = migrate()
    sys.exit(0 if success else 1)
```

**How to run (on VPS):**
```bash
ssh deploy@178.156.161.140
cd /opt/citations/dashboard/migrations
python3 add_user_id_columns.py
```

**Expected output:**
```
============================================================
User ID Columns Migration
============================================================

📂 Opening database: /opt/citations/dashboard/data/validations.db
➕ Adding paid_user_id column...
✓ Added paid_user_id column
➕ Adding free_user_id column...
✓ Added free_user_id column
➕ Adding indexes...
✓ Added indexes

✅ Migration completed successfully!

📊 Verification:
   Columns in validations table: 13
   - paid_user_id present: True
   - free_user_id present: True
```

---

### 6.2 Rollback Plan

**If migration fails or needs reversal:**

SQLite doesn't support `DROP COLUMN`, so rollback requires:
1. Restore from backup (created before migration)
2. Or recreate table without columns (destructive)

**Backup before migration (recommended):**
```bash
cp /opt/citations/dashboard/data/validations.db \
   /opt/citations/dashboard/data/validations.db.backup-$(date +%Y%m%d)
```

**Rollback command:**
```bash
mv /opt/citations/dashboard/data/validations.db.backup-20251203 \
   /opt/citations/dashboard/data/validations.db
```

---

## 7. Deployment Plan

### 7.1 Pre-Deployment Checklist

**On local machine:**
- [ ] All tests pass (`pytest backend/tests/`)
- [ ] Frontend builds (`npm run build`)
- [ ] Frontend tests pass (`npm test`)
- [ ] Migration script tested on local copy of prod database
- [ ] Code reviewed (use `/oracle-review`)

**On VPS (before deploying code):**
- [ ] SSH to VPS: `ssh deploy@178.156.161.140`
- [ ] Backup dashboard database
- [ ] Run migration script
- [ ] Verify migration successful
- [ ] Check dashboard still works (UI accessible)

---

### 7.2 Deployment Steps

**1. Backup Production Database**
```bash
cd /opt/citations/dashboard/data
cp validations.db validations.db.backup-$(date +%Y%m%d-%H%M)
ls -lh validations.db*
```

**2. Run Migration**
```bash
cd /opt/citations/dashboard/migrations
python3 add_user_id_columns.py
# Verify success (should see "✅ Migration completed successfully!")
```

**3. Test Dashboard Still Works**
```bash
# Access dashboard UI
curl -I http://178.156.161.140:4646
# Should return 200 OK
```

**4. Deploy Code Changes**
```bash
cd /opt/citations
git pull origin main
./deployment/scripts/deploy.sh
```

**5. Verify Deployment**
```bash
# Check backend logs show user IDs
tail -f /opt/citations/backend/logs/app.log | grep "user_type="

# Should see lines like:
# user_type=free, paid_user_id=N/A, free_user_id=550e8400-...
# user_type=paid, paid_user_id=abc12345, free_user_id=N/A
```

---

### 7.3 Post-Deployment Verification

**Immediate checks (5 minutes after deployment):**
- [ ] Backend service running: `systemctl status citations-backend`
- [ ] Frontend accessible: Visit https://citationformatchecker.com
- [ ] Logs show user IDs: `grep "paid_user_id" /opt/citations/backend/logs/app.log`
- [ ] No errors in logs: `grep "ERROR" /opt/citations/backend/logs/app.log | tail -20`

**Within 10 minutes (wait for parser cron):**
- [ ] Dashboard parser runs without errors
- [ ] Dashboard shows user IDs in table (new validations only)
- [ ] Can filter by user ID in dashboard

**Within 1 hour (functional testing):**
- [ ] Create free user validation → check logs show `free_user_id`
- [ ] Create paid user validation → check logs show `paid_user_id`
- [ ] Check dashboard displays both user types correctly
- [ ] Verify localStorage contains `citation_checker_free_user_id` for free users

---

### 7.4 Rollback Procedure

**If deployment fails:**

1. **Restore database backup:**
```bash
cd /opt/citations/dashboard/data
cp validations.db.backup-YYYYMMDD-HHMM validations.db
```

2. **Revert code:**
```bash
cd /opt/citations
git log --oneline -5  # Find commit before deployment
git revert <commit-sha>
./deployment/scripts/deploy.sh
```

3. **Verify rollback:**
- Check backend logs (no user ID logging)
- Check dashboard (works without user ID columns)
- Verify service stable

---

## 8. Success Criteria

### 8.1 Technical Success

**Backend:**
- ✅ All validations log user IDs (paid or free)
- ✅ No errors decoding `X-Free-User-ID` headers
- ✅ `extract_user_id()` unit tests pass
- ✅ Integration tests updated and passing

**Frontend:**
- ✅ Free users generate UUID on first validation
- ✅ UUID persists across page refreshes
- ✅ Paid users don't send `X-Free-User-ID`
- ✅ Free→paid conversion clears `free_user_id`

**Dashboard:**
- ✅ Parser extracts user IDs from logs
- ✅ Database stores user IDs correctly
- ✅ UI displays user IDs in table
- ✅ Can filter by user ID
- ✅ Old records show "unknown" gracefully

---

### 8.2 Business Success

**Analytics enabled:**
- ✅ Can see user journeys (multiple validations from same user)
- ✅ Can count distinct users (not just validation volume)
- ✅ Can analyze free user behavior patterns
- ✅ Can track paid user usage over time

**Queries possible:**
```sql
-- How many users validated multiple times?
SELECT COUNT(*) as repeat_users
FROM (
  SELECT free_user_id, COUNT(*) as validation_count
  FROM validations
  WHERE free_user_id IS NOT NULL
  GROUP BY free_user_id
  HAVING COUNT(*) > 1
);

-- What's the average validations per user?
SELECT AVG(validation_count) as avg_validations_per_user
FROM (
  SELECT free_user_id, COUNT(*) as validation_count
  FROM validations
  WHERE free_user_id IS NOT NULL
  GROUP BY free_user_id
);

-- Which users are power users (> 5 validations)?
SELECT free_user_id, COUNT(*) as validation_count
FROM validations
WHERE free_user_id IS NOT NULL
GROUP BY free_user_id
HAVING COUNT(*) > 5
ORDER BY validation_count DESC;
```

---

## 9. Known Limitations

1. **Free→Paid Conversion:** History breaks when user upgrades. Accept this limitation.

2. **Cross-Device Tracking:** Each device/browser gets unique ID. Can't link them.

3. **localStorage Clearing:** If user clears data, gets new ID. Looks like new user.

4. **Anonymous First Validations:** Rare edge case where UUID not generated. Logged as anonymous.

5. **Old Logs:** Pre-deployment validations have no user IDs. Show as "unknown."

6. **Privacy Trade-off:** Paid user IDs are only 8 chars (token[:8]), so multiple users could collide if tokens share prefix. Acceptable risk for analytics.

---

## 10. Future Enhancements (Out of Scope)

**Phase 2 considerations (not in current design):**

1. **Conversion Tracking:** Link `free_user_id` to `paid_user_id` when user upgrades
   - Requires: Conversion tracking table, webhook update, frontend tracking

2. **User Cohort Analysis:** Group users by signup date, analyze retention
   - Requires: User creation timestamp

3. **Session Duration Tracking:** How long users spend on site
   - Requires: Additional event logging (page views, time on page)

4. **Geographic Analysis:** Where are users located?
   - Requires: IP address logging (privacy concerns, GDPR implications)

5. **Abuse Detection:** Flag users with suspicious patterns
   - Requires: Rate limiting logic, automated alerting

6. **Real-time Dashboard:** Live updates instead of 5-minute delay
   - Requires: WebSocket connection, streaming log parser

---

## 11. References

**Related Issues:**
- `citations-08wk` - Add user IP and identifier logging (this design)
- `citations-xyov` - Build internal operational dashboard (parent)
- `citations-6b51` - Persist full validation results (Phase 2)
- `citations-wekx` - Add credits before/after logging (Phase 2)

**Design Documents:**
- `docs/plans/2025-11-27-dashboard-design.md` - Original dashboard design
- `docs/plans/2025-11-27-gated-validation-results-design.md` - Gating system

**Code References:**
- `backend/gating.py` - User type detection logic
- `backend/app.py` - Validation endpoints
- `dashboard/log_parser.py` - Log parsing logic
- `dashboard/database.py` - Database schema and queries

---

## Appendix A: Discussion Summary

**Key decisions from brainstorming session (2025-12-03):**

1. **Goal clarification:** User behavior analysis, not abuse detection
2. **Session vs user ID:** Use "user_id" terminology (not "session")
3. **Separate fields:** `X-User-Token` (paid) vs `X-Free-User-ID` (free)
4. **Accept conversion break:** Simple implementation over perfect tracking
5. **No IP address:** Not needed for behavior analysis, adds complexity
6. **Base64 encoding:** Consistency with existing `X-Free-Used` header
7. **Database schema:** Two columns (paid_user_id, free_user_id) for clarity

**Edge cases considered:**
- Free→paid conversion (accept break)
- Anonymous first validation (rare, handle gracefully)
- Invalid base64 (log warning, continue)
- localStorage clearing (can't prevent)
- Multiple devices (expected behavior)
- Old logs (backward compatibility)

---

**End of Design Document**
