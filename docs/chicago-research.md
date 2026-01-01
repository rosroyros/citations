# Chicago Manual of Style 17th Edition - Research Document

**Purpose**: Foundation research for Chicago 17th Edition bibliography validator
**Date**: 2025-12-31
**Epic**: citations-1pdt

---

## 1. Overview

### History
The Chicago Manual of Style (CMOS) is the oldest American style guide, first published in 1906 by the University of Chicago Press. Now in its 17th edition (2017), it remains the definitive guide for academic writing in humanities disciplines.

### Two Documentation Systems

Chicago offers two distinct citation systems:

| System | Uses | How It Works |
|--------|------|--------------|
| **Notes-Bibliography (NB)** | Humanities (literature, history, arts) | Footnotes/endnotes + bibliography at end |
| **Author-Date** | Sciences, social sciences | Parenthetical citations + reference list |

### Our Scope: Notes-Bibliography Bibliography Entries Only

We validate **bibliography entries** in the Notes-Bibliography system. This is analogous to our APA/MLA approach - we validate reference lists, not in-text citations or footnotes.

**Rationale**:
- Bibliography formatting is where students struggle most
- Footnote format mirrors bibliography (same elements, different order)
- Standalone bibliography validation is the core value proposition

---

## 2. Notes-Bibliography System

### Relationship Between Footnotes and Bibliography

| Element | Footnote | Bibliography |
|---------|----------|--------------|
| Author name | First Last | Last, First |
| Separation | Commas between elements | Periods between elements |
| Page reference | Specific page cited | Full page range (or omitted) |
| Purpose | In-document citation | Full reference list |

**Example Comparison**:

Footnote:
```
1. Jack Kerouac, The Dharma Bums (New York: Viking Press, 1958), 42.
```

Bibliography:
```
Kerouac, Jack. The Dharma Bums. New York: Viking Press, 1958.
```

### Key Bibliography Rules

1. **Title**: "Bibliography" centered at top of page
2. **Spacing**: Single-spaced within entries, double-spaced between entries
3. **Indent**: Hanging indent (first line flush left, subsequent lines indented 0.5")
4. **Order**: Alphabetical by author's last name (or title if no author)
5. **Punctuation**: Periods separate major elements

---

## 3. Core Elements

### Author Formatting

| Scenario | Format | Example |
|----------|--------|---------|
| Single author | Last, First. | Smith, John. |
| Two authors | Last, First, and First Last. | Smith, John, and Jane Doe. |
| Three authors | Last, First, First Last, and First Last. | Smith, John, Jane Doe, and Bob Wilson. |
| 4-10 authors | List all in bibliography | All names spelled out |
| 11+ authors | First 7 + "et al." | Smith, John, et al. |
| Corporate author | Organization Name. | American Psychological Association. |
| No author | Begin with title | *Title of Work*. |

**Important Notes**:
- Use "and," NEVER ampersand (&) for multiple authors
- Only first author is inverted (Last, First)
- Editor notation: "Edited by First Last" (spelled out, not "ed.")

### Title Formatting

| Type | Format | Example |
|------|--------|---------|
| Books, journals | Italics | *The Great Gatsby* |
| Articles, chapters | Quotation marks | "The Road Not Taken" |
| Capitalization | Headline/Title Case | All major words capitalized |

**Title Case Rules**:
- Capitalize first and last words
- Capitalize all major words (nouns, verbs, adjectives, adverbs)
- Lowercase articles (a, an, the), prepositions, coordinating conjunctions
- Capitalize first word after colon in subtitles

### Publication Information

**Books** (Critical: Place of publication is REQUIRED):
```
Place of Publication: Publisher, Year.
```
Example: `New York: Viking Press, 1958.`

**Journals**:
```
Volume, no. Issue (Year): Page range.
```
Example: `58, no. 4 (2007): 585–625.`

### Access Information

| Element | When to Use | Format |
|---------|-------------|--------|
| DOI | Preferred for online sources | `https://doi.org/10.xxxx/xxxxx` |
| URL | When no DOI available | Full URL |
| Database name | Alternative to URL | `Project MUSE.` |
| Access date | Only if no publication date | `Accessed January 15, 2024.` |

---

## 4. Source Type Formats

### Books

**Single Author**:
```
Last, First. Title in Italics. Place: Publisher, Year.
```
Example: `Kerouac, Jack. The Dharma Bums. New York: Viking Press, 1958.`

**Multiple Authors**:
```
Last, First, and First Last. Title. Place: Publisher, Year.
```
Example: `Lash, Scott, and John Urry. Economies of Signs & Space. London: Sage Publications, 1994.`

**Edited Book**:
```
Last, First. Title. Edited by First Last. Place: Publisher, Year.
```
Example: `Tylor, Edward B. Researches into the Early Development of Mankind. Edited by Paul Bohannan. Chicago: University of Chicago Press, 1964.`

**Translated Book**:
```
Last, First. Title. Translated by First Last. Place: Publisher, Year.
```
Example: `Cortázar, Julio. Hopscotch. Translated by Gregory Rabassa. New York: Pantheon Books, 1966.`

**Chapter in Edited Book**:
```
Last, First. "Chapter Title." In Book Title, edited by First Last, page range. Place: Publisher, Year.
```
Example: `Harris, Muriel. "Talk to Me: Engaging Reluctant Writers." In A Tutor's Guide, edited by Ben Rafoth, 24-34. New Hampshire: Heinemann, 2000.`

### Journal Articles

**Print Journal**:
```
Last, First. "Article Title." Journal Name Volume, no. Issue (Year): page range.
```
Example: `MacDonald, Susan Peck. "The Erasure of Language." College Composition and Communication 58, no. 4 (2007): 585–625.`

**Online Journal with DOI**:
```
Last, First. "Article Title." Journal Name Volume, no. Issue (Year): page range. DOI.
```
Example: `Rennie, Kriston. "The normative character of monastic exemption." Medieval Worlds 6 (2017): 61-77. https://doi.org/10.1553/medievalworlds_no6_2017s61.`

**Online Journal with Database**:
```
Last, First. "Article Title." Journal Name Volume, no. Issue (Year): page range. Database Name.
```
Example: `LaSalle, Peter. "Conundrum: A Story about Reading." New England Review 38, no. 1 (2017): 95–109. Project MUSE.`

### Websites

**Website with Author**:
```
Last, First. "Page Title." Website Name. Date. URL.
```
Example: `Ross, Andrea. "'It Still Fits': Diamond Ring Missing Since 2004 Turns Up on Garden Carrot." CBC.ca. Last modified August 15, 2017. http://www.cbc.ca/...`

**Website without Author (Corporate)**:
```
Organization. "Page Title." Date or Accessed Date. URL.
```
Example: `Google. "Privacy Policy." Effective November 15, 2023. https://policies.google.com/privacy.`

### Newspaper/Magazine Articles

**Newspaper**:
```
Last, First. "Headline." Newspaper Name, Month Day, Year.
```
Example: `Deo, Nisha. "Visiting Professor Lectures on Photographer." Exponent (West Lafayette, IN), Feb. 13, 2009.`

**Magazine**:
```
Last, First. "Article Title." Magazine Title, Month Year.
```
Example: `Macel, Emily. "Beijing's Modern Movement." Dance Magazine, February 2009.`

**Notes**:
- Omit "The" from newspaper names
- Add city/state for lesser-known newspapers
- Page numbers typically omitted (editions vary)

### Films/Videos

**Film (DVD/Physical)**:
```
Last, First, dir. Title. Original Year; Place: Distributor, Release Year. Format.
```
Example: `Singer, Bryan, dir. The Usual Suspects. 1995; Santa Monica, CA: Metro-Goldwyn-Mayer, 2014. DVD.`

**YouTube Video**:
```
Last, First or Username. "Video Title." YouTube video, duration. Date. URL.
```
Example: `Bellaimey, John. "The Five Major World Religions." YouTube video, 11:09. November 14, 2013. https://www.youtube.com/watch?v=m6dCxo7t_aE.`

**Note**: YouTube videos are often cited only in notes, not bibliography.

### Government Documents

**Federal Document**:
```
Country. Department/Agency. Title. Place: Publisher, Year. URL.
```
Example: `U.S. Department of State. Foreign Relations of the United States: Diplomatic Papers, 1943. Washington, DC: GPO, 1965.`

**Congressional Document**:
```
U.S. Congress. House/Senate. Committee. Title. Congress, Session, Report Number.
```

### Dissertations/Theses

```
Last, First. "Title." PhD diss. or MA thesis, Institution, Year.
```
Example: `Rutz, Cynthia Lillian. "King Lear and Its Folktale Analogues." PhD diss., University of Chicago, 2013.`

### Interviews

**Published Interview**:
```
Interviewee Last, First. "Title." Interview by First Last. Publication, Date.
```

**Unpublished Interview**: Typically cited only in notes, not bibliography.

---

## 5. Key Differences from APA/MLA

| Element | APA 7 | MLA 9 | Chicago NB |
|---------|-------|-------|------------|
| Author format | Last, F. M. | Last, First. | Last, First. |
| Multiple authors | Use & | Use "and" | Use "and" |
| Title case | Sentence case | Title Case | Title Case |
| Book titles | Italics | Italics | Italics |
| Article titles | No quotes | Quotes | Quotes |
| Publisher location | No | No | **Yes (required!)** |
| Date position | After author | End | End |
| Page prefix | p./pp. | pp. | None |
| DOI format | https://doi.org/... | https://doi.org/... | https://doi.org/... |
| Access date | Required for undated | Not required | Only if no pub date |
| "Retrieved from" | Yes | No | No |
| Hanging indent | Yes | Yes | Yes |
| Alphabetization | By author | By author | By author |

**Critical Chicago-Specific Requirements**:
1. **Publisher location is REQUIRED for books** (unlike APA/MLA)
2. **Full first names** (not initials like APA)
3. **Periods between major elements** (not commas like footnotes)

---

## 6. Special Rules

### 3-Em Dash Rule

**Traditional Rule**: When citing multiple works by the same author, replace the author's name with a 3-em dash (———) in subsequent entries:

```
Morrison, Toni. Beloved. New York: Knopf, 1987.
———. Song of Solomon. New York: Knopf, 1977.
```

**17th Edition Change**: The 17th edition DISCOURAGES the use of 3-em dashes due to modern publishing technologies (digital formats, database entries).

**Our Decision**: Accept BOTH formats.
- Rationale: Some professors still require it; others don't
- It's a stylistic choice, not an error
- We should NOT penalize either approach

### 'Ibid.' Usage

- Primarily used in footnotes (not our validation scope)
- 17th edition discourages ibid. in favor of shortened citations
- Note for awareness but don't validate

### Multiple Works by Same Author

- Arrange chronologically from oldest to newest publication
- If same year, alphabetize by title
- Accept both with and without 3-em dash

### No Author

- Begin entry with title (ignore articles A, An, The for alphabetization)
- Corporate/organizational author can replace individual author

### Titles within Titles

- Book title within article: `"Reading *Moby-Dick* Today"`
- Article title within book: Keep original formatting

---

## 7. Common Errors to Test

### Author Formatting Errors
1. Using initials instead of full first names (APA habit)
2. Using ampersand (&) instead of "and" for multiple authors
3. Inverting all authors (only first should be inverted)
4. Missing period after author name
5. Using "eds." abbreviation instead of "Edited by"
6. Incorrect "et al." usage (should only appear with 11+ authors in bibliography)

### Title Errors
7. Using sentence case instead of Title Case
8. Missing italics on book/journal titles
9. Missing quotation marks on article/chapter titles
10. Incorrect capitalization after colon in subtitles

### Publication Information Errors
11. **Missing place of publication for books** (CRITICAL - required in Chicago)
12. Using abbreviations for publisher names (should be written out)
13. Missing comma between place and publisher
14. Using "p." or "pp." before page numbers (not used in Chicago)

### Online Source Errors
15. Missing DOI when available
16. Incorrect DOI format (should be full URL: https://doi.org/...)
17. Including "Retrieved from" (APA habit, not used in Chicago)
18. Including access date when publication date exists (unnecessary)

### Structural Errors
19. Using commas instead of periods between major elements
20. Missing hanging indent
21. Incorrect alphabetization (forgetting to ignore articles)
22. Double spacing within entries (should be single)

### Punctuation Errors
23. Missing period at end of entry
24. Colon instead of period after author
25. Missing comma in date (Month Day, Year)

---

## 8. Sources Consulted

### Tier 1 - Official/Authoritative Sources

1. **Chicago Manual of Style Online**
   https://www.chicagomanualofstyle.org/tools_citationguide/citation-guide-1.html
   Accessed: December 31, 2025

2. **Turabian Citation Guide**
   https://www.chicagomanualofstyle.org/turabian/citation-guide.html
   Accessed: December 31, 2025

3. **Purdue OWL - Chicago Manual 17th Edition**
   https://owl.purdue.edu/owl/research_and_citation/chicago_manual_17th_edition/
   Accessed: December 31, 2025

### Tier 2 - Academic Library Sources

4. **University of Queensland Library - Chicago 17th Notes-Bibliography**
   https://guides.library.uq.edu.au/referencing/chicago17-notes-bibliography
   Accessed: December 31, 2025

5. **Camosun College Library - Chicago Style Guide 17th Edition**
   https://camosun.libguides.com/Chicago-17thEd
   Accessed: December 31, 2025

6. **University of Wisconsin-Milwaukee - Chicago Notes-Biblio**
   https://guides.library.uwm.edu/citationstyles/chicago
   Accessed: December 31, 2025

7. **West Sound Academy - Chicago Citation Style 17th Edition**
   https://libguides.westsoundacademy.org/chicago-citation
   Accessed: December 31, 2025

8. **University of Nevada Las Vegas - Chicago Manual of Style 17th ed.**
   https://guides.library.unlv.edu/c.php?g=380753&p=2679284
   Accessed: December 31, 2025

9. **Scribbr - Chicago Style Citation Guide**
   https://www.scribbr.com/category/chicago-style/
   Accessed: December 31, 2025

---

## Appendix: Validation Design Decisions

### What We Validate
- Bibliography entry format correctness
- Required elements present (author, title, publication info)
- Proper punctuation between elements
- Correct Title Case capitalization
- Proper italics/quotation mark usage
- Publisher location for books (Chicago-specific requirement)

### What We Accept (Lenient)
- 3-em dash OR repeated author name (both valid)
- Minor variations in date formatting (Month Day, Year vs. Day Month Year)
- DOI with or without https:// prefix
- Trailing period present or absent

### What We Don't Validate
- Footnote/endnote format
- Ibid. usage
- In-text citations
- Alphabetical ordering of entries
- Page layout/spacing

### Guardrails
- Detect if user pastes footnotes instead of bibliography entries (numbers at start)
- Warn about common APA/MLA habits (initials, ampersand, sentence case)
