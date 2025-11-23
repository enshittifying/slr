# Quick Reference: RB 1.12 Critical Fix

## THE RULE (CORRECTED)

**"See generally" citations REQUIRE an explanatory parenthetical.**

If a "see generally" citation lacks a parenthetical, leave an [AA:] Comment:
```
[AA:] Add explanatory parenthetical required for 'see generally' signal
```

**"Cf." citations should NOT include explanatory parentheticals.**

---

## DETECTION PATTERNS

### Pattern 1: See Generally Without Parenthetical (ERROR)
```regex
See generally\s+[^(]+\.\s*$
```

Detects citations like:
```
See generally RICHARD POSNER, ECONOMIC ANALYSIS OF LAW (9th ed. 2014).
```

### Pattern 2: Cf. With Parenthetical (ERROR)
```regex
Cf\.\s+[^.]+\([^)]+\)\.
```

Detects citations like:
```
Cf. Brown v. Board, 347 U.S. 483 (1954) (holding segregation unconstitutional).
```

### Pattern 3: Validate See Generally Has Parenthetical
```regex
See generally\s+[^(]+\([^)]{10,}\)
```

Validates citations have substantive parenthetical (10+ characters).

---

## ERROR TYPES

### RB_1.12_E1: see_generally_missing_parenthetical
- **Severity:** ERROR
- **Auto-fix:** NO
- **Comment:** [AA:] Add explanatory parenthetical required for 'see generally' signal

**Example:**
```
❌ WRONG: See generally John Doe, Theory of Justice, 100 HARV. L. REV. 1 (2020).
✅ RIGHT: See generally John Doe, Theory of Justice, 100 HARV. L. REV. 1 (2020) (tracing historical development of distributive justice theories from Aristotle to Rawls).
```

### RB_1.12_E2: cf_has_parenthetical
- **Severity:** ERROR
- **Auto-fix:** YES

**Example:**
```
❌ WRONG: Cf. Brown v. Board, 347 U.S. 483 (1954) (holding segregation unconstitutional).
✅ RIGHT: Cf. Brown v. Board, 347 U.S. 483 (1954).
```

### RB_1.12_E3: see_generally_weak_parenthetical
- **Severity:** WARNING
- **Auto-fix:** NO

**Example:**
```
⚠️  WEAK: See generally Smith (2019) (discussing topic).
✅ RIGHT: See generally Smith (2019) (providing comprehensive historical analysis of constitutional interpretation from 1789 to present).
```

### RB_1.12_E4: see_generally_parenthetical_not_substantive
- **Severity:** WARNING
- **Auto-fix:** NO

**Example:**
```
⚠️  WEAK: See generally Brown (2020) (for background).
✅ RIGHT: See generally Brown (2020) (examining the evolution of Fourth Amendment jurisprudence and its application to modern surveillance technologies).
```

---

## COMPLETE EXAMPLES

### ❌ INCORRECT CITATIONS

1. **See Generally Without Parenthetical**
   ```
   See generally RICHARD POSNER, ECONOMIC ANALYSIS OF LAW (9th ed. 2014).
   ```
   **Action:** Add [AA:] comment requesting parenthetical

2. **See Generally Too Vague**
   ```
   See generally John Doe, Theory of Justice, 100 HARV. L. REV. 1 (2020) (discussing justice).
   ```
   **Action:** Request more substantive parenthetical

3. **Cf. With Parenthetical**
   ```
   Cf. Brown v. Board, 347 U.S. 483 (1954) (holding segregation unconstitutional).
   ```
   **Action:** Remove parenthetical (auto-fix: yes)

4. **See Generally in Citation String**
   ```
   See generally Smith (2019); Jones (2020); Brown (2021).
   ```
   **Action:** Each source needs its own parenthetical

5. **See Generally Generic Parenthetical**
   ```
   See generally Wilson (2018) (providing background information).
   ```
   **Action:** Require specific explanation of background content

### ✅ CORRECT CITATIONS

1. **See Generally With Substantive Parenthetical**
   ```
   See generally RICHARD POSNER, ECONOMIC ANALYSIS OF LAW (9th ed. 2014) (providing comprehensive economic framework for analyzing legal rules and demonstrating efficiency-based approach to tort, contract, and criminal law).
   ```

2. **See Generally Historical Context**
   ```
   See generally John Doe, Theory of Justice, 100 HARV. L. REV. 1 (2020) (tracing historical development of distributive justice theories from Aristotle through Rawls and examining modern applications to constitutional law).
   ```

3. **Cf. Without Parenthetical**
   ```
   Cf. Brown v. Board, 347 U.S. 483 (1954).
   ```

4. **See Generally With Individual Parentheticals**
   ```
   See generally Smith (2019) (analyzing original intent); Jones (2020) (examining legislative history); Brown (2021) (discussing modern applications).
   ```

5. **See Generally Specific Background**
   ```
   See generally Wilson, Historical Foundations of Fourth Amendment Doctrine, 95 YALE L.J. 1000 (2018) (examining evolution of privacy protections from common law trespass doctrine through modern surveillance jurisprudence).
   ```

---

## CHECKLIST FOR EDITORS

When you encounter "see generally":
- [ ] Does citation have a parenthetical?
- [ ] If NO parenthetical: Add [AA:] comment
- [ ] If YES parenthetical: Is it substantive (10+ words)?
- [ ] Does it explain WHY this is background material?
- [ ] Does it describe WHAT background the source provides?
- [ ] Is it specific enough to be useful to reader?

When you encounter "cf.":
- [ ] Does citation have a parenthetical?
- [ ] If YES: Remove it (auto-fix)
- [ ] If NO: Citation is correct

---

## WHY THIS MATTERS

**"See generally"** signals that a source provides background or context, NOT direct support. The parenthetical is REQUIRED because:
1. Reader needs to know WHY source is cited as background
2. Source doesn't directly support the proposition
3. Without parenthetical, reader can't evaluate relevance
4. Substantive explanation distinguishes from "See" (direct support)

**"Cf."** signals an analogous proposition that's clearly relevant. No parenthetical needed because:
1. The analogy should be self-evident from context
2. Adding explanation defeats the "compare" signal's purpose
3. Reader expected to draw the comparison themselves

---

## RELATED RULES

- **RB 1.11:** Grammar of Explanatory Parentheticals (how to write them)
- **RB 1.10:** Length of Explanatory Parentheticals (keep under 50 words)
- **RB 1.16:** Ordering of Parentheticals (where to place them)
- **BB 1.2:** Introductory Signals (Bluebook base rule)

---

**File Location:** `/home/user/slr/SLRinator/output/analysis/redbook_ALL_115_RULES_FIXED.json`
**Rule ID:** 1.12
**Critical Fix:** ✅ Applied
