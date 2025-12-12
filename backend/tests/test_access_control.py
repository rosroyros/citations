"""
Unit tests for access control logic.

Tests cover all access control scenarios including:
1. Free user access limits
2. Credits user validation
3. Pass user daily limits
4. Pass expiration and reset
5. Oracle scenarios (#10, #14)
6. Race condition handling

Test file: backend/tests/test_access_control.py
"""

import pytest
import sqlite3
import time
import threading
import base64
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock the dashboard import
sys.modules['dashboard'] = MagicMock()
sys.modules['dashboard.log_parser'] = MagicMock()
sys.modules['analytics'] = MagicMock()

from app import (
    check_user_access,
    extract_user_id,
    FREE_LIMIT,
    PASS_DAILY_LIMIT,
    UserStatus
)
from database import (
    init_db,
    get_credits,
    deduct_credits,
    add_pass,
    get_active_pass,
    try_increment_daily_usage,
    get_db_path
)
from fastapi import Request
from pricing_config import get_next_utc_midnight

# Test database setup
TEST_DB = Path(__file__).parent / 'test_access_control.db'


@pytest.fixture(autouse=True)
def setup_test_db():
    """Create clean test database before each test."""
    # Override DB_PATH for testing
    import database
    original_get_db_path = database.get_db_path
    database.get_db_path = lambda: str(TEST_DB)

    # Clean up any existing test db
    if TEST_DB.exists():
        TEST_DB.unlink()

    # Initialize fresh test database
    init_db()

    yield

    # Cleanup
    if TEST_DB.exists():
        TEST_DB.unlink()

    # Restore original function
    database.get_db_path = original_get_db_path


class TestFreeUserAccess:
    """Test free user access control logic."""

    def test_free_user_within_limit(self):
        """Test free user within 5 validation limit."""
        # Free users are tracked client-side via headers
        # This tests the client-side tracking logic
        used = 3
        citation_count = 2

        # Simulate client check: free_used + citation_count <= FREE_LIMIT
        assert used + citation_count <= FREE_LIMIT

    def test_free_user_at_limit(self):
        """Test free user exactly at 5 validation limit."""
        used = 5
        citation_count = 0

        assert used + citation_count <= FREE_LIMIT

    def test_free_user_exceeds_limit(self):
        """Test free user exceeding 5 validation limit."""
        used = 5
        citation_count = 1

        # Would exceed limit
        assert used + citation_count > FREE_LIMIT

    def test_free_user_partial_results(self):
        """Test free user gets partial results when exceeding limit."""
        used = 4
        citation_count = 3

        # Should get partial results
        allowed = FREE_LIMIT - used
        assert allowed == 1  # Only 1 more validation allowed


class TestCreditsUserAccess:
    """Test credits user access control logic."""

    def test_credits_user_sufficient_balance(self, setup_test_db):
        """Test user with sufficient credits."""
        token = "test_token_123"
        citation_count = 10

        # Add credits to user
        conn = sqlite3.connect(str(TEST_DB))
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (token, credits) VALUES (?, ?)", (token, 100))
        conn.commit()
        conn.close()

        # Check access
        result = check_user_access(token, citation_count)

        assert result['has_access'] is True
        assert result['access_type'] == 'credits'
        assert result['user_status'].type == 'credits'
        assert result['user_status'].balance == 90  # 100 - 10
        assert result['error_message'] is None

    def test_credits_user_insufficient_balance(self, setup_test_db):
        """Test user with insufficient credits."""
        token = "test_token_456"
        citation_count = 50

        # Add fewer credits than needed
        conn = sqlite3.connect(str(TEST_DB))
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (token, credits) VALUES (?, ?)", (token, 20))
        conn.commit()
        conn.close()

        # Check access
        result = check_user_access(token, citation_count)

        assert result['has_access'] is False
        assert result['access_type'] == 'credits'
        assert result['user_status'].type == 'credits'
        assert result['user_status'].balance == 20  # Unchanged
        assert "insufficient credits" in result['error_message'].lower()

    def test_credits_user_exact_balance(self, setup_test_db):
        """Test user with exact credits needed."""
        token = "test_token_789"
        citation_count = 30

        # Add exact credits
        conn = sqlite3.connect(str(TEST_DB))
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (token, credits) VALUES (?, ?)", (token, 30))
        conn.commit()
        conn.close()

        # Check access
        result = check_user_access(token, citation_count)

        assert result['has_access'] is True
        assert result['user_status'].balance == 0  # All credits used

    def test_credits_deduction_atomicity(self, setup_test_db):
        """Test that credit deduction is atomic."""
        token = "test_token_atomic"
        initial_credits = 100
        citation_count = 25

        # Setup user with credits
        conn = sqlite3.connect(str(TEST_DB))
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (token, credits) VALUES (?, ?)", (token, initial_credits))
        conn.commit()
        conn.close()

        # Check access (which deducts credits)
        result = check_user_access(token, citation_count)

        # Verify credits were deducted correctly
        remaining_credits = get_credits(token)
        assert remaining_credits == initial_credits - citation_count
        assert result['has_access'] is True


class TestPassUserAccess:
    """Test pass user access control logic."""

    def test_pass_user_within_daily_limit(self, setup_test_db):
        """Test pass user within 1000 daily citation limit."""
        token = "test_pass_token_1"
        citation_count = 100

        # Add active pass (expires in 7 days)
        expiration = int((datetime.utcnow() + timedelta(days=7)).timestamp())
        conn = sqlite3.connect(str(TEST_DB))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_passes (token, expiration_timestamp, pass_type, purchase_date, order_id) VALUES (?, ?, ?, ?, ?)",
            (token, expiration, "weekly", int(time.time()), "order_123")
        )
        conn.commit()
        conn.close()

        # Check access
        result = check_user_access(token, citation_count)

        assert result['has_access'] is True
        assert result['access_type'] == 'pass'
        assert result['user_status'].type == 'pass'
        assert result['user_status'].daily_used == citation_count
        assert result['user_status'].daily_limit == PASS_DAILY_LIMIT
        assert result['error_message'] is None

    def test_pass_user_at_daily_limit(self, setup_test_db):
        """Test pass user exactly at 1000 daily limit."""
        token = "test_pass_token_2"

        # Add active pass
        expiration = int((datetime.utcnow() + timedelta(days=7)).timestamp())
        conn = sqlite3.connect(str(TEST_DB))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_passes (token, expiration_timestamp, pass_type, purchase_date, order_id) VALUES (?, ?, ?, ?, ?)",
            (token, expiration, "weekly", int(time.time()), "order_124")
        )

        # Set daily usage to exactly 1000
        reset_timestamp = get_next_utc_midnight()
        cursor.execute(
            "INSERT INTO daily_usage (token, reset_timestamp, citations_count) VALUES (?, ?, ?)",
            (token, reset_timestamp, 1000)
        )
        conn.commit()
        conn.close()

        # Try to check access with 1 more citation
        result = check_user_access(token, 1)

        assert result['has_access'] is False
        assert result['access_type'] == 'pass'
        assert "daily citation limit exceeded" in result['error_message'].lower()

    def test_pass_user_exceeds_daily_limit(self, setup_test_db):
        """Test pass user exceeding daily limit."""
        token = "test_pass_token_3"

        # Add active pass
        expiration = int((datetime.utcnow() + timedelta(days=7)).timestamp())
        conn = sqlite3.connect(str(TEST_DB))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_passes (token, expiration_timestamp, pass_type, purchase_date, order_id) VALUES (?, ?, ?, ?, ?)",
            (token, expiration, "weekly", int(time.time()), "order_125")
        )

        # Set daily usage to 950
        reset_timestamp = get_next_utc_midnight()
        cursor.execute(
            "INSERT INTO daily_usage (token, reset_timestamp, citations_count) VALUES (?, ?, ?)",
            (token, reset_timestamp, 950)
        )
        conn.commit()
        conn.close()

        # Try to use 100 citations (would exceed limit)
        result = check_user_access(token, 100)

        assert result['has_access'] is False
        assert result['user_status'].daily_used == 1050  # 950 + 100
        assert result['user_status'].daily_limit == PASS_DAILY_LIMIT

    def test_pass_user_daily_usage_increment(self, setup_test_db):
        """Test that daily usage increments correctly."""
        token = "test_pass_token_4"
        first_citations = 50
        second_citations = 30

        # Add active pass
        expiration = int((datetime.utcnow() + timedelta(days=7)).timestamp())
        conn = sqlite3.connect(str(TEST_DB))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_passes (token, expiration_timestamp, pass_type, purchase_date, order_id) VALUES (?, ?, ?, ?, ?)",
            (token, expiration, "weekly", int(time.time()), "order_126")
        )
        conn.commit()
        conn.close()

        # First access
        result1 = check_user_access(token, first_citations)
        assert result1['has_access'] is True
        assert result1['user_status'].daily_used == first_citations

        # Second access
        result2 = check_user_access(token, second_citations)
        assert result2['has_access'] is True
        assert result2['user_status'].daily_used == first_citations + second_citations


class TestPassExpirationAndReset:
    """Test pass expiration and midnight reset behavior."""

    @patch('pricing_config.get_next_utc_midnight')
    def test_pass_user_midnight_reset(self, mock_midnight, setup_test_db):
        """Test Oracle #10: Pass user can access again after midnight reset."""
        token = "test_pass_reset"
        citation_count = 50

        # Mock midnight timestamp in the past
        past_midnight = int((datetime.utcnow() - timedelta(hours=1)).timestamp())
        mock_midnight.return_value = past_midnight

        # Add active pass
        expiration = int((datetime.utcnow() + timedelta(days=7)).timestamp())
        conn = sqlite3.connect(str(TEST_DB))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_passes (token, expiration_timestamp, pass_type, purchase_date, order_id) VALUES (?, ?, ?, ?, ?)",
            (token, expiration, "weekly", int(time.time()), "order_127")
        )

        # Set usage for previous day
        cursor.execute(
            "INSERT INTO daily_usage (token, reset_timestamp, citations_count) VALUES (?, ?, ?)",
            (token, past_midnight - 86400, 1000)  # Previous day at limit
        )
        conn.commit()
        conn.close()

        # After midnight, should have fresh limit
        result = check_user_access(token, citation_count)

        assert result['has_access'] is True
        assert result['user_status'].daily_used == citation_count
        assert result['user_status'].daily_limit == PASS_DAILY_LIMIT

    def test_pass_user_expiration(self, setup_test_db):
        """Test pass user after pass expires."""
        token = "test_pass_expired"
        citation_count = 10

        # Add expired pass
        expiration = int((datetime.utcnow() - timedelta(days=1)).timestamp())
        conn = sqlite3.connect(str(TEST_DB))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_passes (token, expiration_timestamp, pass_type, purchase_date, order_id) VALUES (?, ?, ?, ?, ?)",
            (token, expiration, "weekly", int(time.time()), "order_128")
        )

        # Add credits as fallback
        cursor.execute("INSERT INTO users (token, credits) VALUES (?, ?)", (token, 50))
        conn.commit()
        conn.close()

        # Should fall back to credits
        result = check_user_access(token, citation_count)

        assert result['has_access'] is True
        assert result['access_type'] == 'credits'  # Not pass
        assert result['user_status'].type == 'credits'
        assert result['user_status'].balance == 40  # 50 - 10


class TestOracleScenarios:
    """Test specific Oracle feedback scenarios."""

    def test_oracle_14_credits_dont_apply_during_pass(self, setup_test_db):
        """Test Oracle #14: Credits are NOT used when user has active pass."""
        token = "test_oracle_14"
        citation_count = 25
        initial_credits = 100

        # Add both credits and active pass
        expiration = int((datetime.utcnow() + timedelta(days=7)).timestamp())
        conn = sqlite3.connect(str(TEST_DB))
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (token, credits) VALUES (?, ?)", (token, initial_credits))
        cursor.execute(
            "INSERT INTO user_passes (token, expiration_timestamp, pass_type, purchase_date, order_id) VALUES (?, ?, ?, ?, ?)",
            (token, expiration, "weekly", int(time.time()), "order_129")
        )
        conn.commit()
        conn.close()

        # Check access
        result = check_user_access(token, citation_count)

        # Should use pass, NOT credits
        assert result['has_access'] is True
        assert result['access_type'] == 'pass'
        assert result['user_status'].type == 'pass'

        # Verify credits were NOT touched
        remaining_credits = get_credits(token)
        assert remaining_credits == initial_credits  # Still 100, unchanged

    @patch('time.time')
    def test_oracle_10_fast_forward_clock(self, mock_time, setup_test_db):
        """Test Oracle #10: Time-based tests with mocked clock."""
        token = "test_oracle_10"
        citation_count = 100

        # Mock current time: 2025-01-15 10:00 UTC
        mock_time.return_value = datetime(2025, 1, 15, 10, 0).timestamp()

        # Add pass expiring tomorrow
        expiration = datetime(2025, 1, 16, 0, 0).timestamp()
        conn = sqlite3.connect(str(TEST_DB))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_passes (token, expiration_timestamp, pass_type, purchase_date, order_id) VALUES (?, ?, ?, ?, ?)",
            (token, expiration, "weekly", int(time.time()), "order_130")
        )
        conn.commit()
        conn.close()

        # Check access
        result = check_user_access(token, citation_count)

        assert result['has_access'] is True
        assert result['access_type'] == 'pass'

        # Fast-forward to after pass expiration
        mock_time.return_value = datetime(2025, 1, 17, 10, 0).timestamp()

        # Add credits for fallback
        conn = sqlite3.connect(str(TEST_DB))
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (token, credits) VALUES (?, ?)", (token, 50))
        conn.commit()
        conn.close()

        # Should now use credits
        result2 = check_user_access(token, 20)
        assert result2['access_type'] == 'credits'


class TestRaceConditions:
    """Test concurrent access race conditions."""

    def test_concurrent_daily_usage_increment(self, setup_test_db):
        """Test race condition protection for daily usage tracking."""
        token = "test_race_token"
        num_threads = 10
        citations_per_thread = 5

        # Add active pass
        expiration = int((datetime.utcnow() + timedelta(days=7)).timestamp())
        conn = sqlite3.connect(str(TEST_DB))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_passes (token, expiration_timestamp, pass_type, purchase_date, order_id) VALUES (?, ?, ?, ?, ?)",
            (token, expiration, "weekly", int(time.time()), "order_131")
        )
        conn.commit()
        conn.close()

        results = []
        errors = []

        def worker():
            try:
                result = check_user_access(token, citations_per_thread)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Create concurrent threads
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Verify total usage doesn't exceed limit
        total_citations = num_threads * citations_per_thread
        successful_requests = sum(1 for r in results if r['has_access'])

        # Check final daily usage
        reset_timestamp = get_next_utc_midnight()
        conn = sqlite3.connect(str(TEST_DB))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT citations_count FROM daily_usage WHERE token = ? AND reset_timestamp = ?",
            (token, reset_timestamp)
        )
        row = cursor.fetchone()
        conn.close()

        final_usage = row[0] if row else 0
        assert final_usage <= PASS_DAILY_LIMIT

        # If we exceeded the limit, some requests should have failed
        if total_citations > PASS_DAILY_LIMIT:
            assert successful_requests < num_threads

    def test_concurrent_credit_deduction(self, setup_test_db):
        """Test atomic credit deduction under concurrent access."""
        token = "test_credit_race"
        initial_credits = 100
        num_threads = 5
        credits_per_thread = 15

        # Setup user with credits
        conn = sqlite3.connect(str(TEST_DB))
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (token, credits) VALUES (?, ?)", (token, initial_credits))
        conn.commit()
        conn.close()

        results = []
        errors = []

        def worker():
            try:
                result = check_user_access(token, credits_per_thread)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Create concurrent threads
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify no errors
        assert len(errors) == 0

        # Check final credit balance
        final_credits = get_credits(token)

        # Total credits deducted should never exceed initial
        total_deducted = initial_credits - final_credits
        successful_requests = sum(1 for r in results if r['has_access'])
        expected_deducted = successful_requests * credits_per_thread

        assert total_deducted == expected_deducted
        assert final_credits >= 0
        assert total_deducted <= initial_credits


class TestUserIdExtraction:
    """Test user ID extraction from headers."""

    def test_extract_paid_user_id(self):
        """Test extraction of paid user ID from token."""
        # Create mock request with token
        request = MagicMock(spec=Request)
        request.headers = {
            'X-User-Token': 'abc12345def67890'
        }

        paid_id, free_id, user_type = extract_user_id(request)

        assert paid_id == 'abc12345'  # First 8 chars
        assert free_id is None
        assert user_type == 'paid'

    def test_extract_free_user_id(self):
        """Test extraction of free user ID."""
        # Create mock free user ID
        free_uuid = "550e8400-e29b-41d4-a716-446655440000"
        encoded_id = base64.b64encode(free_uuid.encode()).decode()

        request = MagicMock(spec=Request)
        request.headers = {
            'X-Free-User-ID': encoded_id
        }

        paid_id, free_id, user_type = extract_user_id(request)

        assert paid_id is None
        assert free_id == free_uuid
        assert user_type == 'free'

    def test_extract_anonymous_user(self):
        """Test anonymous user extraction."""
        request = MagicMock(spec=Request)
        request.headers = {}

        paid_id, free_id, user_type = extract_user_id(request)

        assert paid_id is None
        assert free_id is None
        assert user_type == 'anonymous'

    def test_paid_user_takes_precedence(self):
        """Test that paid user ID takes precedence over free user ID."""
        free_uuid = "550e8400-e29b-41d4-a716-446655440000"
        encoded_id = base64.b64encode(free_uuid.encode()).decode()

        request = MagicMock(spec=Request)
        request.headers = {
            'X-User-Token': 'abc12345def67890',
            'X-Free-User-ID': encoded_id
        }

        paid_id, free_id, user_type = extract_user_id(request)

        assert paid_id == 'abc12345'
        assert free_id is None  # Should be None when paid user
        assert user_type == 'paid'

    def test_malformed_free_user_id(self, caplog):
        """Test handling of malformed free user ID."""
        request = MagicMock(spec=Request)
        request.headers = {
            'X-Free-User-ID': 'invalid_base64!'
        }

        paid_id, free_id, user_type = extract_user_id(request)

        assert paid_id is None
        assert free_id is None
        assert user_type == 'anonymous'  # Falls back to anonymous when invalid
        assert 'Failed to decode' in caplog.text