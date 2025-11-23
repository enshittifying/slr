# Bluebook Rule 10: Cases - Core Citation Rules

## Overview
This document covers the fundamental case citation rules from Bluebook Rule 10, focusing on basic format, case names, reporters, court identification, and dates. Each section includes detection patterns for automated cite checking.

---

## Rule 10.1: Basic Citation Forms

### Full Citation Structure
A complete case citation includes:
1. Case name (italicized/underlined)
2. Volume number
3. Reporter abbreviation
4. First page of case
5. Pinpoint page (if citing specific content)
6. Court abbreviation (if not obvious from reporter)
7. Year of decision

**Standard Format:**
```
Case Name, Volume Reporter Page, Pinpoint (Court Year).
```

**Example:**
```
Roe v. Wade, 410 U.S. 113, 115 (1973).
```

### Detection Pattern
```regex
^([A-Z][^,]+v\.\s+[^,]+),\s+(\d+)\s+([A-Z][^\s]+)\s+(\d+)(?:,\s+(\d+))?\s+\(([^)]+\s+\d{4})\)\.?$
```

**Components:**
- Group 1: Case name
- Group 2: Volume
- Group 3: Reporter
- Group 4: First page
- Group 5: Pinpoint (optional)
- Group 6: Court and year

---

## Rule 10.2: Case Names

### Rule 10.2.1: General Rules for Case Names

#### Name Format Rules
1. **Individuals**: Use last names only (omit first names, middle names, initials)
   - ✓ Correct: `Smith v. Jones`
   - ✗ Wrong: `John Smith v. Robert Jones`

2. **"The" Omission**: Omit "The" as first word of party name
   - ✓ Correct: `New York Times Co. v. Sullivan`
   - ✗ Wrong: `The New York Times Co. v. Sullivan`

3. **Acronyms**: Use widely known acronyms
   - ✓ `NLRB v. Jones & Laughlin Steel Corp.`
   - ✓ `SEC v. Texas Gulf Sulphur Co.`

4. **Abbreviations**: Abbreviate certain words per Table T6
   - Co. (Company)
   - Inc. (Incorporated)
   - Ltd. (Limited)
   - Ass'n (Association)
   - Bros. (Brothers)

5. **Exception**: Do NOT abbreviate first word of party name
   - ✓ Correct: `Association of Data Processing v. Camp`
   - ✗ Wrong: `Ass'n of Data Processing v. Camp`

#### Detection Patterns

**Find first names/initials in case names:**
```regex
\b([A-Z]\.\s+)?([A-Z][a-z]+\s+)?[A-Z][a-z]+\s+v\.\s+
```

**Find "The" at start of party name:**
```regex
\bThe\s+[A-Z][^\s]+\s+v\.
```

**Find unabbreviated company terms (not first word):**
```regex
v\.\s+[^\s,]+\s+(Company|Corporation|Incorporated|Limited|Association|Brothers)\b
```

### Rule 10.2.2: Additional Rules for Case Names in Citations

#### Party Omission Rules
1. **Multiple Parties**: Include only first listed on each side
   - ✓ Correct: `Smith v. Jones` (even if "Smith, Brown, and Green v. Jones and White")
   - Exception: Include "ex rel." parties when needed

2. **Alternative Names**: Omit "AKA", "d/b/a" entries
   - ✓ Correct: `Smith v. Acme Corp.`
   - ✗ Wrong: `Smith v. Acme Corp. d/b/a Best Services`

3. **Procedural Designations**: Use "In re" or "Ex parte" as appropriate
   - `In re Estate of Smith`
   - `Ex parte Johnson`

4. **Geographical Units**: Abbreviate per Table T10 when part of case name
   - ✓ `United States v. Morrison` (named party, no abbreviation)
   - ✓ `Smith v. Cal. Dep't of Corrections` (descriptive, abbreviate)

#### Detection Patterns

**Find multiple parties (& or "and" between parties):**
```regex
([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:&|and)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.
```

**Find d/b/a or AKA:**
```regex
\b(?:d/b/a|a/k/a|AKA|also known as)\b
```

**Find In re/Ex parte formats:**
```regex
^(?:In re|Ex parte)\s+[A-Z]
```

---

## Rule 10.3: Reporters and Other Sources

### Rule 10.3.1: Parallel Citations

**General Rule**: In law reviews, cite only official or most authoritative reporter
**Exception**: Court documents may require parallel citations

**Format with Parallel Citation:**
```
Smith v. Jones, 100 Ill. 2d 200, 250 N.E.2d 300 (1970).
```

**Detection Pattern for Parallel Citations:**
```regex
,\s+\d+\s+[A-Z][^\s]+\s+\d+,\s+\d+\s+[A-Z][^\s]+\s+\d+\s+\(
```

### Rule 10.3.2: Reporters

#### Standard Reporter Abbreviations (Table T1)

**U.S. Supreme Court:**
- U.S. (official, preferred)
- S. Ct. (Supreme Court Reporter)
- L. Ed. (Lawyers' Edition)
- U.S.L.W. (United States Law Week, for recent cases)

**Federal Courts of Appeals:**
- F. (Federal Reporter, 1880-1924)
- F.2d (Federal Reporter, Second Series, 1924-1993)
- F.3d (Federal Reporter, Third Series, 1993-2021)
- F.4th (Federal Reporter, Fourth Series, 2021-present)

**Federal District Courts:**
- F. Supp. (Federal Supplement, 1932-1998)
- F. Supp. 2d (Federal Supplement, Second Series, 1998-2014)
- F. Supp. 3d (Federal Supplement, Third Series, 2014-present)

**State Reporters (Regional):**
- A. / A.2d / A.3d (Atlantic)
- N.E. / N.E.2d / N.E.3d (North Eastern)
- N.W. / N.W.2d (North Western)
- P. / P.2d / P.3d (Pacific)
- S.E. / S.E.2d (South Eastern)
- S.W. / S.W.2d / S.W.3d (South Western)
- So. / So. 2d / So. 3d (Southern)

#### Detection Patterns

**Find reporter citations:**
```regex
\d+\s+(U\.S\.|S\.\s+Ct\.|L\.\s+Ed(?:\.\s+2d)?|F\.\s*(?:2d|3d|4th)?|F\.\s+Supp\.\s*(?:2d|3d)?|A\.\s*(?:2d|3d)?|N\.E\.\s*(?:2d|3d)?|N\.W\.\s*2d?|P\.\s*(?:2d|3d)?|S\.E\.\s*2d?|S\.W\.\s*(?:2d|3d)?|So\.\s*(?:2d|3d)?)\s+\d+
```

**Validate series notation:**
```regex
\b(2d|3d|4th)\b
```
Note: NOT "2nd", "3rd", "4th" - use "2d", "3d", "4th"

### Rule 10.3.3: Public Domain Format

Some jurisdictions use public domain citations (year and decision number):

**Format:**
```
State v. Smith, 1999 ND 45, ¶ 12, 591 N.W.2d 505, 508.
```

**Components:**
- 1999 = Year
- ND = State abbreviation
- 45 = Sequential decision number
- ¶ 12 = Paragraph number (pinpoint)
- Parallel reporter citation follows

**Detection Pattern:**
```regex
\d{4}\s+[A-Z]{2,4}\s+\d+
```

---

## Rule 10.4: Court and Jurisdiction

### Identification Rules

**Include court abbreviation when:**
1. Reporter doesn't clearly indicate court
2. Multiple courts could publish in same reporter
3. State intermediate appellate court

**Omit court abbreviation when:**
1. U.S. Supreme Court (U.S. reporter clearly indicates)
2. State reporter that clearly indicates highest court
3. Circuit obvious from F.2d/F.3d designation with circuit in parenthetical

### Standard Court Abbreviations

**Federal Courts:**
- Supreme Court: (omit court, just year)
- Circuit Courts: `(1st Cir. 2020)`, `(2d Cir. 2020)`, `(9th Cir. 2020)`
- District Courts: `(S.D.N.Y. 2020)`, `(N.D. Cal. 2020)`, `(D. Mass. 2020)`

**State Courts:**
- Highest Court: `(N.Y. 1990)` [Court of Appeals]
- Intermediate: `(Cal. Ct. App. 1990)`, `(Tex. App. 1990)`
- Trial: Include full designation

### Detection Patterns

**Find circuit court citations:**
```regex
\((?:1st|2d|3d|4th|5th|6th|7th|8th|9th|10th|11th|D\.C\.|Fed\.) Cir\.\s+\d{4}\)
```

**Find district court citations:**
```regex
\((?:[ENSW]\.D\.|D\.)\s+[A-Z][a-z\.]+\s+\d{4}\)
```

**Find state court citations:**
```regex
\((?:[A-Z][a-z\.]+)\s+(?:Ct\. App\.|App\.)?\s*\d{4}\)
```

---

## Rule 10.5: Date or Year

### Year Requirements

**Standard Rule**: Include year of decision in parentheses
- `Smith v. Jones, 100 F.3d 200 (9th Cir. 2000).`

**Full Date**: Include when essential (multiple decisions same year)
- `Smith v. Jones, No. 20-1234, 2020 WL 123456 (S.D.N.Y. Mar. 15, 2020).`

**U.S. Supreme Court**: Year alone always sufficient
- `Roe v. Wade, 410 U.S. 113 (1973).`

### Detection Patterns

**Find year-only citations:**
```regex
\(\d{4}\)\.?$
```

**Find full date citations:**
```regex
\((?:[A-Z][a-z\.]+\s+)?(?:Jan\.|Feb\.|Mar\.|Apr\.|May|June|July|Aug\.|Sept\.|Oct\.|Nov\.|Dec\.)\s+\d{1,2},\s+\d{4}\)
```

**Validate year format (four digits):**
```regex
\b(19|20)\d{2}\b
```

---

## Rule 10.6: Parenthetical Information

### Rule 10.6.1: Weight of Authority

Include parenthetical for:
- **Per curiam**: `(per curiam)`
- **En banc**: `(en banc)`
- **Plurality**: `(plurality opinion)`
- **Dissent**: `(Scalia, J., dissenting)`
- **Concurrence**: `(Kennedy, J., concurring)`

**Examples:**
```
Bush v. Gore, 531 U.S. 98 (2000) (per curiam).
United States v. Microsoft Corp., 253 F.3d 34 (D.C. Cir. 2001) (en banc).
Regents of Univ. of Cal. v. Bakke, 438 U.S. 265 (1978) (plurality opinion).
```

### Detection Patterns

**Find weight of authority parentheticals:**
```regex
\((?:per curiam|en banc|plurality opinion)\)
```

**Find opinion type with judge name:**
```regex
\([A-Z][a-z]+(?:,\s+[A-Z]\.)?(?:,\s+J\.)?,\s+(?:dissenting|concurring|concurring in part and dissenting in part)\)
```

### Rule 10.6.3: Quoting/Citing Parentheticals

When citation contains another citation:
```
Smith v. Jones, 100 F.3d 200, 205 (9th Cir. 2000) (quoting Brown v. Board of Educ., 347 U.S. 483, 495 (1954)).
```

**Note**: Interior citation not italicized

**Detection Pattern:**
```regex
\((?:quoting|citing)\s+[A-Z][^,]+,\s+\d+\s+[A-Z][^\s]+\s+\d+(?:,\s+\d+)?\s+\([^)]+\)\)
```

### Rule 10.6.4: Order of Parentheticals

**Correct Order:**
1. Weight of authority
2. Explanatory parenthetical
3. Quoting/citing parenthetical

**Example:**
```
Smith v. Jones, 100 F.3d 200 (9th Cir. 2000) (per curiam) (holding that due process requires notice) (quoting Mullane v. Central Hanover Bank & Trust Co., 339 U.S. 306, 314 (1950)).
```

---

## 20 Core Examples with Detection Patterns

### Example 1: Basic U.S. Supreme Court Citation
**Citation:**
```
Brown v. Board of Education, 347 U.S. 483 (1954).
```
**Pattern Check:**
- ✓ Case name format
- ✓ Reporter: U.S.
- ✓ No court needed (Supreme Court obvious)
- ✓ Year only

### Example 2: U.S. Supreme Court with Pinpoint
**Citation:**
```
Miranda v. Arizona, 384 U.S. 436, 444 (1966).
```
**Pattern Check:**
- ✓ Pinpoint: 444
- ✓ Comma before pinpoint

### Example 3: Circuit Court Citation
**Citation:**
```
United States v. Lopez, 2 F.3d 1342 (5th Cir. 1993).
```
**Pattern Check:**
- ✓ Circuit designation: (5th Cir. 1993)
- ✓ Reporter: F.3d

### Example 4: District Court Citation
**Citation:**
```
Smith v. Jones, 100 F. Supp. 2d 200 (S.D.N.Y. 2000).
```
**Pattern Check:**
- ✓ District: S.D.N.Y.
- ✓ Reporter: F. Supp. 2d

### Example 5: State Supreme Court (Regional Reporter)
**Citation:**
```
People v. Anderson, 493 P.2d 880 (Cal. 1972).
```
**Pattern Check:**
- ✓ State abbreviation: Cal.
- ✓ Regional reporter: P.2d

### Example 6: State Appellate Court
**Citation:**
```
Smith v. Superior Court, 220 Cal. App. 3d 100 (Ct. App. 1990).
```
**Pattern Check:**
- ✓ Intermediate court: Ct. App.
- ✓ Year: 1990

### Example 7: Per Curiam Opinion
**Citation:**
```
Bush v. Gore, 531 U.S. 98 (2000) (per curiam).
```
**Pattern Check:**
- ✓ Weight parenthetical: (per curiam)

### Example 8: En Banc Decision
**Citation:**
```
United States v. Microsoft Corp., 253 F.3d 34 (D.C. Cir. 2001) (en banc).
```
**Pattern Check:**
- ✓ Weight parenthetical: (en banc)
- ✓ D.C. Circuit designation

### Example 9: Plurality Opinion
**Citation:**
```
Regents of University of California v. Bakke, 438 U.S. 265 (1978) (plurality opinion).
```
**Pattern Check:**
- ✓ Weight parenthetical: (plurality opinion)

### Example 10: Dissenting Opinion
**Citation:**
```
Obergefell v. Hodges, 576 U.S. 644, 686 (2015) (Scalia, J., dissenting).
```
**Pattern Check:**
- ✓ Judge name: Scalia, J.
- ✓ Opinion type: dissenting
- ✓ Pinpoint to dissent start

### Example 11: Concurring Opinion
**Citation:**
```
Loving v. Virginia, 388 U.S. 1, 13 (1967) (Stewart, J., concurring).
```
**Pattern Check:**
- ✓ Judge name: Stewart, J.
- ✓ Opinion type: concurring

### Example 12: Case Name with Corporate Party
**Citation:**
```
Facebook, Inc. v. Duguid, 141 S. Ct. 1163 (2021).
```
**Pattern Check:**
- ✓ Corporate designation: Inc.
- ✓ Reporter: S. Ct.

### Example 13: Case Name with Acronym
**Citation:**
```
NLRB v. Jones & Laughlin Steel Corp., 301 U.S. 1 (1937).
```
**Pattern Check:**
- ✓ Acronym: NLRB
- ✓ Ampersand: &
- ✓ Abbreviation: Corp.

### Example 14: In Re Proceeding
**Citation:**
```
In re Gault, 387 U.S. 1 (1967).
```
**Pattern Check:**
- ✓ Procedural designation: In re
- ✓ Single party name

### Example 15: Ex Parte Proceeding
**Citation:**
```
Ex parte Quirin, 317 U.S. 1 (1942).
```
**Pattern Check:**
- ✓ Procedural designation: Ex parte
- ✓ Single party name

### Example 16: Multiple Pinpoints
**Citation:**
```
Chevron U.S.A. Inc. v. Natural Resources Defense Council, Inc., 467 U.S. 837, 842-43 (1984).
```
**Pattern Check:**
- ✓ Pinpoint range: 842-43
- ✓ En dash in range

### Example 17: State with Public Domain Citation
**Citation:**
```
State v. Smith, 1999 ND 45, ¶ 12, 591 N.W.2d 505, 508.
```
**Pattern Check:**
- ✓ Public domain: 1999 ND 45
- ✓ Paragraph pinpoint: ¶ 12
- ✓ Parallel citation

### Example 18: Quoting Parenthetical
**Citation:**
```
Marbury v. Madison, 5 U.S. (1 Cranch) 137, 177 (1803) (quoting 1 William Blackstone, Commentaries *163).
```
**Pattern Check:**
- ✓ Early reporter format: (1 Cranch)
- ✓ Quoting parenthetical

### Example 19: Federal District Court, Full Date
**Citation:**
```
Doe v. University of Kentucky, No. 20-1234, 2020 WL 123456, at *3 (E.D. Ky. Mar. 15, 2020).
```
**Pattern Check:**
- ✓ Docket number: No. 20-1234
- ✓ Database citation: WL
- ✓ Full date: Mar. 15, 2020
- ✓ Star pinpoint: *3

### Example 20: State Intermediate Court with Explanatory Parenthetical
**Citation:**
```
People v. Superior Court, 220 Cal. App. 3d 100, 105 (Ct. App. 1990) (holding that warrantless searches violate Fourth Amendment).
```
**Pattern Check:**
- ✓ Court: Ct. App.
- ✓ Explanatory parenthetical starts with participle

---

## Quick Reference: Common Detection Issues

### Issue 1: Missing Pinpoint Citations
**Problem**: Citation lacks specific page reference
**Detection**: Check if citation supports specific proposition but has no pinpoint
**Rule**: Always include pinpoint except for textual sentences naming case

### Issue 2: Incorrect Reporter Series
**Problem**: Using "2nd" instead of "2d"
**Detection**: `\b(?:1st|2nd|3rd)\b` (should be 2d, 3d)
**Fix**: Use 2d, 3d, 4th (never 2nd, 3rd)

### Issue 3: Unnecessary Court Designation
**Problem**: Including court when reporter makes it obvious
**Example Wrong**: `Brown v. Board of Education, 347 U.S. 483 (U.S. 1954).`
**Example Right**: `Brown v. Board of Education, 347 U.S. 483 (1954).`

### Issue 4: First Word Abbreviation
**Problem**: Abbreviating first word of party name
**Example Wrong**: `Ass'n of Data Processing v. Camp`
**Example Right**: `Association of Data Processing v. Camp`

### Issue 5: Including "The" in Party Name
**Problem**: Starting party name with "The"
**Example Wrong**: `The New York Times Co. v. Sullivan`
**Example Right**: `New York Times Co. v. Sullivan`

### Issue 6: Multiple Parties Listed
**Problem**: Including all parties instead of first only
**Example Wrong**: `Smith, Jones, and Brown v. White and Green`
**Example Right**: `Smith v. White`

### Issue 7: Unabbreviated Company Designations
**Problem**: Not abbreviating Co., Inc., Corp., Ltd.
**Example Wrong**: `Acme Company v. Smith`
**Example Right**: `Acme Co. v. Smith`

### Issue 8: Missing En Dash in Page Ranges
**Problem**: Using hyphen instead of en dash
**Example Wrong**: `100 F.3d 200, 205-06`
**Example Right**: `100 F.3d 200, 205–06`

### Issue 9: Italicized Comma After Case Name
**Problem**: Italicizing comma after case name
**Example Wrong**: `*Brown v. Board of Education,* 347 U.S. 483`
**Example Right**: `*Brown v. Board of Education*, 347 U.S. 483`

### Issue 10: Missing Space in Reporter
**Problem**: No space between abbreviation elements
**Example Wrong**: `F.Supp.2d`
**Example Right**: `F. Supp. 2d`

---

## Validation Checklist

Use this checklist to validate case citations:

- [ ] Case name properly formatted (last names only, no "The", proper abbreviations)
- [ ] First word of party name NOT abbreviated (unless acronym)
- [ ] Volume number present
- [ ] Reporter properly abbreviated (check Table T1)
- [ ] Series designation correct (2d, 3d, 4th - not 2nd, 3rd)
- [ ] First page number present
- [ ] Pinpoint page included (if citing specific content)
- [ ] Court designation included if not obvious from reporter
- [ ] Court designation omitted if obvious from reporter
- [ ] Year in parentheses at end
- [ ] Period at end of citation
- [ ] Proper spacing throughout
- [ ] Weight of authority parenthetical if needed (per curiam, en banc, etc.)
- [ ] Parentheticals in correct order

---

## Master Regex Pattern for Full Case Citation

**Comprehensive Pattern:**
```regex
^([A-Z][A-Za-z\.'&\s]+)\s+v\.\s+([A-Z][A-Za-z\.'&\s]+),\s+(\d+)\s+([A-Z][A-Za-z\.\s]+(?:2d|3d|4th)?)\s+(\d+)(?:,\s+(\d+(?:[-–]\d+)?))?\s+\((?:([A-Z][A-Za-z\.\s]+)\s+)?(\d{4})\)(?:\s+\(([^)]+)\))?\.?$
```

**Capture Groups:**
1. First party name
2. Second party name
3. Volume
4. Reporter
5. First page
6. Pinpoint (optional)
7. Court (optional)
8. Year
9. Parenthetical (optional)

---

*Document Size: ~25KB*
*Last Updated: 2025-11-23*
