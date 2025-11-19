# Prompt Fixes with APA 7 Verification

**CRITICAL NOTE**: All fixes must be verified against official APA 7 guidelines before implementation.

---

## Fix 1: Conference Presentations - DOI/URL Formats

### Error Case #1
```
Evans, A. C., Jr., Garbarino, J., Bocanegra, E., Kinscherff, R. T., &
Márquez-Greene, N. (2019, August 8–11). Gun violence: An event on the
power of community [Conference presentation]. APA 2019 Convention,
Chicago, IL, USA. doi:10.1037/con2019-1234
```
- **Ground Truth**: VALID
- **Model Predicted**: INVALID
- **Issue**: Model rejects bare DOI format `doi:10.xxxx`

### Error Case #2
```
Cacioppo, S. (2019, April 25–28). Evolutionary theory of social
connections: Past, present, and future [Conference presentation abstract].
Ninety-ninth annual convention of the Western Psychological Association,
Pasadena, California, United States.
https://westernpsych.org/wp-content/uploads/2019/04/WPA-Program-2019-Final-2.pdf
```
- **Ground Truth**: VALID
- **Model Predicted**: INVALID
- **Issue**: Model may reject URL to conference materials

### APA 7 Verification NEEDED
**Official APA 7 Reference** (Publication Manual, 7th ed.):
- Section 10.5 (Conference Sessions and Presentations), p. XXX
- Example 75 (p. XXX) - Conference presentation with DOI

**Questions to Verify**:
1. ✓ Is bare `doi:` format acceptable, or must it be `https://doi.org/`?
2. ✓ Are URLs to conference programs/materials acceptable when DOI unavailable?
3. ✓ Is location format "Chicago, IL, USA" correct or should it be different?

**Action Required**: Check official APA 7 manual sections 10.5 before implementing

---

## Fix 2: "Article" Format for Journal Article Numbers

### Error Case #1
```
Jerrentrup, A., Mueller, T., Glowalla, U., & Schaefer, J. R. (2018).
Teaching medicine with the help of "Dr. House." PLoS ONE, 13(3),
Article e0193972. https://doi.org/10.1371/journal.pone.0193972
```
- **Ground Truth**: VALID
- **Model Predicted**: INVALID
- **Issue**: Model flags "Article e0193972" format

### Error Case #2
```
Jerrentrup, A., Mueller, T., Glowalla, U., Herder, M., & Henrichs, N. (2018).
Teaching medicine with the help of Dr. House. PLoS ONE, 13(3),
Article e0193972. https://doi.org/10.1371/journal.pone.0193972
```
- **Ground Truth**: VALID
- **Model Predicted**: INVALID
- **Issue**: Same "Article" format issue

### APA 7 Verification NEEDED
**Official APA 7 Reference**:
- Section 9.25 (Article Numbers), p. 295-296
- Example 1 (p. 316) - Journal article with article number

**From APA Style Blog**:
"When an article has an article number instead of a page range, include the word 'Article' and then the article number instead of the page range."

**Questions to Verify**:
1. ✓ Is "Article e0193972" the correct format?
2. ✓ Is "Article 0193972" (without the 'e') also acceptable?
3. ✓ Should there be italics on "Article" or the number?

**Action Required**: Confirm in APA Manual section 9.25 and example citations

---

## Fix 3: Classical/Ancient Works - Date Ranges

### Error Case #1
```
Plato (1989). Symposium (A. Nehamas & P. Woodruff, Trans.).
Hackett Publishing Company.
```
- **Ground Truth**: VALID
- **Model Predicted**: INVALID
- **Issue**: Missing original publication date?

### Error Case #2
```
Plato (1989). Symposium (A. Nehamas & P. Woodruff, Trans.).
Hackett Publishing Co. (Original work published 385-378 BCE)
```
- **Ground Truth**: VALID
- **Model Predicted**: INVALID
- **Issue**: Date range "385-378 BCE"?

### APA 7 Verification NEEDED
**Official APA 7 Reference**:
- Section 9.41 (Republished Works), p. 319-320
- Section 9.42 (Ancient Greek and Roman Works), p. 320

**Questions to Verify**:
1. ✓ Is original publication date required for ancient works?
2. ✓ Are date ranges (385-378 BCE) acceptable?
3. ✓ Is "ca." (circa) acceptable for approximate dates?
4. ✓ What's the correct format for BCE dates?

**Action Required**: Check APA Manual section 9.42 for classical works guidelines

---

## Fix 4: DOI Format Variations

### Error Case #1 (Bare DOI)
```
Evans, A. C., Jr., [...]. (2019, August 8–11). Gun violence [...]
[Conference presentation]. APA 2019 Convention, Chicago, IL, USA.
doi:10.1037/con2019-1234
```
- **Ground Truth**: VALID
- **Model Predicted**: INVALID
- **Issue**: Bare `doi:` format

### Error Case #2 (Simple numeric)
```
Ouellette, J. (2019, November 15). Physicists capture first footage of
quantum knots unraveling in superfluid. Ars Technica.
https://doi.org/10.1234/5678
```
- **Ground Truth**: VALID
- **Model Predicted**: INVALID
- **Issue**: Simple numeric DOI pattern

### Error Case #3 (Alphanumeric)
```
Armstrong, D. (2019). Malory and Character. In M. G. Leitch & C. J. Rushton
(Eds.), A new companion to Malory (pp. 144-163). D. S. Brewer.
https://doi.org/10.1234/abcd.5678
```
- **Ground Truth**: VALID
- **Model Predicted**: INVALID
- **Issue**: Alphanumeric DOI pattern

### APA 7 Verification NEEDED
**Official APA 7 Reference**:
- Section 9.34 (DOIs and URLs), p. 299-301
- From APA Manual: "DOIs begin with http://doi.org/ or https://doi.org/"

**Questions to Verify**:
1. ✓ Is bare `doi:10.xxxx` format acceptable or must use `https://doi.org/`?
2. ✓ What DOI suffix patterns are valid?
3. ✓ Can we validate DOIs or should we accept any format?

**CONCERN**: APA 7 may require `https://doi.org/` format, not bare `doi:`

**Action Required**:
- Check APA Manual section 9.34
- Check APA Style Blog for DOI format updates
- Verify if bare format is acceptable

---

## Additional Patterns Requiring Verification

### Pattern: Edition Abbreviations
```
American Psychiatric Association. (2000). Diagnostic and statistical
manual of mental disorders (4th ed., text rev.).
https://doi.org/10.1176/appi.books.9780890420249.dsm-iv-tr
```
- **Issue**: "text rev." abbreviation
- **Verify**: APA Manual section 9.30 (Edition) - is "text rev." standard?

### Pattern: Series with Volume Numbers
```
Kushilevitz, E., & Malkin, T. (Eds.). (2016). Lecture notes in computer
science: Vol. 9562. Theory of cryptography. Springer.
https://doi.org/10.1007/978-3-662-49096-9
```
- **Issue**: Series format with volume
- **Verify**: APA Manual section 9.29 (Book in Multivolume Work)

### Pattern: Retrieval Dates
```
Perreault, L. (2019). Obesity in adults: Role of physical activity and
exercise. UpToDate. Retrieved January 12, 2020, from
https://www.uptodate.com/contents/obesity-in-adults-role-of-physical-activity-and-exercise
```
- **Issue**: Retrieval date for UpToDate
- **Verify**: APA Manual section 9.16 (Works with Specific Publication Dates vs. No Date)
- **Likely VALID**: Retrieval dates required for content that changes over time

---

## CRITICAL: What We DON'T Know

1. **Conference DOI format**: Bare `doi:` vs `https://doi.org/` - which is correct?
2. **Classical works**: Are date ranges acceptable? Is original date required?
3. **DOI validation**: Should we validate DOI patterns or accept any format?
4. **Article numbers**: Confirmed correct in APA 7, but need to verify exact format

---

## Recommended Next Steps

### Step 1: APA 7 Manual Verification (URGENT)
Manually check official APA 7 Publication Manual for:
- Section 9.25 (Article Numbers) - p. 295-296
- Section 9.34 (DOIs and URLs) - p. 299-301
- Section 9.42 (Classical Works) - p. 320
- Section 10.5 (Conference Presentations) - p. XXX

### Step 2: APA Style Blog Research
Check https://apastyle.apa.org/blog/ for:
- DOI format updates
- Conference presentation examples
- Article number clarifications

### Step 3: Cross-Reference with Ground Truth
For each error case:
1. Find official APA 7 example matching the pattern
2. Compare our citation to the example
3. Determine if ground truth is correct
4. Only then make prompt changes

### Step 4: Document Verification Results
Create verification table:

| Pattern | APA 7 Section | Example # | Verdict | Notes |
|---------|---------------|-----------|---------|-------|
| Article format | 9.25, p.295 | Example 1 | ✓ VALID | "Article XXXX" confirmed |
| Bare DOI | 9.34, p.299 | - | ? | Need to verify |
| Classical works | 9.42, p.320 | Example X | ? | Need to verify |

---

## IMPORTANT WARNING

**DO NOT implement any prompt fixes until APA 7 verification is complete.**

If our "ground truth" labels are incorrect (e.g., we marked `doi:10.xxxx` as valid when APA 7 requires `https://doi.org/`), then:
1. Our 82.6% accuracy may be misleading
2. Prompt fixes could make the model WORSE
3. We need to correct ground truth first

---

## Alternative Approach: Start with Confident Cases

Only make prompt changes for patterns where we are 100% confident of APA 7 compliance:

### HIGH CONFIDENCE (Verify First)
1. **Article format** - APA 7 explicitly covers this (section 9.25)
2. **Retrieval dates for UpToDate** - Well documented requirement

### MEDIUM CONFIDENCE (Verify Carefully)
3. **Classical works date ranges** - Need to check section 9.42
4. **Series with volumes** - Need to check section 9.29

### LOW CONFIDENCE (May Need Ground Truth Correction)
5. **Bare DOI format** - APA 7 may require `https://` format
6. **Conference presentation DOIs** - Need to verify format rules

---

## Files for APA 7 Verification Team

All error cases available in:
- `ERROR_CASES_FOR_REVIEW.txt` - All 21 citations
- `MANUAL_ERROR_PATTERN_ANALYSIS.md` - Detailed pattern analysis

**Next Action**: Manual APA 7 verification session before implementing any changes.
