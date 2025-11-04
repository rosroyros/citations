"""Test HTMLToTextConverter with TipTap's actual <p> tag structure."""
import sys
sys.path.insert(0, '/Users/roy/Documents/Projects/citations/backend')

from app import html_to_text_with_formatting
from prompt_manager import PromptManager

print("=" * 80)
print("TESTING: TipTap HTML with <p> tags (what frontend actually sends)")
print("=" * 80)

# This is what TipTap actually generates when you paste 3 citations with blank lines between them
tiptap_html = """<p>Smith, J. A. (2023). Advances in computer vision techniques. <em>IEEE/CVF Conference on Computer Vision and Pattern Recognition</em>.</p>
<p></p>
<p>Johnson, M. R., Davis, S. L., & Thompson, A. K. (2022). Remote learning effectiveness during COVID-19: A meta-analysis. <em>Review of Educational Research</em>, 92(3), 412-445. https://doi.org/10.3102/00346543221075623</p>
<p></p>
<p>Garcia, E. M. (2021). Nurse burnout and patient safety: The mediating role of working conditions. <em>Journal of Nursing Administration</em>, 51(7), 389-395. https://doi.org/10.1097/NNA.0000000000001015</p>"""

print("\n1. TIPTAP HTML INPUT:")
print(tiptap_html)

print("\n" + "=" * 80)
print("2. AFTER HTMLToTextConverter:")
print("=" * 80)
text = html_to_text_with_formatting(tiptap_html)
print(repr(text))
print("\n" + text)

print("\n" + "=" * 80)
print("3. AFTER PromptManager.format_citations():")
print("=" * 80)
pm = PromptManager()
formatted = pm.format_citations(text)
print(formatted)

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)
print("\nKey observations:")
print("1. TipTap wraps EACH paragraph in <p> tags")
print("2. Empty lines become <p></p> (empty paragraph tags)")
print("3. HTMLToTextConverter adds \\n for EACH <p> tag")
print("4. Let's trace the flow...")

print("\n\nDETAILED TRACE:")
print("-" * 80)

lines = text.split('\n')
print(f"\nAfter split('\\n'): {len(lines)} lines")
for i, line in enumerate(lines):
    print(f"  Line {i}: {repr(line)}")

print("\n\nNow prompt_manager processes these lines:")
print("-" * 80)

citations = []
current_citation = []
for i, line in enumerate(lines):
    line_stripped = line.strip()
    print(f"Line {i}: {repr(line)} -> stripped: {repr(line_stripped)}")

    if not line_stripped:
        print(f"  -> Empty line! End current citation.")
        if current_citation:
            citation = ' '.join(current_citation)
            citations.append(citation)
            print(f"     Added citation: {repr(citation)}")
            current_citation = []
    else:
        print(f"  -> Non-empty, append to current_citation")
        current_citation.append(line_stripped)

# Don't forget last citation
if current_citation:
    citation = ' '.join(current_citation)
    citations.append(citation)
    print(f"\nFinal citation (not followed by blank): {repr(citation)}")

print(f"\n\nFINAL RESULT: {len(citations)} citations detected")
for i, cit in enumerate(citations, 1):
    print(f"\nCitation {i}:")
    print(f"  {cit[:80]}...")
