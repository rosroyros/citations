You are providing technical guidance and problem solving assistance.

## Issue Context
### Beads Issue ID: citations-4px3

**Title:** Add Original Citations to Operational Dashboard Details
**Status:** open
**Priority:** P2
**Type:** feature

**Description:**

The operational dashboard shows validation job metadata (duration, citation count, status) but does NOT display the actual submitted citation text. Users want to see the original citations they submitted when viewing job details in the dashboard.

The original citations ARE stored in the backend application logs (/Users/roy/Documents/Projects/citations/logs/app.log) but the current log parser only extracts metrics, not the citation text content.

**Requirements:**
- [ ] Add original citation text to job details view in operational dashboard
- [ ] Extract original citations from application logs using log parser
- [ ] Store citations in dashboard database for efficient retrieval
- [ ] Update dashboard API to return citation data for jobs
- [ ] Update frontend to display citations in job details modal

**Implementation Approach:**

### Phase 1: Extend Log Parser
1. Add new extraction functions to `dashboard/log_parser.py`:
   - `extract_citation_preview()` - Extract citation text preview from logs
   - `extract_full_citations()` - Extract complete citations from LLM response
2. Modify database schema to add `citations_text` column to validations table
3. Update parser to store extracted citations in database

### Phase 2: Update Dashboard API
1. Extend `ValidationResponse` model in `dashboard/api.py` to include citations field
2. Update database schema migration for new column
3. Modify validation retrieval to include citation text

### Phase 3: Frontend Integration
1. Update job details modal in dashboard frontend to display citations
2. Add proper formatting and styling for citation display
3. Add scroll/collapse for long citation lists

**Data Sources Available:**
- **Backend logs**: `/Users/roy/Documents/Projects/citations/logs/app.log` contains original citation text
- **Current extraction**: Log entries show `Citation text preview` and `ORIGINAL` citation blocks in LLM responses
- **Dashboard database**: `validations` table needs `citations_text` column

### Current Status

**What's been done so far:**
1. ✅ Explored codebase architecture and confirmed dashboard functionality
2. ✅ Verified original citations exist in both local and production logs
3. ✅ Found log patterns for citation extraction:
   - `"Citation text preview: Smith, J. (2023). Test citation..."`
   - `"ORIGINAL:\nSmith, J. (2012). _Perception. Children's Literature..."`
4. ✅ Created comprehensive 6-task implementation plan at `docs/plans/2025-11-27-dashboard-citations-enhancement.md`
5. ✅ Confirmed current log parser extracts metrics but not citation content
6. ✅ Identified exact file locations for all required changes

**Current state:** Ready for implementation with detailed bite-sized task breakdown

**Any blockers:** None - plan is complete and technically sound

### The Question/Problem/Dilemma

**User wants to focus on:** share the full plan with the oracle including our discoverries that led to it and ask for concrete feedback on the plan

**Clear description of what help is needed related to this focus area. Be specific about:**

I have created a detailed 6-task implementation plan to add original citations to the operational dashboard. The plan includes:

1. **Database Schema Changes** - Adding `citations_text` column to validations table
2. **Log Parser Extensions** - Two new extraction functions for citation text
3. **API Model Updates** - Extending ValidationResponse to include citations
4. **Frontend Modal Updates** - Display citations in job details with proper styling
5. **Database Migration** - Migration script and cron job updates
6. **Production Deployment** - Full deployment and verification steps

**What you're trying to accomplish regarding this focus:**
- Get concrete technical feedback on the implementation approach
- Validate that the plan is technically sound and complete
- Identify any potential pitfalls or missing considerations
- Confirm that the database schema and log parsing strategies are optimal

**What options you're considering:**
- Current plan uses SQLite TEXT column for citation storage
- Log parser extracts from two different log entry patterns (preview and full ORIGINAL)
- Frontend uses simple pre-formatted display with scroll container
- Migration script adds column safely with existence check

**What's blocking you:**
- Need validation that this approach is optimal before implementation
- Want to ensure no missing edge cases or performance considerations
- Confirmation that the log parsing patterns are robust enough

**What specific guidance you need:**
- Are there any security or privacy concerns with storing original citations?
- Is the TEXT column approach optimal for potentially long citation lists?
- Are there better ways to handle the frontend display of citations?
- Should we consider any indexing or performance optimizations?
- Any missing error handling or edge cases to consider?

### Relevant Context

**Architecture Overview:**
- Backend: FastAPI + OpenAI API for citation validation
- Logs: Citations logged at `/opt/citations/logs/app.log` in production
- Dashboard: FastAPI + SQLite + HTML/JavaScript frontend
- Current workflow: Log parser extracts metrics -> Dashboard database -> Frontend display

**Log Patterns Discovered:**
```
2025-11-04 21:42:48 - citation_validator - DEBUG - app.py:275 - Citation text preview: Adli, A. (2013). Syntactic variation in French Wh-questions...

ORIGINAL:
Smith, K. (2012). _Perception. Children's Literature Association Quarterly_, 37(3), 247-249

SOURCE TYPE: journal article
```

**Current Database Schema:**
```sql
CREATE TABLE validations (
    job_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    duration_seconds REAL,
    citation_count INTEGER,
    token_usage_prompt INTEGER,
    token_usage_completion INTEGER,
    token_usage_total INTEGER,
    user_type TEXT NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT
)
```

**Current Frontend Structure:**
- Single-page HTML application with glassmorphism design
- Job details modal opens when clicking job IDs
- Currently shows: job_id, created_at, completed_at, duration, citation_count, status, error_message

### Supporting Information

**Key Files Modified in Plan:**
1. `dashboard/database.py` - Add citations_text column and migration logic
2. `dashboard/log_parser.py` - Add extract_citation_preview() and extract_full_citations()
3. `dashboard/api.py` - Extend ValidationResponse model
4. `dashboard/static/index.html` - Add citations display to job details modal
5. `dashboard/migration_add_citations.py` - Database migration script
6. `dashboard/parse_logs_cron.py` - Updated to extract citations

**Production Environment Details:**
- VPS: 178.156.161.140
- App directory: `/opt/citations/`
- Dashboard service: `citations-backend` systemd service
- Log file: `/opt/citations/logs/app.log` (7.8MB, recent activity)

**Sample Production Log Entry:**
```
2025-11-27 17:29:08 - citation_validator - INFO - app.py:590 - Creating async job 1f80c655-c915-4d65-a1b0-12f4d35c1e2a for free user
...
2025-11-27 17:29:50 - openai_provider - DEBUG - openai_provider.py:74 - Response preview: ═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Smith, K. (2012). _Perception. Children's Literature Association Quarterly_, 37(3), 247-249

SOURCE TYPE: journal article
```

**Implementation Plan File:** `docs/plans/2025-11-27-dashboard-citations-enhancement.md`

**Specific Technical Questions:**
1. Should we store citations as separate table rather than TEXT column for better normalization?
2. Are there any GDPR/privacy concerns with storing user-submitted citation text?
3. Should we implement citation formatting/parsing for better display vs. raw text?
4. Any considerations for handling extremely long citation submissions?
5. Should we add database indexing on the citations_text column for search functionality?