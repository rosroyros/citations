#!/usr/bin/env python3
"""
Backfill script to update existing test jobs from citation logs.

Since citations_text column is empty in the database, we need to parse
the citation logs to identify test jobs and update their is_test_job flag.
"""

import sqlite3
import argparse
import logging
import os
import sys
import re
from typing import Set, Tuple
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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


def find_test_jobs_from_logs(log_dir: str) -> Tuple[Set[str], list]:
    """
    Parse all citation logs to find job IDs that contain test citations.

    Returns:
        Tuple of (Set of job IDs, List of (job_id, citation) matches)
    """
    test_job_ids = set()
    test_matches = []  # Store matches for review

    import glob
    import gzip

    # Find all citation log files
    log_files = []

    # Current log
    current_log = os.path.join(log_dir, 'citations.log')
    if os.path.exists(current_log):
        log_files.append(current_log)

    # Rotated logs
    for log_path in glob.glob(os.path.join(log_dir, 'citations.log.[0-9]*')):
        log_files.append(log_path)

    if not log_files:
        logger.warning(f"No citation logs found in {log_dir}")
        return test_job_ids, test_matches

    logger.info(f"Parsing {len(log_files)} citation log files...")

    for log_file in sorted(log_files, reverse=True):  # Process newest first
        logger.debug(f"Processing log file: {os.path.basename(log_file)}")

        # Determine if file is gzipped
        is_gzipped = log_file.endswith('.gz')

        try:
            if is_gzipped:
                f = gzip.open(log_file, 'rt', encoding='utf-8')
            else:
                f = open(log_file, 'r', encoding='utf-8')

            current_job_id = None
            in_citation = False

            for line in f:
                # Check for job ID marker
                if line.startswith('<<JOB_ID:'):
                    current_job_id = line.strip()[9:-2]  # Extract UUID
                    in_citation = True
                    continue

                # If we're in a citation section, check for test patterns
                if in_citation and current_job_id and line.strip():
                    # Test patterns to look for
                    line_lower = line.lower()

                    # Check for any test indicators
                    if any(pattern in line_lower for pattern in [
                        'testtesttest',  # Official marker
                        'e2e test',      # E2E test
                        'test citation', # Test citation
                        'test',          # Any occurrence of test
                        'asdf',          # Placeholder text
                    ]):
                        test_job_ids.add(current_job_id)
                        test_matches.append((current_job_id, line.strip()))
                        logger.debug(f"Found test job {current_job_id}: {line.strip()[:50]}...")

                    # Reset after first non-empty line (job IDs are followed by citations)
                    in_citation = False

            f.close()

        except Exception as e:
            logger.error(f"Error processing {log_file}: {e}")

    logger.info(f"Found {len(test_job_ids)} test jobs in logs")
    return test_job_ids, test_matches


def update_test_jobs(db_path: str, test_job_ids: Set[str], dry_run: bool = False) -> int:
    """
    Update test jobs to set is_test_job = 1.

    Returns:
        Number of records updated
    """
    if not test_job_ids:
        logger.info("No test jobs to update")
        return 0

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # First check which jobs exist in database
            job_id_list = list(test_job_ids)
            placeholders = ','.join(['?'] * len(job_id_list))

            cursor.execute(f"""
                SELECT job_id, DATE(created_at) as date
                FROM validations
                WHERE job_id IN ({placeholders})
                AND (is_test_job IS NULL OR is_test_job = 0)
            """, job_id_list)

            existing_jobs = cursor.fetchall()
            logger.info(f"Found {len(existing_jobs)} test jobs in database to update")

            if dry_run:
                logger.info("\nDRY RUN - Jobs that would be updated:")
                for job_id, date in existing_jobs[:5]:  # Show first 5
                    logger.info(f"  Job {job_id[:8]}... from {date}")
                if len(existing_jobs) > 5:
                    logger.info(f"  ... and {len(existing_jobs) - 5} more")
                return len(existing_jobs)

            # Update the jobs
            update_count = 0
            for job_id, date in existing_jobs:
                cursor.execute("""
                    UPDATE validations
                    SET is_test_job = 1
                    WHERE job_id = ?
                """, (job_id,))
                update_count += 1

            conn.commit()
            logger.info(f"Updated {update_count} test jobs in database")
            return update_count

    except sqlite3.Error as e:
        logger.error(f"Error updating database: {e}")
        return 0


def get_daily_breakdown(db_path: str, test_job_ids: Set[str]) -> dict:
    """
    Get a breakdown of test jobs vs real jobs per day.

    Returns:
        Dictionary with date as key and (test_count, total_count) as value
    """
    daily_stats = {}

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Get total jobs per day (last 30 days)
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as total
                FROM validations
                WHERE created_at >= date('now', '-30 days')
                GROUP BY DATE(created_at)
                ORDER BY date
            """)

            for date, total in cursor.fetchall():
                daily_stats[date] = [0, total]

            # Get test jobs per day
            if test_job_ids:
                job_id_list = list(test_job_ids)
                placeholders = ','.join(['?'] * len(job_id_list))

                cursor.execute(f"""
                    SELECT DATE(created_at) as date, COUNT(*) as test_count
                    FROM validations
                    WHERE job_id IN ({placeholders})
                    AND created_at >= date('now', '-30 days')
                    GROUP BY DATE(created_at)
                """, job_id_list)

                for date, test_count in cursor.fetchall():
                    if date in daily_stats:
                        daily_stats[date][0] = test_count

    except sqlite3.Error as e:
        logger.error(f"Error getting daily breakdown: {e}")

    return daily_stats


def main():
    parser = argparse.ArgumentParser(description='Backfill test job flags from citation logs')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be updated without making changes')
    parser.add_argument('--db-path', type=str, default='/opt/citations/dashboard/data/validations.db',
                       help='Path to validations database')
    parser.add_argument('--log-dir', type=str, default='/opt/citations/logs',
                       help='Directory containing citation logs')
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
    logger.info(f"Using log directory: {args.log_dir}")

    # Create backup unless disabled or in dry-run mode
    backup_path = None
    if not args.dry_run and not args.no_backup:
        backup_path = backup_database(args.db_path)

    # Find test jobs from logs
    logger.info("Searching for test jobs in citation logs...")
    test_job_ids, test_matches = find_test_jobs_from_logs(args.log_dir)

    if not test_job_ids:
        logger.info("No test jobs found in logs")
        return

    # Show sample of matched citations
    logger.info(f"\nSample of citations matched as test jobs (showing first 20):")
    for i, (job_id, citation) in enumerate(test_matches[:20]):
        logger.info(f"  {i+1}. {job_id[:8]}...: {citation[:100]}...")
    if len(test_matches) > 20:
        logger.info(f"  ... and {len(test_matches) - 20} more")

    # Get daily breakdown
    logger.info("\nAnalyzing daily statistics...")
    daily_stats = get_daily_breakdown(args.db_path, test_job_ids)

    logger.info("\nDaily Breakdown (Test Jobs vs Total Jobs):")
    for date, (test_count, total_count) in sorted(daily_stats.items()):
        percentage = (test_count / total_count * 100) if total_count > 0 else 0
        logger.info(f"  {date}: {test_count}/{total_count} test jobs ({percentage:.1f}%)")

    # Update test jobs
    logger.info(f"\n{'DRY RUN: ' if args.dry_run else ''}Updating test jobs...")
    updated_count = update_test_jobs(args.db_path, test_job_ids, args.dry_run)

    # Summary
    logger.info(f"\nSummary:")
    logger.info(f"  Total test jobs found in logs: {len(test_job_ids)}")
    logger.info(f"  Jobs in database to update: {updated_count}")

    if args.dry_run:
        logger.info(f"\nDRY RUN: No changes made. Run without --dry-run to apply updates.")


if __name__ == '__main__':
    main()