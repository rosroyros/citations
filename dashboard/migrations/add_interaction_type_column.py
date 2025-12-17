#!/usr/bin/env python3
"""
Database migration: Add interaction_type column to validations table.

Purpose: Add interaction_type column to distinguish between passive views
         and active clicks for inline pricing A/B test analytics.

When to run: BEFORE deploying code changes that log interaction_type.
             Run directly on VPS at /opt/citations/dashboard/

Safety: Idempotent (checks if column exists before adding).
        Non-destructive (only adds column, doesn't modify data).
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
    """Add interaction_type column to validations table."""

    # Check if database exists
    if not Path(DB_PATH).exists():
        print(f"❌ Database not found at {DB_PATH}")
        print("   Dashboard must be deployed first.")
        return False

    print(f"📂 Opening database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check and add interaction_type column
        if check_column_exists(cursor, 'validations', 'interaction_type'):
            print("✓ interaction_type column already exists")
        else:
            print("➕ Adding interaction_type column...")
            cursor.execute("ALTER TABLE validations ADD COLUMN interaction_type TEXT")
            print("✓ Added interaction_type column")

        # Add index for performance
        print("➕ Adding index...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_interaction_type
            ON validations(interaction_type)
        """)
        print("✓ Added index")

        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")

        # Verify migration
        print("\n📊 Verification:")
        cursor.execute("PRAGMA table_info(validations)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"   Columns in validations table: {len(columns)}")
        print(f"   - interaction_type present: {('interaction_type' in columns)}")

        # Show expected values info
        print("\n📝 Expected values for interaction_type:")
        print("   - NULL: Legacy data (before this feature)")
        print("   - 'active': User clicked upgrade button (intentional)")
        print("   - 'auto': Pricing was shown automatically (inline variant)")

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Interaction Type Column Migration")
    print("=" * 60)
    print()

    success = migrate()
    sys.exit(0 if success else 1)