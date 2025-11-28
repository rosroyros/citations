"""
Unit tests for validation tracking database functions.

Tests for the new validation tracking functionality including
record creation, updates, reveal tracking, and analytics.
"""

import pytest
import os
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import modules to test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from database import (
    get_validations_db_path,
    create_validation_record,
    update_validation_tracking,
    record_result_reveal,
    get_validation_analytics
)


class TestValidationDatabaseHelpers:
    """Test validation tracking database helper functions."""

    @patch.dict(os.environ, {'TEST_VALIDATIONS_DB_PATH': '/test/validations.db'})
    def test_get_validations_db_path_test_override(self):
        """Test that test environment variable overrides database path."""
        result = get_validations_db_path()
        assert result == '/test/validations.db'

    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('sqlite3.connect')
    def test_create_validation_record_success(self, mock_sqlite, mock_makedirs, mock_exists):
        """Test successful creation of validation record."""
        mock_exists.return_value = False
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        result = create_validation_record('job-123', 'free', 5, 'pending')

        assert result is True
        mock_makedirs.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

        # Verify the SQL call
        call_args = mock_cursor.execute.call_args[0]
        assert 'INSERT INTO validations' in call_args[0]
        assert call_args[1] == ('job-123', 'free', 5, 'pending')

    @patch('sqlite3.connect')
    def test_create_validation_record_database_error(self, mock_sqlite):
        """Test handling of database errors during record creation."""
        mock_sqlite.connect.side_effect = sqlite3.Error("Database error")

        result = create_validation_record('job-456', 'paid', 3, 'processing')

        assert result is False

    @patch('sqlite3.connect')
    def test_update_validation_tracking_partial_update(self, mock_sqlite):
        """Test partial update of validation tracking."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        result = update_validation_tracking(
            job_id='job-789',
            validation_status='completed',
            results_gated=True
        )

        assert result is True
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

        # Verify the SQL call includes only provided fields
        call_args = mock_cursor.execute.call_args[0]
        sql = call_args[0]
        assert 'UPDATE validations SET' in sql
        assert 'validation_status = ?' in sql
        assert 'results_gated = ?' in sql
        assert call_args[1][:-1] == ('completed', True)  # Exclude job_id
        assert call_args[1][-1] == 'job-789'  # job_id is last

    @patch('sqlite3.connect')
    def test_update_validation_tracking_no_updates(self, mock_sqlite):
        """Test update with no provided fields."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        result = update_validation_tracking(job_id='job-000')

        assert result is False
        mock_cursor.execute.assert_not_called()
        mock_conn.commit.assert_not_called()

    @patch('sqlite3.connect')
    def test_update_validation_tracking_all_fields(self, mock_sqlite):
        """Test update with all possible fields."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        result = update_validation_tracking(
            job_id='job-111',
            validation_status='completed',
            results_gated=True,
            user_type='free',
            gated_at='2023-01-01T12:00:00',
            results_ready_at='2023-01-01T12:01:00',
            error_message=None
        )

        assert result is True

        # Verify all fields are in the SQL
        call_args = mock_cursor.execute.call_args[0]
        sql = call_args[0]
        assert 'validation_status = ?' in sql
        assert 'results_gated = ?' in sql
        assert 'user_type = ?' in sql
        assert 'gated_at = ?' in sql
        assert 'results_ready_at = ?' in sql
        assert len(call_args[1]) == 7  # 6 fields + job_id

    @patch('sqlite3.connect')
    def test_record_result_reveal_success(self, mock_sqlite):
        """Test successful recording of result reveal."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock the database query for getting gated_at
        mock_cursor.fetchone.return_value = ['2023-01-01T12:00:00']

        with patch('database.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0, 30)
            mock_datetime.fromisoformat.return_value = datetime(2023, 1, 1, 12, 0, 0)

            result = record_result_reveal('job-222', 'revealed')

            assert result is True
            mock_cursor.execute.assert_called()
            mock_conn.commit.assert_called_once()
            mock_conn.close.assert_called_once()

    @patch('sqlite3.connect')
    def test_record_result_reveal_no_validation_record(self, mock_sqlite):
        """Test recording reveal for non-existent validation record."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock no validation record found
        mock_cursor.fetchone.return_value = None

        result = record_result_reveal('job-333', 'revealed')

        assert result is False
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_not_called()

    @patch('sqlite3.connect')
    def test_record_result_reveal_not_gated(self, mock_sqlite):
        """Test recording reveal for results that weren't gated."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock validation record found but not gated
        mock_cursor.fetchone.return_value = [None]

        result = record_result_reveal('job-444', 'revealed')

        assert result is False
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_not_called()

    @patch('sqlite3.connect')
    def test_get_validation_analytics_success(self, mock_sqlite):
        """Test successful retrieval of validation analytics."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock analytics query result
        mock_cursor.fetchone.return_value = (100, 30, 20, 45.5, 95, 5)

        result = get_validation_analytics(days=7, user_type='free')

        expected = {
            'period_days': 7,
            'user_type': 'free',
            'total_validations': 100,
            'gated_results': 30,
            'revealed_results': 20,
            'reveal_rate': 66.7,
            'avg_time_to_reveal_seconds': 45.5,
            'success_rate': 95.0,
            'failed_validations': 5
        }

        assert result == expected
        mock_cursor.execute.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('sqlite3.connect')
    def test_get_validation_analytics_no_data(self, mock_sqlite):
        """Test analytics retrieval with no data."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock empty result
        mock_cursor.fetchone.return_value = None

        result = get_validation_analytics(days=30)

        expected = {
            'period_days': 30,
            'user_type': 'all',
            'total_validations': 0,
            'gated_results': 0,
            'revealed_results': 0,
            'reveal_rate': 0,
            'avg_time_to_reveal_seconds': 0,
            'success_rate': 0,
            'failed_validations': 0
        }

        assert result == expected

    @patch('sqlite3.connect')
    def test_get_validation_analytics_all_users(self, mock_sqlite):
        """Test analytics retrieval for all user types."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock analytics query result
        mock_cursor.fetchone.return_value = (200, 60, 40, 30.0, 190, 10)

        result = get_validation_analytics(days=1)

        expected = {
            'period_days': 1,
            'user_type': 'all',
            'total_validations': 200,
            'gated_results': 60,
            'revealed_results': 40,
            'reveal_rate': 66.7,
            'avg_time_to_reveal_seconds': 30.0,
            'success_rate': 95.0,
            'failed_validations': 10
        }

        assert result == expected

    @patch('sqlite3.connect')
    def test_get_validation_analytics_database_error(self, mock_sqlite):
        """Test handling of database errors in analytics."""
        mock_sqlite.connect.side_effect = sqlite3.Error("Database error")

        result = get_validation_analytics()

        assert result == {}


class TestValidationDatabaseQueries:
    """Test specific database queries and SQL construction."""

    @patch('sqlite3.connect')
    def test_analytics_query_construction(self, mock_sqlite):
        """Test that analytics queries are constructed correctly."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        get_validation_analytics(days=5, user_type='paid')

        # Verify the SQL query construction
        call_args = mock_cursor.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]

        assert 'COUNT(*) as total_validations' in sql
        assert 'COUNT(CASE WHEN results_gated = 1 THEN 1 END)' in sql
        assert 'created_at >= datetime(\'now\', \'-5 days\')' in sql
        assert 'AND user_type = ?' in sql
        assert params == ['paid']

    @patch('sqlite3.connect')
    def test_analytics_query_no_user_filter(self, mock_sqlite):
        """Test analytics query without user type filter."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        get_validation_analytics(days=10)

        # Verify the SQL query doesn't include user type filter
        call_args = mock_cursor.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]

        assert 'created_at >= datetime(\'now\', \'-10 days\')' in sql
        assert 'AND user_type' not in sql
        assert len(params) == 0

    @patch('sqlite3.connect')
    def test_update_tracking_dynamic_sql(self, mock_sqlite):
        """Test that update SQL is built dynamically based on provided fields."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Test with only validation status
        update_validation_tracking(job_id='test-job', validation_status='completed')

        call_args = mock_cursor.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]

        assert 'validation_status = ?' in sql
        assert 'results_gated = ?' not in sql
        assert params == ('completed', 'test-job')

        # Reset mock for next test
        mock_cursor.reset_mock()

        # Test with multiple fields
        update_validation_tracking(
            job_id='test-job-2',
            validation_status='completed',
            results_gated=True,
            user_type='free'
        )

        call_args = mock_cursor.execute.call_args
        sql = call_args[0][0]
        params = call_args[0][1]

        assert 'validation_status = ?' in sql
        assert 'results_gated = ?' in sql
        assert 'user_type = ?' in sql
        assert params == ('completed', True, 'free', 'test-job-2')


if __name__ == '__main__':
    pytest.main([__file__])