#!/usr/bin/env python3
"""
Migration script to add gating columns to validations table
Run this to add the missing gating-related columns to the database schema
"""
import sqlite3
import os
import sys

def add_gating_columns(db_path: str):
    """
    Add gating-related columns to the validations table

    Args:
        db_path: Path to the SQLite database
    """
    if not os.path.exists(db_path):
        print(f"Error: Database {db_path} does not exist")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check current schema
        cursor.execute("PRAGMA table_info(validations)")
        columns = [col[1] for col in cursor.fetchall()]

        print(f"Current columns in validations table: {columns}")

        # Add missing columns - validated against expected column names
        columns_to_add = [
            ("results_gated", "BOOLEAN"),
            ("results_revealed_at", "TEXT"),
            ("gated_outcome", "TEXT")
        ]

        # Validate column names to prevent injection
        valid_column_names = {"results_gated", "results_revealed_at", "gated_outcome"}
        valid_column_types = {"BOOLEAN", "TEXT", "INTEGER", "REAL"}

        added_columns = []
        for col_name, col_type in columns_to_add:
            if col_name not in columns:
                # Security validation
                if col_name not in valid_column_names:
                    raise ValueError(f"Invalid column name: {col_name}")
                if col_type not in valid_column_types:
                    raise ValueError(f"Invalid column type: {col_type}")

                print(f"Adding column: {col_name}")
                cursor.execute(f"ALTER TABLE validations ADD COLUMN {col_name} {col_type}")
                added_columns.append(col_name)
            else:
                print(f"Column {col_name} already exists")

        if added_columns:
            conn.commit()
            print(f"✅ Successfully added columns: {added_columns}")
        else:
            print("ℹ️  All gating columns already exist")

        # Verify the schema
        cursor.execute("PRAGMA table_info(validations)")
        updated_columns = [col[1] for col in cursor.fetchall()]
        print(f"Updated columns in validations table: {updated_columns}")

        return True

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Main migration function"""
    # Default path for dashboard database
    default_db = "dashboard/data/validations.db"

    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = default_db

    print(f"Running migration on database: {db_path}")

    success = add_gating_columns(db_path)

    if success:
        print("\n✅ Migration completed successfully!")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()