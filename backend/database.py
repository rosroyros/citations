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


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {get_db_path()}")