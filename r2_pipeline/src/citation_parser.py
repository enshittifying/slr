"""
Parse footnotes from Word doc and structure citation data.
Uses regex and heuristics to identify citation components.
"""
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class Citation:
    """Structured representation of a citation."""
    footnote_num: int
    citation_num: int  # Position within footnote (1st, 2nd, etc.)
    full_text: str
    type: str  # 'case', 'article', 'statute', 'book', 'supra', 'id', 'infra'

    # Citation components (filled based on type)
    case_name: Optional[str] = None
    reporter: Optional[str] = None
    pinpoint: Optional[str] = None
    court: Optional[str] = None
    year: Optional[str] = None

    author: Optional[str] = None
    title: Optional[str] = None
    journal: Optional[str] = None
    volume: Optional[str] = None
    start_page: Optional[str] = None

    statute_code: Optional[str] = None
    section: Optional[str] = None

    signal: Optional[str] = None  # See, see also, cf., etc.
    parenthetical: Optional[str] = None
    quoted_text: Optional[str] = None

    # Validation flags
    has_errors: bool = False
    error_messages: List[str] = field(default_factory=list)

class CitationParser:
    """Parse citations from footnote text."""

    # Bluebook signals (Rule 1.2) - Complete hard-coded list from Bluebook 22nd edition
    # Order: Supporting -> Comparison -> Contradictory -> Background
    SIGNALS = [
        # Supporting signals (Rule 1.2(a)) - in order of precedence
        # [no signal] - not applicable for splitting, citation directly states proposition
        'see generally',   # Background materials (always last if used)
        'see also',        # Additional support (requires explanatory parenthetical)
        'see, e.g.,',      # Combined: inferential step + example
        'see e.g.,',       # Variant without comma after "see"
        'e.g.,',           # Example (when other citations would be unhelpful)
        'accord',          # Agreement with proposition
        'see',             # Inferential step between proposition and cited authority
        'cf.',             # Compare by analogy (classified as supportive per Rule 1.2(a))

        # Comparison signals (Rule 1.2(b))
        # Format: "Compare A, with B, and C" per Bluebook Rule 1.2(b)
        'compare',         # Starts comparison (must be used with 'with')
        'with',            # Continues comparison (ONLY valid after 'compare')

        # Contradictory signals (Rule 1.2(c))
        'but cf.',         # Analogically contradictory
        'but see',         # Clearly contradictory
        'contra',          # Directly contradictory (opposite of [no signal])

        # Additional variants that may appear
        'see e.g.',        # Alternative format for see, e.g.,
    ]

    # Note: "and" is also italicized in "Compare A, with B, and C" but we don't split on it
    # as it's part of the list structure, not a separate citation

    # Reporter patterns
    REPORTER_PATTERN = r'\d+\s+(?:U\.S\.|S\.\s*Ct\.|L\.\s*Ed\.|F\.\s*Supp\.|F\.\s*3d|F\.\s*2d|F\.\s*4th|F\.\s*App\'x)\s+\d+'

    # Statute patterns
    STATUTE_PATTERN = r'\d+\s+U\.S\.C\.\s+§\s*\d+'

    def __init__(self, footnote_text: str, footnote_num: int):
        self.footnote_text = footnote_text
        self.footnote_num = footnote_num
        self.citations = []

    def parse(self) -> List[Citation]:
        """
        Main parsing method.
        Splits footnote into individual citations and parses each.
        """
        # Split on semicolons (typical citation separator)
        raw_citations = self._split_citations(self.footnote_text)

        for idx, raw_cit in enumerate(raw_citations, start=1):
            citation = self._parse_single_citation(raw_cit, idx)
            self.citations.append(citation)

        return self.citations

    def _split_citations(self, text: str) -> List[str]:
        """
        Split footnote into individual citations.

        Citations are separated by:
        1. Semicolons (when not inside parens/quotes) - traditional citation strings
        2. Newlines (when not inside parens/quotes)
        3. Bluebook signals (See, see also, But see, etc.) at the start of a new citation
        4. Sentence boundaries in narrative footnotes (e.g., ". See [case]", ". Id.")

        We do NOT split on periods in:
        - URLs (e.g., "SellPoolSuppliesOnline.com")
        - Abbreviations (e.g., "Inc.", "v.", "Tel.")
        - Reporter citations (e.g., "F. Supp.")

        Narrative footnotes: Multiple sentences with citations after each sentence.
        Example: "One court did X. See Case1. Another court did Y. See Case2."
        """
        # Check if this is a narrative footnote (no semicolons, multiple sentences with citations)
        if self._is_narrative_footnote(text):
            return self._split_narrative_footnote(text)
        # First, do a simple split on semicolons and newlines
        # Use apostrophe-aware quote detection (same as signal splitting)
        citations = []
        current = ""
        paren_depth = 0
        in_dq = False  # double quotes
        in_sq = False  # single quotes

        def is_apostrophe(i: int) -> bool:
            """Check if character at position i is an apostrophe (between letters)."""
            return (0 < i < len(text) - 1) and text[i-1].isalnum() and text[i+1].isalnum()

        i = 0
        while i < len(text):
            char = text[i]

            # Handle parentheses (only when not in quotes)
            if not in_dq and not in_sq:
                if char == '(':
                    paren_depth += 1
                elif char == ')':
                    paren_depth = max(0, paren_depth - 1)

            # Handle quotes with apostrophe detection
            if char in ('"', '\u201c', '\u201d'):
                if in_dq:
                    if char in ('"', '\u201d'):  # closing
                        in_dq = False
                else:
                    if char in ('"', '\u201c'):  # opening
                        in_dq = True
            elif char in ("'", '\u2018', '\u2019'):
                # Skip if apostrophe (like O'Neal)
                if char == "'" and is_apostrophe(i):
                    current += char
                    i += 1
                    continue
                if in_sq:
                    if char in ("'", '\u2019'):  # closing
                        in_sq = False
                else:
                    if char in ("'", '\u2018'):  # opening
                        in_sq = True

            # Check for citation separator: semicolons OR newlines
            if (char == ';' or char == '\n') and paren_depth == 0 and not in_dq and not in_sq:
                if current.strip():
                    citations.append(current.strip())
                current = ""
                i += 1
                # Skip whitespace after separator
                while i < len(text) and text[i] in ' \t\n\r':
                    i += 1
                continue

            current += char
            i += 1

        # Add last citation
        if current.strip():
            citations.append(current.strip())

        # Second pass: merge supplemental supra references back with previous citation
        merged_citations = []
        for i, citation in enumerate(citations):
            # Check if this is a supplemental cross-reference that should stay with previous
            if i > 0 and self._is_supplemental_reference(citation):
                # Merge with previous citation
                if merged_citations:
                    merged_citations[-1] = merged_citations[-1] + "; " + citation
                else:
                    merged_citations.append(citation)
            else:
                merged_citations.append(citation)

        # Third pass: split on signals within citations
        final_citations = []
        for citation in merged_citations:
            split_by_signals = self._split_on_signals(citation)
            final_citations.extend(split_by_signals)

        return final_citations if final_citations else [text]

    def _split_on_signals(self, text: str) -> List[str]:
        """
        Split a citation on Bluebook signals using regex.
        Signals like *See*, *see also*, *But see* indicate new citations.

        Special handling: 'with' is ONLY a signal when used after 'compare'
        (Bluebook Rule 1.2(b): "Compare A, with B, and C")

        Using regex ignores formatting marks (*) when matching signals.
        """
        import re

        # --- Build robust, italics/punctuation-tolerant patterns ---
        # We capture the SIGNAL WORD in a named group (?P<sig>...) so we can split at the word, not at the prefix.
        def compile_signal_patterns():
            pats = []
            for sig in self.SIGNALS:
                if sig == 'with':
                    # Require a preceding comma, but start split at 'with' (group 'sig'), not at the comma.
                    pattern = r',\s*\*?(?P<sig>' + re.escape('with') + r')\*?(?=[\s\*,;:\)]|$)'
                elif sig == 'compare':
                    # Allow BOS/space/paren before, italics around the word, and punctuation/space after.
                    pattern = r'(^|\s|\()\*?(?P<sig>' + re.escape('compare') + r')\*?(?=[\s\*,;:\)]|$)'
                else:
                    # Generic signals (e.g., 'see also', 'but cf.', 'cf.', 'e.g.,', 'see, e.g.,')
                    pattern = r'(^|\s|\()\*?(?P<sig>' + re.escape(sig) + r')\*?(?=[\s\*,;:\)]|$)'
                pats.append((sig, re.compile(pattern, re.IGNORECASE)))
            return pats

        signal_patterns = compile_signal_patterns()

        # Track parentheses and quotes to avoid splitting inside them
        def get_paren_quote_regions(txt: str):
            """
            Return (start, end) spans to protect (parentheses and *true* quoted regions).
            IMPORTANT: do NOT treat apostrophes inside words (e.g., O'Neal) as quote delimiters.
            """
            regions = []
            paren_depth = 0
            paren_start = None
            in_dq = False; dq_start = None          # " … "  or " … "
            in_sq = False; sq_start = None          # ' … '  or ' … '

            def is_apostrophe(i: int) -> bool:
                return (0 < i < len(txt) - 1) and txt[i-1].isalnum() and txt[i+1].isalnum()

            for i, ch in enumerate(txt):
                # parentheses (only when not inside quotes)
                if not in_dq and not in_sq:
                    if ch == '(':
                        if paren_depth == 0:
                            paren_start = i
                        paren_depth += 1
                    elif ch == ')':
                        if paren_depth > 0:
                            paren_depth -= 1
                            if paren_depth == 0 and paren_start is not None:
                                regions.append((paren_start, i + 1))
                                paren_start = None

                # double quotes (straight or curly)
                if ch in ('"', '\u201c', '\u201d'):
                    if in_dq:
                        if ch in ('"', '\u201d'):   # closing
                            in_dq = False
                            regions.append((dq_start, i + 1))
                            dq_start = None
                    else:
                        if ch in ('"', '\u201c'):   # opening
                            in_dq = True
                            dq_start = i
                    continue

                # single quotes (straight or curly) — ignore apostrophes between letters
                if ch in ("'", '\u2018', '\u2019'):
                    if ch == "'" and is_apostrophe(i):
                        continue  # treat as apostrophe, not a quote delimiter
                    if in_sq:
                        if ch in ("'", '\u2019'):   # closing
                            in_sq = False
                            regions.append((sq_start, i + 1))
                            sq_start = None
                    else:
                        if ch in ("'", '\u2018'):   # opening
                            in_sq = True
                            sq_start = i

            return regions

        # Find all protected regions
        protected_regions = get_paren_quote_regions(text)

        def is_in_protected_region(pos):
            """Check if position is inside parentheses or quotes."""
            for start, end in protected_regions:
                if start <= pos < end:
                    return True
            return False

        # Collect candidate matches with the start at the signal word
        candidates = []
        for signal, pattern in signal_patterns:
            for match in pattern.finditer(text):
                # Split after group 1 (whitespace/paren) to preserve any leading formatting like *
                # This ensures *See becomes part of the new citation, not left behind
                sig_start = match.end(1)  # Position after leading whitespace/paren, before *
                sig_end   = match.end()    # End of full match including trailing *

                # Skip if inside parentheses or quotes
                if is_in_protected_region(sig_start):
                    continue

                # Special handling for 'with' - only valid after 'compare'
                if signal == 'with':
                    # must have a preceding 'compare' in the same chunk with no semicolon between
                    prior_compare = None
                    for m2 in signal_patterns:
                        if m2[0] == 'compare':
                            for mc in m2[1].finditer(text[:sig_start]):
                                c_start = mc.start('sig')
                                if not is_in_protected_region(c_start):
                                    prior_compare = mc
                    if not prior_compare:
                        continue
                    if ';' in text[prior_compare.end():sig_start]:
                        continue

                candidates.append((sig_start, sig_end, signal))

        # De-duplicate overlaps: prefer the longest signal at a given start (e.g., 'see also' over 'see')
        candidates.sort(key=lambda t: (t[0], -(t[1]-t[0])))
        matches = []
        last_end = -1
        for s, e, sig in candidates:
            if s >= last_end:
                matches.append((s, e, sig))
                last_end = e

        # Split text at signal positions
        if not matches:
            return [text] if text.strip() else []

        citations = []
        last_pos = 0

        for start_pos, end_pos, signal in matches:
            # Add text before this signal as a citation
            if start_pos > last_pos:
                before_text = text[last_pos:start_pos].strip()
                # Filter out garbage (just formatting marks, no actual content)
                if before_text and not self._is_just_formatting(before_text):
                    citations.append(before_text)

            # Start new citation from the signal word itself
            last_pos = start_pos

        # Add remaining text
        if last_pos < len(text):
            remaining = text[last_pos:].strip()
            if remaining and not self._is_just_formatting(remaining):
                citations.append(remaining)

        return citations if citations else [text]

    def _is_just_formatting(self, text: str) -> bool:
        """
        Check if text is just formatting marks with no actual content.
        Returns True if text contains only: *, whitespace, commas, semicolons, etc.
        """
        # Remove all formatting characters
        cleaned = text.strip('*_~`\'" \t\n\r,;:')
        return len(cleaned) == 0

    def _is_supplemental_reference(self, text: str) -> bool:
        """
        Check if text is a supplemental cross-reference that should stay with previous citation.

        Patterns:
        - "supra notes X-Y and accompanying text"
        - "infra notes X-Y"
        - Other cross-references without case names or reporters
        """
        import re

        # Remove markdown formatting before checking
        text_clean = re.sub(r'[\*_]', '', text).lower().strip()

        # Pattern 1: supra/infra notes X-Y and accompanying text
        if re.match(r'(supra|infra)\s+notes?\s+\d+', text_clean):
            return True

        # Pattern 2: Just supra/infra without a full citation
        # (has supra/infra but no reporter citation)
        if text_clean.startswith(('supra', 'infra')):
            # Check if it has a reporter (indicates it's a full citation)
            has_reporter = re.search(self.REPORTER_PATTERN, text)
            if not has_reporter:
                return True

        return False

    def _is_narrative_footnote(self, text: str) -> bool:
        """
        Detect if this is a narrative footnote.

        Key distinction: Narrative footnotes START with prose/analysis,
        then citations appear. Normal citation strings START with citations.

        Example narrative: "A court held X. See Case1. Another court held Y. See Case2."
        Example normal: "*See* Case1; Case2; *see also* Case3."
        """
        import re

        # Must have multiple sentences (at least 3 periods that look like sentence boundaries)
        # This filters out normal citations which have periods in abbreviations
        # Pattern: period, space, capital letter followed by lowercase (not abbreviations like "L. Rev.")
        sentence_boundaries = re.findall(r'\.\s+[A-Z][a-z]', text)
        if len(sentence_boundaries) < 3:
            return False

        # Should not have semicolons (traditional citation format uses semicolons)
        # Allow at most 1 semicolon (might be inside a parenthetical or quote)
        semicolon_count = text.count(';')
        if semicolon_count > 1:
            return False

        # Key test: Check first ~150 characters for citation patterns
        # If citation appears at start, it's NOT a narrative footnote
        start_text = text[:150].lower()

        # If starts with signal, it's a traditional citation string
        if any(start_text.strip().startswith(sig.lower()) for sig in self.SIGNALS):
            return False

        # If starts with case name pattern (within first 50 chars), it's traditional
        if re.match(r'^[A-Z][a-zA-Z\.\s&-]+\s+v\.\s+[A-Z]', text[:50]):
            return False

        # If starts with Id., it's traditional
        if start_text.strip().startswith('id.'):
            return False

        # Narrative footnotes have substantial prose before first citation
        # Check if there's at least 50 characters before first reporter/signal/v.
        first_signal_pos = min(
            [text.lower().find(sig.lower()) for sig in [' see ', ' id.', ' cf.', 'supra']
             if sig.lower() in text.lower()] + [9999]
        )
        first_case_match = re.search(r'\bv\.\s+[A-Z]', text)
        first_case_pos = first_case_match.start() if first_case_match else 9999
        first_reporter_match = re.search(self.REPORTER_PATTERN, text)
        first_reporter_pos = first_reporter_match.start() if first_reporter_match else 9999

        first_citation_pos = min(first_signal_pos, first_case_pos, first_reporter_pos)

        # If first citation is very early (< 50 chars), it's traditional
        # If first citation is later (> 50 chars), it's narrative
        return first_citation_pos > 50

    def _split_narrative_footnote(self, text: str) -> List[str]:
        """
        Split a narrative footnote into chunks of (prose + citation).

        Pattern: Intro. Analysis sentence. Citation sentence. Another analysis. Another citation.

        We want: [Prose1 + Citation1, Prose2 + Citation2, Prose3 + Citation3, ...]

        Each chunk includes the narrative context sentence before its citation.
        """
        import re

        citations = []
        current = ""
        i = 0
        seen_first_citation = False
        start_accumulating = False  # Only start after we've seen citation pattern once

        # Check if period is part of an abbreviation
        def is_abbreviation_period(pos):
            # Pattern 1: Single capital letter + period (N., F., etc.)
            if pos > 0 and text[pos-1].isupper():
                return True

            # Pattern 2: Common multi-letter abbreviations
            lookback = text[max(0, pos-15):pos+1].lower()
            common_abbrs = [
                'inc.', 'corp.', 'ltd.', 'supp.', 'cir.', 'libr.', 'rsch.', 'info.',
                'cal.', 'fla.', 'ill.', 'mass.', 'mich.', 'wash.', 'tex.', 'jan.', 'feb.', 'mar.',
                'apr.', 'aug.', 'sept.', 'oct.', 'nov.', 'dec.', 'educ.', 'est.', 'auto.', 'tel.'
            ]
            for abbr in common_abbrs:
                if lookback.endswith(abbr):
                    return True

            # Pattern 3: "v." (versus) - very common in case names
            if lookback.endswith('v.'):
                return True

            return False

        # Check if we're at the start of a citation
        def is_citation_start(txt):
            txt_lower = txt.lower().strip()

            # Pattern 1: Starts with a signal or Id.
            for sig in self.SIGNALS + ['Id.', 'id.']:
                if txt_lower.startswith(sig.lower()):
                    return True

            # Pattern 2: Starts with case name pattern (e.g., "Sanborn Libr. LLC v. ERIS")
            if re.match(r'^[A-Z][a-z]+[a-zA-Z\.\s&-]*?\s+v\.\s+[A-Z]', txt.strip()):
                return True

            # Pattern 3: Short form citation (Case Name, Year WL...)
            # e.g., "Say It Visually, 2025 WL 933951"
            if re.match(r'^[A-Z][a-zA-Z\.\s&-]+,\s+\d{4}\s+WL\s+\d+', txt.strip()):
                return True

            # Pattern 4: Standalone "Id." (very common)
            if txt_lower.strip() == 'id.' or txt_lower.strip().startswith('id.'):
                return True

            return False

        while i < len(text):
            char = text[i]
            current += char

            # Check if we just added a period (potential sentence boundary)
            if char == '.':
                # Skip if this is an abbreviation period
                if is_abbreviation_period(i):
                    i += 1
                    continue

                # Look ahead
                remaining = text[i+1:].lstrip()

                # Check if next sentence is a citation
                next_is_citation = is_citation_start(remaining)

                # If we see a citation starting
                if next_is_citation:
                    if not start_accumulating:
                        # First citation ever - discard intro prose, start fresh
                        start_accumulating = True
                        seen_first_citation = True
                        current = ""
                        i += 1
                        continue
                    else:
                        # Another citation after we've started
                        seen_first_citation = True
                        # Continue accumulating - don't split yet
                        i += 1
                        continue

                # If we just finished a citation and next is NOT a citation
                # (i.e., next is prose), that's where we split
                if seen_first_citation and not next_is_citation and start_accumulating:
                    # Save the chunk (prose + citation) including the period
                    chunk = current.strip()
                    if chunk and not self._is_just_formatting(chunk):
                        citations.append(chunk)
                    current = ""
                    seen_first_citation = False
                    i += 1
                    continue

            i += 1

        # Add remaining text (if we've started accumulating)
        if start_accumulating and current.strip() and not self._is_just_formatting(current.strip()):
            citations.append(current.strip())

        return citations if citations else [text]

    def _parse_single_citation(self, text: str, citation_num: int) -> Citation:
        """Parse a single citation into structured components."""

        citation = Citation(
            footnote_num=self.footnote_num,
            citation_num=citation_num,
            full_text=text,
            type="unknown"
        )

        # Detect citation type
        citation.type = self._detect_type(text)

        # Extract signal if present
        citation.signal = self._extract_signal(text)

        # Extract quoted text if present
        citation.quoted_text = self._extract_quotes(text)

        # Extract parenthetical if present
        citation.parenthetical = self._extract_parenthetical(text)

        # Type-specific parsing
        if citation.type == 'case':
            self._parse_case(citation, text)
        elif citation.type == 'article':
            self._parse_article(citation, text)
        elif citation.type == 'statute':
            self._parse_statute(citation, text)
        elif citation.type in ['supra', 'id', 'infra']:
            self._parse_short_form(citation, text)

        return citation

    def _detect_type(self, text: str) -> str:
        """Detect the type of citation."""
        text_lower = text.lower()

        if text_lower.strip().startswith('id'):
            return 'id'
        elif 'supra note' in text_lower or 'supra at' in text_lower:
            return 'supra'
        elif 'infra' in text_lower:
            return 'infra'
        elif re.search(self.STATUTE_PATTERN, text):
            return 'statute'
        elif re.search(self.REPORTER_PATTERN, text):
            return 'case'
        elif re.search(r'\d+\s+\w+\.\s+L\.\s+Rev\.', text):
            return 'article'
        else:
            return 'unknown'

    def _extract_signal(self, text: str) -> Optional[str]:
        """Extract Bluebook signal from citation."""
        text_start = text.lower().strip()[:30]

        for signal in self.SIGNALS:
            if text_start.startswith(signal.lower()):
                return signal

        return None

    def _extract_quotes(self, text: str) -> Optional[str]:
        """Extract quoted text from citation."""
        # Find text within quotes
        matches = re.findall(r'"([^"]*)"', text)
        if matches:
            return matches[0]
        return None

    def _extract_parenthetical(self, text: str) -> Optional[str]:
        """Extract parenthetical explanation."""
        # Find the last parenthetical (usually the explanatory one)
        matches = re.findall(r'\(([^)]+)\)(?!.*\()', text)
        if matches:
            return matches[-1]
        return None

    def _parse_case(self, citation: Citation, text: str):
        """Parse case citation components."""
        # Extract case name (usually italicized, before reporter)
        case_match = re.search(r'^(?:See\s+)?([^,]+)\s+v\.\s+([^,]+)', text, re.IGNORECASE)
        if case_match:
            citation.case_name = f"{case_match.group(1).strip()} v. {case_match.group(2).strip()}"

        # Extract reporter
        reporter_match = re.search(self.REPORTER_PATTERN, text)
        if reporter_match:
            citation.reporter = reporter_match.group(0)

        # Extract pinpoint (page after reporter)
        pinpoint_match = re.search(r'(\d+)\s+(?:U\.S\.|F\.\s*(?:Supp\.|3d|2d|4th|App\'x))\s+(\d+),\s*(\d+)', text)
        if pinpoint_match:
            citation.pinpoint = pinpoint_match.group(3)

        # Extract court and year
        court_year_match = re.search(r'\(([^)]+)\s+(\d{4})\)', text)
        if court_year_match:
            citation.court = court_year_match.group(1)
            citation.year = court_year_match.group(2)

    def _parse_article(self, citation: Citation, text: str):
        """Parse article citation components."""
        # Extract author (before comma)
        author_match = re.search(r'^(?:See\s+)?([^,]+),', text)
        if author_match:
            citation.author = author_match.group(1).strip()

        # Extract volume and start page
        vol_page_match = re.search(r'(\d+)\s+([A-Za-z\.\s&]+)\s+(\d+)', text)
        if vol_page_match:
            citation.volume = vol_page_match.group(1)
            citation.journal = vol_page_match.group(2).strip()
            citation.start_page = vol_page_match.group(3)

        # Extract year
        year_match = re.search(r'\((\d{4})\)', text)
        if year_match:
            citation.year = year_match.group(1)

    def _parse_statute(self, citation: Citation, text: str):
        """Parse statute citation components."""
        statute_match = re.search(r'(\d+)\s+U\.S\.C\.\s+§\s*(\d+[a-z]?(?:\(\w+\))?)', text)
        if statute_match:
            citation.statute_code = statute_match.group(1) + " U.S.C."
            citation.section = "§ " + statute_match.group(2)

        # Extract year
        year_match = re.search(r'\((\d{4})\)', text)
        if year_match:
            citation.year = year_match.group(1)

    def _parse_short_form(self, citation: Citation, text: str):
        """Parse short form citations (supra, id, infra)."""
        if citation.type == 'supra':
            note_match = re.search(r'supra note\s+(\d+)', text, re.IGNORECASE)
            if note_match:
                citation.parenthetical = f"note {note_match.group(1)}"

            # Extract pinpoint
            at_match = re.search(r'at\s+(\d+)', text)
            if at_match:
                citation.pinpoint = at_match.group(1)

        elif citation.type == 'infra':
            # Similar parsing for infra
            pass
