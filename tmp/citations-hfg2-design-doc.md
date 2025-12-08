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
