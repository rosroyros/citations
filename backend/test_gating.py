"""
Tests for Gating Logic

This module tests the gating functionality that determines when validation results
should be gated behind user interaction for free tier users.
"""

import pytest
import os
from gating import should_gate_results, should_gate_results_sync


class TestGatingLogic:
    """Test gating decision logic for different user scenarios."""

    def test_free_user_at_limit_with_empty_results_should_be_gated(self):
        """
        Test that free users who hit their limit (partial=true, empty results) are gated.

        This is the core bug we're fixing - users at limit should see gated overlay,
        not empty results.
        """
        # Test using the lower-level should_gate_results function directly
        # since it doesn't rely on module-level environment variables
        from gating import should_gate_results

        # Simulate a free user who hit their 10-citation limit
        user_type = 'free'
        results_dict = {
            'isPartial': True,  # Partial result due to limit
            'results': []     # No results shown (all locked behind gate)
        }

        # Test the core logic directly (bypassing GATED_RESULTS_ENABLED check)
        # We expect this to return True (gated) after our fix
        result = should_gate_results(user_type, results_dict, True)

        # Test expectation - user at limit should be gated
        assert result is True, "Free users at limit with empty results should be gated"

    def test_free_user_with_partial_data_results_should_not_be_gated(self):
        """
        Test that free users with partial data (e.g., timeouts) are not gated.

        This ensures we don't break legitimate partial results scenarios.
        """
        user_type = 'free'
        validation_response = {
            'partial': True,
            'results': [
                {'citation_number': 1, 'original': 'Test', 'errors': []}
            ]
        }

        result = should_gate_results_sync(user_type, validation_response)

        # Should not be gated - user can see some results
        assert result is False, "Free users with partial data results should not be gated"

    def test_paid_user_at_limit_should_not_be_gated(self):
        """
        Test that paid users are never gated, even with partial/empty results.
        """
        user_type = 'paid'
        validation_response = {
            'partial': True,
            'results': []
        }

        result = should_gate_results_sync(user_type, validation_response)

        # Paid users should never be gated
        assert result is False, "Paid users should never be gated"

    def test_free_user_with_full_results_should_not_be_gated(self):
        """
        Test that free users under limit with full results are not gated.
        """
        user_type = 'free'
        validation_response = {
            'partial': False,
            'results': [
                {'citation_number': 1, 'original': 'Test', 'errors': []},
                {'citation_number': 2, 'original': 'Test 2', 'errors': []}
            ]
        }

        result = should_gate_results_sync(user_type, validation_response)

        # Should not be gated - under limit with full results
        assert result is False, "Free users under limit with full results should not be gated"