# Citations-FDXF Design: Store Citations at Source Instead of Parsing Logs

## Problem Statement

The operational dashboard currently displays citation details by parsing multiline text from application logs. This approach has fundamental limitations:

**Current Issues:**
- Backend `Citations to validate:` debug message only contains first citation, not all citations submitted
- Log parsing is inherently fragile - depends on log format stability
- Multiline text in logs is problematic for automated parsing
- Citations are mixed with debug metadata, making extraction unreliable
- Users see incomplete citation data (e.g., job shows 9 citations but modal displays only 1)

## Solution Overview

**Architecture:** Separate citation logging with structured format, integrated into existing log parser pipeline

**Key Design Principles:**
- Core citation validation remains independent of database operations
- Leverage existing log parser infrastructure and patterns
- Minimal complexity - single additional log file
- Backward compatible with current behavior as fallback

## Detailed Design

### 1. Citation Log Format

**File Location:** `/opt/citations/logs/citations.log`

**Entry Format:**
```
<<JOB_ID:abc123-def456-789>>
citation_1
<<<END_JOB>>>

<<JOB_ID:xyz789-uvw456-123>>
citation_1
citation_2
<<<END_JOB>>>
```

**Validation:** Parser only processes entries with complete `<<<END_JOB>>>` markers

### 2. Backend Changes

**Modified Files:** `backend/app.py`

**Changes:**
- Replace single `Citations to validate:` log entry with structured citations log
- Write all citations (not just first one) to separate citation log
- Use clear start/end markers that won't appear in citation text
- Maintain existing validation logic unchanged

**Implementation:**
```python
# Current: logs only first citation
logger.info(f"Citations to validate: {citations[0][:200]}...")

# New: structured citation log
with open("/opt/citations/logs/citations.log", "a") as f:
    f.write(f"<<JOB_ID:{job_id}>>\n")
    for citation in citations:
        f.write(f"{citation}\n")
    f.write("<<<END_JOB>>>\n")
```

### 3. Log Parser Enhancements

**Modified Files:** `dashboard/log_parser.py`

**Changes:**
- Add citation log processing alongside existing log parsing
- Use job-based tracking to prevent duplicate processing
- Feed citation data to dashboard using same existing mechanisms

**Processing Logic:**
```python
def process_citation_log():
    processed_jobs = get_jobs_with_citations()

    for job_entry in parse_citation_log():
        job_id = job_entry.job_id

        # Skip if already processed
        if job_id in processed_jobs:
            continue

        # Only process if job exists in validations table
        if job_exists_in_validations(job_id):
            citations = job_entry.citations
            add_citations_to_dashboard(job_id, citations)
            mark_job_citations_processed(job_id)
```

### 4. System Management

**Log Rotation:** Weekly rotation at 5am UTC via `/etc/logrotate.d/citations`
```
/opt/citations/logs/citations.log {
    weekly
    rotate 4
    missingok
    notifempty
    delaycompress
    compress
    create 644 deploy deploy
    copytruncate
}
```

**Performance:** Simple linear scan - 50MB files are well within acceptable limits

**Cleanup:** Orphaned entries ignored and automatically cleaned up by weekly rotation

### 5. Monitoring and Observability

**Metrics Logged to:** `/opt/citations/logs/cron.log` (existing log)

**Key Metrics:**
- Citation entries found/processed/skipped per run
- Parse time duration
- File size monitoring
- Permission/error tracking

**Sample Output:**
```
Citation log: processed 15 jobs, 3 entries skipped, 0 errors, 0.2s
```

## Risk Mitigation

### 1. Race Conditions
- **Solution:** End-marker validation ensures parser only processes complete entries
- **Behavior:** Parser skips incomplete entries, retries on next run
- **Pattern:** Same as existing log parser behavior

### 2. Corrupted/Missing Entries
- **Solution:** Check for `<<<END_JOB>>>` marker
- **Fallback:** Continue with current behavior if citation entry missing/invalid
- **Recovery:** Orphaned entries ignored, cleaned up by rotation

### 3. Database Dependency
- **Solution:** Citation logging completely independent of database operations
- **Isolation:** Core validation unaffected by citation log issues
- **Fallback:** Dashboard shows current limited citation data if parsing fails

### 4. Performance Impact
- **Solution:** Simple linear scan of manageable file sizes
- **Bound:** Weekly rotation keeps files under ~50MB
- **Overhead:** Minimal compared to existing log parsing workload

## Implementation Plan

### Phase 1: Backend Citation Logging
1. Add citation log writing to validation request handler
2. Test with various citation formats and edge cases
3. Ensure proper error handling for file I/O operations

### Phase 2: Log Parser Enhancement
1. Add citation log reading to existing parser
2. Implement job-based tracking for duplicate prevention
3. Integrate with existing dashboard data structures

### Phase 3: System Integration
1. Set up log rotation configuration
2. Add monitoring metrics to cron job
3. Test end-to-end with production data

### Phase 4: Validation and Testing
1. Test with various failure scenarios (crashes, corruption)
2. Verify backward compatibility with existing behavior
3. Performance testing with realistic citation volumes

## Success Criteria

- [ ] Modal displays ALL citations submitted by user (not just first)
- [ ] Citation count in modal matches actual submissions
- [ ] No database dependency for core validation functionality
- [ ] Robust against log format changes and corruption
- [ ] No regression in existing functionality
- [ ] Performance impact minimal (< 1 second additional processing time)
- [ ] System self-healing from partial failures and crashes

## Dependencies

- Backend validation request handler modification
- Log parser citation extraction logic update
- Log rotation system configuration
- Dashboard API integration (no breaking changes)

## Implementation Estimate

- **Backend citation logging**: 3-4 hours
- **Log parser updates**: 2-3 hours
- **System integration and testing**: 3-4 hours
- **Documentation and deployment**: 1-2 hours
- **Total**: 9-13 hours

---

*This design maintains the principle that "logs are for debugging, not data storage" while solving the fundamental issue of incomplete citation display through structured, reliable citation logging.*