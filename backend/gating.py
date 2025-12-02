"""
Gated Results Tracking Module

This module implements the business logic for determining when validation results
should be gated behind user interaction, based on user type, result quality,
and system configuration.

The approach uses simple, deterministic rules and relies on structured logging
for analytics, not database writes.
"""

import os
from typing import Dict, Any, Optional
from fastapi import Request
from logger import setup_logger

logger = setup_logger("gating")

# Feature flag - can be controlled via environment variable
GATED_RESULTS_ENABLED = os.getenv('GATED_RESULTS_ENABLED', 'false').lower() == 'true'

def get_user_type(request: Request) -> str:
    """
    Determine user type from authentication headers and tokens.

    Args:
        request: FastAPI Request object containing headers

    Returns:
        str: User type ('paid', 'free', or 'anonymous')
    """
    token = request.headers.get('X-User-Token')
    if token:
        logger.debug(f"User identified as paid via token: {token[:8]}...")
        return 'paid'

    free_used_header = request.headers.get('X-Free-Used')
    if free_used_header is not None:
        logger.debug("User identified as free via X-Free-Used header")
        return 'free'

    logger.debug("User identified as anonymous (defaulting to free behavior)")
    return 'anonymous'


def should_gate_results(
    user_type: str,
    results: Dict[str, Any],
    validation_success: bool
) -> bool:
    """
    Determine if validation results should be gated based on business rules.

    Args:
        user_type: Type of user ('paid', 'free', 'anonymous')
        results: Validation results dictionary from LLM provider
        validation_success: Whether validation completed without processing errors

    Returns:
        bool: True if results should be gated, False otherwise
    """
    if not GATED_RESULTS_ENABLED:
        logger.debug("Gating disabled - results will be shown directly")
        return False

    if user_type not in ['free', 'anonymous']:
        logger.debug(f"User type '{user_type}' bypasses gating")
        return False

    if not validation_success:
        logger.debug("Validation errors bypass gating")
        return False

    if results.get('isPartial', False):
        # Only bypass gating if there are actually results being shown
        if results.get('results'):
            logger.debug("Partial results with data bypass gating")
            return False
        # If partial but empty results (limit reached), continue to gating logic
        logger.info("Partial results with NO data. Applying standard gating logic.")

    # Frontend gates all free users, so we log gating decisions for all free users
    # This ensures dashboard can track when gating modal was shown vs actual result limitation
    reason = "Free user gating modal policy"
    logger.info(f"Results gated for {user_type} user ({reason})")
    return True


def should_gate_results_sync(
    user_type: str,
    validation_response: Dict[str, Any],
    validation_success: bool = True
) -> tuple[bool, str]:
    """
    Helper function for synchronous validation endpoint.

    Converts ValidationResponse format to the format expected by should_gate_results.

    Args:
        user_type: Type of user ('paid', 'free', 'anonymous')
        validation_response: ValidationResponse dictionary
        validation_success: Whether validation completed without processing errors

    Returns:
        tuple: (bool, str) - (should_gate, reason)
    """
    results_dict = {
        'isPartial': validation_response.get('partial', False),
        'results': validation_response.get('results', [])
    }

    # Call should_gate_results to get the decision
    should_gate = should_gate_results(user_type, results_dict, validation_success)

    # Determine the reason based on user type and gating decision
    if should_gate:
        if user_type == 'free':
            reason = "Free user gating modal policy"
        elif user_type == 'anonymous':
            reason = "Anonymous user gating modal policy"
        else:
            reason = "User gating policy"
    else:
        if user_type not in ['free', 'anonymous']:
            reason = "Paid user bypasses gating"
        elif not validation_success:
            reason = "Validation errors bypass gating"
        elif results_dict.get('isPartial', False) and results_dict.get('results'):
            reason = "Partial results with data bypass gating"
        else:
            reason = "Gating disabled"

    return should_gate, reason


def log_gating_event(
    job_id: str,
    user_type: str,
    results_gated: bool,
    reason: Optional[str] = None
) -> None:
    """
    Log gating decision for dashboard parsing and analytics using a structured format.

    Args:
        job_id: Unique identifier for the validation job
        user_type: Type of user ('paid', 'free', 'anonymous')
        results_gated: Whether results were gated
        reason: Optional reason for the decision
    """
    reason_str = reason if reason else "N/A"
    logger.info(
        f"GATING_DECISION: job_id={job_id} user_type={user_type} results_gated={results_gated} reason='{reason_str}'"
    )