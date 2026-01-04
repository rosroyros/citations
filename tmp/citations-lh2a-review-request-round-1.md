You are conducting a code review for the Inline Citation Validation epic.

## Issue Context
### Beads Issue ID: citations-lh2a

**Task:** P1.4: Update prompt_manager.py and styles.py

**Description:**
This is the fourth task for Phase 1 (Backend Core) of the Inline Citation Validation epic.

We need to extend the existing prompt management system to load inline validation prompts. The current system already handles ref-list validation prompts; we're adding a parallel set for inline validation.

## Requirements (from issue)
- [x] Add inline prompt path mapping to `prompt_manager.py`
- [x] Add `get_inline_prompt(style: str)` function
- [x] Update `styles.py` STYLE_CONFIG with inline_prompt_file keys
- [x] Ensure fallback behavior matches ref-list (APA as default)

## Implementation Summary

### File: `backend/styles.py`
Added `inline_prompt_file` key to `SUPPORTED_STYLES` for all styles:
- apa7: "validator_prompt_inline_apa.txt"
- mla9: "validator_prompt_inline_mla.txt"
- chicago17: "validator_prompt_inline_chicago17.txt"

### File: `backend/prompt_manager.py`
Added `load_inline_prompt(style)` method to `PromptManager` class:
- Loads inline prompt from style config
- Falls back to APA if style doesn't have inline_prompt_file defined
- Follows same pattern as existing `load_prompt()` method

## Code Changes

### backend/styles.py
```python
SUPPORTED_STYLES: Dict[str, Dict[str, str]] = {
    "apa7": {
        "label": "APA 7th Edition",
        "prompt_file": "validator_prompt_v3_no_hallucination.txt",
        "inline_prompt_file": "validator_prompt_inline_apa.txt",  # NEW
        "success_message": "No APA 7 formatting errors detected"
    },
    "mla9": {
        "label": "MLA 9th Edition",
        "prompt_file": "validator_prompt_mla9_v1.1.txt",
        "inline_prompt_file": "validator_prompt_inline_mla.txt",  # NEW
        "success_message": "No MLA 9 formatting errors detected"
    },
    "chicago17": {
        "label": "Chicago 17th Edition",
        "prompt_file": "validator_prompt_chicago17_v1.2.txt",
        "inline_prompt_file": "validator_prompt_inline_chicago17.txt",  # NEW
        "success_message": "No Chicago 17 formatting errors detected"
    }
}
```

### backend/prompt_manager.py
```python
def load_inline_prompt(self, style: StyleType = DEFAULT_STYLE) -> str:
    """
    Load the inline citation validation prompt for a given citation style.

    Args:
        style: Citation style to load inline prompt for (default: apa7)

    Returns:
        str: The inline prompt template text

    Raises:
        FileNotFoundError: If inline prompt file doesn't exist
    """
    config = get_style_config(style)
    prompt_filename = config.get("inline_prompt_file")

    # Fall back to APA if inline_prompt_file not defined
    if not prompt_filename:
        logger.warning(f"No inline_prompt_file for style '{style}', falling back to APA")
        config = get_style_config(DEFAULT_STYLE)
        prompt_filename = config.get("inline_prompt_file")

    prompt_path = self._prompts_dir / prompt_filename

    logger.debug(f"Loading inline prompt from: {prompt_path}")

    if not prompt_path.exists():
        logger.error(f"Inline prompt file not found: {prompt_path}")
        raise FileNotFoundError(f"Inline prompt file not found: {prompt_path}")

    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt = f.read()

    logger.info(f"Loaded inline validation prompt: {prompt_path.name} ({len(prompt)} characters)")
    return prompt
```

## Verification Results
All tests pass:
- ✓ inline_prompt_file in SUPPORTED_STYLES for apa7, mla9, chicago17
- ✓ APA inline prompt loads correctly (3692 chars)
- ✓ MLA inline prompt loads correctly (6531 chars)
- ✓ Default parameter (apa7 fallback) works

## Review Checklist
Please review against:
1. **Design alignment** - Does this match the requirements from P1.4?
2. **Code quality** - Is the implementation clean and follows existing patterns?
3. **Error handling** - Are edge cases handled properly?
4. **Testing** - Are the verification tests sufficient?
5. **Dependencies** - Is this ready for P1.3 (inline_validator.py) to use?

## Specific Questions for Reviewer
1. Is the `load_inline_prompt` method name consistent with existing conventions (vs `get_inline_prompt` in requirements)?
2. Should we validate that the inline prompt files exist at startup or is lazy loading acceptable?
3. Is the fallback behavior correct (APA for missing inline_prompt_file)?
4. Any concerns about adding chicago17 inline_prompt_file when chicago17 may not be a priority?

