import sqlite3
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from backend.database import get_validations_db_path

def migrate_schema():
    db_path = get_validations_db_path()
    print(f"Migrating database at: {db_path}")
    
    if not os.path.exists(db_path):
        print("Database file not found. Creating new database...")
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Ensure table exists first (in case of fresh install)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS validations (
            job_id TEXT PRIMARY KEY,
            user_type TEXT,
            citation_count INTEGER,
            status TEXT,
            validation_status TEXT,
            paid_user_id TEXT,
            free_user_id TEXT,
            is_test_job BOOLEAN,
            created_at TIMESTAMP,
            error_message TEXT
        )
    ''')
    
    # Columns to add
    new_columns = {
        'experiment_variant': 'TEXT',
        'product_id': 'TEXT',
        'amount_cents': 'INTEGER',
        'currency': 'TEXT',
        'order_id': 'TEXT'
    }
    
    # Get existing columns
    cursor.execute("PRAGMA table_info(validations)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    for col_name, col_type in new_columns.items():
        if col_name not in existing_columns:
            print(f"Adding column: {col_name} ({col_type})")
            try:
                cursor.execute(f"ALTER TABLE validations ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError as e:
                print(f"Error adding column {col_name}: {e}")
        else:
            print(f"Column {col_name} already exists.")
            
    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate_schema()
