import sqlite3
import os
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database file path
DB_PATH = 'backend/credits.db'

def init_db():
    """
    Initialize the SQLite database with the required schema.
    Creates the database file and tables if they don't exist.
    """
    try:
        # Ensure the directory exists
        db_dir = os.path.dirname(DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Created database directory: {db_dir}")

        # Connect to database (creates file if it doesn't exist)
        logger.info(f"Initializing database at: {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)

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


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")