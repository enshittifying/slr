#!/usr/bin/env python3
"""
Stanford Law Review Sourcepull System
Implements the complete retrieval hierarchy from the Member Handbook
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import requests

from src.core.source_identifier import SourceIdentifier, SourceType, CitationComponents
from src.utils.api_logger import get_api_logger, log_api_usage


@dataclass
class RetrievalAttempt:
    """Record of a single retrieval attempt"""
    source: str
    timestamp: str
    success: bool
    message: str
    file_path: Optional[str] = None
    url: Optional[str] = None
    

@dataclass 
class SourcepullResult:
    """Complete result for a single source"""
    footnote_number: int
    citation_text: str
    source_type: SourceType
    components: CitationComponents
    retrieval_attempts: List[RetrievalAttempt]
    final_status: str  # "success", "partial", "failed"
    reasoning: str
    final_file_path: Optional[str] = None
    requires_manual: bool = False
    manual_instructions: Optional[str] = None


class RetrievalStrategy:
    """
    Defines retrieval strategies for each source type
    Following Member Handbook hierarchy
    """
    
    def __init__(self, api_keys: Dict[str, Any]):
        self.api_keys = api_keys
        self.strategies = self._build_strategies()
    
    def _build_strategies(self) -> Dict[SourceType, List[str]]:
        """Build retrieval strategy hierarchy for each source type"""
        return {
            # Supreme Court - try official first
            SourceType.SUPREME_COURT: [
                "supreme_court_website",
                "courtlistener",
                "justia",
                "google_scholar",
                "heinonline",
                "westlaw",
                "lexis"
            ],
            
            # Federal Appellate
            SourceType.FEDERAL_APPELLATE: [
                "courtlistener",
                "court_website",
                "justia",
                "google_scholar",
                "heinonline",
                "westlaw",
                "lexis"
            ],
            
            # Federal District
            SourceType.FEDERAL_DISTRICT: [
                "courtlistener",
                "pacer",
                "justia",
                "google_scholar",
                "westlaw",
                "lexis"
            ],
            
            # Federal Statutes
            SourceType.FEDERAL_STATUTE: [
                "govinfo",
                "congress_gov",
                "cornell_lii",
                "justia",
                "heinonline",
                "westlaw",
                "lexis"
            ],
            
            # Federal Regulations
            SourceType.FEDERAL_REGULATION: [
                "govinfo",
                "ecfr",
                "cornell_lii",
                "justia",
                "westlaw",
                "lexis"
            ],
            
            # State Courts
            SourceType.STATE_HIGH_COURT: [
                "state_court_website",
                "courtlistener",
                "justia",
                "google_scholar",
                "westlaw",
                "lexis"
            ],
            
            SourceType.STATE_APPELLATE: [
                "state_court_website",
                "courtlistener",
                "justia",
                "google_scholar",
                "westlaw",
                "lexis"
            ],
            
            # Law Review Articles
            SourceType.LAW_REVIEW_ARTICLE: [
                "journal_website",
                "ssrn",
                "heinonline",
                "crossref",
                "google_scholar",
                "westlaw",
                "lexis"
            ],
            
            # Books
            SourceType.BOOK: [
                "publisher_website",
                "google_books",
                "worldcat",
                "library_catalog",
                "amazon"
            ],
            
            # Congressional Materials
            SourceType.CONGRESSIONAL_RECORD: [
                "congress_gov",
                "govinfo",
                "heinonline"
            ],
            
            SourceType.HOUSE_REPORT: [
                "congress_gov",
                "govinfo",
                "heinonline"
            ],
            
            SourceType.SENATE_REPORT: [
                "congress_gov",
                "govinfo",
                "heinonline"
            ],
            
            # Default fallback
            SourceType.UNKNOWN: [
                "google_scholar",
                "google_search"
            ]
        }
    
    def get_strategies(self, source_type: SourceType) -> List[str]:
        """Get ordered list of retrieval strategies for a source type"""
        return self.strategies.get(source_type, self.strategies[SourceType.UNKNOWN])


class SourcepullSystem:
    """
    Main sourcepull system implementing Member Handbook procedures
    """
    
    def __init__(self, config_path: str = "config/api_keys.json"):
        """Initialize the sourcepull system"""
        # Load API keys
        self.api_keys = self._load_api_keys(config_path)
        
        # Initialize components
        self.identifier = SourceIdentifier()
        self.strategy = RetrievalStrategy(self.api_keys)
        
        # Setup output directories
        self.output_dir = Path("output/data/Sourcepull")
        self.retrieved_dir = self.output_dir / "Retrieved"
        self.retrieved_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.log_dir = Path("output/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._setup_logging()
        
        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Stanford Law Review Sourcepull System'
        })
        
    def _load_api_keys(self, config_path: str) -> Dict[str, Any]:
        """Load API keys from configuration file"""
        config_file = Path(config_path)
        if not config_file.exists():
            logging.warning(f"API keys file not found: {config_path}")
            return {}
        
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_file = self.log_dir / f"sourcepull_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def process_citation(self, footnote_number: int, citation_text: str) -> SourcepullResult:
        """
        Process a single citation through the sourcepull system
        
        Args:
            footnote_number: The footnote number in the article
            citation_text: The full citation text
            
        Returns:
            SourcepullResult with retrieval details
        """
        self.logger.info(f"Processing FN{footnote_number}: {citation_text[:100]}...")
        
        # Identify source type and extract components
        source_type, components = self.identifier.identify(citation_text)
        priority = self.identifier.get_priority(source_type)
        
        self.logger.info(f"  Identified as: {source_type.value} (priority: {priority})")
        
        # Initialize result
        result = SourcepullResult(
            footnote_number=footnote_number,
            citation_text=citation_text,
            source_type=source_type,
            components=components,
            retrieval_attempts=[],
            final_status="failed",
            reasoning=f"Source type: {source_type.value}, Priority level: {priority}"
        )
        
        # Get retrieval strategies
        strategies = self.strategy.get_strategies(source_type)
        
        # Try each strategy in order
        for strategy in strategies:
            if result.final_status == "success":
                break
                
            attempt = self._try_retrieval_strategy(
                strategy, source_type, components, footnote_number
            )
            result.retrieval_attempts.append(attempt)
            
            if attempt.success:
                result.final_status = "success"
                result.final_file_path = attempt.file_path
                self.logger.info(f"  ✓ Success with {strategy}")
                break
            else:
                self.logger.info(f"  ✗ Failed with {strategy}: {attempt.message}")
        
        # Set manual retrieval instructions if failed
        if result.final_status == "failed":
            result.requires_manual = True
            result.manual_instructions = self._get_manual_instructions(source_type, components)
            self.logger.warning(f"  ⚠ Requires manual retrieval for FN{footnote_number}")
        
        return result
    
    def _try_retrieval_strategy(self, strategy: str, source_type: SourceType, 
                                components: CitationComponents, 
                                footnote_number: int) -> RetrievalAttempt:
        """Try a specific retrieval strategy"""
        timestamp = datetime.now().isoformat()
        
        # Map strategies to methods
        strategy_methods = {
            "courtlistener": self._retrieve_courtlistener,
            "govinfo": self._retrieve_govinfo,
            "supreme_court_website": self._retrieve_supreme_court,
            "justia": self._retrieve_justia,
            "google_scholar": self._retrieve_google_scholar,
            "ssrn": self._retrieve_ssrn,
            "congress_gov": self._retrieve_congress,
            "cornell_lii": self._retrieve_cornell,
            "ecfr": self._retrieve_ecfr,
            "crossref": self._retrieve_crossref,
            "heinonline": self._retrieve_heinonline,
            "westlaw": self._retrieve_westlaw,
            "lexis": self._retrieve_lexis,
        }
        
        # Get the appropriate method
        method = strategy_methods.get(strategy)
        
        if not method:
            return RetrievalAttempt(
                source=strategy,
                timestamp=timestamp,
                success=False,
                message=f"Strategy '{strategy}' not implemented"
            )
        
        # Only try enabled APIs
        if strategy in ["courtlistener", "govinfo", "crossref", "google_books"]:
            api_config = self.api_keys.get(strategy, {})
            if not api_config.get("enabled", False):
                return RetrievalAttempt(
                    source=strategy,
                    timestamp=timestamp,
                    success=False,
                    message=f"API not enabled in configuration"
                )
        
        # Try the retrieval
        try:
            return method(source_type, components, footnote_number)
        except Exception as e:
            return RetrievalAttempt(
                source=strategy,
                timestamp=timestamp,
                success=False,
                message=f"Error: {str(e)}"
            )
    
    def _retrieve_courtlistener(self, source_type: SourceType, 
                                components: CitationComponents,
                                footnote_number: int) -> RetrievalAttempt:
        """Retrieve from CourtListener API"""
        timestamp = datetime.now().isoformat()
        
        if source_type not in [SourceType.SUPREME_COURT, SourceType.FEDERAL_APPELLATE, 
                               SourceType.FEDERAL_DISTRICT, SourceType.STATE_HIGH_COURT,
                               SourceType.STATE_APPELLATE]:
            return RetrievalAttempt(
                source="courtlistener",
                timestamp=timestamp,
                success=False,
                message="Not a case citation"
            )
        
        # Build search query
        api_token = self.api_keys.get("courtlistener", {}).get("token")
        if not api_token or api_token == "YOUR_COURTLISTENER_TOKEN_HERE":
            return RetrievalAttempt(
                source="courtlistener",
                timestamp=timestamp,
                success=False,
                message="CourtListener API token not configured"
            )
        
        # Search for the case
        search_url = "https://www.courtlistener.com/api/rest/v3/search/"
        params = {
            "q": f"{components.party1} {components.party2}",
            "type": "o",  # opinions
            "order_by": "score desc"
        }
        headers = {"Authorization": f"Token {api_token}"}
        
        try:
            # Log API call
            log_api_usage(
                api_name="courtlistener",
                endpoint=search_url,
                method="GET",
                parameters=params,
                footnote_number=footnote_number,
                citation_text=f"{components.party1} v. {components.party2}"
            )
            
            response = self.session.get(search_url, params=params, headers=headers, timeout=10)
            
            # Log response
            log_api_usage(
                api_name="courtlistener",
                endpoint=search_url,
                method="GET",
                parameters=params,
                response_code=response.status_code,
                success=(response.status_code == 200),
                footnote_number=footnote_number
            )
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                if results:
                    # Try to get the PDF
                    case_id = results[0].get("id")
                    pdf_url = f"https://www.courtlistener.com/api/rest/v3/opinions/{case_id}/pdf/"
                    
                    # Log PDF retrieval attempt
                    log_api_usage(
                        api_name="courtlistener",
                        endpoint=pdf_url,
                        method="GET",
                        footnote_number=footnote_number
                    )
                    
                    pdf_response = self.session.get(pdf_url, headers=headers, timeout=30)
                    
                    # Log PDF retrieval result
                    log_api_usage(
                        api_name="courtlistener",
                        endpoint=pdf_url,
                        method="GET",
                        response_code=pdf_response.status_code,
                        success=(pdf_response.status_code == 200),
                        footnote_number=footnote_number
                    )
                    
                    if pdf_response.status_code == 200:
                        # Save the PDF
                        filename = self._generate_filename(footnote_number, components)
                        file_path = self.retrieved_dir / filename
                        
                        with open(file_path, 'wb') as f:
                            f.write(pdf_response.content)
                        
                        return RetrievalAttempt(
                            source="courtlistener",
                            timestamp=timestamp,
                            success=True,
                            message="Retrieved from CourtListener",
                            file_path=str(file_path),
                            url=pdf_url
                        )
                        
        except Exception as e:
            # Log error
            log_api_usage(
                api_name="courtlistener",
                endpoint=search_url,
                method="GET",
                success=False,
                error_message=str(e),
                footnote_number=footnote_number
            )
        
        return RetrievalAttempt(
            source="courtlistener",
            timestamp=timestamp,
            success=False,
            message="Case not found in CourtListener"
        )
    
    def _retrieve_govinfo(self, source_type: SourceType,
                         components: CitationComponents,
                         footnote_number: int) -> RetrievalAttempt:
        """Retrieve from GovInfo API using collections endpoint"""
        timestamp = datetime.now().isoformat()
        
        if source_type not in [SourceType.FEDERAL_STATUTE, SourceType.FEDERAL_REGULATION]:
            return RetrievalAttempt(
                source="govinfo",
                timestamp=timestamp,
                success=False,
                message="Not a federal statute or regulation"
            )
        
        api_key = self.api_keys.get("govinfo", {}).get("api_key")
        if not api_key or api_key == "YOUR_GOVINFO_API_KEY_HERE":
            return RetrievalAttempt(
                source="govinfo",
                timestamp=timestamp,
                success=False,
                message="GovInfo API key not configured"
            )
        
        # Try collections endpoint first (simpler and more reliable)
        if source_type == SourceType.FEDERAL_STATUTE and components.title_number and components.section:
            try:
                # Try browsing collections for U.S. Code
                collections_url = f"https://api.govinfo.gov/collections/USCODE?api_key={api_key}"
                
                log_api_usage(
                    api_name="govinfo",
                    endpoint="https://api.govinfo.gov/collections/USCODE",
                    method="GET",
                    parameters={"title": components.title_number, "section": components.section},
                    footnote_number=footnote_number,
                    citation_text=f"{components.title_number} U.S.C. § {components.section}"
                )
                
                response = self.session.get(collections_url, timeout=10)
                
                log_api_usage(
                    api_name="govinfo",
                    endpoint="https://api.govinfo.gov/collections/USCODE", 
                    method="GET",
                    response_code=response.status_code,
                    success=(response.status_code == 200),
                    footnote_number=footnote_number
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Look for packages that might contain our statute
                    if "packages" in data:
                        for package in data["packages"][:5]:  # Check first 5 packages
                            package_id = package.get("packageId")
                            
                            # Try to get package details to find our section
                            if package_id and str(components.title_number) in package_id:
                                package_url = f"https://api.govinfo.gov/packages/{package_id}?api_key={api_key}"
                                
                                package_response = self.session.get(package_url, timeout=10)
                                if package_response.status_code == 200:
                                    package_data = package_response.json()
                                    
                                    # Look for PDF download link
                                    download_url = package_data.get("download", {}).get("pdfLink")
                                    
                                    if download_url:
                                        # Try to download the PDF
                                        pdf_url = f"{download_url}?api_key={api_key}"
                                        
                                        log_api_usage(
                                            api_name="govinfo",
                                            endpoint=download_url,
                                            method="GET",
                                            footnote_number=footnote_number
                                        )
                                        
                                        pdf_response = self.session.get(pdf_url, timeout=30)
                                        
                                        log_api_usage(
                                            api_name="govinfo",
                                            endpoint=download_url,
                                            method="GET",
                                            response_code=pdf_response.status_code,
                                            success=(pdf_response.status_code == 200),
                                            footnote_number=footnote_number
                                        )
                                        
                                        if pdf_response.status_code == 200:
                                            # Save the PDF
                                            filename = self._generate_filename(footnote_number, components)
                                            file_path = self.retrieved_dir / filename
                                            
                                            with open(file_path, 'wb') as f:
                                                f.write(pdf_response.content)
                                            
                                            return RetrievalAttempt(
                                                source="govinfo",
                                                timestamp=timestamp,
                                                success=True,
                                                message="Retrieved from GovInfo collections",
                                                file_path=str(file_path),
                                                url=download_url
                                            )
                
            except Exception as e:
                log_api_usage(
                    api_name="govinfo",
                    endpoint="https://api.govinfo.gov/collections/USCODE",
                    method="GET",
                    success=False,
                    error_message=str(e),
                    footnote_number=footnote_number
                )
        
        return RetrievalAttempt(
            source="govinfo",
            timestamp=timestamp,
            success=False,
            message="Document not found in GovInfo"
        )
    
    def _retrieve_supreme_court(self, source_type: SourceType,
                                components: CitationComponents,
                                footnote_number: int) -> RetrievalAttempt:
        """Retrieve from Supreme Court website"""
        timestamp = datetime.now().isoformat()
        
        if source_type != SourceType.SUPREME_COURT:
            return RetrievalAttempt(
                source="supreme_court_website",
                timestamp=timestamp,
                success=False,
                message="Not a Supreme Court case"
            )
        
        # Try CourtListener first for Supreme Court cases
        try:
            courtlistener_result = self._retrieve_courtlistener(source_type, components, footnote_number)
            if courtlistener_result.success:
                # Return success but with supreme court source
                return RetrievalAttempt(
                    source="supreme_court_website",
                    timestamp=timestamp,
                    success=True,
                    message="Retrieved via CourtListener",
                    file_path=courtlistener_result.file_path,
                    url=courtlistener_result.url
                )
        except:
            pass
        
        # Supreme Court provides bound volumes as PDFs
        if components.volume and int(components.volume) >= 502:  # Volumes 502+ are available
            volume_url = f"https://www.supremecourt.gov/opinions/boundvolumes/{components.volume}bv.pdf"
            
            try:
                log_api_usage(
                    api_name="supreme_court",
                    endpoint=volume_url,
                    method="HEAD",
                    footnote_number=footnote_number,
                    citation_text=f"{components.party1} v. {components.party2}"
                )
                
                response = self.session.head(volume_url, timeout=5)
                
                log_api_usage(
                    api_name="supreme_court",
                    endpoint=volume_url,
                    method="HEAD",
                    response_code=response.status_code,
                    success=(response.status_code == 200),
                    footnote_number=footnote_number
                )
                
                if response.status_code == 200:
                    return RetrievalAttempt(
                        source="supreme_court_website",
                        timestamp=timestamp,
                        success=True,
                        message=f"Available in bound volume {components.volume} - manual download required",
                        url=volume_url
                    )
            except Exception as e:
                log_api_usage(
                    api_name="supreme_court",
                    endpoint=volume_url,
                    method="HEAD",
                    success=False,
                    error_message=str(e),
                    footnote_number=footnote_number
                )
        
        return RetrievalAttempt(
            source="supreme_court_website",
            timestamp=timestamp,
            success=False,
            message="Not available from Supreme Court website"
        )
    
    def _retrieve_justia(self, source_type: SourceType,
                        components: CitationComponents,
                        footnote_number: int) -> RetrievalAttempt:
        """Retrieve from Justia (free legal database)"""
        timestamp = datetime.now().isoformat()
        
        try:
            if source_type == SourceType.FEDERAL_STATUTE and components.title_number and components.section:
                # Justia has U.S. Code sections
                # Format: https://law.justia.com/codes/us/{title}/{section}/
                justia_url = f"https://law.justia.com/codes/us/{components.title_number}/{components.section}/"
                
                log_api_usage(
                    api_name="justia",
                    endpoint=justia_url,
                    method="GET",
                    parameters={"title": components.title_number, "section": components.section},
                    footnote_number=footnote_number,
                    citation_text=f"{components.title_number} U.S.C. § {components.section}"
                )
                
                response = self.session.get(justia_url, timeout=10)
                
                log_api_usage(
                    api_name="justia",
                    endpoint=justia_url,
                    method="GET",
                    response_code=response.status_code,
                    success=(response.status_code == 200),
                    footnote_number=footnote_number
                )
                
                if response.status_code == 200:
                    # Check if this is actually a statute page
                    if "U.S.C." in response.text and components.section in response.text:
                        # Save as HTML since Justia doesn't provide PDFs
                        filename = self._generate_filename(footnote_number, components, extension=".html")
                        file_path = self.retrieved_dir / filename
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        
                        return RetrievalAttempt(
                            source="justia",
                            timestamp=timestamp,
                            success=True,
                            message="Retrieved from Justia (HTML)",
                            file_path=str(file_path),
                            url=justia_url
                        )
                        
            elif source_type in [SourceType.SUPREME_COURT, SourceType.FEDERAL_APPELLATE, SourceType.FEDERAL_DISTRICT]:
                # Justia has federal cases
                if components.party1 and components.party2:
                    # Try searching by case name
                    case_search = f"{components.party1} {components.party2}".replace(" v. ", " ")
                    # Simplified - would need proper case search implementation
                    pass
                    
        except Exception as e:
            log_api_usage(
                api_name="justia",
                endpoint="https://law.justia.com/",
                method="GET",
                success=False,
                error_message=str(e),
                footnote_number=footnote_number
            )
        
        return RetrievalAttempt(
            source="justia",
            timestamp=timestamp,
            success=False,
            message="Document not found in Justia"
        )
    
    def _retrieve_google_scholar(self, source_type: SourceType,
                                 components: CitationComponents,
                                 footnote_number: int) -> RetrievalAttempt:
        """Retrieve from Google Scholar"""
        timestamp = datetime.now().isoformat()
        
        # Google Scholar can find many academic and legal sources
        # Would need to implement search and PDF extraction
        return RetrievalAttempt(
            source="google_scholar",
            timestamp=timestamp,
            success=False,
            message="Google Scholar retrieval not implemented"
        )
    
    def _retrieve_ssrn(self, source_type: SourceType,
                      components: CitationComponents,
                      footnote_number: int) -> RetrievalAttempt:
        """Retrieve from SSRN"""
        timestamp = datetime.now().isoformat()
        
        if source_type != SourceType.LAW_REVIEW_ARTICLE:
            return RetrievalAttempt(
                source="ssrn",
                timestamp=timestamp,
                success=False,
                message="Not a law review article"
            )
        
        # SSRN provides many legal academic papers
        # Would search by author and title
        return RetrievalAttempt(
            source="ssrn",
            timestamp=timestamp,
            success=False,
            message="SSRN retrieval not implemented"
        )
    
    def _retrieve_congress(self, source_type: SourceType,
                          components: CitationComponents,
                          footnote_number: int) -> RetrievalAttempt:
        """Retrieve from Congress.gov"""
        timestamp = datetime.now().isoformat()
        
        # Congress.gov provides legislative materials
        return RetrievalAttempt(
            source="congress_gov",
            timestamp=timestamp,
            success=False,
            message="Congress.gov retrieval not implemented"
        )
    
    def _retrieve_cornell(self, source_type: SourceType,
                         components: CitationComponents,
                         footnote_number: int) -> RetrievalAttempt:
        """Retrieve from Cornell Legal Information Institute"""
        timestamp = datetime.now().isoformat()
        
        if source_type == SourceType.FEDERAL_STATUTE and components.title_number and components.section:
            try:
                # Cornell LII has direct URLs for U.S. Code sections
                # Format: https://www.law.cornell.edu/uscode/text/{title}/{section}
                cornell_url = f"https://www.law.cornell.edu/uscode/text/{components.title_number}/{components.section}"
                
                log_api_usage(
                    api_name="cornell_lii",
                    endpoint=cornell_url,
                    method="GET",
                    parameters={"title": components.title_number, "section": components.section},
                    footnote_number=footnote_number,
                    citation_text=f"{components.title_number} U.S.C. § {components.section}"
                )
                
                response = self.session.get(cornell_url, timeout=10)
                
                log_api_usage(
                    api_name="cornell_lii",
                    endpoint=cornell_url,
                    method="GET",
                    response_code=response.status_code,
                    success=(response.status_code == 200),
                    footnote_number=footnote_number
                )
                
                if response.status_code == 200:
                    # Check if this is actually the statute page (not a 404 page)
                    if "U.S.C." in response.text and components.section in response.text:
                        # Create HTML file since Cornell doesn't provide PDFs
                        filename = self._generate_filename(footnote_number, components, extension=".html")
                        file_path = self.retrieved_dir / filename
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        
                        return RetrievalAttempt(
                            source="cornell_lii",
                            timestamp=timestamp,
                            success=True,
                            message="Retrieved from Cornell LII (HTML)",
                            file_path=str(file_path),
                            url=cornell_url
                        )
                
            except Exception as e:
                log_api_usage(
                    api_name="cornell_lii",
                    endpoint=f"https://www.law.cornell.edu/uscode/text/{components.title_number}/{components.section}",
                    method="GET",
                    success=False,
                    error_message=str(e),
                    footnote_number=footnote_number
                )
        
        elif source_type == SourceType.SUPREME_COURT:
            # Cornell also has Supreme Court cases
            try:
                # Try to find case by name search
                if components.case_name:
                    # Use Cornell's search (simplified implementation)
                    search_url = f"https://www.law.cornell.edu/supct/"
                    # This would need a proper search implementation
                    pass
                    
            except Exception:
                pass
        
        return RetrievalAttempt(
            source="cornell_lii",
            timestamp=timestamp,
            success=False,
            message="Document not found in Cornell LII"
        )
    
    def _retrieve_ecfr(self, source_type: SourceType,
                      components: CitationComponents,
                      footnote_number: int) -> RetrievalAttempt:
        """Retrieve from eCFR"""
        timestamp = datetime.now().isoformat()
        
        if source_type != SourceType.FEDERAL_REGULATION:
            return RetrievalAttempt(
                source="ecfr",
                timestamp=timestamp,
                success=False,
                message="Not a federal regulation"
            )
        
        # eCFR.gov provides federal regulations
        return RetrievalAttempt(
            source="ecfr",
            timestamp=timestamp,
            success=False,
            message="eCFR retrieval not implemented"
        )
    
    def _retrieve_crossref(self, source_type: SourceType,
                          components: CitationComponents,
                          footnote_number: int) -> RetrievalAttempt:
        """Retrieve from CrossRef"""
        timestamp = datetime.now().isoformat()
        
        if source_type != SourceType.LAW_REVIEW_ARTICLE:
            return RetrievalAttempt(
                source="crossref",
                timestamp=timestamp,
                success=False,
                message="Not an article citation"
            )
        
        # CrossRef provides DOI lookup for academic articles
        return RetrievalAttempt(
            source="crossref",
            timestamp=timestamp,
            success=False,
            message="CrossRef retrieval not implemented"
        )
    
    def _retrieve_heinonline(self, source_type: SourceType,
                            components: CitationComponents,
                            footnote_number: int) -> RetrievalAttempt:
        """Retrieve from HeinOnline (premium)"""
        timestamp = datetime.now().isoformat()
        
        if not self.api_keys.get("heinonline", {}).get("enabled", False):
            return RetrievalAttempt(
                source="heinonline",
                timestamp=timestamp,
                success=False,
                message="HeinOnline not configured"
            )
        
        # HeinOnline is a premium database
        return RetrievalAttempt(
            source="heinonline",
            timestamp=timestamp,
            success=False,
            message="HeinOnline requires manual access"
        )
    
    def _retrieve_westlaw(self, source_type: SourceType,
                         components: CitationComponents,
                         footnote_number: int) -> RetrievalAttempt:
        """Retrieve from Westlaw (premium)"""
        timestamp = datetime.now().isoformat()
        
        if not self.api_keys.get("westlaw", {}).get("enabled", False):
            return RetrievalAttempt(
                source="westlaw",
                timestamp=timestamp,
                success=False,
                message="Westlaw not configured"
            )
        
        # Westlaw is a premium database
        return RetrievalAttempt(
            source="westlaw",
            timestamp=timestamp,
            success=False,
            message="Westlaw requires manual access"
        )
    
    def _retrieve_lexis(self, source_type: SourceType,
                       components: CitationComponents,
                       footnote_number: int) -> RetrievalAttempt:
        """Retrieve from Lexis (premium)"""
        timestamp = datetime.now().isoformat()
        
        if not self.api_keys.get("lexis", {}).get("enabled", False):
            return RetrievalAttempt(
                source="lexis",
                timestamp=timestamp,
                success=False,
                message="Lexis not configured"
            )
        
        # Lexis is a premium database
        return RetrievalAttempt(
            source="lexis",
            timestamp=timestamp,
            success=False,
            message="Lexis requires manual access"
        )
    
    def _generate_filename(self, footnote_number: int, components: CitationComponents, extension: str = ".pdf") -> str:
        """Generate filename for retrieved source"""
        # Create short name from components
        if components.party1 and components.party2:
            short_name = f"{components.party1}_v_{components.party2}"
        elif components.author:
            short_name = components.author.split()[-1] if components.author else "Unknown"
        elif components.title_number and components.section:
            short_name = f"{components.title_number}USC{components.section}"
        else:
            short_name = "source"
        
        # Clean filename
        short_name = "".join(c for c in short_name if c.isalnum() or c in "_-")[:50]
        
        return f"FN{footnote_number:03d}_{short_name}{extension}"
    
    def _get_manual_instructions(self, source_type: SourceType, 
                                 components: CitationComponents) -> str:
        """Get manual retrieval instructions based on source type"""
        instructions = {
            SourceType.SUPREME_COURT: "Check Supreme Court website or Westlaw/Lexis",
            SourceType.FEDERAL_APPELLATE: "Check circuit court website or PACER",
            SourceType.FEDERAL_DISTRICT: "Check PACER or court website",
            SourceType.STATE_HIGH_COURT: "Check state court website or Westlaw/Lexis",
            SourceType.LAW_REVIEW_ARTICLE: "Check journal website, HeinOnline, or request ILL",
            SourceType.BOOK: "Check library catalog or request ILL",
            SourceType.FEDERAL_STATUTE: "Check United States Code online",
            SourceType.FEDERAL_REGULATION: "Check Code of Federal Regulations",
        }
        
        base_instruction = instructions.get(source_type, "Manual search required")
        
        # Add specific details
        if components.volume and components.reporter and components.page:
            base_instruction += f" ({components.volume} {components.reporter} {components.page})"
        elif components.title_number and components.section:
            base_instruction += f" (Title {components.title_number}, Section {components.section})"
        
        return base_instruction
    
    def generate_report(self, results: List[SourcepullResult]) -> Dict[str, Any]:
        """Generate a summary report of sourcepull results"""
        total = len(results)
        successful = sum(1 for r in results if r.final_status == "success")
        failed = sum(1 for r in results if r.final_status == "failed")
        
        # Group by source type
        by_type = {}
        for result in results:
            type_name = result.source_type.value
            if type_name not in by_type:
                by_type[type_name] = {"total": 0, "success": 0, "failed": 0}
            by_type[type_name]["total"] += 1
            if result.final_status == "success":
                by_type[type_name]["success"] += 1
            elif result.final_status == "failed":
                by_type[type_name]["failed"] += 1
        
        # Find which retrieval sources were most successful
        source_stats = {}
        for result in results:
            for attempt in result.retrieval_attempts:
                if attempt.source not in source_stats:
                    source_stats[attempt.source] = {"attempts": 0, "successes": 0}
                source_stats[attempt.source]["attempts"] += 1
                if attempt.success:
                    source_stats[attempt.source]["successes"] += 1
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_sources": total,
                "successful": successful,
                "failed": failed,
                "success_rate": f"{(successful/total*100):.1f}%" if total > 0 else "0%"
            },
            "by_source_type": by_type,
            "retrieval_sources": source_stats,
            "manual_required": [
                {
                    "footnote": r.footnote_number,
                    "citation": r.citation_text[:100],
                    "instructions": r.manual_instructions
                }
                for r in results if r.requires_manual
            ]
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: str = "sourcepull_report.json"):
        """Save report to file"""
        report_path = self.output_dir / filename
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        self.logger.info(f"Report saved to {report_path}")
        return report_path


def test_system():
    """Test the sourcepull system"""
    system = SourcepullSystem()
    
    test_citations = [
        (1, "Alice Corp. v. CLS Bank Int'l, 573 U.S. 208 (2014)"),
        (2, "35 U.S.C. § 101 (2018)"),
        (3, "Mark A. Lemley, Software Patents, 2013 Wis. L. Rev. 905"),
    ]
    
    results = []
    for fn_num, citation in test_citations:
        print(f"\nProcessing FN{fn_num}: {citation}")
        result = system.process_citation(fn_num, citation)
        results.append(result)
        
        print(f"  Type: {result.source_type.value}")
        print(f"  Status: {result.final_status}")
        if result.final_file_path:
            print(f"  File: {result.final_file_path}")
        if result.requires_manual:
            print(f"  Manual: {result.manual_instructions}")
    
    # Generate report
    report = system.generate_report(results)
    print("\n" + "="*60)
    print("SOURCEPULL REPORT")
    print("="*60)
    print(f"Success Rate: {report['summary']['success_rate']}")
    print(f"Sources Retrieved: {report['summary']['successful']}/{report['summary']['total']}")
    
    if report['manual_required']:
        print("\nManual Retrieval Required:")
        for item in report['manual_required']:
            print(f"  FN{item['footnote']}: {item['instructions']}")


if __name__ == "__main__":
    test_system()