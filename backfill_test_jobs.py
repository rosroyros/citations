#!/usr/bin/env python3
"""
Backfill script to update existing records with 'test' in citations to have is_test_job=True.

This script should be run once to update historical data before the testtesttest
marker was introduced. It identifies validation jobs that contain 'test' in their
citation text and marks them as test jobs.

Usage:
    python3 backfill_test_jobs.py [--dry-run] [--db-path /path/to/validations.db]

Options:
    --dry-run: Show what would be updated without making changes
    --db-path: Path to the validations database (default: dashboard/data/validations.db)
"""

import sqlite3
import argparse
import logging
import os
import sys
from typing import List, Tuple
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_default_db_path() -> str:
    """Get default database path."""
    # Try to find the database relative to this script
    script_dir = Path(__file__).parent
    db_path = script_dir / 'dashboard' / 'data' / 'validations.db'

    # If not found, try current working directory
    if not db_path.exists():
        db_path = Path.cwd() / 'dashboard' / 'data' / 'validations.db'

    return str(db_path)


def check_database_schema(db_path: str) -> bool:
    """Check if the database has the required columns."""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(validations)")
            columns = [row[1] for row in cursor.fetchall()]

            has_is_test_job = 'is_test_job' in columns
            has_citations = 'citations' in columns

            logger.info(f"Database columns: {columns}")

            if not has_is_test_job:
                logger.error("Database schema missing 'is_test_job' column")
                return False

            if not has_citations:
                logger.warning("Database schema missing 'citations' column - will check log-based records")

            return True

    except sqlite3.Error as e:
        logger.error(f"Error checking database schema: {e}")
        return False


def find_test_jobs(db_path: str) -> List[Tuple[str, str]]:
    """
    Find validation jobs that contain 'test' in their citations.

    Returns:
        List of tuples (job_id, citations_text)
    """
    test_jobs = []

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Check if citations column exists
            cursor.execute("PRAGMA table_info(validations)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'citations_text' in columns:
                # Query records with 'test' or 'asdf' in citations (case-insensitive)
                cursor.execute("""
                    SELECT job_id, citations_text
                    FROM validations
                    WHERE (LOWER(citations_text) LIKE '%test%'
                           OR LOWER(citations_text) LIKE '%asdf%')
                    AND (is_test_job IS NULL OR is_test_job = 0)
                """)
                test_jobs = cursor.fetchall()
                logger.info(f"Found {len(test_jobs)} records with 'test' or 'asdf' in citations_text column")
            else:
                # If no citations column, we need to check logs instead
                logger.warning("No citations column found - checking logs for test patterns")
                # This would require parsing logs, which is more complex
                # For now, just report the limitation
                logger.info("To identify test jobs from logs, run: grep -i 'test' /opt/citations/logs/citations.log")

    except sqlite3.Error as e:
        logger.error(f"Error querying database: {e}")

    return test_jobs


def get_daily_breakdown(db_path: str, test_jobs: List[Tuple[str, str]]) -> dict:
    """
    Get a breakdown of test jobs vs real jobs per day.

    Returns:
        Dictionary with date as key and (test_count, total_count) as value
    """
    daily_stats = {}

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Get total jobs per day
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as total
                FROM validations
                WHERE created_at IS NOT NULL
                GROUP BY DATE(created_at)
                ORDER BY date
            """)

            for date, total in cursor.fetchall():
                daily_stats[date] = [0, total]

            # Get test jobs per day (from our identified list)
            job_ids = [job_id for job_id, _ in test_jobs]
            if job_ids:
                placeholders = ','.join(['?'] * len(job_ids))
                cursor.execute(f"""
                    SELECT DATE(created_at) as date, COUNT(*) as test_count
                    FROM validations
                    WHERE job_id IN ({placeholders})
                    AND created_at IS NOT NULL
                    GROUP BY DATE(created_at)
                """, job_ids)

                for date, test_count in cursor.fetchall():
                    if date in daily_stats:
                        daily_stats[date][0] = test_count
    except sqlite3.Error as e:
        logger.error(f"Error getting daily breakdown: {e}")

    return daily_stats


def update_test_jobs(db_path: str, test_jobs: List[Tuple[str, str]], dry_run: bool = False) -> int:
    """
    Update test jobs to set is_test_job = True.

    Returns:
        Number of records updated
    """
    updated_count = 0

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            for job_id, citations in test_jobs:
                # Additional filtering to avoid false positives
                # Only mark as test job if it looks like a genuine test
                if is_likely_test_job(citations):
                    if dry_run:
                        logger.info(f"DRY RUN: Would update job {job_id} as test job")
                        logger.info(f"  Citations: {citations[:100]}...")
                    else:
                        cursor.execute("""
                            UPDATE validations
                            SET is_test_job = 1
                            WHERE job_id = ?
                        """, (job_id,))
                        logger.info(f"Updated job {job_id} as test job")
                        logger.info(f"  Citations: {citations[:100]}...")

                    updated_count += 1
                else:
                    logger.debug(f"Skipping job {job_id} - doesn't appear to be a test job")
                    logger.debug(f"  Citations: {citations[:100]}...")

            if not dry_run:
                conn.commit()
                logger.info(f"Committed {updated_count} updates to database")

    except sqlite3.Error as e:
        logger.error(f"Error updating database: {e}")

    return updated_count


def is_likely_test_job(citations: str) -> bool:
    """
    Determine if a citation is likely from a test job.
    Simple check for 'test' or 'asdf' in citations.
    """
    if not citations:
        return False

    citations_lower = citations.lower()

    # Simple check - look for 'test' or 'asdf'
    return 'test' in citations_lower or 'asdf' in citations_lower


def backup_database(db_path: str) -> str:
    """Create a backup of the database and return the backup path."""
    import shutil
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup.{timestamp}"

    logger.info(f"Creating database backup at: {backup_path}")
    shutil.copy2(db_path, backup_path)

    # Verify backup was created
    if not os.path.exists(backup_path) or os.path.getsize(backup_path) != os.path.getsize(db_path):
        logger.error("Database backup verification failed")
        sys.exit(1)

    logger.info(f"Database backup successful ({os.path.getsize(backup_path)} bytes)")
    return backup_path


def main():
    parser = argparse.ArgumentParser(description='Backfill test job flags')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be updated without making changes')
    parser.add_argument('--db-path', type=str, default=get_default_db_path(),
                       help='Path to validations database')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip database backup (not recommended)')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Validate database path
    if not os.path.exists(args.db_path):
        logger.error(f"Database not found at: {args.db_path}")
        sys.exit(1)

    logger.info(f"Using database: {args.db_path}")

    # Check database schema
    if not check_database_schema(args.db_path):
        logger.error("Database schema check failed")
        sys.exit(1)

    # Create backup unless disabled or in dry-run mode
    backup_path = None
    if not args.dry_run and not args.no_backup:
        backup_path = backup_database(args.db_path)

    # Find test jobs
    logger.info("Searching for test jobs...")
    test_jobs = find_test_jobs(args.db_path)

    if not test_jobs:
        logger.info("No test jobs found to update")
        return

    logger.info(f"Found {len(test_jobs)} potential test jobs")

    # Show sample of what will be updated
    logger.info("\nSample of jobs to be updated:")
    for i, (job_id, citations) in enumerate(test_jobs[:3]):
        logger.info(f"  {i+1}. Job {job_id}: {citations[:80]}...")

    if len(test_jobs) > 3:
        logger.info(f"  ... and {len(test_jobs) - 3} more")

    # Update test jobs
    logger.info(f"\n{'DRY RUN: ' if args.dry_run else ''}Updating test jobs...")
    updated_count = update_test_jobs(args.db_path, test_jobs, args.dry_run)

    if args.dry_run:
        logger.info(f"DRY RUN: Would update {updated_count} records")
    else:
        logger.info(f"Updated {updated_count} records")

    # Show daily breakdown
    if not args.dry_run or test_jobs:
        logger.info("\nDaily Breakdown (Test Jobs vs Total Jobs):")
        daily_stats = get_daily_breakdown(args.db_path, test_jobs)

        for date, (test_count, total_count) in sorted(daily_stats.items()):
            percentage = (test_count / total_count * 100) if total_count > 0 else 0
            logger.info(f"  {date}: {test_count}/{total_count} test jobs ({percentage:.1f}%)")

    # Summary
    logger.info(f"\nSummary:")
    logger.info(f"  Total records checked: {len(test_jobs)}")
    logger.info(f"  Records identified as test jobs: {updated_count}")
    logger.info(f"  Records skipped (likely legitimate): {len(test_jobs) - updated_count}")


if __name__ == '__main__':
    main()