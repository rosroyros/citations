# Manual Error Pattern Analysis: GPT-5-mini_optimized

## Summary

- Total errors: 21
- False positives (too strict): 16 (76%)
- False negatives (too lenient): 5 (24%)

**Primary Issue**: Model incorrectly flags VALID citations as invalid

---

## FALSE POSITIVE PATTERNS (16 cases - Model too strict)

### Pattern 1: Conference Presentations with DOI (2 cases)

**Cases**:
- FP#2: Evans et al. - uses `doi:10.1037/con2019-1234` (bare DOI without https://)
- FP#3: Cacioppo - URL instead of DOI

**Issue**: Model may be incorrectly flagging conference presentations that use either:
  - Bare DOI format (`doi:10.1037/...`) instead of URL format
  - Regular URLs for conference materials

**APA 7 Rule**: Both formats are acceptable for conference presentations
  - DOI preferred when available (can use bare `doi:` format)
  - URL acceptable for conference materials/abstracts

**Prompt Fix**: Add clarification that conference presentations can use:
  - Bare DOI format: `doi:10.xxxx/xxxxx`
  - URL to conference program/materials

---

### Pattern 2: Abbreviations in Journal Titles (1 case)

**Cases**:
- FP#4: "Proceedings of the National Academy of Sciences, _USA_"

**Issue**: `USA` is italicized along with journal title

**APA 7 Rule**: Abbreviations like USA that are part of the journal name ARE italicized with the title

**Prompt Fix**: Clarify that common abbreviations (USA, UK, etc.) within journal titles should be italicized

---

### Pattern 3: Series Information with Volume Numbers (1 case)

**Cases**:
- FP#5: "Lecture notes in computer science: Vol. 9562."

**Issue**: Series title with volume number in specific format

**APA 7 Rule**: This is correct format for numbered book series

**Prompt Fix**: Add example of series with volume numbers: "_Series title: Vol. XXX. Book title_"

---

### Pattern 4: Ancient/Classical Works with Date Ranges (2 cases)

**Cases**:
- FP#6: Plato (1989) - no original date
- FP#10: Plato (1989) - WITH original date range "(Original work published 385-378 BCE)"

**Issue**: Model may be inconsistently handling:
  - Ancient works without original publication date
  - Date ranges for classical works (385-378 BCE)

**APA 7 Rule**:
  - Original publication date is recommended but not required
  - Date ranges are acceptable for ancient works

**Prompt Fix**: Add exception for classical/ancient works:
  - Date ranges acceptable (e.g., "385-378 BCE")
  - Original publication date recommended but optional

---

### Pattern 5: Edition Abbreviations (1 case)

**Cases**:
- FP#7: "(4th ed., text rev.)" - "text rev." abbreviation

**Issue**: "text rev." may be flagged as non-standard abbreviation

**APA 7 Rule**: "text rev." is standard APA abbreviation for "text revision"

**Prompt Fix**: Add "text rev." to list of accepted edition abbreviations

---

### Pattern 6: Non-English Publisher URLs (1 case)

**Cases**:
- FP#8: Hans Reitzels Forlag with Danish URL (earlychildhoodeducation.digi.hansreitzel.dk)

**Issue**: Non-English publisher with international domain

**APA 7 Rule**: International publishers and non-.com/.org/.edu domains are valid

**Prompt Fix**: Clarify that non-English publishers and international TLDs are acceptable

---

### Pattern 7: "Article" Format in Journal Citations (2 cases)

**Cases**:
- FP#9: "Article e0193972" - with period and italics around journal name
- FP#12: "Article e0193972" - no period after journal name

**Issue**: Both use "Article eXXXXX" format which is correct APA 7

**APA 7 Rule**: "Article XXXXXX" is preferred format for article numbers

**Prompt Fix**: Reinforce that "Article XXXXXX" format is CORRECT and preferred

---

### Pattern 8: Book Chapter DOIs with Numeric Format (1 case)

**Cases**:
- FP#11: Armstrong chapter with https://doi.org/10.1234/abcd.5678

**Issue**: May be incorrectly validating DOI format

**APA 7 Rule**: DOI format varies; this is a valid structure

**Prompt Fix**: Relax DOI validation - accept various numeric/alphanumeric formats

---

### Pattern 9: Government Reports with Publication Numbers (1 case)

**Cases**:
- FP#13: "(NIH Publication No. 18-2059)" with multi-level government agency

**Issue**: Publication number format with nested agency structure

**APA 7 Rule**: This is correct format for government publications

**Prompt Fix**: Add examples of government publications with:
  - Publication numbers
  - Multi-level agency hierarchies (Institute > Department > Agency)

---

### Pattern 10: Database/Reference Work Entries with Retrieval Dates (1 case)

**Cases**:
- FP#14: UpToDate with "Retrieved January 12, 2020, from"

**Issue**: Model may incorrectly handle regularly updated reference works

**APA 7 Rule**: Retrieval dates ARE required for works that change over time (UpToDate, wikis, etc.)

**Prompt Fix**: Clarify retrieval dates are REQUIRED for:
  - Regularly updated databases (UpToDate, Cochrane, etc.)
  - Works without publication date or frequently updated

---

### Pattern 11: Fact Sheets with (n.d.) and Brackets (1 case)

**Cases**:
- FP#15: "(n.d.)" with "[Fact sheet]" designation and multi-level agency

**Issue**: Combination of (n.d.), bracketed description, and agency hierarchy

**APA 7 Rule**: All elements are correct per APA 7

**Prompt Fix**: Add example combining (n.d.) + [Fact sheet] + multi-level agency

---

### Pattern 12: Blog/News Articles with Non-Standard DOIs (1 case)

**Cases**:
- FP#16: Ars Technica with https://doi.org/10.1234/5678 (appears to be test/placeholder DOI)

**Issue**: DOI format looks unusual (simple numeric)

**APA 7 Rule**: DOI format varies; if it resolves, it's valid

**Prompt Fix**: Accept any DOI format that follows https://doi.org/XX.XXXX/... structure

---

### Pattern 13: Blog Comments with Long Titles (1 case)

**Cases**:
- FP#1: Comment on blog post with long context in title

**Issue**: Long descriptive text in [Comment] brackets

**APA 7 Rule**: Descriptive context in brackets is acceptable

**Prompt Fix**: Allow longer descriptive text in brackets for blog comments/posts

---

## FALSE NEGATIVE PATTERNS (5 cases - Model too lenient)

### FN Pattern 1: Dissertation - Publication Number in Wrong Location (1 case)

**Case**: Miranda & Smith - "(Publication No. 27542827) [Doctoral dissertation, Pepperdine University]"

**Issue**: Publication number should come AFTER the bracketed description
  - Wrong: `(Publication No. X) [Doctoral dissertation, University]`
  - Correct: `[Doctoral dissertation, University]. (Publication No. X)`

**Prompt Fix**: Add rule - Publication numbers must appear AFTER bracketed description for dissertations

---

### FN Pattern 2: Conference Presentation - Missing State Abbreviation (1 case)

**Case**: Cacioppo - "Pasadena, CA" should be "Pasadena, CA, United States"

**Issue**: Uses state abbreviation but missing country when outside US context OR
  Should be "Pasadena, California, United States" (spell out state + country)

**APA 7 Rule**: For conferences, use "City, State, Country" (spell out state) or just "City, Country"

**Prompt Fix**: Strengthen location format rules for conferences:
  - Spell out state names (California not CA)
  - Include country for all conference locations

---

### FN Pattern 3: Newspaper Article - Extra Period Before URL (1 case)

**Case**: Carey - "_The New York Times._" (period after italics before URL)

**Issue**: Should be "_The New York Times_." (period outside italics) OR no period before URL

**APA 7 Rule**: No period directly before URL

**Prompt Fix**: Strengthen rule - no punctuation immediately before URLs

---

### FN Pattern 4: Journal Article - Missing Volume Italics (1 case)

**Case**: Schlesselmann & Held - "_Behaviour Research and Therapy, 185_"

**Issue**: Volume number (185) should not be italicized, only journal name

**APA 7 Rule**: Journal name italicized, volume number italicized, issue number NOT italicized

Wait - checking format: "_Journal Name, Volume_(Issue)"
The citation shows: "_Behaviour Research and Therapy, 185_" - volume IS italicized with comma, which is INCORRECT

**Prompt Fix**: Add rule - Volume must be separated from journal name, not included in italics with comma

---

### FN Pattern 5: Report - Incorrect URL Path (1 case)

**Case**: Baral et al. - "restoring-financing" should probably be "restoration-financing"

**Issue**: URL may have typo or formatting issue (hard to verify without checking actual URL)

**APA 7 Rule**: URLs must be accurate and resolvable

**Prompt Fix**: This is difficult to catch without URL validation. Consider adding note about URL verification.

---

## RECOMMENDED PROMPT CHANGES (Priority Order)

### High Priority (Fixes 8+ FP errors)

1. **Conference Presentations - Flexible Format**
   - Accept bare DOI format: `doi:10.xxxx/xxxxx`
   - Accept URLs to conference programs/materials
   - Examples: Conference with DOI, conference with URL

2. **"Article" Format - Reinforce Correctness**
   - Explicitly state "Article XXXXXX" is CORRECT and PREFERRED
   - Do not flag this as an error

3. **Classical/Ancient Works**
   - Date ranges acceptable (e.g., "385-378 BCE")
   - Original publication date optional for ancient works
   - Example: Plato, Aristotle, etc.

4. **DOI Format Flexibility**
   - Accept any format following https://doi.org/XX.XXXX/...
   - Accept bare `doi:` prefix format
   - Accept numeric, alphanumeric, mixed formats

### Medium Priority (Fixes 2-4 FP errors)

5. **Series with Volume Numbers**
   - Format: "_Series title: Vol. XXX. Book title_"
   - Example from Lecture Notes in Computer Science

6. **Retrieval Dates for Dynamic Content**
   - REQUIRED for regularly updated works (UpToDate, Cochrane, wikis)
   - Format: "Retrieved Month DD, YYYY, from URL"

7. **Complex Government Publications**
   - Multi-level agencies acceptable
   - Publication numbers: "(Agency Publication No. XX-XXXX)"
   - Example: NIH > DHHS structure

### Medium Priority - False Negatives (Prevent 5 FN errors)

8. **Dissertation Publication Numbers**
   - MUST appear after bracketed description
   - Wrong: `(Pub. No. X) [Dissertation, Univ]`
   - Correct: `[Dissertation, Univ]. (Publication No. X)`

9. **Conference Locations**
   - Spell out state names (California not CA)
   - Include country: "City, State, Country"

10. **Punctuation Before URLs**
    - NO period or comma immediately before URL
    - Check last character before https://

11. **Journal Volume Formatting**
    - Volume NOT included in italics with comma
    - Wrong: "_Journal Name, 185_"
    - Correct: "_Journal Name_, _185_"

### Low Priority (Edge cases - 1 error each)

12. **Text Revision Abbreviation**
    - "text rev." is valid abbreviation

13. **International Publishers/Domains**
    - Non-English publishers valid
    - International TLDs valid (.dk, .uk, etc.)

14. **Abbreviations in Journal Titles**
    - USA, UK, etc. are italicized with journal name

15. **Long Bracketed Descriptions**
    - Blog comments can have longer descriptive text in brackets

---

## ESTIMATED IMPACT

If we implement fixes for:
- **High Priority only**: Could fix ~10-12 FP errors = +8-10% accuracy
- **High + Medium Priority**: Could fix all 16 FP + 5 FN = +17% accuracy (99.6% total!)
- **Target**: Aim for High + Medium to reach **95%+ accuracy**

---

## NEXT STEPS

1. Update GPT-5-mini_optimized prompt with High Priority changes
2. Test on validation set
3. If not at 95%, add Medium Priority changes
4. Re-test until 95% achieved
