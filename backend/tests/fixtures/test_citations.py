"""Test citation fixtures for integration testing.

Provides sample citations in different sizes (small, medium, large batches)
for testing async job processing with real LLM calls.
"""

# Small batch fixtures (1-3 citations)
SMALL_BATCH_SINGLE = "<p>Smith, J. (2020). Example journal article. Journal of Testing, 15(2), 123-145.</p>"

SMALL_BATCH_DOUBLE = """<p>Smith, J. (2020). Example journal article. Journal of Testing, 15(2), 123-145.</p>
<p>Jones, A. B. (2021). Book example. Academic Press.</p>"""

SMALL_BATCH_TRIPLE = """<p>Smith, J. (2020). Example journal article. Journal of Testing, 15(2), 123-145.</p>
<p>Jones, A. B. (2021). Book example. Academic Press.</p>
<p>Wilson, K. (2019). Conference paper. Proceedings of Test Conference, 45-67.</p>"""

# Medium batch fixtures (5-10 citations)
MEDIUM_BATCH_FIVE = """<p>Smith, J. (2020). Example journal article. Journal of Testing, 15(2), 123-145.</p>
<p>Jones, A. B. (2021). Book example. Academic Press.</p>
<p>Wilson, K. (2019). Conference paper. Proceedings of Test Conference, 45-67.</p>
<p>Davis, M. L. (2022). Website example. https://example.com/article</p>
<p>Johnson, R. (2018). Chapter in edited book. In K. Williams (Ed.), Academic Writing (pp. 89-112). University Press.</p>"""

MEDIUM_BATCH_EIGHT = """<p>Smith, J. (2020). Example journal article. Journal of Testing, 15(2), 123-145.</p>
<p>Jones, A. B. (2021). Book example. Academic Press.</p>
<p>Wilson, K. (2019). Conference paper. Proceedings of Test Conference, 45-67.</p>
<p>Davis, M. L. (2022). Website example. https://example.com/article</p>
<p>Johnson, R. (2018). Chapter in edited book. In K. Williams (Ed.), Academic Writing (pp. 89-112). University Press.</p>
<p>Brown, T. (2020). Dissertation example. Doctoral dissertation, University of Example.</p>
<p>Taylor, S. (2021). Magazine article. Tech Monthly, 45(3), 78-85.</p>
<p>Anderson, P. (2019). Government report. Department of Education Report No. 123.</p>"""

# Large batch fixtures (15-25+ citations) - for testing timeout handling
LARGE_BATCH_FIFTEEN = """<p>Smith, J. (2020). Example journal article. Journal of Testing, 15(2), 123-145.</p>
<p>Jones, A. B. (2021). Book example. Academic Press.</p>
<p>Wilson, K. (2019). Conference paper. Proceedings of Test Conference, 45-67.</p>
<p>Davis, M. L. (2022). Website example. https://example.com/article</p>
<p>Johnson, R. (2018). Chapter in edited book. In K. Williams (Ed.), Academic Writing (pp. 89-112). University Press.</p>
<p>Brown, T. (2020). Dissertation example. Doctoral dissertation, University of Example.</p>
<p>Taylor, S. (2021). Magazine article. Tech Monthly, 45(3), 78-85.</p>
<p>Anderson, P. (2019). Government report. Department of Education Report No. 123.</p>
<p>Miller, D. (2020). Patent example. U.S. Patent No. 10,123,456.</p>
<p>Thomas, E. (2018). Software manual. Version 2.0. Tech Company.</p>
<p>White, J. (2021). Newspaper article. City Times, p. A5.</p>
<p>Harris, M. (2019). Online video. https://youtube.com/example</p>
<p>Martin, L. (2020). Blog post. https://blog.example.com/post</p>
<p>Garcia, C. (2021). Podcast episode. Episode 12. Podcast Network.</p>
<p>Lee, H. (2018). Thesis example. Master's thesis, State University.</p>"""

LARGE_BATCH_TWENTY_FIVE = LARGE_BATCH_FIFTEEN + """
<p>Clark, R. (2022). Encyclopedia entry. In Academic Encyclopedia (Vol. 3, pp. 145-150).</p>
<p>Rodriguez, A. (2020). Map example. Geographic Data Institute.</p>
<p>Lewis, M. (2021). Interview transcript. Personal communication, June 15.</p>
<p>Walker, K. (2019). Classical work. Shakespeare, W. (1600). Hamlet.</p>
<p>Hall, S. (2020). Legal case. Supreme Court Decision, 123 U.S. 456.</p>
<p>Young, T. (2021). Press release. Company Name Announcement.</p>
<p>King, D. (2018). Standard. ISO 9001:2015. International Organization.</p>
<p>Wright, J. (2020). Database example. Academic Database Online.</p>
<p>Lopez, M. (2021). Symposium paper. Advances in Science, 78-95.</p>
<p>Hill, P. (2019). Working paper. Economic Research Institute.</p>"""

# Malformed citations for testing validation
MALFORMED_CITATIONS = [
    "Smith 2020 Journal of Testing",  # Missing punctuation and formatting
    "Jones (2021) Book Academic Press",  # Incorrect parentheses placement
    "Wilson, 2019, conference proceedings",  # Lowercase and missing italics
    "https://example.com",  # Just a URL, no proper citation
    "Some random text that's not a citation at all",  # Non-citation text
]

# Mixed quality citations for testing partial results
MIXED_QUALITY_CITATIONS = """<p>Smith, J. (2020). Well-formatted journal article. Journal of Testing, 15(2), 123-145.</p>
<p>Smith 2020 Journal of Testing</p>
<p>Wilson, K. (2019). Another good citation. Proceedings of Test Conference, 45-67.</p>
<p>https://example.com/article</p>
<p>Johnson, R. (2018). Proper book citation. Academic Press.</p>"""

# Different source types for comprehensive testing
DIFFERENT_SOURCE_TYPES = """<p>Smith, J. (2020). Journal article. Journal of Testing, 15(2), 123-145.</p>
<p>Jones, A. B. (2021). Book example. Academic Press.</p>
<p>Wilson, K. (2019). Conference paper. Proceedings of Test Conference, 45-67.</p>
<p>Davis, M. L. (2022). Website example. https://example.com/article</p>
<p>Johnson, R. (2018). Chapter in edited book. In K. Williams (Ed.), Academic Writing (pp. 89-112). University Press.</p>
<p>Brown, T. (2020). Dissertation example. Doctoral dissertation, University of Example.</p>
<p>Taylor, S. (2021). Magazine article. Tech Monthly, 45(3), 78-85.</p>
<p>Anderson, P. (2019). Government report. Department of Education Report No. 123.</p>"""

# Test data utilities
def get_citation_batch(size: str = "small"):
    """Get citation batch by size.

    Args:
        size: "small", "medium", or "large"

    Returns:
        str: HTML-formatted citations

    Raises:
        ValueError: If size is not recognized
    """
    if size == "small":
        return SMALL_BATCH_TRIPLE
    elif size == "medium":
        return MEDIUM_BATCH_EIGHT
    elif size == "large":
        return LARGE_BATCH_FIFTEEN
    else:
        raise ValueError(f"Unknown size: {size}. Use 'small', 'medium', or 'large'.")

def get_malformed_citations():
    """Get malformed citations for testing error handling."""
    return "<p>".join(MALFORMED_CITATIONS) + "</p>"

def get_mixed_quality_citations():
    """Get mix of well-formatted and malformed citations."""
    return MIXED_QUALITY_CITATIONS

def count_citations(html_text: str) -> int:
    """Count the number of <p> tags in HTML text.

    Args:
        html_text: HTML text containing citations

    Returns:
        int: Number of citations (paragraph tags)
    """
    return html_text.count("<p>")