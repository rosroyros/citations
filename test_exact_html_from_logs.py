"""Test with EXACT HTML from the real request logs."""
import sys
sys.path.insert(0, '/Users/roy/Documents/Projects/citations/backend')

from app import html_to_text_with_formatting
from prompt_manager import PromptManager

# EXACT HTML from your real request (from logs)
real_html = """<p>Adli, A. (2013). Syntactic variation in French Wh-questions: A quantitative study from the angle of Bourdieu's sociocultural theory. <em>Linguistics</em>, <em>51</em>(3), 473-515.</p><p>Agarwal, D., Naaman, M., &amp; Vashistha, A. (2025, April). AI suggestions homogenize writing toward western styles and diminish cultural nuances. In <em>Proceedings of the 2025 CHI Conference on Human Factors in Computing Systems</em> (pp. 1-21).</p><p>Airoldi, M. (2021). <em>Machine habitus: Toward a sociology of algorithms</em>. John Wiley &amp; Sons.</p><p>Airoldi 2022</p><p>Ajunwa, I. (2020). The "black box" at work. <em>Big Data &amp; Society</em>, <em>7</em>(2), 2053951720966181.</p><p>Ajunwa, I. (2023). <em>The quantified worker: Law and technology in the modern workplace</em>. Cambridge University Press.</p><p>Alvero, A. J., Pal, J., &amp; Moussavian, K. M. (2022). Linguistic, cultural, and narrative capital: computational and human readings of transfer admissions essays. <em>Journal of Computational Social Science</em>, <em>5</em>(2), 1709-1734.</p><p>Alvero, A. J., Lee, J., Regla-Vargas, A., Kizilcec, R. F., Joachims, T., &amp; Antonio, A. L. (2024). Large language models, social demography, and hegemony: comparing authorship in human and synthetic text. <em>Journal of Big Data</em>, <em>11</em>(1), 138.</p><p>Angwin, J., Larson, J., Mattu, S. and Kirchner, L. (2016) 'Machine bias', ProPublica, 23 May 2016, <a target="_blank" rel="noopener noreferrer nofollow" href="https://bit.ly/2NubAFX">https://bit.ly/2NubAFX</a>.</p>"""

print("=" * 80)
print("EXACT HTML FROM YOUR REAL REQUEST")
print("=" * 80)
print(f"\nHTML structure:")
print(f"  - 9 <p> tags")
print(f"  - 0 empty <p></p> tags")
print(f"  - Tags are consecutive: </p><p> with no space/newline between")

print("\n" + "=" * 80)
print("STEP 1: HTMLToTextConverter")
print("=" * 80)

text = html_to_text_with_formatting(real_html)
print(f"\nConverted text ({len(text)} chars):")
print(repr(text))

print("\n" + "=" * 80)
print("STEP 2: Analyze line structure")
print("=" * 80)

lines = text.split('\n')
print(f"\nTotal lines after split('\\n'): {len(lines)}")
for i, line in enumerate(lines):
    if line.strip():
        print(f"  Line {i}: [TEXT] {line[:60]}...")
    else:
        print(f"  Line {i}: [BLANK]")

print("\n" + "=" * 80)
print("STEP 3: format_citations() logic simulation")
print("=" * 80)

citations = []
current_citation = []

for i, line in enumerate(lines):
    line_stripped = line.strip()
    if not line_stripped:  # Blank line
        if current_citation:
            citations.append(' '.join(current_citation))
            print(f"  Line {i} is blank → End citation #{len(citations)}")
            current_citation = []
    else:  # Non-blank line
        current_citation.append(line_stripped)
        print(f"  Line {i} has text → Add to current citation")

# Don't forget last citation
if current_citation:
    citations.append(' '.join(current_citation))
    print(f"  End of input → Final citation #{len(citations)}")

print(f"\n🔍 RESULT: {len(citations)} citation(s) detected")
print(f"📋 EXPECTED: 9 citations")

if len(citations) == 1:
    print("\n❌ All citations were MERGED into one!")
    print("\n🤔 WHY?")
    print("   Because there are NO blank lines between citations.")
    print("   format_citations() only splits on blank lines.")

print("\n" + "=" * 80)
print("ROOT CAUSE ANALYSIS")
print("=" * 80)

print("\nHTMLToTextConverter behavior:")
print("  <p>Text1</p><p>Text2</p>")
print("  ↓ handle_starttag('p') on first <p>")
print("    → Adds \\n if needed (line 53-54)")
print("  ↓ handle_data('Text1')")
print("    → Adds 'Text1'")
print("  ↓ handle_endtag('p') on first </p>")
print("    → Adds \\n (line 67)")
print("  ↓ handle_starttag('p') on second <p>")
print("    → Adds \\n if needed (but last char IS \\n, so skips)")
print("  ↓ handle_data('Text2')")
print("  ↓ handle_endtag('p')")
print("    → Adds \\n")
print("\n  Result: '\\nText1\\n\\nText2\\n'")
print("          After .strip(): 'Text1\\n\\nText2'")
print("\n  ✅ Should have blank line between citations!")

print("\n🔍 So why does the real output show NO blank lines?")
print("   Let me check if there's a bug in the parser...")

# Actually parse it
print("\n" + "=" * 80)
print("ACTUAL PARSING TEST")
print("=" * 80)

pm = PromptManager()
formatted = pm.format_citations(text)
print(formatted)

detected = formatted.count('\n\n') + 1
print(f"\n📊 Detected: {detected} citation(s)")
print(f"📋 Expected: 9 citations")

if detected != 9:
    print(f"\n❌ BUG CONFIRMED: Only {detected} citation(s) detected instead of 9")
