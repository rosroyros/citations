"""Test what happens when user presses Enter ONCE between citations (not twice)."""
import sys
sys.path.insert(0, '/Users/roy/Documents/Projects/citations/backend')

from app import html_to_text_with_formatting
from prompt_manager import PromptManager

print("=" * 80)
print("TESTING: User presses Enter ONCE between citations (single newlines)")
print("=" * 80)

# When you press Enter once, TipTap creates separate <p> tags but no empty <p> between them
tiptap_html_single_newline = """<p>Smith, J. A. (2023). Advances in computer vision techniques. <em>IEEE/CVF Conference on Computer Vision and Pattern Recognition</em>.</p>
<p>Johnson, M. R., Davis, S. L., & Thompson, A. K. (2022). Remote learning effectiveness during COVID-19: A meta-analysis. <em>Review of Educational Research</em>, 92(3), 412-445. https://doi.org/10.3102/00346543221075623</p>
<p>Garcia, E. M. (2021). Nurse burnout and patient safety: The mediating role of working conditions. <em>Journal of Nursing Administration</em>, 51(7), 389-395. https://doi.org/10.1097/NNA.0000000000001015</p>"""

print("\n1. TIPTAP HTML (separate <p> tags, no empty <p> between):")
print(tiptap_html_single_newline)

print("\n" + "=" * 80)
print("2. AFTER HTMLToTextConverter:")
print("=" * 80)
text = html_to_text_with_formatting(tiptap_html_single_newline)
print(repr(text))
print("\n" + text)

print("\n" + "=" * 80)
print("3. Looking at individual lines after split:")
print("=" * 80)
lines = text.split('\n')
for i, line in enumerate(lines):
    print(f"Line {i}: {repr(line)}")

print("\n" + "=" * 80)
print("4. AFTER PromptManager.format_citations():")
print("=" * 80)
pm = PromptManager()
formatted = pm.format_citations(text)
print(formatted)

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)
print("\nWith SINGLE newlines (Enter once):")
print("- Each citation is in its own <p> tag")
print("- HTMLToTextConverter adds \\n at start AND end of each <p>")
print("- Result: Citation1\\n\\nCitation2\\n\\nCitation3")
print("- Split gives: ['Citation1', '', 'Citation2', '', 'Citation3']")
print("- Parser sees blank lines and should split correctly!")
