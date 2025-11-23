# Detailed Examples from Bluebook Tables T6, T7, and T8

This document provides detailed examples showing the complete analysis for representative entries from each table.

---

## Table T6 Examples: Common Words in Case Names

### Example 1: Association (With Apostrophe)

```json
{
  "word": "Association",
  "abbreviation": "Ass'n",
  "regex_long": "\\bAssociation\\b",
  "regex_short": "\\bAss'n\\b",
  "error_pattern": "Missing apostrophe (e.g., 'Assn' instead of 'Ass'n') | Using full form 'Association' instead of abbreviated 'Ass'n' in case names",
  "gpt_prompt": "Verify that all instances of \"Association\" in case names, institutional names, or periodical titles are properly abbreviated as \"Ass'n\".\n\nCheck for:\n1. Unabbreviated forms of \"Association\" that should be \"Ass'n\"\n2. Incorrect abbreviations (missing apostrophes, periods, or wrong letters)\n3. Inconsistent abbreviation within the same citation\n4. Context: Only abbreviate in case names/titles, not in explanatory text\n\nReturn instances that violate Bluebook Table T6 rules."
}
```

**Correct Usage:**
- National Ass'n of Realtors v. Department of Justice
- American Bar Ass'n v. FTC

**Incorrect Usage:**
- ❌ National Association of Realtors v. DOJ
- ❌ National Assn of Realtors v. DOJ
- ❌ Nat'l Assn. of Realtors v. DOJ

---

### Example 2: United States (Multiple Periods)

```json
{
  "word": "United States",
  "abbreviation": "U.S.",
  "regex_long": "\\bUnited States\\b",
  "regex_short": "\\bU\\.S\\.\\b",
  "error_pattern": "Missing period (e.g., 'U.S' instead of 'U.S.') | Using full form 'United States' instead of abbreviated 'U.S.' in case names",
  "gpt_prompt": "Verify that all instances of \"United States\" in case names, institutional names, or periodical titles are properly abbreviated as \"U.S.\".\n\nCheck for:\n1. Unabbreviated forms of \"United States\" that should be \"U.S.\"\n2. Incorrect abbreviations (missing apostrophes, periods, or wrong letters)\n3. Inconsistent abbreviation within the same citation\n4. Context: Only abbreviate in case names/titles, not in explanatory text\n\nReturn instances that violate Bluebook Table T6 rules."
}
```

**Correct Usage:**
- U.S. v. Microsoft Corp.
- Brown v. U.S.

**Incorrect Usage:**
- ❌ United States v. Microsoft Corp.
- ❌ U.S v. Microsoft Corp. (missing second period)
- ❌ US v. Microsoft Corp. (no periods)

---

### Example 3: Multi-Variant Entry (Accountant/Accounting/Accountancy)

```json
{
  "word": "Accountant/Accounting/Accountancy",
  "abbreviation": "Acct.",
  "regex_long": "\\b(Accountant|Accounting|Accountancy)\\b",
  "regex_short": "\\bAcct\\.\\b",
  "error_pattern": "Missing period (e.g., 'Acct' instead of 'Acct.') | Using full form 'Accountant/Accounting/Accountancy' instead of abbreviated 'Acct.' in case names | Inconsistent abbreviation across variants: Accountant/Accounting/Accountancy",
  "gpt_prompt": "Verify that all instances of \"Accountant/Accounting/Accountancy\" in case names, institutional names, or periodical titles are properly abbreviated as \"Acct.\".\n\nCheck for:\n1. Unabbreviated forms of \"Accountant/Accounting/Accountancy\" that should be \"Acct.\"\n2. Incorrect abbreviations (missing apostrophes, periods, or wrong letters)\n3. Inconsistent abbreviation within the same citation\n4. Context: Only abbreviate in case names/titles, not in explanatory text\n\nReturn instances that violate Bluebook Table T6 rules."
}
```

**Correct Usage:**
- American Institute of Certified Pub. Acct. v. IRS
- Accounting Standards Bd. v. SEC → Acct. Standards Bd. v. SEC

**All three variants use the same abbreviation:**
- Accountant → Acct.
- Accounting → Acct.
- Accountancy → Acct.

---

### Example 4: Special Case (and → &)

```json
{
  "word": "and",
  "abbreviation": "&",
  "regex_long": "\\band\\b",
  "regex_short": "\\b&\\b",
  "error_pattern": "Using full form 'and' instead of abbreviated '&' in case names",
  "gpt_prompt": "Verify that all instances of \"and\" in case names, institutional names, or periodical titles are properly abbreviated as \"&\".\n\nCheck for:\n1. Unabbreviated forms of \"and\" that should be \"&\"\n2. Incorrect abbreviations (missing apostrophes, periods, or wrong letters)\n3. Inconsistent abbreviation within the same citation\n4. Context: Only abbreviate in case names/titles, not in explanatory text\n\nReturn instances that violate Bluebook Table T6 rules."
}
```

**Correct Usage:**
- Planned Parenthood of Se. Pa. v. Casey
- Sears, Roebuck & Co. v. FTC

**Incorrect Usage:**
- ❌ Sears, Roebuck and Company v. FTC

**Note:** The ampersand (&) has no period.

---

## Table T7 Examples: Court Names

### Example 5: Supreme Court (Federal)

```json
{
  "word": "Supreme Court (federal)",
  "abbreviation": "U.S.",
  "regex_long": "\\b(Supreme Court|Supreme Court federal)\\b",
  "regex_short": "\\bU\\.S\\.\\b",
  "error_pattern": "Using full form 'Supreme Court (federal)' instead of 'U.S.' | Misspelling or incorrect abbreviation of 'Court' | Missing periods in abbreviation",
  "gpt_prompt": "Verify that all instances of the court name \"Supreme Court (federal)\" are properly abbreviated as \"U.S.\".\n\nCheck for:\n1. Full court name \"Supreme Court (federal)\" used instead of abbreviation \"U.S.\"\n2. Incorrect abbreviation format (missing periods, wrong spacing)\n3. Inconsistent court name abbreviations within the same document\n4. Proper use of jurisdictional identifiers with court abbreviations\n\nReturn instances that violate Bluebook Table T7 court name abbreviation rules."
}
```

**Correct Usage:**
- Brown v. Board of Educ., 347 U.S. 483 (1954)
- Roe v. Wade, 410 U.S. 113 (1973)

**Incorrect Usage:**
- ❌ Brown v. Board of Education, 347 Supreme Court 483 (1954)
- ❌ Roe v. Wade, 410 U.S 113 (1973) (missing second period)

---

### Example 6: District Court (Federal)

```json
{
  "word": "District Court (federal)",
  "abbreviation": "D.",
  "regex_long": "\\b(District Court|District Court federal)\\b",
  "regex_short": "\\bD\\.\\b",
  "error_pattern": "Using full form 'District Court (federal)' instead of 'D.' | Misspelling or incorrect abbreviation of 'Court' | Missing periods in abbreviation",
  "gpt_prompt": "Verify that all instances of the court name \"District Court (federal)\" are properly abbreviated as \"D.\".\n\nCheck for:\n1. Full court name \"District Court (federal)\" used instead of abbreviation \"D.\"\n2. Incorrect abbreviation format (missing periods, wrong spacing)\n3. Inconsistent court name abbreviations within the same document\n4. Proper use of jurisdictional identifiers with court abbreviations\n\nReturn instances that violate Bluebook Table T7 court name abbreviation rules."
}
```

**Correct Usage:**
- Smith v. Jones, 123 F. Supp. 2d 456 (S.D.N.Y. 2000)
- Doe v. Roe, 456 F. Supp. 3d 789 (E.D. Va. 2020)

**Format:** [District]. [State Abbr.]
- S.D.N.Y. = Southern District of New York
- E.D. Va. = Eastern District of Virginia

---

### Example 7: Court with Jurisdiction Placeholder

```json
{
  "word": "County Court",
  "abbreviation": "<Name> Cnty. Ct.",
  "regex_long": "\\bCounty Court\\b",
  "regex_short": "\\b[A-Z][a-zA-Z]+ Cnty\\. Ct\\.\\b",
  "error_pattern": "Using full form 'County Court' instead of '<Name> Cnty. Ct.' | Misspelling or incorrect abbreviation of 'Court' | Missing periods in abbreviation",
  "gpt_prompt": "Verify that all instances of the court name \"County Court\" are properly abbreviated as \"<Name> Cnty. Ct.\".\n\nCheck for:\n1. Full court name \"County Court\" used instead of abbreviation \"<Name> Cnty. Ct.\"\n2. Incorrect abbreviation format (missing periods, wrong spacing)\n3. Inconsistent court name abbreviations within the same document\n4. Proper use of jurisdictional identifiers with court abbreviations\n\nReturn instances that violate Bluebook Table T7 court name abbreviation rules."
}
```

**Correct Usage:**
- Smith v. Jones, 123 N.Y.S.2d 456 (Nassau Cnty. Ct. 1995)
- Doe v. Roe, 456 Cal. Rptr. 789 (Los Angeles Cnty. Ct. 2010)

**Pattern:** The jurisdiction name precedes "Cnty. Ct."

---

### Example 8: Bankruptcy Court

```json
{
  "word": "Bankruptcy Court/Judge",
  "abbreviation": "Bankr.",
  "regex_long": "\\b(Bankruptcy Court|Bankruptcy Judge)\\b",
  "regex_short": "\\bBankr\\.\\b",
  "error_pattern": "Using full form 'Bankruptcy Court/Judge' instead of 'Bankr.' | Misspelling or incorrect abbreviation of 'Court' | Missing periods in abbreviation",
  "gpt_prompt": "Verify that all instances of the court name \"Bankruptcy Court/Judge\" are properly abbreviated as \"Bankr.\".\n\nCheck for:\n1. Full court name \"Bankruptcy Court/Judge\" used instead of abbreviation \"Bankr.\"\n2. Incorrect abbreviation format (missing periods, wrong spacing)\n3. Inconsistent court name abbreviations within the same document\n4. Proper use of jurisdictional identifiers with court abbreviations\n\nReturn instances that violate Bluebook Table T7 court name abbreviation rules."
}
```

**Correct Usage:**
- In re XYZ Corp., 123 B.R. 456 (Bankr. S.D.N.Y. 2000)
- In re ABC Inc., 456 B.R. 789 (Bankr. D. Del. 2010)

---

## Table T8 Examples: Explanatory Phrases

### Example 9: Certiorari Denied (Abbreviated)

```json
{
  "word": "certiorari denied",
  "abbreviation": "cert. denied",
  "regex_long": "\\bcertiorari denied\\b",
  "regex_short": "\\bcert\\. denied\\b",
  "error_pattern": "Using full phrase 'certiorari denied' in parenthetical instead of 'cert. denied'",
  "gpt_prompt": "Verify that all instances of the explanatory phrase \"certiorari denied\" are properly abbreviated as \"cert. denied\" in parenthetical explanations.\n\nCheck for:\n1. Full phrase \"certiorari denied\" used instead of abbreviation \"cert. denied\"\n2. Incorrect abbreviation (missing apostrophes or wrong contraction)\n3. Proper placement in parenthetical (after case citation)\n4. Correct punctuation and spacing\n\nReturn instances that violate Bluebook Table T8 explanatory phrase abbreviation rules."
}
```

**Correct Usage:**
- Smith v. Jones, 123 F.3d 456 (2d Cir. 2000), cert. denied, 531 U.S. 1234 (2001)
- Doe v. Roe, 456 F.3d 789 (9th Cir. 2005), cert. denied, 546 U.S. 1100 (2006)

**Incorrect Usage:**
- ❌ Smith v. Jones, 123 F.3d 456 (2d Cir. 2000), certiorari denied, 531 U.S. 1234 (2001)

---

### Example 10: Affirmed (Apostrophe Contraction)

```json
{
  "word": "affirmed",
  "abbreviation": "aff'd",
  "regex_long": "\\baffirmed\\b",
  "regex_short": "\\baff'd\\b",
  "error_pattern": "Missing apostrophe in contraction (e.g., 'affd' instead of 'aff'd') | Using full phrase 'affirmed' in parenthetical instead of 'aff'd'",
  "gpt_prompt": "Verify that all instances of the explanatory phrase \"affirmed\" are properly abbreviated as \"aff'd\" in parenthetical explanations.\n\nCheck for:\n1. Full phrase \"affirmed\" used instead of abbreviation \"aff'd\"\n2. Incorrect abbreviation (missing apostrophes or wrong contraction)\n3. Proper placement in parenthetical (after case citation)\n4. Correct punctuation and spacing\n\nReturn instances that violate Bluebook Table T8 explanatory phrase abbreviation rules."
}
```

**Correct Usage:**
- Smith v. Jones, 123 F.3d 456 (2d Cir. 2000), aff'd, 531 U.S. 1234 (2001)
- Doe v. Roe, 456 F. Supp. 2d 789 (S.D.N.Y. 2005), aff'd, 567 F.3d 890 (2d Cir. 2006)

**Incorrect Usage:**
- ❌ Smith v. Jones, 123 F.3d 456 (2d Cir. 2000), affirmed, 531 U.S. 1234 (2001)
- ❌ Smith v. Jones, 123 F.3d 456 (2d Cir. 2000), affd, 531 U.S. 1234 (2001)

---

### Example 11: Reversed (Apostrophe Contraction)

```json
{
  "word": "reversed",
  "abbreviation": "rev'd",
  "regex_long": "\\breversed\\b",
  "regex_short": "\\brev'd\\b",
  "error_pattern": "Missing apostrophe in contraction (e.g., 'revd' instead of 'rev'd') | Using full phrase 'reversed' in parenthetical instead of 'rev'd'",
  "gpt_prompt": "Verify that all instances of the explanatory phrase \"reversed\" are properly abbreviated as \"rev'd\" in parenthetical explanations.\n\nCheck for:\n1. Full phrase \"reversed\" used instead of abbreviation \"rev'd\"\n2. Incorrect abbreviation (missing apostrophes or wrong contraction)\n3. Proper placement in parenthetical (after case citation)\n4. Correct punctuation and spacing\n\nReturn instances that violate Bluebook Table T8 explanatory phrase abbreviation rules."
}
```

**Correct Usage:**
- Smith v. Jones, 123 F. Supp. 2d 456 (S.D.N.Y. 2000), rev'd, 567 F.3d 890 (2d Cir. 2002)

**Incorrect Usage:**
- ❌ Smith v. Jones, 123 F. Supp. 2d 456 (S.D.N.Y. 2000), reversed, 567 F.3d 890 (2d Cir. 2002)
- ❌ Smith v. Jones, 123 F. Supp. 2d 456 (S.D.N.Y. 2000), revd, 567 F.3d 890 (2d Cir. 2002)

---

### Example 12: Vacated (No Abbreviation)

```json
{
  "word": "vacated",
  "abbreviation": "vacated",
  "regex_long": "\\bvacated\\b",
  "regex_short": "\\bvacated\\b",
  "error_pattern": "No abbreviation needed - use as-is: 'vacated'",
  "gpt_prompt": "Verify that the explanatory phrase \"vacated\" is used correctly in parenthetical explanations.\n\nCheck for:\n1. Proper placement in parenthetical (after case citation)\n2. Correct capitalization and punctuation\n3. Appropriate context for use of this phrase\n4. No unnecessary abbreviation (this phrase should not be abbreviated)\n\nReturn instances that violate Bluebook Table T8 explanatory phrase rules."
}
```

**Correct Usage:**
- Smith v. Jones, 123 F.3d 456 (2d Cir. 2000), vacated, 531 U.S. 1234 (2001)

**Important:** Some T8 phrases are NOT abbreviated:
- vacated (not "vac.")
- modified (not "mod.")
- withdrawn (not "withd.")
- enforced (not "enf.")

---

## Common Error Patterns Across All Tables

### 1. Missing Apostrophes
**Most Common Issue:** Omitting apostrophes in contractions

Examples:
- ❌ Assn → ✓ Ass'n
- ❌ Atty → ✓ Att'y
- ❌ Commn → ✓ Comm'n
- ❌ Dept → ✓ Dep'tI- ❌ Intl → ✓ Int'l
- ❌ Natl → ✓ Nat'l
- ❌ affd → ✓ aff'd
- ❌ revd → ✓ rev'd

### 2. Missing Periods
**Second Most Common:** Omitting final periods

Examples:
- ❌ Fed → ✓ Fed.
- ❌ Corp → ✓ Corp.
- ❌ Educ → ✓ Educ.
- ❌ U.S → ✓ U.S. (need both periods)

### 3. Using Full Forms
**Context Error:** Using unabbreviated forms in case names

Examples:
- ❌ National Association → ✓ Nat'l Ass'n
- ❌ United States → ✓ U.S.
- ❌ certiorari denied → ✓ cert. denied

### 4. Inconsistent Abbreviation
**Consistency Error:** Different abbreviations for the same word

Example Citation with Errors:
❌ National Association of Manufacturers v. Environmental Prot. Agency

Should be:
✓ Nat'l Ass'n of Mfrs. v. Env't Prot. Agency

---

## Integration Tips

### For Regex Validation
1. Use `regex_long` to find unabbreviated forms
2. Use `regex_short` to verify correct abbreviations
3. Check context (case names vs. explanatory text)

### For GPT Validation
1. Pass the entire citation to GPT with the relevant prompt
2. GPT can understand context better than regex
3. Use for complex cases with multiple potential violations

### For Error Reporting
1. Use `error_pattern` to generate helpful user messages
2. Provide specific correction (not just "abbreviation error")
3. Include both the incorrect form and correct form

---

## Quick Reference

**Total Entries:** 451
- T6: 299 common words
- T7: 111 court names
- T8: 41 explanatory phrases

**Entries with Apostrophes:** 51
**Entries with Periods:** ~400
**Multi-Variant Entries:** ~75
**No-Abbreviation Entries:** 18

**Most Complex Patterns:** Multi-variant words with slashes
**Most Error-Prone:** Apostrophe omissions

---

*For complete structured data with all 451 entries, see `/home/user/slr/SLRinator/output/analysis/tables_6-8_analysis.json`*
