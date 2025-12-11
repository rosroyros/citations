#!/usr/bin/env python3
"""
Database migration: Add pricing model A/B test tables.

Creates:
- user_passes: Time-based access grants
- daily_usage: Per-day citation tracking for pass users
- Adds experiment_variant, product_id columns to validations

Oracle Feedback:
- #3: Use Unix timestamps (INTEGER) not date strings
- #6: UNIQUE constraint on order_id for webhook idempotency
"""

import sqlite3
import sys
from pathlib import Path

# Database paths - match application configuration
# Script is at backend/migrations/, so parent.parent is project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
CREDITS_DB_PATH = PROJECT_ROOT / 'backend' / 'credits.db'
VALIDATIONS_DB_PATH = PROJECT_ROOT / 'dashboard' / 'data' / 'validations.db'

def migrate():
    """Run migration - safe to run multiple times (IF NOT EXISTS)."""
    print(f"Running migration on credits.db: {CREDITS_DB_PATH}")
    print(f"Running migration on validations.db: {VALIDATIONS_DB_PATH}")

    # Migrate credits.db
    conn = sqlite3.connect(CREDITS_DB_PATH)
    cursor = conn.cursor()

    try:
        # Table 1: user_passes
        # Stores time-based access grants
        print("Creating user_passes table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_passes (
                token TEXT PRIMARY KEY,
                expiration_timestamp INTEGER NOT NULL,
                pass_type TEXT NOT NULL,
                purchase_date INTEGER NOT NULL,
                order_id TEXT UNIQUE NOT NULL
            )
        """)

        # Index for efficient expiration checks
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_passes_expiration
            ON user_passes(token, expiration_timestamp)
        """)

        # Table 2: daily_usage
        # Tracks citations used per day for pass users (1000/day limit)
        print("Creating daily_usage table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_usage (
                token TEXT NOT NULL,
                reset_timestamp INTEGER NOT NULL,
                citations_count INTEGER DEFAULT 0,
                PRIMARY KEY (token, reset_timestamp)
            )
        """)

        conn.commit()
        # Note: credits.db changes committed here. If validations migration fails,
        # system will be in partially migrated state but migration is idempotent
        conn.close()

        # Migrate validations.db
        print("\nMigrating validations database...")
        conn = sqlite3.connect(VALIDATIONS_DB_PATH)
        cursor = conn.cursor()

        # Table 3: Add tracking columns to validations
        # experiment_variant: '1' or '2' (which pricing table shown)
        # product_id: Polar product ID purchased
        print("Adding experiment_variant column to validations...")
        try:
            cursor.execute("ALTER TABLE validations ADD COLUMN experiment_variant TEXT")
            print("  ✓ Added experiment_variant column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("  → experiment_variant column already exists")
            else:
                raise

        print("Adding product_id column to validations...")
        try:
            cursor.execute("ALTER TABLE validations ADD COLUMN product_id TEXT")
            print("  ✓ Added product_id column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("  → product_id column already exists")
            else:
                raise

        conn.commit()
        print("\n✓ Migration complete!")
        print("\nCreated tables:")
        print("  - user_passes (token, expiration_timestamp, pass_type, purchase_date, order_id)")
        print("  - daily_usage (token, reset_timestamp, citations_count)")
        print("\nAdded columns:")
        print("  - validations.experiment_variant")
        print("  - validations.product_id")

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)
    finally:
        try:
            conn.close()
        except:
            pass

if __name__ == '__main__':
    migrate()