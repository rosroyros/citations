
import sqlite3
import os
import sys

# The dashboard database is in the `backend` directory, one level up from `tools`
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', 'dashboard.db')

# --- Schema Definitions ---
# This is the schema as it exists in the user's environment
OLD_SCHEMA_COLUMNS = [
    "job_id", "user_type", "citation_count", "validation_status", "created_at",
    "results_gated", "gated_at", "results_ready_at", "results_revealed_at",
    "time_to_reveal_seconds", "gated_outcome", "error_message"
]

# This is the target schema defined in dashboard/database.py
FINAL_SCHEMA = {
    "job_id": "TEXT PRIMARY KEY",
    "created_at": "TEXT NOT NULL",
    "completed_at": "TEXT",
    "duration_seconds": "REAL",
    "citation_count": "INTEGER",
    "token_usage_prompt": "INTEGER",
    "token_usage_completion": "INTEGER",
    "token_usage_total": "INTEGER",
    "user_type": "TEXT NOT NULL",
    "status": "TEXT NOT NULL",
    "error_message": "TEXT",
    "citations_text": "TEXT",
    # Gating columns from the old schema that need to be preserved
    "results_gated": "BOOLEAN",
    "gated_at": "TIMESTAMP",
    "results_ready_at": "TIMESTAMP",
    "results_revealed_at": "TIMESTAMP",
    "time_to_reveal_seconds": "INTEGER",
    "gated_outcome": "TEXT"
}

def get_table_info(cursor, table_name):
    """Returns a list of column names for a given table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]

def migrate():
    """
    Performs a safe, transactional migration of the dashboard database schema.
    - Adds all missing columns.
    - Renames 'validation_status' to 'status' by recreating the table.
    """
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        sys.exit(1)

    print(f"Connecting to database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("Beginning transaction...")
        cursor.execute("BEGIN TRANSACTION")

        current_columns = get_table_info(cursor, 'validations')
        print(f"Current columns: {current_columns}")

        # Step 1: Check if migration is even needed.
        # If 'status' exists and 'validation_status' does not, we assume migration is done.
        if 'status' in current_columns and 'validation_status' not in current_columns:
            print("Schema is already up-to-date. No migration needed.")
            cursor.execute("COMMIT")
            return

        # If we are in the old state, validation_status must exist.
        if 'validation_status' not in current_columns:
             raise RuntimeError(
                "The database schema is in an unexpected state. "
                "It lacks both 'status' and 'validation_status'. Halting migration."
            )

        # Step 2: Recreate table with the final schema and copy data.
        print("Recreating table to rename 'validation_status' to 'status' and add columns...")

        # Create the new table with the complete, correct schema
        final_columns_sql = ", ".join([f'\"{k}\" {v}' for k, v in FINAL_SCHEMA.items()])
        create_sql = f"CREATE TABLE validations_new ({final_columns_sql})"
        print(f"Executing: {create_sql}")
        cursor.execute(create_sql)

        # Build the mapping of columns for the data copy.
        # The key is the new column name, the value is the old source.
        # We map 'status' to be populated from 'validation_status'.
        column_mapping = {
            "job_id": "job_id",
            "user_type": "user_type",
            "citation_count": "citation_count",
            "status": "validation_status", # The critical rename/mapping
            "created_at": "created_at",
            "results_gated": "results_gated",
            "gated_at": "gated_at",
            "results_ready_at": "results_ready_at",
            "results_revealed_at": "results_revealed_at",
            "time_to_reveal_seconds": "time_to_reveal_seconds",
            "gated_outcome": "gated_outcome",
            "error_message": "error_message"
        }
        
        new_cols = ", ".join(column_mapping.keys())
        old_cols = ", ".join(column_mapping.values())

        # Copy data from the old table to the new one
        copy_sql = f"INSERT INTO validations_new ({new_cols}) SELECT {old_cols} FROM validations"
        print(f"Executing: {copy_sql}")
        cursor.execute(copy_sql)

        # Drop the old table
        print("Dropping old 'validations' table...")
        cursor.execute("DROP TABLE validations")

        # Rename the new table to the original name
        print("Renaming 'validations_new' to 'validations'...")
        cursor.execute("ALTER TABLE validations_new RENAME TO validations")

        # Step 3: Commit the transaction
        print("Committing transaction...")
        cursor.execute("COMMIT")

        print("\nMigration successful!")
        final_cols_check = get_table_info(cursor, 'validations')
        print(f"Final columns: {final_cols_check}")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Rolling back transaction...")
        cursor.execute("ROLLBACK")
        sys.exit(1)
    finally:
        conn.close()
        print("Database connection closed.")

if __name__ == "__main__":
    # Add a confirmation step for safety
    print("This script will modify the database schema.")
    print(f"TARGET DATABASE: {os.path.abspath(DB_PATH)}")
    response = input("Are you sure you want to continue? (y/n): ")
    if response.lower() == 'y':
        migrate()
    else:
        print("Migration cancelled.")
