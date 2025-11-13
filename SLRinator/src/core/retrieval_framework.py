#!/usr/bin/env python3
"""
Systematic Source Retrieval Framework for Stanford Law Review
Following Member Editor Handbook Volume 78 Instructions

This framework implements the exact retrieval hierarchy and reasoning
documentation as specified in the SLR Member Handbook.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum, auto
from datetime import datetime
import logging
import json
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SourceType(Enum):
    """Source types as defined in Member Handbook Appendix A"""
    CASE = auto()
    STATUTE_FEDERAL = auto()
    STATUTE_STATE = auto()
    REGULATION_FEDERAL = auto()
    REGULATION_STATE = auto()
    JOURNAL_ARTICLE = auto()
    BOOK = auto()
    NEWSPAPER = auto()
    MAGAZINE = auto()
    WEBSITE = auto()
    COURT_DOCUMENT = auto()
    SCOTUS_BRIEF = auto()
    ORAL_ARGUMENT = auto()
    LEGISLATIVE_HISTORY = auto()
    EXECUTIVE_MATERIAL = auto()
    INTERNATIONAL_MATERIAL = auto()
    TREATISE = auto()
    UNKNOWN = auto()


class RetrievalPriority(Enum):
    """Priority levels for source retrieval"""
    FORMAT_PRESERVING_ELECTRONIC = 1
    FORMAT_PRESERVING_PHYSICAL = 2
    NON_FORMAT_PRESERVING = 3
    AUTHOR_PROVIDED = 4
    MANUAL_RETRIEVAL_NEEDED = 5


class RetrievalSource(Enum):
    """Where the source was retrieved from"""
    HEINONLINE = "HeinOnline"
    WESTLAW = "Westlaw"
    LEXIS = "Lexis"
    BLOOMBERG = "Bloomberg"
    JSTOR = "JSTOR"
    SEARCHWORKS = "SearchWorks"
    GOOGLE_BOOKS = "Google Books"
    HATHITRUST = "HathiTrust"
    SUPREMECOURT_GOV = "supremecourt.gov"
    GOVINFO = "GovInfo"
    CORNELL_LAW = "Cornell Law"
    COURTLISTENER = "CourtListener"
    LIBRARY_PHYSICAL = "Physical Library"
    AUTHOR_PROVIDED = "Author Provided"
    ILL = "Interlibrary Loan"
    SSRN = "SSRN"
    JOURNAL_WEBSITE = "Journal Website"
    OTHER = "Other"


@dataclass
class CitationComponents:
    """Parsed components of a citation"""
    raw_text: str
    type: SourceType
    # Case components
    party1: Optional[str] = None
    party2: Optional[str] = None
    volume: Optional[str] = None
    reporter: Optional[str] = None
    page: Optional[str] = None
    pincite: Optional[str] = None
    year: Optional[str] = None
    court: Optional[str] = None
    # Statute/Regulation components
    title: Optional[str] = None
    section: Optional[str] = None
    # Article/Book components
    author: Optional[str] = None
    article_title: Optional[str] = None
    journal: Optional[str] = None
    publisher: Optional[str] = None
    edition: Optional[str] = None
    # Additional metadata
    parenthetical: Optional[str] = None
    subsequent_history: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class RetrievalAttempt:
    """Record of a single retrieval attempt"""
    source: RetrievalSource
    timestamp: datetime
    success: bool
    priority: RetrievalPriority
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    reasoning: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'source': self.source.value,
            'timestamp': self.timestamp.isoformat(),
            'success': self.success,
            'priority': self.priority.value,
            'file_path': self.file_path,
            'error_message': self.error_message,
            'reasoning': self.reasoning
        }


@dataclass
class RetrievalRecord:
    """Complete record of source retrieval"""
    footnote_number: int
    citation: CitationComponents
    attempts: List[RetrievalAttempt] = field(default_factory=list)
    final_status: str = "pending"
    final_file_path: Optional[str] = None
    redboxing_required: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    
    def add_attempt(self, attempt: RetrievalAttempt):
        """Add a retrieval attempt to the record"""
        self.attempts.append(attempt)
        if attempt.success:
            self.final_status = "success"
            self.final_file_path = attempt.file_path
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'footnote_number': self.footnote_number,
            'citation': self.citation.to_dict(),
            'attempts': [a.to_dict() for a in self.attempts],
            'final_status': self.final_status,
            'final_file_path': self.final_file_path,
            'redboxing_required': self.redboxing_required,
            'notes': self.notes
        }


class SourceClassifier:
    """Classify citations into source types based on Member Handbook rules"""
    
    @staticmethod
    def classify(citation_text: str) -> Tuple[SourceType, Dict[str, Any]]:
        """
        Classify a citation and extract its components
        Returns: (SourceType, extracted_components)
        """
        citation_text = citation_text.strip()
        
        # Federal Statutes (e.g., "35 U.S.C. § 101")
        if re.search(r'\d+\s+U\.S\.C\.\s*§', citation_text):
            match = re.search(r'(\d+)\s+U\.S\.C\.\s*§\s*([\d\w\-\.]+)', citation_text)
            if match:
                return SourceType.STATUTE_FEDERAL, {
                    'title': match.group(1),
                    'section': match.group(2)
                }
        
        # Federal Regulations (e.g., "21 C.F.R. § 314.50")
        if re.search(r'\d+\s+C\.F\.R\.\s*§', citation_text):
            match = re.search(r'(\d+)\s+C\.F\.R\.\s*§\s*([\d\w\-\.]+)', citation_text)
            if match:
                return SourceType.REGULATION_FEDERAL, {
                    'title': match.group(1),
                    'section': match.group(2)
                }
        
        # Cases - Supreme Court (U.S. reporter)
        if re.search(r'\d+\s+U\.S\.\s+\d+', citation_text):
            return SourceType.CASE, SourceClassifier._extract_case_components(citation_text)
        
        # Cases - Federal (F., F.2d, F.3d, F. Supp., etc.)
        if re.search(r'\d+\s+F\.\s*(?:2d|3d|Supp\.?)', citation_text):
            return SourceType.CASE, SourceClassifier._extract_case_components(citation_text)
        
        # Cases - General pattern "v." or "v "
        if ' v. ' in citation_text or ' v ' in citation_text:
            return SourceType.CASE, SourceClassifier._extract_case_components(citation_text)
        
        # Journal Articles (contains journal abbreviations)
        journal_patterns = [
            r'\d+\s+[A-Z][a-z]*\.?\s+L\.\s*(?:Rev\.|J\.)',  # Law Review/Journal
            r'Stan\.\s+L\.\s+Rev\.',  # Stanford Law Review
            r'Harv\.\s+L\.\s+Rev\.',  # Harvard Law Review
            r'Yale\s+L\.\s*J\.',  # Yale Law Journal
        ]
        for pattern in journal_patterns:
            if re.search(pattern, citation_text):
                return SourceType.JOURNAL_ARTICLE, SourceClassifier._extract_article_components(citation_text)
        
        # Books (often have publishers in parentheses with years)
        if re.search(r'\([^)]*\d{4}\)', citation_text) and not re.search(r'\d+\s+[A-Z]', citation_text):
            return SourceType.BOOK, SourceClassifier._extract_book_components(citation_text)
        
        # Websites (contains http or www)
        if 'http://' in citation_text or 'https://' in citation_text or 'www.' in citation_text:
            return SourceType.WEBSITE, {'url': citation_text}
        
        # Default to UNKNOWN
        return SourceType.UNKNOWN, {'raw_text': citation_text}
    
    @staticmethod
    def _extract_case_components(citation: str) -> Dict[str, Any]:
        """Extract components from a case citation"""
        components = {}
        
        # Extract parties (everything before the first comma or volume number)
        case_name_match = re.match(r'^([^,\d]+?)(?:,|\s+\d)', citation)
        if case_name_match:
            case_name = case_name_match.group(1).strip()
            # Split on v. or v
            if ' v. ' in case_name:
                parts = case_name.split(' v. ')
            elif ' v ' in case_name:
                parts = case_name.split(' v ')
            else:
                parts = [case_name]
            
            if len(parts) >= 2:
                components['party1'] = parts[0].strip()
                components['party2'] = parts[1].strip()
            else:
                components['party1'] = parts[0].strip()
        
        # Extract volume, reporter, page
        reporter_match = re.search(r'(\d+)\s+([A-Z][A-Za-z0-9\.\s]+?)\s+(\d+)', citation)
        if reporter_match:
            components['volume'] = reporter_match.group(1)
            components['reporter'] = reporter_match.group(2).strip()
            components['page'] = reporter_match.group(3)
        
        # Extract pincite (page after comma following main page)
        pincite_match = re.search(r'\d+,\s*(\d+)', citation)
        if pincite_match:
            components['pincite'] = pincite_match.group(1)
        
        # Extract year
        year_match = re.search(r'\((\d{4})\)', citation)
        if year_match:
            components['year'] = year_match.group(1)
        
        return components
    
    @staticmethod
    def _extract_article_components(citation: str) -> Dict[str, Any]:
        """Extract components from a journal article citation"""
        components = {}
        
        # Extract author (before first comma)
        author_match = re.match(r'^([^,]+),', citation)
        if author_match:
            components['author'] = author_match.group(1).strip()
        
        # Extract title (between commas, before volume)
        title_match = re.search(r',\s*([^,]+?)\s*,?\s*\d+\s+', citation)
        if title_match:
            components['article_title'] = title_match.group(1).strip()
        
        # Extract volume, journal, page
        journal_match = re.search(r'(\d+)\s+([A-Z][A-Za-z\.\s]+?)\s+(\d+)', citation)
        if journal_match:
            components['volume'] = journal_match.group(1)
            components['journal'] = journal_match.group(2).strip()
            components['page'] = journal_match.group(3)
        
        # Extract year
        year_match = re.search(r'\((\d{4})\)', citation)
        if year_match:
            components['year'] = year_match.group(1)
        
        return components
    
    @staticmethod
    def _extract_book_components(citation: str) -> Dict[str, Any]:
        """Extract components from a book citation"""
        components = {}
        
        # Extract author (before first comma or title in caps)
        author_match = re.match(r'^([^,]+?)(?:,|\s+[A-Z]{2,})', citation)
        if author_match:
            components['author'] = author_match.group(1).strip()
        
        # Extract title (in all caps or title case)
        title_match = re.search(r'([A-Z][A-Za-z\s:]+?)(?:\s+\d+|\s*\()', citation)
        if title_match:
            components['title'] = title_match.group(1).strip()
        
        # Extract year and publisher from parenthetical
        paren_match = re.search(r'\(([^)]*?)(\d{4})\)', citation)
        if paren_match:
            components['year'] = paren_match.group(2)
            publisher = paren_match.group(1).strip()
            if publisher:
                components['publisher'] = publisher.rstrip(',').strip()
        
        return components


class RetrievalStrategy:
    """
    Implements the retrieval strategy hierarchy from the Member Handbook
    """
    
    def __init__(self):
        self.strategies = self._build_strategy_hierarchy()
    
    def _build_strategy_hierarchy(self) -> Dict[SourceType, List[Tuple[RetrievalSource, RetrievalPriority, str]]]:
        """
        Build the retrieval hierarchy based on Member Handbook Appendix A
        Returns: Dict[SourceType, List[(source, priority, reasoning)]]
        """
        return {
            SourceType.CASE: [
                (RetrievalSource.HEINONLINE, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC, 
                 "HeinOnline preferred for Supreme Court cases - has U.S. Reports"),
                (RetrievalSource.WESTLAW, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "Westlaw Original Image PDF for format-preserving version"),
                (RetrievalSource.LEXIS, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "LexisNexis Reporter Images as alternative"),
                (RetrievalSource.COURTLISTENER, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "CourtListener for free access to federal cases"),
                (RetrievalSource.HATHITRUST, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "HathiTrust for older state reporters"),
                (RetrievalSource.LIBRARY_PHYSICAL, RetrievalPriority.FORMAT_PRESERVING_PHYSICAL,
                 "Physical reporter from library"),
                (RetrievalSource.WESTLAW, RetrievalPriority.NON_FORMAT_PRESERVING,
                 "Westlaw non-format-preserving as last resort"),
            ],
            
            SourceType.STATUTE_FEDERAL: [
                (RetrievalSource.GOVINFO, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "GovInfo provides official format-preserving U.S. Code"),
                (RetrievalSource.CORNELL_LAW, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "Cornell Law as alternative source"),
                (RetrievalSource.WESTLAW, RetrievalPriority.NON_FORMAT_PRESERVING,
                 "Westlaw/Lexis as last resort for statutes"),
            ],
            
            SourceType.REGULATION_FEDERAL: [
                (RetrievalSource.HEINONLINE, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "HeinOnline for C.F.R. and Federal Register"),
                (RetrievalSource.GOVINFO, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "GovInfo for federal regulations"),
                (RetrievalSource.WESTLAW, RetrievalPriority.NON_FORMAT_PRESERVING,
                 "Westlaw/Lexis for regulations if needed"),
            ],
            
            SourceType.JOURNAL_ARTICLE: [
                (RetrievalSource.HEINONLINE, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "HeinOnline for law review articles"),
                (RetrievalSource.JSTOR, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "JSTOR for academic articles"),
                (RetrievalSource.SEARCHWORKS, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "SearchWorks Articles+ to find links"),
                (RetrievalSource.JOURNAL_WEBSITE, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "Journal's own website for recent articles"),
                (RetrievalSource.SSRN, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "SSRN for forthcoming articles"),
                (RetrievalSource.LIBRARY_PHYSICAL, RetrievalPriority.FORMAT_PRESERVING_PHYSICAL,
                 "Physical bound volume from library"),
                (RetrievalSource.WESTLAW, RetrievalPriority.NON_FORMAT_PRESERVING,
                 "Westlaw/Lexis as last resort - not format-preserving"),
            ],
            
            SourceType.BOOK: [
                (RetrievalSource.SEARCHWORKS, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "SearchWorks for electronic books in Stanford system"),
                (RetrievalSource.GOOGLE_BOOKS, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "Google Books for freely available books"),
                (RetrievalSource.HATHITRUST, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "HathiTrust for out-of-copyright books"),
                (RetrievalSource.LIBRARY_PHYSICAL, RetrievalPriority.FORMAT_PRESERVING_PHYSICAL,
                 "Physical book from Stanford libraries"),
                (RetrievalSource.ILL, RetrievalPriority.FORMAT_PRESERVING_PHYSICAL,
                 "Interlibrary Loan if not available at Stanford"),
            ],
            
            SourceType.COURT_DOCUMENT: [
                (RetrievalSource.WESTLAW, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "Westlaw for court documents - check for format-preserving"),
                (RetrievalSource.LEXIS, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "Lexis Courtlink for court documents"),
                (RetrievalSource.BLOOMBERG, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "Bloomberg Dockets sourced from PACER"),
            ],
            
            SourceType.SCOTUS_BRIEF: [
                (RetrievalSource.OTHER, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "ABANet.org for Supreme Court briefs"),
                (RetrievalSource.WESTLAW, RetrievalPriority.FORMAT_PRESERVING_ELECTRONIC,
                 "Westlaw for SCOTUS briefs"),
            ],
        }
    
    def get_retrieval_order(self, source_type: SourceType) -> List[Tuple[RetrievalSource, RetrievalPriority, str]]:
        """Get the ordered list of retrieval strategies for a source type"""
        return self.strategies.get(source_type, [
            (RetrievalSource.OTHER, RetrievalPriority.MANUAL_RETRIEVAL_NEEDED, 
             "Unknown source type - manual retrieval needed")
        ])


class RetrievalEngine:
    """
    Main engine for systematic source retrieval
    """
    
    def __init__(self):
        self.classifier = SourceClassifier()
        self.strategy = RetrievalStrategy()
        self.records: List[RetrievalRecord] = []
    
    def process_footnote(self, footnote_number: int, citation_text: str) -> RetrievalRecord:
        """
        Process a single footnote through the retrieval system
        """
        logger.info(f"Processing footnote {footnote_number}: {citation_text[:50]}...")
        
        # Classify the citation
        source_type, components = self.classifier.classify(citation_text)
        
        # Create citation components
        citation = CitationComponents(
            raw_text=citation_text,
            type=source_type,
            **components
        )
        
        # Create retrieval record
        record = RetrievalRecord(
            footnote_number=footnote_number,
            citation=citation
        )
        
        # Determine redboxing requirements based on source type
        record.redboxing_required = self._determine_redboxing_requirements(source_type, components)
        
        # Get retrieval strategy
        retrieval_order = self.strategy.get_retrieval_order(source_type)
        
        # Log the retrieval strategy
        logger.info(f"Source type: {source_type.name}")
        logger.info(f"Retrieval strategy: {len(retrieval_order)} potential sources")
        
        # Add strategy to notes
        record.notes.append(f"Source classified as: {source_type.name}")
        record.notes.append(f"Retrieval hierarchy: {', '.join([s[0].value for s in retrieval_order[:3]])}")
        
        self.records.append(record)
        return record
    
    def _determine_redboxing_requirements(self, source_type: SourceType, components: Dict) -> List[str]:
        """
        Determine what needs to be redboxed based on Member Handbook instructions
        """
        requirements = []
        
        if source_type == SourceType.CASE:
            requirements.extend([
                "Case name/parties",
                "Volume number",
                "Reporter abbreviation",
                "Starting page number",
                "Pincite pages",
                "Year of decision",
                "Court (if lower court)",
                "Judge/panel composition",
                "Check for subsequent history",
                "Check for negative treatment"
            ])
        
        elif source_type in [SourceType.STATUTE_FEDERAL, SourceType.STATUTE_STATE]:
            requirements.extend([
                "Title number",
                "Section number(s)",
                "Year of codification",
                "Any subsections cited"
            ])
        
        elif source_type == SourceType.JOURNAL_ARTICLE:
            requirements.extend([
                "Author name(s)",
                "Article title",
                "Journal name",
                "Volume number",
                "Starting page",
                "Pincite pages",
                "Year of publication",
                "Check if consecutively paginated (pull TOC)"
            ])
        
        elif source_type == SourceType.BOOK:
            requirements.extend([
                "Author/editor names",
                "Full title",
                "Publisher",
                "Year of publication",
                "Edition (if not first)",
                "Pincite pages",
                "ISBN (if available)"
            ])
        
        return requirements
    
    def generate_sourcepull_sheet_entry(self, record: RetrievalRecord) -> Dict[str, Any]:
        """
        Generate an entry formatted for the Google Sheets sourcepull spreadsheet
        """
        entry = {
            'Footnote': record.footnote_number,
            'Source Type': record.citation.type.name,
            'Full Citation': record.citation.raw_text,
            'Retrieval Strategy': ', '.join([a.source.value for a in record.attempts]),
            'Final Status': record.final_status,
            'File Path': record.final_file_path,
            'Redboxing Checklist': '\n'.join(record.redboxing_required),
            'Notes': '\n'.join(record.notes),
            'Last Updated': datetime.now().isoformat()
        }
        
        # Add parsed components
        if record.citation.type == SourceType.CASE:
            entry.update({
                'Party 1': record.citation.party1,
                'Party 2': record.citation.party2,
                'Volume': record.citation.volume,
                'Reporter': record.citation.reporter,
                'Page': record.citation.page,
                'Year': record.citation.year
            })
        
        return entry
    
    def export_retrieval_log(self, filepath: str):
        """Export the complete retrieval log to JSON"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'total_footnotes': len(self.records),
            'records': [r.to_dict() for r in self.records]
        }
        
        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        logger.info(f"Retrieval log exported to {filepath}")


def main():
    """
    Example usage of the systematic retrieval framework
    """
    engine = RetrievalEngine()
    
    # Test with sample citations
    test_citations = [
        (1, "Alice Corp. Pty. Ltd. v. CLS Bank Int'l, 573 U.S. 208, 216 (2014)."),
        (2, "35 U.S.C. § 101 (2018)."),
        (3, "Mayo Collaborative Servs. v. Prometheus Lab'ys, Inc., 566 U.S. 66, 70 (2012)."),
        (20, "Mark A. Lemley, Software Patents and the Return of Functional Claiming, 2013 Wis. L. Rev. 905, 908."),
    ]
    
    for footnote_num, citation in test_citations:
        record = engine.process_footnote(footnote_num, citation)
        
        # Print the results
        print(f"\n{'='*60}")
        print(f"Footnote {footnote_num}:")
        print(f"Type: {record.citation.type.name}")
        print(f"Components: {record.citation.to_dict()}")
        print(f"Redboxing required: {', '.join(record.redboxing_required[:3])}...")
        
        # Generate spreadsheet entry
        sheet_entry = engine.generate_sourcepull_sheet_entry(record)
        print(f"Spreadsheet entry keys: {list(sheet_entry.keys())[:5]}...")
    
    # Export the log
    engine.export_retrieval_log('retrieval_log.json')
    print(f"\n✅ Processed {len(engine.records)} citations")


if __name__ == "__main__":
    main()