#!/usr/bin/env python3
import sqlite3
import os
from datetime import datetime

db_path = 'dashboard/data/validations.db'
print('Running manual citations_text migration...')

# Create backup first
backup_file = f'{db_path}.manual_migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
print(f'Creating backup: {backup_file}')
import shutil
shutil.copy2(db_path, backup_file)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if column exists
    cursor.execute('PRAGMA table_info(validations)')
    columns = [col[1] for col in cursor.fetchall()]

    if 'citations_text' in columns:
        print('citations_text column already exists')
    else:
        print('Adding citations_text column...')
        cursor.execute('ALTER TABLE validations ADD COLUMN citations_text TEXT')

        # Create index
        print('Creating citations_text index...')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_citations_text
            ON validations(citations_text)
            WHERE citations_text IS NOT NULL AND length(citations_text) > 0
        ''')

        conn.commit()
        print('citations_text column added successfully')

    # Verify
    cursor.execute('PRAGMA table_info(validations)')
    columns = [col[1] for col in cursor.fetchall()]

    if 'citations_text' in columns:
        print('Migration verified - citations_text column exists')
    else:
        print('Migration failed')
        raise Exception('Column not added')

    conn.close()

    print('Manual migration completed successfully')

except Exception as e:
    print(f'Manual migration failed: {e}')
    print(f'Restoring from backup: {backup_file}')
    shutil.copy2(backup_file, db_path)