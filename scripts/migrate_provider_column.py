import sqlite3
import os
import sys

# Add backend directory to path to locate database module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from database import get_validations_db_path
except ImportError:
    # Fallback if running directly from scripts dir without backend in path
    def get_validations_db_path():
        return os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'backend', 'dashboard', 'data', 'validations.db'
        )

def migrate():
    db_path = get_validations_db_path()
    print(f"Migrating database at: {db_path}")

    if not os.path.exists(db_path):
        print("Database not found! Skipping migration.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(validations)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'provider' in columns:
            print("Column 'provider' already exists. Skipping.")
        else:
            print("Adding 'provider' column...")
            cursor.execute("ALTER TABLE validations ADD COLUMN provider TEXT")
            conn.commit()
            print("Migration successful: Added 'provider' column.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
