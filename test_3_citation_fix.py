"""Test the fix with the original 3-citation example from the issue."""
import sys
sys.path.insert(0, '/Users/roy/Documents/Projects/citations/backend')

from app import html_to_text_with_formatting
from prompt_manager import PromptManager

# Original 3 citations from your screenshot
html_input = """<p>Smith, J. A. (2023). Advances in computer vision techniques. <em>IEEE/CVF Conference on Computer Vision and Pattern Recognition</em>.</p><p>Johnson, M. R., Davis, S. L., & Thompson, A. K. (2022). Remote learning effectiveness during COVID-19: A meta-analysis. <em>Review of Educational Research</em>, 92(3), 412-445. https://doi.org/10.3102/00346543221075623</p><p>Garcia, E. M. (2021). Nurse burnout and patient safety: The mediating role of working conditions. <em>Journal of Nursing Administration</em>, 51(7), 389-395. https://doi.org/10.1097/NNA.0000000000001015</p>"""

print("=" * 80)
print("TESTING: Original 3-citation example (Smith, Johnson, Garcia)")
print("=" * 80)

print("\nStep 1: HTML to Text Conversion")
text = html_to_text_with_formatting(html_input)
print(f"Length: {len(text)} chars")
print(f"\n{text}")

print("\n" + "=" * 80)
print("Step 2: Citation Formatting")
print("=" * 80)

pm = PromptManager()
formatted = pm.format_citations(text)
print(formatted)

# Count detected
detected = formatted.count('\n\n') + 1
print(f"\n" + "=" * 80)
print("RESULT")
print("=" * 80)
print(f"Expected: 3 citations")
print(f"Detected: {detected} citations")

if detected == 3:
    print("✅ SUCCESS! Fix works correctly!")

    # Check italics
    if '_IEEE/CVF' in formatted and '_Review of Educational Research_' in formatted:
        print("✅ Italics preserved correctly!")
    else:
        print("⚠️ Italics might not be preserved")
else:
    print(f"❌ FAILED: Expected 3, got {detected}")
