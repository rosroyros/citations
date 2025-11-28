"""
Gated Results Tracking Module

This module implements the business logic for determining when validation results
should be gated behind user interaction, based on user type, result quality,
and system configuration.

The approach uses simple, deterministic rules rather than complex behavioral
analysis to ensure reliability and maintainability.
"""

import os
from datetime import datetime
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
    # Check for paid user token
    token = request.headers.get('X-User-Token')
    if token:
        # Could further validate token against database here if needed
        # For now, any token = paid user
        logger.debug(f"User identified as paid via token: {token[:8]}...")
        return 'paid'

    # Check for free session indicators
    free_used_header = request.headers.get('X-Free-Used')
    if free_used_header is not None:
        logger.debug("User identified as free via X-Free-Used header")
        return 'free'

    # Default to anonymous - treat as free for gating purposes
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
    # Early exit if feature flag is disabled
    if not GATED_RESULTS_ENABLED:
        logger.debug("Gating disabled - results will be shown directly")
        return False

    # Rule 1: Only gate free/anonymous users
    if user_type not in ['free', 'anonymous']:
        logger.debug(f"User type '{user_type}' bypasses gating")
        return False

    # Rule 2: Don't gate if validation had processing errors
    if not validation_success:
        logger.debug("Validation errors bypass gating")
        return False

    # Rule 3: Don't gate partial results (citation limits reached)
    if results.get('isPartial', False):
        logger.debug("Partial results bypass gating")
        return False

    # Rule 4: Don't gate if there are validation errors in results
    errors = results.get('errors', [])
    if errors:
        logger.debug(f"Validation errors found ({len(errors)}) bypass gating")
        return False

    # All checks passed - gate the results
    logger.info(f"Results gated for {user_type} user")
    return True


def should_gate_results_sync(
    user_type: str,
    validation_response: Dict[str, Any],
    validation_success: bool = True
) -> bool:
    """
    Helper function for synchronous validation endpoint.

    Converts ValidationResponse format to the format expected by should_gate_results.

    Args:
        user_type: Type of user ('paid', 'free', 'anonymous')
        validation_response: ValidationResponse dictionary
        validation_success: Whether validation completed without processing errors

    Returns:
        bool: True if results should be gated, False otherwise
    """
    # Convert ValidationResponse to expected format
    results = {
        'isPartial': validation_response.get('partial', False),
        'errors': []  # ValidationResponse doesn't expose individual errors directly
    }

    # Check if results are empty (could indicate citation limit reached)
    if not validation_response.get('results'):
        results['isPartial'] = True
        logger.debug("Empty results indicate citation limit reached")

    return should_gate_results(user_type, results, validation_success)


async def store_gated_results(
    job_id: str,
    results_gated: bool,
    user_type: str,
    results: Dict[str, Any],
    db_conn=None
) -> None:
    """
    Store initial gating decision and metadata in database.

    Args:
        job_id: Unique identifier for the validation job
        results_gated: Whether results were gated
        user_type: Type of user ('paid', 'free', 'anonymous')
        results: Validation results dictionary
        db_conn: Optional database connection (for transactions)
    """
    try:
        # Import here to avoid circular dependencies
        from database import get_validations_db_path
        import sqlite3

        if not db_conn:
            db_path = get_validations_db_path()
            db_conn = sqlite3.connect(db_path)
            should_close = True
        else:
            should_close = False

        cursor = db_conn.cursor()

        # Update validation tracking record
        now = datetime.utcnow().isoformat()
        cursor.execute('''
            UPDATE validations
            SET results_gated = ?,
                user_type = ?,
                gated_at = ?,
                updated_at = ?
            WHERE job_id = ?
        ''', (
            results_gated,
            user_type,
            now if results_gated else None,
            now,
            job_id
        ))

        db_conn.commit()

        if should_close:
            db_conn.close()

        logger.info(f"Stored gating decision for job {job_id}: gated={results_gated}, user_type={user_type}")

    except Exception as e:
        logger.error(f"Failed to store gating decision for job {job_id}: {str(e)}")
        # Don't raise - gating storage failure shouldn't break validation flow


def log_gating_event(
    job_id: str,
    user_type: str,
    results_gated: bool,
    reason: Optional[str] = None
) -> None:
    """
    Log gating decision for dashboard parsing and analytics.

    Args:
        job_id: Unique identifier for the validation job
        user_type: Type of user ('paid', 'free', 'anonymous')
        results_gated: Whether results were gated
        reason: Optional reason for the decision
    """
    if results_gated:
        logger.info(f"RESULTS_READY_GATED: job_id={job_id}, user_type={user_type}")
    else:
        logger.info(f"RESULTS_READY_DIRECT: job_id={job_id}, user_type={user_type}, reason={reason or 'No gating needed'}")


def get_gating_summary() -> Dict[str, Any]:
    """
    Get summary statistics for gated results analytics.

    Returns:
        dict: Summary of gating statistics
    """
    try:
        import sqlite3
        from database import get_validations_db_path

        db_path = get_validations_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get gating statistics
        cursor.execute('''
            SELECT
                COUNT(*) as total_validations,
                COUNT(CASE WHEN results_gated = 1 THEN 1 END) as gated_count,
                COUNT(CASE WHEN results_gated = 0 THEN 1 END) as direct_count,
                COUNT(CASE WHEN user_type = 'free' THEN 1 END) as free_users,
                COUNT(CASE WHEN user_type = 'paid' THEN 1 END) as paid_users
            FROM validations
            WHERE created_at >= datetime('now', '-24 hours')
        ''')

        stats = cursor.fetchone()
        conn.close()

        if stats and stats[0] > 0:
            total, gated, direct, free, paid = stats
            return {
                'total_validations': total,
                'gated_results': gated,
                'direct_results': direct,
                'gating_rate': round((gated / total) * 100, 1) if total > 0 else 0,
                'free_users': free,
                'paid_users': paid,
                'feature_enabled': GATED_RESULTS_ENABLED
            }

        return {
            'total_validations': 0,
            'gated_results': 0,
            'direct_results': 0,
            'gating_rate': 0,
            'free_users': 0,
            'paid_users': 0,
            'feature_enabled': GATED_RESULTS_ENABLED
        }

    except Exception as e:
        logger.error(f"Failed to get gating summary: {str(e)}")
        return {
            'total_validations': 0,
            'gated_results': 0,
            'direct_results': 0,
            'gating_rate': 0,
            'free_users': 0,
            'paid_users': 0,
            'feature_enabled': GATED_RESULTS_ENABLED,
            'error': str(e)
        }