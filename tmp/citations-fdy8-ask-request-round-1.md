You are providing technical guidance and problem solving assistance.

## Issue Context
### Beads Issue ID: citations-fdy8

**Title**: Fix citation log parser duplicate parsing issue
**Status**: open
**Priority**: P0
**Type**: bug

## Description
Dashboard citation table shows 5,089 entries with massive duplicates - same citations appearing 116-232 times each. This is causing dashboard to show incorrect citation statistics.

## Root Cause
Position tracking in parse_citations_cron.py is failing, causing cron job to re-read entire citations.log file every 5 minutes.

## Current Status

We've identified the problem is in `/opt/citations/dashboard/parse_citations_cron.py`. The position tracking mechanism is failing, causing the same citation blocks to be re-processed repeatedly.

### Issues Identified:
1. **Position saved AFTER parsing** - If parsing fails or exits early, position file isn't updated
2. **No log rotation detection** - If citations.log is rotated, position becomes invalid
3. **No position validation** - Position can exceed file size
4. **Race condition** - Position read and save aren't atomic

### Current Code Flow (problematic):
```python
# Line 130: Load position
last_position = load_position()
# Line 131: Get current file size
current_file_size = log_path.stat().st_size
# Lines 141-143: Read from last_position
with open(PRODUCTION_CITATION_LOG_PATH, 'r', encoding='utf-8') as f:
    f.seek(last_position)
    new_content = f.read()
# Lines 189-190: Save position AFTER processing
new_position = current_file_size
save_position(new_position)
```

### Current Deduplication (not working):
```python
# Lines 169-179: Check duplicates before insert
cursor.execute("""
    SELECT COUNT(*) FROM citations_dashboard
    WHERE job_id = ? AND citation_text = ?
""", (citation.get('job_id'), citation.get('citation_text')))
if cursor.fetchone()[0] == 0:
    db.insert_citation_to_dashboard(citation)
```

## The Question/Problem/Dilemma

**User wants to focus on:** "consult the gemini oracle about the problem and the propose solution"

We need guidance on:

1. **Is our proposed fix correct?** We want to:
   - Save position IMMEDIATELY after reading (before processing)
   - Add log rotation detection
   - Add position validation
   - Make position saving atomic
   - Keep the deduplication logic as backup

2. **Are we missing anything?** Should we consider:
   - Different approach entirely (unified parser)?
   - Better deduplication strategy?
   - Database-level constraints?

3. **What about the existing duplicates?** Should we:
   - Clean them up now?
   - Leave them and just fix going forward?
   - Create separate cleanup task?

4. **Deployment considerations:** How to safely deploy without losing data?

## Relevant Context

- Production environment: `/opt/citations/` on `178.156.161.140`
- Cron runs every 5 minutes: `*/5 * * * * /opt/citations/venv/bin/python3 /opt/citations/dashboard/parse_citations_cron.py`
- Citations logged to: `/opt/citations/logs/citations.log`
- Position file: `/opt/citations/logs/citations.position`
- Database: `/opt/citations/dashboard/data/validations.db`
- Table structure already exists with 5,089 rows

### Citation Log Format:
```
<<JOB_ID:abc-123>>
Smith, J. (2020). Title. Publisher.
Doe, J. (2021). Another Title. Journal.
<<<END_JOB>>>
```

### Current Duplicate Counts in Production:
- "(Landreth, 2024, p. 66)" - 232 duplicates
- "(Koukourikos et al., 2021)" - 232 duplicates
- Various other citations - 116 duplicates each

## Supporting Information

The system has two parsers:
1. `parse_logs_cron.py` - Parses `app.log` for job metadata
2. `parse_citations_cron.py` - Parses `citations.log` for citation text

These run independently, but we think the issue is only with #2.

The citations are written to `citations.log` by `backend/citation_logger.py` using:
```python
content.append(f"<<JOB_ID:{job_id}>>")
for citation in citations:
    content.append(citation)
content.append("<<<END_JOB>>>")
```