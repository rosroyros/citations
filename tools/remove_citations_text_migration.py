#!/usr/bin/env python3
"""
Migration script to remove citations_text column from validations database
Issue: citations-kslk
"""

import sqlite3
import os
import logging
import time
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
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'dashboard',
        'data',
        'validations.db'
    )

def check_citations_text_exists(conn) -> bool:
    """Check if citations_text column exists in validations table."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(validations)")
    columns = [row[1] for row in cursor.fetchall()]
    return 'citations_text' in columns

def backup_database(db_path: str) -> str:
    """Create a backup of the database before migration."""
    import shutil
    backup_path = f"{db_path}.backup_{int(time.time())}"
    shutil.copy2(db_path, backup_path)
    logger.info(f"Created database backup: {backup_path}")
    return backup_path

def remove_citations_text_column():
    """Remove citations_text column and its index from validations table."""
    try:
        db_path = get_validations_db_path()

        # Check if database exists
        if not os.path.exists(db_path):
            logger.error(f"Database not found at: {db_path}")
            return False

        logger.info(f"Starting migration on database: {db_path}")

        # Create backup
        import time
        backup_path = backup_database(db_path)

        with sqlite3.connect(db_path) as conn:
            # Check if column exists
            if not check_citations_text_exists(conn):
                logger.info("citations_text column does not exist - nothing to migrate")
                return True

            logger.info("Removing citations_text column from validations table...")

            # Check SQLite version supports ALTER TABLE DROP COLUMN (3.35.0+)
            cursor = conn.cursor()
            cursor.execute("SELECT sqlite_version()")
            sqlite_version = cursor.fetchone()[0]
            version_parts = [int(x) for x in sqlite_version.split('.')]

            if version_parts[0] > 3 or (version_parts[0] == 3 and version_parts[1] >= 35):
                # Use modern ALTER TABLE DROP COLUMN for better performance
                logger.info(f"SQLite {sqlite_version} supports ALTER TABLE DROP COLUMN - using modern approach")
                cursor.execute("ALTER TABLE validations DROP COLUMN citations_text")
                logger.info("Dropped citations_text column using ALTER TABLE DROP COLUMN")
            else:
                # Fallback to the table recreation method for older SQLite versions
                logger.warning(f"SQLite {sqlite_version} does not support ALTER TABLE DROP COLUMN - using fallback method")
                # Get column names excluding citations_text
                cursor.execute("PRAGMA table_info(validations)")
                all_columns = [row[1] for row in cursor.fetchall()]
                new_columns = [col for col in all_columns if col != 'citations_text']

                # Explicitly select and insert data (safer than SELECT *)
                columns_str = ', '.join(new_columns)
                cursor.execute(f"SELECT {columns_str} FROM validations")
                rows = cursor.fetchall()

                # Drop and recreate table
                cursor.execute("DROP TABLE validations")
                cursor.execute(f"""
                    CREATE TABLE validations (
                        job_id TEXT PRIMARY KEY,
                        created_at TEXT NOT NULL,
                        completed_at TEXT,
                        duration_seconds REAL,
                        citation_count INTEGER,
                        token_usage_prompt INTEGER,
                        token_usage_completion INTEGER,
                        token_usage_total INTEGER,
                        user_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        error_message TEXT
                    )
                """)

                # Re-insert data explicitly
                placeholders = ', '.join(['?' for _ in new_columns])
                cursor.executemany(f"INSERT INTO validations ({columns_str}) VALUES ({placeholders})", rows)
                logger.info("Recreated table and migrated data using fallback method")

            # Remove citations_text index if it exists
            cursor.execute("DROP INDEX IF EXISTS idx_citations_text")
            logger.info("Removed citations_text index if it existed")

            conn.commit()
            logger.info("Migration completed successfully")

        return True

    except sqlite3.Error as e:
        logger.error(f"Database error during migration: {e}")
        # Restore from backup if migration failed
        if os.path.exists(backup_path):
            logger.info("Restoring database from backup...")
            import shutil
            shutil.copy2(backup_path, db_path)
            logger.info("Database restored from backup")
        return False

    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        return False

def main():
    """Main migration function."""
    logger.info("Starting citations_text column removal migration...")

    if remove_citations_text_column():
        logger.info("✅ Migration completed successfully!")
        print("\n✅ citations_text column has been removed from validations database")
        print("📝 The following changes were made:")
        print("   - Removed citations_text column from validations table")
        print("   - Removed idx_citations_text index")
        print("   - All other data and indexes preserved")
        print("   - Database backup created automatically")
    else:
        logger.error("❌ Migration failed!")
        print("\n❌ Migration failed. Check logs for details.")
        exit(1)

if __name__ == "__main__":
    main()