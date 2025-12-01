#!/usr/bin/env python3
"""
Gradual migration script for dashboard database.
Implements Claude Oracle's safer approach:
- Add missing columns without renaming validation_status
- Preserve existing gated results functionality
- Enable citation text feature
"""

import sqlite3
import os
import sys

DB_PATH = "./dashboard/data/validations.db"

def get_table_info(cursor, table_name):
    """Returns a list of column names for a given table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]

def add_missing_columns(cursor):
    """Add missing validation columns without disrupting existing schema"""
    missing_columns = {
        'completed_at': 'TEXT',
        'duration_seconds': 'REAL',
        'token_usage_prompt': 'INTEGER',
        'token_usage_completion': 'INTEGER',
        'token_usage_total': 'INTEGER',
        'citations_text': 'TEXT'
    }

    current_columns = get_table_info(cursor, 'validations')

    for col_name, col_type in missing_columns.items():
        if col_name not in current_columns:
            print(f"Adding column: {col_name} ({col_type})")
            cursor.execute(f"ALTER TABLE validations ADD COLUMN {col_name} {col_type}")
        else:
            print(f"Column {col_name} already exists, skipping...")

def create_compatibility_indexes(cursor):
    """Create indexes for both status and validation_status columns"""
    current_columns = get_table_info(cursor, 'validations')

    if 'status' in current_columns:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON validations(status)")
        print("Created index on 'status' column")

    if 'validation_status' in current_columns:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_validation_status ON validations(validation_status)")
        print("Created index on 'validation_status' column")

def migrate():
    """Perform gradual migration to add missing columns"""
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        sys.exit(1)

    print(f"Connecting to database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("Starting gradual migration...")
        cursor.execute("BEGIN TRANSACTION")

        # Check current state
        current_columns = get_table_info(cursor, 'validations')
        print(f"Current columns: {current_columns}")
        record_count = cursor.execute("SELECT COUNT(*) FROM validations").fetchone()[0]
        print(f"Record count: {record_count}")

        # Phase 1: Add missing columns (non-disruptive)
        add_missing_columns(cursor)

        # Phase 2: Create compatibility indexes
        create_compatibility_indexes(cursor)

        cursor.execute("COMMIT")
        print("\nMigration completed successfully!")

        # Verify final state
        final_columns = get_table_info(cursor, 'validations')
        print(f"Final columns: {final_columns}")

    except Exception as e:
        print(f"\nMigration failed: {e}")
        print("Rolling back...")
        cursor.execute("ROLLBACK")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    print("Gradual Database Migration - Claude Oracle's Safe Approach")
    print("=" * 60)
    print(f"Target database: {os.path.abspath(DB_PATH)}")
    print("This migration will:")
    print("- Add missing columns: completed_at, duration_seconds, token_usage_*, citations_text")
    print("- Preserve existing validation_status column (gated results depend on this)")
    print("- Create compatibility indexes")
    print()

    response = input("Continue with migration? (y/n): ")
    if response.lower() == 'y':
        migrate()
    else:
        print("Migration cancelled.")