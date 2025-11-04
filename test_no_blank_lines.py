"""Test what happens when user pastes citations WITHOUT blank lines between them."""
import sys
sys.path.insert(0, '/Users/roy/Documents/Projects/citations/backend')

from app import html_to_text_with_formatting
from prompt_manager import PromptManager

print("=" * 80)
print("TESTING: User pastes 3 citations WITHOUT blank lines (all in one paragraph)")
print("=" * 80)

# When you paste multiple citations without line breaks, TipTap treats it as ONE paragraph
tiptap_html_no_breaks = """<p>Smith, J. A. (2023). Advances in computer vision techniques. <em>IEEE/CVF Conference on Computer Vision and Pattern Recognition</em>.Johnson, M. R., Davis, S. L., & Thompson, A. K. (2022). Remote learning effectiveness during COVID-19: A meta-analysis. <em>Review of Educational Research</em>, 92(3), 412-445. https://doi.org/10.3102/00346543221075623Garcia, E. M. (2021). Nurse burnout and patient safety: The mediating role of working conditions. <em>Journal of Nursing Administration</em>, 51(7), 389-395. https://doi.org/10.1097/NNA.0000000000001015</p>"""

print("\n1. TIPTAP HTML (all in one <p> tag):")
print(tiptap_html_no_breaks)

print("\n" + "=" * 80)
print("2. AFTER HTMLToTextConverter:")
print("=" * 80)
text = html_to_text_with_formatting(tiptap_html_no_breaks)
print(repr(text))
print("\n" + text)

print("\n" + "=" * 80)
print("3. AFTER PromptManager.format_citations():")
print("=" * 80)
pm = PromptManager()
formatted = pm.format_citations(text)
print(formatted)

print("\n" + "=" * 80)
print("THIS IS THE BUG!")
print("=" * 80)
print("\nWhen user pastes from Word/Google Docs without hitting Enter between citations,")
print("TipTap treats the entire paste as ONE paragraph.")
print("\nThe parser sees NO blank lines, so treats it as 1 citation.")
print("\n✅ Italics ARE preserved correctly (_text_)")
print("❌ Citations are NOT separated")
