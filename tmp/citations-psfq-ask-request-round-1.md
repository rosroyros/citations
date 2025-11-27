You are providing technical guidance and problem solving assistance.

## Issue Context
### Beads Issue ID: citations-psfq

**citations-psfq**: Enhance citation logging to capture full citation text for analysis dataset
Status: open
Priority: P1
Type: feature
Created: 2025-11-27 14:32
Updated: 2025-11-27 14:32

Description:
## Context
Currently citation logging truncates the full citation text to only 200 characters (line 45 in openai_provider.py). This limits our ability to analyze the complete citation dataset for research, quality monitoring, and debugging purposes.

## Requirements
- [ ] Remove or significantly increase the 200 character truncation limit in citation logging
- [ ] Ensure full citation text is captured in debug logs for dataset analysis
- [ ] Balance log storage considerations with data completeness needs

## Implementation Approach
Simple fix: Modify the debug log statement in backend/providers/openai_provider.py to capture more of the citation text, removing the [:200] truncation or setting a much higher limit.

## Verification Criteria
- [ ] Full citation text appears in production logs
- [ ] Log parser can handle longer citation text properly
- [ ] Log file sizes remain manageable for operational use

## Dependencies
None - this is a straightforward logging enhancement.

### Current Status

**Implementation completed**: We have implemented the simple fix approach by modifying the debug log statement in `backend/providers/openai_provider.py` line 45.

**Change made**:
- **Before**: `logger.debug(f"Citations to validate: {citations[:200]}...")`
- **After**: `logger.debug(f"Citations to validate: {citations[:2000]}...")`

**Rationale**: Increased truncation limit from 200 to 2000 characters to capture most complete citations while maintaining some protection against extremely long inputs. This addresses the user's goal of building a comprehensive dataset for analysis while being mindful of log storage concerns.

**What we're trying to accomplish**: The user wants to enhance citation logging to capture significantly more citation text for building an analysis dataset. They specifically chose option 1-b (build dataset for analysis), option 2-d (increase truncation limit while managing storage/privacy concerns), and option 3-a (simple fix approach).

### The Question/Problem/Dilemma

We've implemented a straightforward solution and would like the Oracle to review our approach and provide guidance on:

1. **Is a 2000 character limit appropriate** for capturing full citation text, or should we consider a different limit? We want to balance completeness with storage efficiency.

2. **Are there any potential issues** with the current log parser (`dashboard/log_parser.py`) handling longer citation text? The parser doesn't currently extract citation content specifically from the "Citations to validate" debug lines.

3. **Storage and operational impact**: What considerations should we have for the increased log volume, and should we implement any log rotation or archival policies for the enhanced citation data?

4. **Alternative approaches**: Should we consider any of these alternatives or is our simple approach the right balance:
   - Separate dedicated citation log file/destination
   - Different log level for full citations (e.g., INFO vs DEBUG)
   - Structured logging (JSON format) for better parsing

5. **Production deployment**: Any specific considerations for rolling out this change to production?

### Relevant Context

**Current logging pattern**:
```
2025-11-27 09:51:37 - openai_provider - DEBUG - openai_provider.py:45 - Citations to validate: Shouli, A., Barthwal, A., Campbell, M., & Shrestha, A. K. (2025, March 19). Ethical AI for...
```

**After our change, this will now capture up to 2000 characters** instead of 200, providing much more complete citation data for analysis.

**Current citation length analysis** from production data shows:
- Mean citation length: ~154 characters
- Max observed length: 203 characters
- Median length: 180 characters

This suggests that 2000 characters should capture virtually all complete citations.

### Supporting Information

**Git diff of the change**:
```diff
- logger.debug(f"Citations to validate: {citations[:200]}...")
+ logger.debug(f"Citations to validate: {citations[:2000]}...")
```

**File location**: `backend/providers/openai_provider.py:45`

**Current citation data insights**:
- We have extracted 1,036 citations from production logs for analysis
- Many citations were truncated at 200 characters, limiting analysis quality
- The longest observed complete citation was 203 characters in our current dataset
- We're building this dataset for research/analysis purposes as per user requirement 1-b

**Log parser considerations**: The current `dashboard/log_parser.py` focuses on extracting job lifecycle events, metrics, and structured data (durations, token usage, etc.) but doesn't specifically parse citation content from debug logs. The enhanced citation data will be available in raw log files for analysis.