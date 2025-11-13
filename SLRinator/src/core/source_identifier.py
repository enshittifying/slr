#!/usr/bin/env python3
"""
Rule-based Source Type Identifier for Stanford Law Review
Identifies citation types according to Member Handbook rules
"""

import re
from enum import Enum
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass


class SourceType(Enum):
    """Source types per Stanford Law Review Member Handbook"""
    # Cases
    SUPREME_COURT = "supreme_court"
    FEDERAL_APPELLATE = "federal_appellate"
    FEDERAL_DISTRICT = "federal_district"
    STATE_HIGH_COURT = "state_high_court"
    STATE_APPELLATE = "state_appellate"
    STATE_TRIAL = "state_trial"
    
    # Statutes & Regulations
    FEDERAL_STATUTE = "federal_statute"
    STATE_STATUTE = "state_statute"
    FEDERAL_REGULATION = "federal_regulation"
    STATE_REGULATION = "state_regulation"
    
    # Secondary Sources
    LAW_REVIEW_ARTICLE = "law_review_article"
    BOOK = "book"
    TREATISE = "treatise"
    NEWS_ARTICLE = "news_article"
    WEBSITE = "website"
    
    # Legislative Materials
    CONGRESSIONAL_RECORD = "congressional_record"
    HOUSE_REPORT = "house_report"
    SENATE_REPORT = "senate_report"
    HEARING = "hearing"
    
    # Other
    BRIEF = "brief"
    ORAL_ARGUMENT = "oral_argument"
    TRANSCRIPT = "transcript"
    UNKNOWN = "unknown"


@dataclass
class CitationComponents:
    """Extracted components from a citation"""
    # Case components
    party1: Optional[str] = None
    party2: Optional[str] = None
    volume: Optional[str] = None
    reporter: Optional[str] = None
    page: Optional[str] = None
    pincite: Optional[str] = None
    court: Optional[str] = None
    year: Optional[str] = None
    
    # Statute components
    title_number: Optional[str] = None
    code_name: Optional[str] = None
    section: Optional[str] = None
    
    # Article/Book components
    author: Optional[str] = None
    article_title: Optional[str] = None
    journal: Optional[str] = None
    book_title: Optional[str] = None
    publisher: Optional[str] = None
    
    # Other
    url: Optional[str] = None
    database: Optional[str] = None
    docket_number: Optional[str] = None
    document_type: Optional[str] = None


class SourceIdentifier:
    """Identifies citation types using Member Handbook rules"""
    
    # Federal Reporters (from Member Handbook)
    SUPREME_COURT_REPORTERS = {"U.S.", "S. Ct.", "L. Ed.", "L. Ed. 2d", "U.S. LEXIS"}
    
    FEDERAL_APPELLATE_REPORTERS = {
        "F.", "F.2d", "F.3d", "F.4th", "F. App'x", "Fed. App'x",
        "F. Cas.", "Fed. Cas."
    }
    
    FEDERAL_DISTRICT_REPORTERS = {
        "F. Supp.", "F. Supp. 2d", "F. Supp. 3d",
        "F.R.D.", "B.R.", "T.C."
    }
    
    # State Reporters (examples from handbook)
    STATE_REPORTERS = {
        # Regional reporters
        "A.", "A.2d", "A.3d",  # Atlantic
        "N.E.", "N.E.2d", "N.E.3d",  # North Eastern
        "N.W.", "N.W.2d", "N.W.3d",  # North Western
        "P.", "P.2d", "P.3d",  # Pacific
        "S.E.", "S.E.2d",  # South Eastern
        "S.W.", "S.W.2d", "S.W.3d",  # South Western
        "So.", "So. 2d", "So. 3d",  # Southern
        # State-specific
        "Cal.", "Cal. 2d", "Cal. 3d", "Cal. 4th", "Cal. 5th",
        "Cal. App.", "Cal. App. 2d", "Cal. App. 3d", "Cal. App. 4th", "Cal. App. 5th",
        "N.Y.", "N.Y.2d", "N.Y.3d",
        "A.D.", "A.D.2d", "A.D.3d",
        "N.Y.S.", "N.Y.S.2d", "N.Y.S.3d"
    }
    
    # Federal Codes
    FEDERAL_CODES = {"U.S.C.", "U.S.C.A.", "U.S.C.S."}
    
    # Federal Regulations
    FEDERAL_REGULATIONS = {"C.F.R.", "Fed. Reg."}
    
    # Law Review Patterns
    LAW_REVIEW_SIGNALS = {
        "L. Rev.", "L.J.", "J.L.", "Rev.", "L.Q.", "J. Legal",
        "Harv.", "Yale", "Stan.", "Colum.", "N.Y.U.", "Geo.", "Mich.",
        "U. Chi.", "U. Pa.", "Tex.", "Cal.", "Va.", "Duke", "Cornell"
    }
    
    def __init__(self):
        """Initialize the identifier with compiled regex patterns"""
        # Case pattern: Party v. Party, Volume Reporter Page (Court Year)
        self.case_pattern = re.compile(
            r"^([^,]+?)\s+v\.\s+([^,]+?),\s*(\d+)\s+([A-Za-z.\s']+?)\s+(\d+)(?:,\s*(\d+))?\s*(?:\(([^)]+)\))?",
            re.IGNORECASE
        )
        
        # Statute pattern: Title U.S.C. § Section (Year) - enhanced for subsections
        self.federal_statute_pattern = re.compile(
            r"(\d+)\s+(U\.S\.C\.(?:A\.|S\.)?)\s*§+\s*([0-9a-zA-Z\-\.]+(?:\([a-z0-9]+\))*(?:\([a-z0-9]+\))*)(?:\s*\(([^)]+)\))?",
            re.IGNORECASE
        )
        
        # Regulation pattern: Title C.F.R. § Section (Year)
        self.federal_regulation_pattern = re.compile(
            r"(\d+)\s+(C\.F\.R\.)\s*§+\s*([0-9a-zA-Z\-\.]+)(?:\s*\(([^)]+)\))?",
            re.IGNORECASE
        )
        
        # Law Review pattern: Author, Title, Volume Journal Page (Year)
        self.law_review_pattern = re.compile(
            r"^([^,]+?),\s*([^,]+?),\s*(\d+)\s+([^0-9]+?)\s+(\d+)(?:,\s*(\d+))?\s*\((\d{4})\)",
            re.IGNORECASE
        )
        
        # URL pattern
        self.url_pattern = re.compile(
            r"https?://[^\s]+",
            re.IGNORECASE
        )
        
        # Year pattern
        self.year_pattern = re.compile(r"\((\d{4})\)")
        
    def identify(self, citation: str) -> Tuple[SourceType, CitationComponents]:
        """
        Identify the source type and extract components from a citation
        
        Args:
            citation: The full citation text
            
        Returns:
            Tuple of (SourceType, CitationComponents)
        """
        citation = citation.strip()
        components = CitationComponents()
        
        # Check for URL
        if self.url_pattern.search(citation):
            components.url = self.url_pattern.search(citation).group(0)
            return SourceType.WEBSITE, components
        
        # Try case pattern first
        case_match = self.case_pattern.search(citation)
        if case_match:
            components.party1 = case_match.group(1).strip()
            components.party2 = case_match.group(2).strip()
            components.volume = case_match.group(3)
            components.reporter = case_match.group(4).strip()
            components.page = case_match.group(5)
            components.pincite = case_match.group(6) if case_match.group(6) else None
            
            # Extract court and year from parenthetical
            if case_match.group(7):
                paren_content = case_match.group(7)
                year_match = re.search(r"(\d{4})", paren_content)
                if year_match:
                    components.year = year_match.group(1)
                    components.court = paren_content.replace(year_match.group(1), "").strip()
                else:
                    components.court = paren_content.strip()
            
            # Determine case type based on reporter
            source_type = self._identify_case_type(components.reporter)
            return source_type, components
            
        # Try simpler case patterns for edge cases
        # Pattern: Party1 v. Party2, Volume Reporter Page (Year)
        complex_case = re.search(r"^(.+?)\s+v\.?\s+(.+?),\s*(\d+)\s+([^0-9]+?)\s+(\d+)(?:,\s*(\d+))?\s*(?:\(([^)]*(\d{4})[^)]*)\))?", citation, re.IGNORECASE)
        if complex_case and " v." in citation.lower():
            components.party1 = complex_case.group(1).strip()
            components.party2 = complex_case.group(2).strip()
            components.volume = complex_case.group(3)
            components.reporter = complex_case.group(4).strip()
            components.page = complex_case.group(5)
            components.pincite = complex_case.group(6) if complex_case.group(6) else None
            if complex_case.group(8):  # Year found
                components.year = complex_case.group(8)
                if complex_case.group(7):  # Full parenthetical
                    components.court = complex_case.group(7).replace(complex_case.group(8), "").strip()
            
            source_type = self._identify_case_type(components.reporter)
            return source_type, components
            
        # Pattern: Party1 v. Party2 (Year) - no citation info
        simple_case = re.search(r"^([^,]+?)\s+v\.?\s+([^,(]+?)(?:\s*\(([^)]*?(\d{4})[^)]*?)\))?", citation, re.IGNORECASE)
        if simple_case and " v." in citation.lower():
            components.party1 = simple_case.group(1).strip()
            components.party2 = simple_case.group(2).strip()
            if simple_case.group(4):  # Year found
                components.year = simple_case.group(4)
                if simple_case.group(3):  # Full parenthetical
                    components.court = simple_case.group(3).replace(simple_case.group(4), "").strip()
            
            # Try to find reporter information later in citation
            reporter_search = re.search(r"(\d+)\s+([^0-9]+?)\s+(\d+)", citation)
            if reporter_search:
                components.volume = reporter_search.group(1)
                components.reporter = reporter_search.group(2).strip()
                components.page = reporter_search.group(3)
                source_type = self._identify_case_type(components.reporter)
            else:
                source_type = SourceType.UNKNOWN
                
            return source_type, components
        
        # Try federal statute pattern
        statute_match = self.federal_statute_pattern.search(citation)
        if statute_match:
            components.title_number = statute_match.group(1)
            components.code_name = statute_match.group(2)
            # For retrieval purposes, use base section number (Cornell LII structure)
            full_section = statute_match.group(3)
            base_section = re.match(r"(\d+)", full_section).group(1)
            components.section = base_section
            if statute_match.group(4):
                components.year = statute_match.group(4)
            return SourceType.FEDERAL_STATUTE, components
        
        # Try alternative statute patterns for edge cases
        # Pattern: Title ## § ###
        alt_statute = re.search(r"(?:Title\s+)?(\d+)\s*§\s*(\d+(?:\.\d+)?(?:\([a-z]\))?)", citation, re.IGNORECASE)
        if alt_statute:
            components.title_number = alt_statute.group(1)
            components.code_name = "U.S.C."
            components.section = alt_statute.group(2)
            # Look for year in parentheses
            year_match = self.year_pattern.search(citation)
            if year_match:
                components.year = year_match.group(1)
            return SourceType.FEDERAL_STATUTE, components
            
        # Pattern: ## USC § ### - enhanced for subsections
        usc_pattern = re.search(r"(\d+)\s*USC?\s*§\s*(\d+(?:\.\d+)?(?:\([a-z0-9]+\))?(?:\([a-z0-9]+\))*)", citation, re.IGNORECASE)
        if usc_pattern:
            components.title_number = usc_pattern.group(1)
            components.code_name = "U.S.C."
            # Clean up section - for Cornell LII, use just the base section
            full_section = usc_pattern.group(2)
            base_section = re.match(r"(\d+)", full_section).group(1)
            components.section = base_section  # Cornell LII works better with just the base section
            year_match = self.year_pattern.search(citation)
            if year_match:
                components.year = year_match.group(1)
            return SourceType.FEDERAL_STATUTE, components
        
        # Try federal regulation pattern
        reg_match = self.federal_regulation_pattern.search(citation)
        if reg_match:
            components.title_number = reg_match.group(1)
            components.code_name = reg_match.group(2)
            components.section = reg_match.group(3)
            if reg_match.group(4):
                components.year = reg_match.group(4)
            return SourceType.FEDERAL_REGULATION, components
        
        # Try law review pattern
        review_match = self.law_review_pattern.search(citation)
        if review_match:
            components.author = review_match.group(1).strip()
            components.article_title = review_match.group(2).strip()
            components.volume = review_match.group(3)
            components.journal = review_match.group(4).strip()
            components.page = review_match.group(5)
            components.pincite = review_match.group(6) if review_match.group(6) else None
            components.year = review_match.group(7)
            
            # Check if it's actually a law review
            if self._is_law_review(components.journal):
                return SourceType.LAW_REVIEW_ARTICLE, components
        
        # Check for book patterns
        if " (" in citation and ")" in citation and not any(r in citation for r in ["v.", "§"]):
            # Likely a book: Author, TITLE (Publisher Year)
            parts = citation.split("(")
            if len(parts) >= 2:
                author_title = parts[0].strip()
                if "," in author_title:
                    author, title = author_title.split(",", 1)
                    components.author = author.strip()
                    components.book_title = title.strip()
                else:
                    components.book_title = author_title
                
                paren = parts[1].split(")")[0]
                year_match = re.search(r"(\d{4})", paren)
                if year_match:
                    components.year = year_match.group(1)
                    components.publisher = paren.replace(year_match.group(1), "").strip()
                
                return SourceType.BOOK, components
        
        # Check for Congressional materials
        if "Cong. Rec." in citation:
            return SourceType.CONGRESSIONAL_RECORD, components
        elif "H.R. Rep." in citation or "H. Rep." in citation:
            return SourceType.HOUSE_REPORT, components
        elif "S. Rep." in citation:
            return SourceType.SENATE_REPORT, components
        elif "Hearing" in citation:
            return SourceType.HEARING, components
        
        # Default to unknown
        return SourceType.UNKNOWN, components
    
    def _identify_case_type(self, reporter: str) -> SourceType:
        """Identify the specific type of case based on reporter"""
        if not reporter:
            return SourceType.UNKNOWN
        
        # Normalize reporter
        reporter = reporter.strip()
        
        # Check Supreme Court
        if reporter in self.SUPREME_COURT_REPORTERS:
            return SourceType.SUPREME_COURT
        
        # Check Federal Appellate
        if reporter in self.FEDERAL_APPELLATE_REPORTERS:
            return SourceType.FEDERAL_APPELLATE
        
        # Check Federal District
        if reporter in self.FEDERAL_DISTRICT_REPORTERS:
            return SourceType.FEDERAL_DISTRICT
        
        # Check State (simplified - would need more logic for specific state courts)
        if reporter in self.STATE_REPORTERS:
            # Try to determine if high court or appellate
            if any(x in reporter for x in ["Cal. 4th", "Cal. 5th", "N.Y.2d", "N.Y.3d"]):
                return SourceType.STATE_HIGH_COURT
            elif "App." in reporter or "A.D." in reporter:
                return SourceType.STATE_APPELLATE
            else:
                return SourceType.STATE_HIGH_COURT  # Default state cases to high court
        
        return SourceType.UNKNOWN
    
    def _is_law_review(self, journal: str) -> bool:
        """Check if a journal name is likely a law review"""
        journal_upper = journal.upper()
        return any(signal.upper() in journal_upper for signal in self.LAW_REVIEW_SIGNALS)
    
    def get_priority(self, source_type: SourceType) -> int:
        """
        Get retrieval priority based on Member Handbook hierarchy
        Lower number = higher priority
        """
        priority_map = {
            # Highest priority - authoritative sources
            SourceType.SUPREME_COURT: 1,
            SourceType.FEDERAL_STATUTE: 1,
            SourceType.FEDERAL_REGULATION: 2,
            
            # High priority - federal courts
            SourceType.FEDERAL_APPELLATE: 3,
            SourceType.FEDERAL_DISTRICT: 4,
            
            # Medium priority - state courts
            SourceType.STATE_HIGH_COURT: 5,
            SourceType.STATE_APPELLATE: 6,
            SourceType.STATE_TRIAL: 7,
            SourceType.STATE_STATUTE: 5,
            SourceType.STATE_REGULATION: 6,
            
            # Lower priority - secondary sources
            SourceType.LAW_REVIEW_ARTICLE: 8,
            SourceType.BOOK: 9,
            SourceType.TREATISE: 9,
            
            # Lowest priority - other materials
            SourceType.CONGRESSIONAL_RECORD: 10,
            SourceType.HOUSE_REPORT: 10,
            SourceType.SENATE_REPORT: 10,
            SourceType.HEARING: 10,
            SourceType.NEWS_ARTICLE: 11,
            SourceType.WEBSITE: 12,
            SourceType.BRIEF: 11,
            SourceType.ORAL_ARGUMENT: 11,
            SourceType.TRANSCRIPT: 11,
            SourceType.UNKNOWN: 99
        }
        return priority_map.get(source_type, 99)


def test_identifier():
    """Test the source identifier with sample citations"""
    identifier = SourceIdentifier()
    
    test_citations = [
        "Alice Corp. v. CLS Bank Int'l, 573 U.S. 208, 216 (2014)",
        "Mayo Collaborative Servs. v. Prometheus Labs., Inc., 566 U.S. 66 (2012)",
        "35 U.S.C. § 101 (2018)",
        "17 C.F.R. § 240.10b-5 (2021)",
        "Mark A. Lemley, Software Patents and the Return of Functional Claiming, 2013 Wis. L. Rev. 905",
        "ROBERT P. MERGES & JOHN F. DUFFY, PATENT LAW AND POLICY (7th ed. 2017)",
        "H.R. Rep. No. 114-114 (2015)",
        "Apple Inc. v. Samsung Elecs. Co., 839 F.3d 1034 (Fed. Cir. 2016)",
        "Oracle Am., Inc. v. Google Inc., 750 F.3d 1339 (Fed. Cir. 2014)",
        "Impression Prods., Inc. v. Lexmark Int'l, Inc., 816 F.3d 721 (Fed. Cir. 2016)",
    ]
    
    for citation in test_citations:
        source_type, components = identifier.identify(citation)
        priority = identifier.get_priority(source_type)
        print(f"\nCitation: {citation[:80]}...")
        print(f"Type: {source_type.value}")
        print(f"Priority: {priority}")
        if components.party1:
            print(f"  Parties: {components.party1} v. {components.party2}")
        if components.volume:
            print(f"  Volume: {components.volume}")
        if components.reporter:
            print(f"  Reporter: {components.reporter}")
        if components.title_number:
            print(f"  Title: {components.title_number}")
        if components.section:
            print(f"  Section: {components.section}")
        if components.author:
            print(f"  Author: {components.author}")


if __name__ == "__main__":
    test_identifier()