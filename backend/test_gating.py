"""
Tests for Gating Logic

This module tests the gating functionality that determines when validation results
should be gated behind user interaction for free tier users.
"""

import pytest
import os

# Set up environment for gating tests FIRST
os.environ['GATED_RESULTS_ENABLED'] = 'true'

# NOW import the module
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

    def test_free_user_with_partial_data_results_should_be_gated(self):
        """
        Test that free users with partial data are gated for engagement tracking.

        After our change, ALL partial results for free users should be gated.
        """
        user_type = 'free'
        validation_response = {
            'partial': True,
            'results': [
                {'citation_number': 1, 'original': 'Test', 'errors': []}
            ]
        }

        should_gate, reason = should_gate_results_sync(user_type, validation_response)

        # Should be gated - all partial results are now gated
        assert should_gate is True, f"Free users with partial data results should be gated. Got {should_gate} with reason: {reason}"

    def test_paid_user_at_limit_should_not_be_gated(self):
        """
        Test that paid users are never gated, even with partial/empty results.
        """
        user_type = 'paid'
        validation_response = {
            'partial': True,
            'results': []
        }

        should_gate, reason = should_gate_results_sync(user_type, validation_response)

        # Paid users should never be gated
        assert should_gate is False, f"Paid users should never be gated. Got {should_gate} with reason: {reason}"

    def test_free_user_with_full_results_should_be_gated(self):
        """
        Test that free users with full results are gated (existing behavior).

        Note: The system gates ALL free users, not just partial results.
        We're ensuring partial results follow this same pattern.
        """
        user_type = 'free'
        validation_response = {
            'partial': False,
            'results': [
                {'citation_number': 1, 'original': 'Test', 'errors': []},
                {'citation_number': 2, 'original': 'Test 2', 'errors': []}
            ]
        }

        should_gate, reason = should_gate_results_sync(user_type, validation_response)

        # Should be gated - all free users are gated
        assert should_gate is True, f"Free users with full results should be gated. Got {should_gate} with reason: {reason}"