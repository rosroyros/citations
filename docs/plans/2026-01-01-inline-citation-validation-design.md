# Design: Smart Context-Aware Inline Citation Validation

**Status:** Final Design (Ready for Implementation)
**Last Updated:** 2026-01-03
**Authors:** Roy + Claude

---

## Table of Contents
1. [Overview & Problem Statement](#1-overview--problem-statement)
2. [Key Decisions Summary](#2-key-decisions-summary)
3. [User Experience Flow](#3-user-experience-flow)
4. [Architecture & Data Flow](#4-architecture--data-flow)
5. [Backend Implementation](#5-backend-implementation)
6. [Frontend Implementation](#6-frontend-implementation)
7. [LLM Prompt Development](#7-llm-prompt-development)
8. [Analytics & Dashboard](#8-analytics--dashboard)
9. [Testing Strategy](#9-testing-strategy)
10. [File-by-File Implementation Scope](#10-file-by-file-implementation-scope)
11. [Implementation Phases](#11-implementation-phases)

---

## 1. Overview & Problem Statement

### The Problem

Currently, our citation validator only checks the Reference List/Bibliography formatting. Users often have errors *within* their document text:
- Year mismatches: "(Smith, 2019)" in text vs "Smith, J. (2020)" in bibliography
- Author name typos: "(Smyth, 2019)" vs "Smith, J. (2019)"
- Missing references: Citations in text with no corresponding bibliography entry
- Missing citations: References that are never cited in the text

Checking an entire document (e.g., 50 pages) for these inline errors is prohibitively expensive (LLM token costs) and slow if we simply send the full text.

### The Solution: Smart Context Extraction

Instead of sending the full document to the LLM, we:
1. **Parse & Split:** Separately identify the "Body Text" and the "Reference List" using header detection
2. **Scan:** Use fast, free regex patterns to find inline citation candidates (e.g., `(Name, Year)`)
3. **Extract Context:** Extract only the citation marker text (not surrounding paragraph)
4. **Validate in Batches:** Send citation markers + Reference List to the LLM

### Business Value

- **Cost Efficiency:** Reduces token usage by ~95% for long documents
- **Freemium Model:** Free tier shows first 5 reference entries with their inline matches
- **Accuracy:** Focused prompts reduce LLM "hallucination"
- **Competitive Advantage:** Few competitors check both inline AND reference formatting

### Competitive Landscape

Based on research (Jan 2026):
- **Most tools only generate citations** (MyBib, EasyBib, Citation Machine)
- **Only 3 competitors do inline + reference matching:**
  - Recite - Upload .docx, color-coded results
  - Scribbr - Upload .docx, AI-powered, APA-focused
  - Grammarly Premium - Auto-detects citations in text
- **No competitor offers:**
  - "Check first 5 free" freemium for inline
  - Smart context extraction (all process full doc)
  - Both paste AND upload support

---

## 2. Key Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Input mode** | Auto-detect | No toggle needed. We detect if content has inline citations. |
| **Input methods** | Paste OR upload DOCX | Both supported. Upload parses via mammoth. |
| **Split detection** | Header heuristic only | Look for "References", "Bibliography", "Works Cited". No LLM fallback. |
| **If no header found** | Treat as ref-list only | Backward compatible with current behavior. |
| **File formats** | DOCX only | PDF parsing too complex for v1. |
| **Preview** | Informational in results | "Found 12 refs + 18 inline citations" shown in header. No blocking confirmation. |
| **Results structure** | Hierarchical | Refs with nested inline citations. Orphans grouped at top. |
| **Orphan display** | Warning box at top | Critical errors shown prominently. |
| **Context shown** | Citation only | No surrounding sentence. Keep it compact. |
| **Free tier limit** | 5 reference entries | Each with all its inline matches. Inline is "bonus value". |
| **LLM calls** | Two parallel | Ref-list validation (existing) + inline validation (new). |
| **Inline batching** | 10 per batch, sequential | Simpler than parallel. Optimize later if needed. |
| **Error types v1** | Matching + basic format | Author/year match, missing refs, et al. usage, basic punctuation. Not placement. |
| **Styles** | APA + MLA | Match current ref-list validator support. |
| **Max citations** | 100 limit | Hard limit. Reject documents with more. |
| **Parse failure** | Error + suggest paste | "Could not read file. Try pasting your text instead." |
| **Partial failure** | Show ref results + warning | If inline fails, show refs with "Inline check failed" message. |
| **Feature flag** | None | Ship directly, no gradual rollout. |

---

## 3. User Experience Flow

### 3.1 Input Flow

```
User arrives at site
    │
    ├── Option A: Paste content
    │   └── Paste into existing editor (body + refs, or refs only)
    │
    └── Option B: Upload DOCX
        └── Click upload area → select .docx file
        └── File sent to backend → parsed → returned as HTML
        └── HTML inserted into editor (user can review)
    │
    ▼
User clicks "Check My Citations"
    │
    ▼
Backend auto-detects content type:
    ├── If no "References" header → treat as ref-list only (current behavior)
    └── If "References" header found → split body/refs → validate both
```

### 3.2 Results Display

```
┌─────────────────────────────────────────────────────────────┐
│ Validation Results                                          │
│ Found 18 refs + 40 inline citations • 15 perfect • 3 errors │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ⚠️ 2 Citations Missing from References                      │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ • (Brown, 2021) - cited 1×                              │ │
│ │ • (Wilson, 2018) - cited 2×                             │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─ Reference Entry ─────────────────────────────────────────┐
│ │ 1. Smith, J. (2019). Title of article. Journal, 1(2).    │
│ │    [source_type: Journal Article]                         │
│ │    ✓ Perfect                                              │
│ │                                                           │
│ │    📍 Cited 3× in document                                │
│ │    • (Smith, 2019) ✓                                      │
│ │    • (Smith, 2019) ✓                                      │
│ │    • (Smith, 2019) ✓                                      │
│ └───────────────────────────────────────────────────────────┘
│                                                             │
│ ┌─ Reference Entry ─────────────────────────────────────────┐
│ │ 2. Jones, K. (2020). Another article. Publisher.          │
│ │    [source_type: Book]                                    │
│ │    ✗ 1 issue                                              │
│ │                                                           │
│ │    [Corrected Citation Card]                              │
│ │    Issues Found (1): Missing DOI                          │
│ │                                                           │
│ │    📍 Cited 2× in document                                │
│ │    • (Jones, 2020) ✓                                      │
│ │    • (Jones, 2019) ⚠️ year mismatch                       │
│ │      → Should be: (Jones, 2020)                           │
│ └───────────────────────────────────────────────────────────┘
│                                                             │
│ [... more reference entries ...]                            │
│                                                             │
│ ┌─ LOCKED: Upgrade to see all ──────────────────────────────┐
│ │ 13 more references with 22 inline citations               │
│ │ [Upgrade Now]                                             │
│ └───────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────┘
```

### 3.3 MLA Ambiguity Handling

When an MLA inline citation like `(Smith 15)` matches multiple references:

```
│ 1. Smith, John. Book One. Publisher, 2019.                  │
│    📍 Cited 1× in document                                  │
│    • (Smith 15) ⚠️ Matches multiple references              │
│      → Add title for clarity: (Smith, Book One 15)          │
│                                                             │
│ 2. Smith, John. Book Two. Publisher, 2020.                  │
│    📍 Cited 1× in document                                  │
│    • (Smith 15) ⚠️ Matches multiple references              │
│      → Add title for clarity: (Smith, Book Two 15)          │
```

The same inline citation appears under BOTH matching references with a notice.

---

## 4. Architecture & Data Flow

### 4.1 Component Diagram

```
User                   Frontend                    Backend
 │                        │                           │
 ├─ Upload DOCX ─────────►│                           │
 │                        ├─ POST /api/validate/async │
 │                        │   (multipart: file)  ────►│
 │                        │                           ├─ mammoth: DOCX→HTML
 │                        │                           ├─ Split: body vs refs
 │                        │                           ├─ Regex: find inline cites
 │                        │                           │
 │                        │                           ├─ PARALLEL:
 │                        │                           │   ├─ Ref-list LLM call
 │                        │                           │   └─ Inline LLM calls (batched)
 │                        │                           │
 │                        │                           ├─ Aggregate results
 │                        │                           ├─ Apply gating (5 refs)
 │                        │◄─ JSON response ──────────┤
 │◄─ Display results ─────┤                           │
```

### 4.2 Request/Response Flow

**Request (multipart/form-data):**
```
POST /api/validate/async
Content-Type: multipart/form-data

file: [binary .docx data]
style: "apa7"
```

OR (for paste):
```
POST /api/validate/async
Content-Type: application/json

{
  "citations": "<html content>",
  "style": "apa7"
}
```

**Response:**
```json
{
  "job_id": "abc-123",
  "status": "completed",
  "validation_type": "full_doc",
  "stats": {
    "ref_count": 18,
    "inline_count": 40,
    "orphan_count": 2,
    "perfect_count": 15,
    "error_count": 3
  },
  "results": [
    {
      "citation_number": 1,
      "original": "Smith, J. (2019). Title. Journal, 1(2).",
      "source_type": "Journal Article",
      "errors": [],
      "corrected_citation": null,
      "inline_citations": [
        {
          "id": "c1",
          "citation_text": "(Smith, 2019)",
          "match_status": "matched",
          "format_errors": []
        },
        {
          "id": "c5",
          "citation_text": "(Smith, 2019)",
          "match_status": "matched",
          "format_errors": []
        }
      ]
    },
    {
      "citation_number": 2,
      "original": "Jones, K. (2020). Another. Publisher.",
      "source_type": "Book",
      "errors": [{"component": "DOI", "problem": "Missing", "correction": "Add DOI"}],
      "corrected_citation": "Jones, K. (2020). Another. Publisher. https://doi.org/...",
      "inline_citations": [
        {
          "id": "c2",
          "citation_text": "(Jones, 2020)",
          "match_status": "matched",
          "format_errors": []
        },
        {
          "id": "c3",
          "citation_text": "(Jones, 2019)",
          "match_status": "mismatch",
          "mismatch_reason": "Year mismatch: inline says 2019, reference says 2020",
          "suggested_correction": "(Jones, 2020)",
          "format_errors": []
        }
      ]
    }
  ],
  "orphan_citations": [
    {
      "id": "c10",
      "citation_text": "(Brown, 2021)",
      "match_status": "not_found",
      "citation_count": 1
    }
  ],
  "is_gated": true,
  "refs_shown": 5,
  "refs_remaining": 13
}
```

---

## 5. Backend Implementation

### 5.1 New Files to Create

#### `backend/parsing.py`
Document parsing and analysis utilities.

```python
"""
Document parsing utilities for inline citation validation.

This module handles:
1. DOCX → HTML conversion using mammoth
2. Section splitting (body vs reference list)
3. Inline citation detection using regex
"""

import re
from typing import Tuple, List, Dict, Optional
import mammoth

# Headers that indicate start of reference list
REFERENCE_HEADERS = [
    "references",
    "reference list",
    "bibliography",
    "works cited",
    "literature cited",
    "sources",
    "sources cited",
    "references cited"
]

def convert_docx_to_html(file_bytes: bytes) -> str:
    """
    Convert DOCX file to HTML preserving formatting.

    Preserves <em> and <strong> tags which are semantic requirements
    for citation styles (italics for titles, etc.)

    Args:
        file_bytes: Raw bytes of the .docx file

    Returns:
        HTML string

    Raises:
        ValueError: If file cannot be parsed
    """
    try:
        result = mammoth.convert_to_html(io.BytesIO(file_bytes))
        return result.value
    except Exception as e:
        raise ValueError(f"Could not parse DOCX file: {str(e)}")


def split_document(html: str) -> Tuple[str, str, bool]:
    """
    Split document into body text and reference list.

    Uses heuristic: find last occurrence of reference header in
    <h1>, <h2>, <h3>, or <strong> tags.

    Args:
        html: Full document HTML

    Returns:
        Tuple of (body_html, refs_html, found_header)
        If no header found, body_html is empty and refs_html is full content.
    """
    # Pattern matches headers containing reference keywords
    # Case insensitive, matches h1-h3 or strong tags
    pattern = r'<(h[1-3]|strong)[^>]*>([^<]*(?:' + '|'.join(REFERENCE_HEADERS) + r')[^<]*)<\/\1>'

    matches = list(re.finditer(pattern, html, re.IGNORECASE))

    if not matches:
        # No header found - treat entire content as reference list (backward compat)
        return "", html, False

    # Use last match (refs typically at end)
    last_match = matches[-1]
    split_point = last_match.start()

    body_html = html[:split_point]
    refs_html = html[split_point:]

    return body_html, refs_html, True


def scan_inline_citations(body_html: str, style: str) -> List[Dict]:
    """
    Scan body text for inline citation candidates using regex.

    Uses permissive patterns - false positives are OK (LLM will reject),
    but false negatives are bad.

    Args:
        body_html: Body text HTML (without reference list)
        style: Citation style ("apa7" or "mla9")

    Returns:
        List of dicts with {id, text, position}
    """
    # Strip HTML tags for regex scanning
    text = re.sub(r'<[^>]+>', ' ', body_html)

    citations = []

    # APA pattern: (Author, Year) with variants
    # Matches: (Smith, 2019), (Smith & Jones, 2019), (Smith et al., 2019)
    apa_pattern = r'\([A-Za-z][A-Za-z\s&.,]+\d{4}[a-z]?\)'

    # MLA pattern: (Author Page)
    # Matches: (Smith 12), (Smith 42-45), (Smith and Jones 12)
    mla_pattern = r'\([A-Za-z][A-Za-z\s]+\d+(?:-\d+)?\)'

    # Use appropriate pattern based on style
    if style == "mla9":
        pattern = mla_pattern
    else:  # Default to APA
        pattern = apa_pattern

    for i, match in enumerate(re.finditer(pattern, text)):
        citations.append({
            "id": f"c{i+1}",
            "text": match.group(),
            "position": match.start()
        })

    return citations
```

#### `backend/inline_validator.py`
Inline citation validation logic.

```python
"""
Inline citation validation against reference list.

This module handles:
1. Batching inline citations for LLM calls
2. Parsing LLM responses
3. Matching inline citations to reference entries
4. Identifying orphans and ambiguous matches
"""

from typing import List, Dict, Any, Optional
import json

BATCH_SIZE = 10  # Citations per LLM call
MAX_CITATIONS = 100  # Hard limit


async def validate_inline_citations(
    inline_citations: List[Dict],
    reference_list: List[Dict],
    style: str,
    provider
) -> Dict[str, Any]:
    """
    Validate inline citations against reference list.

    Args:
        inline_citations: List of {id, text} from regex scan
        reference_list: List of {index, text} reference entries
        style: Citation style
        provider: LLM provider instance

    Returns:
        Dict with results, orphans, stats
    """
    if len(inline_citations) > MAX_CITATIONS:
        raise ValueError(f"Document has {len(inline_citations)} citations. Maximum is {MAX_CITATIONS}.")

    # Batch citations
    batches = [
        inline_citations[i:i+BATCH_SIZE]
        for i in range(0, len(inline_citations), BATCH_SIZE)
    ]

    all_results = []

    # Process sequentially (parallel deferred to v1.1)
    for batch in batches:
        batch_results = await _validate_batch(batch, reference_list, style, provider)
        all_results.extend(batch_results)

    # Organize results by reference
    results_by_ref = _organize_by_reference(all_results, reference_list)

    # Extract orphans
    orphans = [r for r in all_results if r["match_status"] == "not_found"]

    return {
        "results_by_ref": results_by_ref,
        "orphans": orphans,
        "total_found": len(inline_citations),
        "total_validated": len(all_results)
    }


async def _validate_batch(
    citations: List[Dict],
    reference_list: List[Dict],
    style: str,
    provider
) -> List[Dict]:
    """Validate a single batch of citations."""
    prompt = _build_inline_prompt(citations, reference_list, style)
    response = await provider.call_llm(prompt)
    return _parse_inline_response(response)


def _organize_by_reference(
    results: List[Dict],
    reference_list: List[Dict]
) -> Dict[int, List[Dict]]:
    """Group inline citation results by their matched reference index."""
    by_ref = {i: [] for i in range(len(reference_list))}

    for result in results:
        if result["matched_ref_index"] is not None:
            by_ref[result["matched_ref_index"]].append(result)
        # Handle ambiguous - add to all matched refs
        if result.get("matched_ref_indices"):
            for idx in result["matched_ref_indices"]:
                if result not in by_ref[idx]:
                    by_ref[idx].append(result)

    return by_ref
```

#### `backend/prompts/validator_prompt_inline_apa.txt`
```
You are an expert citation validator for APA 7th Edition.

I will provide a Reference List and a set of Inline Citations found in a document.
For each inline citation, determine if it correctly matches a reference.

## Reference List
{reference_list}

## Inline Citations to Validate
{inline_citations}

## Your Task

For each inline citation, return a JSON object with:
- `id`: The citation ID from input
- `citation_text`: The inline citation text
- `match_status`: One of "matched", "mismatch", "not_found", "ambiguous"
- `matched_ref_index`: Index of matching reference (0-based), or null
- `matched_ref_indices`: Array of indices if ambiguous (multiple matches)
- `mismatch_reason`: If mismatch, explain why (e.g., "Year mismatch: inline says 2019, reference says 2020")
- `format_errors`: Array of formatting issues with the inline citation itself
- `suggested_correction`: Corrected inline citation if errors exist

## APA Inline Citation Rules to Check
- Author names match reference exactly
- Year matches reference exactly
- Use "&" between authors in parenthetical, "and" in narrative
- "et al." used correctly (3+ authors)
- Page numbers use "p." or "pp." for direct quotes

Return a JSON array of results.
```

#### `backend/prompts/validator_prompt_inline_mla.txt`
```
You are an expert citation validator for MLA 9th Edition.

I will provide a Works Cited list and a set of Inline Citations found in a document.
For each inline citation, determine if it correctly matches a Works Cited entry.

## Works Cited
{reference_list}

## Inline Citations to Validate
{inline_citations}

## Your Task

For each inline citation, return a JSON object with:
- `id`: The citation ID from input
- `citation_text`: The inline citation text
- `match_status`: One of "matched", "mismatch", "not_found", "ambiguous"
- `matched_ref_index`: Index of matching reference (0-based), or null
- `matched_ref_indices`: Array of indices if ambiguous (same author, multiple works)
- `mismatch_reason`: If mismatch, explain why (e.g., "Author spelling: inline has 'Smyth', reference has 'Smith'")
- `format_errors`: Array of formatting issues with the inline citation itself
- `suggested_correction`: Corrected inline citation if errors exist

## MLA Inline Citation Rules to Check
- Author name matches Works Cited exactly
- Page numbers have no "p." prefix (just the number)
- Multiple works by same author require title for disambiguation
- Use "and" between authors (never "&")

## Ambiguity Detection
If an author has multiple works in the Works Cited, mark as "ambiguous" unless:
- The inline citation includes a title to disambiguate
- There is only one work by that author

Return a JSON array of results.
```

### 5.2 Files to Modify

#### `backend/app.py`
Key changes:
1. Accept file upload in `/api/validate/async`
2. Call parsing and inline validation
3. Return combined results

```python
# Add to imports
from parsing import convert_docx_to_html, split_document, scan_inline_citations
from inline_validator import validate_inline_citations

# Update ValidationRequest (around line 506)
class ValidationRequest(BaseModel):
    citations: Optional[str] = None  # For paste
    style: str = DEFAULT_STYLE

# Add new endpoint for file upload (or modify existing)
@app.post("/api/validate/async")
async def create_validation_job(
    request: Request,
    file: Optional[UploadFile] = File(None),
    citations: Optional[str] = Form(None),
    style: str = Form(DEFAULT_STYLE)
):
    """
    Create async validation job.

    Accepts either:
    - file: DOCX upload (multipart/form-data)
    - citations: HTML string (JSON or form data)
    """
    # Handle file upload
    if file:
        if not file.filename.endswith('.docx'):
            raise HTTPException(400, "Only .docx files supported")
        try:
            content = await file.read()
            html = convert_docx_to_html(content)
        except ValueError as e:
            raise HTTPException(400, f"Could not parse file: {e}. Try pasting your text instead.")
    elif citations:
        html = citations
    else:
        raise HTTPException(400, "Provide either file or citations")

    # Create job and process...
    # (rest of existing logic, extended for inline)


async def process_validation_job(job_id: str, html: str, style: str, ...):
    """Extended to handle inline validation."""

    # Split document
    body_html, refs_html, has_header = split_document(html)

    # Determine validation type
    if has_header and body_html:
        validation_type = "full_doc"
        inline_citations = scan_inline_citations(body_html, style)
    else:
        validation_type = "ref_only"
        inline_citations = []

    # Log validation type
    logger.info(f"VALIDATION_TYPE: job_id={job_id} type={validation_type}")

    # Run validations in parallel
    ref_task = validate_reference_list(refs_html, style, provider)

    inline_results = None
    if inline_citations:
        try:
            inline_task = validate_inline_citations(inline_citations, ref_entries, style, provider)
            ref_results, inline_results = await asyncio.gather(ref_task, inline_task)
        except Exception as e:
            logger.error(f"Job {job_id}: Inline validation failed: {e}")
            ref_results = await ref_task
            inline_results = {"error": str(e)}
    else:
        ref_results = await ref_task

    # Merge results
    # ... (combine ref formatting results with inline match results)

    # Log inline stats
    if inline_results and "error" not in inline_results:
        inline_count = inline_results["total_found"]
        orphan_count = len(inline_results["orphans"])
        logger.info(f"Inline validation stats: {inline_count} citations_found, {inline_count - orphan_count} valid, {orphan_count} orphan")
```

#### `backend/requirements.txt`
Add:
```
mammoth>=0.3.0
```

#### `backend/prompt_manager.py`
Add inline prompt loading:
```python
INLINE_PROMPTS = {
    "apa7": "validator_prompt_inline_apa.txt",
    "mla9": "validator_prompt_inline_mla.txt"
}

def get_inline_prompt(style: str) -> str:
    """Load inline validation prompt for style."""
    filename = INLINE_PROMPTS.get(style, INLINE_PROMPTS["apa7"])
    return _load_prompt_file(filename)
```

#### `backend/styles.py`
Add inline prompt paths to style config:
```python
STYLE_CONFIG = {
    "apa7": {
        "name": "APA 7th Edition",
        "prompt_file": "validator_prompt_v3_no_hallucination.txt",
        "inline_prompt_file": "validator_prompt_inline_apa.txt"  # NEW
    },
    "mla9": {
        "name": "MLA 9th Edition",
        "prompt_file": "validator_prompt_mla9_v1.1.txt",
        "inline_prompt_file": "validator_prompt_inline_mla.txt"  # NEW
    }
}
```

#### `backend/citation_logger.py`
Add inline stats logging:
```python
def log_validation_complete(
    job_id: str,
    citation_count: int,
    duration: float,
    validation_type: str = "ref_only",  # NEW
    inline_citation_count: int = 0,      # NEW
    orphan_count: int = 0                # NEW
):
    """Log validation completion with inline stats."""
    logger.info(
        f"Job {job_id}: Completed in {duration}s. "
        f"Type={validation_type}, Refs={citation_count}, "
        f"Inline={inline_citation_count}, Orphans={orphan_count}"
    )
```

---

## 6. Frontend Implementation

### 6.1 Files to Modify

#### `App.jsx`
Add state for inline results:
```javascript
// New state variables
const [inlineResults, setInlineResults] = useState(null)
const [orphanCitations, setOrphanCitations] = useState([])
const [validationType, setValidationType] = useState('ref_only')

// Update result handling
const handleResults = (data) => {
  setResults(data.results)
  setInlineResults(data.inline_results || null)
  setOrphanCitations(data.orphan_citations || [])
  setValidationType(data.validation_type)
  // ... existing logic
}
```

#### `ValidationTable.jsx`
Add hierarchical display with inline citations nested under refs:
```javascript
// Add InlineCitationList rendering inside each row
{result.inline_citations && result.inline_citations.length > 0 && (
  <InlineCitationList
    citations={result.inline_citations}
    refIndex={result.citation_number}
  />
)}
```

#### `UploadArea.jsx`
Connect to real upload:
```javascript
const handleFileSelect = async (file) => {
  if (!file.name.endsWith('.docx')) {
    setError('Only .docx files supported')
    return
  }

  // Create FormData and submit
  const formData = new FormData()
  formData.append('file', file)
  formData.append('style', selectedStyle)

  try {
    const response = await fetch('/api/validate/async', {
      method: 'POST',
      body: formData
    })
    // Handle response...
  } catch (e) {
    setError('Could not read file. Try pasting your text instead.')
  }
}
```

Update text to indicate DOCX only.

#### `useFileProcessing.js`
Replace stub with real API call (or remove if logic moved to UploadArea).

#### `ValidationLoadingState.jsx`
Update status messages:
```javascript
const statusMessages = [
  "Scanning document...",
  "Finding citations in text...",
  "Checking for mismatches...",
  "Verifying references...",
  "Cross-referencing style rules..."
]
```

#### `CorrectedCitationCard.jsx`
Handle inline citation corrections in addition to ref corrections.

#### `mockData.js`
Add mock inline results for testing:
```javascript
export const mockInlineResults = [
  {
    id: "c1",
    citation_text: "(Smith, 2019)",
    match_status: "matched",
    matched_ref_index: 0
  },
  // ...
]
```

### 6.2 New Files to Create

#### `OrphanWarningBox.jsx`
```javascript
function OrphanWarningBox({ orphans }) {
  if (!orphans || orphans.length === 0) return null

  return (
    <div className="orphan-warning-box">
      <div className="orphan-header">
        <span className="warning-icon">⚠️</span>
        <strong>{orphans.length} Citation{orphans.length > 1 ? 's' : ''} Missing from References</strong>
      </div>
      <ul className="orphan-list">
        {orphans.map(orphan => (
          <li key={orphan.id}>
            <code>{orphan.citation_text}</code>
            <span className="orphan-count">cited {orphan.citation_count}×</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
```

#### `OrphanWarningBox.css`
```css
.orphan-warning-box {
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.orphan-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.orphan-list {
  margin: 0;
  padding-left: 24px;
}

.orphan-list li {
  margin: 4px 0;
}

.orphan-list code {
  background: #fff;
  padding: 2px 6px;
  border-radius: 4px;
}
```

#### `InlineCitationList.jsx`
```javascript
function InlineCitationList({ citations, refIndex }) {
  if (!citations || citations.length === 0) return null

  return (
    <div className="inline-citation-list">
      <div className="inline-header">
        📍 Cited {citations.length}× in document
      </div>
      <ul className="inline-items">
        {citations.map(cite => (
          <li key={cite.id} className={`inline-item status-${cite.match_status}`}>
            <code>{cite.citation_text}</code>
            {cite.match_status === 'matched' && <span className="status-icon">✓</span>}
            {cite.match_status === 'mismatch' && (
              <>
                <span className="status-icon">⚠️</span>
                <span className="mismatch-reason">{cite.mismatch_reason}</span>
                {cite.suggested_correction && (
                  <span className="correction">→ {cite.suggested_correction}</span>
                )}
              </>
            )}
            {cite.match_status === 'ambiguous' && (
              <>
                <span className="status-icon">❓</span>
                <span className="ambiguous-note">Matches multiple references</span>
              </>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
```

#### `useInlineCitations.js`
Hook to organize inline data:
```javascript
export function useInlineCitations(results, inlineResults, orphans) {
  return useMemo(() => {
    if (!inlineResults) return { organized: results, hasInline: false }

    // Merge inline citations into their parent refs
    const organized = results.map(ref => ({
      ...ref,
      inline_citations: inlineResults.filter(
        inline => inline.matched_ref_index === ref.citation_number - 1
      )
    }))

    return {
      organized,
      orphans,
      hasInline: true,
      stats: {
        totalInline: inlineResults.length,
        matched: inlineResults.filter(i => i.match_status === 'matched').length,
        mismatched: inlineResults.filter(i => i.match_status === 'mismatch').length,
        orphaned: orphans.length
      }
    }
  }, [results, inlineResults, orphans])
}
```

### 6.3 Files to Delete

#### `ComingSoonModal.jsx`
No longer needed - upload is now functional.

---

## 7. LLM Prompt Development

### 7.1 Golden Set Creation Process

**Target:** 100 test cases per style (APA, MLA), split 50/50 train/holdout.

**Sources for test data:**
1. APA/MLA official style guide sample papers
2. University writing center examples (Purdue OWL, etc.)
3. Open access papers from arXiv, PubMed Central
4. Hand-crafted edge cases

**Test case categories (aim for 10+ each):**

| Category | Example | Expected Result |
|----------|---------|-----------------|
| Perfect match | (Smith, 2019) → Smith, J. (2019) | matched |
| Year mismatch | (Smith, 2019) → Smith, J. (2020) | mismatch + reason |
| Author spelling | (Smyth, 2019) → Smith, J. (2019) | mismatch + reason |
| Missing from refs | (Jones, 2021) → [not in list] | not_found |
| Et al. correct | (Smith et al., 2019) → 3+ authors | matched |
| Et al. wrong | (Smith et al., 2019) → 2 authors | mismatch |
| Multiple citations | (Smith, 2019; Jones, 2020) | check both |
| Narrative style | Smith (2019) said... | matched |
| MLA ambiguous | (Smith 15) → 2 Smith works | ambiguous |
| MLA with title | (Smith, Book 15) | matched to correct work |

### 7.2 Golden Set File Format

**Location:** `Checker_Prompt_Optimization/inline_apa_train.jsonl`

```json
{"inline_citation": "(Smith, 2019)", "ref_list": ["Smith, J. (2019). Title. Journal, 1(2), 10-20.", "Jones, K. (2020). Book. Publisher."], "expected": {"match_status": "matched", "matched_ref_index": 0, "errors": []}}
{"inline_citation": "(Smith, 2020)", "ref_list": ["Smith, J. (2019). Title. Journal, 1(2), 10-20."], "expected": {"match_status": "mismatch", "mismatch_reason": "Year mismatch", "matched_ref_index": 0}}
{"inline_citation": "(Brown, 2021)", "ref_list": ["Smith, J. (2019). Title. Journal."], "expected": {"match_status": "not_found", "matched_ref_index": null}}
```

### 7.3 Test Runner

**Location:** `Checker_Prompt_Optimization/test_inline_prompt.py`

Similar to existing `test_mla9_prompt_batched.py`:
- Load golden set
- Run prompt against test cases
- Calculate accuracy, precision, recall, F1
- Report by error category
- Launch criteria: ≥80% accuracy to ship

---

## 8. Analytics & Dashboard

### 8.1 Log Format

Backend emits these log lines for inline validation:

```
2026-01-03 14:23:45 VALIDATION_TYPE: job_id=abc-123 type=full_doc
2026-01-03 14:23:50 Inline validation stats: 42 citations_found, 38 valid, 4 orphan
```

### 8.2 Dashboard Database Changes

**File:** `dashboard/database.py`

Add columns to `validations` table:
```sql
validation_type TEXT,        -- 'ref_only' or 'full_doc'
inline_citation_count INTEGER,
orphan_count INTEGER
```

### 8.3 Log Parser Changes

**File:** `dashboard/log_parser.py`

Add extraction functions:
```python
def extract_validation_type(log_line: str) -> Optional[Tuple[str, str]]:
    pattern = r'VALIDATION_TYPE: job_id=([a-f0-9-]+) type=(ref_only|full_doc)'
    match = re.search(pattern, log_line)
    if match:
        return match.group(1), match.group(2)
    return None

def extract_inline_validation_stats(log_line: str) -> Optional[Dict[str, int]]:
    pattern = r'Inline validation stats: (\d+) citations_found, (\d+) valid, (\d+) orphan'
    match = re.search(pattern, log_line)
    if match:
        return {
            "inline_citation_count": int(match.group(1)),
            "valid_count": int(match.group(2)),
            "orphan_count": int(match.group(3))
        }
    return None
```

### 8.4 Dashboard API Changes

**File:** `dashboard/api.py`

Add filter parameters:
```python
def get_validations(
    ...
    validation_type: Optional[str] = None,  # NEW
    has_inline: Optional[bool] = None       # NEW
):
```

### 8.5 Frontend Analytics Events

**File:** `frontend/src/utils/analytics.js`

Add:
```javascript
export const trackInlineValidation = (jobId, inlineCitationCount, orphanCount, validationType) => {
  gtag('event', 'inline_validation_completed', {
    job_id: jobId,
    inline_citation_count: inlineCitationCount,
    orphan_count: orphanCount,
    validation_type: validationType
  })
}
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

**Backend:**
| File | Tests |
|------|-------|
| `tests/test_parsing.py` | DOCX conversion, section splitting, regex scanning |
| `tests/test_inline_validator.py` | Batching, matching logic, orphan detection |

**Key test cases:**
- DOCX with all header variations (References, Bibliography, Works Cited)
- DOCX with no header (should treat as ref-only)
- Body with mixed citation styles
- Edge cases: et al., multiple authors, page numbers

### 9.2 E2E Tests

**Critical path tests for deployment:**

| Test | File | Description |
|------|------|-------------|
| Upload DOCX → Results | `e2e-inline-flow.spec.cjs` | Upload test doc, verify inline citations shown |
| Paste Full Doc → Results | `e2e-inline-flow.spec.cjs` | Paste body + refs, verify split detection |
| Orphan Warning | `e2e-inline-flow.spec.cjs` | Submit doc with orphans, verify warning box |
| Free Tier Gating | existing tests | Verify first 5 refs shown with inline matches |
| Parse Error | `e2e-inline-flow.spec.cjs` | Upload bad file, verify error + paste suggestion |

**Test data files:**
| File | Contents |
|------|----------|
| `test_doc_valid.docx` | Valid doc with refs + inline citations |
| `test_doc_orphans.docx` | Doc with citations not in ref list |
| `test_doc_refs_only.docx` | Doc with only reference list (no body) |
| `test_doc_corrupt.docx` | Corrupted file for error handling |

### 9.3 Deployment Pipeline Updates

**File:** `deployment/scripts/run_remote_e2e.sh`

Add inline test to deployment verification:
```bash
# After existing e2e-full-flow.spec.cjs
npm run test:e2e -- tests/e2e/core/e2e-inline-flow.spec.cjs --project=production
```

**File:** `deployment/scripts/verify_data_integrity.py`

Add checks for new columns:
```python
# Verify inline columns exist and are populated
assert 'validation_type' in columns
assert 'inline_citation_count' in columns
```

---

## 10. File-by-File Implementation Scope

### Backend Files

| File | Action | Changes |
|------|--------|---------|
| `requirements.txt` | MODIFY | Add `mammoth>=0.3.0` |
| `app.py` | MODIFY | File upload, inline validation call, response schema |
| `prompt_manager.py` | MODIFY | Load inline prompts |
| `styles.py` | MODIFY | Add inline prompt paths |
| `citation_logger.py` | MODIFY | Log inline stats |
| `parsing.py` | CREATE | DOCX→HTML, section split, regex scan |
| `inline_validator.py` | CREATE | Inline validation logic |
| `prompts/validator_prompt_inline_apa.txt` | CREATE | APA inline prompt |
| `prompts/validator_prompt_inline_mla.txt` | CREATE | MLA inline prompt |
| `tests/test_parsing.py` | CREATE | Unit tests for parsing |
| `tests/test_inline_validator.py` | CREATE | Unit tests for validation |

### Frontend Files

| File | Action | Changes |
|------|--------|---------|
| `App.jsx` | MODIFY | State for inline results, orphans |
| `ValidationTable.jsx` | MODIFY | Hierarchical display with nested inline |
| `ValidationTable.css` | MODIFY | Nested row styles |
| `UploadArea.jsx` | MODIFY | Real DOCX upload |
| `useFileProcessing.js` | MODIFY | Real API call |
| `ValidationLoadingState.jsx` | MODIFY | Update status messages |
| `CorrectedCitationCard.jsx` | MODIFY | Handle inline corrections |
| `mockData.js` | MODIFY | Add mock inline results |
| `OrphanWarningBox.jsx` | CREATE | Warning box component |
| `OrphanWarningBox.css` | CREATE | Warning box styles |
| `InlineCitationList.jsx` | CREATE | Nested inline display |
| `InlineCitationList.css` | CREATE | Inline styles |
| `useInlineCitations.js` | CREATE | Data organization hook |
| `analytics.js` | MODIFY | Add inline tracking events |
| `ComingSoonModal.jsx` | DELETE | No longer needed |

### Dashboard Files

| File | Action | Changes |
|------|--------|---------|
| `log_parser.py` | MODIFY | Extract inline stats |
| `database.py` | MODIFY | Add columns, update insert |
| `api.py` | MODIFY | Add filter parameters |

### Test Files

| File | Action | Purpose |
|------|--------|---------|
| `inline_apa_train.jsonl` | CREATE | APA golden set (50 cases) |
| `inline_apa_holdout.jsonl` | CREATE | APA holdout (50 cases) |
| `inline_mla_train.jsonl` | CREATE | MLA golden set (50 cases) |
| `inline_mla_holdout.jsonl` | CREATE | MLA holdout (50 cases) |
| `test_inline_prompt.py` | CREATE | Prompt test runner |
| `e2e-inline-flow.spec.cjs` | CREATE | E2E tests |
| `test_doc_*.docx` | CREATE | Test documents |

### Deployment Files

| File | Action | Changes |
|------|--------|---------|
| `run_remote_e2e.sh` | MODIFY | Add inline E2E test |
| `verify_data_integrity.py` | MODIFY | Check inline columns |

---

## 11. Implementation Phases

### Phase 1: Backend Core (3-4 days)
1. Add mammoth to requirements
2. Create `parsing.py` with DOCX conversion, section splitting
3. Create `inline_validator.py` with batching logic
4. Unit tests for parsing and validation
5. Update `app.py` to accept file upload

### Phase 2: LLM Prompts (3-4 days)
1. Create golden set (50 train + 50 holdout per style)
2. Draft initial prompts
3. Create test runner
4. Iterate until ≥80% accuracy on train set
5. Validate on holdout set

### Phase 3: Frontend (3-4 days)
1. Update UploadArea for real upload
2. Create OrphanWarningBox component
3. Create InlineCitationList component
4. Update ValidationTable for hierarchical display
5. Update App.jsx state management

### Phase 4: Analytics & Dashboard (1-2 days)
1. Update backend logging
2. Update log parser
3. Add database columns
4. Update dashboard API

### Phase 5: Testing & Polish (2-3 days)
1. E2E tests for critical path
2. Deployment pipeline integration
3. Test with real documents
4. Fix edge cases

### Phase 6: Deploy & Monitor (1 day)
1. Deploy to production
2. Monitor logs for errors
3. Check dashboard metrics
4. Address any issues

**Total estimated time: 13-18 days**

---

## Appendix: LLM Response Schema

**Input to LLM:**
```json
{
  "style": "apa7",
  "reference_list": [
    {"index": 0, "text": "Smith, J. (2019). Title. Journal, 1(2), 10-20."},
    {"index": 1, "text": "Jones, K. (2020). Another title. Publisher."}
  ],
  "inline_citations": [
    {"id": "c1", "text": "(Smith, 2019)"},
    {"id": "c2", "text": "(Jones, 2019)"},
    {"id": "c3", "text": "(Brown, 2021)"}
  ]
}
```

**Expected LLM Response:**
```json
{
  "results": [
    {
      "id": "c1",
      "citation_text": "(Smith, 2019)",
      "match_status": "matched",
      "matched_ref_index": 0,
      "matched_ref_indices": null,
      "mismatch_reason": null,
      "format_errors": [],
      "suggested_correction": null
    },
    {
      "id": "c2",
      "citation_text": "(Jones, 2019)",
      "match_status": "mismatch",
      "matched_ref_index": 1,
      "matched_ref_indices": null,
      "mismatch_reason": "Year mismatch: inline says 2019, reference says 2020",
      "format_errors": [],
      "suggested_correction": "(Jones, 2020)"
    },
    {
      "id": "c3",
      "citation_text": "(Brown, 2021)",
      "match_status": "not_found",
      "matched_ref_index": null,
      "matched_ref_indices": null,
      "mismatch_reason": null,
      "format_errors": [],
      "suggested_correction": null
    }
  ]
}
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Citation ID from input |
| `citation_text` | string | The inline citation text |
| `match_status` | enum | "matched" / "mismatch" / "not_found" / "ambiguous" |
| `matched_ref_index` | int/null | Index into reference_list (0-based) |
| `matched_ref_indices` | int[]/null | Multiple indices for ambiguous matches |
| `mismatch_reason` | string/null | Human-readable explanation |
| `format_errors` | string[] | Formatting issues (punctuation, et al., etc.) |
| `suggested_correction` | string/null | Fixed inline citation |

---

## Appendix: Reference Header Detection

Headers to search for (case-insensitive):
- "References"
- "Reference List"
- "Bibliography"
- "Works Cited"
- "Literature Cited"
- "Sources"
- "Sources Cited"
- "References Cited"

Search in tags: `<h1>`, `<h2>`, `<h3>`, `<strong>`

Algorithm:
1. Find all matches
2. Take LAST match (refs typically at end)
3. Split at that point
4. If no match found, treat entire content as ref-list only
