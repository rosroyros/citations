"""Test for max_tokens limiting LLM response with multiple citations."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from providers.openai_provider import OpenAIProvider


@pytest.mark.asyncio
async def test_nine_citations_within_token_limit():
    """Test that 9 citations can be validated without hitting token limit."""
    provider = OpenAIProvider(api_key="test-key")

    # Sample 9 citations (from the actual logs)
    citations = """Adli, A. (2013). Syntactic variation in French Wh-questions: A quantitative study from the angle of Bourdieu's sociocultural theory. _Linguistics_, _51_(3), 473-515.

Agarwal, D., Naaman, M., & Vashistha, A. (2025, April). AI suggestions homogenize writing toward western styles and diminish cultural nuances. In _Proceedings of the 2025 CHI Conference on Human Factors in Computing Systems_ (pp. 1-21).

Airoldi, M. (2021). _Machine habitus: Toward a sociology of algorithms_. John Wiley & Sons.

Airoldi 2022

Ajunwa, I. (2020). The "black box" at work. _Big Data & Society_, _7_(2), 2053951720966181.

Ajunwa, I. (2023). _The quantified worker: Law and technology in the modern workplace_. Cambridge University Press.

Alvero, A. J., Pal, J., & Moussavian, K. M. (2022). Linguistic, cultural, and narrative capital: computational and human readings of transfer admissions essays. _Journal of Computational Social Science_, _5_(2), 1709-1734.

Alvero, A. J., Lee, J., Regla-Vargas, A., Kizilcec, R. F., Joachims, T., & Antonio, A. L. (2024). Large language models, social demography, and hegemony: comparing authorship in human and synthetic text. _Journal of Big Data_, _11_(1), 138.

Angwin, J., Larson, J., Mattu, S. and Kirchner, L. (2016) 'Machine bias', ProPublica, 23 May 2016, https://bit.ly/2NubAFX."""

    # Mock the OpenAI API response with ALL 9 citations
    # This simulates what SHOULD happen with sufficient max_tokens
    mock_response = Mock()
    mock_response.choices = [Mock()]

    # Create a full response with all 9 citations (truncated for brevity)
    full_response = """═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Adli, A. (2013). Syntactic variation in French Wh-questions: A quantitative study from the angle of Bourdieu's sociocultural theory. _Linguistics_, _51_(3), 473-515.

SOURCE TYPE: Journal Article

VALIDATION RESULTS:
✓ No APA 7 formatting errors detected.

═══════════════════════════════════════════════════════════════════════════
CITATION #2
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Agarwal, D., Naaman, M., & Vashistha, A. (2025, April). AI suggestions homogenize writing toward western styles and diminish cultural nuances. In _Proceedings of the 2025 CHI Conference on Human Factors in Computing Systems_ (pp. 1-21).

SOURCE TYPE: Conference Paper

VALIDATION RESULTS:
✓ No APA 7 formatting errors detected.

═══════════════════════════════════════════════════════════════════════════
CITATION #3
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Airoldi, M. (2021). _Machine habitus: Toward a sociology of algorithms_. John Wiley & Sons.

SOURCE TYPE: Book

VALIDATION RESULTS:
✓ No APA 7 formatting errors detected.

═══════════════════════════════════════════════════════════════════════════
CITATION #4
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Airoldi 2022

SOURCE TYPE: Incomplete Citation

VALIDATION RESULTS:
❌ Missing Components: This citation is incomplete and missing essential information (title, publication details).

═══════════════════════════════════════════════════════════════════════════
CITATION #5
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Ajunwa, I. (2020). The "black box" at work. _Big Data & Society_, _7_(2), 2053951720966181.

SOURCE TYPE: Journal Article

VALIDATION RESULTS:
✓ No APA 7 formatting errors detected.

═══════════════════════════════════════════════════════════════════════════
CITATION #6
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Ajunwa, I. (2023). _The quantified worker: Law and technology in the modern workplace_. Cambridge University Press.

SOURCE TYPE: Book

VALIDATION RESULTS:
✓ No APA 7 formatting errors detected.

═══════════════════════════════════════════════════════════════════════════
CITATION #7
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Alvero, A. J., Pal, J., & Moussavian, K. M. (2022). Linguistic, cultural, and narrative capital: computational and human readings of transfer admissions essays. _Journal of Computational Social Science_, _5_(2), 1709-1734.

SOURCE TYPE: Journal Article

VALIDATION RESULTS:
✓ No APA 7 formatting errors detected.

═══════════════════════════════════════════════════════════════════════════
CITATION #8
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Alvero, A. J., Lee, J., Regla-Vargas, A., Kizilcec, R. F., Joachims, T., & Antonio, A. L. (2024). Large language models, social demography, and hegemony: comparing authorship in human and synthetic text. _Journal of Big Data_, _11_(1), 138.

SOURCE TYPE: Journal Article

VALIDATION RESULTS:
✓ No APA 7 formatting errors detected.

═══════════════════════════════════════════════════════════════════════════
CITATION #9
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Angwin, J., Larson, J., Mattu, S. and Kirchner, L. (2016) 'Machine bias', ProPublica, 23 May 2016, https://bit.ly/2NubAFX.

SOURCE TYPE: Blog/Online Article

VALIDATION RESULTS:
✓ No APA 7 formatting errors detected."""

    mock_response.choices[0].message.content = full_response
    mock_response.usage = Mock()
    mock_response.usage.prompt_tokens = 1025
    mock_response.usage.completion_tokens = 2500  # More than previous 2000 limit
    mock_response.usage.total_tokens = 3525

    # Patch the OpenAI client
    with patch.object(provider.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response

        # Validate
        result = await provider.validate_citations(citations)

        # Should get ALL 9 citations back
        assert len(result["results"]) == 9, f"Expected 9 results, got {len(result['results'])}"

        # Verify the API was called with sufficient max_tokens
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["max_tokens"] >= 4000, f"max_tokens should be at least 4000 for 9 citations, got {call_kwargs['max_tokens']}"


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_nine_citations_within_token_limit())
    print("✓ Test passed - 9 citations can be validated with sufficient max_tokens")
