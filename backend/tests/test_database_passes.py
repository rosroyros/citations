"""
Unit tests for pass management database functions.

Coverage requirements:
- 100% line coverage on all DB functions
- All Oracle feedback scenarios tested
- All edge cases verified

Oracle Feedback tested:
- #1: Atomic daily usage increment (race conditions)
- #6: Webhook idempotency (duplicate order_id)
- #10: Time-based expiration (mocked clocks)
- #15: Pass extension logic (add days, don't replace)
"""

import pytest
import sqlite3
import time
import threading
from unittest.mock import patch
from pathlib import Path

# Import functions to test
from database import (
    try_increment_daily_usage,
    add_pass,
    get_active_pass,
    get_daily_usage_for_current_window,
    get_db_path
)
from pricing_config import get_next_utc_midnight

# Test database setup
TEST_DB = Path(__file__).parent / 'test_credits.db'

@pytest.fixture(autouse=True)
def setup_test_db():
    """Create clean test database before each test."""
    # Override DB_PATH for testing by patching get_db_path
    import database
    original_get_db_path = database.get_db_path
    database.get_db_path = lambda: str(TEST_DB)

    # Create tables
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            token TEXT PRIMARY KEY,
            credits INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            token TEXT NOT NULL,
            credits_granted INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pass_days INTEGER,
            pass_type TEXT,
            FOREIGN KEY (token) REFERENCES users(token)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_passes (
            token TEXT PRIMARY KEY,
            expiration_timestamp INTEGER NOT NULL,
            pass_type TEXT NOT NULL,
            purchase_date INTEGER NOT NULL,
            order_id TEXT UNIQUE NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_usage (
            token TEXT NOT NULL,
            reset_timestamp INTEGER NOT NULL,
            citations_count INTEGER DEFAULT 0,
            PRIMARY KEY (token, reset_timestamp)
        )
    """)

    conn.commit()
    conn.close()

    yield

    # Cleanup
    database.get_db_path = original_get_db_path
    if TEST_DB.exists():
        TEST_DB.unlink()


class TestDailyUsageIncrement:
    """Test try_increment_daily_usage() - Oracle Feedback #1 (race conditions)."""

    def test_increment_from_zero(self):
        """First increment of the day."""
        result = try_increment_daily_usage('user1', 50)

        assert result['success'] is True
        assert result['used_before'] == 0
        assert result['used_after'] == 50
        assert result['remaining'] == 950
        assert 'reset_timestamp' in result

    def test_increment_sequential(self):
        """Multiple sequential increments under limit."""
        try_increment_daily_usage('user1', 100)
        result = try_increment_daily_usage('user1', 200)

        assert result['success'] is True
        assert result['used_before'] == 100
        assert result['used_after'] == 300
        assert result['remaining'] == 700

    def test_increment_exactly_1000(self):
        """Increment exactly to limit."""
        try_increment_daily_usage('user1', 900)
        result = try_increment_daily_usage('user1', 100)

        assert result['success'] is True
        assert result['used_after'] == 1000
        assert result['remaining'] == 0

    def test_increment_over_limit(self):
        """Increment that would exceed limit is rejected."""
        try_increment_daily_usage('user1', 950)
        result = try_increment_daily_usage('user1', 60)

        assert result['success'] is False
        assert result['used_before'] == 950
        assert result['remaining'] == 50
        assert 'used_after' not in result  # Rejected, so no after value

    def test_increment_1001_rejected(self):
        """Cannot use 1001 citations in one day."""
        try_increment_daily_usage('user1', 1000)
        result = try_increment_daily_usage('user1', 1)

        assert result['success'] is False
        assert result['remaining'] == 0

    @pytest.mark.slow
    def test_concurrent_increments_atomic(self):
        """
        Oracle Feedback #1 CRITICAL: Atomic increment prevents race conditions.

        Without BEGIN IMMEDIATE:
        - Thread A reads 950
        - Thread B reads 950
        - Thread A writes 990 (950 + 40)
        - Thread B writes 1010 (950 + 60)
        - Result: 1010 citations used (exceeds daily limit)

        With BEGIN IMMEDIATE:
        - One thread locks, other waits
        - Only the 40-citation request succeeds (990 total)
        - The 60-citation request fails (would exceed limit)
        """
        # Setup: User has 950 citations used
        try_increment_daily_usage('user1', 950)

        results = []

        def try_increment(citations):
            result = try_increment_daily_usage('user1', citations)
            results.append(result)

        # Two threads try to use different amounts
        # One asks for 40 (should succeed: 950 + 40 = 990)
        # One asks for 60 (should fail: 950 + 60 = 1010)
        t1 = threading.Thread(target=try_increment, args=(40,))
        t2 = threading.Thread(target=try_increment, args=(60,))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Verify: Exactly one succeeded, one failed
        successes = [r for r in results if r['success']]
        failures = [r for r in results if not r['success']]

        assert len(successes) == 1, f"Exactly one request should succeed, got {len(successes)}. Results: {results}"
        assert len(failures) == 1, f"Exactly one request should fail, got {len(failures)}. Results: {results}"

        # Verify: Final usage is 990 (950 + 40), not 1010 or 1070
        final_usage = get_daily_usage_for_current_window('user1')
        assert final_usage == 990

    def test_different_users_independent(self):
        """Different users have independent daily limits."""
        try_increment_daily_usage('user1', 800)
        try_increment_daily_usage('user2', 900)

        result1 = try_increment_daily_usage('user1', 150)
        result2 = try_increment_daily_usage('user2', 90)

        assert result1['success'] is True
        assert result1['used_after'] == 950

        assert result2['success'] is True
        assert result2['used_after'] == 990


class TestPassManagement:
    """Test add_pass() and get_active_pass() - Oracle #6, #10, #15."""

    def test_grant_new_pass(self):
        """Grant pass to user who doesn't have one."""
        now = int(time.time())

        result = add_pass('user1', 7, '7day', 'order123')

        assert result is True

        pass_info = get_active_pass('user1')
        assert pass_info is not None
        assert pass_info['pass_type'] == '7day'
        assert pass_info['expiration_timestamp'] >= now + (7 * 86400)
        assert pass_info['hours_remaining'] >= 7 * 24 - 1  # ~7 days

    def test_pass_expiration_1day(self):
        """1-day pass expires after 24 hours."""
        now = int(time.time())
        add_pass('user1', 1, '1day', 'order1')

        pass_info = get_active_pass('user1')
        expected_exp = now + 86400

        # Allow 1 second tolerance for test execution time
        assert abs(pass_info['expiration_timestamp'] - expected_exp) <= 1

    @patch('time.time')
    def test_pass_expiration_after_duration(self, mock_time):
        """
        Oracle Feedback #10: Fast-forward clock test.

        Verify pass expires after duration.
        """
        # Given: Grant 1-day pass at t=0
        start_time = 1704067200  # Jan 1, 2024 00:00 UTC
        mock_time.return_value = start_time

        add_pass('user1', 1, '1day', 'order1')
        assert get_active_pass('user1') is not None

        # When: Fast-forward 23 hours (still valid)
        mock_time.return_value = start_time + (23 * 3600)
        assert get_active_pass('user1') is not None

        # When: Fast-forward 25 hours (expired)
        mock_time.return_value = start_time + (25 * 3600)
        assert get_active_pass('user1') is None

    def test_webhook_idempotency_same_order(self):
        """
        Oracle Feedback #6 CRITICAL: Webhook idempotency.

        Processing same order_id twice doesn't double-grant.
        """
        now = int(time.time())

        # First webhook delivery
        add_pass('user1', 7, '7day', 'order123')
        pass1 = get_active_pass('user1')
        initial_exp = pass1['expiration_timestamp']

        # Second webhook delivery (duplicate)
        time.sleep(0.1)  # Small delay to simulate network retry
        add_pass('user1', 7, '7day', 'order123')  # SAME order_id
        pass2 = get_active_pass('user1')

        # Verify: Expiration UNCHANGED (not extended by 7 more days)
        assert pass2['expiration_timestamp'] == initial_exp

    def test_pass_extension_same_type(self):
        """
        Oracle Feedback #15: Pass extension - add days, don't replace.

        User has 7-day pass with 3 days left, buys another 7-day pass.
        Result: 10 days total (3 + 7), not 7 days.
        """
        now = int(time.time())

        # Grant 7-day pass
        add_pass('user1', 7, '7day', 'order1')
        pass1 = get_active_pass('user1')

        # Fast-forward 4 days (3 days remaining)
        # We can't actually fast-forward, so we'll manually set expiration
        conn = sqlite3.connect(TEST_DB)
        cursor = conn.cursor()
        three_days_from_now = now + (3 * 86400)
        cursor.execute("""
            UPDATE user_passes
            SET expiration_timestamp = ?, purchase_date = ?
            WHERE token = ?
        """, (three_days_from_now, now - (4 * 86400), 'user1'))
        conn.commit()
        conn.close()

        # Buy another 7-day pass (different order_id)
        add_pass('user1', 7, '7day', 'order2')

        pass2 = get_active_pass('user1')
        expected_exp = three_days_from_now + (7 * 86400)  # 3 + 7 = 10 days

        assert abs(pass2['expiration_timestamp'] - expected_exp) <= 1

    def test_pass_extension_different_type(self):
        """
        Oracle Feedback #15: Extension works across different pass types.

        User has 1-day pass with 12 hours left, buys 30-day pass.
        Result: 30.5 days total, not 30 days.
        """
        now = int(time.time())

        # Manually insert 1-day pass expiring in 12 hours
        twelve_hours_from_now = now + (12 * 3600)
        conn = sqlite3.connect(TEST_DB)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_passes
            (token, expiration_timestamp, pass_type, purchase_date, order_id)
            VALUES (?, ?, ?, ?, ?)
        """, ('user1', twelve_hours_from_now, '1day', now - (12 * 3600), 'order1'))
        conn.commit()
        conn.close()

        # Buy 30-day pass
        add_pass('user1', 30, '30day', 'order2')

        pass_info = get_active_pass('user1')
        expected_exp = twelve_hours_from_now + (30 * 86400)

        assert abs(pass_info['expiration_timestamp'] - expected_exp) <= 1
        assert pass_info['pass_type'] == '30day'  # Type updated

    def test_no_active_pass_returns_none(self):
        """User with no pass returns None."""
        result = get_active_pass('user_never_purchased')
        assert result is None

    @patch('time.time')
    def test_expired_pass_returns_none(self, mock_time):
        """Expired pass is not considered active."""
        # Grant pass at t=0
        start_time = 1704067200
        mock_time.return_value = start_time
        add_pass('user1', 1, '1day', 'order1')

        # Check after expiration
        mock_time.return_value = start_time + (2 * 86400)  # 2 days later
        result = get_active_pass('user1')
        assert result is None


class TestDailyUsageQuery:
    """Test get_daily_usage_for_current_window()."""

    def test_no_usage_returns_zero(self):
        """User with no usage returns 0."""
        result = get_daily_usage_for_current_window('new_user')
        assert result == 0

    def test_returns_current_window_usage(self):
        """Returns usage for current UTC day window."""
        try_increment_daily_usage('user1', 150)
        result = get_daily_usage_for_current_window('user1')
        assert result == 150

    def test_ignores_old_window_usage(self):
        """Usage from previous day window is ignored."""
        # Insert old usage manually
        reset_timestamp = get_next_utc_midnight()
        yesterday_reset = reset_timestamp - 86400

        conn = sqlite3.connect(TEST_DB)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO daily_usage (token, reset_timestamp, citations_count)
            VALUES (?, ?, ?)
        """, ('user1', yesterday_reset, 500))
        conn.commit()
        conn.close()

        # Current window should be 0
        result = get_daily_usage_for_current_window('user1')
        assert result == 0


class TestDatabaseErrors:
    """Test error handling coverage."""

    def test_increment_exception_handling(self):
        """Test generic exception inside try_increment_daily_usage try block."""
        # We need connect to succeed, but execute to fail inside the try block
        with patch('database.sqlite3.connect') as mock_connect:
            mock_cursor = mock_connect.return_value.cursor.return_value
            # Fail on BEGIN IMMEDIATE which is inside the try block
            mock_cursor.execute.side_effect = Exception("Transaction Failed")
            
            with pytest.raises(Exception) as exc:
                try_increment_daily_usage('user1', 50)
            assert "Transaction Failed" in str(exc.value)

    def test_add_pass_integrity_error_race_condition(self):
        """
        Test IntegrityError in add_pass (simulates race condition).
        This covers the 'except sqlite3.IntegrityError' block.
        """
        # We need to let the first part succeed (SELECT 1...) but fail on INSERT
        
        def side_effect_execute(sql, *args):
            # Raise error on the order insertion
            if "INSERT INTO orders" in sql:
                raise sqlite3.IntegrityError("UNIQUE constraint failed: orders.order_id")
            return None

        with patch('database.sqlite3.connect') as mock_connect:
            mock_conn = mock_connect.return_value
            mock_cursor = mock_conn.cursor.return_value
            
            # Setup: order does NOT exist yet (so first check passes)
            mock_cursor.fetchone.return_value = None
            
            # When INSERT happens, raise IntegrityError
            mock_cursor.execute.side_effect = side_effect_execute
            
            # Call function
            result = add_pass('user1', 7, '7day', 'order_race')
            
            # Should return True (handled as success)
            assert result is True

    def test_add_pass_generic_exception(self):
        """Test generic exception inside add_pass try block."""
        with patch('database.sqlite3.connect') as mock_connect:
            mock_cursor = mock_connect.return_value.cursor.return_value
            # Fail on BEGIN IMMEDIATE
            mock_cursor.execute.side_effect = Exception("Generic Failure")
            
            with pytest.raises(Exception):
                add_pass('user1', 7, '7day', 'order1')

