#!/usr/bin/env python3
"""
Database migration script for gated results tracking
Adds new columns to validations table for tracking user engagement metrics
"""

import sqlite3
import sys
import os
from pathlib import Path
import shutil
from datetime import datetime

def backup_database(db_path: str) -> str:
    """Create a backup of the database before migration"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Database backed up to: {backup_path}")
    return backup_path

def verify_columns_exist(cursor: sqlite3.Cursor, table_name: str) -> list:
    """Check which columns already exist in the table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = [row[1] for row in cursor.fetchall()]
    return existing_columns

def run_migration(db_path: str) -> bool:
    """Execute the database migration"""
    print(f"🚀 Starting migration on: {db_path}")

    # Create backup
    backup_path = backup_database(db_path)

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check existing columns
        existing_columns = verify_columns_exist(cursor, "validations")
        print(f"📋 Existing columns: {existing_columns}")

        # New columns to add
        new_columns = [
            ("results_ready_at", "TEXT DEFAULT NULL"),
            ("results_revealed_at", "TEXT DEFAULT NULL"),
            ("time_to_reveal_seconds", "INTEGER DEFAULT NULL"),
            ("results_gated", "BOOLEAN DEFAULT FALSE"),
            ("gated_outcome", "TEXT DEFAULT NULL")
        ]

        # Add missing columns
        columns_added = 0
        for col_name, col_def in new_columns:
            if col_name not in existing_columns:
                sql = f"ALTER TABLE validations ADD COLUMN {col_name} {col_def}"
                print(f"➕ Adding column: {col_name}")
                cursor.execute(sql)
                columns_added += 1
            else:
                print(f"⚠️  Column {col_name} already exists, skipping")

        # Create index for performance optimization
        index_name = "idx_validations_gated_tracking"
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'")
        if not cursor.fetchone():
            index_sql = f"""
            CREATE INDEX {index_name} ON validations(
                results_gated,
                results_revealed_at,
                created_at
            )
            """
            print(f"📊 Creating index: {index_name}")
            cursor.execute(index_sql)
        else:
            print(f"⚠️  Index {index_name} already exists, skipping")

        # Commit changes
        conn.commit()
        print(f"✅ Migration completed successfully")
        print(f"   - Added {columns_added} new columns")
        print(f"   - Created performance index")

        # Verify schema
        cursor.execute("PRAGMA table_info(validations)")
        updated_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Updated table has {len(updated_columns)} columns")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        # Restore backup if migration failed
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, db_path)
            print(f"🔄 Restored database from backup")
        return False

def test_migration(db_path: str):
    """Test that database functions correctly after migration"""
    print("\n🧪 Testing database functionality...")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Test basic operations
        cursor.execute("SELECT COUNT(*) FROM validations")
        count = cursor.fetchone()[0]
        print(f"✅ Basic query works: {count} rows in validations")

        # Test new columns are accessible
        cursor.execute("""
            SELECT job_id, results_ready_at, results_revealed_at,
                   time_to_reveal_seconds, results_gated, gated_outcome
            FROM validations
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            print(f"✅ New columns accessible: {len(row)} columns returned")

        # Test index usage
        cursor.execute(f"EXPLAIN QUERY PLAN SELECT * FROM validations WHERE results_gated = 1")
        plan = cursor.fetchall()
        uses_index = any("idx_validations_gated_tracking" in str(p) for p in plan)
        print(f"✅ Query plan analysis complete, index usage: {uses_index}")

        conn.close()
        print("✅ Database functionality test passed")

    except Exception as e:
        print(f"❌ Database test failed: {e}")
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
    print("DATABASE SCHEMA MIGRATION")
    print("Gated Results Tracking - citations-76h0")
    print("=" * 60)

    success = run_migration(db_path)

    if success:
        test_success = test_migration(db_path)
        if test_success:
            print("\n🎉 Migration completed successfully!")
            sys.exit(0)
        else:
            print("\n⚠️  Migration succeeded but tests failed")
            sys.exit(1)
    else:
        print("\n💥 Migration failed!")
        sys.exit(1)