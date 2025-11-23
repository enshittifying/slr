# Capitalization Linting Patterns for Bluebook Rule 8

This document provides regex patterns and linting rules that can be used to identify potential capitalization violations in legal writing.

---

## Regex Patterns for Capitalization Detection

### Pattern 1: Lowercase amendments (potential error)

```regex
\b(first|second|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|twentieth|twenty.first|twenty.second|twenty.third|twenty.fourth|twenty.fifth|twenty.sixth|twenty.seventh) amendment\b
```

**Trigger**: Suggests "Amendment" should be capitalized
**Exception**: When used in phrase like "the first amendment's protections" (amendment is still part of proper reference)
**Correction**: Capitalize → "First Amendment"

---

### Pattern 2: Lowercase civil rights act (potential error)

```regex
\b(civil rights|fair housing|americans with disabilities|social security|affordable care|environmental protection|equal pay|americans|civil)?(\s)?[a-z]+(\s)?act\b
```

**Trigger**: Suggests specific act name should have "Act" capitalized
**Exception**: Generic "the act" or "this act"
**Correction**: Capitalize named acts → "Civil Rights Act"

---

### Pattern 3: Inconsistent court capitalization

```regex
(?<![A-Z])(the court)(?!\s(of|in|system))|(?<![A-Z])(this court)|(?<![A-Z])(our court)
```

**Trigger**: Potential U.S. Supreme Court reference using lowercase "court"
**Exception**: When clearly referring to lower courts in context
**Correction**: Change to "the Court" if referring to U.S. Supreme Court

---

### Pattern 4: Lowercase judge titles before names

```regex
\b(judge|justice|chief\s+justice|associate\s+justice)\s+([a-z][a-z]+)\b
```

**Trigger**: Judge/justice title not capitalized before a name
**Exception**: None - should always capitalize
**Correction**: Capitalize titles → "Judge Smith", "Chief Justice Marshall"

---

### Pattern 5: Party names with first names

```regex
\b([A-Z][a-z]+\s+[A-Z][a-z]+|[A-Z]\.\s+[A-Z]\.)\s+v\.\s+
```

**Trigger**: Potential first name in party name (e.g., "John Smith v.")
**Correction**: Use last name only → "Smith v."

---

### Pattern 6: Party names starting with "The"

```regex
\bThe\s+[A-Z][a-z]+\s+v\.\s+
```

**Trigger**: Party name starts with "The"
**Correction**: Omit "The" → "Blue Cross v." not "The Blue Cross v."

---

### Pattern 7: Lowercase document titles (specific documents)

```regex
\b(brief|motion|affidavit|declaration|petition|complaint|answer|reply|memorandum)\s+(for|in|of)\s+[a-z]
```

**Trigger**: Document title not following title case capitalization
**Exception**: When used generically ("the brief", "a motion", "this affidavit")
**Correction**: Capitalize → "Brief for Petitioner", "Motion for Summary Judgment"

---

### Pattern 8: Inconsistent constitution element capitalization

```regex
\b(article|amendment|clause|section)\s+([IVX]+|[A-Z]|[0-9]+)\b(?![A-Z])
```

**Trigger**: Constitutional element reference with lowercase lead word
**Correction**: Capitalize → "Article I", "Fourteenth Amendment", "Commerce Clause"

---

### Pattern 9: Parenthetical capitalization error

```regex
\(\s*([A-Z][a-z]+\s+[^.!?]*|[A-Z][a-z]+\s+[a-z]+[^.!?]*)
```

**Trigger**: Parenthetical starting with capitalized word (that isn't proper noun)
**Exception**: When first word is proper noun (place, person, institution name)
**Correction**: Start with lowercase → "(finding that...", not "(Finding that...)"

---

### Pattern 10: Book/article titles - improper capitalization

```regex
\b(in|on|at|for|by|of|a|an|the|and|but|or|nor)\s+[A-Z][a-z]+
```

**Trigger**: Articles/conjunctions/short prepositions capitalized in middle of title
**Exception**: If word is first or last in title, or it's a proper noun
**Correction**: Lowercase → "Law and Society" not "Law And Society"

---

## Linting Rules (For Automation)

### Rule 1: Amendment Capitalization
**Severity**: HIGH
**Pattern**: Lowercase amendment names
**Auto-fix**: Capitalize → `first amendment` → `First Amendment`
**Bluebook Reference**: Rule 8

---

### Rule 2: Act/Statute Name Capitalization
**Severity**: HIGH
**Pattern**: Named acts with lowercase "act"
**Auto-fix**: Capitalize → `civil rights act` → `Civil Rights Act`
**Exceptions**: Generic references like "the act", "this statute"
**Bluebook Reference**: Rule 8

---

### Rule 3: Court Name Capitalization
**Severity**: MEDIUM
**Pattern**: Inconsistent "Court" vs "court" usage
**Auto-fix**:
- U.S. Supreme Court context: lowercase → `the Court`
- Other courts: capitalize → `the court` (if appropriate context)
**Bluebook Reference**: Rule 9

---

### Rule 4: Judge/Official Title Capitalization
**Severity**: HIGH
**Pattern**: Lowercase titles before names
**Auto-fix**: Capitalize → `judge smith` → `Judge Smith`
**Note**: Only capitalize before names or when referring to specific person
**Bluebook Reference**: Rule 9

---

### Rule 5: Party Name - No First Names
**Severity**: HIGH
**Pattern**: First or middle names in party names
**Auto-fix**: Remove → `John Smith v. Mary Jones` → `Smith v. Jones`
**Bluebook Reference**: Rule 10.2

---

### Rule 6: Party Name - No Leading "The"
**Severity**: MEDIUM
**Pattern**: Party name starts with "The"
**Auto-fix**: Remove → `The Blue Cross v. State` → `Blue Cross v. State`
**Bluebook Reference**: Rule 10.2

---

### Rule 7: Document Title Capitalization
**Severity**: HIGH
**Pattern**: Specific document titles not in title case
**Auto-fix**: Apply title case → `brief for petitioner` → `Brief for Petitioner`
**Exception**: Generic references ("the brief", "a motion")
**Bluebook Reference**: Rule 10.8.3

---

### Rule 8: Constitutional Element Capitalization
**Severity**: HIGH
**Pattern**: Lowercase constitutional references
**Auto-fix**:
- `article i` → `Article I`
- `fourteenth amendment` → `Fourteenth Amendment`
- `commerce clause` → `Commerce Clause`
**SLR Note**: SLR capitalizes Clause even in generic use
**Bluebook Reference**: Rule 11, SLR 8.1(a)

---

### Rule 9: Book/Article Title Capitalization
**Severity**: MEDIUM
**Pattern**: Improper capitalization in titles
**Auto-fix**: Apply title case rules
**Logic**:
- Capitalize: all nouns, verbs, adjectives, adverbs, first word, last word
- Lowercase: articles, conjunctions, prepositions (≤4 letters) - unless first/last
**Bluebook Reference**: Rule 15.3, Rule 16.3

---

### Rule 10: Parenthetical Opening Capitalization
**Severity**: MEDIUM
**Pattern**: Parenthetical starting with capitalized word (not proper noun)
**Auto-fix**: Lowercase → `(Finding that...)` → `(finding that...)`
**Exception**: Do not lowercase proper nouns
**Bluebook Reference**: Rule 1.5

---

## Detection Algorithm Pseudocode

```
FUNCTION checkCapitalization(text, documentType):
    violations = []

    // Check amendment capitalization
    FOR each match of "\\b[a-z]+ amendment\\b":
        IF match NOT in exception_list:
            violations.add("Amendment not capitalized", match, "Rule 8")

    // Check named acts
    FOR each match of act_names AND lowercase:
        violations.add("Act name not capitalized", match, "Rule 8")

    // Check court references
    FOR each "the court" in context:
        IF context indicates U.S. Supreme Court:
            violations.add("Court should be capitalized", match, "Rule 9")
        ELSE IF context indicates lower court:
            IF "Court" is capitalized:
                violations.add("Court should be lowercase", match, "Rule 9")

    // Check judge titles
    FOR each match of "judge|justice|etc + name":
        IF title is lowercase:
            violations.add("Title should be capitalized", match, "Rule 9")

    // Check party names
    FOR each "v." pattern:
        party_name = text_before_v()
        IF party_name contains first_name OR starts_with_the:
            violations.add("Party name format error", match, "Rule 10.2")

    // Check document titles
    FOR each document_pattern in text:
        IF used_specifically AND not in title_case:
            violations.add("Document title not in title case", match, "Rule 10.8.3")

    // Check parenthetical capitalization
    FOR each "(word" pattern:
        IF word is NOT proper_noun AND is capitalized:
            violations.add("Parenthetical should start with lowercase", match, "Rule 1.5")

    RETURN violations
END FUNCTION
```

---

## Context-Aware Rules

### Rule: Amendment vs. "the amendment"

**CAPITALIZE Amendment:**
- First Amendment protects speech
- The Fourth Amendment requires warrants
- Under the Fourteenth Amendment

**lowercase "the amendment":**
- the amendment provides
- this amendment states
- these amendments were ratified

**Detection Logic:**
```
IF word is "amendment" AND preceded by:
    [ordinal/name]: CAPITALIZE
    ["the", "this", "these"]: lowercase
```

---

### Rule: Court vs. "the court"

**CAPITALIZE "Court" (U.S. Supreme Court):**
- The Supreme Court held
- the Court's opinion
- The Court reasoned

**lowercase "court" (other contexts):**
- the district court
- appellate court
- lower courts
- trial court

**Detection Logic:**
```
IF "court" in text:
    IF referring_to_supreme_court: CAPITALIZE
    ELSE IF generic_lower_court: lowercase
```

---

### Rule: Judge Title Capitalization

**CAPITALIZE Title + Name:**
- Chief Justice Marshall
- Justice Kagan
- Judge Williams
- The President

**lowercase Title Alone (Generic):**
- a judge decided
- the chief justice wrote
- any justice may

**Detection Logic:**
```
IF title_word followed_by_name: CAPITALIZE_TITLE
ELSE IF title_word_alone_or_generic: lowercase_title
```

---

### Rule: Document Title Usage

**CAPITALIZE Specific Document:**
- Brief for Petitioner at 15
- Motion for Summary Judgment
- Plaintiff's Complaint

**lowercase Generic Document:**
- the brief states
- a motion was filed
- this document shows

**Detection Logic:**
```
IF document_term is_specific_reference: CAPITALIZE_ALL_WORDS
ELSE IF document_term is_generic: lowercase
```

---

## Common False Positives and Exceptions

### False Positive 1: Article titles in running text
```
Wrong detection: "the right to counsel" in book title
Correct handling: Check if in citation context or title markup
```

### False Positive 2: Constitutional elements in descriptions
```
Wrong detection: "article about commerce"
Correct handling: Confirm "Article" is constitutional reference, not common noun
```

### False Positive 3: Judge/official titles in descriptions
```
Wrong detection: "this judge is qualified"
Correct handling: "judge" here is common noun, not title - no error
```

### Exception 1: Acronyms
```
Correct: FBI (all caps for acronym)
Correct: NLRB v. Smith (acronym in party name)
Do not flag as error
```

### Exception 2: Titles in quotations
```
Original title may have non-standard capitalization
If quoting exactly, preserve original capitalization
Add [sic] if needed
```

### Exception 3: Foreign language titles
```
Follow capitalization rules of that language
Do not apply English title case
Do provide English translation in brackets
```

---

## Implementation Considerations

### Confidence Levels for Auto-Correction

**HIGH CONFIDENCE (Safe to auto-correct):**
- First Amendment → first amendment
- Civil Rights Act → civil rights act
- Judge Smith → judge smith
- Party name with first name

**MEDIUM CONFIDENCE (Flag but ask for confirmation):**
- Court vs. court determination (depends on context)
- Document title capitalization (check if specific reference)

**LOW CONFIDENCE (Flag and review manually):**
- Parenthetical capitalization (depends on proper noun detection)
- Title case in titles (need to identify first/last words)
- Constitutional element capitalization (need context)

---

## Testing Strategies

### Test Case 1: Amendment Capitalization
```
Input: "The first amendment protects speech."
Expected: Detect lowercase "amendment"
Correction: "The First Amendment protects speech."
```

### Test Case 2: Act Names
```
Input: "The civil rights act requires..."
Expected: Detect lowercase "act"
Correction: "The Civil Rights Act requires..."
```

### Test Case 3: Party Names
```
Input: "John Smith v. Mary Jones"
Expected: Detect first names
Correction: "Smith v. Jones"
```

### Test Case 4: Court References
```
Input: "The court held that..."
Context: U.S. Supreme Court
Expected: Detect lowercase "court"
Correction: "The Court held that..."
```

### Test Case 5: Document Titles
```
Input: "the brief for petitioner filed today"
Expected: Detect specific reference not capitalized
Correction: "the Brief for Petitioner filed today"
```

### Test Case 6: Parenthetical
```
Input: "(Finding that the statute applies)"
Expected: Detect capitalized starting word
Correction: "(finding that the statute applies)"
```

---

## Integration Points

### For Code Linters
- ESLint (with custom rules)
- Pylint (for Python linters)
- StyleLint (for CSS/formatting)

### For Text Editors
- VS Code extensions
- Atom plugins
- Sublime Text packages

### For Document Tools
- Google Docs add-ons
- Word macros
- LaTeX packages

### For CI/CD Pipelines
- Pre-commit hooks
- GitHub Actions
- GitLab CI

---

## References

- Bluebook Rule 8: Capitalization
- Bluebook Rule 9: Titles of Judges, Officials, Terms of Court
- Bluebook Rule 10.2: Case Names
- Bluebook Rule 15.3: Book Titles
- Bluebook Rule 16.3: Article Titles
- SLR Redbook 8.1: Capitalization rules

---

Document Type: Linting Patterns and Rules
Created: 2025-11-23
Format: Markdown with regex patterns
Status: Reference guide for automated capitalization checking
