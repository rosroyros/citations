You are providing technical guidance and problem solving assistance.

## Issue Context
### Beads Issue ID: citations-hfg2

citations-hfg2: Enhance dashboard with upgrade workflow tracking
Status: open
Priority: P2
Type: feature
Created: 2025-12-05 16:11
Updated: 2025-12-05 16:11

Description:
## Context
We currently track validation jobs (duration, tokens, etc.) in the dashboard, but we don't track what happens after the job completes regarding user upgrade behavior. Understanding the upgrade funnel is critical for optimizing conversion and user experience.

## Requirements
- [ ] Track if users were presented with locked results after validation
- [ ] Track if users clicked the upgrade button
- [ ] Track if users opened the upgrade modal
- [ ] Track if users completed the Polar checkout flow
- [ ] Track if users returned from Polar to our success page
- [ ] Display this information as a series of checkmarks in the dashboard

## Implementation Approach
Need to:
1. Add new database fields/columns to track upgrade funnel events
2. Update validation job tracking to record upgrade-related events
3. Modify dashboard UI to display upgrade workflow status
4. Ensure proper event tracking for Polar integration

## Verification Criteria
- [ ] Dashboard shows upgrade workflow checkmarks for each validation job
- [ ] All upgrade funnel events are properly tracked and stored
- [ ] UI clearly indicates where users drop off in the upgrade process

### Current Status

We've brainstormed the upgrade funnel steps and created a design document. The proposed approach uses a single database column for upgrade state and log-based tracking rather than direct database writes.

### The Question/Problem/Dilemma

User wants to focus on: "share the design doc with the zoracle and ask for concrete feedback - then we can review the feedback together"

I'm looking for concrete feedback on our upgrade workflow tracking design, specifically:
1. Is the log-based approach with localStorage for job context appropriate?
2. Are there any architectural concerns with the proposed implementation?
3. Should we reconsider any aspects of the design?
4. Any missing edge cases or considerations?

### Relevant Context

Current system has:
- SQLite database with validations table tracking job lifecycle
- Existing gating system that tracks when results are gated/revealed
- Polar checkout integration for payments
- Log parser that extracts structured events from app.log
- Dashboard showing validation metrics

Key technical details:
- Free tier limit: 10 citations
- Results are truncated with "upgrade to see more" button when limit exceeded
- Polar checkout flow: upgrade button → modal → payment → success page
- Current logging: GATING_DECISION events, REVEAL_EVENT events
- No current tracking of upgrade funnel progression

### Supporting Information

Design document content:

# Upgrade Workflow Tracking Design Document

## Overview
Add upgrade funnel tracking to the citations dashboard to understand user behavior from hitting quota limits through payment completion.

## Current State Analysis
- Dashboard already tracks validation jobs (duration, tokens, status)
- Gating system tracks when results are gated vs revealed
- Polar checkout integration exists but no funnel tracking
- Free tier limit is 10 citations, after which results are truncated

## Proposed Upgrade Funnel Steps
1. **🔒 Locked**: Results truncated due to quota exceeded ("Free tier limit reached")
2. **🛒 Upgrade**: User clicks upgrade button
3. **💳 Modal**: User clicks proceed in Polar checkout modal
4. **✅ Success**: User completes payment and returns

## Technical Design

### Database Schema
Add single `upgrade_state` column to validations table:
```sql
ALTER TABLE validations ADD COLUMN upgrade_state TEXT;
```
Possible values: `NULL`, `locked`, `clicked`, `modal`, `success`

### Backend Changes
1. **Fix existing logs** - Add job_id to "Free tier limit reached" message
2. **Add new log events**:
   - `UPGRADE_WORKFLOW: job_id={id} event=clicked_upgrade`
   - `UPGRADE_WORKFLOW: job_id={id} event=modal_proceed`
   - `UPGRADE_WORKFLOW: job_id={id} event=success`

### Frontend Changes
1. **When upgrade button clicked**:
   - Store job_id in localStorage: `pending_upgrade_job_id`
   - Track click event
2. **When modal proceed clicked**:
   - Track event
3. **On success page load**:
   - Read job_id from localStorage
   - Send to backend to log success event
   - Clear localStorage

### Dashboard UI
Add "Upgrade" column to validations table:
- Shows icon sequence: 🔒 🛒 💳 ✅
- Icons always visible, colored when step completed
- Based on upgrade_state value

### Log Parser Updates
Extract UPGRADE_WORKFLOW events and map to upgrade_state:
- `clicked_upgrade` → `clicked`
- `modal_proceed` → `modal`
- `success` → `success`
- Existing "Free tier limit reached" → `locked`

## Implementation Plan
1. Backend: Add job_id to existing limit logs
2. Frontend: Add localStorage tracking on upgrade flow
3. Backend: Add new UPGRADE_WORKFLOW log events
4. Database: Add upgrade_state column
5. Dashboard: Update log parser
6. Frontend: Add upgrade icons to table

## Explicitly Ignored Concerns (MVP)
- Multiple tabs overwriting localStorage
- Direct navigation to /success page
- Attribution window for stale job_ids
- Polar webhook context limitations

## Success Criteria
- Dashboard shows upgrade funnel for each validation job
- All steps tracked through log parsing (no direct DB writes)
- Visual indicators clearly show where users drop off