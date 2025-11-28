#!/usr/bin/env python3
"""
Database rollback script for gated results tracking
Removes columns added by migrate_gated_results.py
"""

import sqlite3
import sys
import os
import shutil
from datetime import datetime
from pathlib import Path

def backup_database(db_path: str) -> str:
    """Create a backup before rollback"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.pre_rollback_{timestamp}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Database backed up to: {backup_path}")
    return backup_path

def create_new_table_without_columns(cursor: sqlite3.Cursor) -> str:
    """Create new validations table without gated results columns"""

    # Get current schema
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='validations'")
    current_schema = cursor.fetchone()[0]
    print(f"📋 Current schema: {current_schema[:100]}...")

    # New schema without the gated results columns
    new_schema = """
    CREATE TABLE validations_new (
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
        error_message TEXT,
        citations_text TEXT
    )
    """

    return new_schema

def run_rollback(db_path: str) -> bool:
    """Execute the database rollback"""
    print(f"🔄 Starting rollback on: {db_path}")

    # Create backup
    backup_path = backup_database(db_path)

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")

        # Check if gated results columns exist
        cursor.execute("PRAGMA table_info(validations)")
        existing_columns = [row[1] for row in cursor.fetchall()]

        gated_columns = [
            "results_ready_at", "results_revealed_at", "time_to_reveal_seconds",
            "results_gated", "gated_outcome"
        ]

        columns_to_remove = [col for col in gated_columns if col in existing_columns]

        if not columns_to_remove:
            print("⚠️  No gated results columns found, nothing to rollback")
            conn.close()
            return True

        print(f"🗑️  Columns to remove: {columns_to_remove}")

        # Create new table without gated columns
        new_schema = create_new_table_without_columns(cursor)
        cursor.execute(new_schema)
        print("➕ Created new validations table")

        # Copy data to new table (excluding gated columns)
        original_columns = [col for col in existing_columns if col not in gated_columns]
        columns_str = ", ".join(original_columns)

        cursor.execute(f"""
            INSERT INTO validations_new ({columns_str})
            SELECT {columns_str}
            FROM validations
        """)

        rows_copied = cursor.rowcount
        print(f"📦 Copied {rows_copied} rows to new table")

        # Drop the gated tracking index if it exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_validations_gated_tracking'")
        if cursor.fetchone():
            cursor.execute("DROP INDEX idx_validations_gated_tracking")
            print("🗑️  Dropped gated tracking index")

        # Drop original table
        cursor.execute("DROP TABLE validations")
        print("🗑️  Dropped original validations table")

        # Rename new table
        cursor.execute("ALTER TABLE validations_new RENAME TO validations")
        print("✅ Renamed new table to validations")

        # Recreate original indexes (except the gated one)
        cursor.execute("CREATE INDEX idx_created_at ON validations(created_at)")
        cursor.execute("CREATE INDEX idx_status ON validations(status)")
        cursor.execute("CREATE INDEX idx_user_type ON validations(user_type)")
        cursor.execute("""
            CREATE INDEX idx_citations_text
            ON validations(citations_text)
            WHERE citations_text IS NOT NULL AND length(citations_text) > 0
        """)
        print("📊 Recreated original indexes")

        # Commit changes
        conn.commit()
        print(f"✅ Rollback completed successfully")

        # Verify rollback
        cursor.execute("PRAGMA table_info(validations)")
        final_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Final table has {len(final_columns)} columns: {final_columns}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        # Restore backup if rollback failed
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, db_path)
            print(f"🔄 Restored database from backup")
        return False

def test_rollback(db_path: str):
    """Test that database functions correctly after rollback"""
    print("\n🧪 Testing database functionality after rollback...")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Test basic operations
        cursor.execute("SELECT COUNT(*) FROM validations")
        count = cursor.fetchone()[0]
        print(f"✅ Basic query works: {count} rows in validations")

        # Test original columns are still there
        original_columns = [
            "job_id", "created_at", "completed_at", "duration_seconds",
            "citation_count", "token_usage_prompt", "token_usage_completion",
            "token_usage_total", "user_type", "status", "error_message", "citations_text"
        ]

        for col in original_columns:
            try:
                cursor.execute(f"SELECT {col} FROM validations LIMIT 1")
            except sqlite3.OperationalError:
                print(f"❌ Missing original column: {col}")
                return False

        print(f"✅ All original columns present")

        # Test that gated columns are gone
        gated_columns = ["results_ready_at", "results_revealed_at", "time_to_reveal_seconds", "results_gated", "gated_outcome"]
        for col in gated_columns:
            try:
                cursor.execute(f"SELECT {col} FROM validations LIMIT 1")
                print(f"⚠️  Gated column still exists: {col}")
            except sqlite3.OperationalError:
                print(f"✅ Gated column removed: {col}")

        conn.close()
        print("✅ Database rollback test passed")

    except Exception as e:
        print(f"❌ Database rollback test failed: {e}")
        return False

    return True

if __name__ == "__main__":
    # Default to validations database
    db_path = "dashboard/data/validations.db"

    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        sys.exit(1)

    print("=" * 60)
    print("DATABASE SCHEMA ROLLBACK")
    print("Gated Results Tracking - citations-76h0")
    print("=" * 60)
    print("⚠️  This will remove gated results columns and data!")
    print("⚠️  Make sure you have a backup before proceeding!")
    print()

    # Ask for confirmation
    response = input("Are you sure you want to proceed? (yes/no): ")
    if response.strip().lower() != 'yes':
        print("❌ Rollback cancelled")
        sys.exit(0)

    success = run_rollback(db_path)

    if success:
        test_success = test_rollback(db_path)
        if test_success:
            print("\n🎉 Rollback completed successfully!")
            sys.exit(0)
        else:
            print("\n⚠️  Rollback succeeded but tests failed")
            sys.exit(1)
    else:
        print("\n💥 Rollback failed!")
        sys.exit(1)