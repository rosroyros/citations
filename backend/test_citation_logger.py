import pytest
import os
import tempfile
from unittest.mock import patch, mock_open
import logging
from citation_logger import log_citations_to_dashboard


class TestCitationLogger:
    """Test suite for log_citations_to_dashboard function."""

    def test_log_citations_writes_structured_format(self):
        """Test that citations are logged in the correct structured format."""
        job_id = "test_job_123"
        citations = [
            "Smith, J. (2023). Test citation one. Journal Title, 1(1), 1-10.",
            "Doe, J. (2023). Test citation two. Another Journal, 2(2), 20-30."
        ]

        expected_content = (
            "<<JOB_ID:test_job_123>>\n"
            "Smith, J. (2023). Test citation one. Journal Title, 1(1), 1-10.\n"
            "Doe, J. (2023). Test citation two. Another Journal, 2(2), 20-30.\n"
            "<<<END_JOB>>>\n"
        )

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("os.makedirs", return_value=None):
                result = log_citations_to_dashboard(job_id, citations)

                # Should return True on success
                assert result is True

                # File should be opened for append
                mock_file.assert_called_once_with("/opt/citations/logs/citations.log", "a", encoding="utf-8")

                # Content should be written correctly
                handle = mock_file()
                written_content = "".join(call[0][0] for call in handle.write.call_args_list)
                assert written_content == expected_content

    def test_log_citations_with_empty_list(self):
        """Test that empty citation list is handled gracefully."""
        job_id = "test_job_456"
        citations = []

        expected_content = (
            "<<JOB_ID:test_job_456>>\n"
            "<<<END_JOB>>>\n"
        )

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("os.makedirs", return_value=None):
                result = log_citations_to_dashboard(job_id, citations)

                assert result is True
                handle = mock_file()
                written_content = "".join(call[0][0] for call in handle.write.call_args_list)
                assert written_content == expected_content

    def test_log_citations_handles_io_error_gracefully(self):
        """Test that I/O errors are caught and logged but don't raise exceptions."""
        job_id = "test_job_789"
        citations = ["Smith, J. (2023). Test citation."]

        with patch("builtins.open", side_effect=IOError("Permission denied")):
            with patch("os.makedirs", return_value=None):
                with patch("citation_logger.logger") as mock_logger:
                    result = log_citations_to_dashboard(job_id, citations)

                    # Should return False on error, not raise exception
                    assert result is False

                    # Should log critical error
                    mock_logger.critical.assert_called_once()

    def test_log_citations_handles_os_error_gracefully(self):
        """Test that OS errors are caught and logged but don't raise exceptions."""
        job_id = "test_job_error"
        citations = ["Smith, J. (2023). Test citation."]

        with patch("builtins.open", side_effect=OSError("Directory doesn't exist")):
            with patch("os.makedirs", side_effect=OSError("Permission denied")):
                with patch("citation_logger.logger") as mock_logger:
                    result = log_citations_to_dashboard(job_id, citations)

                    # Should return False on error, not raise exception
                    assert result is False

                    # Should log critical error
                    mock_logger.critical.assert_called_once()

    def test_log_citations_creates_directory_if_needed(self):
        """Test that function creates log directory if it doesn't exist."""
        job_id = "test_job_dir"
        citations = ["Smith, J. (2023). Test citation."]

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("os.makedirs") as mock_makedirs:
                result = log_citations_to_dashboard(job_id, citations)

                assert result is True
                mock_makedirs.assert_called_once_with("/opt/citations/logs", exist_ok=True)

    def test_log_citations_with_single_citation(self):
        """Test logging with a single citation."""
        job_id = "single_citation_job"
        citations = ["Smith, J. (2023). Single test citation. Journal Title, 1(1), 1-10."]

        expected_content = (
            "<<JOB_ID:single_citation_job>>\n"
            "Smith, J. (2023). Single test citation. Journal Title, 1(1), 1-10.\n"
            "<<<END_JOB>>>\n"
        )

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("os.makedirs", return_value=None):
                result = log_citations_to_dashboard(job_id, citations)

                assert result is True
                handle = mock_file()
                written_content = "".join(call[0][0] for call in handle.write.call_args_list)
                assert written_content == expected_content