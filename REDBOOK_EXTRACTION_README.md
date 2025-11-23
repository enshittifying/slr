# REDBOOK ALL RULES MASTER - Complete Extraction

## Overview

This document accompanies **`REDBOOK_ALL_RULES_MASTER.json`**, a comprehensive extraction of **EVERY SINGLE rule** from the Stanford Law Review Redbook (Volume 78).

**CRITICAL**: The Redbook is **separate from and sometimes OVERRIDES the Bluebook**. This extraction contains ONLY Redbook rules - no Bluebook rules are included.

## File Location

**`/home/user/slr/REDBOOK_ALL_RULES_MASTER.json`**

## Extraction Statistics

- **Total Rules Extracted**: 127
- **SLR-Specific House Style Rules**: 26
- **Explicit Bluebook Deviations**: 12
- **Clarifications**: 89
- **Red-Marked Deviations**: 19 (explicitly contradicts Bluebook/CMOS)
- **Total Regex Patterns**: 176
- **Rules with Regex Patterns**: 59

## Hierarchy of Citation Rules (Per Redbook Preamble)

1. **The Redbook (RB)** - Stanford Law Review house style - **TAKES PRECEDENCE**
2. **The Bluebook (BB)** - General citation guide
3. **The Chicago Manual of Style (CMOS)**
4. **Merriam-Webster**

## Structure of JSON File

```json
{
  "metadata": { ... },
  "preamble": { ... },
  "slr_specific_rules": [ ... ],
  "bluebook_deviations": [ ... ],
  "clarifications": [ ... ],
  "all_rules_by_section": { ... },
  "quick_reference": {
    "major_deviations": [ ... ],
    "forbidden_practices": [ ... ],
    "required_practices": [ ... ]
  }
}
```

## Major Categories

### 1. SLR-Specific Rules (26 rules)

These rules establish Stanford Law Review's unique house style:

- **Section 1.1**: Quoting parentheticals (ALWAYS required when source quotes another)
- **Section 16.5**: No citing abstracts
- **Section 18.1**: Use Perma.cc archival links exclusively
- **Section 18.4**: Never use "last visited" parentheticals
- And 22 more...

### 2. Bluebook Deviations (19 Red-Marked)

Explicit contradictions to Bluebook, marked in RED in the original Redbook:

1. **URLs**: Use archival link ONLY, never both original and archival
2. **"Last Visited"**: Never use; use "archived" parenthetical instead
3. **Movies**: Include director(s), not production company
4. **Email**: Always close as "email" not "e-mail"
5. **En Dashes**: Do not use; use hyphens instead
6. **Capitalization After Colon**: Capitalize if proper noun or complete sentence
7. **Professional Degrees**: Keep periods (J.D., Ph.D.)
8. **Court Filings**: Different pincite rules for electronic databases
9. **Services**: Do not cite services
10. **Public Domain Citations**: NEVER use
11. **Short Forms for Statutes**: Must include title number
12. **Federal Register Dates**: Use page top date, not promulgation date
13. **Et al.**: First citation must include ALL authors (except amicus briefs)
14. **Subtitles**: ALWAYS include
15. **Federalist Essays**: Special short form format
16. **Works in Collections**: Always use "in"
17. **Online Newspapers**: Use internet citation, not print
18. **Hyphenation**: Close "decisionmaking", "policymaking", etc.
19. **Underlined Type**: NEVER use; always use italics

### 3. Forbidden Practices

**These are NEVER allowed at SLR:**

1. **Underlined type** (Section 2.1) → Use italics instead
2. **Et seq.** (Section 3.7) → Specify full range instead
3. **Public domain citations** (Section 10.15) → Do not use

## Key Features

### Comprehensive Content Extraction

Each rule includes:
- **Section number and title**
- **Full rule text** with all paragraphs
- **Rule summary** (first paragraph)
- **Rule type** (SLR_SPECIFIC, BLUEBOOK_DEVIATION, or CLARIFICATION)
- **Deviations from Bluebook** (red-marked text)
- **Correct examples**
- **Incorrect examples**
- **Structured lists**
- **Bluebook references**
- **CMOS references**
- **Regex patterns** for automated validation
- **Metadata** (complexity, has_examples, has_patterns, etc.)

### Regex Patterns

176 regex patterns across 59 rules for:
- Id. citations
- Case names
- Signals
- Pincites
- Hereinafter
- Supra references
- Docket numbers
- URLs
- And more...

Each pattern includes:
- Regex expression
- Description
- Example
- Bluebook/Redbook reference
- Severity level (where applicable)

## Usage Examples

### Finding a Specific Rule

```python
import json

with open('REDBOOK_ALL_RULES_MASTER.json', 'r') as f:
    redbook = json.load(f)

# Get rule by section
rule = redbook['all_rules_by_section']['section_4_1']
print(rule['section_title'])  # "Using Id."
print(rule['rule_summary'])
```

### Finding All Deviations

```python
# Get all red-marked deviations
deviations = redbook['quick_reference']['major_deviations']

for dev in deviations:
    print(f"Section {dev['section']}: {dev['title']}")
    print(f"  {dev['deviation']}")
```

### Finding Forbidden Practices

```python
# Get practices that are never allowed
forbidden = redbook['quick_reference']['forbidden_practices']

for practice in forbidden:
    print(f"❌ {practice['practice']}")
    print(f"   Section {practice['section']}: {practice['note']}")
```

### Getting Regex Patterns

```python
# Get all regex patterns for a specific section
rule = redbook['all_rules_by_section']['section_4_1']

for pattern in rule['regex_patterns']:
    print(f"Pattern: {pattern['pattern']}")
    print(f"Description: {pattern['description']}")
    print(f"Example: {pattern['example']}")
```

## Critical Differences from Bluebook

### Id. Usage (Section 4.1)

**Redbook is VERY specific about when Id. can be used:**
- As first citation in footnote IF previous footnote cites ONLY that source
- As first/only citation in citation clause IF previous citation cites ONLY that source
- Within stringcite when citing immediately preceding source

### Et al. (Section 15.1)

**Redbook REQUIRES all authors in first citation:**
- ❌ Bluebook: Use "et al." for 3+ authors
- ✅ Redbook: Include ALL authors in first citation
- Only use "et al." in subsequent supra citations

### Subtitles (Section 15.2)

**Redbook ALWAYS includes subtitles:**
- ❌ Bluebook: May omit subtitles
- ✅ Redbook: ALWAYS include subtitles

### Public Domain Citations (Section 10.15)

**Redbook NEVER uses public domain format:**
- ❌ Example: 2020 VT 123
- ✅ Use traditional reporter citations instead

### Internet Sources (Section 18.1)

**Redbook uses ONLY Perma.cc archival links:**
- ❌ Bluebook: May include both original and archival
- ✅ Redbook: Only Perma.cc archival link

## Extraction Methodology

This file was created by:

1. **Parsing all 127 Redbook HTML files** from `/home/user/slr/reference_files/redbook_processed/`
2. **Extracting red-marked text** (color:#C00000) indicating Bluebook deviations
3. **Separating correct vs. incorrect examples**
4. **Generating regex patterns** based on rule content
5. **Categorizing rules** by type and complexity
6. **Creating cross-references** to Bluebook and CMOS sections
7. **Building quick reference** for major deviations and forbidden practices

## Quality Assurance

- ✅ No duplicate rules
- ✅ All 127 sections extracted
- ✅ Red-marked deviations identified and tagged
- ✅ Examples separated (correct vs. incorrect)
- ✅ Comprehensive regex patterns
- ✅ Cross-references to Bluebook and CMOS
- ✅ Metadata for filtering and searching

## File Size

- **646 KB** (compressed and deduplicated)
- **11,118 lines** of JSON
- Human-readable formatting (indent=2)

## Applications

This master file can be used for:

1. **Automated Citation Validation**: Use regex patterns to validate citations
2. **Citation Format Checking**: Compare against correct/incorrect examples
3. **Editor Training**: Reference for all SLR-specific rules
4. **Style Guide Integration**: Embed in citation management tools
5. **Conflict Resolution**: Identify when Redbook overrides Bluebook
6. **Pattern Matching**: Use regex patterns for automated corrections

## Important Notes

### Separation from Bluebook

**This file contains ONLY Redbook rules.** It does NOT include:
- Bluebook rules (except as referenced in cross-references)
- General citation formats (unless modified by Redbook)
- Tables from Bluebook (T1, T6, T10, etc.)

The Redbook is meant to **supplement and sometimes override** the Bluebook, not replace it entirely.

### Red-Marked Deviations

Text marked in RED in the original Redbook indicates an **explicit contradiction** to Bluebook or CMOS. These are the most critical deviations to remember and enforce.

### Hierarchy is Critical

When in doubt, follow this order:
1. Check Redbook FIRST
2. If Redbook doesn't address it, check Bluebook
3. If Bluebook doesn't address it, check CMOS
4. If CMOS doesn't address it, check Merriam-Webster

## Extraction Scripts

The extraction was performed using:
- **`/home/user/slr/extract_redbook_enhanced.py`**

The script can be re-run if the Redbook HTML files are updated.

## Version Information

- **Source**: Stanford Law Review Redbook, Volume 78
- **Extraction Date**: 2025-11-23
- **Format**: JSON (UTF-8)
- **Schema Version**: 1.0

## Support

For questions about:
- **Rule interpretation**: Refer to the original Redbook HTML files
- **Extraction issues**: Check the extraction script
- **Missing rules**: Verify against the index at `/home/user/slr/reference_files/redbook_processed/index.html`

## License

This extraction is for internal Stanford Law Review use. The underlying Redbook content remains the property of Stanford Law Review.

---

**Last Updated**: 2025-11-23
**Extracted By**: Enhanced Redbook Extraction Script v2.0
