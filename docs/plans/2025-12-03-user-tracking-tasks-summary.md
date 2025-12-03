# User Identification & Tracking - Task Summary

**Date Created:** 2025-12-03
**Epic ID:** citations-euzm
**Design Document:** `docs/plans/2025-12-03-user-tracking-design.md`

---

## Overview

Complete implementation of user identification and tracking system to enable user behavior analytics. This allows tracking individual user journeys across multiple validations for both free and paid users.

**Total Tasks:** 20 (1 epic + 4 phases + 15 implementation tasks)

---

## Task Hierarchy

```
citations-euzm: User Identification & Tracking (EPIC)
│
├── Phase 0: Database Migration (citations-x7g2)
│   ├── citations-ncxy: Create database migration script
│   ├── citations-61xp: Create backup and rollback procedures
│   └── citations-grva: Run database migration on production VPS
│       └── Blocks all other phases
│
├── Phase 1: Frontend Implementation (citations-oi0l)
│   ├── citations-6aoz: Add free user ID functions to creditStorage.js
│   ├── citations-x227: Update App.jsx to send X-Free-User-ID header
│   │   └── Blocked by: citations-6aoz
│   ├── citations-xgl1: Add free user ID cleanup on payment success
│   │   └── Blocked by: citations-6aoz
│   └── citations-v0rf: Write unit tests for creditStorage
│       └── Blocked by: citations-6aoz
│
├── Phase 2: Backend Implementation (citations-gyu8)
│   ├── citations-4lds: Add extract_user_id() helper function
│   ├── citations-peav: Update validation endpoints to log user IDs
│   │   └── Blocked by: citations-4lds
│   ├── citations-h5dg: Write unit tests for extract_user_id()
│   │   └── Blocked by: citations-4lds
│   └── citations-8hfj: Update existing backend tests
│       └── Blocked by: citations-peav
│
├── Phase 3: Dashboard & Testing (citations-wii5)
│   ├── citations-sowc: Update log_parser.py to extract user IDs
│   ├── citations-e3py: Update database.py for user ID columns
│   │   └── Blocked by: citations-sowc
│   ├── citations-yyu4: Update dashboard UI to display user IDs
│   │   └── Blocked by: citations-e3py
│   ├── citations-w5h3: Write dashboard parser unit tests
│   │   └── Blocked by: citations-sowc
│   └── citations-8p2l: Write E2E tests for complete flow
│
└── Phase 4: Deployment & Verification (citations-yupw)
    ├── citations-rpr3: Pre-deployment checklist and code review
    ├── citations-5jfg: Deploy to production
    │   └── Blocked by: citations-rpr3
    └── citations-svyw: Post-deployment verification
        └── Blocked by: citations-5jfg
```

---

## Phase Details

### Phase 0: Database Migration & Preparation
**ID:** citations-x7g2
**Priority:** P0
**Must Complete First:** YES - blocks all other phases

**Purpose:** Add paid_user_id and free_user_id columns to dashboard database before deploying code that uses them.

**Tasks:**
1. **citations-ncxy** - Create migration script
   - Write Python script to ALTER TABLE and add columns
   - Idempotent design (can run multiple times safely)
   - Includes verification step
   - Estimated: 1 hour

2. **citations-61xp** - Create backup/rollback procedures
   - backup.sh script for database snapshots
   - rollback.sh for restoration
   - Documentation (README.md)
   - Estimated: 1 hour

3. **citations-grva** - Run migration on production
   - Manual execution on VPS
   - Backup → Migrate → Verify flow
   - **Critical:** Must complete before code deployment
   - Estimated: 30 minutes

---

### Phase 1: Frontend - User ID Generation
**ID:** citations-oi0l
**Priority:** P0
**Blocked By:** Phase 0 (database migration)

**Purpose:** Generate UUIDs for free users and send via headers to enable tracking.

**Tasks:**
1. **citations-6aoz** - Add creditStorage.js functions
   - getFreeUserId(), ensureFreeUserId(), clearFreeUserId()
   - Uses crypto.randomUUID() browser API
   - Follows existing code patterns
   - Estimated: 30 minutes

2. **citations-x227** - Update App.jsx header sending
   - Send X-Free-User-ID header for free users
   - Base64 encode UUID
   - Apply to all validation endpoints
   - Estimated: 45 minutes

3. **citations-xgl1** - Payment success cleanup
   - Clear free_user_id when user upgrades
   - Maintain clean storage separation
   - Estimated: 30 minutes

4. **citations-v0rf** - Unit tests for creditStorage
   - 8+ tests covering all functions
   - Edge cases and error handling
   - 100% coverage goal
   - Estimated: 1 hour

**Total Phase 1 Time:** ~3 hours

---

### Phase 2: Backend - User ID Extraction & Logging
**ID:** citations-gyu8
**Priority:** P0
**Blocked By:** Phase 0 (database migration)

**Purpose:** Extract user IDs from headers and log with validations for dashboard to parse.

**Tasks:**
1. **citations-4lds** - Add extract_user_id() function
   - Parse X-User-Token (paid) or X-Free-User-ID (free)
   - Handle base64 decoding
   - Return (paid_id, free_id, user_type) tuple
   - Estimated: 45 minutes

2. **citations-peav** - Update validation endpoints
   - Call extract_user_id() in /api/validate and /api/validate/async
   - Log user IDs with validations
   - Format: "paid_user_id=X, free_user_id=Y"
   - Estimated: 45 minutes

3. **citations-h5dg** - Unit tests for extract_user_id()
   - Test paid user extraction
   - Test free user extraction
   - Test invalid base64 handling
   - Test precedence rules
   - Estimated: 1 hour

4. **citations-8hfj** - Update existing tests
   - 14 test files reference headers
   - Add assertions for user ID logging
   - Ensure compatibility
   - Estimated: 2 hours

**Total Phase 2 Time:** ~4.5 hours

---

### Phase 3: Dashboard Parser & E2E Testing
**ID:** citations-wii5
**Priority:** P0
**Blocked By:** Phase 1 and Phase 2

**Purpose:** Parse user IDs from logs into dashboard database and enable UI filtering. Add comprehensive end-to-end tests.

**Tasks:**
1. **citations-sowc** - Update log_parser.py
   - Add regex pattern for user ID extraction
   - Extract from "paid_user_id=X, free_user_id=Y" format
   - Handle old logs without IDs (graceful degradation)
   - Estimated: 1 hour

2. **citations-e3py** - Update database.py
   - Modify insert_validation() for new columns
   - Add query methods for user ID filtering
   - Handle NULL values for old records
   - Estimated: 1 hour

3. **citations-yyu4** - Update dashboard UI
   - Add User ID column to table
   - Add filter/search by user ID
   - Display format: paid=token[:8], free=uuid[:8]...
   - Estimated: 1.5 hours

4. **citations-w5h3** - Dashboard parser unit tests
   - Test user ID extraction from various log formats
   - Test handling of old logs
   - Test NULL value handling
   - Estimated: 1 hour

5. **citations-8p2l** - E2E tests for complete flow
   - Test free user validation (UUID generated and sent)
   - Test paid user validation (token sent, no UUID)
   - Test UUID persistence across page refresh
   - Test free→paid conversion (UUID cleared)
   - Estimated: 2 hours

**Total Phase 3 Time:** ~6.5 hours

---

### Phase 4: Deployment & Production Verification
**ID:** citations-yupw
**Priority:** P0
**Blocked By:** Phase 3

**Purpose:** Deploy to production and verify everything works in live environment.

**Tasks:**
1. **citations-rpr3** - Pre-deployment checklist
   - All tests passing (unit, integration, E2E)
   - Frontend builds successfully
   - Code reviewed (use /oracle-review)
   - Migration verified on VPS
   - Estimated: 1 hour

2. **citations-5jfg** - Deploy to production
   - Git push to main
   - SSH to VPS
   - Run deployment script
   - Monitor logs during deployment
   - Estimated: 30 minutes

3. **citations-svyw** - Post-deployment verification
   - Check backend logs show user IDs
   - Verify dashboard parser runs without errors
   - Test free user flow (generates UUID)
   - Test paid user flow (logs token)
   - Verify dashboard displays user IDs
   - Estimated: 1 hour

**Total Phase 4 Time:** ~2.5 hours

---

## Timeline Estimate

**Total Implementation Time:** ~17 hours

**Breakdown by phase:**
- Phase 0 (Migration): 2.5 hours
- Phase 1 (Frontend): 3 hours
- Phase 2 (Backend): 4.5 hours
- Phase 3 (Dashboard): 6.5 hours
- Phase 4 (Deployment): 2.5 hours

**Recommended Schedule:**
- **Session 1:** Phase 0 (migration prep and execution)
- **Session 2:** Phase 1 (frontend implementation and tests)
- **Session 3:** Phase 2 (backend implementation and tests)
- **Session 4:** Phase 3 tasks 1-3 (dashboard parser and UI)
- **Session 5:** Phase 3 tasks 4-5 (testing)
- **Session 6:** Phase 4 (deployment and verification)

**Total:** 6 sessions over 2-3 days

---

## Critical Path

The critical path (longest dependency chain):

1. **Phase 0: Run migration** (citations-grva)
   ↓ blocks
2. **Phase 1: Add creditStorage functions** (citations-6aoz)
   ↓ blocks
3. **Phase 1: Update App.jsx** (citations-x227)
   ↓ blocks
4. **Phase 3: Update log parser** (citations-sowc)
   ↓ blocks
5. **Phase 3: Update database** (citations-e3py)
   ↓ blocks
6. **Phase 3: Update UI** (citations-yyu4)
   ↓ blocks
7. **Phase 4: Deploy** (citations-5jfg)
   ↓ blocks
8. **Phase 4: Verify** (citations-svyw)

**Critical Path Time:** ~8 hours (minimum time if working sequentially on critical path only)

---

## Parallel Work Opportunities

Tasks that can be done in parallel (within same phase):

**Phase 1:**
- citations-x227, citations-xgl1, citations-v0rf can all proceed once citations-6aoz is complete

**Phase 2:**
- citations-peav and citations-h5dg can proceed once citations-4lds is complete
- (citations-8hfj must wait for citations-peav)

**Phase 3:**
- citations-e3py and citations-w5h3 can proceed once citations-sowc is complete
- citations-8p2l can start as soon as Phase 1 and Phase 2 are both complete

**Optimization:** Can reduce total time to ~12-13 hours with parallel work.

---

## Risk Mitigation

**High-Risk Tasks:**
1. **citations-grva** (run migration on prod)
   - Mitigation: Backup procedures, tested migration script, rollback plan
   - Can revert: Yes (restore from backup)

2. **citations-5jfg** (deploy to production)
   - Mitigation: All tests passing, code reviewed, deployment tested on staging
   - Can revert: Yes (git revert + redeploy)

**Medium-Risk Tasks:**
3. **citations-8hfj** (update 14 test files)
   - Mitigation: Run tests after each file update
   - Can cause: Test suite failures if not updated correctly

4. **citations-peav** (update validation endpoints)
   - Mitigation: Test locally with mock data
   - Can cause: Validation failures if logging breaks execution

**Low-Risk Tasks:**
- All frontend tasks (isolated, easy to test locally)
- All unit test tasks (no prod impact)
- Dashboard tasks (dashboard is read-only, can't break validations)

---

## Success Metrics

**Technical Success:**
- [ ] All 15 implementation tasks completed and closed
- [ ] All tests passing (unit, integration, E2E)
- [ ] No errors in production logs related to user tracking
- [ ] Dashboard shows user IDs for new validations

**Business Success:**
- [ ] Can query validations by user ID
- [ ] Can see user journeys (multiple validations from same user)
- [ ] Can count distinct users (not just validation volume)
- [ ] Analytics queries work (see design doc section 8.2)

**Example Analytics Query:**
```sql
-- How many users validated multiple times?
SELECT COUNT(*) as repeat_users
FROM (
  SELECT free_user_id, COUNT(*) as validation_count
  FROM validations
  WHERE free_user_id IS NOT NULL
  GROUP BY free_user_id
  HAVING COUNT(*) > 1
);
```

---

## Next Steps

1. **Review this summary and design doc** with team
2. **Start with Phase 0** (database migration) - must complete first
3. **Use beads commands to track progress:**
   ```bash
   bd show citations-x7g2  # Start with Phase 0
   bd update <task-id> --status in_progress  # When starting task
   bd close <task-id> --reason "Completed successfully"  # When done
   ```

4. **Update epic with progress:**
   ```bash
   bd update citations-euzm --description "$(bd show citations-euzm --format description)

   ## Progress - $(date +%Y-%m-%d)
   - Completed Phase 0 (migration)
   - Working on Phase 1 (frontend)
   "
   ```

---

## Resources

- **Design Document:** `docs/plans/2025-12-03-user-tracking-design.md`
- **Epic:** `citations-euzm`
- **View all tasks:** `bd list --json | jq -r '.[] | select(.id | startswith("citations-")) | "\(.id): \(.title)"'`
- **View dependency tree:** `bd dep tree citations-euzm`

---

**Document Last Updated:** 2025-12-03
**Total Tasks Created:** 20
**Estimated Total Time:** 17 hours (can be reduced to 12-13 hours with parallel work)
