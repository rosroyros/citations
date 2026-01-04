You are providing technical guidance and problem solving assistance.

## Issue Context
### Beads Issue ID: citations-70ik

**Title:** Fix citation parser UTF-8 crash and data loss
**Priority:** P1 (High)
**Type:** Bug

### Summary
The citation parser (`parse_citations_cron.py`) crashes when multi-byte UTF-8 characters appear at tracked byte positions. The parser uses a position file to track how many bytes it has processed, but this byte position can fall in the middle of a multi-byte UTF-8 sequence (e.g., Greek characters like Π use 2 bytes: 0xce 0xa0). When the parser seeks to that position and tries to decode, it fails because 0xa0 is a continuation byte, not a valid start byte.

**Impact:** 5 jobs lost citations (19 total citations) on 2026-01-02. Parser was stuck in crash loop for ~4 hours until midnight log rotation.

### Proposed Fix: 3-Layer Defense

**Layer 1 (Immediate):** Add `errors='replace'` to open() call
- One-line change: `open(..., encoding='utf-8', errors='replace')`
- Prevents crash, replaces invalid bytes with �
- Tradeoff: loses partial character data

**Layer 2 (Better):** Find UTF-8 character boundary before reading
- New function to adjust byte position to valid UTF-8 boundary
- Preserves data quality
- More complex implementation

**Layer 3 (Safety Net):** Process rotated logs when rotation detected
- Recovers missed citations from crash loops
- Uses existing deduplication logic
- Only runs on rotation detection

### Current Status
Root cause analysis complete. Proposed 3-layer fix documented in issue. Ready for implementation but seeking second opinion on approach before proceeding.

## The Question

I'm planning to implement all 3 layers for defense in depth, but I want a second opinion on:

1. **Is the 3-layer approach appropriate** or is it over-engineering?
2. **Are there any edge cases or risks** I'm missing with the proposed approach?
3. **Should I consider the architectural fix** (direct database insertion instead of file-based logging) instead of patching the parser?
4. **Any alternative approaches** I should consider?

## Relevant Context

**Architecture:**
- Jobs write citations to `/opt/citations/logs/citations.log` in real-time
- Cron job runs every minute to parse new citations
- Parser maintains position in `/opt/citations/logs/citations.position`
- Parsed citations inserted into `citations_dashboard` table
- Log rotation happens daily at midnight (logrotate with copytruncate)

**Constraints:**
- Must handle multi-language citations (Greek, Chinese, Arabic, etc.)
- Position tracking is byte-based, not character-based
- Multiple cron jobs run concurrently (4 instances in logs)
- Log rotation uses copytruncate (can truncate during write)

**Current Code:**
File: `/opt/citations/dashboard/parse_citations_cron.py`

Key section (lines 169-178):
```python
# Read only the new content
try:
    with open(PRODUCTION_CITATION_LOG_PATH, 'r', encoding='utf-8') as f:
        f.seek(last_position)
        new_content = f.read()
        # Get the actual position after reading (handles if file grew during read)
        new_position = f.tell()
except IOError as e:
     logger.error(f"Failed to read log file: {e}")
     sys.exit(1)
```

The crash happens at `f.read()` when `last_position` points to middle of multi-byte character.

## Supporting Information

**Evidence of the bug:**
```
2026-01-02 19:00:01,585 - INFO - Processing new content from position 1256 to 3847
2026-01-02 19:00:01,585 - ERROR - Citation cron job failed: 'utf-8' codec can't decode byte 0xa0 in position 0: invalid start byte
```

**File dump around position 1256:**
```
Hex: cebd202620cea0cebfcebbceb9cf84ceb9cf83cebccf8ecebdc2bb
Decoded: ν & Πολιτισμών»</e
                        ↑
                  Position 1256 = 0xa0 (second byte of Π)
```

**Deduplication already exists** (lines 208-219):
```python
cursor.execute("""
    SELECT COUNT(*) FROM citations_dashboard
    WHERE job_id = ? AND citation_text = ?
""", (citation.get('job_id'), citation.get('citation_text')))

if cursor.fetchone()[0] == 0:
    db.insert_citation_to_dashboard(citation)
```

This means Layer 3 (rotated log parsing) is safe from duplicates.
