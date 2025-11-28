"""
Unit tests for gated results tracking logic.

Tests cover all business rules and edge cases for the gating decision engine,
user type detection, and database helper functions.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from fastapi import Request
from datetime import datetime

# Import modules to test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from gating import (
    get_user_type,
    should_gate_results,
    should_gate_results_sync,
    store_gated_results,
    log_gating_event,
    log_results_revealed,
    get_gating_summary
)


class TestUserTypeDetection:
    """Test user type detection logic."""

    def test_paid_user_with_token(self):
        """Test that users with X-User-Token header are identified as paid."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {'X-User-Token': 'test-token-123'}

        result = get_user_type(mock_request)
        assert result == 'paid'

    def test_free_user_with_free_used_header(self):
        """Test that users with X-Free-Used header are identified as free."""
        mock_request = Mock(spec=Request)
        mock_request.headers.get = Mock(side_effect=lambda key, default=None:
                                       '5' if key == 'X-Free-Used' else None)

        result = get_user_type(mock_request)
        assert result == 'free'

    def test_anonymous_user_no_headers(self):
        """Test that users with no identifying headers are anonymous."""
        mock_request = Mock(spec=Request)
        mock_request.headers.get = Mock(return_value=None)

        result = get_user_type(mock_request)
        assert result == 'anonymous'

    def test_user_type_priority_token_over_free(self):
        """Test that token takes priority over free-used header."""
        mock_request = Mock(spec=Request)
        mock_request.headers = {
            'X-User-Token': 'paid-token-456',
            'X-Free-Used': '8'
        }

        result = get_user_type(mock_request)
        assert result == 'paid'


class TestGatingDecisionEngine:
    """Test the core gating decision logic."""

    @patch('gating.GATED_RESULTS_ENABLED', False)
    def test_gating_disabled_bypasses_all(self):
        """Test that disabled feature flag bypasses all gating."""
        result = should_gate_results('free', {'isPartial': False, 'errors': []}, True)
        assert result is False

    @patch('gating.GATED_RESULTS_ENABLED', True)
    def test_paid_users_bypass_gating(self):
        """Test that paid users never get gated."""
        result = should_gate_results('paid', {'isPartial': False, 'errors': []}, True)
        assert result is False

    @patch('gating.GATED_RESULTS_ENABLED', True)
    def test_validation_errors_bypass_gating(self):
        """Test that validation errors bypass gating for all users."""
        result = should_gate_results('free', {'isPartial': False, 'errors': ['some error']}, True)
        assert result is False

    @patch('gating.GATED_RESULTS_ENABLED', True)
    def test_partial_results_bypass_gating(self):
        """Test that partial results bypass gating."""
        result = should_gate_results('free', {'isPartial': True, 'errors': []}, True)
        assert result is False

    @patch('gating.GATED_RESULTS_ENABLED', True)
    def test_validation_failure_bypass_gating(self):
        """Test that validation processing failures bypass gating."""
        result = should_gate_results('free', {'isPartial': False, 'errors': []}, False)
        assert result is False

    @patch('gating.GATED_RESULTS_ENABLED', True)
    def test_perfect_conditions_trigger_gating(self):
        """Test that perfect conditions trigger gating for free users."""
        result = should_gate_results('free', {'isPartial': False, 'errors': []}, True)
        assert result is True

    @patch('gating.GATED_RESULTS_ENABLED', True)
    def test_anonymous_users_treated_as_free(self):
        """Test that anonymous users are treated as free for gating."""
        result = should_gate_results('anonymous', {'isPartial': False, 'errors': []}, True)
        assert result is True


class TestSyncGatingHelper:
    """Test the synchronous validation helper function."""

    def test_sync_gating_with_empty_results(self):
        """Test that empty results are treated as partial (bypass gating)."""
        validation_response = {
            'results': [],
            'partial': False
        }

        result = should_gate_results_sync('free', validation_response, True)
        assert result is False  # Should NOT gate because empty results are treated as partial

    def test_sync_gating_with_successful_results(self):
        """Test successful sync gating decision."""
        validation_response = {
            'results': [{'citation': 'test'}],
            'partial': False
        }

        with patch('gating.GATED_RESULTS_ENABLED', True):
            result = should_gate_results_sync('free', validation_response, True)
            assert result is True

    def test_sync_gating_paid_user(self):
        """Test that paid users bypass gating in sync mode."""
        validation_response = {
            'results': [{'citation': 'test'}],
            'partial': False
        }

        result = should_gate_results_sync('paid', validation_response, True)
        assert result is False


class TestGatingEventLogging:
    """Test gating event logging functionality."""

    @patch('gating.logger')
    def test_log_gated_results(self, mock_logger):
        """Test logging of gated results."""
        log_gating_event('job-123', 'free', True)

        mock_logger.info.assert_called_once_with("RESULTS_READY_GATED: job_id=job-123, user_type=free")

    @patch('gating.logger')
    def test_log_direct_results_with_reason(self, mock_logger):
        """Test logging of direct results with reason."""
        log_gating_event('job-456', 'paid', False, 'Paid user')

        mock_logger.info.assert_called_once_with(
            "RESULTS_READY_DIRECT: job_id=job-456, user_type=paid, reason=Paid user"
        )

    @patch('gating.logger')
    def test_log_direct_results_default_reason(self, mock_logger):
        """Test logging of direct results with default reason."""
        log_gating_event('job-789', 'anonymous', False)

        mock_logger.info.assert_called_once_with(
            "RESULTS_READY_DIRECT: job_id=job-789, user_type=anonymous, reason=No gating needed"
        )


class TestGatedResultsStorage:
    """Test storage of gating decisions in database."""

    @patch('gating.sqlite3')
    @patch('database.get_validations_db_path')
    def test_store_gated_results_success(self, mock_db_path, mock_sqlite):
        """Test successful storage of gating decision."""
        mock_db_path.return_value = '/test/path.db'
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        store_gated_results('job-123', True, 'free', {'test': 'data'})

        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('database.sqlite3')
    @patch('database.get_validations_db_path')
    def test_store_gated_results_with_provided_connection(self, mock_db_path, mock_sqlite):
        """Test storage with provided database connection."""
        mock_db_path.return_value = '/test/path.db'
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor

        store_gated_results('job-456', False, 'paid', {}, mock_conn)

        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        # Connection should not be closed when provided
        mock_conn.close.assert_not_called()

    @patch('database.sqlite3')
    @patch('database.get_validations_db_path')
    @patch('gating.logger')
    def test_store_gated_results_database_error(self, mock_logger, mock_db_path, mock_sqlite):
        """Test handling of database errors during storage."""
        mock_db_path.return_value = '/test/path.db'
        mock_sqlite.connect.side_effect = Exception("Database error")

        # Should not raise exception, just log error
        store_gated_results('job-789', True, 'free', {})

        mock_logger.error.assert_called_once()


class TestGatingSummary:
    """Test gating summary statistics."""

    @patch('database.sqlite3')
    @patch('database.get_validations_db_path')
    def test_get_gating_summary_with_data(self, mock_db_path, mock_sqlite):
        """Test getting gating summary with database data."""
        mock_db_path.return_value = '/test/path.db'
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock database query result
        mock_cursor.fetchone.return_value = (100, 30, 70, 60, 40)

        with patch('gating.GATED_RESULTS_ENABLED', True):
            result = get_gating_summary()

            assert result['total_validations'] == 100
            assert result['gated_results'] == 30
            assert result['direct_results'] == 70
            assert result['gating_rate'] == 30.0
            assert result['free_users'] == 60
            assert result['paid_users'] == 40
            assert result['feature_enabled'] is True

    @patch('database.sqlite3')
    @patch('database.get_validations_db_path')
    def test_get_gating_summary_no_data(self, mock_db_path, mock_sqlite):
        """Test getting gating summary with no data."""
        mock_db_path.return_value = '/test/path.db'
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_sqlite.connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock empty database result
        mock_cursor.fetchone.return_value = (0, 0, 0, 0, 0)

        result = get_gating_summary()

        assert result['total_validations'] == 0
        assert result['gated_results'] == 0
        assert result['direct_results'] == 0
        assert result['gating_rate'] == 0
        assert result['free_users'] == 0
        assert result['paid_users'] == 0

    @patch('database.sqlite3')
    @patch('database.get_validations_db_path')
    @patch('gating.logger')
    def test_get_gating_summary_database_error(self, mock_logger, mock_db_path, mock_sqlite):
        """Test handling of database errors in summary."""
        mock_db_path.return_value = '/test/path.db'
        mock_sqlite.connect.side_effect = Exception("Database error")

        result = get_gating_summary()

        assert result['total_validations'] == 0
        assert 'error' in result
        mock_logger.error.assert_called_once()


class TestFeatureFlagBehavior:
    """Test behavior controlled by the feature flag."""

    @patch('gating.GATED_RESULTS_ENABLED', False)
    def test_feature_flag_disables_all_gating(self):
        """Test that disabled feature flag prevents all gating."""
        # Even with conditions that would normally trigger gating
        result = should_gate_results('free', {'isPartial': False, 'errors': []}, True)
        assert result is False

        result = should_gate_results('anonymous', {'isPartial': False, 'errors': []}, True)
        assert result is False

    @patch('gating.GATED_RESULTS_ENABLED', True)
    def test_feature_flag_enables_gating(self):
        """Test that enabled feature flag allows gating."""
        # Conditions that should trigger gating
        result = should_gate_results('free', {'isPartial': False, 'errors': []}, True)
        assert result is True

        result = should_gate_results('anonymous', {'isPartial': False, 'errors': []}, True)
        assert result is True

        # Conditions that should not trigger gating
        result = should_gate_results('paid', {'isPartial': False, 'errors': []}, True)
        assert result is False


class TestResultsRevealedLogging:
    """Test logging of results revealed analytics events."""

    @patch('gating.logger')
    def test_log_results_revealed_success(self, mock_logger):
        """Test successful logging of results revealed event."""
        job_id = 'test-job-123'
        time_to_reveal = 45
        user_type = 'free'

        log_results_revealed(job_id, time_to_reveal, user_type)

        # Verify the info log was called with correct format
        mock_logger.info.assert_called_once_with(
            f"RESULTS_REVEALED: job_id={job_id}, "
            f"time_to_reveal={time_to_reveal}s, "
            f"user_type={user_type}"
        )

    @patch('gating.logger')
    @patch.dict(os.environ, {'DEBUG_ANALYTICS': 'true'})
    def test_log_results_revealed_with_debug_logging(self, mock_logger):
        """Test logging with debug analytics enabled."""
        job_id = 'test-job-456'
        time_to_reveal = 120
        user_type = 'paid'

        log_results_revealed(job_id, time_to_reveal, user_type)

        # Verify both info and debug logs were called
        assert mock_logger.info.call_count == 1
        assert mock_logger.debug.call_count == 1

        # Check info log format
        info_call = mock_logger.info.call_args[0][0]
        assert f"RESULTS_REVEALED: job_id={job_id}" in info_call
        assert f"time_to_reveal={time_to_reveal}s" in info_call
        assert f"user_type={user_type}" in info_call

    @patch('gating.logger')
    def test_log_results_revealed_invalid_job_id(self, mock_logger):
        """Test handling of invalid job_id parameter."""
        invalid_job_ids = [None, '', '   ']

        for job_id in invalid_job_ids:
            log_results_revealed(job_id, 45, 'free')

        # Should log warning for each invalid job_id
        assert mock_logger.warning.call_count == len(invalid_job_ids)

        # Verify warning messages
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        for warning in warning_calls:
            assert "Invalid job_id in log_results_revealed:" in warning

    @patch('gating.logger')
    def test_log_results_revealed_invalid_time_to_reveal(self, mock_logger):
        """Test handling of invalid time_to_reveal parameter."""
        invalid_times = [-5, 'not-a-number', None]

        for time_val in invalid_times:
            log_results_revealed('valid-job', time_val, 'free')

        # Should log warning for each invalid time
        assert mock_logger.warning.call_count == len(invalid_times)

        # Verify warning messages
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        for warning in warning_calls:
            assert "Invalid time_to_reveal in log_results_revealed:" in warning

    @patch('gating.logger')
    def test_log_results_revealed_invalid_user_type(self, mock_logger):
        """Test handling of invalid user_type parameter."""
        log_results_revealed('valid-job', 45, 'invalid_type')

        # Should log warning for invalid user type
        mock_logger.warning.assert_called_once_with(
            "Invalid user_type in log_results_revealed: invalid_type"
        )

    @patch('gating.logger')
    def test_log_results_revealed_exception_handling(self, mock_logger):
        """Test that exceptions are caught and logged without raising."""
        # Mock logger to raise an exception
        mock_logger.info.side_effect = Exception("Logging failed")

        # Should not raise exception
        log_results_revealed('test-job', 45, 'free')

        # Should log the error
        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args[0][0]
        assert "Failed to log results revealed analytics:" in error_call

    @patch('gating.logger')
    def test_log_results_revealed_edge_cases(self, mock_logger):
        """Test edge cases for valid parameters."""
        # Test boundary values
        test_cases = [
            ('job-0', 0, 'anonymous'),  # Zero time
            ('job-3600', 3600, 'paid'),  # Maximum allowed time
            ('job-with-dashes', 999, 'free'),  # Job ID with dashes
        ]

        for job_id, time_to_reveal, user_type in test_cases:
            log_results_revealed(job_id, time_to_reveal, user_type)

        # Should have logged all cases successfully
        assert mock_logger.info.call_count == len(test_cases)
        mock_logger.warning.assert_not_called()
        mock_logger.error.assert_not_called()


if __name__ == '__main__':
    pytest.main([__file__])