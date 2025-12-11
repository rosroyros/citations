"""
Unit tests for pricing_config.py timezone utilities.

Oracle Feedback #3: Use Unix timestamps (not date strings) to avoid timezone issues.
Oracle Feedback #10: Test time-dependent logic with mocked clocks (fast-forward).
"""

import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
import sys
import os

# Add backend directory to path so we can import pricing_config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pricing_config import get_next_utc_midnight, get_hours_until_reset

class TestTimezoneUtilities:
    
    @patch('pricing_config.datetime')
    def test_get_next_utc_midnight_before_noon(self, mock_datetime):
        """Test midnight calculation when current time is before noon."""
        # Given: 2025-12-10 08:30:00 UTC
        mock_now = datetime(2025, 12, 10, 8, 30, 0)
        mock_datetime.utcnow.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        # When: Get next midnight
        result = get_next_utc_midnight()
        
        # Then: Should be 2025-12-11 00:00:00 UTC
        expected = int(datetime(2025, 12, 11, 0, 0, 0).timestamp())
        assert result == expected
    
    @patch('pricing_config.datetime')
    def test_get_next_utc_midnight_after_noon(self, mock_datetime):
        """Test midnight calculation when current time is after noon."""
        # Given: 2025-12-10 20:45:30 UTC
        mock_now = datetime(2025, 12, 10, 20, 45, 30)
        mock_datetime.utcnow.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        # When: Get next midnight
        result = get_next_utc_midnight()
        
        # Then: Still 2025-12-11 00:00:00 UTC
        expected = int(datetime(2025, 12, 11, 0, 0, 0).timestamp())
        assert result == expected
    
    @patch('pricing_config.datetime')
    def test_get_next_utc_midnight_near_midnight(self, mock_datetime):
        """Test midnight calculation when current time is close to midnight."""
        # Given: 2025-12-10 23:59:59 UTC
        mock_now = datetime(2025, 12, 10, 23, 59, 59)
        mock_datetime.utcnow.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        
        # When: Get next midnight
        result = get_next_utc_midnight()
        
        # Then: Should be 2025-12-11 00:00:00 UTC (1 second away)
        expected = int(datetime(2025, 12, 11, 0, 0, 0).timestamp())
        assert result == expected
    
    @patch('pricing_config.time.time')
    @patch('pricing_config.get_next_utc_midnight')
    def test_get_hours_until_reset_full_day(self, mock_midnight, mock_time):
        """Test hours calculation with full day remaining."""
        # Given: 00:30 UTC (30 min after midnight)
        now = 1704067200 + 1800  # Jan 1, 2024 00:30 UTC
        next_midnight = now + (23.5 * 3600)  # 23.5 hours away
        
        mock_time.return_value = now
        mock_midnight.return_value = int(next_midnight)
        
        # When: Get hours until reset
        result = get_hours_until_reset()
        
        # Then: Should be 23 hours (rounded down from 23.5)
        assert result == 23
    
    @patch('pricing_config.time.time')
    @patch('pricing_config.get_next_utc_midnight')
    def test_get_hours_until_reset_few_hours(self, mock_midnight, mock_time):
        """Test hours calculation with few hours remaining."""
        # Given: 20:00 UTC (4 hours before midnight)
        now = 1704067200 + (20 * 3600)  # Jan 1, 2024 20:00 UTC
        next_midnight = now + (4 * 3600)  # 4 hours away
        
        mock_time.return_value = now
        mock_midnight.return_value = int(next_midnight)
        
        # When: Get hours until reset
        result = get_hours_until_reset()
        
        # Then: Should be 4 hours
        assert result == 4
    
    @patch('pricing_config.time.time')
    @patch('pricing_config.get_next_utc_midnight')
    def test_get_hours_until_reset_one_minute(self, mock_midnight, mock_time):
        """Test hours calculation with less than 1 hour remaining."""
        # Given: 59 minutes before midnight
        now = 1704067200 + (23 * 3600) + (59 * 60)
        next_midnight = now + 60  # 1 minute away
        
        mock_time.return_value = now
        mock_midnight.return_value = int(next_midnight)
        
        # When: Get hours until reset
        result = get_hours_until_reset()
        
        # Then: Should be 0 hours (rounded down)
        assert result == 0

    def test_get_next_utc_midnight_returns_integer(self):
        """Verify function returns integer Unix timestamp."""
        result = get_next_utc_midnight()
        assert isinstance(result, int)
        assert result > 0
    
    def test_get_hours_until_reset_returns_integer(self):
        """Verify function returns integer hours."""
        result = get_hours_until_reset()
        assert isinstance(result, int)
        assert 0 <= result <= 24  # Should always be within 24 hours
