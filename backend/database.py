import sqlite3
import os
import logging
from pathlib import Path
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (token) REFERENCES users(token)
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


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {get_db_path()}")
    print(f"Validations database path: {get_validations_db_path()}")