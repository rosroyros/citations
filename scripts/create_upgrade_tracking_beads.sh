#!/bin/bash
set -e

# Function to create a bead and return its ID
# Usage: create_bead "Title" "Description" "Type" [ParentID] [DependsOnID]
create_bead() {
    local title="$1"
    local desc="$2"
    local type="$3"
    local parent_id="$4"
    local depends_on_id="$5"

    # Create the issue
    echo "Creating: $title ($type)..."
    id=$(bd create "$title" -d "$desc" --json | jq -r '.id')
    echo "  -> ID: $id"

    # Link to parent if provided
    if [ ! -z "$parent_id" ] && [ "$parent_id" != "null" ]; then
        echo "  -> Linking as child of $parent_id"
        bd dep add "$id" "$parent_id" --type parent-child
    fi

    # Link dependency if provided
    if [ ! -z "$depends_on_id" ] && [ "$depends_on_id" != "null" ]; then
        echo "  -> Linking as blocked by $depends_on_id"
        bd dep add "$id" "$depends_on_id" --type blocks
    fi

    # Return the ID via global variable to avoid subshell issues
    LAST_ID="$id"
}

echo "Starting Upgrade Flow Tracking bead creation..."

# --- EPIC ---
DESC_EPIC="# Epic: Upgrade Flow Tracking & Analytics Reliability

## Goal
Establish a robust, accurate, and single-source-of-truth upgrade tracking system. 

## Context
Currently, we have two divergent tracking method (legacy tables vs modern logs) and a critical bug with duplicate log parsers. This epic unifies everything under a robust \`validations.db\` architecture where:
1. Prod emits logs (low latency)
2. Cron parses logs to DB (rich analytics)
3. Tests use a special trigger to sync logs (determinism)

## Success Criteria
- Single \`log_parser.py\` source of truth
- Dashboard shows variant, product, and revenue data
- E2E tests are stable and use \`validations.db\`
- No legacy \`UPGRADE_EVENT\` table dependency
"
create_bead "Upgrade Flow Tracking & Reliability" "$DESC_EPIC" "epic" "" ""
EPIC_ID="$LAST_ID"


# --- PHASE 0: Consolidate ---
DESC_P0="# Phase 0: Consolidate Log Parsers

## Critical Bug Fix
We currently have two \`log_parser.py\` files:
- \`dashboard/log_parser.py\` (Used by Cron, has Gemini support)
- \`backend/dashboard/log_parser.py\` (Used by API, has purchase mapping)

## Task
Merge them into a single file at \`dashboard/log_parser.py\` and fix imports.

## Steps
1. Copy \`event_to_state\` mapping (purchase_completed->success) from backend version to dashboard version.
2. Delete \`backend/dashboard/log_parser.py\`.
3. Update \`backend/app.py\` imports to use project root path.
4. Verify backend API and Cron still start.

## Why
Prevents divergent behavior where dashboard sees different data than the API expects.
"
create_bead "Phase 0: Consolidate Log Parsers" "$DESC_P0" "task" "$EPIC_ID" ""
P0_ID="$LAST_ID"


# --- PHASE 1: Unit Tests ---
DESC_P1="# Phase 1: Log Parser Unit Tests

## Goal
Establish safety net before making logic changes.

## Layers to Test
1. **Extraction:** Verify \`extract_partial_results\` identifies 'locked' state.
2. **Extraction:** Verify \`extract_upgrade_workflow\` identifies job_id/events.
3. **State Accumulation:** Verify \`upgrade_state\` CSV builds correctly (locked,clicked,modal,success).
4. **Contract:** Verify log strings match regex.

## Implementation output
- New file: \`tests/test_log_parser_extraction.py\`
- New file: \`backend/tests/test_log_format_contract.py\`

## Future Self Note
Do not mock the parser logic itself; test the pure functions against sample string inputs.
"
create_bead "Phase 1: Add Log Parser Unit Tests" "$DESC_P1" "task" "$EPIC_ID" "$P0_ID"
P1_ID="$LAST_ID"


# --- PHASE 2: Rich Data & Schema ---
DESC_P2="# Phase 2: Extend Schema & Parser for Rich Data

## Goal
Enable dashboard to show revenue and variant performance.

## Tasks
1. **Schema Migration:** Create script to run \`ALTER TABLE validations ADD COLUMN experiment_variant TEXT;\` (and product_id, amount_cents).
2. **Parser Update:** Update regex to capture these fields from \`UPGRADE_WORKFLOW\` logs.
3. **Storage:** Update \`parse_job_events\` to populate the new dictionary keys.

## Architecture Note
This does NOT change the prod logging calls (they already log this data). It only changes how we read/store it in the monitoring layer.
"
create_bead "Phase 2: Extend Schema & Parser" "$DESC_P2" "task" "$EPIC_ID" "$P1_ID"
P2_ID="$LAST_ID"


# --- PHASE 3: E2E Modernization ---
DESC_P3="# Phase 3: E2E Test Synchronization & Cleanup

## The Problem
E2E tests run in seconds. Cron runs every 5 minutes. If we query DB, we see nothing.

## The Solution: Test-Mode Trigger
Modify \`backend/test_helpers.py\` to force-run the parser when requested.

## Steps
1. **Implement Trigger:** In \`/test/get-validation\`, instantiate \`CitationLogParser\` and call \`parse_logs(app_log_path)\` immediately.
2. **Migrate Tests:** Update \`pricing-integration.spec.js\` to use \`/test/get-validation\` (validations.db) instead of \`/test/get-events\`.
3. **Delete Legacy:** Remove \`UPGRADE_EVENT\` table and endpoints.

## Critical Test Case
Verify **User ID Continuity**:
- Test that a flow starting as Free User (locked/clicked) and ending as Paid User (success) is linked into a SINGLE job record in validations.db.
"
create_bead "Phase 3: E2E Test Sync & Legacy Cleanup" "$DESC_P3" "task" "$EPIC_ID" "$P2_ID"
P3_ID="$LAST_ID"


# --- PHASE 4: Integration ---
DESC_P4="# Phase 4: Integration & Analytics Verification

## Goal
Verify the end-to-end monitoring pipeline.

## Tasks
1. **Cron Integration:** Test that \`CronLogParser\` correctly identifies 'new' logs and updates the DB.
2. **Analytics Logic:** Verify \`get_user_analytics\` properly segments by the new variant/product columns.

## Verification
Run a manual purchase flow on localhost and inspect \`validations.db\` to see the full rows populated.
"
create_bead "Phase 4: Integration Validation" "$DESC_P4" "task" "$EPIC_ID" "$P3_ID"


echo "Done! Beads created."
