You are providing technical guidance and problem solving assistance.

## Issue Context
### Beads Issue ID: citations-fdxf

**Status:** open
**Priority:** P1
**Type:** feature

## Problem Statement
The operational dashboard currently displays citation details by parsing multiline text from application logs. This approach has fundamental limitations:

**Current Issues:**
- Backend `Citations to validate:` debug message only contains first citation, not all citations submitted
- Log parsing is inherently fragile - depends on log format stability
- Multiline text in logs is problematic for automated parsing
- Citations are mixed with debug metadata, making extraction unreliable
- Users see incomplete citation data (e.g., job shows 9 citations but modal displays only 1)

**Production Example:** Job e987d7e0-7f19-4f65-93ad-4911e7d3bce0: User submitted 11 citations (6858 chars), backend processed all correctly, but log only captured first citation (1991 chars), users expect to see all 11 in modal.

## Current Status
I have completed a comprehensive design analysis and created a detailed implementation plan. The design has been documented and committed to the repository.

**Design Decision Made:** Separate citation logging approach (not database-dependent)

## The Question/Problem/Dilemma

User wants focus: "show this to gemini and get concrete feedback"

I need concrete feedback on the complete design I've developed for citations-fdxf. Specifically:

1. **Architecture Review:** Is the separate citation logging approach sound?
2. **Risk Assessment:** Have I missed any critical failure modes or operational risks?
3. **Implementation Priority:** Is the phased approach appropriate, or should any components be reordered?
4. **Technical Constraints:** The key constraint is that core citation validation must NOT depend on database availability. Does my design properly respect this?
5. **Production Readiness:** Are there any production deployment considerations I've overlooked?

## Proposed Solution Summary

**Approach:** Separate structured citation log (`/opt/citations/logs/citations.log`) instead of database storage

**Key Design Decisions:**
- Backend writes all citations to structured log format with clear start/end markers
- Log parser reads from citation log (not application logs) and feeds dashboard
- Job-based tracking prevents duplicate processing
- Weekly log rotation for disk management
- Simple end-marker validation (no checksums)
- Linear scan performance (50MB files acceptable)
- Basic monitoring via existing cron logs

**Citation Log Format:**
```
<<JOB_ID:abc123-def456-789>>
citation_1
citation_2
<<<END_JOB>>>
```

**Integration Pattern:** Citation log → log parser → dashboard (same as current flow, different data source)

**Key Benefits:**
- No database dependency for core validation
- Leverages existing log parser infrastructure
- Minimal complexity - single additional log file
- Backward compatible fallback behavior

## Relevant Context

**Current Architecture:**
- Backend processes all citations correctly but only logs first one
- Log parser extracts citation data from debug messages
- Dashboard displays extracted data to users
- Users see incomplete citation information

**System Constraints:**
- Core citation validation must work even if database is down
- Existing log parser runs every 5 minutes via cron
- Current system has no automated log rotation (manual cleanup)
- Database schema drift issues recently addressed

**Implementation Considerations:**
- Need to handle race conditions between backend writing and parser reading
- Must handle partial writes/crashes gracefully
- Citation logs will grow and need cleanup strategy
- Parser must handle orphaned entries (citations without matching jobs)

## Supporting Information

**Design Document:** `docs/plans/2025-12-01-citations-fdxf-design.md`

**Key Files to Modify:**
- `backend/app.py` - Add citation logging to validation handler
- `dashboard/log_parser.py` - Add citation log processing
- `/etc/logrotate.d/citations` - Add citation log rotation

**Risk Mitigations Implemented:**
- End-marker validation prevents processing incomplete entries
- Job-based tracking prevents duplicate processing
- Weekly rotation bounds file growth
- Orphaned entries ignored and cleaned up naturally
- Parser skips malformed entries and continues processing

**Performance Analysis:**
- Citation entries: ~6.6KB per job
- Weekly accumulation: ~1,000 jobs = ~6.6MB per week
- Parser scan time: < 1 second for 50MB files
- Memory usage: minimal (streaming processing)

Please provide concrete, actionable feedback on this design approach.