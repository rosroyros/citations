"""
Document parsing module for inline citation validation.

This module provides core functionality for extracting and processing
citations from uploaded documents. It implements smart context extraction
that achieves ~95% token reduction by splitting documents into body text
and reference sections.

Key functions:
- convert_docx_to_html: Convert DOCX files to HTML preserving formatting
- split_document: Split body text from reference list using header detection
- scan_inline_citations: Find inline citations using regex patterns
"""
import io
import re
from typing import List, Dict, Tuple
import mammoth

# Header keywords that indicate the start of a reference/bibliography section
# Case-insensitive matching
REF_HEADER_KEYWORDS = [
    "references",
    "reference list",
    "bibliography",
    "works cited",
    "literature cited",
    "sources",
    "sources cited",
    "references cited",
]

# Regex patterns for inline citation detection
# Intentionally permissive - false positives OK (LLM will reject)
# False negatives are BAD (would miss actual citations)
INLINE_PATTERNS = {
    "apa7": r"\([A-Za-z][A-Za-z\s&.,]+?,?\s+\d{4}[a-z]?\)",
    # APA: (Smith, 2019), (Smith & Jones, 2019), (Smith et al., 2019a)
    # Pattern breakdown: \( + starts with letter + authors/&/et al. + optional comma + space + 4-digit year + optional letter
    "mla9": r"\([A-Za-z][A-Za-z\s]+,?\s+\d+(?:-\d+)?\)",
    # MLA: (Smith 12), (Smith 42-45), (Smith and Jones 12)
    # Pattern breakdown: \( + starts with letter + author name(s) + optional comma + space + page number(s)
    "chicago17": r"\([A-Za-z][A-Za-z\s]+,?\s+\d+(?:-\d+)?\)",
    # Chicago (notes-biblio style inline): Similar to MLA for author-date
}


def convert_docx_to_html(file_bytes: bytes) -> str:
    """
    Convert DOCX file to HTML preserving formatting.

    Preserves <em> and <strong> tags which are semantic requirements
    for citation styles (italics for titles, etc.).

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

    Uses header detection to find where the reference section begins.
    Searches for common bibliography headers in <h1>, <h2>, <h3>, or <strong> tags.

    Algorithm:
    1. Find all matches of reference header keywords (case-insensitive)
    2. Take the LAST match (references typically at end of document)
    3. Split at that point: everything before is body, everything after is refs
    4. If no match found, treat entire content as ref-list only (backward compat)

    Args:
        html: Full document HTML

    Returns:
        Tuple of (body_html, refs_html, found_header)
        - body_html: HTML content before reference section (empty if no header found)
        - refs_html: HTML content of reference section (full content if no header found)
        - found_header: True if a reference header was detected
    """
    found_header = False
    split_position = 0

    # Build regex pattern to match headers containing reference keywords
    # Matches <h1>, <h2>, <h3>, <strong> tags with any of the keywords
    keywords_pattern = "|".join(re.escape(kw) for kw in REF_HEADER_KEYWORDS)
    header_pattern = rf'<(h1|h2|h3|strong)[^>]*>\s*({keywords_pattern})\s*</\1>'

    # Find all matches (case-insensitive)
    matches = list(re.finditer(header_pattern, html, re.IGNORECASE))

    if matches:
        # Use the LAST match (references at end of document)
        last_match = matches[-1]
        # Use end() to exclude the header tag from refs_html
        # This prevents "References" from being parsed as first citation
        split_position = last_match.end()
        found_header = True

    # Split the document
    if found_header:
        body_html = html[:last_match.start()].strip()  # Body ends before header
        refs_html = html[split_position:].strip()  # Refs start after header
    else:
        # No header found - treat entire content as reference list
        # This maintains backward compatibility with paste-only flow
        body_html = ""
        refs_html = html.strip()

    return body_html, refs_html, found_header


def scan_inline_citations(body_html: str, style: str) -> List[Dict[str, any]]:
    """
    Find inline citations in body text using regex patterns.

    Args:
        body_html: HTML content of the document body (before reference section)
        style: Citation style identifier (e.g., "apa7", "mla9", "chicago17")

    Returns:
        List of dictionaries with keys:
        - id: Sequential citation ID (e.g., "c1", "c2", ...)
        - text: The matched inline citation text (e.g., "(Smith, 2019)")
        - position: Character position in the stripped text string

    Notes:
        - Patterns are intentionally permissive to avoid false negatives
        - HTML tags are stripped before regex scanning
        - False positives are acceptable (LLM validation will filter them out)
        - Returns empty list if style not supported or no citations found
    """
    if not body_html:
        return []

    # Get the appropriate regex pattern for the style
    pattern = INLINE_PATTERNS.get(style.lower())
    if not pattern:
        # Return empty list for unsupported styles
        return []

    # Strip HTML tags for regex scanning (as per design doc)
    text = re.sub(r'<[^>]+>', ' ', body_html)

    # Find all matches
    matches = re.finditer(pattern, text)

    # Build result list with IDs
    citations = []
    for idx, match in enumerate(matches, start=1):
        citations.append({
            "id": f"c{idx}",
            "text": match.group(0),
            "position": match.start(),
        })

    return citations
