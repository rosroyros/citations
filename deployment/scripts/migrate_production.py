#!/usr/bin/env python3
"""
Production migration script for citations_text column
Uses the existing DatabaseManager to perform the migration safely
"""
import sys
import os
import shutil
from datetime import datetime

# Add dashboard to path
sys.path.append('dashboard')
from database import DatabaseManager

def migrate_citations_column():
    """Safely migrate the citations_text column"""

    db_path = 'dashboard/data/validations.db'

    print("🗄️ Starting citations_text column migration...")

    # Check if database exists
    if not os.path.exists(db_path):
        print("⚠️ Database not found - will be created with citations_text column")
        return True

    print(f"✅ Database found: {db_path}")

    # Create backup
    backup_file = f"{db_path}.pre_citations_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"📦 Creating backup: {backup_file}")
    shutil.copy2(db_path, backup_file)

    try:
        # Use DatabaseManager which has built-in migration logic
        print("🔄 Running migration using DatabaseManager...")
        with DatabaseManager(db_path) as db:
            # The DatabaseManager automatically runs _create_schema() which includes the migration
            schema = db.get_table_schema('validations')

            # Verify citations_text column exists
            citations_col = any('citations_text' in col for col in schema)
            if not citations_col:
                print("❌ Migration failed - citations_text column not found")
                return False

            print("✅ citations_text column successfully added")

            # Verify indexes
            indexes = db.get_indexes()
            citations_index = any('citations_text' in idx for idx in indexes)
            if citations_index:
                print("✅ citations_text index exists")
            else:
                print("⚠️ citations_text index missing")

            # Test insertion
            print("🧪 Testing citations_text insertion...")
            import uuid
            test_job_id = f"migration_test_{uuid.uuid4().hex[:8]}"

            test_data = {
                'job_id': test_job_id,
                'created_at': '2025-11-28T10:00:00Z',
                'user_type': 'test',
                'status': 'completed',
                'citations_text': 'Test citation for migration verification'
            }

            db.insert_validation(test_data)

            # Verify insertion worked
            result = db.get_validation(test_job_id)
            if result and result.get('citations_text') == test_data['citations_text']:
                print("✅ citations_text insertion test passed")
                # Clean up test record
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM validations WHERE job_id = ?", (test_job_id,))
                conn.commit()
                conn.close()
            else:
                print("❌ citations_text insertion test failed")
                return False

            # Get final stats
            print("📊 Post-migration database stats:")
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM validations")
            record_count = cursor.fetchone()[0]
            print(f"   Records: {record_count}")
            conn.close()

            print("📋 Final schema:")
            for col in schema:
                print(f"   {col}")

        print("✅ Migration completed successfully!")
        print(f"📦 Backup file: {backup_file}")
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print(f"🔄 Restoring from backup: {backup_file}")
        shutil.copy2(backup_file, db_path)
        return False

if __name__ == "__main__":
    success = migrate_citations_column()
    if success:
        print("\n🎉 Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)