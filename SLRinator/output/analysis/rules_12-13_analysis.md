# Bluebook Rules 11-13: Constitutions and Statutes - Comprehensive Analysis

**Generated:** 2025-11-23
**Source:** `/home/user/slr/SLRinator/config/rules/Bluebook.json`

---

## Table of Contents

1. [Rule 11: Constitutional Citations](#rule-11-constitutional-citations)
2. [Rule 12: Statutes](#rule-12-statutes)
3. [Section Symbols (§)](#section-symbols)
4. [Year Requirements](#year-requirements)
5. [Regex Patterns for Validation](#regex-patterns-for-validation)
6. [GPT Validation Prompts](#gpt-validation-prompts)
7. [Common Errors and Corrections](#common-errors-and-corrections)
8. [Comprehensive Examples](#comprehensive-examples)
9. [Cross-References to Table 1](#cross-references-to-table-1)

---

## Rule 11: Constitutional Citations

### Complete Format Specifications

**Basic Format:**
```
[Constitution Name] [subdivision]
```

**U.S. Constitution:**
- Full name: `U.S. Constitution`
- Citation abbreviation: `U.S. Const.`
- Subdivisions: `art.` (article), `§` (section), `amend.` (amendment), `cl.` (clause)

**State Constitutions:**
- Format: `[State Abbrev.] Const.`
- Examples: `N.Y. Const.`, `Cal. Const.`, `Tex. Const.`

### Key Rules

1. **No dates required** - Constitutional citations do not include dates
2. **Subdivision format** - Use standard abbreviations for constitutional subdivisions
3. **Context-dependent abbreviation** - May drop jurisdiction on subsequent references when clear from context
4. **Use "Id."** for subsequent citations when appropriate

### Constitutional Citation Structure

```
U.S. Const. art. [Roman numeral], § [number]
U.S. Const. amend. [Roman numeral]
U.S. Const. amend. [Roman numeral], § [number]
[State] Const. art. [number/numeral], § [number]
```

### Examples

**Correct:**
- `U.S. Const. art. I, § 8`
- `U.S. Const. amend. XIV`
- `U.S. Const. amend. XIV, § 1`
- `N.Y. Const. art. I, § 6`
- `Cal. Const. art. XIII A, § 1`

**Incorrect:**
- `U.S. Constitution Article 1, Section 8` (not abbreviated)
- `U.S. Const. Art. I, Sec. 8` (incorrect abbreviations)
- `U.S. Const. art. 1, § 8` (Arabic instead of Roman numerals for articles)
- `U.S. Const. amend. 14` (Arabic instead of Roman numerals for amendments)

---

## Rule 12: Statutes

### 12.1 Basic Citation Forms

#### Federal Statutes

**United States Code (Official):**
```
[Title Number] U.S.C. § [Section] ([Year])
```

**Example:**
```
42 U.S.C. § 1983 (2018)
```

**With Popular Name:**
```
[Popular Name], [Title] U.S.C. § [Section] ([Year])
```

**Example:**
```
Civil Rights Act of 1964, 42 U.S.C. § 2000e (2018)
```

#### State Statutes

**Format:**
```
[State Abbrev.] [Code Abbrev.] § [Section] ([Year])
```

**Examples:**
```
N.Y. Penal Law § 120.00 (McKinney 2020)
Cal. Civ. Code § 1714 (West 2020)
Tex. Fam. Code Ann. § 153.001 (West 2021)
```

#### Session Laws

**Federal Session Laws:**
```
[Popular Name], Pub. L. No. [Congress]-[Number], [Volume] Stat. [Page] ([Year])
```

**Example:**
```
Civil Rights Act of 1964, Pub. L. No. 88-352, 78 Stat. 241 (1964)
```

**State Session Laws:**
```
[State Session Law Citation]
```

**Examples:**
```
Act of May 15, 2020, ch. 123, 2020 N.Y. Laws 456
Act of June 1, 2019, ch. 45, 2019 Cal. Stat. 234
```

### 12.2 Choosing the Proper Citation Form

**Order of Preference:**

1. **Official Code** (preferred when available)
   - U.S.C. for federal statutes
   - State official codes (varies by state)

2. **Unofficial Annotated Codes** (when more current or required)
   - U.S.C.A. (West)
   - U.S.C.S. (LexisNexis)
   - State annotated codes

3. **Session Laws** (when not yet codified)
   - Statutes at Large (Stat.)
   - State session laws

**Multiple Sections:**
```
42 U.S.C. §§ 9601-9675 (2018)
```

**Non-consecutive Sections:**
```
42 U.S.C. §§ 1983, 1985, 1988 (2018)
```

### 12.3 Current Official and Unofficial Codes

#### Federal Codes

**Official:**
- `U.S.C.` - United States Code (published every 6 years with supplements)

**Unofficial:**
- `U.S.C.A.` - United States Code Annotated (West)
- `U.S.C.S.` - United States Code Service (LexisNexis)

**Year Citation Rules:**
- Bluebook 21st edition: Federal code citations may omit year if citing current code
- Include year of code edition or supplement year
- Supplement citation: `(Supp. 2020)` or `(main vol. 2018 & Supp. 2020)`

#### State Codes

**Always include:**
- State abbreviation
- Code abbreviation
- Publisher (for unofficial codes): `(West 2020)` or `(LexisNexis 2020)`
- Year of code volume or supplement

**Examples:**
```
Ala. Code § 13A-6-20 (2019)
Alaska Stat. § 11.41.100 (2020)
Ariz. Rev. Stat. Ann. § 13-1203 (2021)
Ark. Code Ann. § 5-13-201 (West 2020)
```

### 12.4 Session Laws

**When to Use:**
- Statute not yet codified
- Referring to law as originally passed
- Historical reference to enactment

**Federal Format:**
```
[Official Name of Act], Pub. L. No. [Congress]-[Number], [Volume] Stat. [Page] ([Year])
```

**Examples:**
```
Affordable Care Act, Pub. L. No. 111-148, 124 Stat. 119 (2010)
Tax Cuts and Jobs Act, Pub. L. No. 115-97, 131 Stat. 2054 (2017)
```

**State Session Laws:**
- Use state-specific citation format (see Table 1)
- Common formats: `[Year] [State] Laws [Chapter]` or `[State] Acts [Year], No. [Number]`

**Examples:**
```
2020 Ala. Acts 123
Alaska Sess. Laws 2020, ch. 45
2019 Ariz. Sess. Laws ch. 234
2021 Ark. Acts No. 567
```

### 12.5 Electronic Databases and Online Sources

**Format:**
```
[Code Citation] ([Database] through [Currency Information])
```

**Examples:**
```
42 U.S.C. § 1983 (LEXIS through Pub. L. No. 116-140)
42 U.S.C. § 2000e (Westlaw through Pub. L. No. 117-25)
Cal. Civ. Code § 1714 (Westlaw current through 2021 legislation)
```

**Best Practices:**
- Use authenticated PDFs or official websites when possible
- Provide URL if required or aids retrieval
- Follow Bluebook Rule 18.2.2 for online sources

### 12.7 Invalidation, Repeal, Amendment, and Prior History

#### 12.7.1 Invalidation

**Format:**
```
[Statute Citation] (held unconstitutional by [Case Citation])
```

**Example:**
```
18 U.S.C. § 3501 (2000) (held unconstitutional by Dickerson v. United States, 530 U.S. 428 (2000))
```

#### 12.7.2 Repeal

**Format:**
```
[Statute Citation] (repealed [Year])
```

**Example:**
```
42 U.S.C. § 6000 (1988) (repealed 1992)
```

#### 12.7.3 Amendment

**Current Code:**
- Generally, don't indicate amendments when citing current code
- Code text is presumed current

**When Amendment is Relevant:**
```
42 U.S.C. § 1983 (2018) (amended 2020)
```

**Forthcoming Amendment:**
```
42 U.S.C. § 2000e (to be amended by Pub. L. No. 117-XXX)
```

### 12.8 Explanatory Parenthetical Phrases

**Purpose:**
- Clarify how statute relates to proposition
- Provide context for reader

**Format:**
```
[Statute Citation] ([explanatory phrase])
```

**Examples:**
```
42 U.S.C. § 7401 (2018) (establishing national ambient air quality standards)
15 U.S.C. § 78j(b) (2018) (prohibiting securities fraud)
18 U.S.C. § 1961 (2018) (defining "racketeering activity")
```

### 12.9 Special Citation Forms

#### 12.9.1 Internal Revenue Code

**Practitioner Format (Preferred):**
```
I.R.C. § [Section]
```

**Academic Format:**
```
26 U.S.C. § [Section] ([Year])
```

**Examples:**
```
I.R.C. § 61
I.R.C. § 162(a)
26 U.S.C. § 61 (2018)
```

#### 12.9.2 Ordinances

**Format:**
```
[City], [State Abbrev.], [Municipal Code/Ordinance] § [Section] ([Year])
```

**Examples:**
```
Chicago, Ill., Municipal Code § 8-4-015 (2020)
Los Angeles, Cal., Municipal Code § 12.24 (2021)
```

**Uncodified Ordinances:**
```
[City], [State], Ordinance No. [Number] (enacted [Date])
```

#### 12.9.3 Rules of Evidence and Procedure

**Federal Rules:**
```
Fed. R. [Civ./Crim./Evid./App.] P. [Rule Number]
```

**Examples:**
```
Fed. R. Civ. P. 56
Fed. R. Crim. P. 11
Fed. R. Evid. 401
Fed. R. App. P. 32
```

**State Rules:**
```
[State Abbrev.] R. [Civ./Crim./Evid./App.] P. [Number]
```

**Local Rules:**
```
[Court Abbrev.] R. [Number]
```

**Example:**
```
S.D.N.Y. R. 4.1
```

#### 12.9.4 Model Codes, Restatements, and Uniform Acts

**Model Penal Code:**
```
Model Penal Code § [Section] (Am. Law Inst. [Year])
```

**Example:**
```
Model Penal Code § 210.3 (Am. Law Inst. 1962)
```

**Restatements:**
```
Restatement ([Second/Third]) of [Subject] § [Section] (Am. Law Inst. [Year])
```

**Examples:**
```
Restatement (Second) of Contracts § 90 (Am. Law Inst. 1981)
Restatement (Third) of Torts § 1 (Am. Law Inst. 2010)
```

**Uniform Acts:**
```
Uniform [Act Name] § [Section] (Am. Law Inst. & Unif. Law Comm'n [Year])
```

**Example:**
```
Uniform Commercial Code § 2-201 (Am. Law Inst. & Unif. Law Comm'n 2017)
```

#### 12.9.5 ABA Model Rules

**Format:**
```
Model Rules of Pro. Conduct r. [Rule] (Am. Bar Ass'n [Year])
```

**Example:**
```
Model Rules of Pro. Conduct r. 1.7 (Am. Bar Ass'n 2020)
```

**Ethics Opinions:**
```
ABA Comm. on Ethics & Pro. Resp., Formal Op. [Number] ([Year])
```

**Example:**
```
ABA Comm. on Ethics & Pro. Resp., Formal Op. 466 (2014)
```

### 12.10 Short Forms for Statutes

**Subsequent Citations:**

1. **"Id." (immediately preceding citation, same section):**
   ```
   Id.
   Id. § 1985.
   ```

2. **Short form with section number:**
   ```
   § 1983
   § 2000e(a)
   ```

3. **Short name:**
   ```
   ACA § 1501
   ERISA § 502(a)
   ```

**Rules:**
- Use "Id." only if immediately preceding citation is same statute
- Do NOT use "supra" for statutes
- Context must make clear which code is referenced
- Include section number even in short form

---

## Section Symbols (§)

### Basic Usage

**Single Section:**
```
§ 1983
```

**Multiple Consecutive Sections:**
```
§§ 1983-1988
```

**Multiple Non-consecutive Sections:**
```
§§ 1983, 1985, 1988
```

### Rules

1. **Always use section symbol** (§) in citations, not the word "section"
2. **Space after symbol:** `§ 1983` (not `§1983`)
3. **Double symbol for plural:** `§§` (not `§§§` or multiple single symbols)
4. **No period after symbol**
5. **In text:** Write out "section" when starting a sentence

### Formatting Rules

- **Typeface:** Use § symbol from character set (U+00A7)
- **Spacing:** Space between § and number
- **Subsections:** Use parentheses: `§ 1983(a)(3)`
- **Ranges:** Use en-dash: `§§ 2000e-2000e-17`

### Examples

**Correct:**
```
42 U.S.C. § 1983
42 U.S.C. §§ 1981-1988
18 U.S.C. §§ 241, 242
15 U.S.C. § 78j(b)
```

**Incorrect:**
```
42 U.S.C. Section 1983 (should use §)
42 U.S.C. §1983 (missing space)
42 U.S.C. § 1981 - 1988 (should use §§)
42 U.S.C. §§ 1983 (single section, should use §)
```

---

## Year Requirements

### Federal Statutes (U.S.C.)

**Bluebook 21st Edition Rule:**
- May omit year when citing current code
- Include year when citing:
  - Historical versions
  - Supplements
  - Repealed provisions
  - When year is relevant to analysis

**Year Format:**
```
([Year])
([main vol. Year & Supp. Year])
(Supp. Year)
```

**Examples:**
```
42 U.S.C. § 1983 (current - year optional)
42 U.S.C. § 1983 (2018) (specific edition)
42 U.S.C. § 1983 (2012 & Supp. V 2017) (main volume + supplement)
```

### State Statutes

**Always include year** for state codes:
- Year of code volume
- Year of supplement
- Publisher name (for unofficial codes)

**Format:**
```
([Publisher] [Year])
([Year])
```

**Examples:**
```
Cal. Civ. Code § 1714 (West 2020)
N.Y. Penal Law § 120.00 (McKinney 2021)
Tex. Fam. Code Ann. § 153.001 (West Supp. 2021)
```

### Session Laws

**Always include year** of enactment:

**Federal:**
```
Pub. L. No. 111-148, 124 Stat. 119 (2010)
```

**State:**
```
2020 Cal. Stat. ch. 123
Act of May 15, 2020, ch. 45, 2020 N.Y. Laws 234
```

### Constitutional Citations

**Never include year** for constitutional citations:
```
U.S. Const. amend. XIV (correct)
U.S. Const. amend. XIV (1868) (incorrect)
```

---

## Regex Patterns for Validation

### U.S.C. Citations

```regex
# Basic U.S.C. citation
^\d+\s+U\.S\.C\.\s+§§?\s+\d+(-\d+)?(,\s+\d+(-\d+)?)*(\s+\([^)]+\))?$

# U.S.C. with subsections
^\d+\s+U\.S\.C\.\s+§\s+\d+(\([a-z]\))?(\(\d+\))?(\([A-Z]\))?(\s+\([^)]+\))?$

# U.S.C. with year
^\d+\s+U\.S\.C\.\s+§§?\s+\d+(-\d+)?(\s+\((\d{4}|Supp\.\s+\d{4})\))?$

# U.S.C. annotated
^\d+\s+U\.S\.C\.[AS]\.\s+§§?\s+\d+(-\d+)?(\s+\([^)]+\s+\d{4}\))?$
```

### State Statute Citations

```regex
# Generic state code
^[A-Z][a-z]{1,4}\.\s+[A-Za-z.]+\s+§§?\s+\d+(-\d+)?(\.\d+)?(\s+\([^)]+\s+\d{4}\))?$

# California codes
^Cal\.\s+(Civ\.|Penal|Bus\.\s+&\s+Prof\.|Health\s+&\s+Safety)\s+Code\s+§§?\s+\d+(\.\d+)?(\s+\(West\s+\d{4}\))?$

# New York codes
^N\.Y\.\s+[A-Za-z.]+\s+Law\s+§§?\s+\d+(\.\d+)?(\s+\(McKinney\s+\d{4}\))?$

# Texas codes
^Tex\.\s+[A-Za-z.]+\s+Code\s+Ann\.\s+§§?\s+\d+(\.\d+)?(\s+\(West\s+\d{4}\))?$
```

### Session Law Citations

```regex
# Federal session law (Pub. L.)
^Pub\.\s+L\.\s+No\.\s+\d{2,3}-\d+,\s+\d+\s+Stat\.\s+\d+(\s+\(\d{4}\))?$

# Federal session law with popular name
^[A-Z][A-Za-z\s]+Act(\s+of\s+\d{4})?,\s+Pub\.\s+L\.\s+No\.\s+\d{2,3}-\d+,\s+\d+\s+Stat\.\s+\d+\s+\(\d{4}\)$

# State session law
^\d{4}\s+[A-Z][a-z]{1,4}\.\s+(Laws|Acts|Sess\.\s+Laws)\s+(ch\.\s+)?\d+$
```

### Constitutional Citations

```regex
# U.S. Constitution article
^U\.S\.\s+Const\.\s+art\.\s+[IVX]+,\s+§\s+\d+$

# U.S. Constitution amendment
^U\.S\.\s+Const\.\s+amend\.\s+[IVX]+$

# U.S. Constitution amendment with section
^U\.S\.\s+Const\.\s+amend\.\s+[IVX]+,\s+§\s+\d+$

# State constitution
^[A-Z][a-z]{1,4}\.\s+Const\.\s+art\.\s+[IVX\d]+,\s+§\s+\d+$
```

### Section Symbol Validation

```regex
# Single section
^§\s+\d+(\([a-z]\))?(\(\d+\))?$

# Multiple sections (range)
^§§\s+\d+-\d+$

# Multiple sections (non-consecutive)
^§§\s+\d+(,\s+\d+)+$

# Section with subsections
^§\s+\d+(\([a-z]\))(\(\d+\))?(\([A-Z]\))?$
```

### Special Forms

```regex
# I.R.C.
^I\.R\.C\.\s+§\s+\d+(\([a-z]\))?(\(\d+\))?$

# Federal Rules
^Fed\.\s+R\.\s+(Civ\.|Crim\.|Evid\.|App\.)\s+P\.\s+\d+$

# Model Penal Code
^Model\s+Penal\s+Code\s+§\s+\d+\.\d+\s+\(Am\.\s+Law\s+Inst\.\s+\d{4}\)$

# Restatement
^Restatement\s+\((Second|Third)\)\s+of\s+[A-Za-z]+\s+§\s+\d+\s+\(Am\.\s+Law\s+Inst\.\s+\d{4}\)$
```

---

## GPT Validation Prompts

### Prompt 1: General Statute Citation Validation

```
You are a Bluebook citation expert. Validate the following statute citation and provide corrections if needed.

Citation: {citation}

Check for:
1. Correct code abbreviation (U.S.C., state code, etc.)
2. Proper use of section symbols (§ vs. §§)
3. Correct spacing around section symbols
4. Proper year format and placement
5. Correct publisher notation for unofficial codes
6. Proper subdivision notation (subsections in parentheses)

Provide:
- Is Valid: [Yes/No]
- Errors Found: [List specific errors]
- Corrected Citation: [Provide corrected version]
- Explanation: [Brief explanation of corrections]
```

### Prompt 2: Constitutional Citation Validation

```
You are a Bluebook citation expert. Validate the following constitutional citation.

Citation: {citation}

Check for:
1. Correct abbreviation (U.S. Const. or state abbreviation)
2. Proper use of article/amendment abbreviations
3. Roman numerals for articles and amendments
4. No date included (dates not used for constitutions)
5. Proper section notation if applicable
6. Correct comma placement

Provide:
- Is Valid: [Yes/No]
- Errors Found: [List specific errors]
- Corrected Citation: [Provide corrected version]
- Rule Citation: [Relevant Bluebook rule]
```

### Prompt 3: Session Law Citation Validation

```
You are a Bluebook citation expert. Validate the following session law citation.

Citation: {citation}

Check for:
1. Correct public law notation (Pub. L. No. for federal)
2. Proper Statutes at Large citation (Stat.)
3. Correct state session law format
4. Year in parentheses at end
5. Popular name formatting (if included)
6. Proper spacing and punctuation

Provide:
- Is Valid: [Yes/No]
- Errors Found: [List specific errors]
- Corrected Citation: [Provide corrected version]
- Alternative Forms: [Suggest if code citation would be better]
```

### Prompt 4: Section Symbol Usage Validation

```
You are a Bluebook citation expert. Validate the use of section symbols in this citation.

Citation: {citation}

Check for:
1. Single § for single section
2. Double §§ for multiple sections
3. Proper spacing after §/§§
4. Correct range notation (§§ 1-10 not § 1-10)
5. Proper subsection notation in parentheses
6. Comma usage for non-consecutive sections

Provide:
- Is Valid: [Yes/No]
- Errors Found: [List specific errors]
- Corrected Citation: [Provide corrected version]
- Explanation: [Why this correction follows Bluebook rules]
```

### Prompt 5: Year Requirement Validation

```
You are a Bluebook citation expert. Validate year requirements for this statutory citation.

Citation: {citation}
Citation Type: {federal/state/session law}

Check for:
1. Year included when required
2. Year omitted when optional (current U.S.C.)
3. Proper year format in parentheses
4. Supplement notation if applicable
5. Publisher and year for unofficial codes
6. Year placement at end of citation

Provide:
- Is Valid: [Yes/No]
- Year Required: [Yes/No/Optional]
- Errors Found: [List specific errors]
- Corrected Citation: [Provide corrected version]
- Justification: [Cite specific Bluebook rule]
```

### Prompt 6: Comprehensive Statute Citation Analysis

```
You are a Bluebook citation expert. Perform a comprehensive analysis of this statute citation.

Citation: {citation}

Analyze:
1. Identify citation type (federal code, state code, session law, etc.)
2. Verify all components are present and correctly formatted
3. Check abbreviations against Bluebook tables
4. Validate section symbol usage
5. Verify year requirements
6. Check for common errors
7. Suggest improvements or alternatives

Provide:
- Citation Type: [Identify type]
- Validity Score: [0-100]
- Component Analysis: [Break down each part]
- Errors Found: [Detailed list]
- Corrected Citation: [Full corrected version]
- Best Practices: [Recommendations]
- Cross-References: [Relevant Bluebook rules and tables]
```

---

## Common Errors and Corrections

### Error Category 1: Section Symbol Mistakes

#### Error 1.1: Missing Space After Section Symbol
**Incorrect:** `42 U.S.C. §1983`
**Correct:** `42 U.S.C. § 1983`
**Explanation:** Always include space between § and the section number.

#### Error 1.2: Single § for Multiple Sections
**Incorrect:** `42 U.S.C. § 1981-1988`
**Correct:** `42 U.S.C. §§ 1981-1988`
**Explanation:** Use double section symbol (§§) when citing multiple sections.

#### Error 1.3: Using "Section" Instead of Symbol
**Incorrect:** `42 U.S.C. Section 1983`
**Correct:** `42 U.S.C. § 1983`
**Explanation:** Always use § symbol in citations, not the word "section."

#### Error 1.4: Wrong Symbol
**Incorrect:** `42 U.S.C. ¶ 1983`
**Correct:** `42 U.S.C. § 1983`
**Explanation:** Use § for sections, not ¶ (paragraph symbol).

#### Error 1.5: Period After Section Symbol
**Incorrect:** `42 U.S.C. §. 1983`
**Correct:** `42 U.S.C. § 1983`
**Explanation:** No period after section symbol.

### Error Category 2: Year Placement and Format

#### Error 2.1: Missing Year for State Codes
**Incorrect:** `Cal. Civ. Code § 1714`
**Correct:** `Cal. Civ. Code § 1714 (West 2020)`
**Explanation:** State codes always require year and publisher.

#### Error 2.2: Year Outside Parentheses
**Incorrect:** `42 U.S.C. § 1983 2018`
**Correct:** `42 U.S.C. § 1983 (2018)`
**Explanation:** Year must be in parentheses.

#### Error 2.3: Wrong Year Format for Supplements
**Incorrect:** `42 U.S.C. § 1983 (2018) (Supplement 2020)`
**Correct:** `42 U.S.C. § 1983 (2018 & Supp. 2020)`
**Explanation:** Use ampersand and abbreviate "Supp."

#### Error 2.4: Including Year for Current U.S.C. When Not Needed
**Incorrect:** Must include year even when current
**Correct:** Year optional for current U.S.C. under Bluebook 21st ed.
**Explanation:** Bluebook 21st edition allows omission of year for current federal code.

#### Error 2.5: Adding Date to Constitutional Citations
**Incorrect:** `U.S. Const. amend. XIV (1868)`
**Correct:** `U.S. Const. amend. XIV`
**Explanation:** Never include dates in constitutional citations.

### Error Category 3: Abbreviation Mistakes

#### Error 3.1: Incorrect Code Abbreviation
**Incorrect:** `42 USC § 1983`
**Correct:** `42 U.S.C. § 1983`
**Explanation:** Include periods in "U.S.C."

#### Error 3.2: Wrong State Code Abbreviation
**Incorrect:** `California Civil Code § 1714`
**Correct:** `Cal. Civ. Code § 1714 (West 2020)`
**Explanation:** Use proper state and code abbreviations from Table 1.

#### Error 3.3: Incorrect Article Abbreviation
**Incorrect:** `U.S. Const. article I, section 8`
**Correct:** `U.S. Const. art. I, § 8`
**Explanation:** Abbreviate "art." and use § for section.

#### Error 3.4: Wrong Amendment Abbreviation
**Incorrect:** `U.S. Const. Amendment XIV`
**Correct:** `U.S. Const. amend. XIV`
**Explanation:** Abbreviate "amend." and use Roman numerals.

#### Error 3.5: Statute vs. Statutes at Large
**Incorrect:** `Pub. L. No. 111-148, 124 Statute 119 (2010)`
**Correct:** `Pub. L. No. 111-148, 124 Stat. 119 (2010)`
**Explanation:** Abbreviate "Statutes at Large" as "Stat."

### Error Category 4: Subsection Notation

#### Error 4.1: Wrong Subsection Format
**Incorrect:** `42 U.S.C. § 1983.a.3`
**Correct:** `42 U.S.C. § 1983(a)(3)`
**Explanation:** Use parentheses for subsections, not periods.

#### Error 4.2: Missing Parentheses
**Incorrect:** `42 U.S.C. § 1983a3`
**Correct:** `42 U.S.C. § 1983(a)(3)`
**Explanation:** Each subdivision level needs parentheses.

#### Error 4.3: Capital Letters for First-Level Subsections
**Incorrect:** `42 U.S.C. § 1983(A)`
**Correct:** `42 U.S.C. § 1983(a)`
**Explanation:** First-level subsections use lowercase letters.

#### Error 4.4: Brackets Instead of Parentheses
**Incorrect:** `42 U.S.C. § 1983[a][3]`
**Correct:** `42 U.S.C. § 1983(a)(3)`
**Explanation:** Use parentheses, not brackets, for subsections.

### Error Category 5: Popular Names and Act Titles

#### Error 5.1: Not Italicizing Popular Names
**Incorrect:** `Americans with Disabilities Act, 42 U.S.C. § 12101`
**Correct (Academic):** `*Americans with Disabilities Act*, 42 U.S.C. § 12101` (in markdown: italicized)
**Explanation:** Italicize popular names in law review citations.

#### Error 5.2: Missing Comma After Popular Name
**Incorrect:** `Civil Rights Act of 1964 42 U.S.C. § 2000e`
**Correct:** `Civil Rights Act of 1964, 42 U.S.C. § 2000e`
**Explanation:** Use comma between popular name and code citation.

### Error Category 6: Session Law Format

#### Error 6.1: Missing "Pub. L. No."
**Incorrect:** `111-148, 124 Stat. 119 (2010)`
**Correct:** `Pub. L. No. 111-148, 124 Stat. 119 (2010)`
**Explanation:** Must include "Pub. L. No." for federal session laws.

#### Error 6.2: Wrong Hyphen Position
**Incorrect:** `Pub. L. No. 111 - 148`
**Correct:** `Pub. L. No. 111-148`
**Explanation:** No spaces around hyphen in public law number.

#### Error 6.3: Missing Statutes at Large Citation
**Incorrect:** `Pub. L. No. 111-148 (2010)`
**Correct:** `Pub. L. No. 111-148, 124 Stat. 119 (2010)`
**Explanation:** Include Statutes at Large volume and page.

### Error Category 7: Roman Numerals

#### Error 7.1: Arabic Numbers for Articles
**Incorrect:** `U.S. Const. art. 1, § 8`
**Correct:** `U.S. Const. art. I, § 8`
**Explanation:** Use Roman numerals for constitutional articles.

#### Error 7.2: Arabic Numbers for Amendments
**Incorrect:** `U.S. Const. amend. 14`
**Correct:** `U.S. Const. amend. XIV`
**Explanation:** Use Roman numerals for constitutional amendments.

#### Error 7.3: Lowercase Roman Numerals
**Incorrect:** `U.S. Const. art. i, § 8`
**Correct:** `U.S. Const. art. I, § 8`
**Explanation:** Use uppercase Roman numerals.

### Error Category 8: Publisher Information

#### Error 8.1: Missing Publisher for Unofficial Code
**Incorrect:** `Cal. Civ. Code § 1714 (2020)`
**Correct:** `Cal. Civ. Code § 1714 (West 2020)`
**Explanation:** Include publisher name for unofficial codes.

#### Error 8.2: Publisher for Official Code
**Incorrect:** `42 U.S.C. § 1983 (West 2018)` (U.S.C. is official)
**Correct:** `42 U.S.C. § 1983 (2018)` OR `42 U.S.C.A. § 1983 (West 2018)`
**Explanation:** Don't include publisher for official U.S.C.; use U.S.C.A. if citing West's annotated version.

#### Error 8.3: Wrong Publisher Abbreviation
**Incorrect:** `N.Y. Penal Law § 120.00 (McKinney's 2020)`
**Correct:** `N.Y. Penal Law § 120.00 (McKinney 2020)`
**Explanation:** Don't add apostrophe-s to publisher name.

### Error Category 9: Range and Multiple Sections

#### Error 9.1: Wrong Dash Type
**Incorrect:** `42 U.S.C. §§ 1981—1988`
**Correct:** `42 U.S.C. §§ 1981-1988`
**Explanation:** Use hyphen or en-dash, not em-dash, for ranges.

#### Error 9.2: Spaces Around Dash
**Incorrect:** `42 U.S.C. §§ 1981 - 1988`
**Correct:** `42 U.S.C. §§ 1981-1988`
**Explanation:** No spaces around dash in ranges.

#### Error 9.3: "To" Instead of Dash
**Incorrect:** `42 U.S.C. §§ 1981 to 1988`
**Correct:** `42 U.S.C. §§ 1981-1988`
**Explanation:** Use dash for ranges, not "to."

### Error Category 10: Special Forms

#### Error 10.1: Internal Revenue Code Format
**Incorrect:** `Title 26 U.S.C. § 61`
**Correct (Practitioner):** `I.R.C. § 61`
**Correct (Academic):** `26 U.S.C. § 61 (2018)`
**Explanation:** Use I.R.C. in practice; either form acceptable in academic writing.

#### Error 10.2: Federal Rules Format
**Incorrect:** `Federal Rule of Civil Procedure 56`
**Correct:** `Fed. R. Civ. P. 56`
**Explanation:** Use standard abbreviation.

#### Error 10.3: Ordinance Without Jurisdiction
**Incorrect:** `Municipal Code § 8-4-015 (2020)`
**Correct:** `Chicago, Ill., Municipal Code § 8-4-015 (2020)`
**Explanation:** Always include city and state for ordinances.

---

## Comprehensive Examples

### Example Set 1: U.S.C. Citations (Correct)

1. `42 U.S.C. § 1983` (current code, year optional under Bluebook 21st ed.)
2. `42 U.S.C. § 1983 (2018)` (specific edition cited)
3. `42 U.S.C. §§ 1981-1988` (range of sections)
4. `42 U.S.C. §§ 1983, 1985, 1988` (non-consecutive sections)
5. `42 U.S.C. § 2000e-2(a)(1)` (with subsections)
6. `15 U.S.C. § 78j(b)` (Securities Exchange Act)
7. `18 U.S.C. § 1961(1)` (RICO)
8. `29 U.S.C. §§ 201-219` (Fair Labor Standards Act)
9. `35 U.S.C. § 101` (Patent Act)
10. `17 U.S.C. § 102(a)` (Copyright Act)

### Example Set 2: U.S.C. Citations (Incorrect with Corrections)

**Incorrect:** `42 USC 1983`
**Correct:** `42 U.S.C. § 1983`
**Error:** Missing periods in U.S.C., missing section symbol

**Incorrect:** `42 U.S.C. Section 1983`
**Correct:** `42 U.S.C. § 1983`
**Error:** Should use § symbol, not word "section"

**Incorrect:** `42 U.S.C. §1983`
**Correct:** `42 U.S.C. § 1983`
**Error:** Missing space after section symbol

**Incorrect:** `42 U.S.C. § 1981 - 1988`
**Correct:** `42 U.S.C. §§ 1981-1988`
**Error:** Need double §§ for range, no spaces around dash

**Incorrect:** `42 U.S.C. § 1983.a.1`
**Correct:** `42 U.S.C. § 1983(a)(1)`
**Error:** Use parentheses for subsections, not periods

### Example Set 3: State Statute Citations (Correct)

1. `Cal. Civ. Code § 1714 (West 2020)` (California Civil Code)
2. `N.Y. Penal Law § 120.00 (McKinney 2021)` (New York Penal Law)
3. `Tex. Fam. Code Ann. § 153.001 (West 2021)` (Texas Family Code)
4. `Fla. Stat. § 768.81 (2020)` (Florida Statutes)
5. `Ill. Comp. Stat. 5/9-101 (West 2020)` (Illinois Compiled Statutes)
6. `Mass. Gen. Laws ch. 231, § 85K (2020)` (Massachusetts General Laws)
7. `Ohio Rev. Code Ann. § 2307.01 (West 2021)` (Ohio Revised Code)
8. `Va. Code Ann. § 8.01-581.15 (2020)` (Virginia Code)
9. `Wash. Rev. Code § 4.16.080 (2020)` (Washington Revised Code)
10. `Mich. Comp. Laws § 600.2912a (2020)` (Michigan Compiled Laws)

### Example Set 4: State Statute Citations (Incorrect with Corrections)

**Incorrect:** `Cal. Civil Code § 1714`
**Correct:** `Cal. Civ. Code § 1714 (West 2020)`
**Error:** Wrong abbreviation, missing publisher and year

**Incorrect:** `New York Penal Law § 120.00`
**Correct:** `N.Y. Penal Law § 120.00 (McKinney 2021)`
**Error:** State not abbreviated, missing publisher and year

**Incorrect:** `Texas Family Code § 153.001 (2021)`
**Correct:** `Tex. Fam. Code Ann. § 153.001 (West 2021)`
**Error:** State not abbreviated, missing "Ann.", missing publisher

**Incorrect:** `Fla. Stat. 768.81 (2020)`
**Correct:** `Fla. Stat. § 768.81 (2020)`
**Error:** Missing section symbol

**Incorrect:** `Illinois 5/9-101`
**Correct:** `735 Ill. Comp. Stat. 5/9-101 (West 2020)`
**Error:** Missing title number, wrong abbreviation, missing publisher/year

### Example Set 5: Session Law Citations (Correct)

1. `Pub. L. No. 111-148, 124 Stat. 119 (2010)` (Affordable Care Act)
2. `Civil Rights Act of 1964, Pub. L. No. 88-352, 78 Stat. 241 (1964)`
3. `Tax Cuts and Jobs Act, Pub. L. No. 115-97, 131 Stat. 2054 (2017)`
4. `Americans with Disabilities Act of 1990, Pub. L. No. 101-336, 104 Stat. 327 (1990)`
5. `Pub. L. No. 116-136, 134 Stat. 281 (2020)` (CARES Act)
6. `2020 Cal. Stat. ch. 123` (California session law)
7. `Act of May 15, 2020, ch. 45, 2020 N.Y. Laws 234` (New York session law)
8. `2019 Tex. Gen. Laws ch. 567` (Texas session law)
9. `2021 Fla. Laws ch. 21-123` (Florida session law)
10. `Pub. L. No. 117-58, 135 Stat. 429 (2021)` (Infrastructure Investment and Jobs Act)

### Example Set 6: Session Law Citations (Incorrect with Corrections)

**Incorrect:** `Public Law 111-148, 124 Stat. 119 (2010)`
**Correct:** `Pub. L. No. 111-148, 124 Stat. 119 (2010)`
**Error:** Must abbreviate "Pub. L." and include "No."

**Incorrect:** `Pub. L. 111-148`
**Correct:** `Pub. L. No. 111-148, 124 Stat. 119 (2010)`
**Error:** Missing Statutes at Large citation and year

**Incorrect:** `P.L. 111-148, 124 Stat. 119 (2010)`
**Correct:** `Pub. L. No. 111-148, 124 Stat. 119 (2010)`
**Error:** Wrong abbreviation (should be "Pub. L." not "P.L.")

**Incorrect:** `Civil Rights Act, 78 Stat. 241 (1964)`
**Correct:** `Civil Rights Act of 1964, Pub. L. No. 88-352, 78 Stat. 241 (1964)`
**Error:** Missing year in name and public law number

### Example Set 7: Constitutional Citations (Correct)

1. `U.S. Const. art. I, § 8` (Article I, Section 8)
2. `U.S. Const. art. I, § 8, cl. 3` (Commerce Clause)
3. `U.S. Const. amend. I` (First Amendment)
4. `U.S. Const. amend. IV` (Fourth Amendment)
5. `U.S. Const. amend. XIV` (Fourteenth Amendment)
6. `U.S. Const. amend. XIV, § 1` (Fourteenth Amendment, Section 1)
7. `N.Y. Const. art. I, § 6` (New York Constitution)
8. `Cal. Const. art. XIII A, § 1` (California Constitution - Prop 13)
9. `Tex. Const. art. I, § 19` (Texas Constitution)
10. `Ill. Const. art. I, § 2` (Illinois Constitution)

### Example Set 8: Constitutional Citations (Incorrect with Corrections)

**Incorrect:** `U.S. Constitution Article I, Section 8`
**Correct:** `U.S. Const. art. I, § 8`
**Error:** Not abbreviated, wrong punctuation

**Incorrect:** `U.S. Const. art. 1, § 8`
**Correct:** `U.S. Const. art. I, § 8`
**Error:** Use Roman numerals for articles

**Incorrect:** `U.S. Const. amend. 14`
**Correct:** `U.S. Const. amend. XIV`
**Error:** Use Roman numerals for amendments

**Incorrect:** `U.S. Const. Amendment XIV (1868)`
**Correct:** `U.S. Const. amend. XIV`
**Error:** Should abbreviate "amend." and never include year

**Incorrect:** `First Amendment`
**Correct:** `U.S. Const. amend. I`
**Error:** Must use proper citation format

### Example Set 9: Special Forms (Correct)

1. `I.R.C. § 61` (Internal Revenue Code - practitioner style)
2. `26 U.S.C. § 162(a) (2018)` (Internal Revenue Code - academic style)
3. `Fed. R. Civ. P. 56` (Federal Rule of Civil Procedure 56)
4. `Fed. R. Crim. P. 11` (Federal Rule of Criminal Procedure 11)
5. `Fed. R. Evid. 401` (Federal Rule of Evidence 401)
6. `Fed. R. App. P. 32` (Federal Rule of Appellate Procedure 32)
7. `Model Penal Code § 210.3 (Am. Law Inst. 1962)`
8. `Restatement (Second) of Contracts § 90 (Am. Law Inst. 1981)`
9. `Restatement (Third) of Torts § 1 (Am. Law Inst. 2010)`
10. `Uniform Commercial Code § 2-201 (Am. Law Inst. & Unif. Law Comm'n 2017)`

### Example Set 10: Ordinances (Correct)

1. `Chicago, Ill., Municipal Code § 8-4-015 (2020)`
2. `Los Angeles, Cal., Municipal Code § 12.24 (2021)`
3. `New York, N.Y., Administrative Code § 27-2004 (2020)`
4. `Houston, Tex., Code of Ordinances § 28-21 (2021)`
5. `Phoenix, Ariz., City Code § 23-12 (2020)`

### Example Set 11: Multiple Sections and Ranges

1. `42 U.S.C. §§ 1981-1988` (consecutive range)
2. `42 U.S.C. §§ 1983, 1985, 1988` (non-consecutive)
3. `42 U.S.C. §§ 9601-9675` (CERCLA - long range)
4. `15 U.S.C. §§ 1-7` (Sherman Act)
5. `18 U.S.C. §§ 1961-1968` (RICO)
6. `29 U.S.C. §§ 621-634` (ADEA)
7. `42 U.S.C. §§ 12101-12213` (ADA)
8. `17 U.S.C. §§ 101-1332` (Copyright Act - full title)
9. `Cal. Civ. Code §§ 1780-1784 (West 2020)` (California Consumer Legal Remedies Act)
10. `N.Y. C.P.L.R. §§ 3001-3025 (McKinney 2021)` (New York CPLR)

### Example Set 12: With Explanatory Parentheticals

1. `42 U.S.C. § 7401 (2018) (establishing national ambient air quality standards)`
2. `15 U.S.C. § 78j(b) (2018) (prohibiting securities fraud)`
3. `18 U.S.C. § 1961 (2018) (defining "racketeering activity")`
4. `42 U.S.C. § 2000e-2(a) (2018) (prohibiting employment discrimination)`
5. `29 U.S.C. § 215(a)(3) (2018) (prohibiting retaliation against employees)`

### Example Set 13: Repealed, Amended, and Invalidated Statutes

1. `42 U.S.C. § 6000 (1988) (repealed 1992)`
2. `18 U.S.C. § 3501 (2000) (held unconstitutional by Dickerson v. United States, 530 U.S. 428 (2000))`
3. `Pub. L. No. 104-193, 110 Stat. 2105 (1996) (codified as amended at 42 U.S.C. §§ 601-619 (2018))`
4. `26 U.S.C. § 1 (2012) (amended 2017)`
5. `Defense of Marriage Act § 3, Pub. L. No. 104-199, 110 Stat. 2419 (1996) (held unconstitutional by United States v. Windsor, 570 U.S. 744 (2013))`

### Example Set 14: Electronic and Online Sources

1. `42 U.S.C. § 1983 (LEXIS through Pub. L. No. 117-140)`
2. `42 U.S.C. § 2000e (Westlaw through Pub. L. No. 117-125)`
3. `Cal. Civ. Code § 1714 (Westlaw current through 2021 legislation)`
4. `N.Y. Penal Law § 120.00 (LEXIS through 2021 legislation)`
5. `Tex. Fam. Code Ann. § 153.001 (Westlaw current through end of 2021 Regular Session)`

### Example Set 15: Short Forms

**After full citation: `42 U.S.C. § 1983 (2018)`**

Short forms:
1. `Id.` (if immediately preceding citation)
2. `§ 1983` (if context clear)
3. `42 U.S.C. § 1983` (repeat if needed for clarity)

**After full citation: `Civil Rights Act of 1964, 42 U.S.C. § 2000e (2018)`**

Short forms:
1. `Id.`
2. `§ 2000e`
3. `Civil Rights Act § 2000e`

---

## Cross-References to Table 1 (Jurisdictions)

### Table 1: Federal Materials

**Legislative Materials:**
- United States Code: `U.S.C.`
- Statutes at Large: `Stat.`
- United States Code Annotated: `U.S.C.A.`
- United States Code Service: `U.S.C.S.`
- Session Laws (Congressional): `Pub. L. No.`

**Administrative Materials:**
- Code of Federal Regulations: `C.F.R.`
- Federal Register: `Fed. Reg.`

### Table 1: State Statutory Compilations

#### Alabama
- **Statutory Compilation:** `Ala. Code`
- **Session Laws:** `Ala. Acts`
- **Administrative Code:** `Ala. Admin. Code`

#### Alaska
- **Statutory Compilation:** `Alaska Stat.`
- **Session Laws:** `Alaska Sess. Laws`
- **Administrative Code:** `Alaska Admin. Code`

#### Arizona
- **Statutory Compilation:** `Ariz. Rev. Stat. Ann.`
- **Session Laws:** `Ariz. Sess. Laws`
- **Administrative Code:** `Ariz. Admin. Code`

#### Arkansas
- **Statutory Compilation:** `Ark. Code Ann.`
- **Session Laws:** `Ark. Acts`
- **Administrative Code:** `Ark. Admin. Code`

#### California
- **Statutory Compilation:** `Cal. [Subject] Code` (e.g., Cal. Civ. Code, Cal. Penal Code)
- **Session Laws:** `Cal. Stat.`
- **Administrative Code:** `Cal. Code Regs.` (C.C.R.)

**California Code Subjects:**
- Civil Code: `Cal. Civ. Code`
- Penal Code: `Cal. Penal Code`
- Business & Professions Code: `Cal. Bus. & Prof. Code`
- Health & Safety Code: `Cal. Health & Safety Code`
- Vehicle Code: `Cal. Veh. Code`
- Evidence Code: `Cal. Evid. Code`
- Family Code: `Cal. Fam. Code`

#### Colorado
- **Statutory Compilation:** `Colo. Rev. Stat.`
- **Session Laws:** `Colo. Sess. Laws`
- **Administrative Code:** `Colo. Code Regs.`

#### Connecticut
- **Statutory Compilation:** `Conn. Gen. Stat.`
- **Session Laws:** `Conn. Pub. Acts`
- **Administrative Code:** `Conn. Agencies Regs.`

#### Delaware
- **Statutory Compilation:** `Del. Code Ann.`
- **Session Laws:** `Del. Laws`

#### Florida
- **Statutory Compilation:** `Fla. Stat.`
- **Session Laws:** `Fla. Laws`
- **Administrative Code:** `Fla. Admin. Code Ann.`

#### Georgia
- **Statutory Compilation:** `Ga. Code Ann.`
- **Session Laws:** `Ga. Laws`
- **Administrative Code:** `Ga. Comp. R. & Regs.`

#### Hawaii
- **Statutory Compilation:** `Haw. Rev. Stat.`
- **Session Laws:** `Haw. Sess. Laws`

#### Idaho
- **Statutory Compilation:** `Idaho Code`
- **Session Laws:** `Idaho Sess. Laws`
- **Administrative Code:** `Idaho Admin. Code`

#### Illinois
- **Statutory Compilation:** `[Number] Ill. Comp. Stat. [Chapter]/[Section]`
- **Session Laws:** `Ill. Laws`
- **Administrative Code:** `Ill. Admin. Code`

#### Indiana
- **Statutory Compilation:** `Ind. Code`
- **Session Laws:** `Ind. Acts`
- **Administrative Code:** `Ind. Admin. Code`

#### Iowa
- **Statutory Compilation:** `Iowa Code`
- **Session Laws:** `Iowa Acts`
- **Administrative Code:** `Iowa Admin. Code`

#### Kansas
- **Statutory Compilation:** `Kan. Stat. Ann.`
- **Session Laws:** `Kan. Sess. Laws`
- **Administrative Code:** `Kan. Admin. Regs.`

#### Kentucky
- **Statutory Compilation:** `Ky. Rev. Stat. Ann.`
- **Session Laws:** `Ky. Acts`
- **Administrative Code:** `Ky. Admin. Regs.`

#### Louisiana
- **Statutory Compilation:** `La. [Subject] Code Ann.` or `La. Rev. Stat. Ann.`
- **Session Laws:** `La. Acts`
- **Administrative Code:** `La. Admin. Code`

#### Maine
- **Statutory Compilation:** `Me. Rev. Stat. Ann.`
- **Session Laws:** `Me. Laws`

#### Maryland
- **Statutory Compilation:** `Md. Code Ann., [Subject]`
- **Session Laws:** `Md. Laws`
- **Administrative Code:** `Md. Regs. Code`

#### Massachusetts
- **Statutory Compilation:** `Mass. Gen. Laws ch. [Chapter], § [Section]`
- **Session Laws:** `Mass. Acts`
- **Administrative Code:** `Mass. Regs. Code`

#### Michigan
- **Statutory Compilation:** `Mich. Comp. Laws`
- **Session Laws:** `Mich. Pub. Acts`
- **Administrative Code:** `Mich. Admin. Code`

#### Minnesota
- **Statutory Compilation:** `Minn. Stat.`
- **Session Laws:** `Minn. Laws`
- **Administrative Code:** `Minn. R.`

#### Mississippi
- **Statutory Compilation:** `Miss. Code Ann.`
- **Session Laws:** `Miss. Laws`

#### Missouri
- **Statutory Compilation:** `Mo. Rev. Stat.` or `Mo. Ann. Stat.`
- **Session Laws:** `Mo. Laws`
- **Administrative Code:** `Mo. Code Regs. Ann.`

#### Montana
- **Statutory Compilation:** `Mont. Code Ann.`
- **Session Laws:** `Mont. Laws`
- **Administrative Code:** `Mont. Admin. R.`

#### Nebraska
- **Statutory Compilation:** `Neb. Rev. Stat.`
- **Session Laws:** `Neb. Laws`
- **Administrative Code:** `Neb. Admin. R. & Regs.`

#### Nevada
- **Statutory Compilation:** `Nev. Rev. Stat.`
- **Session Laws:** `Nev. Stat.`
- **Administrative Code:** `Nev. Admin. Code`

#### New Hampshire
- **Statutory Compilation:** `N.H. Rev. Stat. Ann.`
- **Session Laws:** `N.H. Laws`

#### New Jersey
- **Statutory Compilation:** `N.J. Stat. Ann.` or `N.J. Rev. Stat.`
- **Session Laws:** `N.J. Laws`
- **Administrative Code:** `N.J. Admin. Code`

#### New Mexico
- **Statutory Compilation:** `N.M. Stat. Ann.`
- **Session Laws:** `N.M. Laws`

#### New York
- **Statutory Compilation:** `N.Y. [Subject] Law` (e.g., N.Y. Penal Law, N.Y. C.P.L.R.)
- **Session Laws:** `N.Y. Laws`
- **Administrative Code:** `N.Y. Comp. Codes R. & Regs.`

**Common New York Laws:**
- Penal Law: `N.Y. Penal Law`
- Civil Practice Law and Rules: `N.Y. C.P.L.R.`
- Business Corporation Law: `N.Y. Bus. Corp. Law`
- General Business Law: `N.Y. Gen. Bus. Law`

#### North Carolina
- **Statutory Compilation:** `N.C. Gen. Stat.`
- **Session Laws:** `N.C. Sess. Laws`
- **Administrative Code:** `N.C. Admin. Code`

#### North Dakota
- **Statutory Compilation:** `N.D. Cent. Code`
- **Session Laws:** `N.D. Laws`
- **Administrative Code:** `N.D. Admin. Code`

#### Ohio
- **Statutory Compilation:** `Ohio Rev. Code Ann.`
- **Session Laws:** `Ohio Laws`
- **Administrative Code:** `Ohio Admin. Code`

#### Oklahoma
- **Statutory Compilation:** `Okla. Stat. tit. [Title], § [Section]`
- **Session Laws:** `Okla. Sess. Laws`
- **Administrative Code:** `Okla. Admin. Code`

#### Oregon
- **Statutory Compilation:** `Or. Rev. Stat.`
- **Session Laws:** `Or. Laws`
- **Administrative Code:** `Or. Admin. R.`

#### Pennsylvania
- **Statutory Compilation:** `[Number] Pa. Cons. Stat.` or `Pa. Stat. Ann.`
- **Session Laws:** `Pa. Laws`
- **Administrative Code:** `Pa. Code`

#### Rhode Island
- **Statutory Compilation:** `R.I. Gen. Laws`
- **Session Laws:** `R.I. Pub. Laws`
- **Administrative Code:** `R.I. Code R.`

#### South Carolina
- **Statutory Compilation:** `S.C. Code Ann.`
- **Session Laws:** `S.C. Acts`
- **Administrative Code:** `S.C. Code Ann. Regs.`

#### South Dakota
- **Statutory Compilation:** `S.D. Codified Laws`
- **Session Laws:** `S.D. Sess. Laws`
- **Administrative Code:** `S.D. Admin. R.`

#### Tennessee
- **Statutory Compilation:** `Tenn. Code Ann.`
- **Session Laws:** `Tenn. Pub. Acts`
- **Administrative Code:** `Tenn. Comp. R. & Regs.`

#### Texas
- **Statutory Compilation:** `Tex. [Subject] Code Ann.` (e.g., Tex. Penal Code Ann.)
- **Session Laws:** `Tex. Gen. Laws`
- **Administrative Code:** `Tex. Admin. Code`

**Common Texas Codes:**
- Penal Code: `Tex. Penal Code Ann.`
- Family Code: `Tex. Fam. Code Ann.`
- Business & Commerce Code: `Tex. Bus. & Com. Code Ann.`
- Civil Practice & Remedies Code: `Tex. Civ. Prac. & Rem. Code Ann.`

#### Utah
- **Statutory Compilation:** `Utah Code Ann.`
- **Session Laws:** `Utah Laws`
- **Administrative Code:** `Utah Admin. Code`

#### Vermont
- **Statutory Compilation:** `Vt. Stat. Ann. tit. [Title], § [Section]`
- **Session Laws:** `Vt. Acts`
- **Administrative Code:** `Vt. Code R.`

#### Virginia
- **Statutory Compilation:** `Va. Code Ann.`
- **Session Laws:** `Va. Acts`
- **Administrative Code:** `Va. Admin. Code`

#### Washington
- **Statutory Compilation:** `Wash. Rev. Code`
- **Session Laws:** `Wash. Sess. Laws`
- **Administrative Code:** `Wash. Admin. Code`

#### West Virginia
- **Statutory Compilation:** `W. Va. Code`
- **Session Laws:** `W. Va. Acts`
- **Administrative Code:** `W. Va. Code R.`

#### Wisconsin
- **Statutory Compilation:** `Wis. Stat.`
- **Session Laws:** `Wis. Sess. Laws`
- **Administrative Code:** `Wis. Admin. Code`

#### Wyoming
- **Statutory Compilation:** `Wyo. Stat. Ann.`
- **Session Laws:** `Wyo. Sess. Laws`

---

## Quick Reference Chart

| Citation Type | Format | Example |
|--------------|--------|---------|
| **U.S.C. (current)** | `[Title] U.S.C. § [Section]` | `42 U.S.C. § 1983` |
| **U.S.C. (specific ed.)** | `[Title] U.S.C. § [Section] ([Year])` | `42 U.S.C. § 1983 (2018)` |
| **State Code** | `[State] [Code] § [Section] ([Publisher] [Year])` | `Cal. Civ. Code § 1714 (West 2020)` |
| **Federal Session Law** | `Pub. L. No. [No.], [Vol.] Stat. [Page] ([Year])` | `Pub. L. No. 111-148, 124 Stat. 119 (2010)` |
| **U.S. Constitution** | `U.S. Const. art. [Roman], § [Number]` | `U.S. Const. art. I, § 8` |
| **U.S. Amendment** | `U.S. Const. amend. [Roman]` | `U.S. Const. amend. XIV` |
| **State Constitution** | `[State] Const. art. [Number], § [Number]` | `N.Y. Const. art. I, § 6` |
| **I.R.C.** | `I.R.C. § [Section]` | `I.R.C. § 61` |
| **Federal Rules** | `Fed. R. [Type] P. [Number]` | `Fed. R. Civ. P. 56` |
| **Ordinance** | `[City], [State], [Code] § [Section] ([Year])` | `Chicago, Ill., Municipal Code § 8-4-015 (2020)` |

---

## Summary Checklist

### Before Citing a Statute:

- [ ] Identify type: federal code, state code, or session law
- [ ] Use official code if available
- [ ] Include proper abbreviations from Table 1
- [ ] Use § or §§ correctly (single vs. multiple sections)
- [ ] Space after section symbol
- [ ] Include year (required for state codes, optional for current U.S.C.)
- [ ] Include publisher for unofficial codes
- [ ] Use parentheses for subsections
- [ ] Check for repeals, amendments, or invalidations

### Before Citing a Constitution:

- [ ] Use proper abbreviation (U.S. Const. or state abbreviation)
- [ ] Use Roman numerals for articles and amendments
- [ ] Abbreviate "art." and "amend."
- [ ] Use § for sections
- [ ] Do NOT include dates
- [ ] Check comma placement

---

**Document End**

*This analysis is based on Bluebook Rules 11-13 as implemented in the SLRinator configuration. For the most current Bluebook rules, consult the latest edition of The Bluebook: A Uniform System of Citation.*
