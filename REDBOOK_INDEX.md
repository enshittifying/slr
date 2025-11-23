# Stanford Law Review Redbook - Complete Extraction Index

## 📁 File Locations

All files are located in: **`/home/user/slr/`**

## 📚 Main Files

### 1. **REDBOOK_ALL_RULES_MASTER.json** (646 KB)
**The complete extraction of all 127 Redbook rules**

- ✅ All SLR-specific rules
- ✅ All deviations from Bluebook (red-marked)
- ✅ Stanford Law Review house style rules
- ✅ Complete JSON structure with 176 regex patterns
- ✅ All examples and exceptions
- ✅ Separated from Bluebook rules

**Quick Access:**
```bash
cat /home/user/slr/REDBOOK_ALL_RULES_MASTER.json
```

---

### 2. **REDBOOK_EXTRACTION_README.md** (9.2 KB)
**Comprehensive documentation and usage guide**

Contents:
- Complete file structure explanation
- Usage examples (Python and command line)
- Methodology documentation
- Quality assurance checklist
- Applications and use cases

**Quick Access:**
```bash
cat /home/user/slr/REDBOOK_EXTRACTION_README.md
```

---

### 3. **REDBOOK_QUICK_REFERENCE.md** (9.5 KB)
**Quick reference guide for editors**

Contents:
- ❌ Forbidden practices (3 items)
- 🔴 Red-marked deviations (19 items)
- ⭐ SLR-specific rules
- 📋 Quick checklist
- Critical differences from Bluebook

**Quick Access:**
```bash
cat /home/user/slr/REDBOOK_QUICK_REFERENCE.md
```

---

### 4. **REDBOOK_EXTRACTION_SUMMARY.txt** (12 KB)
**Complete extraction summary and statistics**

Contents:
- Extraction statistics
- All 19 red-marked deviations listed
- Forbidden practices
- Structure documentation
- Verification commands

**Quick Access:**
```bash
cat /home/user/slr/REDBOOK_EXTRACTION_SUMMARY.txt
```

---

## 🎯 Quick Start

### For Editors - Quick Reference
Start here: **REDBOOK_QUICK_REFERENCE.md**
- Quick checklist before finalizing citations
- Forbidden practices list
- Critical deviations from Bluebook

### For Developers - Full JSON
Start here: **REDBOOK_ALL_RULES_MASTER.json**
- Complete rule extraction with regex patterns
- Programmatic access to all rules
- Automated validation support

### For Documentation - Full Details
Start here: **REDBOOK_EXTRACTION_README.md**
- Complete usage guide
- Code examples
- Structure explanation

---

## 📊 Statistics at a Glance

| Metric | Count |
|--------|-------|
| **Total Redbook Sections** | 127 |
| **SLR-Specific Rules** | 26 |
| **Bluebook Deviations** | 12 |
| **Red-Marked Deviations** | 19 |
| **Clarifications** | 89 |
| **Forbidden Practices** | 3 |
| **Total Regex Patterns** | 176 |
| **Rules with Patterns** | 59 |

---

## 🚨 Most Critical Rules (MUST KNOW)

### Never Use These:
1. ❌ **Underlined type** → Use italics
2. ❌ **"et seq."** → Specify full range
3. ❌ **Public domain citations** → Use traditional reporters

### Always Do These:
1. ✅ **Include ALL authors** in first citation (no "et al.")
2. ✅ **Include subtitles** (always)
3. ✅ **Use Perma.cc ONLY** (no original URL)
4. ✅ **One space** after punctuation
5. ✅ **Quoting parenthetical** when source quotes another

---

## 🔍 Quick Searches

### View All Deviations
```python
import json
with open('/home/user/slr/REDBOOK_ALL_RULES_MASTER.json') as f:
    data = json.load(f)

for dev in data['quick_reference']['major_deviations']:
    print(f"Section {dev['section']}: {dev['title']}")
```

### Get Specific Rule
```python
import json
with open('/home/user/slr/REDBOOK_ALL_RULES_MASTER.json') as f:
    data = json.load(f)

# Get Id. rule (Section 4.1)
id_rule = data['all_rules_by_section']['section_4_1']
print(id_rule['rule_summary'])
```

### Find Forbidden Practices
```python
import json
with open('/home/user/slr/REDBOOK_ALL_RULES_MASTER.json') as f:
    data = json.load(f)

for practice in data['quick_reference']['forbidden_practices']:
    print(f"{practice['practice']} - {practice['note']}")
```

---

## 📖 Source Files

### Original Redbook HTML Files
Location: `/home/user/slr/reference_files/redbook_processed/`
- 127 HTML files (rb_01__preamble.html through rb_128__2211-doctrine-of-patently-asinine-results.html)
- Index: `/home/user/slr/reference_files/redbook_processed/index.html`

### Extraction Script
Location: `/home/user/slr/extract_redbook_enhanced.py`
- Can be re-run if Redbook is updated
- Automatically extracts red-marked deviations
- Generates regex patterns

---

## 🎓 Rule Hierarchy (From Preamble)

When citing at Stanford Law Review, follow this order:

1. **Redbook (RB)** ← **CHECK FIRST** ← **TAKES PRECEDENCE**
2. **Bluebook (BB)** ← If not in Redbook
3. **Chicago Manual of Style (CMOS)** ← If not in Bluebook
4. **Merriam-Webster** ← Last resort

**Critical**: Redbook sometimes CONTRADICTS Bluebook. Always check Redbook first!

---

## 💡 Common Use Cases

### Case 1: Validating a Citation
1. Check **REDBOOK_QUICK_REFERENCE.md** for forbidden practices
2. Look up relevant section in **REDBOOK_ALL_RULES_MASTER.json**
3. Use regex patterns to validate format
4. Check correct/incorrect examples

### Case 2: Handling Bluebook Conflict
1. Search for section in **REDBOOK_ALL_RULES_MASTER.json**
2. Check `deviations_from_bluebook` array
3. If red-marked deviation, Redbook takes precedence
4. Use Redbook rule explicitly

### Case 3: Automated Validation
1. Load **REDBOOK_ALL_RULES_MASTER.json**
2. Extract regex patterns from relevant sections
3. Apply patterns to citations
4. Flag violations based on severity

### Case 4: Training New Editors
1. Start with **REDBOOK_QUICK_REFERENCE.md**
2. Memorize forbidden practices
3. Learn critical deviations (19 red-marked)
4. Reference full rules as needed

---

## 🔗 Related Resources

### In This Repository
- `/home/user/slr/reference_files/Bluebook.json` - Bluebook rules (separate)
- `/home/user/slr/reference_files/r1_handbook_summary.md` - Additional documentation

### External
- Original Redbook: Stanford Law Review, Volume 78
- Bluebook: https://www.legalbluebook.com
- Chicago Manual of Style: https://www.chicagomanualofstyle.org

---

## ✅ Verification

To verify extraction completeness:

```bash
# Check all source files present
ls /home/user/slr/reference_files/redbook_processed/rb_*.html | wc -l
# Should output: 127

# Verify JSON structure
python3 -c "import json; d=json.load(open('/home/user/slr/REDBOOK_ALL_RULES_MASTER.json')); print(f'Rules: {len(d[\"all_rules_by_section\"])}')"
# Should output: Rules: 127

# Check categorization
python3 -c "import json; d=json.load(open('/home/user/slr/REDBOOK_ALL_RULES_MASTER.json')); print(f'SLR: {len(d[\"slr_specific_rules\"])}, Dev: {len(d[\"bluebook_deviations\"])}, Clar: {len(d[\"clarifications\"])}')"
# Should output: SLR: 26, Dev: 12, Clar: 89
```

---

## 📝 Notes

- **Extraction Date**: 2025-11-23
- **Source**: Stanford Law Review Redbook, Volume 78 (edited by Volume 78 Managing Editors)
- **Format**: JSON (UTF-8), human-readable
- **Size**: 646 KB (compressed and deduplicated)
- **Quality**: All 127 sections verified, no duplicates

---

## 🆘 Support

If you need help:
1. Check **REDBOOK_EXTRACTION_README.md** for detailed documentation
2. Review **REDBOOK_QUICK_REFERENCE.md** for common rules
3. Search the JSON file for specific sections
4. Refer to original HTML files if interpretation needed

---

**This extraction is COMPLETE and COMPREHENSIVE.**
**Every single Redbook rule has been extracted and documented.**
**Red-marked deviations from Bluebook are clearly identified.**

---

**Last Updated**: 2025-11-23
**Status**: ✅ Complete and Verified
