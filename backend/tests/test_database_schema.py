import pytest
import sqlite3
import tempfile
import os
from pathlib import Path

# Add the backend directory to the path so we can import modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import init_db, DB_PATH


def test_init_db_creates_database_file():
    """Test that init_db() creates the database file"""
    # Use a temporary database file for testing
    test_db_path = tempfile.mktemp(suffix='.db')

    # Override the DB_PATH for this test
    original_db_path = DB_PATH
    import database
    database.DB_PATH = test_db_path

    try:
        # Ensure database doesn't exist initially
        assert not os.path.exists(test_db_path)

        # Initialize database
        init_db()

        # Check that database file was created
        assert os.path.exists(test_db_path)

    finally:
        # Restore original DB_PATH and clean up
        database.DB_PATH = original_db_path
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)


def test_users_table_schema():
    """Test that users table exists with correct columns"""
    # Use a temporary database file for testing
    test_db_path = tempfile.mktemp(suffix='.db')

    # Override the DB_PATH for this test
    original_db_path = DB_PATH
    import database
    database.DB_PATH = test_db_path

    try:
        # Initialize database
        init_db()

        # Connect and check table schema
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Get table info
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()

        # Close connection
        conn.close()

        # Check that table has correct columns
        column_names = [col[1] for col in columns]
        expected_columns = ['token', 'credits', 'created_at']

        assert len(columns) == 3, f"Expected 3 columns, got {len(columns)}"
        assert all(col in column_names for col in expected_columns), f"Missing columns. Expected: {expected_columns}, Got: {column_names}"

        # Check that token is PRIMARY KEY
        token_column = next(col for col in columns if col[1] == 'token')
        assert token_column[5] == 1, "token column should be PRIMARY KEY"

        # Check that credits has default value 0
        credits_column = next(col for col in columns if col[1] == 'credits')
        assert credits_column[4] == '0', f"credits column should have default value '0', got '{credits_column[4]}'"

    finally:
        # Restore original DB_PATH and clean up
        database.DB_PATH = original_db_path
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)


def test_orders_table_schema():
    """Test that orders table exists with correct columns"""
    # Use a temporary database file for testing
    test_db_path = tempfile.mktemp(suffix='.db')

    # Override the DB_PATH for this test
    original_db_path = DB_PATH
    import database
    database.DB_PATH = test_db_path

    try:
        # Initialize database
        init_db()

        # Connect and check table schema
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Get table info
        cursor.execute("PRAGMA table_info(orders)")
        columns = cursor.fetchall()

        # Close connection
        conn.close()

        # Check that table has correct columns
        column_names = [col[1] for col in columns]
        expected_columns = ['order_id', 'token', 'credits_granted', 'created_at']

        assert len(columns) == 4, f"Expected 4 columns, got {len(columns)}"
        assert all(col in column_names for col in expected_columns), f"Missing columns. Expected: {expected_columns}, Got: {column_names}"

        # Check that order_id is PRIMARY KEY
        order_id_column = next(col for col in columns if col[1] == 'order_id')
        assert order_id_column[5] == 1, "order_id column should be PRIMARY KEY"

    finally:
        # Restore original DB_PATH and clean up
        database.DB_PATH = original_db_path
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)


def test_foreign_key_constraint():
    """Test that foreign key constraint works between orders and users tables"""
    # Use a temporary database file for testing
    test_db_path = tempfile.mktemp(suffix='.db')

    # Override the DB_PATH for this test
    original_db_path = DB_PATH
    import database
    database.DB_PATH = test_db_path

    try:
        # Initialize database
        init_db()

        # Connect and test foreign key constraint
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")

        # Try to insert an order with a non-existent token (should fail)
        try:
            cursor.execute(
                "INSERT INTO orders (order_id, token, credits_granted) VALUES (?, ?, ?)",
                ("test_order", "nonexistent_token", 1000)
            )
            conn.commit()
            assert False, "Foreign key constraint should have prevented insert"
        except sqlite3.IntegrityError:
            # Expected behavior - foreign key constraint worked
            pass

        # Close connection
        conn.close()

    finally:
        # Restore original DB_PATH and clean up
        database.DB_PATH = original_db_path
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])