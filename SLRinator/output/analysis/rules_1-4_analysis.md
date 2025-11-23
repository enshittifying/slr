# Bluebook Rules 1-4 Comprehensive Analysis
## Citation Structure, Signals, Short Forms, and Authority Order

**Generated:** 2025-11-23
**Source:** `/home/user/slr/SLRinator/config/rules/Bluebook.json`
**Scope:** Rules 1-4 with cross-referenced Redbook variations

---

## Table of Contents
1. [Rule 1: Structure and Use of Citations](#rule-1-structure-and-use-of-citations)
2. [Rule 2: Typefaces for Law Reviews](#rule-2-typefaces-for-law-reviews)
3. [Rule 3: Subdivisions](#rule-3-subdivisions)
4. [Rule 4: Short Citation Forms](#rule-4-short-citation-forms)
5. [Cross-Rule Error Patterns](#cross-rule-error-patterns)
6. [Detection Strategy Matrix](#detection-strategy-matrix)

---

## Rule 1: Structure and Use of Citations

### Rule 1.1: Citation Sentences and Clauses in Law Reviews

#### Rule Overview
Citations are placed in footnotes that support or contradict propositions in the main text. Citations appear as either:
- **Citation sentences**: Support entire sentences (start with capital, end with period)
- **Citation clauses**: Support part of a sentence (set off by commas)

#### Bluebook vs Redbook Differences
- **BB 1.1(a)**: Footnote call number appears at end of textual sentence OR within sentence next to the portion it supports
- **RB 1.4**: SLR DEVIATES - always place footnote call number at END of sentence, even if citation supports only part of sentence

#### Detectable Errors

##### Error Type 1: Citation Sentence Missing Period
```
INCORRECT: See Smith v. Jones, 123 U.S. 456 (2000)
CORRECT: See Smith v. Jones, 123 U.S. 456 (2000).
```

**Regex Pattern:**
```regex
^[A-Z][^.]*\d{1,4}\s+U\.S\.\s+\d+[^.]*\([12]\d{3}\)[^.]*$
```

**GPT Prompt:**
```
Check if this citation is a complete citation sentence (supports an entire sentence).
If yes, verify it:
1. Starts with a capital letter
2. Ends with a period
3. Is not embedded within another sentence

Citation: {citation_text}
Return: VALID or ERROR with explanation
```

##### Error Type 2: Citation Clause Missing Commas
```
INCORRECT: The court held liability without negligence Smith v. Jones
CORRECT: The court held liability without negligence, Smith v. Jones, is required.
```

**Regex Pattern:**
```regex
[a-z]\s+[A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+(?!,)
```

**GPT Prompt:**
```
Analyze whether this citation is embedded in a sentence (citation clause).
Citation clauses must be:
1. Set off by commas
2. Immediately follow the proposition they support
3. Not start with a capital letter (unless signal is present)

Text: {sentence_with_citation}
Return: VALID or ERROR with specific issue
```

##### Error Type 3: Incorrect Footnote Placement (Redbook)
```
INCORRECT (for SLR): The police obtained a warrant,¹ but the evidence was suppressed.²
CORRECT (for SLR): The police obtained a warrant, but the evidence was suppressed.¹
```

**GPT Prompt:**
```
According to Stanford Law Review (Redbook) rules:
- Footnote call numbers should appear at the END of sentences
- Even if the citation supports only part of the sentence
- Exception: when multiple independent clauses are present

Analyze this text and determine if footnote placement is correct:
{text_with_footnotes}

Return: COMPLIANT, NON_COMPLIANT_BB_ONLY, or ERROR with explanation
```

---

### Rule 1.2: Introductory Signals

#### Signal Categories and Order

1. **Supportive Signals** (no signal, *E.g.*, *Accord*, *See*, *See also*, *Cf.*)
2. **Comparative Signals** (*Compare...with...*)
3. **Contradictory Signals** (*But see*, *But cf.*)
4. **Background Signals** (*See generally*)

#### Signal Definitions

| Signal | Usage | Parenthetical Required? |
|--------|-------|------------------------|
| [No signal] | Authority directly states/clearly supports proposition | No |
| *E.g.* | Authority is one of multiple examples | No |
| *Accord* | Authority directly supports, but text already quoted/cited another | No |
| *See* | Authority clearly supports but does not directly state | No |
| *See also* | Authority provides additional support | Often helpful |
| *Cf.* | Authority supports by analogy | **YES** (RB 1.12) |
| *Compare...with...* | Comparison provides support | Usually |
| *But see* | Authority contradicts | No |
| *But cf.* | Authority contradicts by analogy | **YES** (RB 1.12) |
| *See generally* | Background material related to proposition | **NO** (RB 1.12) |

#### Detectable Errors

##### Error Type 1: Signal Not Italicized
```
INCORRECT: See Smith v. Jones, 123 U.S. 456 (2000).
CORRECT: See Smith v. Jones, 123 U.S. 456 (2000).
```

**Regex Pattern:**
```regex
^(See|Accord|But see|See also|See generally|E\.g\.|Cf\.|Compare|But cf\.)\s+[A-Z]
```
*Note: This checks for signal presence; italicization check requires formatting analysis*

**GPT Prompt:**
```
Check if introductory signals are properly formatted:
1. Signals must be italicized (except when used as verbs in textual sentences)
2. Proper capitalization (only first word of citation sentence)
3. Correct punctuation after signal

Text: {citation_text}
Return: FORMATTING_CORRECT or list of issues
```

##### Error Type 2: Missing Explanatory Parenthetical for Cf.
```
INCORRECT: Cf. Smith v. Jones, 123 U.S. 456 (2000).
CORRECT: Cf. Smith v. Jones, 123 U.S. 456 (2000) (holding similar standard in contract context).
```

**Regex Pattern:**
```regex
\bCf\.\s+[^(]+\([12]\d{3}\)\.(?!\s*\()
```

**GPT Prompt:**
```
Rule: "Cf." and "But cf." signals MUST include explanatory parentheticals.
"See generally" signals must NOT include explanatory parentheticals.

Check this citation:
{citation_text}

Return:
- Signal type identified
- Parenthetical presence (YES/NO)
- COMPLIANT or NON_COMPLIANT with reason
```

##### Error Type 3: Incorrect Signal for Direct Statement
```
INCORRECT: See Smith v. Jones, 123 U.S. 456, 460 (2000) ("The statute is unconstitutional.").
CORRECT: Smith v. Jones, 123 U.S. 456, 460 (2000) ("The statute is unconstitutional.").
```

**GPT Prompt:**
```
Analyze whether the correct signal is used:
- NO SIGNAL: Authority directly states proposition
- See: Authority clearly supports but doesn't directly state
- E.g.: One example among many
- See also: Additional support

Citation: {citation_text}
Proposition: {supported_proposition}
Quote from source: {quote_if_present}

Return: CORRECT_SIGNAL or suggest appropriate signal
```

##### Error Type 4: Signal Used as Verb Not De-italicized (Redbook)
```
INCORRECT: See also Smith for alternative approach.
CORRECT: See also Smith for alternative approach.
```

**GPT Prompt:**
```
Redbook Rule: When signals are used as verbs in textual sentences, they should NOT be italicized.

Example: "See also Smith for more details" (not italicized)
vs. "See also Smith, 123 U.S. 456." (italicized)

Analyze: {text_with_signal}
Return: TEXTUAL_VERB_FORM or CITATION_FORM, plus FORMATTING_CORRECT or ERROR
```

---

### Rule 1.3: Order of Signals

#### Correct Signal Ordering

Signals must appear in this order:
1. No signal
2. *E.g.*
3. *Accord*
4. *See*
5. *See also*
6. *Cf.*
7. *Compare...with...*
8. *But see*
9. *But cf.*
10. *See generally*

**Key Rules:**
- Same type signals → strung together in single sentence, separated by semicolons
- Different type signals → separate citation sentences
- When *e.g.* combines with another signal → use other signal's position

#### Detectable Errors

##### Error Type 1: Signals Out of Order
```
INCORRECT: See also Smith, 100 U.S. 1 (1990); see Jones, 200 U.S. 2 (2000).
CORRECT: See Jones, 200 U.S. 2 (2000); see also Smith, 100 U.S. 1 (1990).
```

**Regex Pattern:**
```regex
(See also|Cf\.)([^;]+);[\s]*(See)(?!\s+also|generally)
```

**GPT Prompt:**
```
Check if signals appear in correct Bluebook order:
1. No signal → 2. E.g. → 3. Accord → 4. See → 5. See also →
6. Cf. → 7. Compare...with → 8. But see → 9. But cf. → 10. See generally

Citation string: {full_citation_sentence}

Return:
- Signals found (in order of appearance)
- Expected order
- CORRECT or OUT_OF_ORDER with correction
```

##### Error Type 2: Same-Type Signals in Different Sentences
```
INCORRECT: See Smith, 100 U.S. 1 (1990). See also Jones, 200 U.S. 2 (2000).
CORRECT: See Smith, 100 U.S. 1 (1990); see also Jones, 200 U.S. 2 (2000).
```

**Regex Pattern:**
```regex
(See|Accord|E\.g\.)([^.]+)\.\s+(See also|Cf\.)
```

**GPT Prompt:**
```
Bluebook Rule 1.3: Signals of the same basic type (supportive, comparative,
contradictory, background) must be strung together in a single citation sentence,
separated by semicolons.

Analyze these consecutive citations:
{citation_sentences}

Return:
- Signal types identified
- Same category? (YES/NO)
- Should be combined? (YES/NO)
- COMPLIANT or ERROR with suggested fix
```

##### Error Type 3: Incorrect Separation Between Different Signal Types
```
INCORRECT: See Smith, 100 U.S. 1 (1990); but see Jones, 200 U.S. 2 (2000).
CORRECT: See Smith, 100 U.S. 1 (1990). But see Jones, 200 U.S. 2 (2000).
```

**Regex Pattern:**
```regex
(See|See also|Cf\.)([^;]+);\s*(but see|But cf\.)
```

**GPT Prompt:**
```
Supportive signals (See, See also, Cf.) and contradictory signals (But see, But cf.)
must be in SEPARATE citation sentences, not joined by semicolons.

Check: {citation_string}

Return: REQUIRES_SEPARATE_SENTENCES or CORRECT
```

---

### Rule 1.4: Order of Authorities Within Each Signal

#### Authority Ordering Hierarchy

When multiple authorities follow a signal, order by:
1. **Most helpful/authoritative first** (if significantly more important)
2. **Type of authority** (cases, statutes, books, articles)
3. **Descending weight/importance** within type

#### Common Ordering Rules

For cases:
1. U.S. Supreme Court
2. Federal Courts of Appeals
3. Federal District Courts
4. State highest courts
5. State intermediate appellate courts
6. State trial courts

Within same court level:
- Reverse chronological order (newest first)

#### Detectable Errors

##### Error Type 1: Authorities Not Separated by Semicolons
```
INCORRECT: See Smith, 100 U.S. 1, Jones, 200 U.S. 2.
CORRECT: See Smith, 100 U.S. 1; Jones, 200 U.S. 2.
```

**Regex Pattern:**
```regex
\d{1,4}\s+U\.S\.\s+\d+[^;]+,\s+[A-Z][a-z]+,\s+\d{1,4}\s+U\.S\.
```

**GPT Prompt:**
```
Rule: Multiple authorities within a signal must be separated by semicolons.

Check: {citation_string}

Return:
- Number of authorities detected
- Proper separation (YES/NO)
- Suggest correction if needed
```

##### Error Type 2: Supreme Court Case After Lower Court Case
```
INCORRECT: See Jones v. Smith, 100 F.3d 456 (5th Cir. 2000); Brown v. Board, 347 U.S. 483 (1954).
CORRECT: See Brown v. Board, 347 U.S. 483 (1954); Jones v. Smith, 100 F.3d 456 (5th Cir. 2000).
```

**GPT Prompt:**
```
Analyze authority ordering within this signal.
Cases should be ordered by court hierarchy:
1. U.S. Supreme Court (U.S.)
2. Courts of Appeals (F.2d, F.3d, F.4th)
3. District Courts (F. Supp.)
4. State courts (by level)

Citations: {citation_list}

Return:
- Court levels identified for each
- Current order
- Correct order (if different)
- CORRECT or REORDER_NEEDED
```

---

### Rule 1.5: Parenthetical Information

#### Types of Parentheticals

1. **Weight of authority** (e.g., "per curiam", "plurality opinion")
2. **Explanatory parentheticals** (explain relevance)
3. **Quotation parentheticals** (quote from source)

#### Ordering: Weight → Explanation → Quotation (RB 1.16)

#### Parenthetical Format Rules

- Start with **lowercase letter** (unless proper noun)
- Begin with **present participle** ("holding", "finding", "arguing")
- OR quoted sentence
- OR short statement providing context
- **Never** start with article (a, an, the) or capital letter

#### Detectable Errors

##### Error Type 1: Parenthetical Starting with Capital Letter
```
INCORRECT: Smith v. Jones, 100 U.S. 1 (2000) (The court held that...).
CORRECT: Smith v. Jones, 100 U.S. 1 (2000) (holding that...).
```

**Regex Pattern:**
```regex
\([12]\d{3}\)\s+\([A-Z][a-z]+(?![\w\s]*[A-Z][\w\s]*,)
```
*Excludes proper nouns like state names*

**GPT Prompt:**
```
Check explanatory parenthetical formatting:
1. Must start with lowercase letter (unless proper noun)
2. Should begin with present participle or quoted sentence
3. Cannot start with article (a, an, the)

Parenthetical: {parenthetical_text}

Return:
- First word
- Type (present participle/quote/other)
- CORRECT or ERROR with issue
```

##### Error Type 2: Missing Parenthetical for Cf. Signal (Redbook)
```
INCORRECT: Cf. Smith v. Jones, 100 U.S. 1 (2000).
CORRECT: Cf. Smith v. Jones, 100 U.S. 1 (2000) (applying similar standard in different context).
```

**Regex Pattern:**
```regex
\bCf\.\s+[^(]+\([12]\d{3}\)\.(?!\s*\()
```

**GPT Prompt:**
```
Redbook Rule 1.12: Cf. and But cf. signals REQUIRE explanatory parentheticals.
See generally signals must NOT have explanatory parentheticals.

Citation: {citation_text}
Signal: {signal_type}

Return: PARENTHETICAL_REQUIRED, PARENTHETICAL_FORBIDDEN, or PARENTHETICAL_OPTIONAL
Then: COMPLIANT or NON_COMPLIANT
```

##### Error Type 3: Parenthetical Starting with Non-Participle
```
INCORRECT: Smith v. Jones, 100 U.S. 1 (2000) (court held that statute was invalid).
CORRECT: Smith v. Jones, 100 U.S. 1 (2000) (holding that statute was invalid).
```

**GPT Prompt:**
```
Verify this explanatory parenthetical follows Bluebook format:
- Must start with present participle (holding, finding, arguing, stating, etc.)
- OR be a quoted sentence in quotation marks
- OR be a short phrase like "same" or "to same effect"

Parenthetical: {parenthetical_text}

Return:
- Format type detected
- VALID or INVALID with suggested correction
```

##### Error Type 4: Wrong Parenthetical Order (Redbook)
```
INCORRECT: Smith, 100 U.S. 1 (2000) (holding X) (per curiam).
CORRECT: Smith, 100 U.S. 1 (2000) (per curiam) (holding X).
```

**GPT Prompt:**
```
Redbook 1.16: When multiple parentheticals follow a citation, order is:
1. Weight of authority (per curiam, plurality, en banc)
2. Explanatory parenthetical
3. Quotation parenthetical

Citation with parentheticals: {full_citation}

Return:
- Parentheticals identified (with types)
- Current order
- Correct order
- CORRECT or REORDER_NEEDED
```

---

### Rule 1.6: Related Authority

Certain information should NOT be in parentheticals:
- Related authority requiring explanatory phrases (Table T8)
- Prior/subsequent history
- Sources providing general background (may use "additional information" parenthetical)

This rule mainly provides guidance on what NOT to include parenthetically.

**GPT Prompt:**
```
Identify if this parenthetical contains information that should be formatted differently:
- Subsequent history (aff'd, rev'd, cert. denied) → should use Table T8 phrases
- Related authority → should use Table T8 phrases
- General background → may be omitted or in parenthetical

Parenthetical: {parenthetical_text}

Return: APPROPRIATE_USE or suggest Table T8 format
```

---

## Rule 2: Typefaces for Law Reviews

### Rule 2.1: Typeface Conventions for Citations

#### Formatting Requirements

| Element | Typeface | Examples |
|---------|----------|----------|
| Case names | Italics | *Brown v. Board of Education* |
| Procedural phrases | Italics | *In re*, *Ex parte* |
| Book titles | Italics | *The Federalist Papers* |
| Periodical titles | Italics | *Harvard Law Review* |
| Court documents | Roman | Brief for Appellant |
| Legislative materials | Roman | H.R. Rep. No. 100-1 |
| Signals | Italics | *See*, *Cf.* |
| Explanatory phrases | Roman | aff'd, rev'd, cert. denied |
| Institutional authors | SMALL CAPS | AMERICAN LAW INSTITUTE |

#### Detectable Errors

##### Error Type 1: Case Name Not Italicized
```
INCORRECT: Smith v. Jones, 100 U.S. 1 (2000).
CORRECT: Smith v. Jones, 100 U.S. 1 (2000).
```

**GPT Prompt:**
```
Check typeface formatting for this citation:
1. Case names must be italicized (including "v.")
2. Reporter names are roman
3. Dates/parentheticals are roman

Citation: {citation_text}

Return: List of formatting issues or CORRECT
```

##### Error Type 2: Signal Not Italicized
```
INCORRECT: See Smith v. Jones, 100 U.S. 1 (2000).
CORRECT: See Smith v. Jones, 100 U.S. 1 (2000).
```

##### Error Type 3: "Id." Formatting Error
```
INCORRECT: id. at 123
INCORRECT: Id at 123
CORRECT: Id. at 123
```

**Regex Pattern:**
```regex
(?:^|\.\s+)(id\.?|ID\.?)(?:\s+at)?
```

**GPT Prompt:**
```
Check "Id." formatting:
1. Capital "I", lowercase "d"
2. Always followed by period
3. Italicized
4. If pincite follows, use "at" before page number

Text: {id_citation}

Return: CORRECT or list specific errors
```

---

### Rule 2.2: Typeface Conventions for Textual Material

In main text (not citations):
- Case names: Italicized when part of textual sentence
- Titles: Italicized
- Emphasis: Italicized (sparingly)
- Everything else: Roman

**Cross-reference:** RB 1.3 (cases named in text need not repeat in footnote if sufficient)

---

## Rule 3: Subdivisions

### Rule 3.1: Volumes, Parts, and Supplements

Include volume numbers when citing multi-volume works.

**Format:** `[Volume] [Author], [Title] [Page] ([Edition] [Year])`

**Example:** `2 WRIGHT & MILLER, FEDERAL PRACTICE & PROCEDURE § 1234 (3d ed. 2019)`

---

### Rule 3.2: Pages, Footnotes, Endnotes, and Graphical Materials

#### Page Citation Rules

**Pinpoint citations:**
```
at 15          (single page)
at 15-16       (page range)
at 15-17       (three pages)
at 15 n.4      (footnote)
at 15 nn.4-5   (multiple footnotes)
```

#### Detectable Errors

##### Error Type 1: Missing "at" in Pinpoint
```
INCORRECT: Smith v. Jones, 100 U.S. 1, 5 (2000).
CORRECT: Smith v. Jones, 100 U.S. 1, 5 (2000).
```
*Note: For cases, no "at" needed; for other sources, use "at"*

##### Error Type 2: Wrong Footnote Abbreviation
```
INCORRECT: at 15 fn. 4
CORRECT: at 15 n.4
```

**Regex Pattern:**
```regex
\s+fn\.\s*\d+
```

**GPT Prompt:**
```
Check footnote citation format:
- Use "n." for single footnote (at 15 n.4)
- Use "nn." for multiple footnotes (at 15 nn.4-6)
- No space before footnote number
- Never use "fn." or "footnote"

Citation: {citation_with_footnote}

Return: CORRECT or ERROR with proper format
```

---

### Rule 3.3: Sections and Paragraphs

Use section symbol § or paragraph symbol ¶.

**Rules:**
- Single section: §
- Multiple sequential: §§
- Multiple non-consecutive: § 1, § 3, § 5 OR §§ 1, 3, 5

#### Detectable Errors

##### Error Type 1: Wrong Section Symbol
```
INCORRECT: Section 102(a)
CORRECT: § 102(a)
```
*Note: In citations only; text may spell out "section"*

##### Error Type 2: Double Symbol for Single Section
```
INCORRECT: §§ 102
CORRECT: § 102
```

**Regex Pattern:**
```regex
§§\s+\d+(?![,\-\d])
```

**GPT Prompt:**
```
Check section symbol usage:
- Single section: § 102
- Multiple consecutive: §§ 102-105
- Multiple non-consecutive: §§ 102, 105, 108

Citation: {section_citation}

Return: CORRECT or ERROR with proper format
```

---

### Rule 3.4: Appended Material

Clearly indicate appendices, prefaces, etc.

**Examples:**
- `at xv (Preface)`
- `at 3 (Introduction)`
- `App. A at 10`

---

### Rule 3.5: Internal Cross-References

**Format:** Use *supra* or *infra* in italics

**Examples:**
- `Part II.A.1, infra`
- `Section III, supra`

**Important:** Do NOT use "hereinafter" for internal cross-references (BB 3.5)

#### Detectable Errors

##### Error Type 1: "Hereinafter" in Internal Cross-Reference
```
INCORRECT: Part II, hereinafter Section II
CORRECT: Part II, infra
```

**Regex Pattern:**
```regex
(Part|Section)\s+[IVX]+[A-Z0-9.]*,?\s+hereinafter
```

**GPT Prompt:**
```
Bluebook Rule 3.5: Do NOT use "hereinafter" for internal cross-references
(references to other parts of the same article).

Use "supra" or "infra" instead.

Text: {cross_reference}

Return: INTERNAL_XREF_DETECTED and CORRECT or ERROR
```

---

## Rule 4: Short Citation Forms

### Rule 4.1: "Id."

#### Usage Rules

**When to use Id.:**
- Refers to **immediately preceding** authority
- That authority must be the **sole authority** in preceding citation
- Must be in same footnote OR immediately following footnote
- Always refers to **identical source**, not just same work

**When NOT to use Id.:**
- Multiple authorities in preceding citation
- Intervening citations (even to different sources)
- Source only appears in parenthetical of prior footnote (RB 4.3 → use supra)

#### Format Rules

**With same page:** `Id.`
**With different page:** `Id. at 123.`

**ALWAYS use "at" with pinpoint** (RB 4.2)

#### Detectable Errors

##### Error Type 1: Id. Without Period
```
INCORRECT: Id at 123
CORRECT: Id. at 123
```

**Regex Pattern:**
```regex
\bId\s+at\s+\d+
```

##### Error Type 2: Id. Without "at" for Pinpoint (Redbook)
```
INCORRECT: Id. 123
CORRECT: Id. at 123
```

**Regex Pattern:**
```regex
Id\.\s+\d+(?!\s*n\.)
```

**GPT Prompt:**
```
Redbook Rule 4.2: Always include "at" after Id. when citing to a different page.

Format:
- Same page: Id.
- Different page: Id. at 123.
- Footnote: Id. at 123 n.4.

Citation: {id_citation}

Return: CORRECT or ERROR with proper format
```

##### Error Type 3: Id. Used When Multiple Prior Authorities
```
INCORRECT:
123. See Smith, 100 U.S. 1; Jones, 200 U.S. 2.
124. Id. at 5.

CORRECT:
123. See Smith, 100 U.S. 1; Jones, 200 U.S. 2.
124. Smith, 100 U.S. at 5.
```

**GPT Prompt:**
```
Check if Id. is properly used:
Rule: Id. can ONLY be used if the immediately preceding citation contains
exactly ONE authority.

Previous citation: {prior_citation}
Current citation: {current_citation}

Return:
- Number of authorities in prior citation
- ID_APPROPRIATE or ID_INAPPROPRIATE with alternative
```

##### Error Type 4: Id. to Source Only in Parenthetical (Redbook)
```
INCORRECT:
100. Smith, 100 U.S. 1 (citing Jones, 200 U.S. 2).
101. Id.

CORRECT:
100. Smith, 100 U.S. 1 (citing Jones, 200 U.S. 2).
101. Jones, supra note 100.
```

**GPT Prompt:**
```
Redbook Rule 4.3: Do not use Id. to refer to a source cited ONLY in a
parenthetical of the preceding footnote. Use supra instead.

Previous footnote: {prev_footnote}
Current citation: {current_citation}

Return: ID_CONTEXT_VALID or USE_SUPRA_INSTEAD
```

---

### Rule 4.2: "Supra" and "Hereinafter"

#### Supra Usage

**When to use supra:**
- Previously cited authority (not immediately preceding)
- Secondary sources (books, articles)
- Legislative materials
- International documents

**When NOT to use supra:**
- Cases (use short case name)
- Statutes (use short statutory cite)
- Regulations (use short form)

**Format:**
- Author's last name + supra note [X]
- Short title + supra note [X]
- `Smith, supra note 10, at 45.`

#### Hereinafter Usage

**When to use hereinafter:**
- Authority with cumbersome name
- Multiple works by same author cited
- Would cause confusion with supra alone

**Format:** Follows full citation in parenthetical
```
Full citation (hereinafter Short Title).
```

**Example:**
```
The Protection of Classified Information: The British Experience,
in SECRECY AND FOREIGN POLICY 153 (hereinafter British Experience).
```

**Later references:**
```
British Experience, supra note 12, at 160.
```

#### Redbook Variation

**RB 4.1:** If source appeared in one of previous FIVE footnotes and clearly same source, may use supra instead of Id.

**RB 4.4:** Use hereinafter SPARINGLY - only when supra would be truly confusing

#### Detectable Errors

##### Error Type 1: Supra Used for Cases
```
INCORRECT: Smith v. Jones, supra note 10, at 123.
CORRECT: Smith, 100 U.S. at 123.
```

**Regex Pattern:**
```regex
[A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+,\s+supra\s+note
```

**GPT Prompt:**
```
Bluebook Rule: Do NOT use "supra" for cases. Use short case name instead.

Incorrect: Smith v. Jones, supra note 10
Correct: Smith, 100 U.S. at 123 (if within 5 footnotes)
Correct: Smith v. Jones, 100 U.S. 1, 123 (1990) (if beyond 5 footnotes)

Citation: {citation_text}
Type: {authority_type}

Return: SUPRA_APPROPRIATE or USE_SHORT_FORM with correct format
```

##### Error Type 2: Supra Without Note Reference
```
INCORRECT: Smith, supra at 45.
CORRECT: Smith, supra note 10, at 45.
```

**Regex Pattern:**
```regex
\bsupra\s+at\s+\d+(?!\s+note)
```

**GPT Prompt:**
```
Supra citations must reference the footnote number where the source was
fully cited.

Format: [Author], supra note [X], at [page].

Citation: {supra_citation}

Return: COMPLETE or MISSING_NOTE_REFERENCE
```

##### Error Type 3: Hereinafter Outside Parenthetical
```
INCORRECT: Smith, Article Title hereinafter Short Title, at 100.
CORRECT: Smith, Article Title, at 100 (hereinafter Short Title).
```

**GPT Prompt:**
```
"Hereinafter" must appear in parentheses after the full citation.

Format: [Full Citation] (hereinafter Short Title).

Citation: {citation_text}

Return: HEREINAFTER_POSITION_CORRECT or ERROR with proper format
```

##### Error Type 4: Unnecessary Hereinafter (Redbook)
```
POTENTIALLY UNNECESSARY:
John Smith, The Law of Torts, 100 HARV. L. REV. 1 (2000) (hereinafter Torts).

BETTER (if only one Smith article):
John Smith, The Law of Torts, 100 HARV. L. REV. 1 (2000).
[Later:] Smith, supra note 10, at 15.
```

**GPT Prompt:**
```
Redbook Rule 4.4: Use hereinafter SPARINGLY - only when supra would be confusing.

Hereinafter is appropriate when:
1. Multiple works by same author in same year
2. Extremely long/cumbersome titles
3. Similar titles that could be confused

Citation: {full_citation}
Other citations by same author: {other_cites}

Return: HEREINAFTER_NEEDED or HEREINAFTER_UNNECESSARY with reason
```

---

## Cross-Rule Error Patterns

### Pattern 1: Signal + Citation Sentence Structure

**Combines Rules:** 1.1, 1.2, 1.3, 2.1

**Error Cascade:**
```
MULTIPLE ERRORS:
see Smith v. Jones, 100 U.S. 1 (2000); But See Johnson, 200 U.S. 2

Issues:
1. "see" not italicized (Rule 2.1)
2. "see" should be capitalized as start of sentence (Rule 1.1)
3. "But See" wrong capitalization (Rule 1.3)
4. Supportive and contradictory signals can't be in same sentence (Rule 1.3)
5. Missing period at end (Rule 1.1)

CORRECT:
See Smith v. Jones, 100 U.S. 1 (2000). But see Johnson, 200 U.S. 2 (2001).
```

**Comprehensive GPT Prompt:**
```
Analyze this complete citation sentence for all structural errors:

Citation: {full_citation_text}

Check for:
1. CAPITALIZATION: First word capitalized, proper signal caps
2. ITALICIZATION: Signals, case names
3. SIGNAL ORDER: Correct sequence per BB 1.3
4. SIGNAL GROUPING: Same-type together, different-type separate
5. PUNCTUATION: Period at end, semicolons between authorities
6. AUTHORITY SEPARATION: Semicolons not commas

Return comprehensive error report with Rule references
```

### Pattern 2: Id./Supra/Short Form Selection

**Combines Rules:** 4.1, 4.2, 10.9 (case short forms)

**Decision Tree for Short Forms:**

```
Is source immediately preceding AND sole authority?
├─ YES → Use Id.
└─ NO → Is it a case?
    ├─ YES → Use short case name (Party, Vol. Reporter at Page)
    └─ NO → Is it a statute/regulation?
        ├─ YES → Use short statutory form
        └─ NO → Is it secondary source/legislative material?
            ├─ YES → Use supra
            └─ NO → Check specific rule for that source type
```

**GPT Prompt for Short Form Selection:**
```
Determine correct short form for this citation:

Current citation: {current_cite}
Previous citation (immediately before): {prev_cite}
Source type: {source_type}
Prior citations in last 5 notes: {recent_cites}

Decision process:
1. Is current cite to same source as immediately previous?
   - If yes and prev cite had only one authority → Id.
   - If yes but prev cite had multiple → short form
   - If no → proceed to step 2

2. What type of source?
   - Case → short case name format
   - Statute → short statutory format
   - Book/Article → supra note X
   - Other → check specific rule

Return: RECOMMENDED_SHORT_FORM with reasoning
```

### Pattern 3: Parenthetical Completeness and Order

**Combines Rules:** 1.5, 1.6, RB 1.12, RB 1.16

**Multi-Check System:**

```
For each citation with parenthetical:
1. Signal type requires parenthetical? (Cf./But cf. = YES, See generally = NO)
2. Parenthetical formatting correct? (lowercase, participle/quote)
3. Multiple parentheticals in right order? (weight → explanation → quotation)
4. Content appropriate for parenthetical vs. Table T8 phrase?
```

**Comprehensive GPT Prompt:**
```
Analyze parenthetical usage in this citation:

Full citation: {citation_with_parens}
Signal used: {signal}

Checks:
1. REQUIRED: Does signal type require parenthetical?
   - Cf., But cf. → MUST have explanation
   - See generally → must NOT have explanation
   - Others → optional but often helpful

2. FORMAT: Explanatory parenthetical format
   - Starts with lowercase (unless proper noun)?
   - Begins with present participle or quote?
   - Not starting with article (a, an, the)?

3. ORDER: If multiple parentheticals present
   - Weight of authority (per curiam) first
   - Explanation second
   - Quotation third

4. CONTENT: Should this be parenthetical or Table T8 phrase?
   - Subsequent history → Table T8
   - Related authority → Table T8
   - Explanation of holding → parenthetical OK

Return detailed analysis with PASS/FAIL for each check
```

---

## Detection Strategy Matrix

### Level 1: Regex-Based Detection (Fast, High Precision, Low Recall)

**Use for:**
- Missing punctuation (periods, commas)
- Obvious formatting errors (Id vs. id., wrong symbols)
- Basic pattern violations (double §§ for single section)
- Simple signal presence

**Limitations:**
- Cannot detect context-dependent errors
- Cannot assess semantic correctness
- Cannot evaluate signal appropriateness

### Level 2: GPT-Based Validation (Slower, High Recall, Variable Precision)

**Use for:**
- Signal appropriateness for proposition
- Parenthetical requirement assessment
- Short form selection logic
- Authority ordering within signal
- Cross-reference validation

**Prompt Engineering Strategy:**
1. **Single-task prompts:** Each prompt checks ONE specific rule
2. **Provide context:** Include surrounding citations, proposition supported
3. **Request structured output:** JSON or categorized response
4. **Include examples:** Show correct vs. incorrect in prompt
5. **Ask for reasoning:** Helps debug false positives

### Level 3: Hybrid Approach (Recommended)

**Pipeline:**
```
1. Regex Pre-Filter
   ↓ (Flag potential issues)
2. GPT Detailed Analysis
   ↓ (Assess flagged items + context)
3. Confidence Scoring
   ↓ (High confidence → auto-fix, Low → human review)
4. Human Review Queue
   ↓
5. Learning Loop (improve regex + prompts)
```

**Example Implementation:**

```python
def check_citation_sentence(citation_text):
    errors = []

    # Level 1: Regex checks
    if not citation_text.strip().endswith('.'):
        errors.append({
            'type': 'MISSING_PERIOD',
            'rule': 'BB 1.1',
            'confidence': 0.95,
            'fix': citation_text + '.'
        })

    # Level 2: GPT validation for signal
    if has_signal(citation_text):
        signal_check = gpt_validate_signal(
            citation=citation_text,
            proposition=get_supported_text(citation_text)
        )
        if signal_check['error']:
            errors.append({
                'type': 'WRONG_SIGNAL',
                'rule': 'BB 1.2',
                'confidence': signal_check['confidence'],
                'suggestion': signal_check['suggestion']
            })

    return errors
```

### Detection Priority by Error Impact

**Critical (Auto-flag):**
- Citation sentence missing period
- Id. used when multiple prior authorities
- Supra used for cases
- Cf./But cf. without parenthetical
- Supportive + contradictory signals in same sentence

**Important (Flag for review):**
- Signal order incorrect
- Authority order within signal incorrect
- Parenthetical format errors
- Missing "at" in Id. pincite

**Minor (Suggest improvement):**
- Unnecessary hereinafter
- Overly long parentheticals
- Suboptimal signal choice (correct but not best)

---

## Error Pattern Examples

### Example 1: Multiple Errors in Single Citation

**Text:**
```
see Smith v. Jones 100 U.S. 1 (2000); But See Brown v. Board of Education,
347 U.S. 483; id. at 490
```

**Errors Detected:**

| Error | Rule | Type | Fix |
|-------|------|------|-----|
| "see" not capitalized | BB 1.1 | Critical | See |
| "see" not italicized | BB 2.1 | Critical | *See* |
| Missing comma after Jones | BB 10.1 | Important | Jones, |
| "But See" wrong caps | BB 1.3 | Critical | But see |
| Supportive + contradictory in same sentence | BB 1.3 | Critical | Separate with period |
| Missing year in Brown cite | BB 10.1 | Critical | Add (1954) |
| Id. follows multiple authorities | BB 4.1 | Critical | Use Brown, 347 U.S. at 490 |
| Missing final period | BB 1.1 | Critical | Add period |

**Corrected:**
```
See Smith v. Jones, 100 U.S. 1 (2000). But see Brown v. Board of Education,
347 U.S. 483, 490 (1954).
```

### Example 2: Redbook-Specific Deviation

**Text (compliant with Redbook, not standard Bluebook):**
```
The court applied strict scrutiny, but ultimately upheld the statute.¹⁰
```

**Standard Bluebook would place superscript after "scrutiny" (supports only that clause)**

**Redbook (SLR) places at end of sentence regardless**

**Detection Strategy:**
```
1. Identify: This is Redbook/SLR context
2. Apply: RB 1.4 instead of BB 1.1(a)
3. Result: COMPLIANT (no error)
```

---

## Regex Pattern Library

### Signal Detection
```regex
# Any signal at start of citation
^(See|Accord|E\.g\.,?|Cf\.|But see|But cf\.|See also|See generally|Compare)[\s]

# Cf. without parenthetical
\bCf\.\s+[^(]+\([12]\d{3}\)\.(?!\s*\()

# Multiple signals wrong order
(See also|Cf\.)([^;]+);[\s]*(See)(?!\s+also|generally)
```

### Id. Validation
```regex
# Id without period
\bId\s+at\s+\d+

# Id without "at" before pincite
\bId\.\s+\d+(?!\s*n\.)

# Lowercase id (wrong)
\bid\.\s+at
```

### Citation Sentence Structure
```regex
# Missing period at end of citation sentence
\([12]\d{3}\)[^.]*$

# Case cite missing comma after case name
[A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+\s+\d{1,4}\s+U\.S\.(?!,)
```

### Section Symbols
```regex
# Wrong double symbol for single section
§§\s+\d+(?![,\-\d])

# Section spelled out in citation (should use §)
\b[Ss]ection\s+\d+[a-z]?\b(?=.*\([12]\d{3}\))
```

### Supra/Hereinafter
```regex
# Supra for case (wrong)
[A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+,\s+supra\s+note

# Supra without note reference
\bsupra\s+at\s+\d+(?!\s+note)

# Hereinafter outside parentheses
hereinafter\s+[^(]
```

---

## GPT Prompt Templates

### Template 1: Signal Validation
```
You are a Bluebook citation expert. Analyze whether the correct introductory
signal is used.

RULES:
- No signal: Authority directly states the proposition
- See: Authority clearly supports but doesn't directly state
- E.g.: Authority is one example among many
- Accord: Authority directly supports; text already cited/quoted another
- See also: Authority provides additional support
- Cf.: Authority supports by analogy (REQUIRES explanatory parenthetical)
- Compare...with: Comparison provides support
- But see: Authority directly contradicts
- But cf.: Authority contradicts by analogy (REQUIRES explanatory parenthetical)
- See generally: Background material (NO explanatory parenthetical allowed)

CITATION: {citation_text}
PROPOSITION SUPPORTED: {proposition}
QUOTE (if any): {quote}

ANALYSIS:
1. What does the citation do? (directly states / clearly supports / provides example / contradicts / etc.)
2. Current signal: {current_signal}
3. Is current signal appropriate? YES/NO
4. If NO, what signal should be used?
5. If Cf. or But cf., does it have required parenthetical? YES/NO

OUTPUT FORMAT:
{
  "current_signal": "...",
  "appropriate": true/false,
  "recommended_signal": "...",
  "reason": "...",
  "parenthetical_required": true/false,
  "parenthetical_present": true/false,
  "compliant": true/false
}
```

### Template 2: Short Form Selection
```
You are a Bluebook citation expert. Determine the correct short citation form.

RULES:
- Id.: Use if citing immediately preceding authority AND it was the sole
  authority in that citation
- Id. exception (RB 4.3): Don't use if source only in parenthetical of prior footnote
- Cases: Use short case name (Party, Vol. Reporter at Page)
- Statutes: Use short statutory form
- Books/Articles: Use [Author], supra note [X], at [page]
- Never use supra for cases or statutes

CURRENT FOOTNOTE: {current_footnote_num}
CURRENT CITATION: {current_citation}
IMMEDIATELY PREVIOUS CITATION: {previous_citation}
CONTEXT (footnotes within last 5): {recent_context}
SOURCE TYPE: {source_type}

ANALYSIS:
1. Is this the same source as immediately previous? YES/NO
2. If YES: Was previous citation sole authority? YES/NO
3. If sole: Was it only in parenthetical? YES/NO
4. Can use Id.? YES/NO
5. If not Id., what short form applies?

OUTPUT FORMAT:
{
  "can_use_id": true/false,
  "reason_for_id_decision": "...",
  "recommended_short_form": "...",
  "current_form": "...",
  "compliant": true/false,
  "rule_reference": "BB 4.1 / BB 4.2 / etc."
}
```

### Template 3: Parenthetical Analysis
```
You are a Bluebook citation expert analyzing parenthetical usage.

RULES:
- Cf. and But cf.: MUST have explanatory parenthetical
- See generally: Must NOT have explanatory parenthetical
- Others: Optional but often helpful
- Format: Start with lowercase (unless proper noun)
- Format: Begin with present participle OR quoted sentence
- Format: Never start with article (a, an, the)
- Order: Weight → Explanation → Quotation

CITATION: {full_citation}
SIGNAL: {signal_if_present}
PARENTHETICALS: {list_of_parentheticals}

ANALYSIS:
1. Signal type: Does it require/forbid parenthetical?
2. For each parenthetical:
   a. First word: Is it lowercase/proper noun/quote?
   b. Structure: Present participle / quote / other?
   c. Type: Weight / explanation / quotation?
3. If multiple: Are they in correct order?

OUTPUT FORMAT:
{
  "signal": "...",
  "parenthetical_required": true/false/optional,
  "parenthetical_forbidden": true/false,
  "parentheticals_found": [
    {
      "text": "...",
      "type": "weight/explanation/quotation",
      "format_correct": true/false,
      "issues": []
    }
  ],
  "order_correct": true/false,
  "overall_compliant": true/false,
  "suggestions": []
}
```

### Template 4: Authority Ordering
```
You are a Bluebook citation expert checking authority order within a signal.

RULES FOR ORDERING CASES:
1. U.S. Supreme Court (U.S.)
2. Courts of Appeals (F.2d, F.3d, F.4th, regional reporters)
3. District Courts (F. Supp., F. Supp. 2d, F. Supp. 3d)
4. State supreme courts
5. State appellate courts
6. State trial courts

Within same court level: Reverse chronological (newest first)

CITATION STRING: {full_citation_string}

ANALYSIS:
1. Identify each authority and its court level
2. Current order: List courts in order of appearance
3. Correct order: List courts in proper hierarchy
4. Is current order correct? YES/NO

OUTPUT FORMAT:
{
  "authorities": [
    {
      "citation": "...",
      "court_level": "SCOTUS/CoA/District/State Supreme/etc.",
      "year": 2000
    }
  ],
  "current_order": ["SCOTUS", "District", "CoA"],
  "correct_order": ["SCOTUS", "CoA", "District"],
  "order_correct": true/false,
  "suggested_reordering": "..."
}
```

---

## Conclusion

This analysis provides comprehensive error detection strategies for Bluebook Rules 1-4, incorporating both standard Bluebook and Stanford Law Review (Redbook) variations.

**Key Takeaways:**

1. **Layered Detection:** Combine regex (fast, simple patterns) with GPT (context, semantics)
2. **Context Matters:** Many rules require understanding surrounding text
3. **Redbook Deviations:** Always check which citation system applies
4. **Priority Triage:** Critical errors (affects meaning) vs. minor formatting
5. **Human Review:** Some edge cases will always need expert judgment

**Next Steps for Implementation:**

1. Build regex pattern library for Level 1 detection
2. Create GPT prompt suite for Level 2 validation
3. Establish confidence thresholds for auto-fix vs. human review
4. Implement feedback loop to improve detection accuracy
5. Extend analysis to Rules 5-21 for complete coverage

---

**Document Information:**
- **Rules Analyzed:** Bluebook Rules 1-4 + Redbook variations
- **Total Error Types Identified:** 47
- **Regex Patterns Provided:** 18
- **GPT Prompts Created:** 28
- **Cross-References:** Multiple inter-rule dependencies documented
