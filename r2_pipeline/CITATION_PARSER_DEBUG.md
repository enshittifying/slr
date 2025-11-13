# Citation Parser Debug Request

## Overall R2 Pipeline Work Summary

### ✅ Completed Fixes

1. **Critical Bug Fixed: Mock Citations** (main.py:181-182)
   - **Issue**: Batches 14-16 were generating 100% mock citations due to accessing non-existent `parser.raw_citations` attribute
   - **Fix**: Removed problematic debug logging that tried to access undefined attribute
   - **Impact**: Word document extraction now works correctly for all batches

2. **NoneType Error Handling** (main.py:330-350)
   - **Issue**: 64/204 entries (31%) failing with `'NoneType' object has no attribute 'get'`
   - **Fix**: Added safe navigation and type checking for validation results
   - **Code**: Changed from direct access to `.get()` with fallbacks and validation
   - **Impact**: Pipeline no longer crashes on validation failures

3. **Citation Parser Improvements**
   - **Before**: 0/6 test cases passing, massive over-splitting (FN78 split into 10 instead of 3)
   - **After**: 3/7 test cases passing exactly, handles semicolons correctly
   - **Changes**:
     - Removed period-splitting (was breaking on URLs like "SellPoolSuppliesOnline.com")
     - Added Bluebook signal detection (*See*, *compare*, *with*, etc.)
     - Implemented regex-based pattern matching to ignore formatting marks
     - Added parentheses/quote protection to avoid splitting inside them

### 🔄 In Progress: Citation Parser

**Current Status: 3/7 passing (43%)**

### 📋 Still TODO (Lower Priority)

4. **Update Support Check Prompt** - Improve clarity on compound propositions and support by contrast
5. **Clean Up Citation Format Prompt** - Remove duplicate "CORE MANDATE" sections
6. **Add Batch Resume Capability** - Script to reprocess the 21 R1 files missing R2 counterparts

---

## Problem Statement (Citation Parser)

I'm building a legal citation parser for Stanford Law Review that needs to split footnotes into individual citations. The parser must handle Bluebook citation signals (like *See*, *compare*, *with*, etc.) while respecting parentheses, quotes, and formatting markers.

## Current Status

**Test Results: 3/7 passing (43%)**

```
✓ FN78: Expected 3, Got 3
✓ FN79: Expected 2, Got 2
✓ FN86: Expected 2, Got 2
❌ FN93: Expected 3, Got 4 (+1)    [over-splitting]
❌ FN108: Expected 8, Got 7 (-1)   [under-splitting]
❌ FN111: Expected 4, Got 3 (-1)   [under-splitting - 'with' not detected]
❌ FN113: Expected 7, Got 3 (-4)   [under-splitting]
```

## Key Requirements

### 1. Bluebook Signals (Rule 1.2)

Citations are separated by:
- **Semicolons** (when not inside parentheses/quotes)
- **Newlines** (when not inside parentheses/quotes)
- **Bluebook signals** (See, see also, But see, compare, with, cf., etc.)

**Complete hard-coded signal list** (Bluebook 22nd edition, Rule 1.2):

```python
SIGNALS = [
    # Supporting signals (Rule 1.2(a))
    # [no signal] - not applicable for splitting
    'see generally',   # Background materials (always last)
    'see also',        # Additional support (requires parenthetical)
    'see, e.g.,',      # Combined: inferential + example
    'see e.g.,',       # Variant without comma
    'e.g.,',           # Example
    'accord',          # Agreement
    'see',             # Inferential step
    'cf.',             # Compare by analogy (supportive per 1.2(a))

    # Comparison signals (Rule 1.2(b))
    'compare',         # Starts comparison (use with 'with')
    'with',            # ONLY valid after 'compare'

    # Contradictory signals (Rule 1.2(c))
    'but cf.',         # Analogically contradictory
    'but see',         # Clearly contradictory
    'contra',          # Directly contradictory

    # Variants
    'see e.g.',        # Alternative format
]
```

**Format note:** Per Bluebook 1.2(b), comparison citations follow: **"Compare A, with B, and C"**
- All signals, "with", and "and" are italicized
- Both "with" and "and" are preceded by commas

### 2. Special Rule: "compare...with"

Per Bluebook Rule 1.2(b), comparison citations use: **"Compare A, with B, and C"**

- `compare` starts the comparison
- `with` is ONLY a signal when used after `compare` (preceded by comma)
- `with` elsewhere (e.g., in quotes or narrative text) should be ignored

### 3. Formatting Markers

Citations use markdown notation:
- `*text*` = italic (e.g., `*See* Smith v. Jones`)
- Signals can be italic or plain text
- Formatting markers should be **ignored** when matching signals

## Current Implementation

```python
def _split_on_signals(self, text: str) -> List[str]:
    """
    Split a citation on Bluebook signals using regex.
    Signals like *See*, *see also*, *But see* indicate new citations.

    Special handling: 'with' is ONLY a signal when used after 'compare'
    (Bluebook Rule 1.2(b): "Compare A, with B, and C")

    Using regex ignores formatting marks (*) when matching signals.
    """
    import re

    # Build regex patterns for each signal (ignoring asterisks)
    signal_patterns = []
    for signal in self.SIGNALS:
        if signal == 'with':
            # 'with' only valid after comma (as in "compare A, with B")
            # Pattern: comma, optional whitespace, optional *, "with", optional *, space or *
            pattern = r',\s*\*?' + re.escape(signal) + r'\*?(?=\s|\*|$)'
        elif signal == 'compare':
            # 'compare' starts comparison
            pattern = r'(?:^|\s)\*?' + re.escape(signal) + r'\*?(?=\s|\*|$)'
        else:
            # Other signals: at start or after whitespace
            pattern = r'(?:^|\s)\*?' + re.escape(signal) + r'\*?(?=\s|\*|$)'

        signal_patterns.append((signal, re.compile(pattern, re.IGNORECASE)))

    # Track parentheses and quotes to avoid splitting inside them
    def get_paren_quote_regions(text):
        """Return list of (start, end) tuples for text inside parens/quotes."""
        regions = []
        paren_depth = 0
        in_quotes = False
        region_start = None

        QUOTE_CHARS = {'"', "'", '\u201c', '\u201d', '\u2018', '\u2019'}

        for i, char in enumerate(text):
            if not in_quotes:
                if char == '(':
                    if paren_depth == 0:
                        region_start = i
                    paren_depth += 1
                elif char == ')':
                    paren_depth -= 1
                    if paren_depth == 0 and region_start is not None:
                        regions.append((region_start, i+1))
                        region_start = None
                elif char in QUOTE_CHARS:
                    in_quotes = True
                    region_start = i
            else:
                if char in QUOTE_CHARS:
                    in_quotes = False
                    if region_start is not None:
                        regions.append((region_start, i+1))
                        region_start = None

        return regions

    # Find all protected regions
    protected_regions = get_paren_quote_regions(text)

    def is_in_protected_region(pos):
        """Check if position is inside parentheses or quotes."""
        for start, end in protected_regions:
            if start <= pos < end:
                return True
        return False

    # Find all signal matches
    matches = []

    for signal, pattern in signal_patterns:
        for match in pattern.finditer(text):
            start_pos = match.start()

            # Skip if inside parentheses or quotes
            if is_in_protected_region(start_pos):
                continue

            # Special handling for 'with' - only valid after 'compare'
            if signal == 'with':
                # Check if we've seen 'compare' before this position
                has_compare_before = any(
                    m[1] == 'compare' and m[0] < start_pos
                    for m in matches
                )
                if not has_compare_before:
                    continue

            matches.append((start_pos, signal, match.group()))

    # Sort matches by position
    matches.sort(key=lambda x: x[0])

    # Split text at signal positions
    if not matches:
        return [text] if text.strip() else []

    citations = []
    last_pos = 0

    for start_pos, signal, matched_text in matches:
        # Add text before this signal as a citation
        if start_pos > last_pos:
            before_text = text[last_pos:start_pos].strip()
            if before_text:
                citations.append(before_text)

        # Start new citation from this signal
        last_pos = start_pos

    # Add remaining text
    if last_pos < len(text):
        remaining = text[last_pos:].strip()
        if remaining:
            citations.append(remaining)

    return citations if citations else [text]
```

## Failing Test Case: FN111

**Expected: 4 citations**
**Got: 3 citations**

### FN111 Text (simplified):

```
Real World Media LLC v. Daily Caller, Inc., 744 F. Supp. 3d 24, 40 (D.D.C. 2024) (stating that there is a "nascent district-court split"...);

Doe 1 v. GitHub, Inc., No. 22-CV-06823-JST, 2024 WL 4336532, at *2 (N.D. Cal. Sept. 27, 2024) (referring to disagreement...);

*compare *Nimmer On Copyright, *supra* note 25 § 12A.10(C)(1) ("[T]o be actionable...'" (quoting O'Neal v.Sideshow, 583 F.Supp. 3d. 1282, 1287 (C.D. Cal. 2022)))*, with* Goldstein On Copyright at § 7.18 ("As a rule, the works must be identical...").
```

### Key Issue: The "with" at position 1043

Character analysis around position 1043:
```
[1040]: '*' = '*'
[1041]: ',' = ','
[1042]: ' ' = ' '
[1043]: 'w' = 'w'    <- 'with' starts here
[1044]: 'i' = 'i'
[1045]: 't' = 't'
[1046]: 'h' = 'h'
[1047]: '*' = '*'
[1048]: ' ' = ' '
```

The exact text is: `...2022)))*, with* Goldstein...`

**Problem:** The `with` signal is NOT being detected and split, resulting in only 3 citations instead of 4.

The regex pattern for "with" is:
```python
pattern = r',\s*\*?' + re.escape(signal) + r'\*?(?=\s|\*|$)'
```

Which should match: `, with*`

### Questions for Debugging

1. **Is the regex pattern correct?** Should it match `, *with*` (with asterisk before "with")?

2. **Is the protected region detection failing?** Could the parentheses from `(C.D. Cal. 2022)))` be incorrectly marking the "with" as protected?

3. **Is the "compare" detection working?** The code checks if "compare" appears before "with", but is it finding the `*compare *` at the start of citation 3?

4. **Should the pattern handle**: `, *with*` where the asterisk is part of the italic formatting around "with"?

## Test Data

The parser is tested against real footnote text from Stanford Law Review. Here are the test expectations:

```python
expected_counts = {
    78: 3,   # ✓ PASSING
    79: 2,   # ✓ PASSING
    86: 2,   # ✓ PASSING
    93: 3,   # ❌ Getting 4 (over-splitting)
    108: 8,  # ❌ Getting 7 (under-splitting)
    111: 4,  # ❌ Getting 3 (under-splitting)
    113: 7,  # ❌ Getting 3 (under-splitting)
}
```

## What I Need

**Please help me fix the regex-based signal detection to:**

1. Correctly detect `*, with*` as a signal split point (FN111)
2. Handle all Bluebook signals regardless of italic formatting (`*signal*` vs plain `signal`)
3. Not split on "with" when it appears without "compare" before it
4. Respect parentheses and quotes (don't split inside them)
5. Handle both semicolons and signals as split points

**The goal is to get 7/7 tests passing with exact citation counts.**

## Additional Context

- Text uses markdown: `*italic*`, `**bold**`, `[SC]small caps[/SC]`
- Footnotes also split on semicolons (handled in separate method, working correctly)
- This `_split_on_signals()` method is called AFTER semicolon splitting
- The full citation parser code is at: `/Users/ben/app/slrapp/r2_pipeline/src/citation_parser.py`

---

**Can you identify the bug(s) in the regex patterns or the signal detection logic and provide a corrected implementation?**
