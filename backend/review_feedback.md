# Code Review: citations-5gwi (Pass Management Database Functions)

## Summary
The implementation successfully addresses all key requirements. Critical features like concurrency control (using `BEGIN IMMEDIATE`), idempotency (checking `orders` table), and pass extension logic are implemented correctly and verified with smoke tests.

## Evaluation

### Strengths
- **Concurrency Control:** Correctly uses `BEGIN IMMEDIATE` to prevent race conditions in usage tracking and pass granting.
- **Idempotency:** Robust check against the persistent `orders` table prevents double-processing of webhooks.
- **Pass Logic:** Extension logic correctly adds time to existing passes rather than overwriting them.
- **Security:** Consistently uses parameterized queries, preventing SQL injection.
- **Schema:** `init_db` correctly handles schema updates (adding columns) and new table creation.

### Minor Issues (Non-Blocking)

1.  **Resource Cleanup Pattern** (`backend/database.py`):
    - Functions like `try_increment_daily_usage` and `add_pass` manually call `conn.close()`. While currently correct in the happy/exception paths implemented, it's less robust than using a context manager.
    - *Suggestion:* Consider `with contextlib.closing(sqlite3.connect(db_path)) as conn:` to ensure closure even if unexpected errors occur before the `try/except` blocks (e.g. inside `get_next_utc_midnight` if moved).

2.  **Error Handling Consistency** (`backend/database.py`):
    - `add_pass` raises exceptions on DB errors, whereas existing functions like `add_credits` catch errors and return `False`.
    - *Note:* This is acceptable (500 error on DB failure is standard), but be aware of the difference in calling conventions.

3.  **Hours Calculation** (`get_active_pass`):
    - `hours_remaining = (row[0] - now) // 3600` uses floor division.
    - *Impact:* 59 minutes remaining will show as `0` hours.
    - *Suggestion:* Consider if the UI expects this, or if `math.ceil` or returning minutes would be better for the frontend.

4.  **Schema Migration**:
    - The `ALTER TABLE` operations in `init_db` are good for now but might slow down startup as the `orders` table grows (checking for column existence). For a larger system, a dedicated migration tool (like Alembic) or versioned schema tracking would be better.

## Verdict
**APPROVED**. The implementation is solid and meets the P1 requirements. The minor issues do not block merging.
