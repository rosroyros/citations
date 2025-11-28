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
    validation_status: str = 'pending'
) -> bool:
    """
    Create a new validation tracking record.

    Args:
        job_id: Unique identifier for the validation job
        user_type: Type of user ('paid', 'free', 'anonymous')
        citation_count: Number of citations being validated
        validation_status: Current status of validation

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

            cursor.execute('''
                INSERT INTO validations (
                    job_id, user_type, citation_count, validation_status, created_at
                ) VALUES (?, ?, ?, ?, datetime('now'))
            ''', (job_id, user_type, citation_count, validation_status))

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
    validation_status: Optional[str] = None,
    results_gated: Optional[bool] = None,
    user_type: Optional[str] = None,
    gated_at: Optional[str] = None,
    results_ready_at: Optional[str] = None,
    error_message: Optional[str] = None
) -> bool:
    """
    Update validation tracking record with completion information.

    Args:
        job_id: Unique identifier for the validation job
        validation_status: New validation status
        results_gated: Whether results were gated
        user_type: Type of user (if needs updating)
        gated_at: ISO timestamp when results were gated
        results_ready_at: ISO timestamp when results became ready
        error_message: Error message if validation failed

    Returns:
        bool: True if update successful, False otherwise
    """
    try:
        db_path = get_validations_db_path()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Build dynamic update query
            updates = []
            params = []

            if validation_status is not None:
                updates.append("validation_status = ?")
                params.append(validation_status)

            if results_gated is not None:
                updates.append("results_gated = ?")
                params.append(results_gated)

            if user_type is not None:
                updates.append("user_type = ?")
                params.append(user_type)

            if gated_at is not None:
                updates.append("gated_at = ?")
                params.append(gated_at)

            if results_ready_at is not None:
                updates.append("results_ready_at = ?")
                params.append(results_ready_at)

            if error_message is not None:
                updates.append("error_message = ?")
                params.append(error_message)

            if updates:
                updates.append("updated_at = datetime('now')")
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


def record_result_reveal(job_id: str, gated_outcome: str = 'revealed') -> bool:
    """
    Record when user reveals gated results.

    Args:
        job_id: Unique identifier for the validation job
        gated_outcome: Outcome type ('revealed', 'abandoned', etc.)

    Returns:
        bool: True if record updated successfully, False otherwise
    """
    try:
        db_path = get_validations_db_path()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Get the time results were gated
            cursor.execute("SELECT gated_at FROM validations WHERE job_id = ?", (job_id,))
            result = cursor.fetchone()

            if not result:
                logger.warning(f"No validation record found for job {job_id}")
                return False

            gated_at = result[0]
            if not gated_at:
                logger.warning(f"Results were not gated for job {job_id}")
                return False

            # Calculate time to reveal
            from datetime import datetime
            gated_time = datetime.fromisoformat(gated_at.replace('Z', '+00:00') if gated_at.endswith('Z') else gated_at)
            reveal_time = datetime.utcnow()
            time_to_reveal = int((reveal_time - gated_time).total_seconds())

            # Update record
            cursor.execute('''
                UPDATE validations
                SET results_revealed_at = ?,
                    time_to_reveal_seconds = ?,
                    gated_outcome = ?,
                    updated_at = datetime('now')
                WHERE job_id = ?
            ''', (reveal_time.isoformat(), time_to_reveal, gated_outcome, job_id))

            conn.commit()
            logger.info(f"Recorded result reveal for job {job_id}: {time_to_reveal}s")
            return True

    except sqlite3.Error as e:
        logger.error(f"Database error recording result reveal: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error recording result reveal: {e}")
        return False


def get_validation_analytics(
    days: int = 7,
    user_type: Optional[str] = None
) -> dict:
    """
    Get analytics data for gated results.

    Args:
        days: Number of days to look back
        user_type: Optional filter by user type

    Returns:
        dict: Analytics data
    """
    try:
        db_path = get_validations_db_path()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Build WHERE clause
            where_conditions = ["created_at >= datetime('now', '-{} days')".format(days)]
            params = []

            if user_type:
                where_conditions.append("user_type = ?")
                params.append(user_type)

            where_clause = " AND ".join(where_conditions)

            # Get base statistics
            cursor.execute(f'''
                SELECT
                    COUNT(*) as total_validations,
                    COUNT(CASE WHEN results_gated = 1 THEN 1 END) as gated_count,
                    COUNT(CASE WHEN results_revealed_at IS NOT NULL THEN 1 END) as revealed_count,
                    AVG(time_to_reveal_seconds) as avg_time_to_reveal,
                    COUNT(CASE WHEN validation_status = 'completed' THEN 1 END) as completed_count,
                    COUNT(CASE WHEN validation_status = 'failed' THEN 1 END) as failed_count
                FROM validations
                WHERE {where_clause}
            ''', params)

            result = cursor.fetchone()
            if result:
                total, gated, revealed, avg_time, completed, failed = result

                # Calculate derived metrics
                reveal_rate = (revealed / gated * 100) if gated > 0 else 0
                success_rate = (completed / total * 100) if total > 0 else 0

                return {
                    'period_days': days,
                    'user_type': user_type or 'all',
                    'total_validations': total,
                    'gated_results': gated,
                    'revealed_results': revealed,
                    'reveal_rate': round(reveal_rate, 1),
                    'avg_time_to_reveal_seconds': round(avg_time, 1) if avg_time else 0,
                    'success_rate': round(success_rate, 1),
                    'failed_validations': failed
                }

            return {
                'period_days': days,
                'user_type': user_type or 'all',
                'total_validations': 0,
                'gated_results': 0,
                'revealed_results': 0,
                'reveal_rate': 0,
                'avg_time_to_reveal_seconds': 0,
                'success_rate': 0,
                'failed_validations': 0
            }

    except sqlite3.Error as e:
        logger.error(f"Database error getting analytics: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error getting analytics: {e}")
        return {}


def get_gated_validation_results(job_id: str) -> Optional[dict]:
    """
    Get gated validation results and status for a specific job.

    Args:
        job_id: Unique identifier for the validation job

    Returns:
        dict: Validation results with gating information, or None if not found
    """
    try:
        db_path = get_validations_db_path()

        # Ensure database and table exist
        if not os.path.exists(db_path):
            logger.debug(f"Validations database does not exist for job {job_id}")
            return None

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Query validation record with gating information
            cursor.execute('''
                SELECT
                    job_id,
                    user_type,
                    citation_count,
                    validation_status,
                    results_gated,
                    gated_at,
                    results_ready_at,
                    created_at,
                    updated_at,
                    error_message
                FROM validations
                WHERE job_id = ?
            ''', (job_id,))

            result = cursor.fetchone()

            if not result:
                logger.debug(f"No validation record found for job {job_id}")
                return None

            # Convert to dictionary
            (
                job_id,
                user_type,
                citation_count,
                validation_status,
                results_gated,
                gated_at,
                results_ready_at,
                created_at,
                updated_at,
                error_message
            ) = result

            return {
                'job_id': job_id,
                'user_type': user_type,
                'citation_count': citation_count,
                'validation_status': validation_status,
                'results_gated': bool(results_gated) if results_gated is not None else None,
                'gated_at': gated_at,
                'results_ready_at': results_ready_at,
                'created_at': created_at,
                'updated_at': updated_at,
                'error_message': error_message
            }

    except sqlite3.Error as e:
        logger.error(f"Database error getting gated validation results for job {job_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting gated validation results for job {job_id}: {e}")
        return None


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {get_db_path()}")
    print(f"Validations database path: {get_validations_db_path()}")