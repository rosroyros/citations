import re
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
import gzip

# Time window for associating user IDs with jobs (5 minutes)
USER_ID_ASSOCIATION_TIMEOUT_SECONDS = 300


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
    # Pattern matches: Job abc-123: Completed [successfully|with any message]
    completion_pattern = r'Job ([a-f0-9-]+): Completed'
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
    # Also matches: Token usage: 1025 input + 997 output = 2022 total
    token_pattern = r'Token usage: (\d+) (?:prompt|input) \+ (\d+) (?:completion|output) = (\d+) total'
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


def extract_provider_selection(log_line: str) -> Optional[Tuple[str, str]]:
    """
    Extract provider selection information from a log line.

    Args:
        log_line: The log line to extract provider selection info from

    Returns:
        tuple of (job_id, provider) if found, None otherwise
    """
    # Pattern matches: PROVIDER_SELECTION: job_id=abc-123 model=model_a status=success fallback=False
    # Job ID pattern matches UUIDs and other job ID formats
    provider_pattern = r'PROVIDER_SELECTION: job_id=([\w-]+) model=(\w+)'
    match = re.search(provider_pattern, log_line)

    if match:
        job_id = match.group(1)
        provider = match.group(2)
        return job_id, provider

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


def extract_gating_decision(log_line: str) -> Optional[Tuple[str, bool, str]]:
    """
    Extract gating decision information from a log line.

    Args:
        log_line: The log line to extract gating decision info from

    Returns:
        tuple of (job_id, results_gated, reason) if found, None otherwise
    """
    # Pattern matches: GATING_DECISION: job_id=abc-123 user_type=free results_gated=True reason='Free tier limit reached'
    # Also handles unquoted reasons: GATING_DECISION: job_id=abc-123 user_type=free results_gated=True reason=Free limit
    gating_pattern = r'GATING_DECISION: job_id=([a-f0-9-]+) user_type=\w+ results_gated=(True|False) reason=\'?([^\']*)\'?'
    match = re.search(gating_pattern, log_line)

    if match:
        job_id = match.group(1)
        results_gated_str = match.group(2).lower()
        reason = match.group(3)

        # Convert string to boolean
        results_gated = results_gated_str == 'true'

        return job_id, results_gated, reason

    return None


def extract_partial_results_event(log_line: str) -> Optional[Tuple[str, str]]:
    """
    Extract partial results event information from a log line.

    This looks for log messages that indicate partial results were returned to the user,
    which should trigger the lock icon in the upgrade funnel.

    Args:
        log_line: The log line to extract partial results info from

    Returns:
        tuple of (job_id, partial_type) if found, None otherwise
        where partial_type is either 'empty' or 'locked'
    """
    # Pattern 1: "Job {job_id}: Free tier limit reached - returning empty partial results"
    pattern1 = r'Job ([a-f0-9-]+): Free tier limit reached - returning empty partial results'
    match1 = re.search(pattern1, log_line)
    if match1:
        return match1.group(1), 'empty'

    # Pattern 2: "Job {job_id}: Completed - free tier limit reached, returning locked partial results with X remaining"
    pattern2 = r'Job ([a-f0-9-]+): Completed - free tier limit reached, returning locked partial results'
    match2 = re.search(pattern2, log_line)
    if match2:
        return match2.group(1), 'locked'

    # Pattern 3: "Partial results with data bypass gating" followed by job_id in GATING_DECISION
    # This pattern spans multiple lines, so we need to handle it differently
    pattern3 = r'Partial results with data bypass gating'
    if re.search(pattern3, log_line):
        # Look for job_id in the same line or next line
        job_pattern = r'job_id=([a-f0-9-]+)'
        match_job = re.search(job_pattern, log_line)
        if match_job:
            return match_job.group(1), 'partial'

    # Pattern 4: GATING_DECISION with reason containing "Partial results with data"
    pattern4 = r'GATING_DECISION: job_id=([a-f0-9-]+) .* reason=\'?.*Partial results with data.*\'?'
    match4 = re.search(pattern4, log_line)
    if match4:
        return match4.group(1), 'partial'

    return None


def extract_reveal_event(log_line: str) -> Optional[Tuple[str, str]]:
    """
    Extract reveal event information from a log line.

    Args:
        log_line: The log line to extract reveal event info from

    Returns:
        tuple of (job_id, outcome) if found, None otherwise
    """
    # Pattern matches: REVEAL_EVENT: job_id=abc-123 outcome=revealed
    reveal_pattern = r'REVEAL_EVENT: job_id=([a-f0-9-]+) outcome=(\w+)'
    match = re.search(reveal_pattern, log_line)

    if match:
        job_id = match.group(1)
        outcome = match.group(2)
        return job_id, outcome

    return None


def extract_upgrade_workflow_event(log_line: str) -> Optional[Tuple[str, str]]:
    """
    Extract upgrade workflow event information from a log line.

    Args:
        log_line: The log line to extract upgrade workflow event info from

    Returns:
        tuple of (job_id, event) if found, None otherwise
    """
    # Pattern matches: UPGRADE_WORKFLOW: job_id=abc-123 event=clicked_upgrade
    upgrade_pattern = r'UPGRADE_WORKFLOW: job_id=([a-f0-9-]+) event=(\w+)'
    match = re.search(upgrade_pattern, log_line)

    if match:
        job_id = match.group(1)
        event = match.group(2)
        return job_id, event

    return None


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


def extract_user_ids(log_line: str) -> tuple[Optional[str], Optional[str]]:
    """
    Extract user IDs from validation request log line.

    Args:
        log_line: Log line containing user ID information

    Returns:
        tuple: (paid_user_id, free_user_id)
            Returns (None, None) if pattern not found
    """
    # Look for the user type and IDs in the log line
    if "Validation request" not in log_line:
        return None, None

    # Extract using simple string parsing
    paid_user_id = None
    free_user_id = None

    # Find user_type
    user_type_match = re.search(r'user_type=(\w+)', log_line)
    if not user_type_match:
        return None, None

    # Extract paid_user_id
    paid_match = re.search(r'paid_user_id=([^,]+)', log_line)
    if paid_match:
        paid_value = paid_match.group(1).strip()
        paid_user_id = paid_value if paid_value != 'N/A' else None

    # Extract free_user_id
    free_match = re.search(r'free_user_id=([^,]+)', log_line)
    if free_match:
        free_value = free_match.group(1).strip()
        free_user_id = free_value if free_value != 'N/A' else None

    return paid_user_id, free_user_id


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
                "status": "pending",
                "paid_user_id": None,
                "free_user_id": None
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
            continue

        # Check for partial results event
        partial_results = extract_partial_results_event(line)
        if partial_results:
            job_id, partial_type = partial_results
            
            # Allow partial updates for existing jobs
            if job_id not in jobs:
                jobs[job_id] = {"job_id": job_id}
                
            if job_id in jobs and jobs[job_id].get('upgrade_state') != 'success':
                # Get current state (handle None or existing string)
                current_state_str = jobs[job_id].get('upgrade_state')
                current_states = current_state_str.split(',') if current_state_str else []
                
                # Add 'locked' if not present
                if 'locked' not in current_states:
                    # Locked should be first
                    current_states.insert(0, 'locked')
                    
                    # Store back as comma-separated string
                    jobs[job_id]["upgrade_state"] = ','.join(current_states)
                    
                jobs[job_id]["partial_results_type"] = partial_type  # Store for debugging
            continue

        # Still check for gating decision for compatibility
        gating_result = extract_gating_decision(line)
        if gating_result:
            job_id, results_gated, reason = gating_result
            if job_id in jobs:
                jobs[job_id]["results_gated"] = results_gated
            continue

        # Check for provider selection
        provider_result = extract_provider_selection(line)
        if provider_result:
            job_id, provider = provider_result
            if job_id in jobs:
                jobs[job_id]["provider"] = provider
            continue

        # Check for reveal event
        reveal_result = extract_reveal_event(line)
        if reveal_result:
            job_id, outcome = reveal_result
            if job_id in jobs:
                # Extract timestamp from beginning of line for reveal time
                timestamp = extract_timestamp(line)
                if timestamp:
                    jobs[job_id]["results_revealed_at"] = timestamp.isoformat() + 'Z'
                jobs[job_id]["gated_outcome"] = outcome
            continue

        # Check for upgrade workflow event
        upgrade_result = extract_upgrade_workflow_event(line)
        if upgrade_result:
            job_id, event = upgrade_result
            
            # Allow partial updates for existing jobs
            if job_id not in jobs:
                jobs[job_id] = {"job_id": job_id}
                
            if job_id in jobs:
                # Map events to state values
                event_to_state = {
                    'clicked_upgrade': 'clicked',
                    'modal_proceed': 'modal',
                    'success': 'success'
                }

                # Get the new state
                new_state = event_to_state.get(event)
                if new_state:
                    # Get current state (handle None or existing string)
                    current_state_str = jobs[job_id].get('upgrade_state')
                    current_states = current_state_str.split(',') if current_state_str else []
                    
                    # Don't duplicate if already present
                    if new_state not in current_states:
                        # Logic to append state based on progression
                        if new_state == 'locked':
                            # Locked should be first
                            current_states.insert(0, 'locked')
                        else:
                            # Append other states
                            current_states.append(new_state)
                        
                        # Store back as comma-separated string
                        jobs[job_id]["upgrade_state"] = ','.join(current_states)
            continue

        # Check for validation request with user IDs
        if "Validation request" in line:
            paid_user_id, free_user_id = extract_user_ids(line)
            if paid_user_id is not None or free_user_id is not None:
                # Find the most recent job that doesn't have user IDs set yet
                # This associates the user IDs with the job that was just created
                timestamp = extract_timestamp(line)
                if timestamp:
                    # Look for a job created within the last 5 minutes that doesn't have user IDs
                    for job_id, job in jobs.items():
                        if (job.get("paid_user_id") is None and
                            job.get("free_user_id") is None and
                            job.get("created_at") and
                            abs((timestamp - job["created_at"]).total_seconds()) < USER_ID_ASSOCIATION_TIMEOUT_SECONDS):
                            job["paid_user_id"] = paid_user_id
                            job["free_user_id"] = free_user_id
                            break

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
    return _finalize_job_data(jobs)


def _finalize_job_data(jobs: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Finalize job data by adding defaults and formatting datetime objects.

    Args:
        jobs: Dictionary of jobs to finalize

    Returns:
        List of finalized job dictionaries
    """
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
        job.setdefault("paid_user_id", None)
        job.setdefault("free_user_id", None)
        job.setdefault("upgrade_state", None)
        job.setdefault("provider", None)

        # Convert datetime objects to proper ISO format strings
        if "created_at" in job and isinstance(job["created_at"], datetime):
            job["created_at"] = job["created_at"].strftime("%Y-%m-%dT%H:%M:%SZ")
        if "completed_at" in job and isinstance(job["completed_at"], datetime):
            job["completed_at"] = job["completed_at"].strftime("%Y-%m-%dT%H:%M:%SZ")

        result.append(job)

    return result


# Initialize logger for this module
logger = logging.getLogger(__name__)


class CitationLogParser:
    """
    Stateful citation log parser with file offset tracking.

    Tracks the last processed position in the log file to only process new entries
    on each run, improving efficiency for large log files.
    """

    def __init__(self, log_file_path: str, position_file_path: Optional[str] = None):
        """
        Initialize the parser with log file and position file paths.

        Args:
            log_file_path: Path to the citation log file
            position_file_path: Path to store last processed position (defaults to /opt/citations/logs/citations.position)
        """
        self.log_file_path = log_file_path
        self.position_file_path = position_file_path or "/opt/citations/logs/citations.position"
        self.last_position = self._load_position()

    def _load_position(self) -> int:
        """
        Load the last processed position from the position file.

        Returns:
            Last processed byte offset, 0 if file doesn't exist
        """
        try:
            if os.path.exists(self.position_file_path):
                with open(self.position_file_path, 'r') as f:
                    position_str = f.read().strip()
                    if position_str.isdigit():
                        return int(position_str)
        except (IOError, ValueError) as e:
            # If we can't read the position file, start from beginning
            logger.warning(f"Could not read position file {self.position_file_path}: {e}")

        return 0

    def _save_position(self, position: int) -> None:
        """
        Save the current position to the position file.

        Args:
            position: Current byte offset in the log file
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.position_file_path), exist_ok=True)

            with open(self.position_file_path, 'w') as f:
                f.write(str(position))
        except IOError as e:
            logger.warning(f"Could not save position to {self.position_file_path}: {e}")

    def _detect_log_rotation(self, current_file_size: int) -> bool:
        """
        Detect if log rotation has occurred by checking if current file size
        is smaller than last stored position.

        Args:
            current_file_size: Current size of the log file in bytes

        Returns:
            True if log rotation detected, False otherwise
        """
        if self.last_position > 0 and self.last_position > current_file_size:
            logger.info(f"Log rotation detected: last position {self.last_position} > current file size {current_file_size}")
            self.last_position = 0
            self._save_position(0)
            return True
        return False

    def parse_new_entries(self) -> List[Dict[str, Any]]:
        """
        Parse only new entries in the log file since last run.

        Returns:
            List of new job dictionaries with extracted information
        """
        # Check if log file exists
        if not os.path.exists(self.log_file_path):
            logger.warning(f"Log file {self.log_file_path} does not exist")
            return []

        # Get current file size and detect rotation
        current_file_size = os.path.getsize(self.log_file_path)
        self._detect_log_rotation(current_file_size)

        # If no new content, return empty list
        if current_file_size <= self.last_position:
            return []

        # Determine if file is gzip compressed
        open_func = gzip.open if self.log_file_path.endswith('.gz') else open

        try:
            # Open in binary mode for proper offset tracking
            with open_func(self.log_file_path, 'rb') as f:
                # Seek to last position
                f.seek(self.last_position)

                # Read new content
                new_content = f.read()

                # Update position to end of file
                self.last_position = f.tell()
                self._save_position(self.last_position)

                # Process new content if any
                if not new_content:
                    return []

                # Decode bytes to string and split into lines
                try:
                    content_str = new_content.decode('utf-8')
                except UnicodeDecodeError as e:
                    logger.error(f"UTF-8 decode error in log file {self.log_file_path}: {e}")
                    return []

                # Split into lines and strip whitespace
                log_lines = [line.strip() for line in content_str.splitlines() if line.strip()]

                if not log_lines:
                    return []

                # Use existing parsing logic on new lines only
                # Pass 1: Extract job lifecycle events
                jobs = parse_job_events(log_lines)

                # Pass 2: Match metrics to jobs
                jobs = parse_metrics(log_lines, jobs)

                # Pass 3: Extract full citations from multiline patterns
                jobs = extract_citations_from_all_lines(log_lines, jobs)

                # Convert to list format and add default values using shared helper
                return _finalize_job_data(jobs)

        except (IOError, OSError) as e:
            logger.error(f"Error reading log file {self.log_file_path}: {e}")
            return []

    def reset_position(self) -> None:
        """
        Reset the parser position to the beginning of the file.
        Useful for testing or when full re-parse is needed.
        """
        self.last_position = 0
        self._save_position(0)

    def get_current_position(self) -> int:
        """
        Get the current parser position.

        Returns:
            Current byte offset in the log file
        """
        return self.last_position