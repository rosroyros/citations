"""
Test fixtures containing correct and incorrect APA 7th edition citations.
These fixtures test the validation system with realistic citation examples.
"""

# ============================================================================
# CORRECT APA 7th CITATIONS (Should pass validation)
# ============================================================================

CORRECT_JOURNAL_ARTICLE = """
Smith, J. A., & Brown, K. L. (2023). Understanding citation validation in academic writing. Journal of Academic Research, 45(3), 234-256. https://doi.org/10.1234/jar.2023.45.3.234
"""

CORRECT_BOOK = """
Johnson, M. R. (2022). The complete guide to academic writing (3rd ed.). Oxford University Press.
"""

CORRECT_BOOK_CHAPTER = """
Williams, T. S., & Davis, P. Q. (2021). Citation styles in the digital age. In R. Anderson & L. Martinez (Eds.), Modern academic practices (pp. 112-145). Cambridge University Press.
"""

CORRECT_WEBPAGE = """
World Health Organization. (2024, March 15). Global health statistics. https://www.who.int/data/global-health-statistics
"""

# All correct citations combined
CORRECT_CITATIONS_ALL = """
Smith, J. A., & Brown, K. L. (2023). Understanding citation validation in academic writing. Journal of Academic Research, 45(3), 234-256. https://doi.org/10.1234/jar.2023.45.3.234

Johnson, M. R. (2022). The complete guide to academic writing (3rd ed.). Oxford University Press.

Williams, T. S., & Davis, P. Q. (2021). Citation styles in the digital age. In R. Anderson & L. Martinez (Eds.), Modern academic practices (pp. 112-145). Cambridge University Press.

World Health Organization. (2024, March 15). Global health statistics. https://www.who.int/data/global-health-statistics
"""

# ============================================================================
# INCORRECT APA 7th CITATIONS (Should fail validation with specific errors)
# ============================================================================

# Error: Uses "and" instead of "&" before last author
INCORRECT_AND_INSTEAD_OF_AMPERSAND = """
Smith, J. A., Brown, K. L., and Wilson, R. T. (2023). Understanding citation validation. Journal of Academic Research, 45(3), 234-256. https://doi.org/10.1234/jar.2023.45.3.234
"""

# Error: Book title not in sentence case (should be lowercase after first word)
INCORRECT_TITLE_CASE_BOOK = """
Johnson, M. R. (2022). The Complete Guide to Academic Writing (3rd ed.). Oxford University Press.
"""

# Error: Article title not in sentence case
INCORRECT_TITLE_CASE_ARTICLE = """
Smith, J. A., & Brown, K. L. (2023). Understanding Citation Validation in Academic Writing. Journal of Academic Research, 45(3), 234-256. https://doi.org/10.1234/jar.2023.45.3.234
"""

# Error: Old DOI format with "doi:" prefix (APA 7th requires https://doi.org/)
INCORRECT_OLD_DOI_FORMAT = """
Smith, J. A., & Brown, K. L. (2023). Understanding citation validation in academic writing. Journal of Academic Research, 45(3), 234-256. doi:10.1234/jar.2023.45.3.234
"""

# Error: Missing DOI for journal article (should have DOI if available)
INCORRECT_MISSING_DOI = """
Smith, J. A., & Brown, K. L. (2023). Understanding citation validation in academic writing. Journal of Academic Research, 45(3), 234-256.
"""

# Error: Includes publisher location (APA 7th omits locations)
INCORRECT_PUBLISHER_LOCATION = """
Johnson, M. R. (2022). The complete guide to academic writing (3rd ed.). New York, NY: Oxford University Press.
"""

# Error: Missing retrieval date for webpage (not needed in APA 7th unless content changes)
# and uses "Retrieved from" (old format)
INCORRECT_OLD_WEBPAGE_FORMAT = """
World Health Organization. (2024). Global health statistics. Retrieved from https://www.who.int/data/global-health-statistics
"""

# Error: Journal title not in title case (should be capitalized)
INCORRECT_JOURNAL_TITLE_CASE = """
Smith, J. A., & Brown, K. L. (2023). Understanding citation validation in academic writing. journal of academic research, 45(3), 234-256. https://doi.org/10.1234/jar.2023.45.3.234
"""

# Error: Missing page numbers for book chapter
INCORRECT_MISSING_PAGE_NUMBERS = """
Williams, T. S., & Davis, P. Q. (2021). Citation styles in the digital age. In R. Anderson & L. Martinez (Eds.), Modern academic practices. Cambridge University Press.
"""

# Error: Using initials without periods
INCORRECT_NO_PERIODS_INITIALS = """
Smith, JA, & Brown, KL (2023). Understanding citation validation in academic writing. Journal of Academic Research, 45(3), 234-256. https://doi.org/10.1234/jar.2023.45.3.234
"""

# Multiple errors in one citation
INCORRECT_MULTIPLE_ERRORS = """
Smith, J. A., Brown, K. L., and Wilson, R. T. (2023). Understanding Citation Validation in Academic Writing. journal of academic research, 45(3), 234-256. doi:10.1234/jar.2023.45.3.234
"""

# All incorrect citations combined
INCORRECT_CITATIONS_ALL = f"""
{INCORRECT_AND_INSTEAD_OF_AMPERSAND.strip()}

{INCORRECT_TITLE_CASE_BOOK.strip()}

{INCORRECT_TITLE_CASE_ARTICLE.strip()}

{INCORRECT_OLD_DOI_FORMAT.strip()}

{INCORRECT_MISSING_DOI.strip()}

{INCORRECT_PUBLISHER_LOCATION.strip()}

{INCORRECT_OLD_WEBPAGE_FORMAT.strip()}

{INCORRECT_JOURNAL_TITLE_CASE.strip()}

{INCORRECT_MISSING_PAGE_NUMBERS.strip()}

{INCORRECT_NO_PERIODS_INITIALS.strip()}

{INCORRECT_MULTIPLE_ERRORS.strip()}
"""

# ============================================================================
# MIXED CORRECT AND INCORRECT CITATIONS
# ============================================================================

MIXED_CITATIONS = """
Smith, J. A., & Brown, K. L. (2023). Understanding citation validation in academic writing. Journal of Academic Research, 45(3), 234-256. https://doi.org/10.1234/jar.2023.45.3.234

Johnson, M. R. (2022). The Complete Guide to Academic Writing (3rd ed.). Oxford University Press.

Williams, T. S., & Davis, P. Q. (2021). Citation styles in the digital age. In R. Anderson & L. Martinez (Eds.), Modern academic practices (pp. 112-145). Cambridge University Press.

World Health Organization. (2024). Global health statistics. Retrieved from https://www.who.int/data/global-health-statistics

Smith, J. A., Brown, K. L., and Wilson, R. T. (2023). Understanding citation validation. Journal of Academic Research, 45(3), 234-256. https://doi.org/10.1234/jar.2023.45.3.234
"""

# ============================================================================
# EDGE CASES
# ============================================================================

# Edge case: More than 20 authors (should use ellipsis)
EDGE_CASE_MANY_AUTHORS = """
Smith, A., Jones, B., Williams, C., Brown, D., Davis, E., Miller, F., Wilson, G., Moore, H., Taylor, I., Anderson, J., Thomas, K., Jackson, L., White, M., Harris, N., Martin, O., Thompson, P., Garcia, Q., Martinez, R., Robinson, S., & Clark, T. (2023). Large collaborative study. Journal of Research, 10(1), 1-50. https://doi.org/10.1234/jr.2023.1
"""

# Edge case: No date (use n.d.)
EDGE_CASE_NO_DATE = """
Ancient Author. (n.d.). Historical manuscript. Ancient Press.
"""

# Edge case: Group/corporate author
EDGE_CASE_CORPORATE_AUTHOR = """
American Psychological Association. (2020). Publication manual of the American Psychological Association (7th ed.). https://doi.org/10.1037/0000165-000
"""

# Edge case: Article with article number instead of page numbers
EDGE_CASE_ARTICLE_NUMBER = """
Lee, S., & Kim, J. (2023). Digital citations in modern research. Nature Communications, 14, Article 5678. https://doi.org/10.1038/s41467-023-5678-x
"""

# All edge cases combined
EDGE_CASES_ALL = f"""
{EDGE_CASE_MANY_AUTHORS.strip()}

{EDGE_CASE_NO_DATE.strip()}

{EDGE_CASE_CORPORATE_AUTHOR.strip()}

{EDGE_CASE_ARTICLE_NUMBER.strip()}
"""

# ============================================================================
# EXPECTED ERRORS (for testing error detection)
# ============================================================================

EXPECTED_ERRORS = {
    "INCORRECT_AND_INSTEAD_OF_AMPERSAND": [
        "should use '&' not 'and' before last author"
    ],
    "INCORRECT_TITLE_CASE_BOOK": [
        "title case",
        "sentence case"
    ],
    "INCORRECT_TITLE_CASE_ARTICLE": [
        "title case",
        "sentence case"
    ],
    "INCORRECT_OLD_DOI_FORMAT": [
        "doi:",
        "https://doi.org/"
    ],
    "INCORRECT_MISSING_DOI": [
        "DOI",
        "missing"
    ],
    "INCORRECT_PUBLISHER_LOCATION": [
        "location",
        "New York"
    ],
    "INCORRECT_OLD_WEBPAGE_FORMAT": [
        "Retrieved from"
    ],
    "INCORRECT_JOURNAL_TITLE_CASE": [
        "journal title",
        "title case"
    ],
    "INCORRECT_MISSING_PAGE_NUMBERS": [
        "page numbers",
        "pp."
    ],
    "INCORRECT_NO_PERIODS_INITIALS": [
        "initials",
        "periods"
    ],
    "INCORRECT_MULTIPLE_ERRORS": [
        "&",
        "title case",
        "doi:"
    ]
}
