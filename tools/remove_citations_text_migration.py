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

            # Get all data from validations table before dropping column
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM validations")
            rows = cursor.fetchall()

            # Get column names excluding citations_text
            cursor.execute("PRAGMA table_info(validations)")
            all_columns = [row[1] for row in cursor.fetchall()]
            new_columns = [col for col in all_columns if col != 'citations_text']

            # Drop the table
            cursor.execute("DROP TABLE validations")
            logger.info("Dropped validations table")

            # Recreate table without citations_text column
            create_table_sql = f"""
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
            """
            cursor.execute(create_table_sql)
            logger.info("Recreated validations table without citations_text column")

            # Recreate indexes (except citations_text index)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON validations(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_type ON validations(user_type)")

            # Handle status vs validation_status compatibility
            cursor.execute("PRAGMA table_info(validations)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'status' in columns:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON validations(status)")
            if 'validation_status' in columns:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_validation_status ON validations(validation_status)")

            logger.info("Recreated indexes")

            # Insert data back (excluding citations_text)
            if rows:
                # Build INSERT statement dynamically
                placeholders = ', '.join(['?' for _ in new_columns])
                insert_sql = f"INSERT INTO validations ({', '.join(new_columns)}) VALUES ({placeholders})"

                # Filter data to exclude citations_text
                filtered_rows = []
                for row in rows:
                    row_dict = dict(zip(all_columns, row))
                    filtered_row = [row_dict[col] for col in new_columns]
                    filtered_rows.append(filtered_row)

                cursor.executemany(insert_sql, filtered_rows)
                logger.info(f"Restored {len(filtered_rows)} records without citations_text column")

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