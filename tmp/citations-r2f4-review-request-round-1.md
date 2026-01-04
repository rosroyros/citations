You are conducting a code review.

## Task Context

### Beads Issue ID: citations-r2f4

citations-r2f4: P3.1: Create OrphanWarningBox component
Status: in_progress
Priority: P1
Type: task

Description:

## Context

This is the first task for Phase 3 (Frontend) of the Inline Citation Validation epic.

**Epic:** citations-ghf3 (Smart Inline Citation Validation)
**Design Doc:** `docs/plans/2026-01-01-inline-citation-validation-design.md`

## Background

Orphan citations are in-text citations that don't match any entry in the reference list. This is a critical error that users need to see prominently. The OrphanWarningBox displays at the TOP of results, before the reference list.

## Requirements

- [ ] Create `frontend/frontend/src/components/OrphanWarningBox.jsx`
- [ ] Create `frontend/frontend/src/components/OrphanWarningBox.css`
- [ ] Display warning icon and count
- [ ] List each orphan citation with its occurrence count
- [ ] Style with warning colors (yellow/amber background)
- [ ] Return null if no orphans

## Implementation Details (from issue spec)

```jsx
import './OrphanWarningBox.css'

function OrphanWarningBox({ orphans }) {
  if (!orphans || orphans.length === 0) return null

  return (
    <div className="orphan-warning-box" data-testid="orphan-warning">
      <div className="orphan-header">
        <span className="warning-icon">⚠️</span>
        <strong>{orphans.length} Citation{orphans.length > 1 ? 's' : ''} Missing from References</strong>
      </div>
      <ul className="orphan-list">
        {orphans.map(orphan => (
          <li key={orphan.id}>
            <code>{orphan.citation_text}</code>
            <span className="orphan-count">cited {orphan.citation_count}×</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default OrphanWarningBox
```

### CSS Specification

```css
.orphan-warning-box {
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.orphan-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 1rem;
}

.warning-icon {
  font-size: 1.2rem;
}

.orphan-list {
  margin: 0;
  padding-left: 24px;
}

.orphan-list li {
  margin: 6px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.orphan-list code {
  background: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-family: monospace;
  border: 1px solid #ddd;
}

.orphan-count {
  color: #856404;
  font-size: 0.85rem;
}
```

## Props Interface

```typescript
interface OrphanCitation {
  id: string;           // e.g., "c10"
  citation_text: string; // e.g., "(Brown, 2021)"
  citation_count: number; // How many times cited
}

interface Props {
  orphans: OrphanCitation[] | null;
}
```

## What Was Implemented

Created a React component (OrphanWarningBox) that displays warnings for orphan citations - in-text citations that don't match any reference list entry. The component shows a warning icon with count, lists each orphan with its occurrence count, uses amber/yellow warning styling, and returns null when no orphans exist. Includes comprehensive unit tests with 7 test cases covering all scenarios.

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: 3ce1a546cf44e6a7e5ff805d2bb11a93e6df8f41
- HEAD_SHA: 3286cba1dbc7c86707b71e7fa66307a8bfdfb3cc

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
- **Frontend visual/UX changes: Playwright tests REQUIRED for any visual or user interaction changes**

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
