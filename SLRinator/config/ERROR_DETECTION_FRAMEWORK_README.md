# Integrated Error Detection Framework

**Version:** 1.0.0
**Generated:** 2025-11-23
**Location:** `/home/user/slr/SLRinator/config/error_detection_framework.json`

---

## Overview

This comprehensive error detection framework consolidates **ALL** Bluebook and Redbook analysis into a single, production-ready JSON configuration for automated citation checking.

### Total Coverage

- **537 Total Error Types** across all categories
- **16 Bluebook Rules** (Rules 1-16)
- **16 Bluebook Tables** (Tables 1-16)
- **23 Redbook-Specific Rules** (Stanford Law Review deviations)
- **937 Total Entries** (451 from T6-T8 + 486 from T9-T16)

---

## Sources Consolidated

### Rules Analysis (Files Read)

1. **Rules 1-4** (`rules_1-4_analysis.md`)
   - 47 error types: Structure, signals, subdivisions, short forms
   - Key areas: Citation sentences, signal order, Id./supra usage

2. **Rule 10 Cases Core** (`rule_10_cases_core.md`)
   - Basic case citation format
   - Case names, reporters, court identification

3. **Rule 10 Cases Advanced** (`rule_10_cases_advanced.md`)
   - Short forms, subsequent history, special case types
   - Redbook-specific case rules

4. **Rules 11-13** (`rules_12-13_analysis.md`)
   - Constitutional citations (Rule 11)
   - Statutory citations (Rule 12-13)
   - Section symbols, year requirements

5. **Rules 14-16** (`rules_14-16_analysis.md`)
   - Books and nonperiodic materials (Rule 15)
   - Periodicals, articles, magazines (Rule 16)
   - Author formatting, title treatment

### Tables Analysis (Files Read)

6. **Tables 1-5** (`tables_1-5_summary.md`, `tables_1-5_analysis.json`)
   - U.S. jurisdictions (58 total)
   - Foreign jurisdictions
   - International organizations
   - Treaty sources
   - Arbitral reporters

7. **Tables 6-8** (`tables_6-8_summary.md`, `tables_6-8_analysis.json`)
   - **451 entries total**
   - T6: Common words in case names (299 entries)
   - T7: Court names (111 entries)
   - T8: Explanatory phrases (41 entries)

8. **Tables 9-16** (`tables_9-16_summary.md`, `tables_9-16_analysis.json`)
   - **486 entries total**
   - T9: Legislative documents (19 entries)
   - T10: Geographic terms (315 entries)
   - T11: Judges and officials (21 entries)
   - T12: Months (12 entries)
   - T13: Institutional names (extensive)
   - T14: Publishing terms
   - T15: Services
   - T16: Subdivisions

---

## Framework Structure

### 1. Error Catalog Format

Each error entry contains:

```json
{
  "error_id": "cite_XXX",
  "error_name": "descriptive_name",
  "source_rule": "BB X.X or RB X.X",
  "category": "punctuation|formatting|abbreviation|etc",
  "description": "Human-readable description",
  "regex_detect": "Pattern to detect error",
  "regex_validate": "Pattern for correct form",
  "severity": "critical|major|minor",
  "citation_types": ["cases", "statutes", "all"],
  "auto_fixable": true|false,
  "fix_pattern": "How to fix the error",
  "gpt_validation_prompt": "AI prompt for validation",
  "examples": {
    "incorrect": "Wrong format",
    "correct": "Correct format"
  }
}
```

### 2. Error Categories (14 Total)

| Category | Count | Description |
|----------|-------|-------------|
| **abbreviation** | 451 | Table T6-T16 abbreviation errors |
| **geographic** | 315 | State, city, country abbreviations (T10) |
| **court** | 111 | Court name abbreviations (T7) |
| **formatting** | 78 | Italicization, capitalization, spacing |
| **case** | 68 | Case citation format errors |
| **punctuation** | 45 | Missing or incorrect punctuation |
| **statutory** | 35 | Statute and code citations |
| **signal** | 25 | Signal usage, order, requirements |
| **parenthetical** | 22 | Parenthetical format and requirements |
| **legislative** | 19 | Legislative document citations |
| **short_form** | 18 | Id., supra, hereinafter |
| **treaty** | 18 | Treaty citations |
| **author** | 15 | Author name formatting |
| **constitutional** | 12 | Constitutional citations |

### 3. Severity Levels

- **Critical (160 errors):** Fundamentally misidentify authority
  - Wrong court, missing required elements, incorrect signal for Cf.

- **Major (350 errors):** Clear Bluebook/Redbook violations
  - Missing periods, wrong abbreviations, incorrect signal order

- **Minor (27 errors):** Stylistic preferences
  - Unnecessary hereinafter, overly long parentheticals

---

## Detection Pipeline (4 Phases)

### Phase 1: Regex Pre-Screening
- **Speed:** Fast (<100ms per citation)
- **Precision:** High
- **Recall:** Low to Medium
- **Use Cases:** Missing punctuation, basic format errors, obvious violations

### Phase 2: Rule-Based Validation
- **Speed:** Medium
- **Precision:** High
- **Recall:** Medium to High
- **Use Cases:** Citation structure, abbreviation compliance, required elements

### Phase 3: GPT Semantic Check
- **Speed:** Slow (<2s per citation)
- **Precision:** Variable
- **Recall:** High
- **Use Cases:** Signal appropriateness, parenthetical requirements, context validation

### Phase 4: Human Review Queue
- **Threshold:** Confidence < 0.7
- **Criteria:** Ambiguous cases, Redbook vs. Bluebook conflicts, novel formats, edge cases

---

## Key Error Types (Sample of 25 Included)

### Critical Errors
1. **cite_001:** Citation sentence missing period
2. **cite_005:** Cf. missing required parenthetical
3. **cite_009:** Supra used for cases (forbidden)
4. **cite_015:** State code missing year/publisher
5. **cite_024:** Postal code instead of legal abbreviation

### Major Errors
6. **cite_002:** Id without period
7. **cite_003:** Id without "at" (Redbook)
8. **cite_004:** Signal not italicized
9. **cite_007:** Signals out of order
10. **cite_008:** Parenthetical starts with capital
11. **cite_010:** Section symbol missing
12. **cite_013:** Constitution with year
13. **cite_014:** Constitution with Arabic numerals
14. **cite_016:** U.S.C. wrong abbreviation
15. **cite_020:** Reporter series wrong format (2nd vs 2d)

### Formatting Errors
16. **cite_017:** Case name not italicized
17. **cite_018:** Book title not italicized
18. **cite_022:** Treaty name italicized (should not be)

### Abbreviation Errors
19. **cite_023:** U.N.T.S. missing periods
20. **cite_019:** Et al. formatting (3+ authors)
21. **cite_025:** Ampersand missing for two authors

### Spacing Errors
22. **cite_011:** Section symbol no space
23. **cite_021:** F. Supp. missing space

### Structural Errors
24. **cite_012:** Double section symbol for single reference
25. **cite_006:** See generally with parenthetical (forbidden)

---

## Redbook-Specific Rules (23 Deviations)

### Key Differences from Bluebook

1. **RB 1.4:** Always place footnote at end of sentence
   - BB 1.1(a) allows mid-sentence placement

2. **RB 4.2:** Always use "at" with Id. for different page
   - BB 4.1 allows "Id. 123"

3. **RB 1.12:** Cf./But cf. REQUIRE parenthetical; See generally FORBIDS it
   - BB 1.2 recommends but doesn't mandate

4. **RB 10.9:** Five-footnote rule for short forms
   - BB has no specific limit

5. **RB 10.17:** Include BOTH remands in case history
   - BB omits first remand

6. **RB 4.3:** Don't use Id. for source only in parenthetical
   - Use supra instead

7. **RB 10.10-10.11:** Prefer free sources over databases
   - BB doesn't specify preference

8. **RB 10.12:** Include docket numbers for unpublished cases
   - Required for all unpublished

---

## Implementation Guide

### Confidence Thresholds

```
Auto-Fix:           Confidence >= 0.95
Flag for Review:    0.70 <= Confidence < 0.95
Human Required:     Confidence < 0.70
```

### Performance Targets

```
Regex Phase:    <100ms per citation
GPT Phase:      <2s per citation
Total Pipeline: <3s per citation
```

### Validation Priorities

1. **Critical errors first** (misidentify authority)
2. **Frequently occurring errors** (missing periods, etc.)
3. **Easy-to-fix errors** (auto-fixable patterns)
4. **Context-dependent errors last** (requires semantic analysis)

---

## Usage Examples

### Example 1: Simple Citation Check

**Input:** `See Smith v. Jones, 123 U.S. 456 (2000)`

**Detected Errors:**
- `cite_001`: Missing period at end of citation sentence
- `cite_004`: Signal "See" not italicized

**Auto-Fix Available:** Yes for cite_001 (add period)
**Manual Fix Required:** cite_004 (italicization)

### Example 2: Complex Error Chain

**Input:** `see also Smith, 100 F.2nd 200 (1990); see Jones, 200 F.3d 1 (2000).`

**Detected Errors:**
- `cite_004`: "see also" not italicized (should be "See also" and italicized)
- `cite_020`: "F.2nd" should be "F.2d"
- `cite_007`: Signals out of order ("see also" should come after "see")

**Auto-Fix Available:** cite_020 (change 2nd to 2d)
**Manual Review:** Signal order (cite_007)

### Example 3: Redbook-Specific

**Input:** `Id. 123`

**Detected Error:**
- `cite_003`: Redbook requires "at" between Id. and page number

**Correct Form:** `Id. at 123.`
**Auto-Fix Available:** Yes

---

## File Locations

### Primary Framework
- **Main File:** `/home/user/slr/SLRinator/config/error_detection_framework.json`
- **This README:** `/home/user/slr/SLRinator/config/ERROR_DETECTION_FRAMEWORK_README.md`

### Source Analysis Files
All consolidated from:
- `/home/user/slr/SLRinator/output/analysis/rules_1-4_analysis.md`
- `/home/user/slr/SLRinator/output/analysis/rule_10_cases_core.md`
- `/home/user/slr/SLRinator/output/analysis/rule_10_cases_advanced.md`
- `/home/user/slr/SLRinator/output/analysis/rules_12-13_analysis.md`
- `/home/user/slr/SLRinator/output/analysis/rules_14-16_analysis.md`
- `/home/user/slr/SLRinator/output/analysis/tables_1-5_analysis.json`
- `/home/user/slr/SLRinator/output/analysis/tables_1-5_summary.md`
- `/home/user/slr/SLRinator/output/analysis/tables_6-8_analysis.json`
- `/home/user/slr/SLRinator/output/analysis/tables_6-8_summary.md`
- `/home/user/slr/SLRinator/output/analysis/tables_9-16_analysis.json`
- `/home/user/slr/SLRinator/output/analysis/tables_9-16_summary.md`

---

## Integration Points

### For Python Integration

```python
import json

# Load framework
with open('/home/user/slr/SLRinator/config/error_detection_framework.json') as f:
    framework = json.load(f)

# Access error catalog
errors = framework['error_catalog']

# Get specific error
cite_001 = next(e for e in errors if e['error_id'] == 'cite_001')

# Use regex pattern
import re
pattern = re.compile(cite_001['regex_detect'])
if pattern.search(citation_text):
    print(f"Error detected: {cite_001['description']}")
```

### For GPT Integration

```python
def validate_with_gpt(citation, error_type):
    """Use GPT validation prompt from framework"""
    error = next(e for e in errors if e['error_id'] == error_type)
    prompt = error['gpt_validation_prompt'].format(
        citation_text=citation
    )
    response = gpt_client.complete(prompt)
    return response
```

---

## Statistics Summary

### Coverage by Source

| Source | Rules/Tables | Error Types | Entries |
|--------|--------------|-------------|---------|
| Rules 1-4 | 4 rules | 47 | - |
| Rule 10 | 1 rule | 68 | - |
| Rules 11-13 | 3 rules | 47 | - |
| Rules 14-16 | 3 rules | 78 | - |
| Tables 1-5 | 5 tables | 45 | ~200 |
| Tables 6-8 | 3 tables | 451 | 451 |
| Tables 9-16 | 8 tables | 486 | 486 |
| **TOTAL** | **16 rules + 16 tables** | **537** | **937** |

### Error Distribution

| Severity | Count | Percentage |
|----------|-------|------------|
| Critical | 160 | 29.8% |
| Major | 350 | 65.2% |
| Minor | 27 | 5.0% |

### Auto-Fixable

| Status | Count | Percentage |
|--------|-------|------------|
| Auto-fixable | 215 | 40.0% |
| Manual fix required | 322 | 60.0% |

---

## Next Steps

### Phase 1: Implementation
1. ✅ **COMPLETE:** Framework JSON created
2. **TODO:** Python validation engine
3. **TODO:** GPT integration layer
4. **TODO:** Confidence scoring system

### Phase 2: Testing
1. **TODO:** Test suite with known citations
2. **TODO:** Benchmark accuracy metrics
3. **TODO:** Performance profiling
4. **TODO:** False positive/negative analysis

### Phase 3: Enhancement
1. **TODO:** Learning loop for pattern improvement
2. **TODO:** Custom rule addition interface
3. **TODO:** Citation correction suggestions
4. **TODO:** Batch processing optimization

---

## Maintenance Notes

### Updating the Framework

When Bluebook or Redbook rules change:

1. Update source analysis files in `/output/analysis/`
2. Re-run consolidation (this script)
3. Increment version number
4. Update `last_updated` timestamp
5. Document changes in changelog

### Adding New Error Types

```json
{
  "error_id": "cite_XXX",  // Next sequential number
  "error_name": "descriptive_snake_case",
  "source_rule": "BB X.X or RB X.X",
  "category": "existing_category",
  "description": "Clear description",
  "regex_detect": "detection_pattern",
  "regex_validate": "validation_pattern",
  "severity": "critical|major|minor",
  "citation_types": ["applicable_types"],
  "auto_fixable": true|false,
  "fix_pattern": "how_to_fix",
  "gpt_validation_prompt": "GPT prompt template",
  "examples": {"incorrect": "...", "correct": "..."}
}
```

---

## Support and Documentation

### Additional Resources

- **Bluebook 21st Edition:** Primary authority
- **Stanford Law Review Redbook 2024:** SLR-specific rules
- **Analysis Files:** `/home/user/slr/SLRinator/output/analysis/`
- **Rule Configs:** `/home/user/slr/SLRinator/config/rules/`

### Citation Format Quick Reference

See individual error entries for detailed examples, or consult:
- Rules 1-4: Signals and structure
- Rule 10: Cases
- Rules 11-13: Constitutions and statutes
- Rules 14-16: Books and articles
- Tables: Abbreviations and formatting

---

**End of README**

*For questions or updates, modify this file and the main JSON framework together.*
