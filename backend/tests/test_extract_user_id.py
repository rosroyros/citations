"""
Tests for extract_user_id function in app.py

Following TDD principles - tests written before implementation.
"""

import pytest
import base64
from fastapi import Request
from unittest.mock import Mock


def test_extract_user_id_paid_user():
    """Test extraction of paid user ID from X-User-Token header."""
    # Create a mock request with X-User-Token header
    mock_request = Mock(spec=Request)
    mock_request.headers = {
        'X-User-Token': 'paid-abc-123-def-456',
        'X-Free-User-ID': base64.b64encode(b'550e8400-e29b-41d4-a716-446655440000').decode()
    }

    # Import the function (this will fail since we haven't implemented it yet)
    from app import extract_user_id

    # Call the function
    paid_user_id, free_user_id, user_type = extract_user_id(mock_request)

    # Assert paid user takes precedence and we get expected values
    assert paid_user_id == 'paid-abc'
    assert free_user_id is None
    assert user_type == 'paid'


def test_extract_user_id_free_user():
    """Test extraction of free user ID from X-Free-User-ID header."""
    # Create a mock request with X-Free-User-ID header
    free_uuid = '550e8400-e29b-41d4-a716-446655440000'
    mock_request = Mock(spec=Request)
    mock_request.headers = {
        'X-Free-User-ID': base64.b64encode(free_uuid.encode()).decode()
    }

    from app import extract_user_id

    paid_user_id, free_user_id, user_type = extract_user_id(mock_request)

    # Assert free user ID is extracted correctly
    assert paid_user_id is None
    assert free_user_id == free_uuid
    assert user_type == 'free'


def test_extract_user_id_invalid_base64():
    """Test handling of invalid base64 in X-Free-User-ID header."""
    mock_request = Mock(spec=Request)
    mock_request.headers = {
        'X-Free-User-ID': 'invalid-base64-!'
    }

    from app import extract_user_id

    paid_user_id, free_user_id, user_type = extract_user_id(mock_request)

    # Should handle gracefully and treat as anonymous
    assert paid_user_id is None
    assert free_user_id is None
    assert user_type == 'anonymous'


def test_extract_user_id_anonymous():
    """Test handling of request with no user ID headers."""
    mock_request = Mock(spec=Request)
    mock_request.headers = {}

    from app import extract_user_id

    paid_user_id, free_user_id, user_type = extract_user_id(mock_request)

    # Should return anonymous user
    assert paid_user_id is None
    assert free_user_id is None
    assert user_type == 'anonymous'


def test_extract_user_id_paid_user_precedence():
    """Test that X-User-Token takes precedence over X-Free-User-ID when both present."""
    mock_request = Mock(spec=Request)
    mock_request.headers = {
        'X-User-Token': 'paid-xyz-789',
        'X-Free-User-ID': base64.b64encode(b'550e8400-e29b-41d4-a716-446655440000').decode()
    }

    from app import extract_user_id

    paid_user_id, free_user_id, user_type = extract_user_id(mock_request)

    # Should prefer paid user ID even if free user ID also present
    assert paid_user_id == 'paid-xyz'
    assert free_user_id is None
    assert user_type == 'paid'


def test_extract_user_id_paid_user_short_token():
    """Test handling of paid user token shorter than 8 characters."""
    mock_request = Mock(spec=Request)
    mock_request.headers = {
        'X-User-Token': 'short'
    }

    from app import extract_user_id

    paid_user_id, free_user_id, user_type = extract_user_id(mock_request)

    # Should handle short tokens gracefully
    assert paid_user_id == 'short'  # Should return entire token if shorter than 8 chars
    assert free_user_id is None
    assert user_type == 'paid'


def test_extract_user_id_empty_headers():
    """Test handling of empty header values."""
    mock_request = Mock(spec=Request)
    mock_request.headers = {
        'X-User-Token': '',
        'X-Free-User-ID': ''
    }

    from app import extract_user_id

    paid_user_id, free_user_id, user_type = extract_user_id(mock_request)

    # Empty strings should be treated as not present
    assert paid_user_id is None
    assert free_user_id is None
    assert user_type == 'anonymous'