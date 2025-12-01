You are providing technical guidance and problem solving assistance.

## Issue Context
### Beads Issue ID: citations-1vh9

Status: in_progress
Priority: P1
Type: task
Created: 2025-11-27 21:13
Updated: 2025-11-27 21:13

Description:
## Context
**Epic:** citations-dashboard-enhancement
**Phase 1**: Foundation - Database & Parser Enhancement

### Strategic Background
This task enhances the log parsing system to extract original citation text from backend application logs. Current parser extracts metrics (duration, token usage) but ignores the actual citation content stored in log entries with 'Citation text preview:' and 'ORIGINAL:' patterns.

### Requirements
- [ ] Add extract_citations_preview() with non-greedy regex and security escaping
- [ ] Add extract_full_citations() with robust boundaries and XSS prevention
- [ ] Update parse_metrics() to extract and store citation data
- [ ] Add comprehensive unit tests for extraction functions
- [ ] Implement length limits (5K preview, 10K full citations)

### Files Modified
- dashboard/log_parser.py (extraction functions)
- dashboard/test_log_parser.py (comprehensive tests)

### Security Implementation
- HTML escaping: text.replace('<', '&lt;').replace('>', '&gt;')
- Script removal: re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
- Length limits: Prevent storage/performance abuse

### Success Criteria
- [ ] Both extraction patterns work with production log samples
- [ ] All security measures implemented and tested
- [ ] Unit tests cover edge cases and malformed data
- [ ] Performance impact < 5% on log parsing time


Depends on (2):
  → citations-oioc: EPIC: Add Original Citations to Operational Dashboard Details [P0]
  → citations-1748: Database Schema - Add citations_text column to validations table [P1]

Blocks (2):
  ← citations-23m2: Database Integration - Update cron job and queries [P1]
  ← citations-gpbh: API Model Enhancement - Add citations to ValidationResponse [P1]

### Current Status

I'm currently using the brainstorming skill to design citation extraction functions. I've analyzed the existing log_parser.py structure and examined log samples. I found two distinct citation patterns:

1. "Citation text preview:" - A shortened preview (truncated with "...")
2. "ORIGINAL:" - Full citation text on a separate line (potentially multiline)

### The Question/Problem/Dilemma

**User wants to focus on: "why there is both a preview and original and why they both exist based on the project code and beads history"**

I need to understand the technical and business reasons for having both citation preview and original citation patterns in the application logs. This will help me design appropriate extraction functions that serve the intended use cases.

Specifically:
- Why does the application log both "Citation text preview:" and "ORIGINAL:" patterns?
- What different purposes do these serve in the application workflow?
- Are they generated at different points in the validation process?
- Do they serve different user needs or system requirements?
- Should I treat them differently in terms of security, length limits, or processing?

### Relevant Context

I'm working on enhancing the log parser to extract citation text for an operational dashboard. The current parser only extracts metrics (duration, token usage, citation count) but ignores the actual citation content.

From log analysis, I can see:
- "Citation text preview:" appears in DEBUG level logs with truncated content
- "ORIGINAL:" appears with what appears to be full citation text
- Both seem to be part of the citation validation workflow

### Supporting Information

Sample log patterns found:

```
2025-11-04 21:42:48 - citation_validator - DEBUG - app.py:275 - Citation text preview: Adli, A. (2013). Syntactic variation in French Wh-questions: A quantitative study from the angle of Bourdieu's sociocultural theory. _Linguistics_, _51_(3), 473-515.

Agarwal, D., Naaman, M., & Vashis...
```

```
ORIGINAL:
Adli, A. (2013). Syntactic variation in French Wh-questions: A quantitative study from the angle of Bourdieu's sociocultural theory. _Linguistics_, _51_(3), 473-515.

[continues with full citation text...]
```

The issue is part of an epic to add original citations to operational dashboard details, and the database schema was already updated to add a citations_text column.