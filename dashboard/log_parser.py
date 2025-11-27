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


def extract_token_usage(log_line: str) -> Optional[Dict[str, int]]:
    """
    Extract token usage from a log line.

    Args:
        log_line: The log line to extract token usage from

    Returns:
        dict with prompt, completion, total if found, None otherwise
    """
    # Pattern matches: Token usage: 1025 prompt + 997 completion = 2022 total
    token_pattern = r'Token usage: (\d+) prompt \+ (\d+) completion = (\d+) total'
    match = re.search(token_pattern, log_line)

    if match:
        try:
            return {
                "prompt": int(match.group(1)),
                "completion": int(match.group(2)),
                "total": int(match.group(3))
            }
        except ValueError:
            return None

    return None


def extract_failure(log_line: str) -> Optional[tuple]:
    """
    Extract job failure information from a log line.

    Args:
        log_line: The log line to extract job failure info from

    Returns:
        tuple of (job_id, timestamp, error_message) if found, None otherwise
    """
    # Pattern matches: Job abc-123: Failed with error: <error message>
    failure_pattern = r'Job ([a-f0-9-]+): Failed with error: (.+)'
    match = re.search(failure_pattern, log_line)

    if match:
        job_id = match.group(1)
        error_message = match.group(2)

        # Extract timestamp from the beginning of the line
        timestamp = extract_timestamp(log_line)

        if timestamp:
            return job_id, timestamp, error_message

    return None


def sanitize_text(text: str, max_length: int) -> tuple[str, bool]:
    """
    Sanitize text for security and length limits.

    Args:
        text: Text to sanitize
        max_length: Maximum allowed length

    Returns:
        tuple of (sanitized_text, was_truncated)
    """
    # Remove script tags
    text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<iframe.*?</iframe>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<object.*?</object>', '', text, flags=re.IGNORECASE | re.DOTALL)

    # Remove SQL injection patterns
    sql_patterns = [
        r"' OR '1'='1",
        r'" OR "1"="1',
        r'DROP TABLE',
        r'INSERT INTO',
        r'DELETE FROM',
        r'UPDATE.*SET',
        r'UNION SELECT',
        r'--',
        r'/\*.*\*/'
    ]

    for pattern in sql_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # HTML escaping
    text = text.replace('<', '&lt;').replace('>', '&gt;')
    text = text.replace('"', '&quot;').replace("'", '&#x27;')

    # Length limit and truncation
    was_truncated = len(text) > max_length
    if was_truncated:
        text = text[:max_length] + '[TRUNCATED]'

    # Remove null bytes and control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

    return text, was_truncated


def extract_citations_preview(log_line: str) -> Optional[tuple[str, bool]]:
    """
    Extract citation preview text from a log line.

    Args:
        log_line: The log line to extract citation preview from

    Returns:
        tuple of (extracted_text, was_truncated) if found, None otherwise
    """
    # Pattern matches: Citation text preview: <text>
    preview_pattern = r'Citation text preview: (.+?)(?:\.{3})?$'
    match = re.search(preview_pattern, log_line)

    if match:
        raw_text = match.group(1).strip()
        sanitized_text, was_truncated = sanitize_text(raw_text, 5000)
        return sanitized_text, was_truncated

    return None


def extract_full_citations(log_lines: List[str], start_index: int) -> Optional[tuple[str, bool]]:
    """
    Extract full citation text from multiline ORIGINAL: pattern.

    Args:
        log_lines: List of log lines to search through
        start_index: Index to start searching from (should be ORIGINAL: line)

    Returns:
        tuple of (extracted_text, was_truncated) if found, None otherwise
    """
    # Check if start_index is valid and line contains ORIGINAL:
    if start_index >= len(log_lines):
        return None

    original_line = log_lines[start_index].strip()
    if not original_line.startswith("ORIGINAL:"):
        return None

    # Collect citation text until next log timestamp pattern
    citation_lines = []
    timestamp_pattern = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'

    # Start from line after ORIGINAL:
    for i in range(start_index + 1, len(log_lines)):
        line = log_lines[i].strip()

        # Stop at next timestamp or empty line
        if re.match(timestamp_pattern, line) or not line:
            break

        citation_lines.append(line)

    if citation_lines:
        full_text = '\n'.join(citation_lines)
        sanitized_text, was_truncated = sanitize_text(full_text, 10000)
        return sanitized_text, was_truncated

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

        # Check for job failure
        failure_result = extract_failure(line)
        if failure_result:
            job_id, timestamp, error_message = failure_result
            if job_id in jobs:
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error_message"] = error_message
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

        # Extract token usage
        token_usage = extract_token_usage(line)
        if token_usage is not None:
            job["token_usage_prompt"] = token_usage["prompt"]
            job["token_usage_completion"] = token_usage["completion"]
            job["token_usage_total"] = token_usage["total"]

        # Extract citation preview (single line)
        preview_result = extract_citations_preview(line)
        if preview_result is not None:
            citations_preview, preview_truncated = preview_result
            job["citations_preview"] = citations_preview
            job["citations_preview_truncated"] = preview_truncated

    return jobs


def extract_citations_from_all_lines(log_lines: List[str], jobs: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Pass 3: Extract full citations from multiline ORIGINAL: patterns.

    Args:
        log_lines: List of log lines to parse for full citations
        jobs: Dictionary of jobs from Pass 1/2

    Returns:
        Updated jobs dictionary with full citations added
    """
    for i, line in enumerate(log_lines):
        # Look for ORIGINAL: pattern
        if line.strip() == "ORIGINAL:":
            # Get timestamp from previous line (if available)
            timestamp = None
            if i > 0:
                timestamp = extract_timestamp(log_lines[i-1])

            # If no timestamp in previous line, try to find next timestamp
            if not timestamp:
                for j in range(i + 1, len(log_lines)):
                    timestamp = extract_timestamp(log_lines[j])
                    if timestamp:
                        break

            # Find which job this citation belongs to
            if timestamp:
                job = find_job_by_timestamp(jobs, timestamp)
                if job:
                    # Extract full citations
                    full_result = extract_full_citations(log_lines, i)
                    if full_result is not None:
                        citations_full, full_truncated = full_result
                        job["citations_full"] = citations_full
                        job["citations_full_truncated"] = full_truncated

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

    # Pass 3: Extract full citations from multiline patterns
    jobs = extract_citations_from_all_lines(log_lines, jobs)

    # Convert to list format and add default values
    result = []
    for job in jobs.values():
        # Add defaults for missing fields
        job.setdefault("duration_seconds", None)
        job.setdefault("citation_count", None)
        job.setdefault("error_message", None)
        job.setdefault("token_usage_prompt", None)
        job.setdefault("token_usage_completion", None)
        job.setdefault("token_usage_total", None)
        job.setdefault("citations_preview", None)
        job.setdefault("citations_preview_truncated", False)
        job.setdefault("citations_full", None)
        job.setdefault("citations_full_truncated", False)

        # Convert datetime objects to proper ISO format strings
        if "created_at" in job and isinstance(job["created_at"], datetime):
            job["created_at"] = job["created_at"].strftime("%Y-%m-%dT%H:%M:%SZ")
        if "completed_at" in job and isinstance(job["completed_at"], datetime):
            job["completed_at"] = job["completed_at"].strftime("%Y-%m-%dT%H:%M:%SZ")

        result.append(job)

    return result