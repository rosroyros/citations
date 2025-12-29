import pytest
import os
import sqlite3
from fastapi.testclient import TestClient


@pytest.fixture
def test_db():
    """Create a fresh test database for each test."""
    test_db_path = 'test_credits_temp.db'

    # Remove if exists
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    # Create tables matching production schema
    conn = sqlite3.connect(test_db_path)
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('''
        CREATE TABLE users (
            token TEXT PRIMARY KEY,
            credits INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE orders (
            order_id TEXT PRIMARY KEY,
            token TEXT NOT NULL,
            credits_granted INTEGER NOT NULL,
            pass_days INTEGER,
            pass_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (token) REFERENCES users(token)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_passes (
            token TEXT PRIMARY KEY,
            expiration_timestamp INTEGER NOT NULL,
            pass_type TEXT NOT NULL,
            purchase_date INTEGER NOT NULL,
            order_id TEXT UNIQUE NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS daily_usage (
            token TEXT NOT NULL,
            reset_timestamp INTEGER NOT NULL,
            citations_count INTEGER DEFAULT 0,
            PRIMARY KEY (token, reset_timestamp)
        )
    ''')
    conn.commit()
    conn.close()

    yield test_db_path

    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture
def client(test_db, monkeypatch):
    """Create TestClient with database path overridden."""
    # Override the database path BEFORE importing app
    monkeypatch.setenv('TEST_DB_PATH', test_db)

    from app import app
    return TestClient(app)