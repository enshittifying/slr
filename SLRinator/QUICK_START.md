# R1 Cite Checking - Quick Start Guide

## What We Have

Two production-ready R1 cite checking systems:

### 1. Structured Cite Checker (Formatting)
- **Purpose:** Check citation formatting, Bluebook/Redbook compliance
- **Speed:** Fast (no API calls)
- **Cost:** Free
- **What it checks:** 997 error types across all BB/RB rules

### 2. Substantive Cite Checker (Support Validation)
- **Purpose:** Check if citations support their text propositions
- **Speed:** Slow (GPT-4o API calls)
- **Cost:** ~$0.003-0.01 per citation
- **What it checks:** Semantic support with [AA:]/[SE:] edits

---

## Run Formatting Check

```bash
cd /home/user/slr/SLRinator

# Check Sanders article
python3 scripts/structured_cite_checker.py

# Output:
# - Console: Summary with error counts
# - JSON: output/sanders_structured_check.json
```

**Results on Sanders:**
- 325 footnotes, 481 citations
- 2,683 errors found
- Errors reported with: Footnote #, Citation #, Rule, Severity

---

## Run Substantive Check

```bash
cd /home/user/slr/SLRinator

# Set API key (required)
export OPENAI_API_KEY="sk-..."
# OR
echo "sk-..." > ~/.openai_api_key

# Check first 5 footnotes (for testing)
python3 scripts/substantive_r1_checker.py

# Check all footnotes (edit line 548 to set sample_size=None)
```

**What it does:**
1. Extracts text propositions (sentences with footnotes)
2. Links each footnote to its text claim
3. Uses GPT-4o to validate support
4. Generates [AA:] and [SE:] comments

**Cost:** Sanders (481 citations) ≈ $1.50-5.00

---

## Output Structure

Both systems produce similar JSON:

```json
{
  "footnotes": [
    {
      "footnote_number": 42,
      "footnote_text": "See Smith v. Jones...",
      "text_proposition": "The court held...",
      "citations": [
        {
          "citation_number": 1,
          "citation_text": "See Smith v. Jones, 123 F.3d 456",

          // From structured checker:
          "errors": [
            {
              "footnote_number": 42,
              "citation_number": 1,
              "error_id": "BB-1-001",
              "rule_id": "1",
              "severity": "high",
              "auto_fixable": true
            }
          ],

          // From substantive checker:
          "support_check": {
            "support_level": "maybe",
            "confidence": 0.7,
            "reasoning": "Citation partially supports...",
            "suggested_action": "flag_aa"
          },

          "edit": {
            "type": "comment",
            "marker": "AA",
            "text": "[AA: Citation partially supports but missing context]",
            "severity": "minor"
          }
        }
      ]
    }
  ]
}
```

---

## Framework Coverage

**Bluebook:**
- 19/21 top-level rules
- 29 subrules
- 711 error types

**Redbook:**
- 115/115 rules (COMPLETE)
- 286 error types
- Stanford-specific overrides

**Total:** 997 error types
**Auto-fixable:** 564 (56.6%)

---

## Key Files

**Production Systems:**
- `scripts/structured_cite_checker.py` - Formatting validator
- `scripts/substantive_r1_checker.py` - Support validator
- `src/r1_validation/auto_fixer.py` - Auto-fix implementations

**Configuration:**
- `config/error_detection_framework_ENHANCED.json` (v3.1.0)

**Documentation:**
- `SESSION_HANDOFF.md` - Complete technical documentation
- `QUICK_START.md` - This file

**Test Results:**
- `output/sanders_structured_check.json` - Full Sanders analysis

---

## Testing

```bash
# Validate framework (runs all 6 test suites)
python3 scripts/test_r1_validation.py

# Test on Sanders article (formatting only)
python3 scripts/test_sanders_article.py

# List all covered rules
python3 scripts/list_all_rules.py

# Analyze error quality
python3 scripts/analyze_sanders_errors.py
```

---

## Common Issues

**1. No API key found**
```bash
# Solution:
export OPENAI_API_KEY="sk-..."
# OR
echo "sk-..." > ~/.openai_api_key
```

**2. Module not found: docx or lxml**
```bash
pip install python-docx lxml openai
```

**3. File not found: Sanders article**
- Article location: `/home/user/slr/sp_machine/Sanders_PreSP_PostEEFormatting.docx`
- Edit file path in scripts if using different article

---

## Next Steps

1. **Review Sanders results:**
   ```bash
   jq . output/sanders_structured_check.json | less
   ```

2. **Test on your article:**
   - Edit file path in checker scripts
   - Run structured checker first (free)
   - Run substantive checker on sample (costs $)

3. **Integrate with R2 pipeline:**
   - Both systems produce compatible JSON
   - Can merge with R2 citation validation
   - See `R1_CITE_CHECKING_INTEGRATION_PLAN.md`

4. **Build Word document integration:**
   - Use `python-docx` to insert comments
   - Apply track changes for auto-fixes
   - Generate redlined PDF

---

## Support

**Full documentation:** `SESSION_HANDOFF.md`

**Questions?**
- Framework coverage: Run `list_all_rules.py`
- Error analysis: Run `analyze_sanders_errors.py`
- Testing: Run `test_r1_validation.py`

**Git branch:** `claude/fix-report-generation-016bLqLGVhEe8gpPP5eXJmfY`

---

**System Status:** ✅ Production-ready
**Last Updated:** 2025-11-23
