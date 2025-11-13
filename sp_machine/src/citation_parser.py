"""
Parse footnotes from Word doc and structure citation data.
Uses regex and heuristics to identify citation components.
"""
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
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
    error_messages: List[str] = None
    
    def __post_init__(self):
        if self.error_messages is None:
            self.error_messages = []

class CitationParser:
    """Parse citations from footnote text."""
    
    # Common Bluebook signals
    SIGNALS = [
        'see', 'see also', 'see generally', 'cf.', 'compare',
        'with',
        'accord', 'see, e.g.,', 'e.g.,', 'contra', 'but see', 'but cf.'
    ]
    
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
        Handles semicolons, but preserves them within parentheticals.
        """
        citations = []
        current = ""
        paren_depth = 0
        
        for char in text:
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            elif char == ';' and paren_depth == 0:
                if current.strip():
                    citations.append(current.strip())
                current = ""
                continue
            
            current += char
        
        # Add last citation
        if current.strip():
            citations.append(current.strip())
        
        return citations
    
    def _parse_single_citation(self, text: str, citation_num: int) -> Citation:
        """Parse a single citation into structured components."""
        
        citation_type = self._detect_type(text)

        citation = Citation(
            footnote_num=self.footnote_num,
            citation_num=citation_num,
            full_text=text,
            type=citation_type
        )
        
        # Detect citation type
        citation.type = citation_type
        
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
        # This is simplified - full parsing is complex
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
