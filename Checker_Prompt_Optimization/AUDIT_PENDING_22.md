# Ground Truth Audit Worksheet

## Summary
- **Total errors**: 27
- **Already audited**: 5 (all confirmed as ground truth errors)
- **Pending audit**: 22

## Already Audited (5 Ground Truth Errors Found)

✅ **Error #1**: GT says VALID, should be INVALID - Book title should be sentence case  
✅ **Error #12**: GT says VALID, should be INVALID - Article title incorrectly italicized  
✅ **Error #21**: GT says VALID, should be INVALID - Missing comma in author name  
✅ **Error #24**: GT says VALID, should be INVALID - Article title should be sentence case  
✅ **Error #25**: GT says VALID, should be INVALID - Article title incorrectly italicized  

**Impact**: If these 5 are fixed, accuracy improves from 77.7% → 82.6%

---

## Pending Audit (22 Errors)

Instructions: For each error below, verify against APA 7 manual and mark as:
- **GT_CORRECT**: Ground truth is correct, model made an error
- **GT_ERROR**: Ground truth is wrong, model was correct
- **AMBIGUOUS**: APA 7 rule is unclear or edge case

---

### False Positives (17 to audit)
Model says INVALID, ground truth says VALID

#### Error #2 (SYNTHETIC)

**Citation**:
```
joachimr., & smithj. (2019, November 19). We are relying on APA as our university style format - the university is located in Germany (Kassel). So I [Comment on the blog post “The transition to seventh edition APA Style”]. _APA Style_. https://apastyle.apa.org/blog/transition-seventh-edition#comment-4694866690
```

**Current labels**:
- Ground Truth: VALID
- Model Prediction: INVALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
joachimr., & smithj. (2019, November 19). We are relying on APA as our university style format - the university is located in Germany (Kassel). So I [Comment on the blog post “The transition to seventh edition APA Style”]. _APA Style_. https://apastyle.apa.org/blog/transition-seventh-edition#comment-4694866690

SOURCE TYPE:...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

#### Error #3 (SYNTHETIC)

**Citation**:
```
Evans, A. C., Jr., Garbarino, J., Bocanegra, E., Kinscherff, R. T., & Márquez-Greene, N. (2019, August 8–11). _Gun violence: An event on the power of community_ [Conference presentation]. APA 2019 Convention, Chicago, IL, USA. doi:10.1037/con2019-1234
```

**Current labels**:
- Ground Truth: VALID
- Model Prediction: INVALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Evans, A. C., Jr., Garbarino, J., Bocanegra, E., Kinscherff, R. T., & Márquez-Greene, N. (2019, August 8–11). _Gun violence: An event on the power of community_ [Conference presentation]. APA 2019 Convention, Chicago, IL, USA. doi:10.1037/con2019-1234

SOURCE TYPE: Conference presentation

VALIDATION RESULTS:

❌ Title forma...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

#### Error #4 (MANUAL/ORIGINAL)

**Citation**:
```
Joly, J. F., Stapel, D. A., & Lindenberg, S. M. (2008). Silence and table manners: When environments activate norms. _Personality and Social Psychology Bulletin_, _34_(8), 1047–1056. https://doi.org/10.1177/0146167208318401(Retraction published 2012, _Personality and Social Psychology Bulletin, 38_[10], 1378)
```

**Current labels**:
- Ground Truth: VALID
- Model Prediction: INVALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Joly, J. F., Stapel, D. A., & Lindenberg, S. M. (2008). Silence and table manners: When environments activate norms. _Personality and Social Psychology Bulletin_, _34_(8), 1047–1056. https://doi.org/10.1177/0146167208318401(Retraction published 2012, _Personality and Social Psychology Bulletin, 38_[10], 1378)

SOURCE TYPE: ...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

#### Error #5 (SYNTHETIC)

**Citation**:
```
U.S. Department of the Interior. (2020, January 10). _Like frosting on a cake, snow coats and clings to the hoodoos at Bryce Canyon National Park in Utah_ [Image attached] [Status update]. Facebook. Retrieved from https://www.facebook.com/USInterior/photos/a.155163054537384/2586475451406120/?type=3&theater
```

**Current labels**:
- Ground Truth: VALID
- Model Prediction: INVALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
U.S. Department of the Interior. (2020, January 10). _Like frosting on a cake, snow coats and clings to the hoodoos at Bryce Canyon National Park in Utah_ [Image attached] [Status update]. Facebook. Retrieved from https://www.facebook.com/USInterior/photos/a.155163054537384/2586475451406120/?type=3&theater

SOURCE TYPE: web...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

#### Error #6 (SYNTHETIC)

**Citation**:
```
Cacioppo, S. (2019, April 25–28). _Evolutionary theory of social connections: Past, present, and future_ [Conference presentation abstract]. Ninety-ninth annual convention of the Western Psychological Association, Pasadena, California, United States. https://westernpsych.org/wp-content/uploads/2019/04/WPA-Program-2019-Final-2.pdf
```

**Current labels**:
- Ground Truth: VALID
- Model Prediction: INVALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Cacioppo, S. (2019, April 25–28). _Evolutionary theory of social connections: Past, present, and future_ [Conference presentation abstract]. Ninety-ninth annual convention of the Western Psychological Association, Pasadena, California, United States. https://westernpsych.org/wp-content/uploads/2019/04/WPA-Program-2019-Final...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

#### Error #7 (MANUAL/ORIGINAL)

**Citation**:
```
Duckworth, A. L., Quirk, A., Gallop, R., Hoyle, R. H., Kelly, D. R., & Matthews, M. D. (2019). Cognitive and noncognitive predictors of success. _Proceedings of the National Academy of Sciences_, _USA_, _116_(47), 23499–23504. https://doi.org/10.1073/pnas.1910510116
```

**Current labels**:
- Ground Truth: VALID
- Model Prediction: INVALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Duckworth, A. L., Quirk, A., Gallop, R., Hoyle, R. H., Kelly, D. R., & Matthews, M. D. (2019). Cognitive and noncognitive predictors of success. _Proceedings of the National Academy of Sciences_, _USA_, _116_(47), 23499–23504. https://doi.org/10.1073/pnas.1910510116

SOURCE TYPE: journal article

VALIDATION RESULTS:

❌ Jour...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

#### Error #8 (MANUAL/ORIGINAL)

**Citation**:
```
Kushilevitz, E., & Malkin, T. (Eds.). (2016). _Lecture notes in computer science: Vol. 9562. Theory of cryptography_. Springer. https://doi.org/10.1007/978-3-662-49096-9
```

**Current labels**:
- Ground Truth: VALID
- Model Prediction: INVALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Kushilevitz, E., & Malkin, T. (Eds.). (2016). _Lecture notes in computer science: Vol. 9562. Theory of cryptography_. Springer. https://doi.org/10.1007/978-3-662-49096-9

SOURCE TYPE: book (edited volume in a series)

VALIDATION RESULTS:

❌ Title / Series formatting and order: The series title and volume are presented as pa...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

#### Error #10 (MANUAL/ORIGINAL)

**Citation**:
```
American Psychiatric Association. (2000). _Diagnostic and statistical manual of mental disorders_ (4th ed., text rev.). https://doi.org/10.1176/appi.books.9780890420249.dsm-iv-tr
```

**Current labels**:
- Ground Truth: VALID
- Model Prediction: VALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
American Psychiatric Association. (2000). _Diagnostic and statistical manual of mental disorders_ (4th ed., text rev.). https://doi.org/10.1176/appi.books.9780890420249.dsm-iv-tr

SOURCE TYPE: book

VALIDATION RESULTS:

✓ No APA 7 formatting errors detected

Notes: The corporate author is the same as the publisher for this ...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

#### Error #11 (MANUAL/ORIGINAL)

**Citation**:
```
Thestrup, K. (2010). To transform, to communicate, to play—The experimenting community in action. In E. Hygum & P. M. Pedersen (Eds.), _Early childhood education: Values and practices in Denmark_. Hans Reitzels Forlag. https://earlychildhoodeducation.digi.hansreitzel.dk/?id=192
```

**Current labels**:
- Ground Truth: VALID
- Model Prediction: INVALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Thestrup, K. (2010). To transform, to communicate, to play—The experimenting community in action. In E. Hygum & P. M. Pedersen (Eds.), _Early childhood education: Values and practices in Denmark_. Hans Reitzels Forlag. https://earlychildhoodeducation.digi.hansreitzel.dk/?id=192

SOURCE TYPE: book chapter (chapter in an edit...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

#### Error #13 (SYNTHETIC)

**Citation**:
```
Jerrentrup, A., Mueller, T., Glowalla, U., & Schaefer, J. R. (2018). Teaching medicine with the help of “Dr. House.” _PLoS ONE_, _13_(3), Article e0193972. https://doi.org/10.1371/journal.pone.0193972
```

**Current labels**:
- Ground Truth: VALID
- Model Prediction: VALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Jerrentrup, A., Mueller, T., Glowalla, U., & Schaefer, J. R. (2018). Teaching medicine with the help of “Dr. House.” _PLoS ONE_, _13_(3), Article e0193972. https://doi.org/10.1371/journal.pone.0193972

SOURCE TYPE: journal article

VALIDATION RESULTS:

✓ No APA 7 formatting errors detected...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

#### Error #15 (SYNTHETIC)

**Citation**:
```
Armstrong, D. (2019). Malory and Character. In M. G. Leitch & C. J. Rushton (Eds.), _A new companion to Malory_ (pp. 144-163). D. S. Brewer. https://doi.org/10.1234/abcd.5678
```

**Current labels**:
- Ground Truth: VALID
- Model Prediction: INVALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Armstrong, D. (2019). Malory and Character. In M. G. Leitch & C. J. Rushton (Eds.), _A new companion to Malory_ (pp. 144-163). D. S. Brewer. https://doi.org/10.1234/abcd.5678

SOURCE TYPE: book chapter

VALIDATION RESULTS:

❌ Title (chapter): Incorrect capitalization
   What’s wrong: Chapter titles in APA 7 should be in sen...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

#### Error #16 (SYNTHETIC)

**Citation**:
```
Schulman, M. (2019, September 9). _Superfans: A love story_. _The New Yorker_. https://doi.org/10.1000/xyz456
```

**Current labels**:
- Ground Truth: VALID
- Model Prediction: INVALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Schulman, M. (2019, September 9). _Superfans: A love story_. _The New Yorker_. https://doi.org/10.1000/xyz456

SOURCE TYPE: magazine article (online)

VALIDATION RESULTS:

❌ Title formatting: The article title is italicized.
   Should be: The article title should be in sentence case and plain text (not italicized). 
   Exam...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

#### Error #17 (SYNTHETIC)

**Citation**:
```
National Cancer Institute. (2019). _Taking time_: Support for people with cancer (NIH Publication No. 18-2059). U.S. Department of Health and Human Services, National Institutes of Health. https://www.cancer.gov/publications/patient-education/takingtime.pdf
```

**Current labels**:
- Ground Truth: VALID
- Model Prediction: INVALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
National Cancer Institute. (2019). _Taking time_: Support for people with cancer (NIH Publication No. 18-2059). U.S. Department of Health and Human Services, National Institutes of Health. https://www.cancer.gov/publications/patient-education/takingtime.pdf

SOURCE TYPE: other (government report)

VALIDATION RESULTS:

❌ Tit...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

#### Error #19 (MANUAL/ORIGINAL)

**Citation**:
```
Perreault, L. (2019). Obesity in adults: Role of physical activity and exercise. _UpToDate_. Retrieved January 12, 2020, from https://www.uptodate.com/contents/obesity-in-adults-role-of-physical-activity-and-exercise
```

**Current labels**:
- Ground Truth: VALID
- Model Prediction: INVALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Perreault, L. (2019). Obesity in adults: Role of physical activity and exercise. _UpToDate_. Retrieved January 12, 2020, from https://www.uptodate.com/contents/obesity-in-adults-role-of-physical-activity-and-exercise

SOURCE TYPE: webpage

VALIDATION RESULTS:

❌ Date: Incomplete date
   What’s wrong: The entry lists only th...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

#### Error #22 (MANUAL/ORIGINAL)

**Citation**:
```
Agency for Toxic Substances and Disease Registry. (n.d.). _Asbestos in your environment: What you can do to limit exposure_ [Fact sheet]. U.S. Department of Health & Human Services. https://www.atsdr.cdc.gov/docs/limitingenvironmentalexposures_factsheet-508.pdf
```

**Current labels**:
- Ground Truth: VALID
- Model Prediction: INVALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Agency for Toxic Substances and Disease Registry. (n.d.). _Asbestos in your environment: What you can do to limit exposure_ [Fact sheet]. U.S. Department of Health & Human Services. https://www.atsdr.cdc.gov/docs/limitingenvironmentalexposures_factsheet-508.pdf

SOURCE TYPE: webpage (government fact sheet)

VALIDATION RESUL...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

#### Error #26 (SYNTHETIC)

**Citation**:
```
Agency for Toxic Substances and Disease Registry. (n.d.). _Asbestos in your environment: What you can do to limit exposure_ [Fact sheet]. U.S. Department of Health & Human Services. doi:10.1234/atsdr.5678
```

**Current labels**:
- Ground Truth: VALID
- Model Prediction: INVALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Agency for Toxic Substances and Disease Registry. (n.d.). _Asbestos in your environment: What you can do to limit exposure_ [Fact sheet]. U.S. Department of Health & Human Services. doi:10.1234/atsdr.5678

SOURCE TYPE: webpage (government fact sheet)

VALIDATION RESULTS:

❌ DOI/Identifier format: The DOI is presented using ...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

#### Error #27 (SYNTHETIC)

**Citation**:
```
Ouellette, J. (2019, November 15). Physicists capture first footage of quantum knots unraveling in superfluid. _Ars Technica_. https://doi.org/10.1234/5678
```

**Current labels**:
- Ground Truth: VALID
- Model Prediction: VALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Ouellette, J. (2019, November 15). Physicists capture first footage of quantum knots unraveling in superfluid. _Ars Technica_. https://doi.org/10.1234/5678

SOURCE TYPE: web page (news article)

VALIDATION RESULTS:

✓ No APA 7 formatting errors detected

──────────────────────────────────────────────────────────────────────...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---


### False Negatives (5 to audit)
Model says VALID, ground truth says INVALID

#### Error #9 (SYNTHETIC)

**Citation**:
```
Miranda, C., & Smith, J. (2019). _Exploring the lived experiences of foster youth who obtained graduate level degrees: Self-efficacy, resilience, and the impact on identity development_. (Publication No. 27542827) [Doctoral dissertation, Pepperdine University] PQDT Open. https://pqdtopen.proquest.com/doc/2309521814.html
```

**Current labels**:
- Ground Truth: INVALID
- Model Prediction: VALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Miranda, C., & Smith, J. (2019). _Exploring the lived experiences of foster youth who obtained graduate level degrees: Self-efficacy, resilience, and the impact on identity development_. (Publication No. 27542827) [Doctoral dissertation, Pepperdine University] PQDT Open. https://pqdtopen.proquest.com/doc/2309521814.html

SO...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

#### Error #14 (SYNTHETIC)

**Citation**:
```
Cacioppo, S. (2019, April 25-28). Evolutionary theory of social connections: Past, present, and future [Conference presentation abstract]. Ninety-ninth annual convention of the Western Psychological Association, Pasadena, CA. https://westernpsych.org/wp-content/uploads/2019/04/WPA-Program-2019-Final-2.pdf
```

**Current labels**:
- Ground Truth: INVALID
- Model Prediction: INVALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Cacioppo, S. (2019, April 25-28). Evolutionary theory of social connections: Past, present, and future [Conference presentation abstract]. Ninety-ninth annual convention of the Western Psychological Association, Pasadena, CA. https://westernpsych.org/wp-content/uploads/2019/04/WPA-Program-2019-Final-2.pdf

SOURCE TYPE: Conf...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

#### Error #18 (SYNTHETIC)

**Citation**:
```
Carey, B. (2019, March 22). Can we get better at forgetting? _The New York Times._ https://www.nytimes.com/2019/03/22/health/memory-forgetting-psychology.html
```

**Current labels**:
- Ground Truth: INVALID
- Model Prediction: VALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Carey, B. (2019, March 22). Can we get better at forgetting? _The New York Times._ https://www.nytimes.com/2019/03/22/health/memory-forgetting-psychology.html

SOURCE TYPE: webpage (newspaper article)

VALIDATION RESULTS:

✓ No APA 7 formatting errors detected

───────────────────────────────────────────────────────────────...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

#### Error #20 (SYNTHETIC)

**Citation**:
```
Schlesselmann, A. J., & Held, P. (2025). Using network analysis to characterize clinical improvement during cognitive processing therapy. _Behaviour Research and Therapy, 185_, Article 104678. https://doi.org/10.1016/j.brat.2024.104678
```

**Current labels**:
- Ground Truth: INVALID
- Model Prediction: VALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Schlesselmann, A. J., & Held, P. (2025). Using network analysis to characterize clinical improvement during cognitive processing therapy. _Behaviour Research and Therapy, 185_, Article 104678. https://doi.org/10.1016/j.brat.2024.104678

SOURCE TYPE: journal article

VALIDATION RESULTS:

✓ No APA 7 formatting errors detected...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

#### Error #23 (SYNTHETIC)

**Citation**:
```
Baral, P., Larsen, M., Archer, M., & Johnson, T. (2019). _Does money grow on trees? Restoration financing in Southeast Asia_. Atlantic Council. https://www.atlanticcouncil.org/in-depth-research-reports/report/does-money-grow-on-trees-restoring-financing-in-southeast-asia/
```

**Current labels**:
- Ground Truth: INVALID
- Model Prediction: INVALID

**Model's reasoning** (truncated):
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Baral, P., Larsen, M., Archer, M., & Johnson, T. (2019). _Does money grow on trees? Restoration financing in Southeast Asia_. Atlantic Council. https://www.atlanticcouncil.org/in-depth-research-reports/report/does-money-grow-on-trees-restoring-financing-in-southeast-asia/

SOURCE TYPE: webpage (online report)

VALIDATION RE...
```

**Audit decision**: [ ] GT_CORRECT  [ ] GT_ERROR  [ ] AMBIGUOUS

**Notes**:


---

