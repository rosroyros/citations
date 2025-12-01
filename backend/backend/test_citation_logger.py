import pytest
import os
import tempfile
from unittest.mock import patch, mock_open
import logging
from citation_logger import log_citations_to_dashboard, ensure_citation_log_ready, parse_citation_blocks


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

    def test_ensure_citation_log_ready_creates_directory_with_permissions(self):
        """Test that ensure_citation_log_ready creates directory and validates write permissions."""
        from pathlib import Path

        with patch("citation_logger.Path") as mock_path:
            # Mock directory and file paths
            mock_log_dir = mock_path.return_value
            mock_log_file = mock_log_dir.__truediv__.return_value

            # Mock directory creation (should succeed)
            mock_log_dir.mkdir.return_value = None

            # Mock file operations
            mock_log_file.exists.return_value = True
            mock_log_file.touch.return_value = None

            # Mock os.access to return True (write permissions OK)
            with patch("citation_logger.os.access", return_value=True):
                with patch("citation_logger.logger") as mock_logger:
                    result = ensure_citation_log_ready()

                    # Should return True when directory and permissions are properly set up
                    assert result is True

                    # Should call mkdir with parents=True and exist_ok=True
                    mock_log_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)

                    # Should log success message
                    mock_logger.info.assert_called_once_with("Citation log directory and permissions are ready")

    def test_ensure_citation_log_ready_handles_permission_error(self):
        """Test that permission errors are handled gracefully."""
        from pathlib import Path

        with patch("citation_logger.Path") as mock_path:
            # Mock directory and file paths
            mock_log_dir = mock_path.return_value
            mock_log_file = mock_log_dir.__truediv__.return_value

            # Mock directory creation to raise PermissionError
            mock_log_dir.mkdir.side_effect = PermissionError("Permission denied")

            with patch("citation_logger.logger") as mock_logger:
                result = ensure_citation_log_ready()

                # Should return False on permission error
                assert result is False

                # Should log critical error
                mock_logger.critical.assert_called_once()
                critical_message = mock_logger.critical.call_args[0][0]
                assert "Failed to prepare citation log directory" in critical_message

    def test_ensure_citation_log_ready_handles_file_creation_error(self):
        """Test that file creation errors are handled gracefully."""
        from pathlib import Path

        with patch("citation_logger.Path") as mock_path:
            # Mock directory and file paths
            mock_log_dir = mock_path.return_value
            mock_log_file = mock_log_dir.__truediv__.return_value

            # Mock directory creation (should succeed)
            mock_log_dir.mkdir.return_value = None

            # Mock file exists as False and touch to raise PermissionError
            mock_log_file.exists.return_value = False
            mock_log_file.touch.side_effect = PermissionError("Cannot create file")

            with patch("citation_logger.logger") as mock_logger:
                result = ensure_citation_log_ready()

                # Should return False on file creation error
                assert result is False

                # Should log critical error
                mock_logger.critical.assert_called_once()

    def test_ensure_citation_log_ready_handles_write_permission_denied(self):
        """Test that write permission denial is handled gracefully."""
        from pathlib import Path

        with patch("citation_logger.Path") as mock_path:
            # Mock directory and file paths
            mock_log_dir = mock_path.return_value
            mock_log_file = mock_log_dir.__truediv__.return_value

            # Mock directory creation (should succeed)
            mock_log_dir.mkdir.return_value = None

            # Mock file operations
            mock_log_file.exists.return_value = True
            mock_log_file.touch.return_value = None

            # Mock os.access to return False (no write permissions)
            with patch("citation_logger.os.access", return_value=False):
                with patch("citation_logger.logger") as mock_logger:
                    result = ensure_citation_log_ready()

                    # Should return False when write permissions are denied
                    assert result is False

                    # Should log critical error about permissions
                    mock_logger.critical.assert_called_once_with("No write permissions to citation log file")


class TestCitationParser:
    """Test suite for parse_citation_blocks function."""

    def test_parse_citation_blocks_with_valid_input(self):
        """Test that valid citation blocks are parsed correctly."""
        content = """<<JOB_ID:job123>>
Smith, J. (2023). Test citation one. Journal Title, 1(1), 1-10.
Doe, J. (2023). Test citation two. Another Journal, 2(2), 20-30.
<<<END_JOB>>>
<<JOB_ID:job456>>
Johnson, A. (2023). Another citation. Third Journal, 3(3), 30-40.
<<<END_JOB>>>
"""

        expected = [
            ("job123", [
                "Smith, J. (2023). Test citation one. Journal Title, 1(1), 1-10.",
                "Doe, J. (2023). Test citation two. Another Journal, 2(2), 20-30."
            ]),
            ("job456", [
                "Johnson, A. (2023). Another citation. Third Journal, 3(3), 30-40."
            ])
        ]

        result = parse_citation_blocks(content)
        assert result == expected

    def test_parse_citation_blocks_with_empty_content(self):
        """Test that empty content returns empty list."""
        content = ""

        result = parse_citation_blocks(content)
        assert result == []

    def test_parse_citation_blocks_handles_malformed_entries_gracefully(self):
        """Test that malformed entries are handled gracefully."""
        content = """Some random text here
<<JOB_ID:job123>>
Smith, J. (2023). Test citation.
More random text
<<JOB_ID:no_end_job>>
This block has no end marker
<<<END_JOB>>>
"""

        expected = [
            ("no_end_job", [
                "This block has no end marker"
            ])
        ]

        result = parse_citation_blocks(content)
        assert result == expected

    def test_parse_citation_blocks_with_incomplete_blocks(self):
        """Test that incomplete blocks (missing END_JOB) are ignored."""
        content = """<<JOB_ID:complete_job>>
Smith, J. (2023). Complete citation.
<<<END_JOB>>>
<<JOB_ID:incomplete_job>>
Doe, J. (2023). Incomplete citation.
Johnson, A. (2023). Another incomplete.
"""

        expected = [
            ("complete_job", [
                "Smith, J. (2023). Complete citation."
            ])
        ]

        result = parse_citation_blocks(content)
        assert result == expected

    def test_parse_citation_blocks_with_special_characters_and_newlines(self):
        """Test that citations with special characters and newlines are handled correctly."""
        content = """<<JOB_ID:special_chars_job>>
Smith, J. (2023). Citation with "quotes" & ampersands. Journal Name, 1(2), 15-25.
Doe, J. & Johnson, A.B. (2023). Citation with émojis 🚀 and unicode ñáíóú.
Multi-line citation that spans
multiple lines but should be treated
as separate entries.
<<<END_JOB>>>
"""

        expected = [
            ("special_chars_job", [
                'Smith, J. (2023). Citation with "quotes" & ampersands. Journal Name, 1(2), 15-25.',
                'Doe, J. & Johnson, A.B. (2023). Citation with émojis 🚀 and unicode ñáíóú.',
                'Multi-line citation that spans',
                'multiple lines but should be treated',
                'as separate entries.'
            ])
        ]

        result = parse_citation_blocks(content)
        assert result == expected