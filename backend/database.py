import sqlite3
import os
import logging
import time
from pathlib import Path
from typing import Optional
from pricing_config import get_next_utc_midnight

# Use the same logger name as app.py to ensure logs go to the same file/format
logger = logging.getLogger("citation_validator")

def get_db_path() -> str:
    """Get database path, using test override if set."""
    # Check for test environment variable
    test_path = os.getenv('TEST_DB_PATH')
    if test_path:
        return test_path

    # Production path
    return os.path.join(os.path.dirname(__file__), 'credits.db')

def init_db():
    """
    Initialize the SQLite database with the required schema.
    Creates the database file and tables if they don't exist.
    """
    try:
        db_path = get_db_path()

        # Ensure the directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Created database directory: {db_dir}")

        # Connect to database (creates file if it doesn't exist)
        logger.info(f"Initializing database at: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")

        # Create users table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                token TEXT PRIMARY KEY,
                credits INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create orders table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                token TEXT NOT NULL,
                credits_granted INTEGER NOT NULL,
                pass_days INTEGER,
                pass_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (token) REFERENCES users(token)
            )
        ''')

        # Add pass columns to orders table if they don't exist
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN pass_days INTEGER")
            logger.info("Added pass_days column to orders table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                pass  # Column already exists
            else:
                raise

        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN pass_type TEXT")
            logger.info("Added pass_type column to orders table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                pass  # Column already exists
            else:
                raise

        # Create user_passes table for time-based access
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_passes (
                token TEXT PRIMARY KEY,
                expiration_timestamp INTEGER NOT NULL,
                pass_type TEXT NOT NULL,
                purchase_date INTEGER NOT NULL,
                order_id TEXT UNIQUE NOT NULL
            )
        ''')

        # Create index for efficient expiration checks
        conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_passes_expiration
            ON user_passes(token, expiration_timestamp)
        ''')

        # Create daily_usage table for tracking citations per day
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_usage (
                token TEXT NOT NULL,
                reset_timestamp INTEGER NOT NULL,
                citations_count INTEGER DEFAULT 0,
                PRIMARY KEY (token, reset_timestamp)
            )
        ''')

        # Create UPGRADE_EVENT table for E2E testing
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS UPGRADE_EVENT (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                event_type TEXT,
                timestamp INTEGER,
                experiment_variant TEXT,
                product_id TEXT,
                amount_cents INTEGER,
                metadata TEXT
            )
        ''')

        # Commit changes
        conn.commit()
        conn.close()

        logger.info("Database initialized successfully")

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error initializing database: {e}")
        raise


def get_credits(token: str) -> int:
    """
    Returns the credit balance for a given token.
    Returns 0 if the token doesn't exist.

    Args:
        token: User token to look up

    Returns:
        int: Number of credits the user has
    """
    try:
        db_path = get_db_path()
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA busy_timeout=5000")
            cursor = conn.cursor()

            cursor.execute("SELECT credits FROM users WHERE token = ?", (token,))
            result = cursor.fetchone()

            if result:
                credits = result[0]
                logger.debug(f"Retrieved {credits} credits for token {token[:8]}...")
                return credits
            else:
                logger.debug(f"No user found for token {token[:8]}..., returning 0")
                return 0

    except sqlite3.Error as e:
        logger.error(f"Database error getting credits: {e}")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error getting credits: {e}")
        return 0


def add_credits(token: str, amount: int, order_id: str) -> bool:
    """
    Adds credits to a user's account. Creates user if doesn't exist.
    Records the order_id to ensure idempotency.

    Args:
        token: User token
        amount: Number of credits to add
        order_id: Unique order ID from payment processor

    Returns:
        bool: True if credits were added, False if order_id already exists
    """
    try:
        db_path = get_db_path()
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            # Check if order_id already exists (idempotency check)
            cursor.execute("SELECT order_id FROM orders WHERE order_id = ?", (order_id,))
            if cursor.fetchone():
                logger.warning(f"Order ID {order_id} already processed, skipping")
                return False

            # Insert or update user and add credits atomically
            cursor.execute('''
                INSERT INTO users (token, credits) VALUES (?, ?)
                ON CONFLICT(token) DO UPDATE SET credits = credits + ?
            ''', (token, amount, amount))

            # Record the order
            cursor.execute('''
                INSERT INTO orders (order_id, token, credits_granted)
                VALUES (?, ?, ?)
            ''', (order_id, token, amount))

            conn.commit()
            logger.info(f"Added {amount} credits for token {token[:8]}..., order {order_id}")
            return True

    except sqlite3.Error as e:
        logger.error(f"Database error adding credits: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error adding credits: {e}")
        return False


def deduct_credits(token: str, amount: int) -> bool:
    """
    Atomically deducts credits from a user's account.

    Args:
        token: User token
        amount: Number of credits to deduct

    Returns:
        bool: True if credits were deducted, False if insufficient credits
    """
    try:
        db_path = get_db_path()
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()

            # Atomic credit deduction using WHERE clause
            cursor.execute('''
                UPDATE users
                SET credits = credits - ?
                WHERE token = ? AND credits >= ?
            ''', (amount, token, amount))

            # Check if any rows were updated (i.e., if user had enough credits)
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Deducted {amount} credits from token {token[:8]}...")
                return True
            else:
                # No rows updated means insufficient credits or user doesn't exist
                logger.warning(f"Insufficient credits for token {token[:8]}..., needed {amount}")
                return False

    except sqlite3.Error as e:
        logger.error(f"Database error deducting credits: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error deducting credits: {e}")
        return False


def get_validations_db_path() -> str:
    """Get validations database path."""
    # Check for test environment variable
    test_path = os.getenv('TEST_VALIDATIONS_DB_PATH')
    if test_path:
        return test_path

    # Production path (in dashboard directory)
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'dashboard',
        'data',
        'validations.db'
    )


def create_validation_record(
    job_id: str,
    user_type: str,
    citation_count: int,
    status: str = 'pending',
    paid_user_id: Optional[str] = None,
    free_user_id: Optional[str] = None,
    is_test_job: bool = False
) -> bool:
    """
    Create a new validation tracking record.

    Args:
        job_id: Unique identifier for the validation job
        user_type: Type of user ('paid', 'free', 'anonymous')
        citation_count: Number of citations being validated
        status: Current status of validation
        paid_user_id: Paid user UUID if applicable
        free_user_id: Free user UUID if applicable
        is_test_job: Whether this is a test job

    Returns:
        bool: True if record created successfully, False otherwise
    """
    try:
        db_path = get_validations_db_path()

        # Ensure directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Check what columns exist in the database
            cursor.execute("PRAGMA table_info(validations)")
            columns = [row[1] for row in cursor.fetchall()]

            has_status = 'status' in columns
            has_validation_status = 'validation_status' in columns
            has_is_test_job = 'is_test_job' in columns

            # Build the INSERT statement based on available columns
            insert_columns = ['job_id', 'user_type', 'citation_count']
            insert_values = [job_id, user_type, citation_count]

            # Add status column(s)
            if has_status and has_validation_status:
                insert_columns.extend(['status', 'validation_status'])
                insert_values.extend([status, status])
            elif has_status:
                insert_columns.append('status')
                insert_values.append(status)
            else:
                insert_columns.append('validation_status')
                insert_values.append(status)

            # Add optional columns
            optional_columns = ['paid_user_id', 'free_user_id']
            optional_values = [paid_user_id, free_user_id]
            for col, val in zip(optional_columns, optional_values):
                if col in columns:
                    insert_columns.append(col)
                    insert_values.append(val)

            # Add is_test_job if available
            if has_is_test_job:
                insert_columns.append('is_test_job')
                insert_values.append(is_test_job)

            # Add created_at
            insert_columns.append('created_at')
            insert_values.append('datetime(\'now\')')

            # Execute the INSERT
            cursor.execute(f'''
                INSERT INTO validations ({', '.join(insert_columns)})
                VALUES ({', '.join(['?'] * (len(insert_values) - 1))}, datetime('now'))
            ''', insert_values[:-1])  # Exclude the datetime('now') from values as it's in the SQL

            conn.commit()
            logger.info(f"Created validation record for job {job_id}")
            return True

    except sqlite3.Error as e:
        logger.error(f"Database error creating validation record: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error creating validation record: {e}")
        return False


def update_validation_tracking(
    job_id: str,
    status: Optional[str] = None,
    error_message: Optional[str] = None
) -> bool:
    """
    Update validation tracking record with completion information.

    Args:
        job_id: Unique identifier for the validation job
        status: New validation status
        error_message: Error message if validation failed

    Returns:
        bool: True if update successful, False otherwise
    """
    try:
        db_path = get_validations_db_path()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Check what status columns exist in the database
            cursor.execute("PRAGMA table_info(validations)")
            columns = [row[1] for row in cursor.fetchall()]

            has_status = 'status' in columns
            has_validation_status = 'validation_status' in columns

            # Build dynamic update query
            updates = []
            params = []

            if status is not None:
                if has_status and has_validation_status:
                    # Both columns exist - update both
                    updates.append("status = ?")
                    updates.append("validation_status = ?")
                    params.extend([status, status])
                elif has_status:
                    # Only status exists
                    updates.append("status = ?")
                    params.append(status)
                else:
                    # Only validation_status exists
                    updates.append("validation_status = ?")
                    params.append(status)

            if error_message is not None:
                updates.append("error_message = ?")
                params.append(error_message)

            if updates:
                params.append(job_id)
                sql = f"UPDATE validations SET {', '.join(updates)} WHERE job_id = ?"
                cursor.execute(sql, params)
                conn.commit()

                logger.debug(f"Updated validation tracking for job {job_id}")
                return True
            else:
                logger.warning(f"No updates provided for job {job_id}")
                return False

    except sqlite3.Error as e:
        logger.error(f"Database error updating validation tracking: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating validation tracking: {e}")
        return False


def try_increment_daily_usage(token: str, citation_count: int) -> dict:
    """
    Atomically check and increment daily usage.

    Returns:
    {
        'success': bool,          # False if would exceed 1000 limit
        'used_before': int,       # Usage before this increment
        'used_after': int,        # Usage after (if success)
        'remaining': int,         # Citations left in window
        'reset_timestamp': int    # When limit resets (Unix timestamp)
    }

    IMPORTANT: Uses BEGIN IMMEDIATE to prevent race conditions.
    Without this, concurrent requests could exceed 1000/day limit.

    Example race condition (without atomic check):
    - Request A reads: 950 citations used
    - Request B reads: 950 citations used
    - Request A writes: 950 + 60 = 1010
    - Request B writes: 950 + 50 = 1000
    - Result: 1010 citations used (OVER LIMIT!)

    Oracle Feedback #1: https://docs/plans/2025-12-10-pricing-model-ab-test-design-FINAL.md
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")

    reset_timestamp = get_next_utc_midnight()

    try:
        # CRITICAL: BEGIN IMMEDIATE acquires write lock immediately
        # Prevents race between read and write
        cursor.execute("BEGIN IMMEDIATE")

        # Get current usage for this window
        cursor.execute("""
            SELECT citations_count FROM daily_usage
            WHERE token = ? AND reset_timestamp = ?
        """, (token, reset_timestamp))

        row = cursor.fetchone()
        current_usage = row[0] if row else 0

        # Check if increment would exceed limit
        if current_usage + citation_count > 1000:
            conn.rollback()
            conn.close()
            return {
                'success': False,
                'used_before': current_usage,
                'remaining': 1000 - current_usage,
                'reset_timestamp': reset_timestamp
            }

        # Safe to increment
        new_usage = current_usage + citation_count
        cursor.execute("""
            INSERT INTO daily_usage (token, reset_timestamp, citations_count)
            VALUES (?, ?, ?)
            ON CONFLICT(token, reset_timestamp) DO UPDATE SET
            citations_count = citations_count + ?
        """, (token, reset_timestamp, citation_count, citation_count))

        conn.commit()
        conn.close()

        return {
            'success': True,
            'used_before': current_usage,
            'used_after': new_usage,
            'remaining': 1000 - new_usage,
            'reset_timestamp': reset_timestamp
        }

    except Exception as e:
        conn.rollback()
        conn.close()
        raise


def get_daily_usage_for_current_window(token: str) -> int:
    """
    Get citation count for current UTC day window.

    Returns citations used in current window (0 if new window or no usage).
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    reset_timestamp = get_next_utc_midnight()
    cursor.execute("""
        SELECT citations_count FROM daily_usage
        WHERE token = ? AND reset_timestamp = ?
    """, (token, reset_timestamp))

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else 0


def get_active_pass(token: str) -> Optional[dict]:
    """
    Check if user has active pass.

    Returns:
    {
        'expiration_timestamp': int,  # Unix timestamp
        'pass_type': str,             # '1day', '7day', '30day'
        'purchase_date': int,
        'hours_remaining': int        # For UI display
    }
    Or None if no active pass.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA busy_timeout=5000")

    now = int(time.time())
    logger.debug(f"Checking active pass for {token[:8]} at {now}")
    
    cursor.execute("""
        SELECT expiration_timestamp, pass_type, purchase_date
        FROM user_passes
        WHERE token = ? AND expiration_timestamp > ?
    """, (token, now))

    row = cursor.fetchone()
    conn.close()

    if row:
        hours_remaining = (row[0] - now) // 3600
        logger.debug(f"Found active pass for {token[:8]}: {row[1]}, expires {row[0]}")
        return {
            'expiration_timestamp': row[0],
            'pass_type': row[1],
            'purchase_date': row[2],
            'hours_remaining': hours_remaining
        }
    
    logger.debug(f"No active pass found for {token[:8]} (checked > {now})")
    return None


def add_pass(token: str, days: int, pass_type: str, order_id: str) -> bool:
    """
    Grant time-based pass to user (idempotent).

    Pass Extension Logic (Oracle Feedback #15):
    - If user has active pass (any type), extend expiration by adding days
    - Example: 3 days left on 7-day pass + buy 30-day pass = 33 days total
    - Rationale: User shouldn't lose remaining time when upgrading/extending

    Idempotency (Oracle Feedback #6):
    - Uses BEGIN IMMEDIATE to prevent race conditions
    - Checks orders table for order_id (persistent record)
    - Catches IntegrityError if another thread processed concurrently

    Args:
        token: User identifier
        days: Duration to add (1, 7, or 30)
        pass_type: Display name ('1day', '7day', '30day')
        order_id: Polar order ID (for idempotency)

    Returns:
        True if pass granted (or already processed)
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")

    try:
        # CRITICAL: Lock early to prevent race conditions
        cursor.execute("BEGIN IMMEDIATE")

        # Idempotency check - has this order been processed?
        cursor.execute("SELECT 1 FROM orders WHERE order_id = ?", (order_id,))
        if cursor.fetchone():
            conn.rollback()
            conn.close()
            logger.info(f"Order {order_id} already processed (idempotent)")
            return True

        # Check for existing active pass
        now = int(time.time())
        cursor.execute("""
            SELECT expiration_timestamp, pass_type
            FROM user_passes
            WHERE token = ? AND expiration_timestamp > ?
        """, (token, now))

        existing = cursor.fetchone()

        if existing:
            # Extend existing pass (add days to current expiration)
            # Oracle Feedback #15: Always extend, regardless of pass type
            current_expiration = existing[0]
            new_expiration = current_expiration + (days * 86400)
            logger.info(f"Extending pass for {token}: {existing[1]} -> {pass_type} (+{days} days)")
        else:
            # New pass (starts now)
            new_expiration = now + (days * 86400)
            logger.info(f"Granting new {pass_type} pass to {token}")

        # Ensure user exists in users table (needed for get_credits to work)
        cursor.execute("INSERT OR IGNORE INTO users (token, credits) VALUES (?, 0)", (token,))

        # Record the order in orders table (persistent history)
        cursor.execute("""
            INSERT INTO orders (order_id, token, credits_granted, pass_days, pass_type)
            VALUES (?, ?, 0, ?, ?)
        """, (order_id, token, days, pass_type))

        # Insert or replace user pass state
        cursor.execute("""
            INSERT OR REPLACE INTO user_passes
            (token, expiration_timestamp, pass_type, purchase_date, order_id)
            VALUES (?, ?, ?, ?, ?)
        """, (token, new_expiration, pass_type, now, order_id))

        conn.commit()
        conn.close()
        return True

    except sqlite3.IntegrityError as e:
        # Race condition - another thread processed this order
        conn.rollback()
        conn.close()
        logger.warning(f"IntegrityError for order {order_id}: {e}")
        return True  # Treat as success (idempotent)

    except Exception as e:
        conn.rollback()
        conn.close()
        logger.error(f"Failed to add pass: {e}")
        raise


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {get_db_path()}")
    print(f"Validations database path: {get_validations_db_path()}")