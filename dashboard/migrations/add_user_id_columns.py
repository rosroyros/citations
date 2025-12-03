#!/usr/bin/env python3
"""
Database migration: Add user ID columns to validations table.

Purpose: Add paid_user_id and free_user_id columns to existing validations table
         to support user tracking and journey analysis.

When to run: BEFORE deploying code changes that log user IDs.
             Run directly on VPS at /opt/citations/dashboard/

Safety: Idempotent (checks if columns exist before adding).
        Non-destructive (only adds columns, doesn't modify data).
"""

import sqlite3
import sys
import os
from pathlib import Path

# Allow DB_PATH override for testing
DB_PATH = os.environ.get('DB_PATH', '/opt/citations/dashboard/data/validations.db')

def check_column_exists(cursor, table, column):
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns

def migrate():
    """Add user ID columns to validations table."""

    # Check if database exists
    if not Path(DB_PATH).exists():
        print(f"❌ Database not found at {DB_PATH}")
        print("   Dashboard must be deployed first.")
        return False

    print(f"📂 Opening database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check and add paid_user_id column
        if check_column_exists(cursor, 'validations', 'paid_user_id'):
            print("✓ paid_user_id column already exists")
        else:
            print("➕ Adding paid_user_id column...")
            cursor.execute("ALTER TABLE validations ADD COLUMN paid_user_id TEXT")
            print("✓ Added paid_user_id column")

        # Check and add free_user_id column
        if check_column_exists(cursor, 'validations', 'free_user_id'):
            print("✓ free_user_id column already exists")
        else:
            print("➕ Adding free_user_id column...")
            cursor.execute("ALTER TABLE validations ADD COLUMN free_user_id TEXT")
            print("✓ Added free_user_id column")

        # Add indexes for performance
        print("➕ Adding indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_paid_user_id
            ON validations(paid_user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_free_user_id
            ON validations(free_user_id)
        """)
        print("✓ Added indexes")

        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")

        # Verify migration
        print("\n📊 Verification:")
        cursor.execute("PRAGMA table_info(validations)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"   Columns in validations table: {len(columns)}")
        print(f"   - paid_user_id present: {('paid_user_id' in columns)}")
        print(f"   - free_user_id present: {('free_user_id' in columns)}")

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("User ID Columns Migration")
    print("=" * 60)
    print()

    success = migrate()
    sys.exit(0 if success else 1)