#!/usr/bin/env python3
"""
Migration script to add provider column to validations table.

This script adds a 'provider' column (TEXT) to the validations table
to store which AI provider was used for each validation job.

The script is idempotent - it checks if the column already exists
before attempting to add it.
"""
import sqlite3
import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_validations_db_path() -> str:
    """Get validations database path."""
    # Check for test environment variable
    test_path = os.getenv('TEST_VALIDATIONS_DB_PATH')
    if test_path:
        return test_path

    # Production path (in dashboard directory)
    # Assumes script is run from project root
    return os.path.join(
        os.path.dirname(__file__),
        '..',
        'dashboard',
        'data',
        'validations.db'
    )


def migrate_provider_column(db_path: str) -> bool:
    """
    Add provider column to validations table if it doesn't exist.

    Args:
        db_path: Path to the SQLite database

    Returns:
        bool: True if migration succeeded or was not needed, False otherwise
    """
    if not os.path.exists(db_path):
        logger.error(f"Database not found at: {db_path}")
        return False

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if provider column already exists
        cursor.execute("PRAGMA table_info(validations)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'provider' in columns:
            logger.info("Provider column already exists in validations table")
            conn.close()
            return True

        # Add provider column
        logger.info("Adding provider column to validations table...")
        cursor.execute("ALTER TABLE validations ADD COLUMN provider TEXT")

        # Create index on provider column for better dashboard query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_provider ON validations(provider)")

        conn.commit()
        conn.close()

        logger.info("✅ Migration completed successfully")
        logger.info(f"   - Added provider column to validations table")
        logger.info(f"   - Created index on provider column")

        return True

    except sqlite3.Error as e:
        logger.error(f"Database error during migration: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        return False


def main():
    """Main migration function."""
    # Get database path
    db_path = get_validations_db_path()

    logger.info("=== Provider Column Migration ===")
    logger.info(f"Database: {db_path}")

    # Confirm before proceeding in production
    if os.getenv('TEST_VALIDATIONS_DB_PATH') is None:
        response = input("\nThis will modify the production database. Continue? (y/N): ")
        if response.lower() != 'y':
            logger.info("Migration cancelled by user")
            sys.exit(0)

    # Run migration
    success = migrate_provider_column(db_path)

    if success:
        logger.info("\n✅ Migration completed successfully")
        sys.exit(0)
    else:
        logger.error("\n❌ Migration failed")
        sys.exit(1)


if __name__ == "__main__":
    main()