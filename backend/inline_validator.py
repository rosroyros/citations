"""
Inline citation validation module.

This module validates inline citations against a reference list using LLM calls.
It handles batching, result organization, orphan detection, and ambiguous matches.

Key functions:
- validate_inline_citations: Main entry point for inline validation
- _validate_batch: Validate a single batch of citations
- _organize_by_reference: Group results by reference index
- _extract_orphans: Extract citations with no matching reference
"""
import json
import re
from typing import List, Dict, Any
from logger import setup_logger
from styles import StyleType, DEFAULT_STYLE

logger = setup_logger("inline_validator")

# Constants
BATCH_SIZE = 10  # Citations per LLM call
MAX_CITATIONS = 100  # Hard limit - reject documents with more


async def validate_inline_citations(
    inline_citations: List[Dict],
    reference_list: List[Dict],
    style: StyleType = DEFAULT_STYLE,
    provider=None
) -> Dict[str, Any]:
    """
    Validate inline citations against reference list.

    Args:
        inline_citations: List of {id, text} from regex scan
        reference_list: List of {index, text} reference entries
        style: Citation style ("apa7" or "mla9")
        provider: LLM provider instance with async call capability

    Returns:
        Dict with:
        - results_by_ref: Dict[int, List[Dict]] - citations grouped by ref index
        - orphans: List[Dict] - citations with no matching ref
        - total_found: int
        - total_validated: int

    Raises:
        ValueError: If document has >100 citations
    """
    total_inline = len(inline_citations)

    # Enforce hard limit
    if total_inline > MAX_CITATIONS:
        raise ValueError(f"Document has {total_inline} inline citations. Maximum allowed is {MAX_CITATIONS}.")

    if total_inline == 0:
        logger.info("No inline citations to validate")
        return {
            "results_by_ref": {},
            "orphans": [],
            "total_found": 0,
            "total_validated": 0
        }

    logger.info(f"Starting inline validation: {total_inline} citations against {len(reference_list)} references (style={style})")

    # Process citations in batches sequentially (parallel deferred to v1.1)
    all_results = []
    batches = [
        inline_citations[i:i + BATCH_SIZE]
        for i in range(0, len(inline_citations), BATCH_SIZE)
    ]

    logger.info(f"Processing {len(batches)} batches of up to {BATCH_SIZE} citations each")

    for batch_idx, batch in enumerate(batches, start=1):
        logger.debug(f"Processing batch {batch_idx}/{len(batches)} ({len(batch)} citations)")
        batch_results = await _validate_batch(batch, reference_list, style, provider)
        all_results.extend(batch_results)

    # Organize results by reference
    results_by_ref = _organize_by_reference(all_results, reference_list)

    # Extract orphans
    orphans = _extract_orphans(all_results)

    result = {
        "results_by_ref": results_by_ref,
        "orphans": orphans,
        "total_found": total_inline,
        "total_validated": len(all_results)
    }

    logger.info(f"Inline validation complete: {len(orphans)} orphans, {sum(len(v) for v in results_by_ref.values())} matched")

    return result


async def _validate_batch(
    batch: List[Dict],
    reference_list: List[Dict],
    style: StyleType,
    provider
) -> List[Dict]:
    """
    Validate a single batch of inline citations.

    Args:
        batch: List of {id, text} citation dicts
        reference_list: List of {index, text} reference entries
        style: Citation style
        provider: LLM provider instance

    Returns:
        List of validation result dicts
    """
    # Import here to avoid circular dependency
    from prompt_manager import PromptManager

    prompt_manager = PromptManager()

    # Build the prompt
    prompt_template = prompt_manager.load_inline_prompt(style)

    # Format reference list
    ref_list_text = _format_reference_list(reference_list)

    # Format inline citations
    inline_text = _format_inline_citations(batch)

    # Build full prompt
    full_prompt = prompt_template.replace("{reference_list}", ref_list_text)
    full_prompt = full_prompt.replace("{inline_citations}", inline_text)

    logger.debug(f"Built inline validation prompt ({len(full_prompt)} chars)")

    # Call LLM
    try:
        response = await _call_llm(full_prompt, provider)
        results = _parse_inline_response(response, batch)

        logger.debug(f"Parsed {len(results)} results from batch of {len(batch)}")

        return results

    except Exception as e:
        logger.error(f"Failed to validate inline batch: {str(e)}", exc_info=True)

        # Return placeholder results on failure
        return [{
            "id": citation["id"],
            "citation_text": citation["text"],
            "match_status": "not_found",
            "matched_ref_index": None,
            "matched_ref_indices": None,
            "mismatch_reason": f"Validation error: {str(e)}",
            "format_errors": [],
            "suggested_correction": None
        } for citation in batch]


async def _call_llm(prompt: str, provider) -> str:
    """
    Call the LLM with the given prompt.

    Args:
        prompt: Full prompt string
        provider: LLM provider instance

    Returns:
        Response text from LLM

    Raises:
        Exception: If LLM call fails
    """
    # Use the provider's internal _call_new_api or _call_legacy_api methods
    # These are async methods in gemini_provider
    if hasattr(provider, '_call_new_api') and provider.use_new_api:
        return await provider._call_new_api(prompt)
    elif hasattr(provider, '_call_legacy_api'):
        return await provider._call_legacy_api(prompt)
    else:
        # Fallback: try to use generate_completion (sync method)
        result = provider.generate_completion(prompt)
        if result is None:
            raise Exception("LLM returned empty response")
        return result


def _parse_inline_response(response: str, batch: List[Dict]) -> List[Dict]:
    """
    Parse LLM response into structured results.

    Args:
        response: Raw LLM response text
        batch: Original batch of citations for validation

    Returns:
        List of parsed result dicts
    """
    # Try to extract JSON from response
    # Look for ```json ... ``` blocks or direct JSON
    json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
    if json_match:
        json_text = json_match.group(1)
    else:
        # Try to find JSON array first [...]
        array_match = re.search(r'\[.*\]', response, re.DOTALL)
        if array_match:
            json_text = array_match.group(0)
        else:
            # Try to find raw JSON object
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
            else:
                # Fallback: entire response might be JSON
                json_text = response.strip()

    try:
        parsed = json.loads(json_text)

        # Handle both {results: [...]} and direct array format
        if isinstance(parsed, dict) and "results" in parsed:
            results = parsed["results"]
        elif isinstance(parsed, list):
            results = parsed
        else:
            raise ValueError(f"Unexpected JSON structure: {type(parsed)}")

        # Validate each result has required fields
        for result in results:
            if "id" not in result:
                raise ValueError("Result missing 'id' field")
            # Ensure all required fields are present
            result.setdefault("match_status", "not_found")
            result.setdefault("matched_ref_index", None)
            result.setdefault("matched_ref_indices", None)
            result.setdefault("mismatch_reason", None)
            result.setdefault("format_errors", [])
            result.setdefault("suggested_correction", None)

        logger.debug(f"Parsed {len(results)} results from LLM response")
        return results

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from LLM response: {str(e)}")
        logger.debug(f"Response text: {response[:500]}...")

        # Return placeholder results on parse error
        return [{
            "id": citation["id"],
            "citation_text": citation["text"],
            "match_status": "not_found",
            "matched_ref_index": None,
            "matched_ref_indices": None,
            "mismatch_reason": f"Parse error: Could not interpret LLM response",
            "format_errors": [],
            "suggested_correction": None
        } for citation in batch]


def _format_reference_list(reference_list: List[Dict]) -> str:
    """
    Format reference list for prompt input.

    Args:
        reference_list: List of {index, text} dicts

    Returns:
        Formatted string with numbered references
    """
    lines = []
    for ref in reference_list:
        index = ref.get("index", 0)
        text = ref.get("text", "")
        lines.append(f"{index}. {text}")

    return "\n".join(lines)


def _format_inline_citations(batch: List[Dict]) -> str:
    """
    Format inline citations for prompt input.

    Args:
        batch: List of {id, text} citation dicts

    Returns:
        Formatted string with citation IDs and text
    """
    lines = []
    for citation in batch:
        cit_id = citation.get("id", "")
        text = citation.get("text", "")
        lines.append(f"{cit_id}: {text}")

    return "\n".join(lines)


def _organize_by_reference(results: List[Dict], reference_list: List[Dict]) -> Dict[int, List[Dict]]:
    """
    Group inline citation results by their matched reference index.

    Args:
        results: List of validation result dicts
        reference_list: List of reference entries (for initialization)

    Returns:
        Dict mapping ref_index to list of citation results
    """
    # Initialize empty dict for all reference indices
    by_ref = {ref.get("index", i): [] for i, ref in enumerate(reference_list)}

    for result in results:
        matched_index = result.get("matched_ref_index")
        matched_indices = result.get("matched_ref_indices")

        if matched_indices:
            # Ambiguous case - add to ALL matched refs
            for idx in matched_indices:
                if idx in by_ref:
                    # Check if already added to avoid duplicates
                    if not any(r["id"] == result["id"] for r in by_ref[idx]):
                        by_ref[idx].append(result)
                else:
                    logger.warning(f"Ambiguous result references unknown index {idx}")
        elif matched_index is not None and matched_index in by_ref:
            by_ref[matched_index].append(result)
        # Orphans are handled separately in _extract_orphans

    return by_ref


def _extract_orphans(results: List[Dict]) -> List[Dict]:
    """
    Extract citations with no matching reference.

    Args:
        results: List of validation result dicts

    Returns:
        List of orphan citation results
    """
    orphans = []

    for result in results:
        match_status = result.get("match_status", "not_found")
        matched_index = result.get("matched_ref_index")
        matched_indices = result.get("matched_ref_indices")

        # Orphan if not_found OR if no index was matched
        if match_status == "not_found" or (matched_index is None and not matched_indices):
            orphans.append(result)

    return orphans
