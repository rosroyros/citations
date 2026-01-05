Now let me review the implementation against the requirements:

## Code Review for citations-r21l: P1.3 inline_validator.py

### 1. Critical

**None identified.**

### 2. Important

**1. Missing citation_text in parse placeholder results** (backend/inline_validator.py:217)
```python
"suggested_correction": None
} for citation in batch]
```
The fallback results in `_parse_inline_response` have `citation_text` set correctly, but the error fallback in `_validate_batch` (line ~153) uses `citation["text"]` which is correct. However, looking more carefully - both are correct actually. The field mapping is `text` → `citation_text`. This is fine.

**2. Potential duplicate in ambiguous citations** (backend/inline_validator.py:280-289)
```python
if idx in by_ref:
    # Check if already added to avoid duplicates
    if not any(r["id"] == result["id"] for r in by_ref[idx]):
        by_ref[idx].append(result)
```
The duplicate check uses O(n) lookup per insertion. For small datasets this is fine, but could be optimized with a set. However, this is acceptable for v1.0 with 100 citation limit.

### 3. Minor

**1. Unused import** (backend/inline_validator.py:5)
```python
import asyncio
```
The `asyncio` module is imported but never used. All async functions use `async def` syntax but don't call asyncio functions directly.

**2. Type hint consistency** (backend/inline_validator.py:17)
```python
style: StyleType = DEFAULT_STYLE,
```
`StyleType` is imported but `DEFAULT_STYLE` is used as default. Should verify both are from `styles` module. Read styles.py to confirm.

**3. Inconsistent error message format** (backend/inline_validator.py:29)
```python
raise ValueError(f"Document has {total_inline} inline citations. Maximum allowed is {MAX_CITATIONS}.")
```
Could include both values clearly, but current format is acceptable.

**4. Redundant comment** (backend/inline_validator.py:48)
```python
# Process citations in batches sequentially (parallel deferred to v1.1)
```
This comment repeats what's already clear from context. Minor style issue.

### 4. Strengths

1. **Excellent test coverage** - 19 tests covering all major paths including edge cases like:
   - Empty input
   - MAX_CITATIONS limit enforcement  
   - Single and multiple batching
   - Multiple JSON parsing formats (code block, raw, array)
   - Ambiguous citation handling (MLA case)
   - Orphan extraction logic
   - Default field initialization

2. **Robust JSON parsing** - `_parse_inline_response` tries multiple patterns before failing:
   - ```json code blocks
   - Direct arrays
   - Raw objects
   - Entire response fallback

3. **Graceful degradation** - Both `_validate_batch` and `_parse_inline_response` return structured placeholder results on failure instead of crashing.

4. **Clear logging** - Appropriate use of info/debug/error levels throughout.

5. **Well-structured code** - Clear separation of concerns with focused helper functions.

6. **Requirements met** - All requirements from design doc addressed:
   - BATCH_SIZE = 10 ✓
   - MAX_CITATIONS = 100 with ValueError ✓
   - Sequential batch processing ✓
   - Integration with prompt_manager.load_inline_prompt() ✓
   - Integration with provider _call_new_api/_call_legacy_api ✓
   - Orphan detection ✓
   - Ambiguous match handling for MLA ✓

7. **Good documentation** - Clear docstrings with Args/Returns/Raises sections.

## Summary

**Status: APPROVED with minor recommendations**

The implementation is solid, well-tested, and meets all requirements. The unused `asyncio` import should be removed for cleanliness, but this is trivial.

**Recommended action before merge:**
- Remove unused `import asyncio` (inline_validator.py:5)

**No blockers found.** The code is production-ready.
