import re
from datetime import datetime
from typing import Optional, Dict, Any, List
import gzip


def extract_timestamp(log_line: str) -> Optional[datetime]:
    """
    Extract timestamp from a log line.

    Args:
        log_line: The log line to extract timestamp from

    Returns:
        datetime object if timestamp found, None otherwise
    """
    # Pattern matches: 2025-11-04 21:42:48
    timestamp_pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
    match = re.search(timestamp_pattern, log_line)

    if match:
        timestamp_str = match.group(1)
        try:
            return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None

    return None


def extract_creation(log_line: str) -> Optional[tuple]:
    """
    Extract job creation information from a log line.

    Args:
        log_line: The log line to extract job creation info from

    Returns:
        tuple of (job_id, timestamp, user_type) if found, None otherwise
    """
    # Pattern matches: Creating async job abc-123 for free user
    creation_pattern = r'Creating async job ([a-f0-9-]+) for (free|paid) user'
    match = re.search(creation_pattern, log_line)

    if match:
        job_id = match.group(1)
        user_type = match.group(2)

        # Extract timestamp from the beginning of the line
        timestamp = extract_timestamp(log_line)

        if timestamp:
            return job_id, timestamp, user_type

    return None


def extract_completion(log_line: str) -> Optional[tuple]:
    """
    Extract job completion information from a log line.

    Args:
        log_line: The log line to extract job completion info from

    Returns:
        tuple of (job_id, timestamp) if found, None otherwise
    """
    # Pattern matches: Job abc-123: Completed successfully
    completion_pattern = r'Job ([a-f0-9-]+): Completed successfully'
    match = re.search(completion_pattern, log_line)

    if match:
        job_id = match.group(1)

        # Extract timestamp from the beginning of the line
        timestamp = extract_timestamp(log_line)

        if timestamp:
            return job_id, timestamp

    return None


def extract_duration(log_line: str) -> Optional[float]:
    """
    Extract LLM API call duration from a log line.

    Args:
        log_line: The log line to extract duration from

    Returns:
        float duration in seconds if found, None otherwise
    """
    # Pattern matches: OpenAI API call completed in 47.0s
    duration_pattern = r'OpenAI API call completed in ([\d.]+)s'
    match = re.search(duration_pattern, log_line)

    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None

    return None


def extract_citation_count(log_line: str) -> Optional[int]:
    """
    Extract citation count from a log line.

    Args:
        log_line: The log line to extract citation count from

    Returns:
        int citation count if found, None otherwise
    """
    # Pattern matches: Found 1 citation result(s) or Found 5 citation results
    citation_pattern = r'Found (\d+) citation results?(?:\(s\))?'
    match = re.search(citation_pattern, log_line)

    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None

    return None


def parse_job_events(log_lines: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Pass 1: Extract job lifecycle events from log lines.

    Args:
        log_lines: List of log lines to parse

    Returns:
        Dictionary of jobs indexed by job_id
    """
    jobs = {}

    for line in log_lines:
        # Check for job creation
        creation_result = extract_creation(line)
        if creation_result:
            job_id, timestamp, user_type = creation_result
            jobs[job_id] = {
                "job_id": job_id,
                "created_at": timestamp,
                "user_type": user_type,
                "status": "pending"
            }
            continue

        # Check for job completion
        completion_result = extract_completion(line)
        if completion_result:
            job_id, timestamp = completion_result
            if job_id in jobs:
                jobs[job_id]["completed_at"] = timestamp
                jobs[job_id]["status"] = "completed"
            continue

        # Check for job failure (basic implementation)
        if "Failed" in line and "Job" in line:
            failure_pattern = r'Job ([a-f0-9-]+): Failed with error: (.+)'
            match = re.search(failure_pattern, line)
            if match:
                job_id = match.group(1)
                error_message = match.group(2)
                timestamp = extract_timestamp(line)
                if job_id in jobs:
                    jobs[job_id]["status"] = "failed"
                    jobs[job_id]["error_message"] = error_message
                    if timestamp:
                        jobs[job_id]["completed_at"] = timestamp

    return jobs


def find_job_by_timestamp(jobs: Dict[str, Dict[str, Any]], timestamp: datetime, window_seconds: int = 120) -> Optional[Dict[str, Any]]:
    """
    Find job that was active at given timestamp.

    Args:
        jobs: Dictionary of jobs indexed by job_id
        timestamp: Target timestamp to match
        window_seconds: Time window to consider for matching

    Returns:
        Job dictionary if found, None otherwise
    """
    for job_id, job in jobs.items():
        # Ensure job_id is included in the returned job dictionary
        job["job_id"] = job_id

        created_at = job.get("created_at")
        completed_at = job.get("completed_at")

        if created_at and created_at <= timestamp:
            # For metrics that occur during job execution (not at completion),
            # check if timestamp is between creation and completion OR within window of creation
            if completed_at:
                # If job has completion time, check if timestamp is within the job's lifecycle
                if created_at <= timestamp <= completed_at:
                    time_diff = min(abs((timestamp - created_at).total_seconds()),
                                   abs((timestamp - completed_at).total_seconds()))
                    if time_diff <= window_seconds:
                        return job
            else:
                # Job hasn't completed yet, check if within window of creation
                time_diff = (timestamp - created_at).total_seconds()
                if time_diff <= window_seconds:
                    return job

    return None


def parse_metrics(log_lines: List[str], jobs: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Pass 2: Match metrics to jobs based on timestamp proximity.

    Args:
        log_lines: List of log lines to parse for metrics
        jobs: Dictionary of jobs from Pass 1

    Returns:
        Updated jobs dictionary with metrics added
    """
    for line in log_lines:
        timestamp = extract_timestamp(line)
        if not timestamp:
            continue

        # Find which job this metric belongs to
        job = find_job_by_timestamp(jobs, timestamp)
        if not job:
            continue

        # Extract duration
        duration = extract_duration(line)
        if duration is not None:
            job["duration_seconds"] = duration

        # Extract citation count
        citation_count = extract_citation_count(line)
        if citation_count is not None:
            job["citation_count"] = citation_count

    return jobs


def parse_logs(log_file_path: str, start_timestamp: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Main function: Parse log file and return list of validation events.

    Args:
        log_file_path: Path to log file (supports .gz compression)
        start_timestamp: Optional timestamp to start parsing from

    Returns:
        List of job dictionaries with extracted information
    """
    # Determine if file is gzip compressed
    open_func = gzip.open if log_file_path.endswith('.gz') else open

    with open_func(log_file_path, 'rt', encoding='utf-8') as f:
        log_lines = f.readlines()

    # Filter by start timestamp if provided
    if start_timestamp:
        filtered_lines = []
        for line in log_lines:
            timestamp = extract_timestamp(line.strip())
            if timestamp and timestamp >= start_timestamp:
                filtered_lines.append(line.strip())
        log_lines = filtered_lines
    else:
        log_lines = [line.strip() for line in log_lines]

    # Pass 1: Extract job lifecycle events
    jobs = parse_job_events(log_lines)

    # Pass 2: Match metrics to jobs
    jobs = parse_metrics(log_lines, jobs)

    # Convert to list format and add default values
    result = []
    for job in jobs.values():
        # Add defaults for missing fields
        job.setdefault("duration_seconds", None)
        job.setdefault("citation_count", None)
        job.setdefault("error_message", None)

        # Convert datetime objects to ISO format strings
        if "created_at" in job and isinstance(job["created_at"], datetime):
            job["created_at"] = job["created_at"].isoformat() + "Z"
        if "completed_at" in job and isinstance(job["completed_at"], datetime):
            job["completed_at"] = job["completed_at"].isoformat() + "Z"

        result.append(job)

    return result