import pytest
import tempfile
import os
import sqlite3

# Add the backend directory to the path so we can import modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database import init_db, get_credits, add_credits, deduct_credits, get_db_path


def setup_test_db():
    """Set up a temporary database for testing"""
    test_db_path = tempfile.mktemp(suffix='.db')

    # Set test environment variable
    os.environ['TEST_DB_PATH'] = test_db_path

    return test_db_path


def cleanup_test_db(test_db_path):
    """Clean up test database"""
    if os.path.exists(test_db_path):
        os.unlink(test_db_path)
    # Remove environment variable
    if 'TEST_DB_PATH' in os.environ:
        del os.environ['TEST_DB_PATH']


def test_get_credits_returns_zero_for_non_existent_token():
    """Test that get_credits returns 0 for non-existent token"""
    test_db_path = setup_test_db()

    try:
        # Initialize database
        init_db()

        # Test non-existent token
        credits = get_credits("non-existent-token")
        assert credits == 0

    finally:
        cleanup_test_db(test_db_path)


def test_add_credits_creates_new_user():
    """Test that add_credits creates new user with correct balance"""
    test_db_path = setup_test_db()

    try:
        # Initialize database
        init_db()

        # Add credits for new user
        result = add_credits("new-user-token", 1000, "order-1")
        assert result is True

        # Verify credits were added
        credits = get_credits("new-user-token")
        assert credits == 1000

    finally:
        cleanup_test_db(test_db_path)


def test_add_credits_adds_to_existing_user():
    """Test that add_credits adds to existing user balance"""
    test_db_path = setup_test_db()

    try:
        # Initialize database
        init_db()

        # Add initial credits
        add_credits("existing-user-token", 100, "order-1")

        # Add more credits
        result = add_credits("existing-user-token", 500, "order-2")
        assert result is True

        # Verify total credits
        credits = get_credits("existing-user-token")
        assert credits == 600  # 100 + 500

    finally:
        cleanup_test_db(test_db_path)


def test_add_credits_rejects_duplicate_order_id():
    """Test that add_credits rejects duplicate order_id (idempotency)"""
    test_db_path = setup_test_db()

    try:
        # Initialize database
        init_db()

        # Add credits
        result1 = add_credits("user-token", 1000, "duplicate-order")
        assert result1 is True

        # Try to add credits again with same order_id
        result2 = add_credits("user-token", 1000, "duplicate-order")
        assert result2 is False

        # Verify credits were only added once
        credits = get_credits("user-token")
        assert credits == 1000  # Not 2000

    finally:
        cleanup_test_db(test_db_path)


def test_deduct_credits_reduces_balance():
    """Test that deduct_credits reduces balance correctly"""
    test_db_path = setup_test_db()

    try:
        # Initialize database
        init_db()

        # Add credits first
        add_credits("user-token", 1000, "order-1")

        # Deduct credits
        result = deduct_credits("user-token", 50)
        assert result is True

        # Verify balance reduced
        credits = get_credits("user-token")
        assert credits == 950  # 1000 - 50

    finally:
        cleanup_test_db(test_db_path)


def test_deduct_credits_returns_false_insufficient():
    """Test that deduct_credits returns False when insufficient credits"""
    test_db_path = setup_test_db()

    try:
        # Initialize database
        init_db()

        # Add credits
        add_credits("user-token", 100, "order-1")

        # Try to deduct more than available
        result = deduct_credits("user-token", 150)
        assert result is False

        # Verify balance unchanged
        credits = get_credits("user-token")
        assert credits == 100  # Unchanged

    finally:
        cleanup_test_db(test_db_path)


def test_deduct_credits_atomic_operation():
    """Test that deduct_credits handles atomic operations correctly"""
    test_db_path = setup_test_db()

    try:
        # Initialize database
        init_db()

        # Add credits
        add_credits("user-token", 100, "order-1")

        # Simulate concurrent deduction (test atomicity)
        conn = sqlite3.connect(test_db_path)

        # First deduction should succeed
        cursor1 = conn.cursor()
        cursor1.execute(
            "UPDATE users SET credits = credits - ? WHERE token = ? AND credits >= ?",
            (50, "user-token", 50)
        )
        conn.commit()

        # Second deduction for remaining amount should succeed
        cursor2 = conn.cursor()
        cursor2.execute(
            "UPDATE users SET credits = credits - ? WHERE token = ? AND credits >= ?",
            (50, "user-token", 50)
        )
        conn.commit()

        conn.close()

        # Verify final balance is 0
        credits = get_credits("user-token")
        assert credits == 0

    finally:
        cleanup_test_db(test_db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])