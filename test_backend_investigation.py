"""
Backend Investigation Tool
Tests the complete pipeline: HTML → Text Conversion → Citation Formatting → LLM Prompt
"""
import sys
sys.path.insert(0, '/Users/roy/Documents/Projects/citations/backend')

from app import html_to_text_with_formatting
from prompt_manager import PromptManager

def test_scenario(name, html_input, expected_citations):
    """Test a specific HTML input scenario."""
    print("=" * 80)
    print(f"SCENARIO: {name}")
    print("=" * 80)

    print("\n1️⃣ INPUT HTML:")
    print(html_input)

    print("\n2️⃣ AFTER HTMLToTextConverter:")
    text = html_to_text_with_formatting(html_input)
    print(f"Text length: {len(text)} characters")
    print(f"Repr: {repr(text)}")
    print(f"\nActual text:\n{text}")

    print("\n3️⃣ LINE-BY-LINE ANALYSIS:")
    lines = text.split('\n')
    print(f"Total lines: {len(lines)}")
    for i, line in enumerate(lines):
        indicator = "📝" if line.strip() else "⚪"
        print(f"  Line {i}: {indicator} {repr(line)}")

    print("\n4️⃣ AFTER format_citations():")
    pm = PromptManager()
    try:
        formatted = pm.format_citations(text)
        print(formatted)

        # Count detected citations
        detected = formatted.count('\n\n') + 1
        print(f"\n📊 DETECTED: {detected} citation(s)")
        print(f"📋 EXPECTED: {expected_citations} citation(s)")

        if detected == expected_citations:
            print("✅ PASS: Correct number of citations detected")
        else:
            print(f"❌ FAIL: Expected {expected_citations}, got {detected}")

        return detected == expected_citations
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

# Test scenarios based on different paste behaviors
scenarios = [
    {
        "name": "All in one <p> tag (copy-paste without breaks)",
        "html": """<p>Smith, J. A. (2023). Advances in computer vision techniques. <em>IEEE/CVF Conference on Computer Vision and Pattern Recognition</em>.Johnson, M. R., Davis, S. L., & Thompson, A. K. (2022). Remote learning effectiveness during COVID-19: A meta-analysis. <em>Review of Educational Research</em>, 92(3), 412-445. https://doi.org/10.3102/00346543221075623Garcia, E. M. (2021). Nurse burnout and patient safety: The mediating role of working conditions. <em>Journal of Nursing Administration</em>, 51(7), 389-395. https://doi.org/10.1097/NNA.0000000000001015</p>""",
        "expected": 3  # Should detect 3, but will likely detect 1
    },
    {
        "name": "Separate <p> tags, no empty <p> between (Enter once)",
        "html": """<p>Smith, J. A. (2023). Advances in computer vision techniques. <em>IEEE/CVF Conference on Computer Vision and Pattern Recognition</em>.</p>
<p>Johnson, M. R., Davis, S. L., & Thompson, A. K. (2022). Remote learning effectiveness during COVID-19: A meta-analysis. <em>Review of Educational Research</em>, 92(3), 412-445. https://doi.org/10.3102/00346543221075623</p>
<p>Garcia, E. M. (2021). Nurse burnout and patient safety: The mediating role of working conditions. <em>Journal of Nursing Administration</em>, 51(7), 389-395. https://doi.org/10.1097/NNA.0000000000001015</p>""",
        "expected": 3
    },
    {
        "name": "Separate <p> tags WITH empty <p> between (Enter twice)",
        "html": """<p>Smith, J. A. (2023). Advances in computer vision techniques. <em>IEEE/CVF Conference on Computer Vision and Pattern Recognition</em>.</p>
<p></p>
<p>Johnson, M. R., Davis, S. L., & Thompson, A. K. (2022). Remote learning effectiveness during COVID-19: A meta-analysis. <em>Review of Educational Research</em>, 92(3), 412-445. https://doi.org/10.3102/00346543221075623</p>
<p></p>
<p>Garcia, E. M. (2021). Nurse burnout and patient safety: The mediating role of working conditions. <em>Journal of Nursing Administration</em>, 51(7), 389-395. https://doi.org/10.1097/NNA.0000000000001015</p>""",
        "expected": 3
    },
    {
        "name": "Mixed: First two together, third separate",
        "html": """<p>Smith, J. A. (2023). Advances in computer vision techniques. <em>IEEE/CVF Conference on Computer Vision and Pattern Recognition</em>.Johnson, M. R., Davis, S. L., & Thompson, A. K. (2022). Remote learning effectiveness during COVID-19: A meta-analysis. <em>Review of Educational Research</em>, 92(3), 412-445. https://doi.org/10.3102/00346543221075623</p>
<p></p>
<p>Garcia, E. M. (2021). Nurse burnout and patient safety: The mediating role of working conditions. <em>Journal of Nursing Administration</em>, 51(7), 389-395. https://doi.org/10.1097/NNA.0000000000001015</p>""",
        "expected": 3  # Should detect 3, but will likely detect 2
    }
]

# Run all tests
print("\n" + "█" * 80)
print("BACKEND INVESTIGATION SUITE")
print("█" * 80 + "\n")

results = []
for scenario in scenarios:
    passed = test_scenario(scenario["name"], scenario["html"], scenario["expected"])
    results.append((scenario["name"], passed))
    print("\n" + "-" * 80 + "\n")

# Summary
print("\n" + "█" * 80)
print("TEST RESULTS SUMMARY")
print("█" * 80 + "\n")

for name, passed in results:
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {name}")

passing = sum(1 for _, p in results if p)
print(f"\n📊 {passing}/{len(results)} tests passing")

if passing < len(results):
    print("\n🔍 NEXT STEPS:")
    print("1. If scenario 1 fails: Citations need intelligent splitting")
    print("2. If scenario 2 fails: HTMLToTextConverter issue with <p> tags")
    print("3. If scenario 4 fails: Confirms need for smart splitting")
    print("\n💡 RECOMMENDATION:")
    print("   → Use LLM-based citation separation in validation prompt")
else:
    print("\n✅ All scenarios pass - issue might be in actual frontend HTML generation")
