# Dashboard Implementation Guide - Complete Issue Structure

**Last Updated:** 2025-11-27
**Epic Issue:** citations-xyov
**Design Doc:** docs/plans/2025-11-27-dashboard-design.md

---

## Overview

This document provides a complete map of all beads (issues) created for the operational dashboard project, with their relationships, context, and implementation order.

---

## Issue Hierarchy

```
citations-xyov (P0) - Operational Dashboard Epic
│
├── citations-ll5r (P0) - Dashboard Infrastructure
│   ├── citations-p3o2 (P0) - Log Parser Module
│   ├── citations-nyoz (P0) - SQLite Database
│   ├── citations-a34z (P0) - Cron Job
│   └── citations-gis2 (P0) - Systemd Service
│
├── citations-7lus (P0) - Dashboard API Layer
│   └── citations-hagy (P0) - FastAPI Endpoints
│       (depends on: citations-nyoz - database)
│
├── citations-a9dv (P0) - Dashboard Frontend
│   ├── citations-pn7d (P0) - HTML Structure
│   ├── citations-adbi (P0) - CSS Styling
│   └── citations-eay2 (P0) - JavaScript Logic
│       (all depend on: citations-7lus - API)
│
├── PHASE 2: Future Enhancements (all P2, blocked by MVP)
│   ├── citations-08wk - User IP/ID Logging
│   ├── citations-wekx - Credits Logging
│   ├── citations-oaci - Validation Outcome Summary
│   └── citations-6b51 - Full Results Persistence
│
└── INFRASTRUCTURE (parallel track)
    └── citations-au4u (P1) - Log Rotation Setup
```

---

## Implementation Order

### Session 1: Infrastructure Foundation
**Goal:** Data pipeline from logs to database

1. **citations-p3o2** - Log Parser Module (~4 hours)
   - Two-pass parsing strategy
   - Extract job lifecycle and metrics
   - Handle edge cases (missing data, compressed logs)
   - Unit + integration tests

2. **citations-nyoz** - SQLite Database (~2-3 hours)
   - Create schema (validations, metadata, errors tables)
   - Implement query helpers
   - Add indexes for performance
   - Test all operations

3. **citations-a34z** - Cron Job (~1 hour)
   - Incremental parsing script
   - Initial data load (last 3 days)
   - Error handling and logging
   - Schedule in cron

4. **citations-gis2** - Systemd Service (~30 min)
   - Service file configuration
   - Enable and start service
   - Verify auto-restart and boot behavior

**Deliverable:** Database populated with 3 days of data, updating every 5 minutes

---

### Session 2: API Layer
**Goal:** REST endpoints to serve data

5. **citations-hagy** - FastAPI Endpoints (~2-3 hours)
   - GET /api/validations (with filters)
   - GET /api/validations/{id}
   - GET /api/stats
   - GET /api/health
   - Static file serving

**Deliverable:** API accessible on port 4646, returns correct data

---

### Session 3: Frontend UI
**Goal:** Web interface for viewing data

6. **citations-pn7d** - HTML Structure (~1 hour)
   - Page layout (header, filters, table, pagination)
   - Semantic HTML structure
   - Modal for job details

7. **citations-adbi** - CSS Styling (~2 hours)
   - Brand color palette application
   - Status color coding (green/amber/orange)
   - Table styling and responsive layout
   - Modal styling

8. **citations-eay2** - JavaScript Logic (~3-4 hours)
   - Fetch data from API
   - Render table dynamically
   - Handle sorting, filtering, pagination
   - Expand/collapse job details
   - Manual refresh

**Deliverable:** Fully functional dashboard accessible in browser

---

### Session 4: Polish & Infrastructure
**Goal:** Production readiness

9. **Testing** (~1-2 hours)
   - End-to-end testing with real data
   - Edge case validation
   - Performance verification
   - Bug fixes

10. **citations-au4u** - Log Rotation (~1 hour)
    - Configure logrotate
    - Test rotation
    - Update parser for .gz support

11. **Documentation** (~30 min)
    - README for setup/deployment
    - Operations guide
    - Troubleshooting tips

**Deliverable:** Production-ready dashboard, documented, stable

---

## Phase 2: Future Enhancements
**When:** After MVP runs successfully for 1+ week

**Evaluate actual needs based on MVP usage:**

12. **citations-08wk** - User IP/ID Logging (~2-3 hours)
    - Do we actually need user tracking?
    - Is abuse a real problem?
    - Privacy implications?

13. **citations-wekx** - Credits Logging (~1-2 hours)
    - Are billing discrepancies happening?
    - Do we need audit trail?

14. **citations-oaci** - Validation Outcome Summary (~1-2 hours)
    - Is quality tracking valuable?
    - Do we see patterns in errors?

15. **citations-6b51** - Full Results Persistence (~2-3 hours)
    - Do users need citation drill-down?
    - Is dashboard useful without it?

**Approach:** Implement only what proves necessary from actual usage patterns.

---

## Key Design Decisions (Context for Future Self)

### Why Custom Build vs Grafana/Loki?
- **Simplicity:** No new services, lower resource usage
- **Speed:** Faster to build exact features needed
- **Control:** Full customization, no learning curve
- **Cost:** Reuse existing FastAPI, no new dependencies

### Why Two-Pass Log Parsing?
- **Correctness:** Logs aren't perfectly ordered
- **Simplicity:** Easier to debug than state machine
- **Performance:** Fast enough for our log volume (<30MB/30 days)
- **Extensibility:** Easy to add new metrics without complex state

### Why SQLite vs PostgreSQL?
- **Deployment:** No separate service to manage
- **Scale:** Handles our query volume easily
- **Backup:** Single file, easy to copy
- **Simplicity:** Stdlib support, no drivers needed

### Why 5-Minute Cron vs Real-Time?
- **Good enough:** Operational dashboard doesn't need real-time
- **Simplicity:** Cron handles restarts/failures automatically
- **Load:** Reduces server overhead vs continuous parsing
- **Flexibility:** Easy to adjust frequency if needed

### Why Manual Refresh vs Auto-Refresh?
- **User control:** User decides when to update
- **Server load:** No polling when not watching
- **Simplicity:** No WebSocket/SSE complexity
- **Typical usage:** Dashboard checked periodically, not monitored continuously

### Why No Authentication?
- **Network security:** VPN/SSH provides access control
- **Internal tool:** Not exposed to public internet
- **Simplicity:** No auth implementation/maintenance
- **Can add later:** If needed, easy to add password layer

---

## Success Metrics

### MVP Success (After 1 Week)
- ✓ Dashboard used for debugging at least 1 issue
- ✓ No parse errors in last 24 hours
- ✓ Query performance <500ms consistently
- ✓ Zero downtime (service restarts handled)
- ✓ Team finds it useful (informal feedback)

### Project Success (After 1 Month)
- ✓ MVP stable and in regular use
- ✓ Phase 2 needs evaluated and prioritized
- ✓ Log rotation preventing disk issues
- ✓ Informed at least 1 product/scaling decision

---

## Risk Mitigation Strategies

### Risk: Log Rotation Breaks Parser
**Impact:** Missing data, parse errors
**Mitigation:**
- Test parser with compressed logs (.gz) before rotation
- Track last_parsed_line_number as fallback
- Monitor parse_errors table for issues

### Risk: Database Grows Too Large
**Impact:** Slow queries, disk space
**Mitigation:**
- 90-day retention policy (configurable)
- Monthly vacuum scheduled in cron
- Monitor disk usage alerts

### Risk: Parsing Performance Degrades
**Impact:** Cron job times out, missing data
**Mitigation:**
- Current approach handles 30 days easily (~30s)
- Can switch to stream parsing if needed
- Can optimize regex patterns
- Can add indexes for faster queries

### Risk: MVP Not Useful
**Impact:** Wasted effort on enhancements
**Mitigation:**
- Low initial investment (3-4 sessions)
- Phase 2 gated by actual usage validation
- Easy to abandon if not valuable
- Reusable components (FastAPI, SQLite patterns)

---

## Non-Goals & Scope Boundaries

### Explicitly Out of Scope
- Real-time updates (5-min delay acceptable)
- Authentication (network security sufficient)
- Charts/graphs (table view sufficient)
- Email alerts (can add later)
- Mobile optimization (desktop-only)
- CSV export (can add later)
- Multi-server support (single VPS)
- Advanced analytics (simple stats sufficient)

### Why These Are Out of Scope
- **YAGNI:** Add complexity only when proven necessary
- **MVP focus:** Deliver value quickly, iterate based on usage
- **Simplicity:** Each feature adds maintenance burden
- **Time:** Focus on core utility first

---

## Troubleshooting Guide

### Dashboard Not Accessible
1. Check service: `sudo systemctl status citations-dashboard`
2. Check port: `ss -tlnp | grep 4646`
3. Check logs: `sudo journalctl -u citations-dashboard -e`
4. Verify VPN/SSH connection

### No Data Showing
1. Check cron ran: `cat /opt/citations/logs/dashboard-cron.log`
2. Check database: `sqlite3 /opt/citations/dashboard/data/validations.db "SELECT COUNT(*) FROM validations;"`
3. Check API health: `curl http://localhost:4646/api/health`
4. Check parse errors: `sqlite3 /opt/citations/dashboard/data/validations.db "SELECT * FROM parser_errors;"`

### Slow Query Performance
1. Check index usage: `EXPLAIN QUERY PLAN SELECT ...`
2. Vacuum database: `sqlite3 validations.db "VACUUM;"`
3. Check retention: How many days of data?
4. Consider adding more indexes

### Parse Errors
1. Check error table: `SELECT * FROM parser_errors ORDER BY timestamp DESC LIMIT 10;`
2. Check log format changes in backend
3. Verify regex patterns still match
4. Check for log corruption

---

## Future Considerations

### If We Outgrow SQLite
**Signs:**
- Query times >1s consistently
- Database size >1GB
- Need for multi-server deployment

**Migration Path:**
1. PostgreSQL (same schema, minimal code changes)
2. Or: DuckDB for better analytics
3. Or: Separate read replicas

### If We Need Real-Time
**Options:**
1. WebSocket updates from backend
2. Server-Sent Events (SSE)
3. Reduce cron frequency to 1 minute

**Consider:** Is real-time actually needed, or just nice-to-have?

### If We Need Advanced Analytics
**Options:**
1. Add charting library (Chart.js, D3)
2. Export to BI tool (Metabase, Redash)
3. Build separate analytics service

**Consider:** Use dashboard data to inform what analytics matter

---

## Maintenance Tasks

### Daily
- Monitor parse errors in dashboard
- Check service status

### Weekly
- Review disk space usage
- Check slow query log

### Monthly
- Vacuum database: `sqlite3 validations.db "VACUUM;"`
- Review retention policy (adjust if needed)
- Check for unused indexes

### Quarterly
- Review Phase 2 enhancements (still needed?)
- Performance audit (query times)
- Security review (logs contain PII?)

---

## Contact & Support

**Documentation:**
- Design: `docs/plans/2025-11-27-dashboard-design.md`
- This guide: `docs/dashboard-implementation-guide.md`
- Code: `/opt/citations/dashboard/`

**Logs:**
- Application: `/opt/citations/logs/app.log`
- Dashboard cron: `/opt/citations/logs/dashboard-cron.log`
- Service: `sudo journalctl -u citations-dashboard`

**Database:**
- Location: `/opt/citations/dashboard/data/validations.db`
- Backup: Copy file to backup location
- Query: `sqlite3 validations.db`

---

## Appendix: Complete Issue List

| Issue ID | Title | Type | Priority | Status | Estimated |
|----------|-------|------|----------|---------|-----------|
| citations-xyov | Operational Dashboard Epic | feature | P0 | open | 12-16h |
| citations-ll5r | Dashboard Infrastructure | task | P0 | open | 8-10h |
| citations-p3o2 | Log Parser Module | task | P0 | open | 4h |
| citations-nyoz | SQLite Database | task | P0 | open | 2-3h |
| citations-a34z | Cron Job | task | P0 | open | 1h |
| citations-gis2 | Systemd Service | task | P0 | open | 30min |
| citations-7lus | Dashboard API Layer | task | P0 | open | 2-3h |
| citations-hagy | FastAPI Endpoints | task | P0 | open | 2-3h |
| citations-a9dv | Dashboard Frontend | task | P0 | open | 6-7h |
| citations-pn7d | HTML Structure | task | P0 | open | 1h |
| citations-adbi | CSS Styling | task | P0 | open | 2h |
| citations-eay2 | JavaScript Logic | task | P0 | open | 3-4h |
| citations-08wk | User IP/ID Logging | task | P2 | open | 2-3h |
| citations-wekx | Credits Logging | task | P2 | open | 1-2h |
| citations-oaci | Validation Outcome Summary | task | P2 | open | 1-2h |
| citations-6b51 | Full Results Persistence | task | P2 | open | 2-3h |
| citations-au4u | Log Rotation Setup | task | P1 | open | 1h |

**Total Estimated Effort:**
- Phase 1 (MVP): 16-20 hours (4 sessions @ 4-5h each)
- Phase 2 (Enhancements): 6-10 hours (evaluate after MVP)
- Infrastructure: 1 hour (parallel)

---

**End of Implementation Guide**
