# Bluebook Tables T6, T7, T8 - Comprehensive Analysis

**Generated:** 2025-11-23
**Total Entries Analyzed:** 451 entries

---

## Overview

This analysis covers three critical Bluebook tables containing hundreds of abbreviation rules:

| Table | Name | Entries | Description |
|-------|------|---------|-------------|
| **T6** | Common Words in Case Names | **299** | Abbreviations for words in case names, institutional names, and periodical titles |
| **T7** | Court Names | **111** | Abbreviations for court names across all jurisdictions |
| **T8** | Explanatory Phrases | **41** | Abbreviations for explanatory phrases in case citations |

---

## Table T6: Common Words in Case Names (299 entries)

### Purpose
Table T6 provides standardized abbreviations for common words appearing in:
- Case names (e.g., *United States v. Association of American Railroads*)
- Institutional names
- Periodical titles

### Key Patterns

#### Apostrophe Usage
Many abbreviations use apostrophes to indicate missing letters:
- **Association** → Ass'n
- **Attorney** → Att'y
- **Commission** → Comm'n
- **Continental** → Cont'l
- **Department** → Dep't
- **International** → Int'l
- **National** → Nat'l

#### Period Usage
Most abbreviations end with a period:
- **Academic** → Acad.
- **Administrator** → Admin.
- **Federal** → Fed.
- **University** → Univ.

#### Special Cases
- **and** → & (ampersand, no period)
- **United States** → U.S. (initials with periods)
- **Law** (as first word) → Law (no abbreviation)
- **Forum** → F. (single letter)
- **Journal(s)** → J. (single letter)

### Multi-Variant Words
Some entries cover multiple word forms with the same abbreviation:
- **Accountant/Accounting/Accountancy** → Acct.
- **Economic/Economical/Economics/Economy** → Econ.
- **Electric/Electrical/Electricity/Electronic** → Elec.

### Common Errors Detected
1. **Missing apostrophes** (e.g., "Assn" instead of "Ass'n")
2. **Missing periods** (e.g., "Fed" instead of "Fed.")
3. **Using full forms in case names** (e.g., "Association" instead of "Ass'n")
4. **Inconsistent abbreviation** across multiple occurrences

---

## Table T7: Court Names (111 entries)

### Purpose
Table T7 provides standardized abbreviations for court names at all jurisdictional levels:
- Federal courts
- State courts
- Specialized tribunals
- Historical courts

### Federal Courts

#### Supreme Court
- **Supreme Court (federal)** → U.S.

#### Courts of Appeals
- **Court of Appeals (federal)** → Cir.
- **Court of Appeals for the Armed Forces** → C.A.A.F.
- **Court of Appeals for Veterans Claims** → Vet. App.

#### District Courts
- **District Court (federal)** → D.
- **Eastern District** → E.D.
- **Western District** → W.D.
- **Northern District** → N.D.
- **Southern District** → S.D.
- **Central District** → C.D.
- **Middle District** → M.D.

#### Specialized Federal Courts
- **Court of Federal Claims** → Fed. Cl.
- **Court of International Trade** → Ct. Int'l Trade
- **Tax Court** → T.C.
- **Bankruptcy Court** → Bankr.

### State Courts

#### General Trial Courts
- **Circuit Court (state)** → Cir. Ct.
- **District Court (state)** → Dist. Ct.
- **Superior Court** → Super. Ct.

#### Appellate Courts
- **Court of Appeal(s) (state)** → Ct. App.
- **Appellate Court** → App. Ct.
- **Appellate Division** → App. Div.

#### Supreme Courts
- **Supreme Court (other jurisdictions)** → Sup. Ct.
- **Supreme Judicial Court** → Sup. Jud. Ct.

### Specialized Courts
- **Bankruptcy Court** → Bankr.
- **Family Court** → Fam. Ct.
- **Juvenile Court** → Juv. Ct.
- **Probate Court** → Prob. Ct.
- **Tax Court** → T.C.
- **Traffic Court** → Traffic Ct.
- **Tribal Court** → <Name> Tribal Ct.

### Courts with Jurisdiction Indicators
Some court abbreviations include the jurisdiction name:
- **Borough Court** → <Name> Bor. Ct.
- **City Court** → <Name> City Ct.
- **County Court** → <Name> Cnty. Ct.
- **Municipal Court** → <Name> Mun. Ct.
- **Parish Court** → <Name> Parish Ct.

### Common Errors Detected
1. **Using full court names** instead of abbreviations
2. **Missing periods** in abbreviations
3. **Incorrect spacing** between abbreviated components
4. **Wrong jurisdictional identifiers**
5. **Confusing federal vs. state court abbreviations**

---

## Table T8: Explanatory Phrases (41 entries)

### Purpose
Table T8 provides standardized abbreviations for explanatory phrases used in parenthetical explanations following case citations.

### Types of Explanatory Phrases

#### Affirmation
- **affirmed** → aff'd
- **affirmed memorandum** → aff'd mem.
- **affirmed on other grounds** → aff'd on other grounds
- **affirmed on rehearing** → aff'd on reh'g
- **affirming** → aff'g

#### Reversal
- **reversed** → rev'd
- **reversed on other grounds** → rev'd on other grounds
- **reversed per curiam** → rev'd per curiam
- **reversing** → rev'g
- **overruled by** → overruled by

#### Certiorari
- **certiorari denied** → cert. denied
- **certiorari dismissed** → cert. dismissed
- **certiorari granted** → cert. granted
- **denying certiorari to** → denying cert. to
- **petition for certiorari filed** → petition for cert. filed

#### Other Procedural Actions
- **appeal denied** → appeal denied (no abbreviation)
- **appeal dismissed** → appeal dismissed (no abbreviation)
- **modified** → modified (no abbreviation)
- **vacated** → vacated (no abbreviation)
- **withdrawn** → withdrawn (no abbreviation)

#### Apostrophe Contractions
Several phrases use apostrophe contractions:
- **rehearing granted [denied]** → reh'g granted [denied]
- **affirmed** → aff'd
- **reversed** → rev'd

### No-Abbreviation Phrases
Many phrases in T8 are **not abbreviated**:
- appeal denied
- appeal dismissed
- amended by
- enforced
- invalidated by
- modified
- vacated
- withdrawn

### Common Errors Detected
1. **Missing apostrophes** in contractions (e.g., "affg" instead of "aff'g")
2. **Using full phrases** where abbreviations required (e.g., "certiorari denied" instead of "cert. denied")
3. **Abbreviating phrases that shouldn't be abbreviated** (e.g., "vac." instead of "vacated")
4. **Incorrect placement** outside parenthetical explanations

---

## Analysis Components

For each of the 451 entries, the analysis provides:

### 1. Regex Pattern for Long Form
Detects unabbreviated forms that should be abbreviated.

**Example (Association):**
```regex
\bAssociation\b
```

### 2. Regex Pattern for Short Form
Verifies proper use of abbreviated forms.

**Example (Association):**
```regex
\bAss'n\b
```

### 3. Error Pattern
Describes common errors for this specific abbreviation.

**Example (Association):**
```
Missing apostrophe (e.g., 'Assn' instead of 'Ass'n') |
Using full form 'Association' instead of abbreviated 'Ass'n' in case names
```

### 4. GPT Validation Prompt
AI prompt for detecting violations of this specific rule.

**Example (Association):**
```
Verify that all instances of "Association" in case names, institutional
names, or periodical titles are properly abbreviated as "Ass'n".

Check for:
1. Unabbreviated forms of "Association" that should be "Ass'n"
2. Incorrect abbreviations (missing apostrophes, periods, or wrong letters)
3. Inconsistent abbreviation within the same citation
4. Context: Only abbreviate in case names/titles, not in explanatory text

Return instances that violate Bluebook Table T6 rules.
```

---

## Special Handling

### Multi-Variant Entries
Entries with slashes (/) are expanded to cover all variants:
- **Accountant/Accounting/Accountancy** → creates patterns for all three words
- **Administrator/Administrative** → creates patterns for both forms

### Parenthetical Variants
Entries with optional parts in parentheses:
- **Business(es)** → matches both "Business" and "Businesses"
- **Broadcast(er/ing)** → matches "Broadcast", "Broadcaster", "Broadcasting"

### Comma-Separated Abbreviations
Some entries have multiple abbreviation options:
- **Admiral/Administrator (female)** → Adm'r, Adm'x
- **Executor/Executrix** → Ex'r, Ex'x

### Slash-Separated Abbreviations
Court name abbreviations with alternatives:
- **Court of General/Special Sessions** → Ct. Gen. Sess. / Ct. Spec. Sess.

### Jurisdiction Placeholders
Court names with `<Name>` placeholders are converted to regex:
- **Borough Court** → `<Name> Bor. Ct.` becomes `\b[A-Z][a-zA-Z]+ Bor\. Ct\.\b`

---

## Usage

The complete structured analysis is available in:
**`/home/user/slr/SLRinator/output/analysis/tables_6-8_analysis.json`**

This file contains all 451 entries with:
- Original word/phrase
- Correct abbreviation
- Regex patterns for detection
- Error patterns
- GPT validation prompts
- Section/category information

---

## Statistics Summary

| Metric | Count |
|--------|-------|
| Total entries | 451 |
| T6 entries | 299 |
| T7 entries | 111 |
| T8 entries | 41 |
| Entries with apostrophes | ~80 |
| Entries with periods | ~400 |
| Multi-variant entries | ~75 |
| No-abbreviation phrases | ~15 |

---

## Integration with R1 System

This analysis supports the R1 citation checking system by providing:

1. **Comprehensive regex patterns** for detecting both correct and incorrect forms
2. **Error descriptions** for generating helpful feedback
3. **GPT prompts** for AI-assisted validation
4. **Structured data** for programmatic cite checking

All patterns can be integrated into:
- Citation validators
- Style checkers
- Legal document processors
- AI-assisted cite checking systems

---

## Notes

- **Context matters**: Many T6 abbreviations only apply in case names, not in text
- **Periods are critical**: Missing periods are a common error
- **Apostrophes indicate contractions**: They show where letters have been removed
- **Consistency is key**: Use the same abbreviation throughout a document
- **Federal vs. State**: Court abbreviations differ by jurisdiction

---

*For the complete structured data with all 451 entries, see `tables_6-8_analysis.json`*
