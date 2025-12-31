# Chicago 17th Edition Golden Test Set Review

**Created**: 2025-12-31
**Updated**: 2025-12-31 (with proper italics formatting)
**Total Citations**: 234 (117 valid + 117 invalid)
**Purpose**: Testing Chicago Notes-Bibliography validator prompt

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Valid citations | 117 |
| Invalid citations | 117 |
| Train set (80%) | 187 |
| Holdout set (20%) | 47 |
| University sources | 8 |
| Source types covered | 20+ |

---

## Error Types Introduced

| Error Type | Count | Description |
|------------|-------|-------------|
| `missing_period` | 35 | Removed final period from citation |
| `author_initials` | 18 | Changed full first name to initial (APA habit) |
| `retrieved_from` | 13 | Added "Retrieved from" before URL (APA habit) |
| `missing_quotes` | 11 | Removed quotation marks from article/chapter titles |
| `ampersand` | 10 | Changed "and" to "&" for multiple authors |
| `colon_after_author` | 9 | Used colon instead of period after author name |
| `missing_place` | 8 | Removed place of publication (critical Chicago error) |
| `sentence_case` | 5 | Changed Title Case to sentence case |
| `missing_comma_date` | 4 | Removed comma in date format |
| `page_prefix` | 3 | Added "pp." or "p." before page numbers (not used in Chicago) |
| `eds_abbreviation` | 1 | Changed "edited by" to "ed." |

---

## Italics Format Note

**IMPORTANT**: All citations use underscore notation for italics: `_Title_`

This is required because the LLM needs a text-based way to identify italicized content. Examples:
- Book titles: `_Beloved_`
- Journal names: `_American Journal of Archaeology_`
- Newspaper names: `_New York Times_`
- Film titles: `_Jurassic Park_`

---

## Example Pairs by Source

### CSU Channel Islands
**Source URL**: https://libguides.csuci.edu/citations/chicagoNB

#### Book - Single Author
**Valid**:
```
Morrison, Toni. _Beloved_. New York: Alfred A. Knopf, 1987.
```

**Invalid** (missing_period):
```
Morrison, Toni. _Beloved_. New York: Alfred A. Knopf, 1987
```
*Error: Final period removed*

---

#### Book - Multiple Authors
**Valid**:
```
Zamudio, Margaret, Caskey Russell, Francisco A Rios, and Jacquelyn L Bridgeman. _Critical Race Theory Matters: Education and Ideology_. New York: Routledge, 2011. ProQuest Ebook Central.
```

**Invalid** (author_initials):
```
Zamudio, M., Caskey Russell, Francisco A Rios, and Jacquelyn L Bridgeman. _Critical Race Theory Matters: Education and Ideology_. New York: Routledge, 2011. ProQuest Ebook Central.
```
*Error: Full first name "Margaret" changed to initial "M."*

---

#### Book - Edited
**Valid**:
```
Berglund, Jeff, Jan Johnson, and Kimberli Lee, eds. _Indigenous Pop: Native American Music from Jazz to Hip Hop_. Tucson: University of Arizona Press, 2016. ProQuest Ebook Central.
```

**Invalid** (sentence_case):
```
Berglund, Jeff, Jan Johnson, and Kimberli Lee, eds. _Indigenous pop: native american music from jazz to hip hop_. Tucson: University of Arizona Press, 2016. ProQuest Ebook Central.
```
*Error: Title Case changed to sentence case*

---

#### Journal Article
**Valid**:
```
Epstein, Saul, and Sara Libby Robinson. "The Soul, Evil Spirits, and the Undead: Vampires, Death, and Burial in Jewish Folklore and Law." _Preternature_ 1, no. 2 (2012): 232–51. https://doi.org/10.5325/preternature.1.2.0232.
```

**Invalid** (author_initials):
```
Epstein, S., and Sara Libby Robinson. "The Soul, Evil Spirits, and the Undead: Vampires, Death, and Burial in Jewish Folklore and Law." _Preternature_ 1, no. 2 (2012): 232–51. https://doi.org/10.5325/preternature.1.2.0232.
```
*Error: "Saul" changed to "S."*

---

#### Newspaper
**Valid**:
```
Streeter, Kurt. "Standing Up for Herself by Sitting, And Empowering Others to Say No." _New York Times_, July 29, 2021.
```

**Invalid** (author_initials):
```
Streeter, K.. "Standing Up for Herself by Sitting, And Empowering Others to Say No." _New York Times_, July 29, 2021.
```
*Error: "Kurt" changed to "K."*

---

### Naval Postgraduate School (NPS)
**Source URL**: https://libguides.nps.edu/citation/chicago-nb

#### Book - Single Author
**Valid**:
```
Pollan, Michael. _The Omnivore's Dilemma: A Natural History of Four Meals_. New York: Penguin, 2006.
```

**Invalid** (colon_after_author):
```
Pollan, Michael: _The Omnivore's Dilemma: A Natural History of Four Meals_. New York: Penguin, 2006.
```
*Error: Period after author name changed to colon*

---

#### Book - Missing Place
**Valid**:
```
Strindberg, Anders, and Mats Wärn. _Islamism: Religion, Radicalization and Resistance_. 2nd ed. Hoboken, NJ: John Wiley and Sons, 2011.
```

**Invalid** (missing_place):
```
Strindberg, Anders, and Mats Wärn. _Islamism: Religion, Radicalization and Resistance_. 2nd ed. John Wiley and Sons, 2011.
```
*Error: Place of publication "Hoboken, NJ:" removed (critical Chicago error)*

---

#### Journal Article
**Valid**:
```
Sanico, Grace F., and Makoto Kakinaka. "Terrorism and Deterrence Policy with Transnational Support." _Defence and Peace Economics_ 19, no. 2 (April 2008): 153–67. https://doi.org/10.1080/10242690701505419.
```

**Invalid** (missing_quotes):
```
Sanico, Grace F., and Makoto Kakinaka. Terrorism and Deterrence Policy with Transnational Support. _Defence and Peace Economics_ 19, no. 2 (April 2008): 153–67. https://doi.org/10.1080/10242690701505419.
```
*Error: Quotation marks removed from article title*

---

#### Audiobook
**Valid**:
```
Strayed, Cheryl. _Wild: From Lost to Found on the Pacific Crest Trail_. Read by Bernadette Dunne. New York: Random House Audio, 2012. Audible, 13:06:00.
```

**Invalid** (missing_period):
```
Strayed, Cheryl. _Wild: From Lost to Found on the Pacific Crest Trail_. Read by Bernadette Dunne. New York: Random House Audio, 2012. Audible, 13:06:00
```
*Error: Final period removed*

---

### Florida State University
**Source URL**: https://guides.lib.fsu.edu/c.php?g=352572&p=8612358

#### Book Chapter
**Valid**:
```
Lomax, Michael E. "Jackie Robinson: Racial Pioneer and Athlete Extraordinaire in an Era of Change." In _Out of the Shadows: A Biographical History of African American Athletes_, edited by David K Wiggins, 163–79. Fayetteville: University of Arkansas Press, 2006. https://doi.org/10.2307/j.ctt1ffjksv.15.
```

**Invalid** (eds_abbreviation):
```
Lomax, Michael E. "Jackie Robinson: Racial Pioneer and Athlete Extraordinaire in an Era of Change." In _Out of the Shadows: A Biographical History of African American Athletes_, ed. David K Wiggins, 163–79. Fayetteville: University of Arkansas Press, 2006. https://doi.org/10.2307/j.ctt1ffjksv.15.
```
*Error: "edited by" changed to "ed."*

---

### Santa Clara University
**Source URL**: https://libguides.scu.edu/c.php?g=1190938&p=8710779

#### Journal Article - Multiple Authors with Ampersand Error
**Valid**:
```
Magee, Peter, Cameron Petrie, Robert Knox, Farid Khan, and Ken Thomas. "The Achaemenid Empire in South Asia and Recent Excavations in Akra in Northwest Pakistan." _American Journal of Archaeology_ 109, no. 4 (October 2005): 711–41. https://doi.org/10.3764/aja.109.4.711.
```

**Invalid** (ampersand):
```
Magee, Peter, Cameron Petrie, Robert Knox, Farid Khan & Ken Thomas. "The Achaemenid Empire in South Asia and Recent Excavations in Akra in Northwest Pakistan." _American Journal of Archaeology_ 109, no. 4 (October 2005): 711–41. https://doi.org/10.3764/aja.109.4.711.
```
*Error: "and" changed to "&"*

---

### UNLV
**Source URL**: https://guides.library.unlv.edu/c.php?g=380753&p=2679284

#### Social Media - Twitter
**Valid**:
```
Chaucer Doth Tweet (@LeVostreGV). "A daye wythout anachronism ys lyke Emily Dickinson wythout her lightsaber." Twitter, April 7, 2018, 8:58 p.m. https://www.twitter.com/LeVostreGC/status/982829987286827009.
```

**Invalid** (retrieved_from):
```
Chaucer Doth Tweet (@LeVostreGV). "A daye wythout anachronism ys lyke Emily Dickinson wythout her lightsaber." Twitter, April 7, 2018, 8:58 p.m. Retrieved from https://www.twitter.com/LeVostreGC/status/982829987286827009.
```
*Error: Added "Retrieved from" before URL (APA habit, not used in Chicago)*

---

### Simmons University
**Source URL**: https://simmons.libguides.com/17chicagostyle

#### Thesis
**Valid**:
```
Savage, Courtney. "The Impact of Experiences of Asexual Students in Four-Year Institutions of Higher Education." Master's thesis, Texas Tech University, 2019. https://ttu-ir.tdl.org/handle/2346/85057.
```

**Invalid** (retrieved_from):
```
Savage, Courtney. "The Impact of Experiences of Asexual Students in Four-Year Institutions of Higher Education." Master's thesis, Texas Tech University, 2019. Retrieved from https://ttu-ir.tdl.org/handle/2346/85057.
```
*Error: Added "Retrieved from" before URL*

---

### Georgetown University
**Source URL**: https://guides.library.georgetown.edu/c.php?g=76018&p=3799160

#### Film
**Valid**:
```
Spielberg, Steven, dir. _Jurassic Park_. Universal City, CA: Amblin Entertainment, 1993. 2 hr., 7 min. Netflix.
```

**Invalid** (author_initials):
```
Spielberg, S., dir. _Jurassic Park_. Universal City, CA: Amblin Entertainment, 1993. 2 hr., 7 min. Netflix.
```
*Error: "Steven" changed to "S."*

---

### Concordia University Chicago
**Source URL**: https://libguides.cuchicago.edu/citation/chicago

#### Interview
**Valid**:
```
Bundy, McGeorge. Interview by Robert MacNeil. _MacNeil/Lehrer NewsHour_. PBS. February 7, 1990.
```

**Invalid** (colon_after_author):
```
Bundy, McGeorge: Interview by Robert MacNeil. _MacNeil/Lehrer NewsHour_. PBS. February 7, 1990.
```
*Error: Period after author name changed to colon*

---

## Source Type Coverage

| Source Type | Count | Examples |
|-------------|-------|----------|
| Books (various) | 35 | Morrison, Pollan, Coelho, Hansberry |
| Book chapters | 8 | Lomax, Lobb, Haynes |
| Journal articles | 25 | Epstein, Sanico, Ingham, Magee |
| Newspapers | 4 | Streeter, Hirsch, Strauss, Li |
| Magazines | 3 | Verducci, Koppelman, Kunzig |
| Websites | 5 | Marcel Breuer, Google |
| Social media | 2 | Chaucer Doth Tweet, Ndiaye |
| Videos | 3 | Smart Student, Snead, Cox |
| Films | 2 | Spielberg |
| Theses | 2 | Savage, Zonta |
| Interviews | 1 | Bundy |
| Artwork | 2 | Waterhouse, McCurry |
| Audiobooks | 1 | Strayed |
| Government docs | 5 | Department of Defense |

---

## Key Chicago Rules Being Tested

1. **Full first names** (not initials like APA)
2. **"and" not "&"** for multiple authors
3. **Place of publication required** for books (unlike APA/MLA)
4. **Title Case** for titles (not sentence case)
5. **No "pp." prefix** for page numbers
6. **No "Retrieved from"** before URLs
7. **Quotation marks** around article/chapter titles
8. **Period after author name** (not colon)
9. **"edited by"** spelled out (not "ed.")
10. **Final period** at end of citation
11. **Italics for standalone works** (books, journals, films) - marked with `_underscores_`

---

## Files Reference

| File | Purpose |
|------|---------|
| `chicago_train_set.jsonl` | Use for prompt iteration (187 citations) |
| `chicago_holdout_set.jsonl` | Use ONCE for final validation (47 citations) |
| `chicago_test_set_COMPREHENSIVE.jsonl` | Full test set, simple format |
| `chicago_test_set_DETAILED.jsonl` | Full test set with metadata |
| `chicago_raw_valid.jsonl` | All 117 valid citations with source URLs |
| `chicago_invalid_variants.jsonl` | All 117 invalid variants with error metadata |

---

## Data Sources

All citations extracted from 8 non-contaminated university library guides (verified not in LLM training data):

1. CSU Channel Islands - https://libguides.csuci.edu/citations/chicagoNB
2. Naval Postgraduate School - https://libguides.nps.edu/citation/chicago-nb
3. Florida State University - https://guides.lib.fsu.edu/c.php?g=352572&p=8612358
4. Santa Clara University - https://libguides.scu.edu/c.php?g=1190938&p=8710779
5. UNLV - https://guides.library.unlv.edu/c.php?g=380753&p=2679284
6. Simmons University - https://simmons.libguides.com/17chicagostyle
7. Concordia University Chicago - https://libguides.cuchicago.edu/citation/chicago
8. Georgetown University - https://guides.library.georgetown.edu/c.php?g=76018&p=3799160
