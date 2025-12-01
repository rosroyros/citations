#!/usr/bin/env python3
"""
Comprehensive tests for enhanced error handling functionality in citation pipeline.
Tests disk space checking, enhanced logging, and pipeline metrics.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os

# Add backend path for imports
sys.path.append('./backend')

from citation_logger import check_disk_space, log_citations_to_dashboard, ensure_citation_log_ready
import shutil


class TestDiskSpaceChecking(unittest.TestCase):
    """Test disk space checking functionality."""

    @patch('shutil.disk_usage')
    def test_check_disk_space_sufficient(self, mock_disk_usage):
        """Test disk space check when sufficient space is available."""
        # Mock 10GB available space
        mock_stat = MagicMock()
        mock_stat.total = 100 * 1024 * 1024 * 1024  # 100GB total
        mock_stat.free = 10 * 1024 * 1024 * 1024  # 10GB free
        mock_disk_usage.return_value = mock_stat

        result = check_disk_space('/test/path')

        self.assertEqual(result['available_bytes'], 10 * 1024 * 1024 * 1024)
        self.assertAlmostEqual(result['available_gb'], 10.0, places=2)
        self.assertTrue(result['has_minimum'])  # Above 100MB
        self.assertFalse(result['has_warning'])  # Above 500MB
        self.assertIsNone(result['error'])

    @patch('shutil.disk_usage')
    def test_check_disk_space_warning_level(self, mock_disk_usage):
        """Test disk space check at warning threshold."""
        # Mock 300MB available space (below warning, above minimum)
        mock_stat = MagicMock()
        mock_stat.total = 100 * 1024 * 1024 * 1024
        mock_stat.free = 300 * 1024 * 1024  # 300MB free
        mock_disk_usage.return_value = mock_stat

        result = check_disk_space('/test/path')

        self.assertEqual(result['available_bytes'], 300 * 1024 * 1024)
        self.assertAlmostEqual(result['available_gb'], 0.29, places=2)
        self.assertTrue(result['has_minimum'])  # Above 100MB
        self.assertTrue(result['has_warning'])  # Below 500MB
        self.assertIsNone(result['error'])

    @patch('shutil.disk_usage')
    def test_check_disk_space_critical_level(self, mock_disk_usage):
        """Test disk space check below minimum threshold."""
        # Mock 50MB available space (below minimum)
        mock_stat = MagicMock()
        mock_stat.total = 100 * 1024 * 1024 * 1024
        mock_stat.free = 50 * 1024 * 1024  # 50MB free
        mock_disk_usage.return_value = mock_stat

        result = check_disk_space('/test/path')

        self.assertEqual(result['available_bytes'], 50 * 1024 * 1024)
        self.assertAlmostEqual(result['available_gb'], 0.05, places=2)
        self.assertFalse(result['has_minimum'])  # Below 100MB
        self.assertTrue(result['has_warning'])  # Below 500MB
        self.assertIsNone(result['error'])

    @patch('shutil.disk_usage')
    def test_check_disk_space_exception(self, mock_disk_usage):
        """Test disk space check when an exception occurs."""
        mock_disk_usage.side_effect = OSError("Permission denied")

        result = check_disk_space('/test/path')

        self.assertEqual(result['available_bytes'], 0)
        self.assertEqual(result['available_gb'], 0)
        self.assertFalse(result['has_minimum'])
        self.assertTrue(result['has_warning'])
        self.assertEqual(result['error'], "Permission denied")


class TestEnhancedCitationLogging(unittest.TestCase):
    """Test enhanced citation logging with disk space validation."""

    @patch('citation_logger.check_disk_space')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    @patch('os.fsync')
    @patch('os.path.dirname')
    def test_logging_with_sufficient_disk_space(self, mock_dirname, mock_fsync, mock_makedirs, mock_file, mock_disk_check):
        """Test successful logging when disk space is sufficient."""
        mock_dirname.return_value = '/test/logs'
        mock_disk_check.return_value = {
            'available_gb': 5.0,
            'has_minimum': True,
            'has_warning': False,
            'error': None
        }

        result = log_citations_to_dashboard('test-job-123', ['Test citation 1', 'Test citation 2'])

        self.assertTrue(result)
        mock_disk_check.assert_called_once_with('/test/logs')
        mock_file.assert_called_once_with('/opt/citations/logs/citations.log', "a", encoding="utf-8")
        mock_fsync.assert_called_once()

    @patch('citation_logger.check_disk_space')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    @patch('os.path.dirname')
    def test_logging_blocked_by_insufficient_disk_space(self, mock_dirname, mock_makedirs, mock_file, mock_disk_check):
        """Test logging blocked when disk space is insufficient."""
        mock_dirname.return_value = '/test/logs'
        mock_disk_check.return_value = {
            'available_gb': 0.05,
            'has_minimum': False,
            'has_warning': True,
            'error': None
        }

        result = log_citations_to_dashboard('test-job-123', ['Test citation 1'])

        self.assertFalse(result)
        mock_disk_check.assert_called_once_with('/test/logs')
        mock_file.assert_not_called()

    @patch('citation_logger.check_disk_space')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    @patch('os.path.dirname')
    def test_logging_with_disk_space_warning(self, mock_dirname, mock_makedirs, mock_file, mock_disk_check):
        """Test logging proceeds with disk space warning but sufficient space."""
        mock_dirname.return_value = '/test/logs'
        mock_disk_check.return_value = {
            'available_gb': 0.3,
            'has_minimum': True,
            'has_warning': True,
            'error': None
        }

        result = log_citations_to_dashboard('test-job-123', ['Test citation 1'])

        self.assertTrue(result)
        mock_disk_check.assert_called_once_with('/test/logs')
        mock_file.assert_called_once()

    @patch('citation_logger.check_disk_space')
    @patch('builtins.open', side_effect=OSError("No space left on device"))
    @patch('os.makedirs')
    @patch('os.path.dirname')
    def test_logging_write_failure_disk_space_exhausted(self, mock_dirname, mock_makedirs, mock_open_file, mock_disk_check):
        """Test handling of write failure due to disk space exhaustion."""
        mock_dirname.return_value = '/test/logs'
        mock_disk_check.return_value = {
            'available_gb': 1.0,
            'has_minimum': True,
            'has_warning': False,
            'error': None
        }

        # Mock the post-failure disk check
        with patch('citation_logger.check_disk_space') as mock_post_check:
            mock_post_check.return_value = {
                'available_gb': 0.05,
                'has_minimum': False,
                'has_warning': True,
                'error': None
            }

            result = log_citations_to_dashboard('test-job-123', ['Test citation 1'])

            self.assertFalse(result)
            # Should be called twice - once pre-check, once post-failure
            self.assertEqual(mock_disk_check.call_count, 2)

    @patch('citation_logger.check_disk_space')
    def test_logging_disk_check_error(self, mock_disk_check):
        """Test logging when disk space check itself fails."""
        mock_disk_check.return_value = {
            'available_gb': 0,
            'has_minimum': False,
            'has_warning': True,
            'error': 'Permission denied'
        }

        result = log_citations_to_dashboard('test-job-123', ['Test citation 1'])

        self.assertFalse(result)
        mock_disk_check.assert_called_once()


class TestPipelineMetricsEnhancements(unittest.TestCase):
    """Test enhanced pipeline metrics functionality."""

    @patch('citation_logger.check_disk_space')
    @patch('os.path.exists')
    @patch('os.stat')
    @patch('datetime.datetime')
    def test_metrics_healthy_disk_space(self, mock_datetime, mock_stat, mock_exists, mock_disk_check):
        """Test metrics with healthy disk space and recent log file."""
        # Setup mocks
        mock_exists.side_effect = lambda path: True  # All files exist
        mock_datetime.now.return_value.timestamp.return_value = 1700000000  # Current time

        file_stat = MagicMock()
        file_stat.st_size = 1024 * 1024  # 1MB
        file_stat.st_mtime = 1700000000 - 3600  # 1 hour ago
        mock_stat.return_value = file_stat

        mock_disk_check.return_value = {
            'available_gb': 10.0,
            'has_minimum': True,
            'has_warning': False,
            'error': None
        }

        # Mock position file content
        with patch('builtins.open', mock_open(read_data='1048576')):  # 1MB position
            # Import inside test to avoid path issues
            sys.path.append('.')
            from app import get_citation_pipeline_metrics

            metrics = get_citation_pipeline_metrics()

        self.assertEqual(metrics['health_status'], 'healthy')
        self.assertTrue(metrics['log_file_exists'])
        self.assertEqual(metrics['disk_space_gb'], 10.0)
        self.assertFalse(metrics['disk_space_warning'])
        self.assertFalse(metrics['disk_space_critical'])
        self.assertEqual(metrics['log_age_hours'], 1.0)

    @patch('citation_logger.check_disk_space')
    @patch('os.path.exists')
    @patch('os.stat')
    @patch('datetime.datetime')
    def test_metrics_critical_disk_space(self, mock_datetime, mock_stat, mock_exists, mock_disk_check):
        """Test metrics with critical disk space."""
        # Setup mocks
        mock_exists.side_effect = lambda path: True  # All files exist
        mock_datetime.now.return_value.timestamp.return_value = 1700000000

        file_stat = MagicMock()
        file_stat.st_size = 1024 * 1024  # 1MB
        file_stat.st_mtime = 1700000000 - 3600  # 1 hour ago
        mock_stat.return_value = file_stat

        mock_disk_check.return_value = {
            'available_gb': 0.05,
            'has_minimum': False,
            'has_warning': True,
            'error': None
        }

        # Mock position file content
        with patch('builtins.open', mock_open(read_data='0')):  # 0 bytes position
            # Import inside test to avoid path issues
            sys.path.append('.')
            from app import get_citation_pipeline_metrics

            metrics = get_citation_pipeline_metrics()

        self.assertEqual(metrics['health_status'], 'error')  # Should be 'error' due to critical disk space
        self.assertTrue(metrics['log_file_exists'])
        self.assertEqual(metrics['disk_space_gb'], 0.05)
        self.assertTrue(metrics['disk_space_warning'])
        self.assertTrue(metrics['disk_space_critical'])

    @patch('os.path.exists')
    @patch('os.stat')
    @patch('datetime.datetime')
    def test_metrics_log_file_not_found(self, mock_datetime, mock_stat, mock_exists):
        """Test metrics when log file doesn't exist."""
        # Setup mocks
        mock_exists.side_effect = lambda path: False  # No files exist

        # Import inside test to avoid path issues
        sys.path.append('.')
        from app import get_citation_pipeline_metrics

        metrics = get_citation_pipeline_metrics()

        self.assertEqual(metrics['health_status'], 'error')
        self.assertFalse(metrics['log_file_exists'])
        self.assertEqual(metrics['last_write_time'], 'File not found')


class TestCitationLogReadiness(unittest.TestCase):
    """Test citation log readiness checking."""

    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('os.access')
    @patch('pathlib.Path.touch')
    @patch('pathlib.Path.mkdir')
    def test_log_readiness_success(self, mock_mkdir, mock_touch, mock_access, mock_exists, mock_os_makedirs):
        """Test successful citation log readiness check."""
        mock_exists.side_effect = lambda path: True
        mock_access.return_value = True

        result = ensure_citation_log_ready()

        self.assertTrue(result)

    @patch('os.path.exists')
    @patch('os.access')
    def test_log_readiness_no_permissions(self, mock_access, mock_exists):
        """Test citation log readiness check with no write permissions."""
        mock_exists.return_value = True
        mock_access.return_value = False

        result = ensure_citation_log_ready()

        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()