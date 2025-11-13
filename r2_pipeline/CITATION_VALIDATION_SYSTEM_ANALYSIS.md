# Citation Validation System - Complete Analysis & Improvement Request

## Context

This document describes the complete citation validation system for the Stanford Law Review R2 Pipeline. The system validates legal citations against Bluebook 21st Edition rules and Stanford Law Review custom "Redbook" rules.

**Current Issue**: The AI is incorrectly flagging parenthetical capitalization errors on direct quotes. See example at the end.

---

## System Architecture

### 1. Two-Tier Validation System

**Primary Method: OpenAI Assistants API with File Search**
- Uses GPT-4 with vector search over `Bluebook.json` (contains Redbook + Bluebook rules)
- Has access to:
  - 115 Redbook rules (Stanford Law Review custom rules)
  - 21 Bluebook rules (general legal citation rules)
  - Tables 1, 6, 13 (abbreviations, court names, journals)

**Fallback Method: Regular GPT-4o-mini**
- Used when Assistants API fails after 3 retry attempts
- Does NOT have access to the Bluebook.json file
- Relies on general knowledge of citation formatting

### 2. Deterministic Pre-Checks

Before AI validation, the system runs deterministic checks for:
1. Curly quotes vs straight quotes (Redbook 24.4)
2. Non-breaking spaces (Redbook 24.8)
3. Parenthetical capitalization (Bluebook 10.2.1)

---

## Complete Validation Rules

### A. Redbook Rules (Stanford Law Review - Priority Rules)

**Rule Priority**: Redbook ALWAYS takes precedence over Bluebook when both apply.

#### Redbook 24.4 - Quote Formatting
- Use curly quotes (" ") NOT straight quotes (" ")
- Use curly apostrophes (') NOT straight apostrophes (')

#### Redbook 24.8 - Non-Breaking Spaces
Must use non-breaking space (U+00A0) after:
- Symbols: § ¶ followed by numbers
- List items: (1) followed by text
- Times: 12:30 PM
- Months: Jan. 15
- "v." in case names: Smith v. Jones
- Identifiers: Part I, Figure 3, Table 2, Proposition 8, No. 123, section 4, notes 1-5, art. II, cl. 3, Exhibit A

#### Redbook 10.12 - Docket Numbers
Omit judge's initials from docket numbers:
- **Incorrect**: No. 21-CV-6425 (PKC)
- **Correct**: No. 21-CV-6425

#### Other Redbook Rules
- Case name formatting (italics, abbreviations)
- Reporter formatting
- Parenthetical formatting
- Signal usage (*See*, *see also*, *cf.*, *compare...with*)

---

### B. Bluebook Rules

#### Bluebook 10.2.1 - Parenthetical Capitalization

**Current Implementation**:
```
A parenthetical phrase that is not a direct quote MUST begin with a lowercase letter.

EXCEPTION: If the parenthetical consists of a direct quotation of a full sentence,
the original capitalization inside the quotation marks MUST be preserved.

Correct: (discussing the new rules)
Correct: ("The new rules are complex.")
Incorrect: (Discussing the new rules)
```

**THE PROBLEM**: The AI is NOT respecting the exception for direct quotes!

#### Bluebook Table 1 - Court Abbreviations
Examples:
- D. Ariz. (District of Arizona)
- S.D.N.Y. (Southern District of New York)
- 9th Cir. (Ninth Circuit)

#### Bluebook Table 6 - Case Name Abbreviations
Examples:
- Ass'n (Association)
- Co. (Company)
- Corp. (Corporation)
- Inc. (Incorporated)

**Important**: If a word is NOT abbreviated (full word is used), that is CORRECT even if an abbreviation exists in the tables.

#### Bluebook Table 13 - Journal Abbreviations
Used for periodical citations.

---

## Current Prompt Given to AI

### System Prompt
```
**CORE MANDATE:
1. YOU ARE FORBIDDEN FROM ANSWERING BASED ON YOUR GENERAL KNOWLEDGE. Your ONLY source of truth is the `Bluebook.json` file provided to you via File Search. Every rule you apply MUST come from this file.
2. IF YOU CHECK A RULE AND FIND THAT THE CITATION FOLLOWS IT CORRECTLY, YOU MUST NOT CREATE AN ERROR FOR IT. Only create errors for rules that are violated.

Before answering, you are REQUIRED to use File Search to find the relevant rules in the provided file.**

You are an expert legal citation checker specialized in the Bluebook (21st edition).

**MANDATORY FILE SEARCH REQUIREMENT**:
You have access to a Bluebook.json file via the File Search tool. You MUST use File Search to look up rules before making ANY determination about citation correctness.

**CRITICAL RULE PRIORITY**:
The Bluebook.json contains TWO sections:
- **"redbook"**: Stanford Law Review (SLR) custom rules (115 rules) - **THESE TAKE PRIORITY**
- **"bluebook"**: General Bluebook rules (21 rules)

**ALWAYS check Redbook rules FIRST**. If a Redbook rule applies, use it and cite it. Only use Bluebook rules if no applicable Redbook rule applies.

**BEFORE responding, you MUST:**
1. Use File Search to search the **"redbook"** section first for SLR-specific rules
2. If no Redbook rule applies, search the **"bluebook"** section
3. Search for keywords related to this citation type (e.g., "supra", "case citations", "statutes", "signals", "parentheticals")
4. **SEARCH THE TABLES** in Bluebook.json for abbreviations:
   - Table 1: Court abbreviations (e.g., "9th Cir.", "S.D.N.Y.")
   - Table 6: Case name abbreviations (e.g., "Ass'n", "Co.", "Corp.")
   - Table 13: Journal and periodical abbreviations
   - You MUST verify abbreviations against these tables
5. Look up the specific rule numbers that apply
6. Quote the exact rule text from the file to verify you found it
7. Only then assess whether the citation follows that rule

**DO NOT** rely on your training data alone - you MUST consult the uploaded Bluebook.json file for every validation.
```

### Formatting Instructions
```
## MARKDOWN FORMATTING NOTATION:
The citation text uses the following markdown notation to represent Word document formatting:
- `*text*` = italic text (single asterisks)
- `**text**` = bold text (double asterisks)
- `[SC]text[/SC]` = small caps text
- Regular text = no special formatting

**CRITICAL**: When providing corrected versions, you MUST preserve and use this same markdown notation to indicate formatting. Per Whitepages Rule 10, case names should NOT be italicized - they should be plain text without asterisks. However, other text that should be italicized (like signals, *id.*, *supra*, etc.) should use the `*text*` notation.

**NBSP FORMATTING**: When generating the `corrected_version`, if a non-breaking space is required, you MUST use the literal Unicode character `\u00a0`. Do not use a regular space.
```

### Parenthetical Capitalization Instructions
```
**FORMATTING CHECKS:**
- **Parenthetical Capitalization**: A parenthetical phrase that is not a direct quote MUST begin with a lowercase letter.
  * **CRITICAL EXCEPTION**: If the parenthetical consists of a direct quotation of a full sentence, the original capitalization inside the quotation marks MUST be preserved. Do NOT flag this as an error.
  * **Correct**: `(discussing the new rules)`
  * **Correct**: `("The new rules are complex.")`
  * **Incorrect**: `(Discussing the new rules)`
- **Docket Numbers (Redbook 10.12)**: Omit any judge's initials that appear in a docket number (e.g., `(PKC)`).
- Page range formatting (en-dashes, abbreviation of second number)
```

### Task Instructions
```
## YOUR JOB:
1. **SEARCH the Bluebook reference** for rules applicable to this citation type
2. **CAREFULLY READ** the citation text character by character
3. Check ALL relevant formatting rules against the citation
4. For EACH error found, provide:
   - The specific Bluebook rule number being violated
   - Your confidence (0.0-1.0) that this specific rule is being violated
   - The current incorrect form
   - The correct form according to the rule
   - A clear explanation of what's wrong
   - **CRITICAL for "current" field**: The value for the "current" field MUST be an *exact substring* of the original citation text provided. Do not paraphrase, reformat, or generate new text for the "current" field.
5. **IMPORTANT**: If the citation is CORRECT and follows all Bluebook rules, you MUST:
   - Set "is_correct": true
   - Leave "errors": [] (empty array)
   - Set "corrected_version" to the same as the original
   - Do NOT invent errors that don't exist
6. Always provide the corrected version (return original if no errors exist)
```

### Response Format
```json
{
  "is_correct": boolean,
  "overall_confidence": float (0.0-1.0),
  "errors": [
    {
      "error_type": "specific type",
      "description": "clear explanation",
      "rb_rule": "Redbook rule number if applicable",
      "bluebook_rule": "Bluebook rule number if no Redbook rule applies",
      "rule_text_quote": "direct quote from Bluebook.json proving you searched",
      "rule_source": "either 'redbook' or 'bluebook'",
      "confidence": float (0.0-1.0),
      "current": "exact incorrect portion from citation",
      "correct": "corrected form"
    }
  ],
  "corrected_version": "full corrected citation",
  "notes": "additional observations",
  "file_search_confirmation": "Brief statement confirming you searched Bluebook.json"
}
```

---

## Deterministic Pre-Validation Code

### Parenthetical Capitalization Check (Python)

**Location**: `/Users/ben/app/slrapp/r2_pipeline/src/citation_validator.py` lines 80-108

```python
def _check_parenthetical_capitalization(self, text: str) -> list:
    """Check for parentheticals that should start with lowercase."""
    errors = []

    # Pattern: Find all parentheticals
    parenthetical_pattern = r'\(([^)]+)\)'

    for match in re.finditer(parenthetical_pattern, text):
        content = match.group(1).strip()

        # Skip if empty
        if not content:
            continue

        # Skip if it's a direct quote (starts with quote mark)
        if content.startswith(('"', '"', '"')):
            continue

        # Skip common legal citations that should be capitalized
        if any(content.startswith(x) for x in ['Id.', 'citing', 'quoting', 'alterations in original']):
            continue

        # Skip if it's a year, page reference, or other non-sentence content
        if re.match(r'^\d{4}$|^at \d+|^[A-Z]\.\s*[A-Z]\.', content):
            continue

        # Check if first letter is uppercase (and not part of a proper name pattern)
        if content and content[0].isupper():
            # This might be an error - flag it
            errors.append({
                "error_type": "parenthetical_capitalization_error",
                "description": "Parenthetical phrase should begin with lowercase letter (Bluebook 10.2.1)",
                "rb_rule": None,
                "bluebook_rule": "10.2.1",
                "rule_source": "bluebook",
                "confidence": 0.8,
                "current": f"({content})",
                "correct": f"({content[0].lower()}{content[1:]})"
            })

    return errors
```

**THE PROBLEM**: This code has a heuristic check that skips quotes starting with `"`, `"`, or `"` (curly quotes), BUT it does NOT handle all cases correctly.

---

## Example of Current Failure

### Input Citation
```
Crusey, supra note 21 at 515 ("Unlike a copyright infringement claim under Section 501, a Section 1202 claim requires no prerequisite copyright registration.").
```

### Current Validation Result
```json
{
  "error_type": "parenthetical_capitalization_error",
  "description": "The parenthetical should begin with a lowercase letter since it is not a direct quote.",
  "bluebook_rule": "10.2.1",
  "current": "\"Unlike a copyright infringement claim under Section 501, a Section 1202 claim requires no prerequisite copyright registration.\"",
  "correct": "\"unlike a copyright infringement claim under Section 501, a Section 1202 claim requires no prerequisite copyright registration.\""
}
```

### Why This Is WRONG

**This IS a direct quote** (notice the quotation marks: `("Unlike..."`). According to Bluebook 10.2.1:

> **CRITICAL EXCEPTION**: If the parenthetical consists of a direct quotation of a full sentence, the original capitalization inside the quotation marks MUST be preserved.

The AI should recognize:
1. The parenthetical starts with `(`
2. Immediately followed by opening quote `"`
3. Contains quoted text: `"Unlike..."`
4. Ends with closing quote and period `.")`

This pattern = **DIRECT QUOTE PARENTHETICAL** → Capitalization is CORRECT, do NOT flag as error.

---

## Research Questions for Analysis

### 1. Prompt Engineering
**Question**: How can we improve the prompt to make the AI better understand and apply the direct quote exception for parenthetical capitalization?

**Current approach**:
- We tell the AI about the exception
- We give examples
- We emphasize with "CRITICAL EXCEPTION"

**Issue**: The AI is still flagging direct quotes as errors.

**Possible improvements**:
- More explicit pattern matching instructions?
- Chain-of-thought reasoning requirement?
- Require the AI to explicitly check "Does this parenthetical start with a quote mark?" before applying the capitalization rule?

### 2. Deterministic Pre-Check
**Question**: Should the deterministic parenthetical check be improved or removed entirely?

**Current logic**:
```python
# Skip if it's a direct quote (starts with quote mark)
if content.startswith(('"', '"', '"')):
    continue
```

**Issue**: `content` is the text INSIDE the parentheses, but we need to check if the parenthetical STARTS with `("` not just `(`.

**Example**:
- Citation: `(citing Smith, 123 ("quoted text"))`
- `content` = `citing Smith, 123 ("quoted text")`
- `content.startswith('"')` = False (starts with 'c')
- Gets flagged incorrectly!

**Possible fix**:
```python
# Check if parenthetical content starts with a quote immediately after (
if content.lstrip().startswith(('"', '"', '"')):
    continue  # This is a direct quote, skip capitalization check
```

### 3. AI vs Deterministic Balance
**Question**: Should parenthetical capitalization be:
- A. Checked by deterministic code only (remove from AI prompt)
- B. Checked by AI only (remove deterministic check)
- C. Checked by both (current approach)
- D. Checked by deterministic code first, only pass ambiguous cases to AI

### 4. Pattern Recognition
**Question**: What patterns should definitively identify a "direct quote parenthetical"?

**Candidates**:
1. Starts with `("` (opening paren + quote)
2. Ends with `")` (quote + closing paren)
3. Contains `"....."` (full sentence in quotes)
4. Parenthetical text is >90% wrapped in quotes

**Edge cases to consider**:
- `(citing Smith, 123 ("quoted portion"))` - nested quote
- `(Smith said "X is Y")` - partial quote in explanatory parenthetical
- `("Quote." Additional text)` - quote + explanation

### 5. Error Merging
**Question**: When deterministic checks and AI checks both flag the same issue, how should we handle it?

**Current approach**: Both errors appear in the output (can cause duplicates)

**Options**:
- Deduplicate based on error type
- Deduplicate based on text location
- Give deterministic checks priority
- Give AI checks priority

### 6. Confidence Scoring
**Question**: Should we adjust confidence scores based on:
- Whether the error came from deterministic check (1.0 confidence) vs AI (variable)?
- Whether AI and deterministic agree (higher confidence) vs disagree (lower)?
- Historical accuracy of specific error types?

---

## Request for Improvements

Please analyze this system and provide:

1. **Root Cause Analysis**: Why is the AI incorrectly flagging direct quote parentheticals despite explicit instructions not to?

2. **Prompt Improvements**: Specific changes to the prompt that would improve the AI's understanding and application of the parenthetical capitalization exception.

3. **Code Improvements**: Fixes to the deterministic parenthetical check to correctly identify direct quotes.

4. **Architecture Recommendations**: Should we fundamentally change how we handle this validation?

5. **Pattern Detection**: Provide a robust algorithm/regex for identifying "direct quote parentheticals" that should preserve capitalization.

6. **Testing Strategy**: How can we create test cases that ensure this error doesn't recur?

---

## System Files

### Main Files
- `/Users/ben/app/slrapp/r2_pipeline/src/citation_validator.py` - Validation orchestrator
- `/Users/ben/app/slrapp/r2_pipeline/src/llm_interface.py` - OpenAI API interface
- `/Users/ben/app/slrapp/r2_pipeline/prompts/citation_format.txt` - Full prompt template
- `/Users/ben/app/slrapp/r2_pipeline/data/bluebook/Bluebook.json` - Rules database

### Test Files
- `/Users/ben/app/slrapp/r2_pipeline/test_actual_footnotes.py` - Integration tests
- `/Users/ben/app/slrapp/r2_pipeline/CITATION_PARSER_FINAL.md` - Previous fixes documentation

---

## Success Criteria

A successful solution should:
1. ✅ Correctly identify `("Quoted text.")` as a direct quote → NO error
2. ✅ Correctly flag `(Unquoted text)` starting with capital → Error
3. ✅ Handle nested quotes `(citing Smith ("Quote"))`
4. ✅ Not flag proper nouns `(Justice Scalia dissenting)`
5. ✅ Maintain 100% accuracy on test suite
6. ✅ Work consistently whether using Assistants API or GPT fallback
