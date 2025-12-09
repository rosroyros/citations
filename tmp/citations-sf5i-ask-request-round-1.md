You are providing technical guidance and problem solving assistance.

## Issue Context
### Beads Issue ID: citations-sf5i

citations-sf5i: Add Charts to Dashboard
Status: open
Priority: P1
Type: feature
Created: 2025-12-09 17:49
Updated: 2025-12-09 17:49

## Context
We need to add visual charts to our internal dashboard to better understand validation patterns and system performance. The dashboard runs on port 4646 and is blocked from external access by Nginx, making it safe for internal tools.

## Requirements
- Add Chart.js for lightweight, client-side charting
- Create charts based on validations table data
- Ensure minimal performance impact on production system
- Keep dashboard internal-only (no external access)

## Technical Details
- Database: SQLite (validations table with fields: job_id, created_at, duration_seconds, citation_count, provider, user_type, status, etc.)
- Current Tech Stack: FastAPI dashboard on port 4646, React-like frontend with vanilla JS
- Security: Dashboard already blocked by Nginx, endpoints inherit this protection

### Current Status

We have analyzed the dashboard structure and identified that it:
- Serves HTML from /dashboard/static/index.html
- Uses FastAPI with SQLite database (validations.db)
- Has existing API endpoints: /api/stats, /api/gated-stats, /api/validations
- Runs on port 4646, blocked externally by Nginx
- Currently displays data in tables and text statistics

### The Question/Problem/Dilemma

User wants to focus on: "present the goal and your recommended (simplest) path for the entire project (chartjs + charts to include based on the data in validations table + setup/security)"

I need guidance on:
1. Overall implementation approach for adding Chart.js to the dashboard
2. Which specific charts would be most valuable based on the validations table schema
3. Whether to use on-the-fly aggregation vs pre-aggregated API endpoints
4. Security considerations for new chart endpoints
5. Simplest path to get working charts quickly

### Relevant Context

Validations table schema includes:
- job_id (TEXT)
- created_at (TIMESTAMP)
- duration_seconds (REAL)
- citation_count (INTEGER)
- provider (TEXT) - 'model_a' or 'model_b' for A/B testing
- user_type (TEXT) - 'free' or 'paid'
- status (TEXT) - 'completed', 'failed', 'pending'
- results_gated (BOOLEAN)
- token_usage_total (INTEGER)
- error_message (TEXT)

The dashboard is internal-only, accessed via VPN at http://100.98.211.49:4646, and blocked from external access by Nginx configuration.

### Supporting Information

Current dashboard features:
- Statistics display (total, completed, failed, avg duration, avg citations)
- Filtering by date range, status, user type
- Pagination for validation records
- Job detail expansion
- Gated results analytics (when applicable)

We want to add visual charts without disrupting the existing functionality and maintaining security.