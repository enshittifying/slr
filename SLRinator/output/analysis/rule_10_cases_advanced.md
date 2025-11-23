# Bluebook Rule 10: Cases - Advanced Topics

## Overview
This document covers advanced case citation topics including short forms, subsequent citations, prior and subsequent history, special case types, and Redbook (Stanford Law Review) specific rules. Each section includes practical detection patterns.

---

## Rule 10.9: Short Forms for Cases

### Basic Short Form Rules

**Requirements for Short Form:**
- Case must have been cited in full within preceding **five footnotes** (Redbook Rule 10.9)
- Short form must be unambiguous

**Three Acceptable Short Forms:**

1. **Case Name Short Form:**
   ```
   Roe, 410 U.S. at 116.
   ```

2. **Id. (Immediately Preceding):**
   ```
   Id. at 116.
   ```

3. **Shortened Case Name:**
   ```
   Brown, 347 U.S. at 495.
   ```

**DO NOT USE:**
- ✗ "Supra" for cases
- ✗ "Hereinafter" for cases

### Short Form Components

**Full Citation:**
```
Brown v. Board of Education, 347 U.S. 483, 495 (1954).
```

**Short Forms:**
```
Brown, 347 U.S. at 495.
Board of Education, 347 U.S. at 495.
Id. at 495. (if immediately preceding citation)
```

### Detection Patterns

**Find short form case citations:**
```regex
^(?:Id\.|[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)?),\s+\d+\s+[A-Z][^\s]+\s+at\s+\d+\.?$
```

**Find Id. citations:**
```regex
^Id\.\s+at\s+\d+\.?$
```

**Validate "at" in pinpoint:**
```regex
\bat\s+\d+
```

### Redbook Rule 10.9: Five-Footnote Rule

**SLR Specific Rule**: If case has NOT been cited within preceding five footnotes, use full citation (not short form)

**This applies even if:**
- Authority is named in text
- It was cited fully elsewhere in same footnote

**Detection Strategy:**
1. Track last citation position for each case
2. Count footnotes since last citation
3. Flag if short form used beyond five footnotes

---

## Rule 10.7: Prior and Subsequent History

### Rule 10.7.1: Explanatory Phrases and Weight

**Include History When:**
1. Case was affirmed, reversed, or modified on appeal
2. Certiorari denied (within two years only)
3. History is significant to analysis

**Common Explanatory Phrases (Table T8):**

| Phrase | Meaning | Usage |
|--------|---------|-------|
| aff'd | affirmed | Lower court decision upheld |
| rev'd | reversed | Lower court decision overturned |
| modified | modified | Decision changed in part |
| cert. denied | certiorari denied | Supreme Court declined review |
| cert. granted | certiorari granted | Supreme Court will review |
| vacated | vacated | Decision nullified |
| overruled by | overruled by | No longer good law |
| abrogated by | abrogated by | Implicitly overruled |
| superseded by | superseded by | Replaced by statute |

### Subsequent History Format

**Basic Format:**
```
Lower Court Citation, aff'd/rev'd, Higher Court Citation.
```

**Examples:**

**Affirmed:**
```
Smith v. Jones, 100 F.3d 200 (9th Cir. 1998), aff'd, 525 U.S. 100 (1999).
```

**Reversed:**
```
Miranda v. Arizona, 384 F.2d 436 (9th Cir. 1967), rev'd, 384 U.S. 436 (1966).
```

**Cert. Denied (within 2 years):**
```
Smith v. Jones, 100 F.3d 200 (9th Cir. 2019), cert. denied, 140 S. Ct. 500 (2020).
```

**Cert. Denied (over 2 years - OMIT):**
```
Smith v. Jones, 100 F.3d 200 (9th Cir. 2017).
[Do NOT include cert. denied from 2020]
```

### Detection Patterns

**Find subsequent history:**
```regex
,\s+(aff'd|rev'd|modified|vacated|cert\.\s+denied|cert\.\s+granted),\s+\d+\s+[A-Z]
```

**Find negative treatment:**
```regex
,\s+(overruled by|abrogated by|superseded by|disapproved by)\s+[A-Z]
```

**Validate cert. denied timing:**
Check if cert. denial is within 2 years of decision

### Redbook Rule 10.1: Citechecking Cases

**SLR Requirement**: For each cited case, verify:
1. Case is still good law
2. No negative treatment (overruled, abrogated, superseded)
3. Add parenthetical if negative treatment exists

**Examples:**
```
Lochner v. New York, 198 U.S. 45 (1905) (overruled by West Coast Hotel Co. v. Parrish, 300 U.S. 379 (1937)).
```

**Pending Review:**
```
Smith v. Jones, 100 F.3d 200 (9th Cir. 2023) (cert. granted).
Doe v. Roe, 500 F.3d 100 (5th Cir. 2024) (reh'g en banc granted).
```

### Rule 10.7.2: Different Case Name on Appeal

When case name changes on appeal, use "sub nom." (under the name):

**Format:**
```
Smith v. Jones, 100 F.3d 200 (9th Cir. 1998), aff'd sub nom. Jones v. Smith, 525 U.S. 100 (1999).
```

**Detection Pattern:**
```regex
\bsub nom\.\s+[A-Z][A-Za-z\s]+v\.\s+[A-Z]
```

### Redbook Rule 10.17: Remand History Phrases

**SLR Deviation**: Include BOTH remands (contrary to Bluebook)

**Bluebook**: Omit first remand
**Redbook**: Include both

**Example:**
```
Smith v. Jones, 100 F.3d 200 (9th Cir. 1998), rev'd and remanded, 525 U.S. 100 (1999), aff'd in relevant part on remand, 200 F.3d 300 (9th Cir. 2000).
```

**Detection Pattern:**
```regex
\b(?:rev'd and remanded|aff'd.*on remand)\b
```

---

## Rule 10.8: Special Citation Forms

### Rule 10.8.1: Pending and Unreported Cases

**Unreported/Unpublished Cases:**

**Format with Database:**
```
Smith v. Jones, No. 20-1234, 2020 WL 123456, at *3 (S.D.N.Y. Mar. 15, 2020).
```

**Components:**
- Docket number: No. 20-1234
- Database: WL (Westlaw) or LEXIS
- Star pagination: *3
- Full date required
- Court required

**Format with Slip Opinion:**
```
Smith v. Jones, No. 20-1234, slip op. at 5 (S.D.N.Y. Mar. 15, 2020).
```

### Redbook Rule 10.10-10.11: Unreported Cases

**SLR Preference Order:**
1. **Free sources** (court websites, news outlets, SCOTUSblog)
2. **Official PDFs** from court websites
3. **Database citations** (only if no free source available)

**Supreme Court Example (Redbook):**
```
Nat'l Fed'n of Indep. Bus. v. Dep't of Labor, Occupational Safety & Health Admin., No. 21A244, 595 U.S. ___ (Jan. 13, 2022) (per curiam), https://www.supremecourt.gov/opinions/21pdf/21a244_hgci.pdf.
```

**DO NOT use:**
- ✗ "2022 WL ..." for 2022 cases if official version available
- ✗ SSRN unless no other source available
- ✗ Database citations when free source exists

**Detection Pattern for Database Citations:**
```regex
\d{4}\s+WL\s+\d+|\d{4}\s+LEXIS\s+\d+
```

### Redbook Rule 10.12: Docket Numbers (Federal)

**Include docket numbers for:**
1. Unpublished cases
2. Cases from 1880 or earlier (even if published)

**Examples:**
```
Smith v. Jones, No. 20-1234, 2020 WL 123456 (S.D.N.Y. Mar. 15, 2020).
Marbury v. Madison, No. 000 (U.S. Feb. 11, 1803).
```

**Do NOT include for:**
- Published cases after 1880

**Detection Pattern:**
```regex
No\.\s+\d{2,4}-\d+
```

### Redbook Rule 10.13: Consolidated Cases

**Rule**: Include docket number ONLY for case author references (not all consolidated cases)

**Wrong:**
```
Smith v. Jones, Nos. 20-1234, 20-1235, 20-1236, 2020 WL 123456 (S.D.N.Y. 2020).
```

**Right:**
```
Smith v. Jones, No. 20-1234, 2020 WL 123456 (S.D.N.Y. 2020).
```

### Rule 10.8.3: Briefs, Court Filings, and Transcripts

**Brief Format:**
```
Brief for Petitioner at 10, Smith v. Jones, 525 U.S. 100 (1999) (No. 98-123).
```

**Components:**
- Document type: Brief for Petitioner
- Page: at 10
- Case name: Smith v. Jones
- Reporter: 525 U.S. 100
- Year: (1999)
- Docket: (No. 98-123)

**Transcript Format:**
```
Transcript of Oral Argument at 15, Smith v. Jones, 525 U.S. 100 (1999) (No. 98-123).
```

**Complaint/Motion Format:**
```
Complaint at 5, Smith v. Jones, No. 20-1234 (S.D.N.Y. filed Jan. 5, 2020).
```

### Redbook Rules 10.5-10.7: Court Filings

**Rule 10.5: Amicus Brief Titles**
- If title starts with "Brief for/of": Use full title
- If title doesn't: Insert "Brief for" at beginning

**Rule 10.6: Parallel Citations**
Always include parallel to PDF/ECF page:
```
Brief for Appellant at 4, Smith v. Jones, No. 20-1234 (9th Cir. filed Jan. 5, 2020), 2020 WL 12345, at *2.
```

**Rule 10.7: Before/After Decision**
- **Before decision**: No court or year in filing citation
- **After decision**: Include court and year

**Example (before decision):**
```
Brief for Petitioner at 10, Smith v. Jones (No. 98-123).
```

**Example (after lower court decision, citing appellate brief):**
```
Brief for Appellant at 10, Smith v. Jones, 100 F.3d 200 (9th Cir. 1998) (No. 98-1234).
```

### Detection Patterns

**Find brief citations:**
```regex
Brief for [A-Za-z\s]+at\s+\d+
```

**Find transcript citations:**
```regex
Transcript of [A-Za-z\s]+at\s+\d+
```

**Find ECF citations:**
```regex
ECF No\.\s+\d+
```

---

## Rule 10.6.1(f): Unpublished Opinions

**Redbook Rule 10.8**: Add parenthetical for unpublished opinions

**Must indicate:**
- Memorandum decision
- Order
- Unpublished

**Examples:**
```
Smith v. Jones, No. 20-1234, 2020 WL 123456 (9th Cir. Mar. 15, 2020) (mem.).
Doe v. Roe, No. 19-5678, 2019 WL 234567 (S.D.N.Y. June 1, 2019) (order).
```

**Exception**: Jurisdictions issuing ONLY unreported decisions (no parenthetical needed)

**Detection Pattern:**
```regex
\((?:mem\.|memorandum|order|unpublished)\)
```

---

## Rule 11: Constitutions

### Basic Format

**U.S. Constitution:**
```
U.S. Const. art. I, § 8.
U.S. Const. amend. XIV, § 1.
U.S. Const. amend. IV.
```

**State Constitutions:**
```
N.Y. Const. art. VI, § 7.
Cal. Const. art. I, § 1.
```

### Format Components

**Article Citation:**
```
U.S. Const. art. [Roman numeral], § [number].
```

**Amendment Citation:**
```
U.S. Const. amend. [Roman/Arabic], § [number].
```

**Preamble:**
```
U.S. Const. pmbl.
```

### Key Rules

1. **No Dates**: Never include year for constitutions
2. **Abbreviations**:
   - art. = article
   - § = section
   - amend. = amendment
   - pmbl. = preamble
3. **Repealed Provisions**: If citing repealed, add parenthetical:
   ```
   U.S. Const. art. I, § 2, cl. 3 (repealed 1868).
   ```

### Redbook Rule 11.1: U.S. Constitution

**SLR Official Source**: National Archives
- URL: https://www.archives.gov/founding-docs/constitution-transcript

**SLR Rule**: Do NOT cite as "U.S. CONST." (not to printed edition)

**Instead**: Write out part/amendment without "U.S. CONST." prefix when context clear

**Context Clear:**
```
The Fourth Amendment protects against unreasonable searches.
```

**Citation Needed:**
```
U.S. Const. amend. IV.
```

### Detection Patterns

**Find constitution citations:**
```regex
(?:[A-Z][a-z\.]+\s+)?Const\.\s+(?:art\.|amend\.|pmbl\.)
```

**Validate article format:**
```regex
\bart\.\s+[IVX]+(?:,\s+§\s+\d+)?
```

**Validate amendment format:**
```regex
\bamend\.\s+(?:[IVX]+|\d+)(?:,\s+§\s+\d+)?
```

---

## Special Case Types

### In Re Proceedings

**Format:**
```
In re Gault, 387 U.S. 1 (1967).
In re Estate of Smith, 100 Cal. App. 3d 200 (Ct. App. 1990).
```

**Pattern:**
```regex
^In re\s+[A-Z]
```

### Ex Parte Proceedings

**Format:**
```
Ex parte Quirin, 317 U.S. 1 (1942).
Ex parte Young, 209 U.S. 123 (1908).
```

**Pattern:**
```regex
^Ex parte\s+[A-Z]
```

### Administrative Adjudications

**Format:**
```
In re XYZ Corp., 123 F.T.C. 456 (2020).
NLRB v. Jones & Laughlin Steel Corp., 301 U.S. 1 (1937).
```

**With Agency:**
```
Smith v. Commissioner, 100 T.C. 200 (1993).
```

### Bankruptcy Cases

**Format:**
```
In re Johns-Manville Corp., 36 B.R. 727 (Bankr. S.D.N.Y. 1984).
```

**Components:**
- In re format
- B.R. reporter (Bankruptcy Reporter)
- Bankruptcy court designation: Bankr. [District]

---

## 20 Advanced Examples with Detection Patterns

### Example 1: Short Form with Id.
**Full Citation (Footnote 10):**
```
Brown v. Board of Education, 347 U.S. 483, 495 (1954).
```
**Short Form (Footnote 11):**
```
Id. at 496.
```
**Pattern Check:**
- ✓ Id. format
- ✓ "at" before pinpoint
- ✓ Immediately following

### Example 2: Short Form with Case Name
**Full Citation (Footnote 10):**
```
Miranda v. Arizona, 384 U.S. 436, 444 (1966).
```
**Short Form (Footnote 14):**
```
Miranda, 384 U.S. at 450.
```
**Pattern Check:**
- ✓ Within five footnotes
- ✓ Reporter included
- ✓ "at" before pinpoint

### Example 3: Affirmed on Appeal
**Citation:**
```
Smith v. Jones, 100 F.3d 200 (9th Cir. 1998), aff'd, 525 U.S. 100 (1999).
```
**Pattern Check:**
- ✓ Subsequent history: aff'd
- ✓ Comma before subsequent history
- ✓ Full citation of affirming court

### Example 4: Reversed on Appeal
**Citation:**
```
Doe v. Roe, 500 F.3d 100 (5th Cir. 2005), rev'd, 547 U.S. 200 (2006).
```
**Pattern Check:**
- ✓ Subsequent history: rev'd
- ✓ Higher court citation

### Example 5: Cert. Denied (Recent)
**Citation:**
```
Smith v. California, 100 F.3d 200 (9th Cir. 2023), cert. denied, 144 S. Ct. 100 (2024).
```
**Pattern Check:**
- ✓ Within 2 years
- ✓ cert. denied format

### Example 6: Cert. Denied (Old - Omit)
**Wrong:**
```
Smith v. Jones, 100 F.3d 200 (9th Cir. 2010), cert. denied, 563 U.S. 900 (2011).
```
**Right:**
```
Smith v. Jones, 100 F.3d 200 (9th Cir. 2010).
```
**Pattern Check:**
- ✓ More than 2 years - omit cert. denied

### Example 7: Overruled Case
**Citation:**
```
Lochner v. New York, 198 U.S. 45 (1905) (overruled by West Coast Hotel Co. v. Parrish, 300 U.S. 379 (1937)).
```
**Pattern Check:**
- ✓ Negative treatment parenthetical
- ✓ Overruling case cited

### Example 8: Sub Nom. (Name Change)
**Citation:**
```
Smith v. Jones, 100 F.3d 200 (9th Cir. 1998), aff'd sub nom. Jones v. United States, 525 U.S. 100 (1999).
```
**Pattern Check:**
- ✓ sub nom. format
- ✓ New case name follows

### Example 9: Unreported Case (Westlaw)
**Citation:**
```
Doe v. University of Kentucky, No. 20-1234, 2020 WL 123456, at *3 (E.D. Ky. Mar. 15, 2020).
```
**Pattern Check:**
- ✓ Docket number
- ✓ WL citation
- ✓ Star pagination: *3
- ✓ Full date

### Example 10: Unreported Case (Court Website - Redbook Preferred)
**Citation:**
```
Nat'l Fed'n of Indep. Bus. v. OSHA, No. 21A244, 595 U.S. ___, at 2 (Jan. 13, 2022) (per curiam), https://www.supremecourt.gov/opinions/21pdf/21a244_hgci.pdf.
```
**Pattern Check:**
- ✓ Free source (court website)
- ✓ URL included
- ✓ No WL citation
- ✓ Per curiam noted

### Example 11: Brief Citation
**Citation:**
```
Brief for Petitioner at 10, Obergefell v. Hodges, 576 U.S. 644 (2015) (No. 14-556).
```
**Pattern Check:**
- ✓ Document type: Brief for Petitioner
- ✓ Page: at 10
- ✓ Case citation
- ✓ Docket number

### Example 12: Oral Argument Transcript
**Citation:**
```
Transcript of Oral Argument at 25, United States v. Texas, 579 U.S. 547 (2016) (No. 15-674).
```
**Pattern Check:**
- ✓ Transcript designation
- ✓ Page number
- ✓ Case and docket

### Example 13: Complaint
**Citation:**
```
Complaint at 5, Smith v. Jones, No. 20-cv-1234 (S.D.N.Y. filed Jan. 5, 2020).
```
**Pattern Check:**
- ✓ Document type: Complaint
- ✓ No case citation (before decision)
- ✓ "filed" date

### Example 14: Unpublished Memorandum
**Citation:**
```
United States v. Smith, No. 19-1234, 2020 WL 123456 (9th Cir. Feb. 10, 2020) (mem.).
```
**Pattern Check:**
- ✓ Memorandum parenthetical
- ✓ Unreported format

### Example 15: En Banc with Subsequent History
**Citation:**
```
United States v. Microsoft Corp., 147 F.3d 935 (D.C. Cir. 1998), rev'd en banc, 253 F.3d 34 (D.C. Cir. 2001).
```
**Pattern Check:**
- ✓ "rev'd en banc" combined
- ✓ Same circuit cited twice

### Example 16: Constitutional Amendment
**Citation:**
```
U.S. Const. amend. XIV, § 1.
```
**Pattern Check:**
- ✓ amend. abbreviation
- ✓ Roman numeral: XIV
- ✓ Section included

### Example 17: State Constitution
**Citation:**
```
Cal. Const. art. I, § 7.
```
**Pattern Check:**
- ✓ State abbreviation
- ✓ Article in Roman numerals
- ✓ No date

### Example 18: In Re Proceeding with Short Form
**Full Citation:**
```
In re Gault, 387 U.S. 1 (1967).
```
**Short Form:**
```
Gault, 387 U.S. at 10.
```
**Pattern Check:**
- ✓ "In re" omitted in short form
- ✓ Just last name

### Example 19: Public Domain Citation
**Citation:**
```
State v. Ruiz, 2015 ND 182, ¶ 15, 867 N.W.2d 766, 770.
```
**Pattern Check:**
- ✓ Year: 2015
- ✓ State: ND
- ✓ Decision number: 182
- ✓ Paragraph pinpoint: ¶ 15
- ✓ Parallel citation

### Example 20: Early Reporter with Short Form
**Full Citation:**
```
Marbury v. Madison, 5 U.S. (1 Cranch) 137 (1803).
```
**Short Form (Redbook 10.14):**
```
1 Cranch at 140.
```
**Pattern Check:**
- ✓ Volume number included in short form
- ✓ Reporter name (Cranch)
- ✓ "at" before pinpoint

---

## Advanced Detection Strategies

### Strategy 1: Validate Short Form Distance

**Algorithm:**
1. Parse all case citations in document
2. Build citation index: case_name → [footnote_positions]
3. For each short form:
   - Find corresponding full citation
   - Calculate footnote distance
   - Flag if > 5 footnotes

**Pseudocode:**
```python
def validate_short_form(short_form_footnote, case_name):
    last_full_cite = find_last_full_citation(case_name, short_form_footnote)
    if last_full_cite is None:
        return "ERROR: No full citation found"
    distance = short_form_footnote - last_full_cite
    if distance > 5:
        return "ERROR: Beyond five-footnote rule"
    return "VALID"
```

### Strategy 2: Check Subsequent History Timing

**For cert. denied:**
1. Extract decision year
2. Extract cert. denied year
3. Calculate difference
4. Flag if > 2 years

**Pattern:**
```regex
(\d{4})\).*cert\.\s+denied.*\((\d{4})\)
```

### Strategy 3: Validate Reporter Series Chronology

**Check if reporter series matches year:**

| Reporter | Years | Valid Years |
|----------|-------|-------------|
| F. | 1880-1924 | 1880-1924 |
| F.2d | 1924-1993 | 1924-1993 |
| F.3d | 1993-2021 | 1993-2021 |
| F.4th | 2021-present | 2021+ |
| F. Supp. | 1932-1998 | 1932-1998 |
| F. Supp. 2d | 1998-2014 | 1998-2014 |
| F. Supp. 3d | 2014-present | 2014+ |

**Validation:**
```python
def validate_reporter_year(reporter, year):
    reporter_ranges = {
        "F.3d": (1993, 2021),
        "F.4th": (2021, 2030),
        # etc.
    }
    if reporter in reporter_ranges:
        min_year, max_year = reporter_ranges[reporter]
        if not (min_year <= year <= max_year):
            return f"ERROR: {reporter} not used in {year}"
    return "VALID"
```

### Strategy 4: Detect Missing Pinpoints

**Rule**: Always include pinpoint except:
1. Case named in textual sentence
2. Citing case as whole

**Detection:**
1. Parse citation
2. Check if includes pinpoint (number after first page)
3. Check context (is it in textual sentence?)
4. Flag if no pinpoint and not textual

**Pattern for Citations Without Pinpoints:**
```regex
[A-Z][^,]+v\.\s+[^,]+,\s+\d+\s+[A-Z][^\s]+\s+(\d+)\s+\([^)]+\d{4}\)\.(?!\s+at)
```

### Strategy 5: Validate Parenthetical Order

**Correct Order:**
1. Weight of authority (per curiam, en banc, etc.)
2. Explanatory parenthetical
3. Subsequent history
4. Quoting/citing parenthetical

**Detection:**
```python
def validate_parenthetical_order(citation):
    parentheticals = extract_parentheticals(citation)
    types = [classify_parenthetical(p) for p in parentheticals]
    expected_order = ["weight", "explanatory", "history", "quoting"]
    return check_order(types, expected_order)
```

---

## Common Advanced Citation Errors

### Error 1: Short Form Beyond Five Footnotes
**Problem**: Using short form when full citation not within 5 footnotes
**Detection**: Track citation positions
**Fix**: Use full citation

### Error 2: Including Old Cert. Denials
**Problem**: Including cert. denied from > 2 years ago
**Detection**: Check year difference
**Fix**: Omit cert. denied

### Error 3: Missing Subsequent History
**Problem**: Not including subsequent history for overruled cases
**Detection**: Check Shepard's/KeyCite
**Fix**: Add parenthetical with negative treatment

### Error 4: Using Supra for Cases
**Problem**: Using "supra" instead of proper short form
**Example Wrong**: `Miranda, supra note 10, at 450.`
**Example Right**: `Miranda, 384 U.S. at 450.`

### Error 5: Incorrect Sub Nom. Usage
**Problem**: Not indicating name change with sub nom.
**Fix**: Add "sub nom." when case name changes

### Error 6: Database Citations When Free Source Available
**Problem**: Using WL/LEXIS when official source exists
**Detection**: Check for official source availability
**Fix**: Replace with court website URL (Redbook preference)

### Error 7: Missing Unpublished Parenthetical
**Problem**: Not indicating memorandum/order for unreported decisions
**Detection**: Check if WL/LEXIS citation without reporter
**Fix**: Add (mem.) or (order) parenthetical

### Error 8: Incorrect Brief Format
**Problem**: Wrong order of elements in brief citation
**Correct**: `Brief for Petitioner at 10, Case, Reporter (Year) (No.).`

### Error 9: Including All Consolidated Docket Numbers
**Problem**: Listing all docket numbers instead of just relevant one
**Fix**: Include only docket for case author cites (Redbook 10.13)

### Error 10: Missing Parallel ECF Citation
**Problem**: Not including parallel PDF page for court filings
**Fix**: Add parallel citation to ECF/PDF page (Redbook 10.6)

---

## Validation Checklist - Advanced

Use this checklist for advanced citation validation:

**Short Forms:**
- [ ] Full citation within preceding 5 footnotes
- [ ] Short form unambiguous
- [ ] "at" used before pinpoint
- [ ] No "supra" or "hereinafter"

**Subsequent History:**
- [ ] All relevant subsequent history included
- [ ] Cert. denied only if within 2 years
- [ ] Negative treatment noted (overruled, abrogated, etc.)
- [ ] Sub nom. used for name changes
- [ ] Both remands included (Redbook)

**Special Forms:**
- [ ] Unreported cases: docket number included
- [ ] Unreported cases: full date included
- [ ] Unpublished: (mem.) or (order) parenthetical
- [ ] Free source used instead of database (Redbook)
- [ ] Early cases (pre-1880): docket number included

**Court Filings:**
- [ ] Proper document designation
- [ ] Page reference included
- [ ] Parallel ECF citation (Redbook)
- [ ] Court/year only if after decision (Redbook)
- [ ] Only relevant docket for consolidated cases (Redbook)

**Constitutions:**
- [ ] No date included
- [ ] Proper abbreviations (art., amend., §)
- [ ] Roman numerals for articles
- [ ] Repealed provisions noted if applicable

---

## Master Advanced Detection Patterns

### Comprehensive Short Form Pattern
```regex
^(?:Id\.|[A-Z][A-Za-z'-]+(?:\s+[A-Z][A-Za-z'-]+)?),\s+\d+\s+[A-Z][A-Za-z\.\s]+(?:2d|3d|4th)?\s+at\s+\d+(?:[-–]\d+)?\.?$
```

### Comprehensive Subsequent History Pattern
```regex
,\s+(aff'd|rev'd|modified|vacated|cert\.\s+(?:granted|denied)|overruled by|abrogated by|superseded by)(?:\s+sub nom\.\s+[A-Z][^,]+)?,\s+\d+\s+[A-Z]
```

### Comprehensive Unreported Pattern
```regex
No\.\s+\d{2,4}-(?:cv-|cr-)?\d+,\s+(?:\d{4}\s+WL\s+\d+|slip op\.),?\s+at\s+\*?\d+\s+\([A-Z][^)]+\s+[A-Z][a-z]{2}\.\s+\d{1,2},\s+\d{4}\)
```

### Comprehensive Brief Pattern
```regex
Brief for [A-Za-z\s]+ at \d+,\s+[A-Z][^,]+,\s+(?:\d+\s+[A-Z][^\s]+\s+\d+\s+\([^)]+\)\s+)?\(No\.\s+\d{2,4}-\d+\)
```

---

*Document Size: ~28KB*
*Last Updated: 2025-11-23*
