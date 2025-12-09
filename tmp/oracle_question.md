You are providing technical guidance for adding charts to a dashboard.

## Goal
Add Chart.js to an internal dashboard (port 4646, blocked from external access) to visualize validation patterns from a SQLite database.

## Key Requirements
- Simplest implementation path
- Use Chart.js for client-side rendering
- Internal-only (already secured by Nginx block)
- Minimal performance impact

## Database Schema (validations table)
- job_id, created_at, duration_seconds, citation_count
- provider (model_a/model_b for A/B testing)
- user_type (free/paid), status (completed/failed/pending)
- results_gated, token_usage_total, error_message

## Current Stack
- FastAPI on port 4646
- SQLite database
- Vanilla JavaScript frontend
- Existing API: /api/stats, /api/validations

## Questions
1. Which charts provide most value for this data?
2. On-the-fly vs pre-aggregated API endpoints?
3. Implementation phases for gradual rollout?
4. Security considerations for new endpoints?
5. Performance impact recommendations?

Please provide concrete recommendations with specific chart types and implementation approach.
