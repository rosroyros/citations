# MLA 9th Edition Citation Rules - Formal Specification

> **Purpose**: This document provides prescriptive, structured rules for validating MLA 9th edition citations. It is optimized for LLM prompt engineering and serves as the source of truth for the MLA validation system.

---

## Universal Rules (All Source Types)

### Author Formatting

**R1.1** Author names MUST use full first names, not initials
- ✅ VALID: Morrison, Toni
- ❌ INVALID: Morrison, T.

**R1.2** First author name MUST be inverted (Last, First Middle)
- ✅ VALID: Smith, John David
- ❌ INVALID: John David Smith

**R1.3** For TWO authors: use "and" between names (second name NOT inverted)
- ✅ VALID: Garcia, Maria, and Sanjay Patel
- ❌ INVALID: Garcia, Maria, & Sanjay Patel
- ❌ INVALID: Garcia, Maria and Patel, Sanjay

**R1.4** For THREE OR MORE authors: use "et al." after first author only
- ✅ VALID: Nickels, William, et al.
- ❌ INVALID: Nickels, William, Smith, John, et al.
- ❌ INVALID: Nickels, W., et al.

**R1.5** NO AUTHOR: Start with title (ignore "A", "An", "The" for alphabetization)
- ✅ VALID: "Climate Change Effects." *Nature Today*...
- ❌ INVALID: n.d. "Climate Change Effects."

### Title Formatting

**R2.1** ALL titles MUST use Title Case (capitalize all major words)
- ✅ VALID: "The Impact of Climate Change"
- ❌ INVALID: "The impact of climate change" (sentence case)

**R2.2** Shorter works use QUOTATION MARKS:
- Article titles, chapter titles, web page titles, poems, short stories, episodes
- ✅ VALID: "Modern Storytelling"

**R2.3** Complete works use ITALICS:
- Book titles, journal names, website names, films, TV series
- ✅ VALID: *Journal of Modern Arts*

**R2.4** Do NOT use both italics AND quotation marks on same title
- ❌ INVALID: *"Book Title"*

### Date Formatting

**R3.1** Date placement: AFTER publisher, BEFORE page numbers/URL
- ✅ VALID: Publisher, 2024, pp. 45-58.
- ❌ INVALID: Publisher. pp. 45-58, 2024. (APA style)

**R3.2** Date format: Day Month Year (abbreviated month, no commas)
- ✅ VALID: 5 Feb. 2024
- ❌ INVALID: Feb. 5, 2024
- ❌ INVALID: 2024-02-05

**R3.3** Year-only format: Just the year (for books, films)
- ✅ VALID: 2024.
- ❌ INVALID: (2024) (no parentheses)

**R3.4** NO DATE available: Omit date element (do not use "n.d.")
- ❌ INVALID: Publisher, n.d.

**R3.5** Access dates: "Accessed Day Month Year" at end (optional but recommended for changing content)
- ✅ VALID: Accessed 28 Dec. 2025.

### Punctuation Rules

**R4.1** Period AFTER: Author, Title of Source
- Morrison, Toni. *Beloved*.

**R4.2** Comma BETWEEN: All other elements within a container
- Publisher, 2024, pp. 45-58.

**R4.3** Period AT END: Every citation ends with a period
- ✅ VALID: ...2024.
- ❌ INVALID: ...2024 (no period)

**R4.4** NO "p." or "pp." in in-text citations:
- ✅ VALID IN-TEXT: (Morrison 42)
- ❌ INVALID IN-TEXT: (Morrison, p. 42)
- ❌ INVALID IN-TEXT: (Morrison, 42)

**R4.5** USE "pp." for page ranges in Works Cited:
- ✅ VALID WORKS CITED: pp. 45-58
- ❌ INVALID WORKS CITED: 45-58 (missing pp.)
- ❌ INVALID WORKS CITED: pages 45-58

### URL/DOI Formatting

**R5.1** Omit http:// or https:// protocol from URLs
- ✅ VALID: www.example.com
- ❌ INVALID: https://www.example.com

**R5.2** DOI preferred over URL when both available
- ✅ VALID: https://doi.org/10.1177/2053019614564785
- Format: Keep "https://doi.org/" prefix for DOIs

**R5.3** URLs come AFTER date, BEFORE access date
- ...2024, www.example.com. Accessed 28 Dec. 2025.

### Container System

**R6.1** Container = larger work holding source
- Article (source) → Journal (container 1)
- Journal → Database (container 2)

**R6.2** Single container punctuation: Period after source title, comma after container title
- "Article Title." *Journal Name*, vol. 4...

**R6.3** Second container: Add after first container's location element
- *Journal*, vol. 4, 2024, pp. 45-58. *JSTOR*, doi...

**R6.4** Container title always ITALICIZED

---

## Book Citations

### Required Elements (in order)

1. Author (Last, First)
2. *Book Title* (italicized, Title Case)
3. Publisher
4. Year.

### Specific Rules

**B1** Basic book format:
```
Author Last, First. Book Title. Publisher, Year.
```

**B2** Edited book: Use "editor" or "editors" after name
```
Last, First, editor. Book Title. Publisher, Year.
```

**B3** Translated book: "Translated by First Last" after title
```
Last, First. Book Title. Translated by First Last, Publisher, Year.
```

**B4** Edition: "2nd ed.," or "3rd ed.," before publisher
```
Last, First. Book Title. 3rd ed., Publisher, Year.
```

**B5** Publisher abbreviations: Common names (Penguin not Penguin Random House LLC)
- Use "UP" for University Press
- ✅ VALID: Oxford UP
- ❌ INVALID: Oxford University Press

**B6** No place of publication needed (removed in MLA 9)
- ❌ INVALID: New York: Publisher, 2024

### Valid Examples

```
Morrison, Toni. Beloved. Knopf, 1987.
Garcia, Maria, and Sanjay Patel. Economics: Principles and Applications. McGraw-Hill Education, 2019.
Nickels, William, et al. Understanding Canadian Business. McGraw-Hill Ryerson, 2016.
Crowley, Sharon, and Debra Hawhee. Ancient Rhetorics for Contemporary Students. 3rd ed., Pearson, 2004.
```

### Invalid Examples (Common Errors)

```
❌ Morrison, T. Beloved. Knopf, 1987. [Initials instead of full name]
❌ Morrison, Toni. "Beloved". Knopf, 1987. [Quotation marks instead of italics]
❌ Morrison, Toni. Beloved. New York: Knopf, 1987. [Place of publication]
❌ Morrison, Toni. Beloved, Knopf, 1987 [Missing period after title, at end]
❌ Morrison, Toni (1987). Beloved. Knopf. [APA style - date after author]
```

---

## Journal Article Citations

### Required Elements (in order)

1. Author (Last, First)
2. "Article Title" (quotation marks, Title Case)
3. *Journal Name* (italicized, Title Case)
4. vol. Volume,
5. no. Issue,
6. Date,
7. pp. page-range.
8. [Optional: DOI or URL]

### Specific Rules

**J1** Basic journal format:
```
Author Last, First. "Article Title." Journal Name, vol. #, no. #, Year, pp. ##-##.
```

**J2** Volume and issue: MUST use "vol." and "no." abbreviations (lowercase)
- ✅ VALID: vol. 4, no. 2
- ❌ INVALID: Vol. 4, No. 2 (capitalized)
- ❌ INVALID: 4(2) (APA style)
- ❌ INVALID: Volume 4, Number 2

**J3** Page ranges: MUST use "pp." before page numbers
- ✅ VALID: pp. 45-58
- ❌ INVALID: p. 45-58
- ❌ INVALID: 45-58

**J4** Monthly/seasonal: Include month or season
- ✅ VALID: Jan. 2024
- ✅ VALID: Spring 2024

**J5** DOI: Include if available (preferred over URL)
```
...pp. 81-98. https://doi.org/10.1177/2053019614564785.
```

**J6** Database (second container): Add after page range
```
...pp. 173-96. ProQuest, doi:10.1017/S0018246X06005966.
```

### Valid Examples

```
Khan, Samira. "Modern Storytelling." Journal of Modern Arts, vol. 4, no. 2, 2022, pp. 45-58.
Steffen, Will, et al. "The Trajectory of the Anthropocene: The Great Acceleration." The Anthropocene Review, vol. 2, no. 1, Jan. 2015, pp. 81-98. https://doi.org/10.1177/2053019614564785.
Langhamer, Claire. "Love and Courtship in Mid-Twentieth-Century England." Historical Journal, vol. 50, no. 1, 2007, pp. 173-96. ProQuest, doi:10.1017/S0018246X06005966.
```

### Invalid Examples (Common Errors)

```
❌ Khan, S. "Modern Storytelling." Journal of Modern Arts, vol. 4, no. 2, 2022, pp. 45-58. [Initials]
❌ Khan, Samira. Modern Storytelling. Journal of Modern Arts, vol. 4, no. 2, 2022, pp. 45-58. [No quotes on article]
❌ Khan, Samira. "Modern Storytelling." "Journal of Modern Arts", vol. 4, no. 2, 2022, pp. 45-58. [Quotes on journal]
❌ Khan, Samira. "Modern storytelling." Journal of Modern Arts, vol. 4, no. 2, 2022, pp. 45-58. [Sentence case]
❌ Khan, Samira. "Modern Storytelling." Journal of Modern Arts 4.2 (2022): 45-58. [APA/Chicago style]
❌ Khan, Samira. "Modern Storytelling." Journal of Modern Arts, Vol. 4, No. 2, 2022, 45-58. [No pp., capitalized]
```

---

## Website Citations

### Required Elements (in order)

1. Author (Last, First) [if available]
2. "Page Title" (quotation marks, Title Case)
3. *Website Name* (italicized, Title Case)
4. Publisher [if different from website name, otherwise omit]
5. Date,
6. URL.
7. [Optional: Accessed Date]

### Specific Rules

**W1** Basic website format:
```
Author Last, First. "Page Title." Website Name, Date, URL.
```

**W2** No author: Start with page title
```
"Page Title." Website Name, Date, URL.
```

**W3** Publisher: Omit if same as website name
- ✅ VALID: "Article." *New York Times*, 5 Feb. 2024, www.nytimes.com...
- ❌ INVALID: "Article." *New York Times*, New York Times, 5 Feb. 2024... [redundant]

**W4** No date: Omit date, include access date instead
```
"Page Title." Website Name, URL. Accessed 28 Dec. 2025.
```

**W5** URL: No http:// or https:// (unless DOI format)
- ✅ VALID: www.example.com
- ❌ INVALID: https://www.example.com

**W6** Access date: Optional but recommended for changing content
- Use for: wikis, dashboards, news sites that update frequently

### Valid Examples

```
Lee, Michael. "Climate Trends 2024." Eco Report, 5 Feb. 2024, www.ecoreport.org/climate2024.
"One Health and Disease: Tick-Borne." National Park Service, U.S. Department of the Interior, www.nps.gov/articles/one-health-disease-ticks-borne.htm.
"The Benefits of Meditation." Healthline, www.healthline.com/nutrition/12-benefits-of-meditation. Accessed 28 Dec. 2025.
```

### Invalid Examples (Common Errors)

```
❌ Lee, M. "Climate Trends 2024." Eco Report, 5 Feb. 2024, www.ecoreport.org/climate2024. [Initials]
❌ Lee, Michael. Climate Trends 2024. Eco Report, 5 Feb. 2024, www.ecoreport.org/climate2024. [No quotes]
❌ Lee, Michael. "Climate trends 2024." Eco Report, 5 Feb. 2024, www.ecoreport.org/climate2024. [Sentence case]
❌ Lee, Michael. "Climate Trends 2024." Eco Report. Web. 5 Feb. 2024. [Old MLA format]
❌ Lee, Michael. "Climate Trends 2024." Eco Report, https://www.ecoreport.org/climate2024. 5 Feb. 2024. [Protocol included, wrong order]
```

---

## Video Citations

### YouTube Videos

**Required Elements:**
1. Creator/Username
2. "Video Title" (quotation marks)
3. *YouTube* (italicized)
4. uploaded by Username [if different from creator],
5. Date,
6. URL.

### Specific Rules

**V1** Creator = Uploader:
```
Creator Name. "Video Title." YouTube, Date, URL.
```

**V2** Creator ≠ Uploader: Include "uploaded by"
```
Creator Name. "Video Title." YouTube, uploaded by Username, Date, URL.
```

**V3** No clear creator: Start with title
```
"Video Title." YouTube, uploaded by Username, Date, URL.
```

**V4** Video title: Use quotation marks (not italics)
- ✅ VALID: "Gaming and Productivity"
- ❌ INVALID: *Gaming and Productivity*

### Films/Movies

**Required Elements:**
1. *Film Title* (italicized)
2. Directed by First Last,
3. Production Company,
4. Year.
5. [Optional: Streaming service as second container]

### Specific Rules

**V5** Basic film format:
```
Film Title. Directed by First Last, Production Company, Year.
```

**V6** Film on streaming (second container):
```
Film Title. Directed by First Last, Production Company, Year. Streaming Service, URL. Accessed Date.
```

**V7** Multiple contributors: Can add "performances by" after director
```
Film Title. Directed by First Last, performances by Actor Names, Production Company, Year.
```

**V8** Film title: Italicized (standalone work)
- ✅ VALID: *Inception*
- ❌ INVALID: "Inception"

### Valid Examples

```
Beyoncé. "Beyoncé – Pretty Hurts (Video)." YouTube, 24 Apr. 2014, www.youtube.com/watch?v=LXXQLa-5n5w.
McGonigal, Jane. "Gaming and Productivity." YouTube, uploaded by Big Think, 3 July 2012, www.youtube.com/watch?v=mkdzy9bWW3E.
Inception. Directed by Christopher Nolan, Warner Brothers Pictures, 2010.
The Water Walker. Directed by James Burns, Seeing Red 6 Nations / Contour Films Inc., 2019. Crave, www.crave.ca/en/tv-shows/the-water-walker. Accessed 6 Oct. 2022.
```

### Invalid Examples (Common Errors)

```
❌ Beyoncé. Beyoncé – Pretty Hurts (Video). YouTube, 24 Apr. 2014, www.youtube.com/watch?v=LXXQLa-5n5w. [No quotes]
❌ Beyoncé. "Beyoncé – Pretty Hurts (Video)." "YouTube", 24 Apr. 2014, www.youtube.com/watch?v=LXXQLa-5n5w. [Quotes on platform]
❌ "Inception". Directed by Christopher Nolan, Warner Brothers Pictures, 2010. [Quotes instead of italics]
❌ Inception. Dir. Christopher Nolan. Warner Brothers Pictures, 2010. [Abbreviated "Dir."]
❌ Nolan, Christopher, dir. Inception. Warner Brothers Pictures, 2010. [Wrong author format]
```

---

## Book Chapter Citations

### Required Elements (in order)

1. Author (Last, First)
2. "Chapter Title" (quotation marks, Title Case)
3. *Book Title* (italicized, Title Case)
4. edited by Editor First Last,
5. Publisher,
6. Year,
7. pp. page-range.

### Specific Rules

**C1** Basic chapter format:
```
Author Last, First. "Chapter Title." Book Title, edited by Editor First Last, Publisher, Year, pp. ##-##.
```

**C2** Editor names: NOT inverted (First Last format)
- ✅ VALID: edited by Ben Rafoth
- ❌ INVALID: edited by Rafoth, Ben

**C3** Multiple editors: List all or use "et al." after first
- ✅ VALID: edited by Sarah Chen and Michael Rodriguez
- ✅ VALID: edited by Sarah Chen, et al.

**C4** Chapter title: Quotation marks (not italics)
- ✅ VALID: "Talk to Me: Engaging Reluctant Writers"
- ❌ INVALID: *Talk to Me: Engaging Reluctant Writers*

**C5** Page range: MUST include with "pp." prefix
- ✅ VALID: pp. 24-34
- ❌ INVALID: 24-34 (missing pp.)
- ❌ INVALID: pages 24-34

**C6** This is a SINGLE container citation:
- Chapter = source
- Book = container
- No second container unless book accessed via database

### Valid Examples

```
Harris, Muriel. "Talk to Me: Engaging Reluctant Writers." A Tutor's Guide: Helping Writers One to One, edited by Ben Rafoth, Heinemann, 2000, pp. 24-34.
Kincaid, Jamaica. "Girl." The Vintage Book of Contemporary American Short Stories, edited by Tobias Wolff, Vintage, 1994, pp. 306-07.
Thompson, Linda. "Digital Rhetoric in Practice." New Media Studies, edited by Sarah Chen and Michael Rodriguez, Oxford UP, 2021, pp. 112-45.
```

### Invalid Examples (Common Errors)

```
❌ Harris, M. "Talk to Me: Engaging Reluctant Writers." A Tutor's Guide, edited by Ben Rafoth, Heinemann, 2000, pp. 24-34. [Initials]
❌ Harris, Muriel. Talk to Me: Engaging Reluctant Writers. A Tutor's Guide, edited by Ben Rafoth, Heinemann, 2000, pp. 24-34. [No quotes on chapter]
❌ Harris, Muriel. "Talk to Me: Engaging Reluctant Writers." "A Tutor's Guide", edited by Ben Rafoth, Heinemann, 2000, pp. 24-34. [Quotes on book]
❌ Harris, Muriel. "Talk to Me: Engaging Reluctant Writers." A Tutor's Guide, edited by Rafoth, Ben, Heinemann, 2000, pp. 24-34. [Editor name inverted]
❌ Harris, Muriel. "Talk to Me: Engaging Reluctant Writers." A Tutor's Guide, edited by Ben Rafoth, Heinemann, 2000, 24-34. [Missing pp.]
❌ Harris, Muriel. "Talk to Me: Engaging Reluctant Writers." Ed. Ben Rafoth. A Tutor's Guide. Heinemann, 2000. 24-34. [Wrong format entirely]
```

---

## Edge Cases

### Multiple Authors

**E1** One author: Standard format (Last, First)
```
Morrison, Toni.
```

**E2** Two authors: First inverted, second normal, "and" between
```
Garcia, Maria, and Sanjay Patel.
```

**E3** Three+ authors: First author + "et al."
```
Nickels, William, et al.
```

**E4** Corporate/organizational author: Use full name
```
American Psychological Association.
```

### Missing Information

**E5** No author: Start with title
```
"Article Title." Rest of citation...
```

**E6** No date: Omit date element (do not use "n.d.")
```
Author. Title. Publisher, URL.
```

**E7** No page numbers: Omit page element
```
Author. "Title." Journal, vol. 4, no. 2, 2024.
```

**E8** No publisher: Omit publisher element
```
Author. Title. Year.
```

### Container Nesting

**E9** Article in journal (single container):
```
Author. "Article." Journal, vol. 4, no. 2, 2024, pp. 45-58.
```

**E10** Article in journal accessed via database (two containers):
```
Author. "Article." Journal, vol. 4, no. 2, 2024, pp. 45-58. Database, doi:...
```

**E11** Film on streaming service (two containers):
```
Film Title. Directed by Name, Company, Year. Netflix, URL. Accessed Date.
```

**E12** Chapter in ebook from database (two containers):
```
Author. "Chapter." Book Title, edited by Editor, Publisher, Year, pp. 45-58. Database, URL.
```

---

## Validation Checklist

Use this checklist to validate any MLA 9 citation:

### Author Check
- [ ] Full first name (not initials)?
- [ ] First author inverted (Last, First)?
- [ ] Two authors: "and" not "&"?
- [ ] Three+ authors: only first + "et al."?

### Title Check
- [ ] Title Case on all major words?
- [ ] Short works in quotes, complete works italicized?
- [ ] NOT both quotes and italics?

### Date Check
- [ ] Date AFTER publisher?
- [ ] Format: Day Month Year (no comma)?
- [ ] NOT in parentheses?

### Punctuation Check
- [ ] Period after author?
- [ ] Period after title of source?
- [ ] Commas between container elements?
- [ ] Period at end?

### Container Check
- [ ] Container title italicized?
- [ ] Second container (if any) after first container's location?

### Format-Specific Check
- [ ] Books: Title italicized?
- [ ] Journals: "vol." and "no." lowercase?
- [ ] Journals: "pp." before pages?
- [ ] Websites: URL without protocol?
- [ ] Chapters: Editor names not inverted?

---

## Error Detection Priority

Focus validation on these high-frequency errors (in order of importance):

### Critical Errors (Always catch)
1. Initials instead of full names
2. Wrong title formatting (italics vs. quotes)
3. Sentence case instead of Title Case
4. Wrong date placement (after author = APA style)
5. Missing punctuation (periods, commas)

### High-Priority Errors
6. "Vol." and "No." capitalized (should be lowercase)
7. Missing "pp." before page numbers
8. "&" instead of "and" for two authors
9. URL with http:// or https://
10. Multiple authors listed instead of "et al."

### Medium-Priority Errors
11. Container confusion (JSTOR as publisher)
12. Editor names inverted (should be First Last)
13. Wrong comma/period placement
14. Missing access dates for changing content
15. Publisher when same as website name

---

## Notes for LLM Validation

- **Be strict on fundamentals**: Names, titles, dates, punctuation
- **Be flexible on optional elements**: Access dates, URLs when DOI present
- **Recognize citation style mixing**: APA patterns (date after author, initials, "&") are common errors
- **Container logic**: Two-level containers (database, streaming) are complex but important
- **Title Case vs. Sentence case**: This is THE most common error in student citations
