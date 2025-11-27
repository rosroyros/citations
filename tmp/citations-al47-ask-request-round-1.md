You are providing technical guidance and problem solving assistance.

## Issue Context
### Beads Issue ID: citations-al47

**Issue:** Collect and analyze real user citations from production
**Status:** open
**Priority:** P1

**Description Summary:**
We've been optimizing citation validation using a manually-labeled test set of 121 citations. However, we don't know if this test set represents actual user behavior in production.

**Goal:** Collect real citations submitted by users over the last few days and analyze:
1. What types of citations users actually submit
2. How they differ from our test set distribution
3. Whether our test set is representative of production usage

## Current Status

**Progress Made:**
1. ✅ Connected to production server successfully
2. ✅ Discovered that citation data is stored in application logs, not a database
3. ✅ Found real user citations in `/opt/citations/logs/app.log` with pattern `Citations to validate:`
4. ✅ Created comprehensive extraction script (`extract_production_citations.py`) that:
   - Parses last 7 days of log entries
   - Filters out test citations using common patterns
   - Classifies citation types automatically (journal, PDF, academic, government, book, webpage, other)
   - Generates statistics (length distribution, URL/DOI presence, type distribution)
   - Saves results to JSON format

**Current Approach:**
- Extracting from application logs instead of database (no citations database found)
- Using regex pattern matching to identify citation validation requests
- Automatic citation type classification based on content patterns
- Sample size will be whatever validation requests occurred in last 7 days

## The Question/Problem/Dilemma

**Primary Question:** Is our log-based extraction approach sound, or should we modify the strategy?

**Specific concerns:**
1. **Data Completeness:** We're extracting from application logs rather than a database. Will this give us a representative sample of all user citations, or only those that reached the validation endpoint?

2. **Classification Accuracy:** Our automatic classification uses simple pattern matching (DOI=journal, PDF=PDF, etc.). Is this sufficient for analysis, or do we need more sophisticated citation type detection?

3. **Filtering Quality:** We filter test citations using patterns like "Test citation", "Smith, J. (2023)", etc. Are we likely to miss edge cases or accidentally filter real citations?

4. **Sample Size Uncertainty:** We don't know how many citations we'll find in 7 days of logs. What if the sample size is too small for meaningful analysis?

5. **Analysis Scope:** The issue requests user IDs, IPs, validation results, but our log approach only gives us citation text and timestamps. Should we modify the backend to capture more metadata, or work with what we have?

**Alternative Approaches Considered:**
- Modify backend to log richer citation metadata for future analysis
- Implement a temporary database capture system
- Extend analysis window beyond 7 days if sample size is small
- Manual classification of a random sample for validation

## Relevant Context

**Technical Environment:**
- Production server: `deploy@178.156.161.140`
- Application logs: `/opt/citations/logs/app.log` (7.6MB, contains validation requests)
- No dedicated citations database found (only `credits.db` for user management)
- Backend appears to be a Flask/FastAPI application with OpenAI integration

**Log Format Examples Found:**
```
2025-11-26 21:56:29 - openai_provider - DEBUG - Citations to validate: Inter IKEA Systems B.V. (2023). _Modern Slavery Statement FY22_ [PDF]. IKEA. https://www.ikea.com/ie/en/files/pdf/2d/f7/2df72f28/modern-slavery-statement-fy22-final-19-05-23-002.pdf...
2025-11-26 23:05:09 - openai_provider - DEBUG - Citations to validate: Dombrowski, S. (2025). _Motivational interviewing (Week 7)_ [Lecture slides]. KIN 3291: Coaching Health Behaviours, University of New Brunswick.
```

**Current Test Set:** 121 manually curated citations for prompt optimization
**Success Criteria:** Collect at least 100 unique real user citations

## Supporting Information

**Script Capabilities:**
```python
# Key functions in extract_production_citations.py:
- extract_citations_from_logs(): Parses log entries by timestamp
- is_test_citation(): Filters obvious test patterns
- classify_citation_type(): Auto-classifies by content patterns
- analyze_citations(): Generates statistics and samples
- compare_with_test_set(): Compares to existing test set
```

**Current Classification Logic:**
- `journal_article`: contains DOI or "10." pattern
- `pdf_document`: contains ".pdf" or "[PDF]"
- `academic_material`: contains "university", "lecture", "slides"
- `government_document`: contains "government", ".gov", ".ca"
- `book`: contains "book" or "in _" (chapter in book)
- `reference_work`: contains "wikipedia", "encycloped"
- `webpage`: contains HTTP/HTTPS URL
- `other`: everything else

**Filtering Patterns:**
- "Test citation", "test citation", "**References**"
- "Smith, J. (2023)", "Johnson, A."
- "Sample citation", "Example citation"