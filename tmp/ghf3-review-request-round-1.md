You are conducting a code review.

## Task Context

### Beads Issue ID: ghf3

citations-ghf3: Epic: Smart Inline Citation Validation
Status: in_progress
Priority: P1
Type: epic

## Overview

Implement smart context-aware inline citation validation - a major new feature that validates in-text citations against the bibliography/reference list, catching year mismatches, author name typos, missing references, and missing citations.

## Business Value

- Cost Efficiency: Reduces token usage by ~95% for long documents via smart context extraction
- Freemium Model: Free tier shows first 5 reference entries with their inline matches
- Accuracy: Focused prompts reduce LLM "hallucination"
- Competitive Advantage: Few competitors check both inline AND reference formatting

## Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Input mode | Auto-detect | No toggle needed. We detect if content has inline citations. |
| Input methods | Paste OR upload DOCX | Both supported. Upload parses via mammoth. |
| Split detection | Header heuristic only | Look for "References", "Bibliography", "Works Cited". No LLM fallback. |
| Results structure | Hierarchical | Refs with nested inline citations. Orphans grouped at top. |
| Free tier limit | 5 reference entries | Each with all its inline matches. Inline is "bonus value". |
| LLM calls | Two parallel | Ref-list validation (existing) + inline validation (new). |
| Inline batching | 10 per batch, sequential | Simpler than parallel. Optimize later if needed. |
| Error types v1 | Matching + basic format | Author/year match, missing refs, et al. usage. |
| Styles | APA + MLA | Match current ref-list validator support. |
| Max citations | 100 limit | Hard limit. Reject documents with more. |

## Success Criteria

- ≥80% accuracy on inline citation validation (golden set)
- E2E tests pass for upload flow, orphan detection, free tier gating
- Dashboard tracks validation_type, inline_citation_count, orphan_count
- Production deployment with monitoring

## Implementation Phases

1. Phase 1: Backend Core - parsing.py, inline_validator.py, app.py file upload
2. Phase 2: LLM Prompts - Golden sets, prompt development, testing to ≥80% accuracy
3. Phase 3: Frontend - UploadArea, OrphanWarningBox, InlineCitationList, ValidationTable updates
4. Phase 4: Analytics & Dashboard - Logging, log parsing, database schema, API filters
5. Phase 5: Testing - Unit tests, E2E tests, test documents
6. Phase 6: Deployment - Pipeline updates, deploy, monitor

### What Was Implemented

This commit (0da10a1) completes 9 tasks across Phase 3 (Frontend) and Phase 5 (Testing):

**Phase 5 - Testing:**
- P5.2: Unit tests for inline_validator.py (19 tests covering batching, limits, organization, orphans, MLA ambiguity)
- P5.3: Test DOCX fixtures (10 files: 7 frontend, 3 backend)
- P5.1: Integration tests (6 tests for validation flow, response schema, style support)

**Phase 3 - Frontend:**
- P3.10: Removed unused useFileProcessing.js hook
- P3.14: Deleted ComingSoonModal component (upload now functional)
- P3.13: Created InlineCitationList.css (status-based styling)
- P3.2: Created InlineCitationList.jsx component (displays nested citations)
- P3.12: Updated ValidationTable.css for nested inline styles
- P3.5: Updated ValidationTable for hierarchical display (OrphanWarningBox, inline stats, nested citations)

### Requirements/Plan

**Completed Requirements:**
1. Unit tests for inline_validator.py - batch processing, max 100 citations, result organization, orphan detection, MLA ambiguous matches
2. Test DOCX files for valid/orphan/ref-only/APA/MLA/large/corrupt scenarios
3. Integration tests for async validation endpoint
4. Remove stub useFileProcessing hook (UploadArea now handles real uploads)
5. Delete ComingSoonModal (no longer needed)
6. Create InlineCitationList component with status icons and corrections
7. Update ValidationTable to show orphans, inline stats, and nested citations per reference

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: 264302f3f79c08ca9e316a6738bd2230bc2bcbd6
- HEAD_SHA: 0da10a16f69127f1d8516eebd0f9628abf2b6442

Use git commands (git diff, git show, git log, etc.) to examine the changes.

## Review Criteria

Evaluate the implementation against these criteria:

**Adherence to Task:**
- Does implementation match task requirements?
- Were all requirements addressed?
- Any scope creep or missing functionality?

**Security:**
- SQL injection, XSS, command injection vulnerabilities
- Hardcoded secrets or credentials
- Input validation and sanitization

**Code Quality:**
- Follows project standards and patterns
- Clear naming and structure
- Appropriate error handling
- Edge cases covered

**Testing:**
- Tests written and passing
- Coverage adequate
- Tests verify actual behavior
- Frontend visual/UX changes: Playwright tests REQUIRED for any visual or user interaction changes

**Performance & Documentation:**
- No obvious performance issues
- Code is self-documenting or commented

## Required Output Format

Provide structured feedback in these categories:

1. **Critical**: Must fix immediately (security, broken functionality, data loss)
2. **Important**: Should fix before merge (bugs, missing requirements, poor patterns)
3. **Minor**: Nice to have (style, naming, optimization opportunities)
4. **Strengths**: What was done well

**IMPORTANT**: Verify implementation matches task requirements above.

Be specific with file:line references for all issues.
