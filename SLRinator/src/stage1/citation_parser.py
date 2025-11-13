"""
Citation Parser Module for Stanford Law Review
Parses and classifies legal citations according to Bluebook format
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CitationType(Enum):
    CASE = "case"
    STATUTE = "statute"
    REGULATION = "regulation"
    ARTICLE = "article"
    BOOK = "book"
    WEB = "web"
    TREATY = "treaty"
    LEGISLATIVE = "legislative"
    UNKNOWN = "unknown"


@dataclass
class CitationMetadata:
    """Stores parsed metadata from a citation"""
    authors: List[str] = field(default_factory=list)
    title: str = ""
    volume: str = ""
    reporter: str = ""
    page: str = ""
    pincite: str = ""
    year: str = ""
    court: str = ""
    url: str = ""
    access_date: str = ""
    publisher: str = ""
    edition: str = ""
    section: str = ""
    paragraph: str = ""
    database: str = ""
    docket_number: str = ""
    judge: str = ""
    parenthetical: str = ""
    signal: str = ""
    short_name: str = ""
    

class Citation:
    """Represents a parsed legal citation"""
    
    def __init__(self, raw_text: str, source_id: str, short_name: str = ""):
        self.raw_text = raw_text.strip()
        self.source_id = source_id
        self.short_name = short_name or self._generate_short_name()
        self.type = self._identify_type()
        self.metadata = self._parse_metadata()
        self.is_valid = self._validate()
        
    def _identify_type(self) -> CitationType:
        """Identify the type of citation based on patterns"""
        text = self.raw_text
        
        # Case patterns
        case_patterns = [
            r'\d+\s+[A-Z]\.\s*[A-Z0-9]+\.?\s*\d+',  # e.g., 123 U.S. 456
            r'\d+\s+F\.\s*(?:2d|3d|4th)',  # Federal reporters
            r'\d+\s+S\.\s*Ct\.',  # Supreme Court reporter
            r'v\.\s+[A-Z]',  # "v." indicates case
            r'[Ii]n\s+re\s+',  # In re cases
            r'[Ee]x\s+parte\s+',  # Ex parte cases
        ]
        
        for pattern in case_patterns:
            if re.search(pattern, text):
                return CitationType.CASE
        
        # Statute patterns
        statute_patterns = [
            r'\d+\s+U\.S\.C\.',  # U.S. Code
            r'\d+\s+C\.F\.R\.',  # Code of Federal Regulations
            r'(?:Pub\.|Priv\.)\s*L\.\s*No\.',  # Public/Private Law
            r'\s+Stat\.\s+',  # Statutes at Large
            r'§+\s*\d+',  # Section symbol
        ]
        
        for pattern in statute_patterns:
            if re.search(pattern, text):
                return CitationType.STATUTE if 'U.S.C.' in text else CitationType.REGULATION
        
        # Article patterns
        article_patterns = [
            r'\d+\s+[A-Z][a-z]+\.\s*L\.\s*Rev\.',  # Law Review
            r'\d+\s+[A-Z][a-z]+\.\s*J\.\s*',  # Journal
            r'[A-Z][a-z]+,\s+[A-Z][a-z]+.*?,\s*\d+\s+[A-Z]',  # Author, Title, Volume
        ]
        
        for pattern in article_patterns:
            if re.search(pattern, text):
                return CitationType.ARTICLE
        
        # Book patterns
        if re.search(r'\(\d{4}\)$', text) and not any(x in text for x in ['http', 'www']):
            if re.search(r'[A-Z][a-z]+,\s+[A-Z]', text) and 'v.' not in text:
                return CitationType.BOOK
        
        # Web patterns
        if any(x in text.lower() for x in ['http://', 'https://', 'www.', '.com', '.org', '.gov']):
            return CitationType.WEB
        
        # Legislative materials
        if any(x in text for x in ['H.R.', 'S.', 'H.R. Rep.', 'S. Rep.', 'Cong. Rec.']):
            return CitationType.LEGISLATIVE
        
        return CitationType.UNKNOWN
    
    def _parse_metadata(self) -> CitationMetadata:
        """Parse metadata based on citation type"""
        metadata = CitationMetadata()
        
        if self.type == CitationType.CASE:
            metadata = self._parse_case()
        elif self.type == CitationType.STATUTE:
            metadata = self._parse_statute()
        elif self.type == CitationType.REGULATION:
            metadata = self._parse_regulation()
        elif self.type == CitationType.ARTICLE:
            metadata = self._parse_article()
        elif self.type == CitationType.BOOK:
            metadata = self._parse_book()
        elif self.type == CitationType.WEB:
            metadata = self._parse_web()
        elif self.type == CitationType.LEGISLATIVE:
            metadata = self._parse_legislative()
        
        # Extract common elements
        metadata.signal = self._extract_signal()
        metadata.parenthetical = self._extract_parenthetical()
        
        return metadata
    
    def _parse_case(self) -> CitationMetadata:
        """Parse case citation metadata"""
        metadata = CitationMetadata()
        text = self.raw_text
        
        # Extract case name (parties)
        case_name_match = re.search(r'^(.*?)\s*,?\s*\d+\s+[A-Z]', text)
        if case_name_match:
            metadata.title = case_name_match.group(1).strip()
        
        # Extract volume, reporter, and page
        reporter_match = re.search(
            r'(\d+)\s+([A-Z][A-Za-z0-9.\s]+?)\s+(\d+)(?:,?\s+(\d+[-–]\d+|\d+))?',
            text
        )
        if reporter_match:
            metadata.volume = reporter_match.group(1)
            metadata.reporter = reporter_match.group(2).strip()
            metadata.page = reporter_match.group(3)
            if reporter_match.group(4):
                metadata.pincite = reporter_match.group(4)
        
        # Extract court and year
        paren_match = re.search(r'\(([^)]+)\)(?:\s*\([^)]+\))?$', text)
        if paren_match:
            court_year = paren_match.group(1)
            year_match = re.search(r'\d{4}', court_year)
            if year_match:
                metadata.year = year_match.group()
                metadata.court = court_year.replace(metadata.year, '').strip(' ,')
            else:
                metadata.court = court_year
        
        return metadata
    
    def _parse_statute(self) -> CitationMetadata:
        """Parse statute citation metadata"""
        metadata = CitationMetadata()
        text = self.raw_text
        
        # Extract title and section for U.S.C.
        usc_match = re.search(r'(\d+)\s+U\.S\.C\.\s+§+\s*([\d\w-]+)', text)
        if usc_match:
            metadata.title = f"Title {usc_match.group(1)}"
            metadata.section = usc_match.group(2)
            metadata.reporter = "U.S.C."
        
        # Extract year if present
        year_match = re.search(r'\((\d{4})\)', text)
        if year_match:
            metadata.year = year_match.group(1)
        
        return metadata
    
    def _parse_regulation(self) -> CitationMetadata:
        """Parse regulation citation metadata"""
        metadata = CitationMetadata()
        text = self.raw_text
        
        # Extract title and section for C.F.R.
        cfr_match = re.search(r'(\d+)\s+C\.F\.R\.\s+§+\s*([\d\w.-]+)', text)
        if cfr_match:
            metadata.title = f"Title {cfr_match.group(1)}"
            metadata.section = cfr_match.group(2)
            metadata.reporter = "C.F.R."
        
        # Extract year
        year_match = re.search(r'\((\d{4})\)', text)
        if year_match:
            metadata.year = year_match.group(1)
        
        return metadata
    
    def _parse_article(self) -> CitationMetadata:
        """Parse article citation metadata"""
        metadata = CitationMetadata()
        text = self.raw_text
        
        # Common pattern: Author, Title, Volume Journal Page (Year)
        article_match = re.search(
            r'^([^,]+?),\s+([^,]+?),\s+(\d+)\s+([^0-9]+?)\s+(\d+)(?:,?\s+(\d+[-–]\d+|\d+))?\s*\((\d{4})\)',
            text
        )
        if article_match:
            metadata.authors = [article_match.group(1).strip()]
            metadata.title = article_match.group(2).strip()
            metadata.volume = article_match.group(3)
            metadata.reporter = article_match.group(4).strip()
            metadata.page = article_match.group(5)
            if article_match.group(6):
                metadata.pincite = article_match.group(6)
            metadata.year = article_match.group(7)
        else:
            # Try alternative patterns
            # Pattern for articles without volume
            no_vol_match = re.search(
                r'^([^,]+?),\s+([^,]+?),\s+([^0-9]+?)\s*,?\s*(\d{4})',
                text
            )
            if no_vol_match:
                metadata.authors = [no_vol_match.group(1).strip()]
                metadata.title = no_vol_match.group(2).strip()
                metadata.reporter = no_vol_match.group(3).strip()
                metadata.year = no_vol_match.group(4)
        
        return metadata
    
    def _parse_book(self) -> CitationMetadata:
        """Parse book citation metadata"""
        metadata = CitationMetadata()
        text = self.raw_text
        
        # Pattern: Author, TITLE (edition year) or Author, TITLE page (year)
        book_match = re.search(
            r'^([^,]+?),\s+([^(]+?)(?:\s+(\d+))?\s*\((?:(\d+(?:st|nd|rd|th)\s+ed\.\s+)?(\d{4}))?\)',
            text
        )
        if book_match:
            metadata.authors = [book_match.group(1).strip()]
            metadata.title = book_match.group(2).strip()
            if book_match.group(3):
                metadata.page = book_match.group(3)
            if book_match.group(4):
                metadata.edition = book_match.group(4).strip()
            if book_match.group(5):
                metadata.year = book_match.group(5)
        
        return metadata
    
    def _parse_web(self) -> CitationMetadata:
        """Parse web citation metadata"""
        metadata = CitationMetadata()
        text = self.raw_text
        
        # Extract URL
        url_match = re.search(r'https?://[^\s,]+', text)
        if url_match:
            metadata.url = url_match.group()
        
        # Extract title (usually before URL)
        if url_match:
            before_url = text[:url_match.start()].strip()
            # Remove author if present
            if ',' in before_url:
                parts = before_url.split(',', 1)
                metadata.authors = [parts[0].strip()]
                metadata.title = parts[1].strip()
            else:
                metadata.title = before_url
        
        # Extract access date
        access_match = re.search(
            r'\((?:last\s+)?(?:visited|accessed|updated)\s+([^)]+)\)',
            text,
            re.IGNORECASE
        )
        if access_match:
            metadata.access_date = access_match.group(1)
        
        return metadata
    
    def _parse_legislative(self) -> CitationMetadata:
        """Parse legislative material citation metadata"""
        metadata = CitationMetadata()
        text = self.raw_text
        
        # House/Senate Reports
        if 'Rep.' in text:
            rep_match = re.search(
                r'(H\.R\.|S\.)\s+Rep\.\s+No\.\s+([\d-]+)(?:,\s+at\s+(\d+))?\s*\((\d{4})\)',
                text
            )
            if rep_match:
                metadata.reporter = f"{rep_match.group(1)} Rep."
                metadata.title = f"No. {rep_match.group(2)}"
                if rep_match.group(3):
                    metadata.page = rep_match.group(3)
                metadata.year = rep_match.group(4)
        
        # Congressional Record
        elif 'Cong. Rec.' in text:
            rec_match = re.search(r'(\d+)\s+Cong\.\s+Rec\.\s+([\dHS-]+)', text)
            if rec_match:
                metadata.volume = rec_match.group(1)
                metadata.page = rec_match.group(2)
                metadata.reporter = "Cong. Rec."
        
        return metadata
    
    def _extract_signal(self) -> str:
        """Extract citation signal (see, see also, cf., etc.)"""
        signals = [
            'See generally', 'See also', 'See', 'Cf.', 'Compare', 'Contra',
            'But see', 'But cf.', 'See, e.g.,', 'E.g.,', 'Accord'
        ]
        
        for signal in signals:
            if self.raw_text.startswith(signal):
                return signal
        
        return ""
    
    def _extract_parenthetical(self) -> str:
        """Extract parenthetical explanation"""
        # Look for parenthetical at the end that's not a date
        paren_match = re.findall(r'\([^)]+\)', self.raw_text)
        if paren_match:
            last_paren = paren_match[-1]
            # Check if it's not just a year or court/year
            if not re.match(r'\(\d{4}\)$', last_paren) and \
               not re.match(r'\([A-Z][^)]*\d{4}\)$', last_paren):
                return last_paren[1:-1]  # Remove parentheses
        
        return ""
    
    def _generate_short_name(self) -> str:
        """Generate a short name for the citation"""
        if self.type == CitationType.CASE:
            # Use first party name
            if 'v.' in self.raw_text:
                return self.raw_text.split('v.')[0].strip().split()[-1]
            elif 'In re' in self.raw_text:
                match = re.search(r'In re\s+([^,]+)', self.raw_text)
                if match:
                    return match.group(1).strip().split()[0]
        elif self.type == CitationType.ARTICLE:
            # Use author's last name
            if ',' in self.raw_text:
                author = self.raw_text.split(',')[0]
                return author.split()[-1] if author else "Article"
        elif self.type == CitationType.BOOK:
            # Use author's last name
            if ',' in self.raw_text:
                author = self.raw_text.split(',')[0]
                return author.split()[-1] if author else "Book"
        
        return f"Source_{self.source_id}"
    
    def _validate(self) -> bool:
        """Validate that the citation has minimum required elements"""
        if self.type == CitationType.CASE:
            return bool(self.metadata.reporter and self.metadata.page)
        elif self.type in [CitationType.STATUTE, CitationType.REGULATION]:
            return bool(self.metadata.section)
        elif self.type == CitationType.ARTICLE:
            return bool(self.metadata.title and self.metadata.authors)
        elif self.type == CitationType.BOOK:
            return bool(self.metadata.title and self.metadata.authors)
        elif self.type == CitationType.WEB:
            return bool(self.metadata.url)
        
        return self.type != CitationType.UNKNOWN
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert citation to dictionary format"""
        return {
            'source_id': self.source_id,
            'short_name': self.short_name,
            'raw_text': self.raw_text,
            'type': self.type.value,
            'metadata': {
                'authors': self.metadata.authors,
                'title': self.metadata.title,
                'volume': self.metadata.volume,
                'reporter': self.metadata.reporter,
                'page': self.metadata.page,
                'pincite': self.metadata.pincite,
                'year': self.metadata.year,
                'court': self.metadata.court,
                'url': self.metadata.url,
                'access_date': self.metadata.access_date,
                'section': self.metadata.section,
                'signal': self.metadata.signal,
                'parenthetical': self.metadata.parenthetical,
            },
            'is_valid': self.is_valid
        }


class CitationParser:
    """Main parser class for processing multiple citations"""
    
    def __init__(self):
        self.citations: List[Citation] = []
        self.errors: List[Dict[str, str]] = []
    
    def parse_citation(self, raw_text: str, source_id: str, short_name: str = "") -> Citation:
        """Parse a single citation"""
        try:
            citation = Citation(raw_text, source_id, short_name)
            self.citations.append(citation)
            return citation
        except Exception as e:
            error = {
                'source_id': source_id,
                'raw_text': raw_text,
                'error': str(e)
            }
            self.errors.append(error)
            logger.error(f"Failed to parse citation {source_id}: {e}")
            # Return a basic citation even on error
            return Citation(raw_text, source_id, short_name or f"Error_{source_id}")
    
    def parse_batch(self, citations_data: List[Tuple[str, str, str]]) -> List[Citation]:
        """Parse multiple citations
        Args:
            citations_data: List of tuples (raw_text, source_id, short_name)
        """
        results = []
        for raw_text, source_id, short_name in citations_data:
            citation = self.parse_citation(raw_text, source_id, short_name)
            results.append(citation)
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get parsing statistics"""
        type_counts = {}
        for citation in self.citations:
            type_name = citation.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        return {
            'total_citations': len(self.citations),
            'valid_citations': sum(1 for c in self.citations if c.is_valid),
            'invalid_citations': sum(1 for c in self.citations if not c.is_valid),
            'errors': len(self.errors),
            'types': type_counts
        }
    
    def export_results(self) -> List[Dict[str, Any]]:
        """Export all parsed citations as dictionaries"""
        return [citation.to_dict() for citation in self.citations]