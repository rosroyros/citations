#!/usr/bin/env python3
"""
Performance test for log parser module.
Tests parsing performance with 3 days of synthetic log data.
"""

import time
import sys
import os
from datetime import datetime, timedelta
import random
import string

# Add the dashboard directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from log_parser import parse_logs, parse_job_events, parse_metrics, find_job_by_timestamp


def generate_sample_log_lines(num_jobs=1000, hours_back=72):
    """
    Generate synthetic log lines for performance testing.

    Args:
        num_jobs: Number of jobs to simulate
        hours_back: How many hours back to start from

    Returns:
        List of log lines
    """
    log_lines = []
    start_time = datetime.now() - timedelta(hours=hours_back)

    for i in range(num_jobs):
        job_id = f"{''.join(random.choices(string.hexdigits.lower(), k=8))}-{''.join(random.choices(string.hexdigits.lower(), k=4))}-{''.join(random.choices(string.hexdigits.lower(), k=4))}-{''.join(random.choices(string.hexdigits.lower(), k=4))}-{''.join(random.choices(string.hexdigits.lower(), k=12))}"
        user_type = random.choice(["free", "paid"])

        # Job creation time (random within the time range)
        created_time = start_time + timedelta(
            hours=random.uniform(0, hours_back),
            minutes=random.uniform(0, 60),
            seconds=random.uniform(0, 60)
        )

        # Job completion time (30-120 seconds later)
        duration = random.uniform(30, 120)
        completed_time = created_time + timedelta(seconds=duration)

        # Citation count (1-10)
        citation_count = random.randint(1, 10)

        # Create log lines
        log_lines.append(f"{created_time.strftime('%Y-%m-%d %H:%M:%S')} - citation_validator - INFO - app.py:590 - Creating async job {job_id} for {user_type} user")

        # Add some LLM call log lines
        log_lines.append(f"{(created_time + timedelta(seconds=10)).strftime('%Y-%m-%d %H:%M:%S')} - openai_provider - INFO - openai_provider.py:43 - Starting validation for {random.randint(1000, 5000)} characters of citation text")

        # Duration log line
        log_lines.append(f"{(created_time + timedelta(seconds=10 + duration/2)).strftime('%Y-%m-%d %H:%M:%S')} - openai_provider - INFO - openai_provider.py:101 - OpenAI API call completed in {duration:.1f}s")

        # Citation result log line
        log_lines.append(f"{completed_time.strftime('%Y-%m-%d %H:%M:%S')} - citation_validator - INFO - app.py:119 - Found {citation_count} citation result{'s' if citation_count > 1 else ''}")

        # Job completion log line
        log_lines.append(f"{completed_time.strftime('%Y-%m-%d %H:%M:%S')} - citation_validator - INFO - app.py:539 - Job {job_id}: Completed successfully")

    # Sort by timestamp
    log_lines.sort(key=lambda line: line[:19])  # Sort by timestamp part

    return log_lines


def test_performance_parse_job_events():
    """Test performance of parse_job_events function."""
    print("Testing parse_job_events performance...")

    log_lines = generate_sample_log_lines(1000, 72)  # 1000 jobs over 72 hours

    start_time = time.time()
    jobs = parse_job_events(log_lines)
    end_time = time.time()

    duration = end_time - start_time
    print(f"  Parsed {len(jobs)} jobs from {len(log_lines)} log lines")
    print(f"  Time: {duration:.3f} seconds")
    print(f"  Rate: {len(log_lines)/duration:.0f} lines/second")

    # Verify results
    assert len(jobs) == 1000, f"Expected 1000 jobs, got {len(jobs)}"

    for job_id, job in jobs.items():
        assert "job_id" in job
        assert "created_at" in job
        assert "user_type" in job
        assert "status" in job
        assert job["status"] == "completed"

    print("  ✓ All assertions passed")
    return duration


def test_performance_two_pass_parsing():
    """Test performance of complete two-pass parsing."""
    print("\nTesting complete two-pass parsing performance...")

    log_lines = generate_sample_log_lines(1000, 72)  # 1000 jobs over 72 hours

    # Pass 1: Parse job events
    start_time = time.time()
    jobs = parse_job_events(log_lines)
    pass1_time = time.time() - start_time

    # Pass 2: Parse metrics
    start_time = time.time()
    jobs = parse_metrics(log_lines, jobs)
    pass2_time = time.time() - start_time

    total_time = pass1_time + pass2_time

    print(f"  Parsed {len(jobs)} jobs from {len(log_lines)} log lines")
    print(f"  Pass 1 (job events): {pass1_time:.3f} seconds")
    print(f"  Pass 2 (metrics): {pass2_time:.3f} seconds")
    print(f"  Total time: {total_time:.3f} seconds")
    print(f"  Overall rate: {len(log_lines)/total_time:.0f} lines/second")

    # Verify metrics were extracted
    jobs_with_duration = sum(1 for job in jobs.values() if "duration_seconds" in job)
    jobs_with_citations = sum(1 for job in jobs.values() if "citation_count" in job)

    print(f"  Jobs with duration: {jobs_with_duration}/{len(jobs)}")
    print(f"  Jobs with citations: {jobs_with_citations}/{len(jobs)}")

    return total_time


def test_performance_find_job_by_timestamp():
    """Test performance of find_job_by_timestamp function."""
    print("\nTesting find_job_by_timestamp performance...")

    # Create jobs
    jobs = {}
    start_time = datetime.now() - timedelta(hours=72)

    for i in range(1000):
        job_id = f"job-{i:04d}"
        created_time = start_time + timedelta(minutes=i*4)  # Job every 4 minutes
        jobs[job_id] = {
            "job_id": job_id,
            "created_at": created_time,
            "user_type": "free",
            "status": "completed",
            "completed_at": created_time + timedelta(seconds=60)
        }

    # Test finding jobs by timestamp
    test_timestamps = [
        start_time + timedelta(minutes=i*4 + 30)  # 30 minutes into each job
        for i in range(1000)
    ]

    start_time = time.time()
    found_jobs = []
    for timestamp in test_timestamps:
        job = find_job_by_timestamp(jobs, timestamp)
        if job:
            found_jobs.append(job)

    end_time = time.time()
    duration = end_time - start_time

    print(f"  Found {len(found_jobs)} jobs out of {len(test_timestamps)} searches")
    print(f"  Time: {duration:.3f} seconds")
    print(f"  Rate: {len(test_timestamps)/duration:.0f} searches/second")

    # Verify all jobs were found
    assert len(found_jobs) == 1000, f"Expected 1000 jobs found, got {len(found_jobs)}"

    print("  ✓ All jobs found successfully")
    return duration


def test_performance_goal():
    """Test if we meet the performance goal of parsing 3 days in <30 seconds."""
    print("\n" + "="*60)
    print("PERFORMANCE GOAL TEST")
    print("Goal: Parse 3 days of logs in <30 seconds")
    print("="*60)

    # Generate data equivalent to 3 days of logs
    # Assuming roughly 1000 jobs per day
    log_lines = generate_sample_log_lines(3000, 72)  # 3000 jobs over 72 hours

    print(f"Generated {len(log_lines)} log lines ({len(log_lines)//5} jobs)")

    # Test complete parsing
    start_time = time.time()
    jobs = parse_job_events(log_lines)
    jobs = parse_metrics(log_lines, jobs)
    end_time = time.time()

    total_time = end_time - start_time

    print(f"Total parsing time: {total_time:.3f} seconds")
    print(f"Performance goal: <30 seconds")

    if total_time < 30:
        print(f"✅ PASS: {total_time:.3f}s < 30s")
        print(f"Performance margin: {30 - total_time:.3f} seconds faster than goal")
    else:
        print(f"❌ FAIL: {total_time:.3f}s > 30s")
        print(f"Over goal by: {total_time - 30:.3f} seconds")

    return total_time < 30


def main():
    """Run all performance tests."""
    print("Log Parser Performance Tests")
    print("="*60)

    # Run individual performance tests
    parse_events_time = test_performance_parse_job_events()
    two_pass_time = test_performance_two_pass_parsing()
    find_job_time = test_performance_find_job_by_timestamp()

    # Test overall performance goal
    goal_met = test_performance_goal()

    print("\n" + "="*60)
    print("PERFORMANCE SUMMARY")
    print("="*60)
    print(f"parse_job_events():     {parse_events_time:.3f}s")
    print(f"two_pass_parsing():     {two_pass_time:.3f}s")
    print(f"find_job_by_timestamp(): {find_job_time:.3f}s")
    print(f"30-second goal met:     {'✅ YES' if goal_met else '❌ NO'}")

    if goal_met:
        print("\n🎉 All performance goals achieved!")
        return 0
    else:
        print("\n⚠️  Performance goals not met. Consider optimization.")
        return 1


if __name__ == '__main__':
    exit(main())