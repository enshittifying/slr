# Rule 15: Books, Reports, and Other Nonperiodic Materials - Complete Analysis & Regex Patterns

## Rule 15 Overview

**Title:** Books, Reports, and Other Nonperiodic Materials

**Scope:** This rule covers how to cite books, treatises, reports, white papers, encyclopedias, dictionaries, and similar non-periodic sources.

**Basic Citation Format:** `Author, Title (edition year)`

### Key Principles:
- Include authors as name in full as given on the publication
- For up to 2 authors: list both names
- For more than 2 authors: use "first author et al." in academic citations
- Titles are italicized
- Include edition if not first edition
- Always include year of publication
- Publisher is generally not required for well-known legal publishers, but required for lesser-known works

---

## Complete Rule 15 Structure

### Rule 15.1: Author
**Content:** Include the author's full name as it appears on the title page.

**Key Requirements:**
- Two authors: List both (John Smith & Jane Doe)
- More than two authors: List first author followed by "et al." in academic writing
- Institutional author: Use name exactly as given, abbreviate per Bluebook rules (e.g., EPA)
- Practitioner documents may prefer listing all authors up to a certain number

**Example Format:**
- Single author: `John Smith`
- Two authors: `John Smith & Jane Doe`
- Multiple authors: `John Smith et al.`
- Institutional: `U.S. Environmental Protection Agency` or `EPA`

---

### Rule 15.2: Editor or Translator
**Content:** If citing a work by an editor or translator (with no named author) or if you want to note an editor/translator, put that name after the title.

**Key Requirements:**
- Precede with abbreviation "ed." or "trans."
- Use plural "eds." if multiple editors
- If author is present, editors typically not included unless the edition is primarily associated with the editor

**Example Format:**
- Single editor: `William Blackstone, Commentaries on the Laws of England ___ (John Doe ed., 2020)`
- Multiple editors: `Title (Jane Smith & John Doe eds., 2020)`
- Translator: `Original Author, Title (Jane Smith trans., 2020)`

---

### Rule 15.3: Title
**Content:** Book titles must be italicized with proper capitalization.

**Key Requirements:**
- Capitalize each word except articles, conjunctions, and prepositions (unless they begin the title or subtitle)
- For multi-volume sets: include volume number information
- For subtitles: include after a colon (e.g., "Title: Subtitle")
- If citing specific essay or chapter: see rule 15.5

**Example Format:**
- Simple title: `Title`
- Title with subtitle: `Title: Subtitle`
- Multi-volume: `Title, Vol. 2`

---

### Rule 15.4: Edition, Publisher, and Date
**Content:** Format for edition, publisher, and date information.

**Key Requirements:**
- If not first edition: include edition number (e.g., "2d ed.", "3d ed.")
- Always include year of publication
- Publisher generally not required in law review citations except for:
  - Less common works
  - Specific editions of codes or multi-volume works
  - Clarity purposes
- For organizational reports: organization can be listed as author or publisher

**Edition Number Patterns:**
- 2d ed.
- 3d ed.
- 4th ed.
- 1st ed. (rarely used)

**Full Format Example:**
- `Author, Title (publisher year)`
- `Author, Title (2d ed. 2020)`
- `Author, Title (publisher 2d ed. 2020)`

---

### Rule 15.5: Shorter Works in Collection

#### Rule 15.5.1: Works in Collection Generally
**Content:** Citation format for essays, articles, or chapters within an edited collection.

**Citation Format:**
`Author, Essay Title, in Book Title page, pinpoint (Editor Name ed., edition year)`

**Key Requirements:**
- Cite piece author, not editor
- Title of piece: in quotes (not italics)
- Book title: italicized
- Starting page and pinpoint page
- Editor with "ed." or "eds."
- Include edition if applicable

**Example:**
`John Doe, Essay Title, in Book Title 123, 130 (Jane Smith ed., 2d ed. 2020)`
- 123 = starting page
- 130 = pinpoint page

#### Rule 15.5.2: Collected Documents
**Content:** Format for documents reprinted in collections.

**Citation Format:**
`Document Description, in Book Title [page] (Editor Name ed., Year)`

**Key Requirements:**
- Include sufficient identifying details (date, addressee, etc.)
- Use brackets for page numbers in some formats

**Example:**
`Letter from X to Y (Dec. 1, 1900), in 5 Collected Letters of X 67 (Z Editor ed., 2000)`

---

### Rule 15.6: Prefaces, Forewords, Introductions, and Epilogues
**Content:** Citation format for these special sections.

**Citation Format:**
`Author, [Section Type], in Main Author, Book Title at page (Year)`

**Key Requirements:**
- Identify as "Foreword," "Introduction," etc.
- Use "at" for page reference (roman numerals common)
- Can cite different author than main work

**Example:**
`Jane Doe, Introduction, in John Smith, Book Title at xiii (2020)`

---

### Rule 15.7: Serial Number
**Content:** Include series information for numbered publications.

**Key Requirements:**
- Include series name and number after title or in parenthetical
- Examples include UN documents, university working papers

**Format Examples:**
- UN Document: `U.N. Doc. A/54/PV.23 (1999)`
- Working Paper: `Author, Title, Univ. of X Working Paper No. 123 (2020)`

---

### Rule 15.8: Special Citation Forms
**Content:** Special formats for looseleaf services, court rules pamphlets, etc.

**Key Requirements:**
- Follow citation guide for specific forms
- Provide author (if any), title, and necessary information
- Looseleafs often require date of last update
- Include edition and year

**Example:**
`2 Charles Alan Wright et al., Federal Practice & Procedure § 1234 (3d ed. 2019)`

---

### Rule 15.9: Electronic Databases and Online Sources
**Content:** Citation format for online books and reports.

**Key Requirements:**
- Cite to print format if possible
- If online only: author, title, (year), with "available at" URL
- For e-books in Westlaw: may indicate database if relevant
- Bluebook treats online books by their print citation

**Format:**
`Author, Title (year), available at https://example.com`

---

### Rule 15.10: Short Citation Forms
**Content:** Subsequent citations after full citation.

**Short Form Examples:**
- `Doe, supra note 5, at 100` (author's last name)
- `Id. at 100` (if immediately preceding note is same source)
- Use "hereinafter" for long titles: `... ("Short Title")` then `Short Title, supra`

#### Rule 15.10.1: Short Forms for Works in Collection
**Content:** Short forms for chapters or essays in collections.

**Format:**
`Chapter Author Last Name, supra note X, at page`

**Key Requirements:**
- Use chapter author's last name
- Include "supra note X"
- May need hereinafter to avoid confusion between multiple chapters

**Example:**
`Doe, supra note 12, at 45`

---

## Regex Patterns for Rule 15 Components

### 1. AUTHOR NAMES

#### Pattern 1a: Single Author (Full Name)
```regex
^[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\s[A-Z][a-z]+(?:\s(?:Jr\.|Sr\.|III|IV|II|V))?(?:,\s)
```
**Matches:** `John Smith, ` or `Mary Jane Doe, ` or `James Wilson Jr., `

#### Pattern 1b: Two Authors (Full Names)
```regex
^[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\s[A-Z][a-z]+\s&\s[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\s[A-Z][a-z]+(?:,\s)
```
**Matches:** `John Smith & Jane Doe, ` or `Mary Jane Doe & Robert Johnson, `

#### Pattern 1c: Multiple Authors with "et al."
```regex
^[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\s[A-Z][a-z]+\set\sal\.(?:,\s)
```
**Matches:** `John Smith et al., ` or `Mary Brown et al., `

#### Pattern 1d: Institutional Author
```regex
^(?:U\.S\.|United States)?\s?[A-Z][a-z]+(?:\s[A-Z][a-z]+)*(?:\s(?:Agency|Bureau|Commission|Department|Office|Board))?(?:,\s)
```
**Matches:** `EPA, ` or `U.S. Environmental Protection Agency, ` or `Federal Trade Commission, `

#### Pattern 1e: Author with Suffixes (Jr., Sr., III, etc.)
```regex
^[A-Z][a-z]+\s[A-Z][a-z]+\s(?:Jr\.|Sr\.|III|II|IV|V)(?:,\s)
```
**Matches:** `James Wilson Jr., ` or `Robert Jones III, `

---

### 2. TITLES (ITALICIZATION)

#### Pattern 2a: Basic Title (Italicized Format)
```regex
\*[A-Z][a-zA-Z\s:'-]+\*
```
**Matches:** `*Title in Italics*` or `*Another Title: Subtitle*`

#### Pattern 2b: Title with Proper Capitalization (Title Case)
```regex
(?:^|\s)(?:The|A|An)?\s?(?:[A-Z][a-z]+)(?:\s(?:[A-Z][a-z]+|and|or|of|in|on|at|by|for|from))*\s*(?::\s[A-Z][a-z]+.*)?
```
**Matches:** `The Constitution`, `Rules and Procedures`, `Title: Subtitle Format`

#### Pattern 2c: Title with Excluded Words (articles, conjunctions, prepositions)
```regex
(?:The|A|An|and|or|but|nor|for|yet|so|of|in|on|at|by|to|from|with)
```
**Matches:** Words that should NOT be capitalized (except at start)

#### Pattern 2d: Complete Title Citation with Italics and Proper Format
```regex
(\*[A-Z][a-zA-Z\s:'-]+\*)\s\((?:(\d{1,2}(?:st|nd|rd|th)\s)?(?:ed\.|ed)\.?)?\s?(\d{4})\)
```
**Matches:** `*Title of Book* (2d ed. 2020)` or `*Title* (2020)`

---

### 3. EDITION NUMBERS

#### Pattern 3a: Edition Indicator (Ordinal + "ed.")
```regex
(\d{1,2})(?:st|nd|rd|th)\s(?:ed\.|ed)
```
**Matches:** `2nd ed.`, `3rd ed.`, `4th ed.`, `1st ed.`, `21st ed.`

#### Pattern 3b: Edition in Full Citation Context
```regex
\((?:(\d{1,2})(?:st|nd|rd|th)\s(?:ed\.|ed)\s)?(\d{4})\)
```
**Matches:** `(2d ed. 2020)`, `(3rd ed. 2019)`, `(2020)`

#### Pattern 3c: Multiple Editions (Volume with Edition)
```regex
vol\.\s(\d+)\s(?:(\d{1,2})(?:st|nd|rd|th)\s(?:ed\.|ed))?
```
**Matches:** `vol. 2 2d ed.` or `vol. 3`

#### Pattern 3d: Edition Ordinal Suffix Recognition
```regex
(?:1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th|11th|12th|13th|14th|15th|16th|17th|18th|19th|20th|21st|22nd|23rd|24th|25th)
```
**Matches:** All edition ordinates from 1st to 25th

---

### 4. PUBLISHERS

#### Pattern 4a: Basic Publisher Name
```regex
\(([A-Z][a-zA-Z\s&.,'-]+)\s(\d{4})\)
```
**Matches:** `(Harvard University Press 2020)`, `(Oxford & Sons 2019)`

#### Pattern 4b: Publisher Abbreviations (Common Legal Publishers)
```regex
(?:West|Lexis|Westlaw|CCH|Bloomberg|Thomson|Oxford|Cambridge|Kluwer|Springer|Routledge|Yale|Harvard|Stanford|Columbia)
```
**Matches:** Common legal publisher names

#### Pattern 4c: University Press Format
```regex
(?:Univ|University)\s\.?\s(?:of\s)?([A-Z][a-z]+)\s(?:Press|Pr\.)
```
**Matches:** `Univ. of Chicago Press`, `University of Yale Press`, `Univ. of Texas Pr.`

#### Pattern 4d: Publisher with Edition and Date
```regex
\(([A-Z][a-zA-Z\s&.,'-]+(?:\s(?:\d{1,2}(?:st|nd|rd|th)\s(?:ed\.|ed))?)?)\s(\d{4})\)
```
**Matches:** `(Harvard University Press 2d ed. 2020)`, `(Oxford 2019)`

#### Pattern 4e: Organization/Agency as Publisher
```regex
(?:U\.S\.|United States)?\s?(?:Government|Environmental|Federal|National)?\s?[A-Z][a-zA-Z\s&.,'-]+(?:\s(?:Agency|Bureau|Commission|Department|Office))?
```
**Matches:** `EPA`, `U.S. Environmental Protection Agency`, `Federal Trade Commission`

---

### 5. DATES

#### Pattern 5a: Year Only (Publication Year)
```regex
\((\d{4})\)
```
**Matches:** `(2020)`, `(1999)`, `(2025)`

#### Pattern 5b: Year with Edition
```regex
\((\d{1,2})?(?:st|nd|rd|th)?\s?(?:ed\.|ed)\.?\s?(\d{4})\)
```
**Matches:** `(2d ed. 2020)`, `(3rd ed. 2019)`, `(ed. 2020)`

#### Pattern 5c: Full Date (Month, Day, Year) - for unpublished works
```regex
\((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s\d{1,2},?\s\d{4}\)
```
**Matches:** `(Jan. 5, 2020)`, `(December 25, 2020)`, `(Feb 14 2019)`

#### Pattern 5d: Date Range (if applicable)
```regex
(\d{4})-(\d{4})
```
**Matches:** `2000-2020`, `1995-2005`

#### Pattern 5e: Date in Specific Citation Context
```regex
at\s(?:([a-z]+)\s)?(\d{1,3})?\s\(([A-Za-z]+\.?\s)?(\d{1,2})?,?\s?(\d{4})\)
```
**Matches:** `at xiii (2020)`, `at 123 (2d ed. 2020)`

---

### 6. PAGE NUMBERS

#### Pattern 6a: Starting Page (First Page of Work)
```regex
(?:^|\s)(\d{1,4})(?:\s|,)
```
**Matches:** `123 ` or `42, ` or `999 `

#### Pattern 6b: Page Range (Starting and Ending Pages)
```regex
(\d{1,4}),?\s*(?:at\s)?(\d{1,4})
```
**Matches:** `123, 150` or `123 150` or `at 456`

#### Pattern 6c: Pinpoint Page Citation
```regex
(?:,\s)?at\s(\d{1,4})
```
**Matches:** `, at 456` or `at 123` or `, at 999`

#### Pattern 6d: Roman Numeral Pages (for introductions, etc.)
```regex
at\s(?:[ivxlcdm]+)
```
**Matches:** `at xiii`, `at iv`, `at xlii`

#### Pattern 6e: Complete Page Citation in Context
```regex
(?:^|\s)(\d{1,4})(?:,?\s(\d{1,4}))?(?:\s\()?
```
**Matches:** `123`, `123, 456`, `123 (` - for standalone page numbers

#### Pattern 6f: Section Number Citation
```regex
§\s?(\d{1,4})(?:\.(\d{1,4}))?
```
**Matches:** `§ 1234`, `§ 42.5`, `§1234`

#### Pattern 6g: Multiple Pinpoints (For complex citations)
```regex
(?:^|\s)(\d{1,4}),\s(\d{1,4}),\s(\d{1,4})(?:\s|,|$)
```
**Matches:** `123, 456, 789 ` - multiple non-contiguous pages

---

## Combined Citation Regex Patterns

### Pattern 7a: Complete Book Citation (Full Format)
```regex
^([A-Z][a-z]+(?:\s[A-Z][a-z]+)*\s[A-Z][a-z]+(?:\set\sal\.)?),\s(\*?[A-Z][a-zA-Z\s:'-]+\*?)\s(?:\((\d{1,2})?(?:st|nd|rd|th)?\s?(?:ed\.|ed)\.?\s?(\d{4})\))?$
```
**Matches:** `John Smith, *Title* (2d ed. 2020)` or `Jane Doe, *Book Title* (2020)`

### Pattern 7b: Book Citation with Editor
```regex
^([A-Z][a-z]+.*),\s(\*[A-Z][a-zA-Z\s:'-]+\*)\s\(([A-Z][a-z]+\s[A-Z][a-z]+)\s(?:ed\.|eds\.),?\s?(\d{4})\)$
```
**Matches:** `William Blackstone, *Commentaries on the Laws of England* (John Doe ed., 2020)`

### Pattern 7c: Chapter in Edited Book
```regex
^([A-Z][a-z]+.*),\s"([^"]+)",\sin\s(\*[A-Z][a-zA-Z\s:'-]+\*)\s(\d{1,4}),\s(\d{1,4})\s\(([A-Z][a-z]+.*)\sed\.(?:s)?,?\s(?:(\d{1,2})?(?:st|nd|rd|th)?\s?(?:ed\.|ed)\.?)?\s?(\d{4})\)$
```
**Matches:** `John Doe, "Essay Title", in *Book Title* 123, 456 (Jane Smith ed., 2d ed. 2020)`

### Pattern 7d: Works in Collection with Page Reference
```regex
^([^,]+),\sin\s([^[]+)\s\[(\d+)\]\s\(([^)]+)(?:ed\.|eds\.),?\s(\d{4})\)$
```
**Matches:** `Letter from X to Y (Dec. 1, 1900), in Collected Letters [67] (Editor ed., 2000)`

---

## Validation Patterns

### Pattern 8a: Validate Author Format
```regex
^[A-Z][a-z]+(?:\s[A-Z][a-z]+)*(?:\s&\s[A-Z][a-z]+)?(?:\set\sal\.)?$
```
**Validates:** Proper author name format

### Pattern 8b: Validate Year Format
```regex
^[12]\d{3}$
```
**Validates:** Years between 1000-2999

### Pattern 8c: Validate Page Number Format
```regex
^\d{1,4}$
```
**Validates:** Page numbers 1-9999

### Pattern 8d: Validate Edition Format
```regex
^(?:\d{1,2})?(?:st|nd|rd|th)?\s?(?:ed\.|ed)?$
```
**Validates:** Edition notation

### Pattern 8e: Validate Title Format (Capitalization Check)
```regex
^[A-Z][a-z]+(?:(?:\s(?:and|or|but|nor|for|yet|so|of|in|on|at|by|to|from|with))?(?:\s[A-Z][a-z]+))*(?::\s[A-Z][a-z]+.*)?$
```
**Validates:** Proper title capitalization rules

---

## Regex Pattern Examples by Citation Type

### Example 1: Basic Book Citation
**Citation:** `John Smith, *Constitutional Law* (2d ed. 2020)`

**Applicable Patterns:**
- Author: `^[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\s[A-Z][a-z]+`
- Title: `\*[A-Z][a-zA-Z\s:'-]+\*`
- Edition: `(\d{1,2})(?:st|nd|rd|th)\s(?:ed\.|ed)`
- Year: `\((?:(\d{1,2})(?:st|nd|rd|th)\s(?:ed\.|ed)\s)?(\d{4})\)`

### Example 2: Chapter in Edited Collection
**Citation:** `James Thompson, "Federal Powers", in *Constitutional Law Studies* 145, 167 (Sarah Wilson ed., 3d ed. 2019)`

**Applicable Patterns:**
- Chapter Author: `^[A-Z][a-z]+(?:\s[A-Z][a-z]+)*`
- Chapter Title (in quotes): `"([^"]+)"`
- Book Title (italicized): `in\s(\*[A-Z][a-zA-Z\s:'-]+\*)`
- Starting Page: `(\d{1,4}),`
- Pinpoint Page: `,\s(\d{1,4})`
- Editor: `\(([A-Z][a-z]+\s[A-Z][a-z]+)\sed\.`
- Edition: `(\d{1,2})(?:st|nd|rd|th)\s(?:ed\.|ed)`
- Year: `(\d{4})\)`

### Example 3: Works with Multiple Authors
**Citation:** `Michael Brown & Jennifer Davis, *Administrative Law Treatise* (West 2021)`

**Applicable Patterns:**
- Multiple Authors: `^[A-Z][a-z]+.*\s[A-Z][a-z]+\s&\s[A-Z][a-z]+.*\s[A-Z][a-z]+`
- Title: `\*[A-Z][a-zA-Z\s:'-]+\*`
- Publisher: `\(([A-Z][a-zA-Z\s&.,'-]+)\s(\d{4})\)`

### Example 4: Multi-Author with "et al."
**Citation:** `Robert Jenkins et al., *Federal Rules of Procedure* (5th ed. 2022)`

**Applicable Patterns:**
- Multiple Authors (et al.): `^[A-Z][a-z]+.*\set\sal\.`
- Title: `\*[A-Z][a-zA-Z\s:'-]+\*`
- Edition: `(\d{1,2})(?:st|nd|rd|th)\s(?:ed\.|ed)`
- Year: `(\d{4})\)`

### Example 5: Government/Institutional Author
**Citation:** `U.S. Environmental Protection Agency, *Environmental Regulations Handbook* (2020)`

**Applicable Patterns:**
- Institutional Author: `^(?:U\.S\.|United States)?\s?[A-Z][a-z]+.*(?:Agency|Bureau|Commission|Department)`
- Title: `\*[A-Z][a-zA-Z\s:'-]+\*`
- Year: `(\d{4})\)`

---

## Practical Implementation Notes

### For Citation Parsing:
1. **Author extraction:** Use Pattern 1a-e to identify and validate author names
2. **Title validation:** Use Pattern 2a-d to confirm proper italicization and capitalization
3. **Edition normalization:** Use Pattern 3a-d to standardize edition notation
4. **Publisher identification:** Use Pattern 4a-e to locate and classify publishers
5. **Date validation:** Use Pattern 5a-e to ensure proper date formatting
6. **Page parsing:** Use Pattern 6a-g to extract and validate page numbers

### For Citation Validation:
- Use Pattern 8a-e to validate individual components before assembly
- Combine patterns to validate complete citations (Pattern 7a-d)
- Check for missing required elements (author, title, year)

### For Citation Reformatting:
- Apply standardized patterns to ensure consistency
- Convert edition notations to standard format (e.g., "2nd ed." to "2d ed.")
- Validate all parenthetical information
- Ensure proper capitalization in titles

---

## Related Bluebook Rules

- **Rule 15.1:** Author information
- **Rule 15.2:** Editors and translators
- **Rule 15.3:** Title formatting and capitalization
- **Rule 15.4:** Edition, publisher, and date
- **Rule 15.5:** Shorter works in collections
- **Rule 15.6:** Prefaces, forewords, introductions
- **Rule 15.7:** Serial numbers
- **Rule 15.8:** Special citation forms
- **Rule 15.9:** Electronic sources
- **Rule 15.10:** Short citation forms

For cross-references: See Rules 16-18 for periodicals, unpublished sources, and electronic media.

