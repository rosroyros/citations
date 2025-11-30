#!/usr/bin/env python3
"""
Create the validations database schema for test server validation.
This script sets up the dashboard data directory and creates the validations
table with a simplified schema for basic job tracking.
"""

import sqlite3
import os
from pathlib import Path

def create_validations_database():
    """Create the validations database with a simplified schema."""

    # Ensure dashboard data directory exists
    dashboard_dir = Path("dashboard/data")
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Created directory: {dashboard_dir}")

    # Database path
    db_path = dashboard_dir / "validations.db"

    # Connect and create schema
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create validations table with a simplified schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS validations (
            job_id TEXT PRIMARY KEY,
            user_type TEXT NOT NULL,
            citation_count INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            error_message TEXT NULL
        )
    ''')

    # Create indexes for performance
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_validations_user_type
        ON validations (user_type)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_validations_status
        ON validations (status, created_at)
    ''')

    # Commit and close
    conn.commit()
    conn.close()

    print(f"✅ Created validations database: {db_path}")
    print("✅ Created validations table with simplified schema")
    print("✅ Created performance indexes")

    return str(db_path)

if __name__ == "__main__":
    db_path = create_validations_database()
    print(f"\n🎉 Database setup complete!")
    print(f"📍 Database location: {db_path}")
    print("\n📊 Schema includes basic job tracking:")
    print("   - job_id, user_type, citation_count, status, created_at, error_message")