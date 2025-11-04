"""Test to reproduce citation separation and italics issues."""
from backend.prompt_manager import PromptManager
from backend.app import html_to_text_with_formatting

# Test Case 1: Multiple citations without blank lines (your example)
print("=" * 80)
print("TEST 1: Multiple citations pasted together (no blank lines)")
print("=" * 80)

# Simulate what the frontend might send
html_input_1 = """Smith, J. A. (2023). Advances in computer vision techniques. <em>IEEE/CVF Conference on Computer Vision and Pattern Recognition</em>.Johnson, M. R., Davis, S. L., & Thompson, A. K. (2022). Remote learning effectiveness during COVID-19: A meta-analysis. <em>Review of Educational Research</em>, 92(3), 412-445. https://doi.org/10.3102/00346543221075623


Garcia, E. M. (2021). Nurse burnout and patient safety: The mediating role of working conditions. <em>Journal of Nursing Administration</em>, 51(7), 389-395. https://doi.org/10.1097/NNA.0000000000001015"""

text_1 = html_to_text_with_formatting(html_input_1)
print("\nConverted text (with markdown):")
print(repr(text_1))
print("\n" + text_1)

pm = PromptManager()
formatted_1 = pm.format_citations(text_1)
print("\nFormatted for LLM:")
print(formatted_1)

# Test Case 2: Properly separated citations
print("\n" + "=" * 80)
print("TEST 2: Properly separated citations (with blank lines)")
print("=" * 80)

html_input_2 = """Smith, J. A. (2023). Advances in computer vision techniques. <em>IEEE/CVF Conference on Computer Vision and Pattern Recognition</em>.

Johnson, M. R., Davis, S. L., & Thompson, A. K. (2022). Remote learning effectiveness during COVID-19: A meta-analysis. <em>Review of Educational Research</em>, 92(3), 412-445. https://doi.org/10.3102/00346543221075623

Garcia, E. M. (2021). Nurse burnout and patient safety: The mediating role of working conditions. <em>Journal of Nursing Administration</em>, 51(7), 389-395. https://doi.org/10.1097/NNA.0000000000001015"""

text_2 = html_to_text_with_formatting(html_input_2)
print("\nConverted text (with markdown):")
print(repr(text_2))
print("\n" + text_2)

formatted_2 = pm.format_citations(text_2)
print("\nFormatted for LLM:")
print(formatted_2)

# Test Case 3: Plain text with italics (no HTML)
print("\n" + "=" * 80)
print("TEST 3: Plain text input (no HTML tags)")
print("=" * 80)

plain_input = """Smith, J. A. (2023). Advances in computer vision techniques. IEEE/CVF Conference on Computer Vision and Pattern Recognition.Johnson, M. R., Davis, S. L., & Thompson, A. K. (2022). Remote learning effectiveness during COVID-19: A meta-analysis. Review of Educational Research, 92(3), 412-445. https://doi.org/10.3102/00346543221075623


Garcia, E. M. (2021). Nurse burnout and patient safety: The mediating role of working conditions. Journal of Nursing Administration, 51(7), 389-395. https://doi.org/10.1097/NNA.0000000000001015"""

text_3 = html_to_text_with_formatting(plain_input)
print("\nConverted text:")
print(repr(text_3))

formatted_3 = pm.format_citations(text_3)
print("\nFormatted for LLM:")
print(formatted_3)

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)
print("\nExpected behavior:")
print("- Citations should be separated when there's a period followed by capital letter")
print("- Italics should be preserved as markdown underscores")
print("\nActual behavior:")
print("- Citations are only separated by blank lines")
print("- Plain text input has no italics markers")
