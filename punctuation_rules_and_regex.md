# Bluebook Punctuation Rules & Regex Pattern Extraction

## Overview
This document extracts ALL punctuation rules from the Bluebook (as defined in `/home/user/slr/reference_files/Bluebook.json`) and provides regex patterns to detect common punctuation errors.

---

## 1. COMMA RULES

### 1.1 Citation Clauses
**Rule**: Authorities that support only part of a sentence are cited in clauses, set off by commas, that immediately follow the proposition they support.

**Example**: "Authorities that support (or contradict) only part of a sentence within a footnote are cited in clauses, set off by commas, that immediately follow the proposition they support (or contradict)."

**Regex Patterns for Errors**:
```regex
# Missing comma before citation clause
/[a-zA-Z0-9]\.?\s+(?:See|See also|But see|Cf\.)\s+[A-Z]/
# Comma should precede citation clause

# Extra space after comma
/,\s{2,}/
# Only one space after comma allowed

# Missing space after comma
/,\S/
# Must have space after comma
```

---

### 1.2 Multiple Citations - Comma vs Semicolon Separator
**Rule**: When multiple authorities follow signals OTHER THAN "compare/contrast", separate them with COMMAS.
- Example: "See X, Y, and Z"

**Rule**: When "compare/contrast" signals are used, separate multiple sources with SEMICOLONS.
- Example: "Compare X, 410 U.S. 113 (1973), with Y, 410 U.S. 179 (1973)"

**Rule**: When a signal is used as a verb, separate multiple sources with SEMICOLONS.
- Example: "But see X; But see Y"

**Regex Patterns for Errors**:
```regex
# Comma instead of semicolon in compare/contrast
/Compare\s+[^;]*,\s+[^w]*with\s+/
# Should use semicolon between compare/contrast pairs

# Comma instead of semicolon when signal is verb (But see X, Y)
/(See also|But see)\s+[A-Za-z].*?,\s+[A-Za-z].*?,/
# Multiple sources with signal-as-verb should use semicolons

# Mixed comma and semicolon incorrectly
/(See|Cf)\s+[^;]*,\s*;\s*/
# Inconsistent separation
```

---

### 1.3 Parallel Citations
**Rule**: When required to provide parallel citations, list citations separated by commas.

**Example**: "23 Nat'l L.J., no. 5, at 12 (2020)"

**Regex Patterns for Errors**:
```regex
# Missing comma before issue number in periodicals
/\d+\s+[A-Z][\w\s]*\s+(?:no|number)\s+/
# Should have comma before "no."

# Space before comma
/\s+,/
# No space should precede comma
```

---

### 1.4 Nonconsecutive Sections
**Rule**: For nonconsecutive sections, separate by commas.

**Example**: "§§ 1234, 1235, 1236"

**Regex Patterns for Errors**:
```regex
# Missing comma between nonconsecutive sections
/§\s*\d+\s+\d+/
# Should have comma: § 1234, 1235

# Incorrect spacing in section numbers
/§\s{2,}|§\s*$/
# Must have exactly one space after §
```

---

## 2. PERIOD RULES

### 2.1 Citation Sentence Requirement
**Rule**: A citation sentence starts with a capital letter and ends with a period.

**Regex Patterns for Errors**:
```regex
# Citation sentence missing period at end
/(See|Accord|Cf|But see|But cf|See generally)\s+[^\.]+$(?!.*\.)
# Citation sentence must end with period

# Multiple periods (ellipsis vs period)
/\.\.\.\./
# Three dots only; four dots typically incorrect

# Period inside parentheses, then outside
/\)\s*\.\s*\(/
# Punctuation placement with parentheses
```

---

### 2.2 No Period After Section Symbols
**Rule**: When citing subdivisions (§ or ¶), use the symbol followed by the number WITHOUT A PERIOD.

**Example**: "42 U.S.C. § 1234" (NOT "§. 1234")

**Regex Patterns for Errors**:
```regex
# Period after section symbol
/§\s*\d+\./
# Remove period: § 1234

# Period after paragraph symbol
/¶\s*\d+\./
# Remove period: ¶ 123

# Double section symbol with period
/§§\s*\d+\./
# Should be: §§ 1234
```

---

### 2.3 Periods in Educational Degrees
**Rule**: SLR does NOT omit periods in educational degrees. Use "J.D." not "JD", and "Ph.D." not "PhD".

**Regex Patterns for Errors**:
```regex
# Missing periods in degrees
/\bJD\b/
# Should be: J.D.

# Missing periods in other degrees
/\bPhD\b|\bMBA\b(?!\.)/
# Should be: Ph.D., M.B.A.

# Incorrect formatting
/J\.D\.|Ph\.D\.|M\.B\.A\./
# Ensure spaces between letters: J.D., Ph.D., M.B.A.
```

---

## 3. SEMICOLON RULES

### 3.1 Semicolons Separating Signal Groups
**Rule**: Signals of the same basic type (supportive, comparative, contradictory, background) must be strung together and separated by SEMICOLONS.

**Example**: "See Mass. Bd. of Ret. v. Murgia, 427 U.S. 307 (1976); cf. Palmer v. Ticcione, 433 F. Supp. 653"

**Regex Patterns for Errors**:
```regex
# Comma instead of semicolon between same-type signals
/(See|Accord)\s+[^;]*\)\s*,\s*(See|Accord|Cf)\s+/
# Should use semicolon between citations of same signal type

# Missing semicolon in authority list
/U\.S\.\s+\d+\)\s*[A-Z]/
# Likely missing semicolon between citations

# Inconsistent use of semicolons and commas
/;\s*and\s+/
# Choose either semicolon OR comma consistently
```

---

### 3.2 Semicolons in Explanatory Parentheticals
**Rule**: When citing multiple authorities in one explanatory parenthetical, separate each authority with a semicolon.

**Example**: "(citing Smith v. Jones, 123 U.S. 456 (1900); Doe v. Bolton, 410 U.S. 179 (1973))"

**Regex Patterns for Errors**:
```regex
# Comma instead of semicolon in parenthetical with multiple citations
/\(\s*(?:citing|quoting)\s+[^;)]*\)\s*,\s*[A-Z]/
# Use semicolon to separate multiple citations in parenthetical

# Missing semicolon before year
/\(\s*\d+\)\s*[A-Z]\./
# Likely needs semicolon before next citation
```

---

## 4. PARENTHESES RULES

### 4.1 Parentheticals in Citations
**Rule**: Certain additional information (case history, explanatory parentheticals) may be provided in parentheses at the end of a citation.

**Regex Patterns for Errors**:
```regex
# Missing parentheses around court/year
/[A-Z]\.S\.\s+\d+\s+\d{4}(?!\))/
# Should be: (2023) at end

# Extra spaces inside parentheses
/\(\s+[A-Z]|\s+\)/
# No spaces after opening paren or before closing paren

# Mismatched parentheses count
/\([^)]*\([^)]*\)[^)]*\)/
# Nested parentheses should use square brackets instead
```

---

### 4.2 Nested Parentheses - MUST Use Square Brackets
**Rule**: Do NOT use nested parentheses. If you need a parenthetical within a parenthetical, change inner parentheses to square brackets.

**Wrong**: "(citing (for example, the Hippocratic Oath))"
**Right**: "(citing [for example, the Hippocratic Oath])"

**Regex Patterns for Errors**:
```regex
# Nested parentheses - CRITICAL ERROR
/\([^)]*\([^)]*\)[^)]*\)/
# Replace inner parentheses with square brackets
# Correct pattern: \([^)]*\[[^\]]*\][^)]*\)

# Unmatched parentheses
/\([^)]*$|[^(]*\)/
# Check for balanced parentheses

# Mixed brackets and parentheses incorrectly
/\(\[|\]\)/
# Should not mix outer parentheses with inner brackets
```

---

### 4.3 Court/Jurisdiction in Parentheses
**Rule**: In parentheses at end of citation, include court abbreviation and year.
- State high courts: "N.Y. 1990"
- Intermediate/Federal courts: "5th Cir." or "Cal. Ct. App."

**Regex Patterns for Errors**:
```regex
# Missing parentheses around court/year
/\b\d{4}\s*$(?!\))/
# Year must be in parentheses

# Missing year in parentheses
/\([A-Z].*\.\)\s*$(?!.*\d{4})/
# Parenthetical missing year

# Space before opening parenthesis
/\)\s{2,}\(/
# Only one space before opening paren of court/year
```

---

### 4.4 Parenthetical Placement
**Rule**: When multiple parentheticals follow a citation:
1. Weight of authority parenthetical
2. Explanatory parenthetical
3. Quotation parenthetical

**Regex Patterns for Errors**:
```regex
# Multiple parentheticals in wrong order
/\(quot[^)]*\)\s*\(argu[^)]*\)/
# Quotation should come after explanatory

# Missing punctuation between parentheticals
/\)\([a-z]/
# Need space: ) (

# Multiple spaces between parentheticals
/\)\s{2,}\(/
# Only one space between parentheticals
```

---

## 5. BRACKET RULES

### 5.1 Brackets for Alterations in Quotations
**Rule**: Indicate alterations to quoted text with brackets, including added/changed letters or words.

**Examples**:
- "[sic]" - error in original
- "start[ing]" - altered form
- "[emphasis added]" - note alterations
- "[Law on Joint Stock Companies]" - translation

**Regex Patterns for Errors**:
```regex
# Missing brackets around altered letters
/[a-z]ing\s+(?:on|of|to)/
# Should be: [ing] or starting[ed]

# Parentheses instead of brackets for alterations
/\(sic\)|\(emphasis added\)|\(emphasis in original\)/
# Use brackets: [sic], [emphasis added]

# Incorrect bracket use for non-alterations
/text\s*\[[^\]]*\]\s+text/
# Brackets should only mark alterations, not just grouping
```

---

### 5.2 Square Brackets for Internal Parentheticals
**Rule**: When parenthetical needed within parenthetical, use square brackets for the inner one.

**Regex Patterns for Errors**:
```regex
# Nested parentheses (should be nested brackets)
/\([^)]*\([^)]*\)[^)]*\)/
# Change to: (text [inner text] text)

# Inconsistent bracket use
/\[[^\]]*\([^)]*\)[^\]]*\]/
# Should be consistent: [ (...) ]
```

---

### 5.3 Brackets for Descriptive Titles/Translations
**Rule**: Use brackets for descriptive or translated titles in citations.

**Examples**:
- "[Name of Act] [year] (UK)"
- "Code civil [C. civ.] art. 1382 (Fr.)"
- "[Law on Joint Stock Companies] (Belgium)"

**Regex Patterns for Errors**:
```regex
# Missing brackets around translations
/\([A-Z].*[a-z].*\)\s*\((?:Fr|Ger|Uk)\)/
# Should bracket the translation

# Inconsistent bracket placement for codes
/code\s+[a-z]\.?\s+art/i
# Should have brackets: Code civ. [C. civ.] art.
```

---

## 6. COLON RULES

### 6.1 Colons in Subtitles
**Rule**: In titles of works, always include subtitles after a COLON.

**Example**: "Title: Subtitle"

**Regex Patterns for Errors**:
```regex
# Dash instead of colon for subtitle
/[A-Z][^:]*–\s*[A-Z]/
# Should use colon: Title: Subtitle

# Missing colon before subtitle
/([A-Z][^:]*)\s+([A-Z][\w\s]+)(?![0-9])/
# Check if subtitle should follow colon

# Multiple colons in title
/:\s*[^:]*:/
# Only one colon for title/subtitle separation
```

---

### 6.2 Colons in Introductory Citations
**Rule**: Footnote call number comes after any punctuation mark EXCEPT a dash or colon.

**Regex Patterns for Errors**:
```regex
# Footnote marker before colon
/\d+\s*:/
# Footnote marker should come after colon

# Space before colon
/\s+:/
# No space before colon
```

---

## 7. DASH RULES

### 7.1 Em Dash in Parentheticals (Non-grammatical)
**Rule**: A parenthetical phrase that is NOT grammatically part of a sentence is preceded by an em dash.

**Example**: "The Court noted... — (explaining the doctrine)."

**Regex Patterns for Errors**:
```regex
# Em dash before grammatical parenthetical
/—\s*\(/
# Em dash should NOT precede grammatical parentheticals

# Hyphen instead of em dash
/-\s*\([a-z]/
# Use em dash (—), not hyphen (-)

# Multiple dashes
/—+|--+/
# Should use single em dash
```

---

### 7.2 Hyphens in Statutory Citations
**Rule**: When identical digits separated by hyphen in statute (42 U.S.C. § 4001-03), write as: § 4001-03 (not §§ 4001-03).

**Regex Patterns for Errors**:
```regex
# Double section symbol with hyphenated range
/§§\s*\d+-\d+/
# Should be: § 4001-03 (single symbol)

# Missing hyphen in range
/\d+\s+\d+/
# Check if should be hyphenated: 4001-03

# Space around hyphen
/\d+\s+-\s+\d+/
# No spaces around hyphen: 4001-03
```

---

### 7.3 Hyphens in Repeated Digits
**Rule**: When section number has identical repeated digit separated by punctuation (42 U.S.C. § 1490dd), include only one section symbol and put COMMA between identical digits.

**Example**: Write "§ 1490, dd" not "§§ 1490dd"

**Regex Patterns for Errors**:
```regex
# Double section symbol with repeated digits
/§§\s*\d+([a-z]+)\d+\1/
# Use single symbol: § 1490, dd

# Missing comma between repeated digits
/§\s*\d+([a-z])\1/
# Add comma: § 1490, dd

# No space after comma in repeated digits
/,([a-z])/
# Should be: , dd
```

---

## 8. QUOTATION AND ELLIPSIS RULES

### 8.1 Block Quotations
**Rule**: Quotations of 50+ words formatted as block quotations (indented, without quotation marks). Shorter quotations remain in-line with quotation marks.

**Regex Patterns for Errors**:
```regex
# Missing opening quotation mark
/(?<![""])\b[A-Z][^.!?]*[.!?](?!\s*[""])/
# Check if quote needs opening quote

# Unmatched quotation marks
/"[^"]*$|^[^"]*"/
# Ensure balanced quotation marks

# Block quote with quotation marks
/^\s{4,}[""]/m
# Block quotes should NOT have quotation marks
```

---

### 8.2 Ellipsis (Three Dots Only)
**Rule**: Use ellipsis ("...") to indicate omitted material. Do not begin quote with ellipsis if material starts midsentence; use lowercase letter instead.

**Regex Patterns for Errors**:
```regex
# Four dots instead of three (period + ellipsis)
/\.\.\.\./
# Use only three dots: ...

# Ellipsis at start of quote
/"\.\.\.\s+[a-z]/
# Remove ellipsis; start with lowercase letter: "[a-z]"

# Space before ellipsis
/\s+\.\.\./
# No space before ellipsis

# Ellipsis with extra spaces between dots
/\.\s+\.\s+\./
# Should be consecutive: ...
```

---

### 8.3 Alternating Quotation Marks
**Rule**: When quoting text containing a quote, alternate between double and single quotation marks (outermost determined by context).

**Example**: He said, "I believe she said 'wait here.'"

**Regex Patterns for Errors**:
```regex
# Matching outer and inner quotes
/"[^"]*"[^"]*"[^"]*"/
# Should alternate: "... '...' ..."

# Missing inner quote change
/'[^']*"[^"]*'/
# Should match: '...' inside "..." and vice versa

# Unmatched quote types
/(?<!")["'][^"']*["'](?!")/
# Ensure quotes are balanced and alternating
```

---

### 8.4 Punctuation Within Quotations
**Rule**: When punctuation mark in underlying material is NOT intended part of quotation:
- OMIT if at END of quotation
- INCLUDE if at BEGINNING of quotation

**Regex Patterns for Errors**:
```regex
# Period inside quote marks followed by citation
/"[^"]*\.[^"]*"\s+[A-Z]/
# May need to move period outside quotes

# Missing punctuation before closing quote
/[a-z]"\s*\)/
# Punctuation typically goes inside quotes (before closing mark)

# Comma splice in quotation
/"[^"]*,[^"]*and/
# Verify comma usage within quote is original
```

---

## 9. INTERNAL PUNCTUATION FORMATTING

### 9.1 Spacing Around Punctuation
**Rule**: Proper spacing around punctuation marks.

**Regex Patterns for Errors**:
```regex
# No space after comma
/,[a-zA-Z0-9]/
# Must have: , [space]

# Space before comma
/\s+,/
# No space before comma

# Space before period (unless ellipsis)
/\s+\.(?!\.)/
# No space before period

# Space before colon (except ratio cases)
/\s+:(?![0-9])/
# No space before colon (except U.S. Reporter format)
```

---

### 9.2 Italics with Punctuation
**Rule**: Italicize punctuation marks ONLY if immediately adjacent to italicized words. No italicization if space exists between word and punctuation.

**Example**:
- Right: *case name*, (italics include comma)
- Wrong: *case name* , (space breaks adjacency)

**Regex Patterns for Errors**:
```regex
# Space between italicized word and following punctuation
/\*[^*]+\*\s+[\.,;:!?]/
# Punctuation should be inside italics if adjacent

# Punctuation outside italics when should be inside
/\*[^*:;,.!?]*[\w]\*\s*[.,;:!?]/
# Check if punctuation should be italicized

# Nested asterisks (markdown formatting issues)
/\*\*.*?\*\*/
# Ensure correct markup
```

---

## 10. ARTICLE/PERIODICAL PUNCTUATION

### 10.1 Article Title Formatting
**Rule**: Article titles in italics in academic writing (or in quotes in court documents). Include any punctuation exactly as published (including question marks).

**Regex Patterns for Errors**:
```regex
# Article title without italic/quote markers
/Author,\s+[A-Z][a-z\s]+,\s+\d+\s+[A-Z]/
# Title should be italicized: *Title Here*

# Missing question mark in title
/Title\s+[A-Z]|Title\s+\d/
# Check if original title ends with ?
```

---

### 10.2 Periodical Date Formatting
**Rule**: Include issue date/number for non-consecutively paginated journals. Format: "23 Nat'l L.J., no. 5, at 12 (2020)"

**Regex Patterns for Errors**:
```regex
# Missing comma before issue number
/\d+\s+Nat'?l\s+\w+(?:no|number)\s+/
# Should be: 23 Nat'l L.J., no. 5

# Incorrect spacing around "no."
/,\s*no\s+\d+|no\.\s{2,}\d+/
# Should be: , no. 5

# Missing "at" before page number
/\d+\s+\(\d{4}\)\s+\d+/
# Should have "at": at 12 (2020)
```

---

## 11. COMMON PUNCTUATION ERROR PATTERNS

### Pattern A: Comma Splice in Citations
```regex
/(See|Accord|But see)\s+[A-Z][^,]*[0-9]\)\s*,\s*[A-Z]/
# Two independent clauses joined by comma
```

### Pattern B: Missing Space After Punctuation
```regex
/[.,;:]\S/
# All marks need space after (except in special cases like URLs)
```

### Pattern C: Double Punctuation
```regex
/[.,;:]{2,}|—+|--+/
# Only single punctuation allowed (except ellipsis)
```

### Pattern D: Unmatched Parentheses/Brackets
```regex
/(\((?:[^()]|\([^)]*\))*\))|(\[(?:[^\[\]]|\[[^\]]*\])*\])/
# Count opening/closing marks
```

### Pattern E: Incorrect Quotation Mark Pairing
```regex
/["'].*?["']/
# Ensure matching pairs and proper nesting
```

---

## 12. QUICK REFERENCE TABLE

| Element | Rule | Regex Pattern |
|---------|------|---------------|
| Comma after citation clause | Required | `/[a-zA-Z]\)\s*,\s+(?:See\|Accord)/` |
| Semicolon between compare/contrast | Required | `/Compare.*with/` should use `;` not `,` |
| Period after sentence | Required | `/^(?:See\|Accord)[^.]*$/` |
| Period after § symbol | Forbidden | `/§\s*\d+\./` |
| Nested parentheses | Forbidden | `/\([^)]*\([^)]*\)[^)]*\)/` |
| Em dash before non-grammatical parenthetical | Required | `/(—\s*\()|(?<!—)\s*\(/` |
| Ellipsis dots | Three only | `/\.\.\.\./` |
| Space after comma | Required | `/,[^\s]/` |
| Space before comma | Forbidden | `/\s+,/` |
| Colon for subtitle | Required | `/Title\s+[A-Z]/` should be `Title:` |

---

## 13. REGEX PATTERNS FOR AUTOMATED CHECKING

### High Priority (Critical Errors)

```javascript
// 1. Nested parentheses without brackets
const nestedParens = /\([^)]*\([^)]*\)[^)]*\)/g;

// 2. Missing periods in degree abbreviations
const missingDegreesPeriods = /\b(JD|PhD|MBA|LLM)(?!\.)/g;

// 3. Four dots instead of three
const fourDots = /\.\.\.\./g;

// 4. Unmatched quotation marks
const unmatchedQuotes = /["'](?:[^"']|"")*$/gm;

// 5. Comma before citation in same signal
const commaBetweenCitations = /(See|Accord)\s+[^;]*\)\s*,\s*(See|Accord)\s+/g;
```

### Medium Priority (Spacing/Formatting)

```javascript
// 1. Space before comma
const spaceBeforeComma = /\s+,/g;

// 2. No space after comma
const noSpaceAfterComma = /,([^\s\d])/g;

// 3. Space before period
const spaceBeforePeriod = /\s+\.(?!\.)/g;

// 4. Multiple spaces between words
const multipleSpaces = /  +/g;

// 5. Em dash with extra spaces
const emDashSpacing = /\s+—\s+/g;
```

### Lower Priority (Style Consistency)

```javascript
// 1. Inconsistent quote types in alternation
const inconsistentQuotes = /"[^"]*'[^']*"/g;

// 2. Capital letter start in parenthetical
const capitalInParenthetical = /\(\s*[A-Z]/g;

// 3. Missing "at" before page in periodical
const missingAtPage = /(\d+)\s+\(\d{4}\)\s+(\d+)/g;
```

---

## 14. IMPLEMENTATION NOTES

1. **Whitespace Sensitivity**: Many errors involve improper spacing. Use `\s` for any whitespace and ` ` (space) for specific spacing.

2. **Context Matters**: Some rules depend on context (e.g., comma usage depends on the signal type). Combine regex with contextual logic.

3. **Character Encoding**: Ensure proper Unicode handling for:
   - Em dash (—, U+2014) vs hyphen (-) vs en dash (–)
   - Different quotation marks (" " ' ' « »)
   - Section symbol (§) and paragraph (¶)

4. **False Positives**: Some regex patterns may trigger false positives in:
   - URLs (spacing rules don't apply)
   - Non-English text (punctuation rules may differ)
   - Block quotes (different formatting)

5. **Testing**: Always test patterns against sample Bluebook citations to ensure accuracy.

---

## 15. SOURCE REFERENCE

All rules extracted from: `/home/user/slr/reference_files/Bluebook.json`

Key sections reviewed:
- Rule 1.0-1.16: Structure and Use of Citations
- Rule 2.0-2.3: Typefaces and Punctuation
- Rule 3.0-3.4: Subdivisions
- Rule 5.0-5.2: Quotations
- Rule 10.0-10.9: Periodicals
- Rules for Statutes, Foreign Sources, and International Materials

---
