# Provenance Analysis: All 27 Validation Errors

**Purpose**: Show exact seed citations and alterations for each error to enable ground truth audit.

**Key Findings**:
- 8 Manual/Original citations (these ARE the seeds themselves)
- 19 Synthetic citations (17 with seeds found, 2 without)
- 22 False Positives (model says INVALID, ground truth says VALID - too strict)
- 5 False Negatives (model says VALID, ground truth says INVALID - too lenient)

---

## Error #1: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: INVALID | **Provenance**: SYNTHETIC

**Test Citation**:
```
David, A., Simpson, J., & Lee, C. (Eds.). (2006). _The Norton Anthology of English Literature: The Middle Ages_ (8th ed., Vol. A). W. W. Norton & Company.
```

**Provenance Issue**: Synthetic citation but seed not found.
- Seed ID: manual_1761231877393

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
David, A., Simpson, J., & Lee, C. (Eds.). (2006). _The Norton Anthology of English Literature: The Middle Ages_ (8th ed., Vol. A). W. W. Norton & Company.

SOURCE TYPE: book

VALIDATION RESULTS:

❌ Title: Incorrect capitalization (title case used)
   What’s wrong: APA 7 requires book titles in references to be in sentence case (capitalize only the first word of the title and subtitle and any proper nouns). The original uses title case for the whole title.
   Should be: _The Norton anthology of English literature: The Middle Ages_ (edition and volume info unchanged)

Corrected full citation example:
David, A., Simpson,...
```

**Metadata**:
- Source Type: unknown
- Metadata Source: synthetic_expansion
- Seed ID: manual_1761231877393

---

## Error #2: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: INVALID | **Provenance**: SYNTHETIC

**Test Citation**:
```
joachimr., & smithj. (2019, November 19). We are relying on APA as our university style format - the university is located in Germany (Kassel). So I [Comment on the blog post “The transition to seventh edition APA Style”]. _APA Style_. https://apastyle.apa.org/blog/transition-seventh-edition#comment-4694866690
```

**Seed → Synthetic Comparison**:

SEED (original manually curated):
```
joachimr. (2019, November 19). We are relying on APA as our university style format - the university is located in Germany (Kassel). So I [Comment on the blog post “The transition to seventh edition APA Style”]. _APA Style_. https://apastyle.apa.org/blog/transition-seventh-edition#comment-4694866690
```

SYNTHETIC (altered version being tested):
```
joachimr., & smithj. (2019, November 19). We are relying on APA as our university style format - the university is located in Germany (Kassel). So I [Comment on the blog post “The transition to seventh edition APA Style”]. _APA Style_. https://apastyle.apa.org/blog/transition-seventh-edition#comment-4694866690
```

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
joachimr., & smithj. (2019, November 19). We are relying on APA as our university style format - the university is located in Germany (Kassel). So I [Comment on the blog post “The transition to seventh edition APA Style”]. _APA Style_. https://apastyle.apa.org/blog/transition-seventh-edition#comment-4694866690

SOURCE TYPE: webpage (blog comment)

VALIDATION RESULTS:

❌ Authors: Incorrect formatting and capitalization
   What’s wrong: Authors are written in lowercase, include an extraneous period after "joachimr." and are not given as last name, initials (or presented as screen names in the correct form).
   Should be...
```

**Metadata**:
- Source Type: unknown
- Metadata Source: synthetic_expansion
- Seed ID: manual_1761231050431

---

## Error #3: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: INVALID | **Provenance**: SYNTHETIC

**Test Citation**:
```
Evans, A. C., Jr., Garbarino, J., Bocanegra, E., Kinscherff, R. T., & Márquez-Greene, N. (2019, August 8–11). _Gun violence: An event on the power of community_ [Conference presentation]. APA 2019 Convention, Chicago, IL, USA. doi:10.1037/con2019-1234
```

**Seed → Synthetic Comparison**:

SEED (original manually curated):
```
Evans, A. C., Jr., Garbarino, J., Bocanegra, E., Kinscherff, R. T., & Márquez-Greene, N. (2019, August 8–11). _Gun violence: An event on the power of community_ [Conference presentation]. APA 2019 Convention, Chicago, IL, United States. https://convention.apa.org/2019-video
```

SYNTHETIC (altered version being tested):
```
Evans, A. C., Jr., Garbarino, J., Bocanegra, E., Kinscherff, R. T., & Márquez-Greene, N. (2019, August 8–11). _Gun violence: An event on the power of community_ [Conference presentation]. APA 2019 Convention, Chicago, IL, USA. doi:10.1037/con2019-1234
```

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Evans, A. C., Jr., Garbarino, J., Bocanegra, E., Kinscherff, R. T., & Márquez-Greene, N. (2019, August 8–11). _Gun violence: An event on the power of community_ [Conference presentation]. APA 2019 Convention, Chicago, IL, USA. doi:10.1037/con2019-1234

SOURCE TYPE: Conference presentation

VALIDATION RESULTS:

❌ Title formatting: Title is italicized.
   Should be: Title in sentence case and not italicized (remove underscores/italics).
   Example: Gun violence: An event on the power of community

❌ DOI format: DOI is given as "doi:10.1037/con2019-1234".
   Should be: DOI presented as a URL beginning with https://doi.or...
```

**Metadata**:
- Source Type: unknown
- Metadata Source: synthetic_expansion
- Seed ID: manual_1761231306984

---

## Error #4: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: INVALID | **Provenance**: MANUAL/ORIGINAL

**Test Citation**:
```
Joly, J. F., Stapel, D. A., & Lindenberg, S. M. (2008). Silence and table manners: When environments activate norms. _Personality and Social Psychology Bulletin_, _34_(8), 1047–1056. https://doi.org/10.1177/0146167208318401(Retraction published 2012, _Personality and Social Psychology Bulletin, 38_[10], 1378)
```

**Provenance**: This IS the original manually curated seed citation (not synthetic).

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Joly, J. F., Stapel, D. A., & Lindenberg, S. M. (2008). Silence and table manners: When environments activate norms. _Personality and Social Psychology Bulletin_, _34_(8), 1047–1056. https://doi.org/10.1177/0146167208318401(Retraction published 2012, _Personality and Social Psychology Bulletin, 38_[10], 1378)

SOURCE TYPE: journal article

VALIDATION RESULTS:

❌ Other (Retraction note appended): The parenthetical "(Retraction published 2012, _Personality and Social Psychology Bulletin, 38_[10], 1378)" should not be appended to the original article citation. Retraction notices are cited as separate items in the referen...
```

**Metadata**:
- Source Type: journal article
- Metadata Source: manual_curation
- Seed ID: manual_1761230887067

---

## Error #5: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: INVALID | **Provenance**: SYNTHETIC

**Test Citation**:
```
U.S. Department of the Interior. (2020, January 10). _Like frosting on a cake, snow coats and clings to the hoodoos at Bryce Canyon National Park in Utah_ [Image attached] [Status update]. Facebook. Retrieved from https://www.facebook.com/USInterior/photos/a.155163054537384/2586475451406120/?type=3&theater
```

**Seed → Synthetic Comparison**:

SEED (original manually curated):
```
U.S. Department of the Interior. (2020, January 10). _Like frosting on a cake, snow coats and clings to the hoodoos at Bryce Canyon National Park in Utah_[Image attached] [Status update]. Facebook. https://www.facebook.com/USInterior/photos/a.155163054537384/2586475451406120/?type=3&theater
```

SYNTHETIC (altered version being tested):
```
U.S. Department of the Interior. (2020, January 10). _Like frosting on a cake, snow coats and clings to the hoodoos at Bryce Canyon National Park in Utah_ [Image attached] [Status update]. Facebook. Retrieved from https://www.facebook.com/USInterior/photos/a.155163054537384/2586475451406120/?type=3&theater
```

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
U.S. Department of the Interior. (2020, January 10). _Like frosting on a cake, snow coats and clings to the hoodoos at Bryce Canyon National Park in Utah_ [Image attached] [Status update]. Facebook. Retrieved from https://www.facebook.com/USInterior/photos/a.155163054537384/2586475451406120/?type=3&theater

SOURCE TYPE: webpage (social media post / Facebook status)

VALIDATION RESULTS:

❌ Title formatting: Title/content of the post is italicized.
   What’s wrong: Social media post content should be presented as plain text (not italicized).
   Should be: Like frosting on a cake, snow coats and clings to the hoodoos at ...
```

**Metadata**:
- Source Type: unknown
- Metadata Source: synthetic_expansion
- Seed ID: manual_1761231730212

---

## Error #6: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: INVALID | **Provenance**: SYNTHETIC

**Test Citation**:
```
Cacioppo, S. (2019, April 25–28). _Evolutionary theory of social connections: Past, present, and future_ [Conference presentation abstract]. Ninety-ninth annual convention of the Western Psychological Association, Pasadena, California, United States. https://westernpsych.org/wp-content/uploads/2019/04/WPA-Program-2019-Final-2.pdf
```

**Seed → Synthetic Comparison**:

SEED (original manually curated):
```
Cacioppo, S. (2019, April 25–28). _Evolutionary theory of social connections: Past, present, and future_ [Conference presentation abstract]. Ninety-ninth annual convention of the Western Psychological Association, Pasadena, CA, United States. https://westernpsych.org/wp-content/uploads/2019/04/WPA-Program-2019-Final-2.pdf
```

SYNTHETIC (altered version being tested):
```
Cacioppo, S. (2019, April 25–28). _Evolutionary theory of social connections: Past, present, and future_ [Conference presentation abstract]. Ninety-ninth annual convention of the Western Psychological Association, Pasadena, California, United States. https://westernpsych.org/wp-content/uploads/2019/04/WPA-Program-2019-Final-2.pdf
```

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Cacioppo, S. (2019, April 25–28). _Evolutionary theory of social connections: Past, present, and future_ [Conference presentation abstract]. Ninety-ninth annual convention of the Western Psychological Association, Pasadena, California, United States. https://westernpsych.org/wp-content/uploads/2019/04/WPA-Program-2019-Final-2.pdf

SOURCE TYPE: other (Conference presentation / abstract)

VALIDATION RESULTS:

❌ Title: Italicized when it should not be.
   What’s wrong: The presentation title is formatted in italics (underscores in the input).
   Should be: The title of a conference presentation (or abstract) is not itali...
```

**Metadata**:
- Source Type: unknown
- Metadata Source: synthetic_expansion
- Seed ID: manual_1761231314585

---

## Error #7: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: INVALID | **Provenance**: MANUAL/ORIGINAL

**Test Citation**:
```
Duckworth, A. L., Quirk, A., Gallop, R., Hoyle, R. H., Kelly, D. R., & Matthews, M. D. (2019). Cognitive and noncognitive predictors of success. _Proceedings of the National Academy of Sciences_, _USA_, _116_(47), 23499–23504. https://doi.org/10.1073/pnas.1910510116
```

**Provenance**: This IS the original manually curated seed citation (not synthetic).

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Duckworth, A. L., Quirk, A., Gallop, R., Hoyle, R. H., Kelly, D. R., & Matthews, M. D. (2019). Cognitive and noncognitive predictors of success. _Proceedings of the National Academy of Sciences_, _USA_, _116_(47), 23499–23504. https://doi.org/10.1073/pnas.1910510116

SOURCE TYPE: journal article

VALIDATION RESULTS:

❌ Journal title (and placement of "USA"): The entry separates "USA" as if it were a distinct, italicized element. APA does not include a separated "USA" after the journal title. Use the journal's full, official title or the commonly accepted title as one continuous italicized element. 
   Should be: _Proc...
```

**Metadata**:
- Source Type: journal article
- Metadata Source: manual_curation
- Seed ID: manual_1761231323585

---

## Error #8: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: INVALID | **Provenance**: MANUAL/ORIGINAL

**Test Citation**:
```
Kushilevitz, E., & Malkin, T. (Eds.). (2016). _Lecture notes in computer science: Vol. 9562. Theory of cryptography_. Springer. https://doi.org/10.1007/978-3-662-49096-9
```

**Provenance**: This IS the original manually curated seed citation (not synthetic).

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Kushilevitz, E., & Malkin, T. (Eds.). (2016). _Lecture notes in computer science: Vol. 9562. Theory of cryptography_. Springer. https://doi.org/10.1007/978-3-662-49096-9

SOURCE TYPE: book (edited volume in a series)

VALIDATION RESULTS:

❌ Title / Series formatting and order: The series title and volume are presented as part of the book title and are italicized. In APA 7 the book title alone should be italicized; the series title and volume number should follow the book title in parentheses (not italicized).
   Should be: The book title in italics, followed by the series information (not italicized) in parentheses. E...
```

**Metadata**:
- Source Type: book
- Metadata Source: manual_curation
- Seed ID: manual_1761231332267

---

## Error #9: FALSE_NEGATIVE

**Ground Truth**: INVALID | **Model Prediction**: VALID | **Provenance**: SYNTHETIC

**Test Citation**:
```
Miranda, C., & Smith, J. (2019). _Exploring the lived experiences of foster youth who obtained graduate level degrees: Self-efficacy, resilience, and the impact on identity development_. (Publication No. 27542827) [Doctoral dissertation, Pepperdine University] PQDT Open. https://pqdtopen.proquest.com/doc/2309521814.html
```

**Seed → Synthetic Comparison**:

SEED (original manually curated):
```
Miranda, C. (2019). _Exploring the lived experiences of foster youth who obtained graduate level degrees: Self-efficacy, resilience, and the impact on identity development_ (Publication No. 27542827) [Doctoral dissertation, Pepperdine University]. PQDT Open. https://pqdtopen.proquest.com/doc/2309521814.html?FMT=AI
```

SYNTHETIC (altered version being tested):
```
Miranda, C., & Smith, J. (2019). _Exploring the lived experiences of foster youth who obtained graduate level degrees: Self-efficacy, resilience, and the impact on identity development_. (Publication No. 27542827) [Doctoral dissertation, Pepperdine University] PQDT Open. https://pqdtopen.proquest.com/doc/2309521814.html
```

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Miranda, C., & Smith, J. (2019). _Exploring the lived experiences of foster youth who obtained graduate level degrees: Self-efficacy, resilience, and the impact on identity development_. (Publication No. 27542827) [Doctoral dissertation, Pepperdine University] PQDT Open. https://pqdtopen.proquest.com/doc/2309521814.html

SOURCE TYPE: dissertation

VALIDATION RESULTS:

✓ No APA 7 formatting errors detected

Notes:
- The authors, year, italicized title in sentence case, publication number, bracketed dissertation description with institution, database name (PQDT Open), and URL are all present and formatted according to A...
```

**Metadata**:
- Source Type: unknown
- Metadata Source: synthetic_expansion
- Seed ID: manual_1761231285037

---

## Error #10: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: VALID | **Provenance**: MANUAL/ORIGINAL

**Test Citation**:
```
American Psychiatric Association. (2000). _Diagnostic and statistical manual of mental disorders_ (4th ed., text rev.). https://doi.org/10.1176/appi.books.9780890420249.dsm-iv-tr
```

**Provenance**: This IS the original manually curated seed citation (not synthetic).

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
American Psychiatric Association. (2000). _Diagnostic and statistical manual of mental disorders_ (4th ed., text rev.). https://doi.org/10.1176/appi.books.9780890420249.dsm-iv-tr

SOURCE TYPE: book

VALIDATION RESULTS:

✓ No APA 7 formatting errors detected

Notes: The corporate author is the same as the publisher for this work, so omitting the publisher name is correct under APA 7. The DOI is correctly presented as a URL and is not followed by a period. The title is in sentence case and the edition information is correctly placed....
```

**Metadata**:
- Source Type: other
- Metadata Source: manual_curation
- Seed ID: manual_1761230443842

---

## Error #11: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: INVALID | **Provenance**: MANUAL/ORIGINAL

**Test Citation**:
```
Thestrup, K. (2010). To transform, to communicate, to play—The experimenting community in action. In E. Hygum & P. M. Pedersen (Eds.), _Early childhood education: Values and practices in Denmark_. Hans Reitzels Forlag. https://earlychildhoodeducation.digi.hansreitzel.dk/?id=192
```

**Provenance**: This IS the original manually curated seed citation (not synthetic).

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Thestrup, K. (2010). To transform, to communicate, to play—The experimenting community in action. In E. Hygum & P. M. Pedersen (Eds.), _Early childhood education: Values and practices in Denmark_. Hans Reitzels Forlag. https://earlychildhoodeducation.digi.hansreitzel.dk/?id=192

SOURCE TYPE: book chapter (chapter in an edited book)

VALIDATION RESULTS:

❌ Title (chapter): Incorrect sentence‑case formatting for the subtitle
   What’s wrong: The subtitle after the em dash is shown as "The experimenting community in action" with "The" capitalized. APA 7 uses sentence case for chapter titles (only the first word and prope...
```

**Metadata**:
- Source Type: book chapter
- Metadata Source: manual_curation
- Seed ID: manual_1761231079609

---

## Error #12: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: INVALID | **Provenance**: SYNTHETIC

**Test Citation**:
```
Smith, J. A., Baniya, S., & Weech, S. (2019). _Data and experience design: Negotiating community-oriented digital research with service-learning_. _Purdue Journal of Service-Learning and International Engagement, 6_(1), 11–16. https://doi.org/10.5703/1288284316979
```

**Seed → Synthetic Comparison**:

SEED (original manually curated):
```
Baniya, S., & Weech, S. (2019). Data and experience design: Negotiating community-oriented digital research with service-learning. _Purdue Journal of Service-Learning and International Engagement_,_ __6_(1), 11–16. https://doi.org/10.5703/1288284316979
```

SYNTHETIC (altered version being tested):
```
Smith, J. A., Baniya, S., & Weech, S. (2019). _Data and experience design: Negotiating community-oriented digital research with service-learning_. _Purdue Journal of Service-Learning and International Engagement, 6_(1), 11–16. https://doi.org/10.5703/1288284316979
```

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Smith, J. A., Baniya, S., & Weech, S. (2019). _Data and experience design: Negotiating community-oriented digital research with service-learning_. _Purdue Journal of Service-Learning and International Engagement, 6_(1), 11–16. https://doi.org/10.5703/1288284316979

SOURCE TYPE: journal article

VALIDATION RESULTS:

❌ Title (article): The article title is incorrectly italicized.
   What’s wrong: In an APA 7 journal reference, the article title should be in plain text (sentence case), not italicized.
   Should be: Data and experience design: Negotiating community-oriented digital research with service-learning.

(Everyt...
```

**Metadata**:
- Source Type: unknown
- Metadata Source: synthetic_expansion
- Seed ID: manual_1761231540482

---

## Error #13: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: VALID | **Provenance**: SYNTHETIC

**Test Citation**:
```
Jerrentrup, A., Mueller, T., Glowalla, U., & Schaefer, J. R. (2018). Teaching medicine with the help of “Dr. House.” _PLoS ONE_, _13_(3), Article e0193972. https://doi.org/10.1371/journal.pone.0193972
```

**Seed → Synthetic Comparison**:

SEED (original manually curated):
```
Jerrentrup, A., Mueller, T., Glowalla, U., Herder, M., Henrichs, N., Neubauer, A., & Schaefer, J. R. (2018). Teaching medicine with the help of “Dr. House.” _PLoS ONE_, _13_(3), Article e0193972. https://doi.org/10.1371/journal.pone.0193972
```

SYNTHETIC (altered version being tested):
```
Jerrentrup, A., Mueller, T., Glowalla, U., & Schaefer, J. R. (2018). Teaching medicine with the help of “Dr. House.” _PLoS ONE_, _13_(3), Article e0193972. https://doi.org/10.1371/journal.pone.0193972
```

**Model's Reasoning**:
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

**Metadata**:
- Source Type: unknown
- Metadata Source: synthetic_expansion
- Seed ID: manual_1761230839817

---

## Error #14: FALSE_NEGATIVE

**Ground Truth**: INVALID | **Model Prediction**: INVALID | **Provenance**: SYNTHETIC

**Test Citation**:
```
Cacioppo, S. (2019, April 25-28). Evolutionary theory of social connections: Past, present, and future [Conference presentation abstract]. Ninety-ninth annual convention of the Western Psychological Association, Pasadena, CA. https://westernpsych.org/wp-content/uploads/2019/04/WPA-Program-2019-Final-2.pdf
```

**Seed → Synthetic Comparison**:

SEED (original manually curated):
```
Cacioppo, S. (2019, April 25–28). _Evolutionary theory of social connections: Past, present, and future_ [Conference presentation abstract]. Ninety-ninth annual convention of the Western Psychological Association, Pasadena, CA, United States. https://westernpsych.org/wp-content/uploads/2019/04/WPA-Program-2019-Final-2.pdf
```

SYNTHETIC (altered version being tested):
```
Cacioppo, S. (2019, April 25-28). Evolutionary theory of social connections: Past, present, and future [Conference presentation abstract]. Ninety-ninth annual convention of the Western Psychological Association, Pasadena, CA. https://westernpsych.org/wp-content/uploads/2019/04/WPA-Program-2019-Final-2.pdf
```

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Cacioppo, S. (2019, April 25-28). Evolutionary theory of social connections: Past, present, and future [Conference presentation abstract]. Ninety-ninth annual convention of the Western Psychological Association, Pasadena, CA. https://westernpsych.org/wp-content/uploads/2019/04/WPA-Program-2019-Final-2.pdf

SOURCE TYPE: Conference presentation (abstract)

VALIDATION RESULTS:

❌ Date: Incorrect range punctuation
   What’s wrong: Uses a hyphen instead of an en dash for the date range.
   Should be: (2019, April 25–28).

❌ Conference/place wording and capitalization
   What’s wrong: The citation omits the standard phrase ...
```

**Metadata**:
- Source Type: unknown
- Metadata Source: synthetic_expansion
- Seed ID: manual_1761231314585

---

## Error #15: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: INVALID | **Provenance**: SYNTHETIC

**Test Citation**:
```
Armstrong, D. (2019). Malory and Character. In M. G. Leitch & C. J. Rushton (Eds.), _A new companion to Malory_ (pp. 144-163). D. S. Brewer. https://doi.org/10.1234/abcd.5678
```

**Provenance Issue**: Synthetic citation but seed not found.
- Seed ID: manual_1761231869026

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Armstrong, D. (2019). Malory and Character. In M. G. Leitch & C. J. Rushton (Eds.), _A new companion to Malory_ (pp. 144-163). D. S. Brewer. https://doi.org/10.1234/abcd.5678

SOURCE TYPE: book chapter

VALIDATION RESULTS:

❌ Title (chapter): Incorrect capitalization
   What’s wrong: Chapter titles in APA 7 should be in sentence case (only the first word, first word after a colon, and proper nouns capitalized). "Character" is not a proper noun and should not be capitalized.
   Should be: "Malory and character."

❌ Page range: Hyphen used instead of en dash
   What’s wrong: APA uses an en dash for page ranges (–), not ...
```

**Metadata**:
- Source Type: unknown
- Metadata Source: synthetic_expansion
- Seed ID: manual_1761231869026

---

## Error #16: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: INVALID | **Provenance**: SYNTHETIC

**Test Citation**:
```
Schulman, M. (2019, September 9). _Superfans: A love story_. _The New Yorker_. https://doi.org/10.1000/xyz456
```

**Seed → Synthetic Comparison**:

SEED (original manually curated):
```
Schulman, M. (2019, September 9). Superfans: A love story. _The New Yorker_. https://www.newyorker.com/magazine/2019/09/16/superfans-a-love-story
```

SYNTHETIC (altered version being tested):
```
Schulman, M. (2019, September 9). _Superfans: A love story_. _The New Yorker_. https://doi.org/10.1000/xyz456
```

**Model's Reasoning**:
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
   Example correction:
   Schulman, M. (2019, September 9). Superfans: A love story. _The New Yorker_. https://doi.org/10.1000/xyz456

✓ Author format: Correct (Schulman, M.).
✓ Date format: Correct (2019, September 9).
✓ Periodical name: Correctly italicized (_The New Yorker_).
✓ DOI/URL: Correctly format...
```

**Metadata**:
- Source Type: unknown
- Metadata Source: synthetic_expansion
- Seed ID: manual_1761230966215

---

## Error #17: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: INVALID | **Provenance**: SYNTHETIC

**Test Citation**:
```
National Cancer Institute. (2019). _Taking time_: Support for people with cancer (NIH Publication No. 18-2059). U.S. Department of Health and Human Services, National Institutes of Health. https://www.cancer.gov/publications/patient-education/takingtime.pdf
```

**Seed → Synthetic Comparison**:

SEED (original manually curated):
```
National Cancer Institute. (2019). _Taking time: Support for people with cancer_(NIH Publication No. 18-2059). U.S. Department of Health and Human Services, National Institutes of Health. https://www.cancer.gov/publications/patient-education/takingtime.pdf
```

SYNTHETIC (altered version being tested):
```
National Cancer Institute. (2019). _Taking time_: Support for people with cancer (NIH Publication No. 18-2059). U.S. Department of Health and Human Services, National Institutes of Health. https://www.cancer.gov/publications/patient-education/takingtime.pdf
```

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
National Cancer Institute. (2019). _Taking time_: Support for people with cancer (NIH Publication No. 18-2059). U.S. Department of Health and Human Services, National Institutes of Health. https://www.cancer.gov/publications/patient-education/takingtime.pdf

SOURCE TYPE: other (government report)

VALIDATION RESULTS:

❌ Title (italics): Only the main title ("Taking time") has been marked as italic. In APA 7 the full report title (title and subtitle) should be italicized in sentence case.
   Should be: _Taking time: Support for people with cancer_ (NIH Publication No. 18-2059). U.S. Department of Health and Human Servi...
```

**Metadata**:
- Source Type: unknown
- Metadata Source: synthetic_expansion
- Seed ID: manual_1761231133489

---

## Error #18: FALSE_NEGATIVE

**Ground Truth**: INVALID | **Model Prediction**: VALID | **Provenance**: SYNTHETIC

**Test Citation**:
```
Carey, B. (2019, March 22). Can we get better at forgetting? _The New York Times._ https://www.nytimes.com/2019/03/22/health/memory-forgetting-psychology.html
```

**Seed → Synthetic Comparison**:

SEED (original manually curated):
```
Carey, B. (2019, March 22). Can we get better at forgetting? _The New York Times_. https://www.nytimes.com/2019/03/22/health/memory-forgetting-psychology.html
```

SYNTHETIC (altered version being tested):
```
Carey, B. (2019, March 22). Can we get better at forgetting? _The New York Times._ https://www.nytimes.com/2019/03/22/health/memory-forgetting-psychology.html
```

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Carey, B. (2019, March 22). Can we get better at forgetting? _The New York Times._ https://www.nytimes.com/2019/03/22/health/memory-forgetting-psychology.html

SOURCE TYPE: webpage (newspaper article)

VALIDATION RESULTS:

✓ No APA 7 formatting errors detected

───────────────────────────────────────────────────────────────────────────...
```

**Metadata**:
- Source Type: unknown
- Metadata Source: synthetic_expansion
- Seed ID: manual_1761230980239

---

## Error #19: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: INVALID | **Provenance**: MANUAL/ORIGINAL

**Test Citation**:
```
Perreault, L. (2019). Obesity in adults: Role of physical activity and exercise. _UpToDate_. Retrieved January 12, 2020, from https://www.uptodate.com/contents/obesity-in-adults-role-of-physical-activity-and-exercise
```

**Provenance**: This IS the original manually curated seed citation (not synthetic).

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Perreault, L. (2019). Obesity in adults: Role of physical activity and exercise. _UpToDate_. Retrieved January 12, 2020, from https://www.uptodate.com/contents/obesity-in-adults-role-of-physical-activity-and-exercise

SOURCE TYPE: webpage

VALIDATION RESULTS:

❌ Date: Incomplete date
   What’s wrong: The entry lists only the year (2019). For a web page (and especially for resources that are updated, like UpToDate), APA 7 requires the full date when available: year, month day (e.g., 2019, June 14).
   Should be: (2019, Month Day) — e.g., Perreault, L. (2019, June 14).

❌ Title vs. Site name formatting: italicization re...
```

**Metadata**:
- Source Type: journal article
- Metadata Source: manual_curation
- Seed ID: manual_1761231684529

---

## Error #20: FALSE_NEGATIVE

**Ground Truth**: INVALID | **Model Prediction**: VALID | **Provenance**: SYNTHETIC

**Test Citation**:
```
Schlesselmann, A. J., & Held, P. (2025). Using network analysis to characterize clinical improvement during cognitive processing therapy. _Behaviour Research and Therapy, 185_, Article 104678. https://doi.org/10.1016/j.brat.2024.104678
```

**Seed → Synthetic Comparison**:

SEED (original manually curated):
```
Schlesselmann, A. J., McNally, R. J., & Held, P. (2025). Using network analysis to characterize clinical improvement during cognitive processing therapy. _Behaviour Research and Therapy_, _185_, Article 104678. https://doi.org/10.1016/j.brat.2024.104678
```

SYNTHETIC (altered version being tested):
```
Schlesselmann, A. J., & Held, P. (2025). Using network analysis to characterize clinical improvement during cognitive processing therapy. _Behaviour Research and Therapy, 185_, Article 104678. https://doi.org/10.1016/j.brat.2024.104678
```

**Model's Reasoning**:
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

**Metadata**:
- Source Type: unknown
- Metadata Source: synthetic_expansion
- Seed ID: manual_1761230845819

---

## Error #21: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: INVALID | **Provenance**: MANUAL/ORIGINAL

**Test Citation**:
```
Harris, K. R., Graham, S., & Urdan T. (Eds.). (2012). _APA educational psychology handbook_ (Vols. 1–3). American Psychological Association.
```

**Provenance**: This IS the original manually curated seed citation (not synthetic).

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Harris, K. R., Graham, S., & Urdan T. (Eds.). (2012). _APA educational psychology handbook_ (Vols. 1–3). American Psychological Association.

SOURCE TYPE: book

VALIDATION RESULTS:

❌ Authors (formatting of editor names): Missing comma between the last name and initials for the third editor.
   Should be: Urdan, T.
   Full corrected authors/editors portion: Harris, K. R., Graham, S., & Urdan, T. (Eds.).

No other APA 7th formatting errors detected — title (italicized, sentence case), volume notation, year, and publisher are correctly presented. 

────────────────────────────────────────────────────────────────────────...
```

**Metadata**:
- Source Type: book
- Metadata Source: manual_curation
- Seed ID: manual_1761230390894

---

## Error #22: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: INVALID | **Provenance**: MANUAL/ORIGINAL

**Test Citation**:
```
Agency for Toxic Substances and Disease Registry. (n.d.). _Asbestos in your environment: What you can do to limit exposure_ [Fact sheet]. U.S. Department of Health & Human Services. https://www.atsdr.cdc.gov/docs/limitingenvironmentalexposures_factsheet-508.pdf
```

**Provenance**: This IS the original manually curated seed citation (not synthetic).

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Agency for Toxic Substances and Disease Registry. (n.d.). _Asbestos in your environment: What you can do to limit exposure_ [Fact sheet]. U.S. Department of Health & Human Services. https://www.atsdr.cdc.gov/docs/limitingenvironmentalexposures_factsheet-508.pdf

SOURCE TYPE: webpage (government fact sheet)

VALIDATION RESULTS:

❌ Publisher / Website name: Uses an ampersand (&)
   What’s wrong: APA 7 uses the word "and" in names of organizations/publishers rather than an ampersand.
   Should be: U.S. Department of Health and Human Services

───────────────────────────────────────────────────────────────────────────

No...
```

**Metadata**:
- Source Type: other
- Metadata Source: manual_curation
- Seed ID: manual_1761231197721

---

## Error #23: FALSE_NEGATIVE

**Ground Truth**: INVALID | **Model Prediction**: INVALID | **Provenance**: SYNTHETIC

**Test Citation**:
```
Baral, P., Larsen, M., Archer, M., & Johnson, T. (2019). _Does money grow on trees? Restoration financing in Southeast Asia_. Atlantic Council. https://www.atlanticcouncil.org/in-depth-research-reports/report/does-money-grow-on-trees-restoring-financing-in-southeast-asia/
```

**Seed → Synthetic Comparison**:

SEED (original manually curated):
```
Baral, P., Larsen, M., & Archer, M. (2019). _Does money grow on trees? Restoration financing in Southeast Asia_. Atlantic Council. https://www.atlanticcouncil.org/in-depth-research-reports/report/does-money-grow-on-trees-restoring-financing-in-southeast-asia/
```

SYNTHETIC (altered version being tested):
```
Baral, P., Larsen, M., Archer, M., & Johnson, T. (2019). _Does money grow on trees? Restoration financing in Southeast Asia_. Atlantic Council. https://www.atlanticcouncil.org/in-depth-research-reports/report/does-money-grow-on-trees-restoring-financing-in-southeast-asia/
```

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Baral, P., Larsen, M., Archer, M., & Johnson, T. (2019). _Does money grow on trees? Restoration financing in Southeast Asia_. Atlantic Council. https://www.atlanticcouncil.org/in-depth-research-reports/report/does-money-grow-on-trees-restoring-financing-in-southeast-asia/

SOURCE TYPE: webpage (online report)

VALIDATION RESULTS:

❌ Date: Missing month and day
   What’s wrong: For a webpage citation APA 7 (per the rules you supplied) requires the full publication date in the form (Year, Month Day). The citation currently lists only the year (2019).
   Should be: Include the full date if available, e.g.
   Baral, P., L...
```

**Metadata**:
- Source Type: unknown
- Metadata Source: synthetic_expansion
- Seed ID: manual_1761231143621

---

## Error #24: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: INVALID | **Provenance**: SYNTHETIC

**Test Citation**:
```
Ganster, D. C., Schaubroeck, J., Sime, W. E., & Mayes, B. T. (1991). The Nomological Validity of the Type A Personality Among Employed Adults [Monograph]. _Journal of Applied Psychology_, _76_(1), 143–168. https://doi.org/10.1037/0021-9010.76.1.143
```

**Seed → Synthetic Comparison**:

SEED (original manually curated):
```
Ganster, D. C., Schaubroeck, J., Sime, W. E., & Mayes, B. T. (1991). The nomological validity of the Type A personality among employed adults [Monograph]. _Journal of Applied Psychology_, _76_(1), 143–168. http://doi.org/10.1037/0021-9010.76.1.143
```

SYNTHETIC (altered version being tested):
```
Ganster, D. C., Schaubroeck, J., Sime, W. E., & Mayes, B. T. (1991). The Nomological Validity of the Type A Personality Among Employed Adults [Monograph]. _Journal of Applied Psychology_, _76_(1), 143–168. https://doi.org/10.1037/0021-9010.76.1.143
```

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Ganster, D. C., Schaubroeck, J., Sime, W. E., & Mayes, B. T. (1991). The Nomological Validity of the Type A Personality Among Employed Adults [Monograph]. _Journal of Applied Psychology_, _76_(1), 143–168. https://doi.org/10.1037/0021-9010.76.1.143

SOURCE TYPE: journal article

VALIDATION RESULTS:

❌ Title: Incorrect capitalization and extraneous bracketed element
   What’s wrong: The article title is in title case ("The Nomological Validity of the Type A Personality Among Employed Adults") but APA 7 requires sentence case for article titles. Also the bracketed label "[Monograph]" does not belong in a standard journa...
```

**Metadata**:
- Source Type: unknown
- Metadata Source: synthetic_expansion
- Seed ID: manual_1761230915834

---

## Error #25: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: INVALID | **Provenance**: SYNTHETIC

**Test Citation**:
```
Pope, J. P., & Wall, H. (2025). _Is the goal intrinsic or extrinsic? Examining self-determination theory researchers’ and the general publics’ perceptions of exercise goals._ _Canadian Journal of Behavioural Science/Revue canadienne des sciences du comportement_, _57_(3), 239–248. https://doi.org/10.1037/cbs0000411
```

**Seed → Synthetic Comparison**:

SEED (original manually curated):
```
Pope, J. P., & Wall, H. (2025). Is the goal intrinsic or extrinsic? Examining self-determination theory researchers’ and the general publics’ perceptions of exercise goals. _Canadian Journal of Behavioural Science/Revue canadienne des sciences du comportement_, _57_(3), 239–248. https://doi.org/10.1037/cbs0000411
```

SYNTHETIC (altered version being tested):
```
Pope, J. P., & Wall, H. (2025). _Is the goal intrinsic or extrinsic? Examining self-determination theory researchers’ and the general publics’ perceptions of exercise goals._ _Canadian Journal of Behavioural Science/Revue canadienne des sciences du comportement_, _57_(3), 239–248. https://doi.org/10.1037/cbs0000411
```

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Pope, J. P., & Wall, H. (2025). _Is the goal intrinsic or extrinsic? Examining self-determination theory researchers’ and the general publics’ perceptions of exercise goals._ _Canadian Journal of Behavioural Science/Revue canadienne des sciences du comportement_, _57_(3), 239–248. https://doi.org/10.1037/cbs0000411

SOURCE TYPE: journal article

VALIDATION RESULTS:

❌ Title (formatting — italics)
   What’s wrong: The article title is italicized. In APA 7th edition, article titles in reference list should NOT be italicized.
   Should be: The article title should be plain text (no italics).

❌ Title (capitalization)
   ...
```

**Metadata**:
- Source Type: unknown
- Metadata Source: synthetic_expansion
- Seed ID: manual_1761230824352

---

## Error #26: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: INVALID | **Provenance**: SYNTHETIC

**Test Citation**:
```
Agency for Toxic Substances and Disease Registry. (n.d.). _Asbestos in your environment: What you can do to limit exposure_ [Fact sheet]. U.S. Department of Health & Human Services. doi:10.1234/atsdr.5678
```

**Seed → Synthetic Comparison**:

SEED (original manually curated):
```
Agency for Toxic Substances and Disease Registry. (n.d.). _Asbestos in your environment: What you can do to limit exposure_ [Fact sheet]. U.S. Department of Health & Human Services. https://www.atsdr.cdc.gov/docs/limitingenvironmentalexposures_factsheet-508.pdf
```

SYNTHETIC (altered version being tested):
```
Agency for Toxic Substances and Disease Registry. (n.d.). _Asbestos in your environment: What you can do to limit exposure_ [Fact sheet]. U.S. Department of Health & Human Services. doi:10.1234/atsdr.5678
```

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Agency for Toxic Substances and Disease Registry. (n.d.). _Asbestos in your environment: What you can do to limit exposure_ [Fact sheet]. U.S. Department of Health & Human Services. doi:10.1234/atsdr.5678

SOURCE TYPE: webpage (government fact sheet)

VALIDATION RESULTS:

❌ DOI/Identifier format: The DOI is presented using the legacy "doi:" prefix.  
   Should be: present the DOI as a functional URL, e.g. https://doi.org/10.1234/atsdr.5678

Optional additional note (not an error if DOI is provided): If this fact sheet does not have a DOI but is retrieved from a website, include the URL of the page instead of a DOI. Al...
```

**Metadata**:
- Source Type: unknown
- Metadata Source: synthetic_expansion
- Seed ID: manual_1761231197721

---

## Error #27: FALSE_POSITIVE

**Ground Truth**: VALID | **Model Prediction**: VALID | **Provenance**: SYNTHETIC

**Test Citation**:
```
Ouellette, J. (2019, November 15). Physicists capture first footage of quantum knots unraveling in superfluid. _Ars Technica_. https://doi.org/10.1234/5678
```

**Seed → Synthetic Comparison**:

SEED (original manually curated):
```
Ouellette, J. (2019, November 15). Physicists capture first footage of quantum knots unraveling in superfluid. _Ars Technica_. https://arstechnica.com/science/2019/11/study-you-can-tie-a-quantum-knot-in-a-superfluid-but-it-will-soon-untie-itself/
```

SYNTHETIC (altered version being tested):
```
Ouellette, J. (2019, November 15). Physicists capture first footage of quantum knots unraveling in superfluid. _Ars Technica_. https://doi.org/10.1234/5678
```

**Model's Reasoning**:
```
═══════════════════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════════════════

ORIGINAL:
Ouellette, J. (2019, November 15). Physicists capture first footage of quantum knots unraveling in superfluid. _Ars Technica_. https://doi.org/10.1234/5678

SOURCE TYPE: web page (news article)

VALIDATION RESULTS:

✓ No APA 7 formatting errors detected

───────────────────────────────────────────────────────────────────────────...
```

**Metadata**:
- Source Type: unknown
- Metadata Source: synthetic_expansion
- Seed ID: manual_1761231042282

---

