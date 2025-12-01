You are providing technical guidance and problem solving assistance.

## Issue Context
### Beads Issue ID: citations-hh1f

citations-hh1f: Bug: Dashboard tokens not displaying - token usage data missing from database
Status: open
Priority: P2
Type: bug
Created: 2025-12-01 12:11
Updated: 2025-12-01 12:11

## Problem
Dashboard shows '-' for all token usage data instead of showing how many tokens users submitted for validation.

## Root Cause Analysis
Investigation revealed multiple issues in the token data pipeline:

### Key Findings:
1. **Token logging IS working**: OpenAI provider correctly logs token usage to app.log (149 entries found)
2. **Log parser IS working**: Cron job parses job IDs successfully (records through Nov 30)
3. **Latest token logs**: Most recent token usage logs are from Nov 23, 2025 16:30:35
4. **Recent validations**: Database has validations through Nov 30, but no token usage data
5. **Database schema**: ✅ Has token_usage_prompt, token_usage_completion, token_usage_total fields
6. **Only 1/95 records** have token data

### Real Issue:
Recent validations (Nov 23-30) are not generating token usage logs, suggesting:
- Token logging might be broken in current code path
- Recent validations might be using a different processing path
- Or there's a gap in the log coverage

### What Needs Investigation:
- Why are there no token usage logs after Nov 23?
- Are recent validations taking a different code path?
- Is there a token logging regression?
- Are logs being rotated or cleaned?

### Impact:
Can't track user token consumption, which is important for:
- Cost analysis
- Usage patterns  
- Resource planning
- User behavior insights

## Current Status

We've completed initial investigation and identified the core mystery: token logging worked until Nov 23 (149 entries), but validations continued through Nov 30 without token logs. The log parser cron job IS working since database has recent records, but they lack token data.

### The Question/Problem/Dilemma

**Root cause analysis needed**: Why did token logging suddenly stop after Nov 23 while validation processing continued successfully?

**Specific mysteries to solve**:
1. Timeline gap: What changed around Nov 23-30 that broke token logging but kept validation working?
2. Code path divergence: Are recent validations using a different code path that bypasses the OpenAI provider token logging?
3. Deployment impact: Did a deployment around Nov 23 introduce a regression in token tracking?
4. Provider switching: Did recent validations switch to a different/mock LLM provider?

**Most likely theories we're considering**:
1. Recent validations use different code path bypassing token logging (highest probability)
2. Token logging regressed in deployment around Nov 23
3. Recent validations are using mock provider instead of OpenAI
4. Log file rotation or coverage issue
5. Conditional token logging failure

### Supporting Information

**Key timeline evidence**:
- Token logs: 149 entries, latest Nov 23, 2025 16:30:35
- Database records: 95 total, records through Nov 30, 2025
- Token data coverage: Only 1/95 records have token usage
- Log parser: Working (recent job IDs in database)

**Technical details**:
- OpenAI provider logs: `logger.info(f"Token usage: {response.usage.prompt_tokens} prompt + {response.usage.completion_tokens} completion = {response.usage.total_tokens} total")`
- Database schema: Has token_usage_prompt, token_usage_completion, token_usage_total
- Cron job: parse_logs_cron.py extracts token usage via regex: `r'Token usage: (\d+) prompt \+ (\d+) completion = (\d+) total'`

**What we need**: Expert analysis of this data pipeline mystery, systematic debugging approach, and identification of most likely root cause given the timeline evidence.
