#!/usr/bin/env python3
"""
PDF Retrieval System for Stanford Law Review
Gets actual readable PDFs from various sources
"""

import os
import logging
import requests
import urllib3
import fitz  # PyMuPDF for PDF validation

# Suppress SSL warnings for government PDF downloads
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

from src.core.enhanced_gpt_parser import Citation
from src.utils.api_logger import log_api_usage


@dataclass
class RetrievalResult:
    """Result of PDF retrieval attempt"""
    citation_id: str
    source_name: str
    success: bool
    file_path: Optional[str]
    file_size_bytes: Optional[int]
    is_valid_pdf: bool
    page_count: Optional[int]
    error_message: Optional[str]
    retrieval_url: Optional[str]
    retrieved_at: str


class PDFRetriever:
    """Retrieves actual readable PDFs from various sources"""
    
    def __init__(self, api_keys: Dict[str, Any], output_dir: Path):
        """Initialize with API keys and output directory"""
        self.api_keys = api_keys
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # HTTP session for efficiency
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Stanford Law Review Sourcepull System (Academic Research)'
        })
        
        # Source priority mapping
        self.source_priorities = {
            'case': [
                'supreme_court_official',
                'courtlistener_pdf', 
                'google_scholar_pdf',
                'justia_pdf',
                'caselaw_access_project'
            ],
            'statute': [
                'uscode_house_gov',
                'legal_information_institute',
                'govinfo_pdf',
                'congress_gov_pdf'
            ],
            'regulation': [
                'govinfo_pdf',
                'ecfr_pdf',
                'federal_register_pdf'
            ],
            'article': [
                'publisher_pdf',
                'repository_pdf',
                'doi_link',
                'google_scholar_pdf'
            ]
        }
    
    def _get_intelligent_sources(self, citation: Citation) -> List[str]:
        """Intelligently route citations based on court and reporter"""
        if citation.citation_type == 'case':
            # Extract reporter from full text to determine court
            full_text = citation.full_text.lower()
            
            # Supreme Court cases - only these should go to supremecourt.gov
            if ' u.s. ' in full_text:
                return ['supreme_court_official', 'courtlistener_pdf', 'justia_pdf', 'google_scholar_pdf']
            
            # Federal Circuit and other federal cases - skip Supreme Court
            elif 'f.3d' in full_text or 'f.4th' in full_text or 'fed. cir.' in full_text:
                return ['courtlistener_pdf', 'justia_pdf', 'google_scholar_pdf']
            
            # Other federal courts (district, appeals, etc.)
            elif 'f.2d' in full_text or 'f. supp' in full_text or 'f.supp' in full_text:
                return ['courtlistener_pdf', 'justia_pdf', 'google_scholar_pdf']
            
            # State cases and others
            else:
                return ['courtlistener_pdf', 'justia_pdf', 'google_scholar_pdf']
        
        # Non-case citations use default routing
        return self.source_priorities.get(citation.citation_type, ['google_scholar_pdf'])
    
    def retrieve_citation(self, citation: Citation) -> RetrievalResult:
        """Retrieve PDF for a single citation"""
        self.logger.info(f"Retrieving {citation.citation_type}: {citation.full_text[:60]}...")
        
        # Get source priority list with intelligent routing
        sources = self._get_intelligent_sources(citation)
        
        for source in sources:
            self.logger.debug(f"  Trying source: {source}")
            
            try:
                result = self._try_source(citation, source)
                # Accept PDFs for cases, or any successful file for statutes
                if result.success and (result.is_valid_pdf or citation.citation_type == 'statute'):
                    self.logger.info(f"  ✓ Retrieved from {source}: {result.file_path}")
                    return result
                else:
                    self.logger.debug(f"  ✗ Failed {source}: {result.error_message}")
            except Exception as e:
                self.logger.debug(f"  ✗ Exception in {source}: {e}")
        
        # All sources failed
        return RetrievalResult(
            citation_id=citation.citation_id,
            source_name="none",
            success=False,
            file_path=None,
            file_size_bytes=None,
            is_valid_pdf=False,
            page_count=None,
            error_message="All retrieval sources failed",
            retrieval_url=None,
            retrieved_at=datetime.now().isoformat()
        )
    
    def _try_source(self, citation: Citation, source: str) -> RetrievalResult:
        """Try to retrieve from a specific source"""
        
        if source == 'supreme_court_official':
            return self._retrieve_supreme_court_official(citation)
        elif source == 'courtlistener_pdf':
            return self._retrieve_courtlistener_pdf(citation)
        elif source == 'govinfo_pdf':
            return self._retrieve_govinfo_pdf(citation)
        elif source == 'legal_information_institute':
            return self._retrieve_lii_usc(citation)
        elif source == 'uscode_house_gov':
            return self._retrieve_uscode_house(citation)
        elif source == 'google_scholar_pdf':
            return self._retrieve_google_scholar_pdf(citation)
        else:
            return self._create_failure_result(citation, source, "Source not implemented")
    
    def _retrieve_supreme_court_official(self, citation: Citation) -> RetrievalResult:
        """Retrieve from supremecourt.gov (bound volumes)"""
        
        if not citation.volume or not citation.page:
            return self._create_failure_result(citation, "supreme_court_official", "Missing volume/page")
        
        volume_num = int(citation.volume)
        if volume_num < 502:
            return self._create_failure_result(citation, "supreme_court_official", "Volume too old")
        
        # Try bound volume PDF
        volume_url = f"https://www.supremecourt.gov/opinions/boundvolumes/{citation.volume}bv.pdf"
        
        try:
            log_api_usage(
                api_name="supreme_court",
                endpoint=volume_url,
                method="HEAD",
                parameters={"volume": citation.volume},
                citation_text=citation.full_text,
                call_reason=f"Check availability of Supreme Court bound volume {citation.volume} for case {citation.case_name}",
                expected_result=f"HTTP 200 if volume {citation.volume} PDF exists on supremecourt.gov",
                citation_type="case",
                retrieval_strategy="supreme_court_official",
                additional_metadata={
                    "volume_number": citation.volume,
                    "case_name": citation.case_name,
                    "page_number": citation.page,
                    "source_priority": 1,  # Highest priority for SCOTUS cases
                    "file_type_expected": "pdf",
                    "estimated_size_mb": "10-50"
                }
            )
            
            # Check if volume exists
            head_response = self.session.head(volume_url, timeout=10)
            
            if head_response.status_code == 200:
                # Download the volume (this is large but contains the case)
                get_response = self.session.get(volume_url, timeout=60)
                
                if get_response.status_code == 200:
                    filename = f"{citation.citation_id}_SCOTUS_Vol{citation.volume}.pdf"
                    file_path = self.output_dir / filename
                    
                    with open(file_path, 'wb') as f:
                        f.write(get_response.content)
                    
                    # Validate PDF
                    is_valid, page_count = self._validate_pdf(file_path)
                    
                    log_api_usage(
                        api_name="supreme_court",
                        endpoint=volume_url,
                        method="GET", 
                        response_code=200,
                        success=True,
                        citation_text=citation.full_text,
                        call_reason=f"Download Supreme Court bound volume {citation.volume} containing case {citation.case_name}",
                        expected_result=f"Complete bound volume PDF for volume {citation.volume}",
                        citation_type="case", 
                        retrieval_strategy="supreme_court_official",
                        additional_metadata={
                            "file_size_bytes": len(get_response.content),
                            "file_size_mb": round(len(get_response.content) / 1024 / 1024, 2),
                            "pdf_pages": page_count,
                            "validation_status": "valid_pdf" if is_valid else "invalid_pdf",
                            "download_success": True,
                            "file_saved_as": str(file_path)
                        }
                    )
                    
                    return RetrievalResult(
                        citation_id=citation.citation_id,
                        source_name="supreme_court_official",
                        success=True,
                        file_path=str(file_path),
                        file_size_bytes=len(get_response.content),
                        is_valid_pdf=is_valid,
                        page_count=page_count,
                        error_message=None,
                        retrieval_url=volume_url,
                        retrieved_at=datetime.now().isoformat()
                    )
                    
        except Exception as e:
            log_api_usage(
                api_name="supreme_court",
                endpoint=volume_url,
                method="GET",
                success=False,
                error_message=str(e),
                citation_text=citation.full_text,
                call_reason=f"Attempt to retrieve Supreme Court bound volume {citation.volume} for case {citation.case_name}",
                expected_result=f"Bound volume PDF for volume {citation.volume}",
                citation_type="case",
                retrieval_strategy="supreme_court_official",
                additional_metadata={
                    "error_type": type(e).__name__,
                    "volume_requested": citation.volume,
                    "page_requested": citation.page,
                    "failure_point": "download_attempt"
                }
            )
        
        return self._create_failure_result(citation, "supreme_court_official", "Download failed")
    
    def _retrieve_courtlistener_pdf(self, citation: Citation) -> RetrievalResult:
        """Retrieve PDF from CourtListener"""
        
        if not citation.case_name:
            return self._create_failure_result(citation, "courtlistener", "No case name")
            
        api_key = self.api_keys.get("courtlistener", {}).get("token")
        if not api_key:
            return self._create_failure_result(citation, "courtlistener", "No API key")
        
        # Search for case using multiple strategies
        search_url = "https://www.courtlistener.com/api/rest/v3/search/"
        headers = {"Authorization": f"Token {api_key}"}
        
        # Try multiple search strategies for better matching
        search_strategies = [
            citation.case_name,  # Full case name
            citation.case_name.replace('Inc.', '').replace('Ltd.', '').replace('Corp.', '').strip(),  # Simplified
            f"{citation.case_name} {citation.year}" if citation.year else citation.case_name,  # With year
        ]
        
        search_response = None
        search_data = None
        
        for strategy in search_strategies:
            search_params = {
                "q": strategy,
                "type": "o",  # opinions
                "order_by": "score desc",
                "format": "json"
            }
            
            try:
                log_api_usage(
                    api_name="courtlistener",
                    endpoint=search_url,
                    method="GET",
                    parameters=search_params,
                    citation_text=citation.full_text,
                    call_reason=f"Search CourtListener for case using strategy: {strategy}",
                    expected_result="JSON with search results containing case opinions and PDF download URLs",
                    citation_type="case",
                    retrieval_strategy="courtlistener_pdf",
                    additional_metadata={
                        "search_query": strategy,
                        "search_type": "opinions",
                        "api_version": "v3",
                        "strategy": "multiple_search_patterns",
                        "free_api": True
                    }
                )
                
                search_response = self.session.get(search_url, params=search_params, headers=headers, timeout=10)
                
                if search_response.status_code == 200:
                    temp_data = search_response.json()
                    results = temp_data.get("results", [])
                    
                    # Use this strategy if it found results with download URLs
                    if any(r.get("download_url") for r in results[:5]):
                        search_data = temp_data
                        break
            except Exception:
                continue
        
        if not search_response or search_response.status_code != 200:
            return self._create_failure_result(citation, "courtlistener", "Search request failed")
        
        if not search_data:
            return self._create_failure_result(citation, "courtlistener", "No results found with any search strategy")
        
        # Try to download PDFs from results
        for result in search_data.get("results", [])[:10]:  # Try top 10 results for better coverage
            # Look for PDF download link
            if result.get("download_url"):
                pdf_url = result["download_url"]
                
                # Log what we found
                case_name = result.get('caseName', '')
                date = result.get('dateFiled', '')
                self.logger.debug(f"Trying PDF from: {case_name} ({date[:10] if date else 'no date'})")
                
                try:
                    # Handle SSL issues with government sites
                    if 'gov' in pdf_url:
                        pdf_response = requests.get(pdf_url, headers=headers, timeout=30, verify=False)
                    else:
                        pdf_response = self.session.get(pdf_url, headers=headers, timeout=30)
                    
                    if pdf_response.status_code == 200 and pdf_response.headers.get("content-type", "").startswith("application/pdf"):
                        filename = f"{citation.citation_id}_CourtListener.pdf"
                        file_path = self.output_dir / filename
                        
                        with open(file_path, 'wb') as f:
                            f.write(pdf_response.content)
                        
                        is_valid, page_count = self._validate_pdf(file_path)
                        
                        if is_valid:
                            log_api_usage(
                                api_name="courtlistener",
                                endpoint=pdf_url,
                                method="GET",
                                response_code=200,
                                success=True,
                                citation_text=citation.full_text
                            )
                            
                            return RetrievalResult(
                                citation_id=citation.citation_id,
                                source_name="courtlistener_pdf",
                                success=True,
                                file_path=str(file_path),
                                file_size_bytes=len(pdf_response.content),
                                is_valid_pdf=True,
                                page_count=page_count,
                                error_message=None,
                                retrieval_url=pdf_url,
                                retrieved_at=datetime.now().isoformat()
                            )
                        else:
                            os.remove(file_path)  # Remove invalid PDF
                except Exception as pdf_error:
                    # Continue to next result if this PDF fails
                    self.logger.debug(f"PDF download failed for {pdf_url}: {pdf_error}")
                    continue
        
        # If we get here, no PDFs were successfully downloaded
        return self._create_failure_result(citation, "courtlistener_pdf", "No valid PDF found")
    
    def _retrieve_uscode_house(self, citation: Citation) -> RetrievalResult:
        """Retrieve USC from uscode.house.gov (official House website)"""
        
        if citation.citation_type != 'statute' or citation.code_name != 'U.S.C.':
            return self._create_failure_result(citation, "uscode_house_gov", "Not a USC statute")
        
        if not citation.title_number or not citation.section:
            return self._create_failure_result(citation, "uscode_house_gov", "Missing title/section")
        
        try:
            # House USC website structure: https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title{title}-section{section}
            title = citation.title_number.zfill(2)  # Zero-pad to 2 digits
            section = citation.section.replace('(', '').replace(')', '').replace('.', '')
            
            # Try both current and prelim versions
            base_urls = [
                f"https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title{title}-section{section}",
                f"https://uscode.house.gov/view.xhtml?req=granuleid:USC-current-title{title}-section{section}"
            ]
            
            for url in base_urls:
                log_api_usage(
                    api_name="uscode_house_gov",
                    endpoint=url,
                    method="GET", 
                    call_reason=f"Retrieve official USC {title} § {citation.section} text for citation {citation.citation_id}",
                    expected_result="HTML page with USC statute text for PDF conversion",
                    citation_type="statute",
                    retrieval_strategy="official_government_source",
                    additional_metadata={
                        "title": title,
                        "section": citation.section,
                        "source_authority": "US House of Representatives",
                        "url_type": "current" if "current" in url else "preliminary"
                    }
                )
                
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200 and "Section" in response.text:
                    # For now, create a text file as a placeholder for PDF conversion
                    
                    # Generate filename
                    filename = f"USC_{title}_{section.replace('.', '_')}.pdf"
                    file_path = self.output_dir / filename
                    
                    try:
                        # Create PDF (this would normally require weasyprint or similar)
                        # For now, create a simple text file to test the workflow
                        with open(file_path.with_suffix('.txt'), 'w') as f:
                            f.write(f"USC Title {title}, Section {citation.section}\n")
                            f.write(f"Retrieved from: {url}\n")
                            f.write(f"Citation: {citation.full_text}\n")
                            f.write(f"Retrieved at: {datetime.now().isoformat()}\n")
                        
                        log_api_usage(
                            api_name="uscode_house_gov",
                            endpoint=url,
                            method="GET",
                            response_code=200,
                            success=True,
                            call_reason=f"Retrieve official USC {title} § {citation.section} text for citation {citation.citation_id}",
                            expected_result="HTML page with USC statute text for PDF conversion", 
                            citation_type="statute",
                            retrieval_strategy="official_government_source",
                            additional_metadata={
                                "content_found": True,
                                "file_created": str(file_path.with_suffix('.txt')),
                                "conversion_method": "html_to_text_placeholder"
                            }
                        )
                        
                        return RetrievalResult(
                            citation_id=citation.citation_id,
                            source_name="uscode_house_gov",
                            success=True,
                            file_path=str(file_path.with_suffix('.txt')),
                            file_size_bytes=file_path.with_suffix('.txt').stat().st_size,
                            is_valid_pdf=False,  # It's actually a text file for now
                            page_count=1,
                            error_message=None,
                            retrieval_url=url,
                            retrieved_at=datetime.now().isoformat()
                        )
                        
                    except Exception as pdf_error:
                        log_api_usage(
                            api_name="uscode_house_gov",
                            endpoint=url,
                            method="GET", 
                            success=False,
                            error_message=str(pdf_error),
                            call_reason=f"Convert USC content to PDF for citation {citation.citation_id}",
                            expected_result="PDF file with statute text",
                            citation_type="statute",
                            retrieval_strategy="official_government_source"
                        )
                        continue
                else:
                    log_api_usage(
                        api_name="uscode_house_gov",
                        endpoint=url,
                        method="GET",
                        response_code=response.status_code,
                        success=False,
                        error_message=f"Status {response.status_code}, content check failed",
                        call_reason=f"Retrieve USC {title} § {citation.section} from House website",
                        expected_result="HTML page with USC statute text",
                        citation_type="statute",
                        retrieval_strategy="official_government_source"
                    )
            
            return self._create_failure_result(citation, "uscode_house_gov", "Content not found on House website")
            
        except Exception as e:
            log_api_usage(
                api_name="uscode_house_gov", 
                endpoint="https://uscode.house.gov",
                method="GET",
                success=False,
                error_message=str(e),
                call_reason=f"Retrieve USC statute for citation {citation.citation_id}",
                expected_result="USC statute content",
                citation_type="statute",
                retrieval_strategy="official_government_source"
            )
            return self._create_failure_result(citation, "uscode_house_gov", f"Request failed: {str(e)}")
    
    def _retrieve_lii_usc(self, citation: Citation) -> RetrievalResult:
        """Retrieve USC from Legal Information Institute (Cornell Law)"""
        
        if citation.citation_type != 'statute' or citation.code_name != 'U.S.C.':
            return self._create_failure_result(citation, "legal_information_institute", "Not a USC statute")
        
        if not citation.title_number or not citation.section:
            return self._create_failure_result(citation, "legal_information_institute", "Missing title/section")
        
        try:
            # LII USC URL structure: https://www.law.cornell.edu/uscode/text/{title}/{section}
            title = citation.title_number
            section = citation.section.split('(')[0]  # Remove subsection for main section
            
            url = f"https://www.law.cornell.edu/uscode/text/{title}/{section}"
            
            log_api_usage(
                api_name="cornell_lii",
                endpoint=url,
                method="GET",
                call_reason=f"Retrieve USC {title} § {citation.section} from Cornell LII for citation {citation.citation_id}",
                expected_result="HTML page with USC statute text from Cornell Law School",
                citation_type="statute", 
                retrieval_strategy="academic_legal_source",
                additional_metadata={
                    "title": title,
                    "section": section,
                    "source_authority": "Cornell Law School",
                    "access_type": "free_public"
                }
            )
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200 and ("U.S.C." in response.text or "United States Code" in response.text):
                # Create a simple text file with the statute information
                filename = f"USC_{title}_{section.replace('.', '_')}_LII.txt"
                file_path = self.output_dir / filename
                
                with open(file_path, 'w') as f:
                    f.write(f"USC Title {title}, Section {citation.section}\n")
                    f.write(f"Source: Cornell Legal Information Institute\n") 
                    f.write(f"URL: {url}\n")
                    f.write(f"Citation: {citation.full_text}\n")
                    f.write(f"Retrieved at: {datetime.now().isoformat()}\n")
                    f.write("\n" + "="*60 + "\n")
                    f.write("Note: Full HTML content parsing would be implemented here\n")
                    f.write("to extract the actual statute text and create a proper PDF.\n")
                
                log_api_usage(
                    api_name="cornell_lii",
                    endpoint=url,
                    method="GET",
                    response_code=200,
                    success=True,
                    call_reason=f"Retrieve USC {title} § {citation.section} from Cornell LII for citation {citation.citation_id}",
                    expected_result="HTML page with USC statute text from Cornell Law School",
                    citation_type="statute",
                    retrieval_strategy="academic_legal_source",
                    additional_metadata={
                        "content_found": True,
                        "file_created": str(file_path),
                        "file_type": "text_placeholder"
                    }
                )
                
                return RetrievalResult(
                    citation_id=citation.citation_id,
                    source_name="cornell_lii",
                    success=True,
                    file_path=str(file_path),
                    file_size_bytes=file_path.stat().st_size,
                    is_valid_pdf=False,  # Text file for now
                    page_count=1,
                    error_message=None,
                    retrieval_url=url,
                    retrieved_at=datetime.now().isoformat()
                )
            else:
                log_api_usage(
                    api_name="cornell_lii",
                    endpoint=url,
                    method="GET",
                    response_code=response.status_code,
                    success=False,
                    error_message=f"Status {response.status_code}, USC content not found",
                    call_reason=f"Retrieve USC {title} § {citation.section} from Cornell LII",
                    expected_result="HTML page with USC statute text",
                    citation_type="statute",
                    retrieval_strategy="academic_legal_source"
                )
                return self._create_failure_result(citation, "cornell_lii", f"USC content not found (status {response.status_code})")
                
        except Exception as e:
            log_api_usage(
                api_name="cornell_lii",
                endpoint=f"https://www.law.cornell.edu/uscode/text/{citation.title_number}/*",
                method="GET",
                success=False,
                error_message=str(e),
                call_reason=f"Retrieve USC statute for citation {citation.citation_id}",
                expected_result="USC statute content from Cornell LII",
                citation_type="statute",
                retrieval_strategy="academic_legal_source"
            )
            return self._create_failure_result(citation, "cornell_lii", f"Request failed: {str(e)}")
    
    def _retrieve_govinfo_pdf(self, citation: Citation) -> RetrievalResult:
        """Retrieve PDF from GovInfo"""
        
        if citation.citation_type not in ['statute', 'regulation']:
            return self._create_failure_result(citation, "govinfo", "Not a statute/regulation")
            
        api_key = self.api_keys.get("govinfo", {}).get("api_key")
        if not api_key:
            return self._create_failure_result(citation, "govinfo", "No API key")
        
        # Try to find the document
        if citation.citation_type == 'statute' and citation.title_number and citation.section:
            collection = "USCODE"
            # This would need more sophisticated mapping to actual GovInfo package IDs
            # For now, return failure as GovInfo API structure is complex
            
        return self._create_failure_result(citation, "govinfo_pdf", "Complex API mapping needed")
    
    def _retrieve_google_scholar_pdf(self, citation: Citation) -> RetrievalResult:
        """Retrieve PDF from Google Scholar (last resort)"""
        # Google Scholar doesn't provide a direct API for PDF downloads
        # This would require web scraping which is against ToS
        return self._create_failure_result(citation, "google_scholar_pdf", "No public API available")
    
    def _validate_pdf(self, file_path: Path) -> Tuple[bool, Optional[int]]:
        """Validate that file is a readable PDF"""
        try:
            doc = fitz.open(str(file_path))
            page_count = len(doc)
            doc.close()
            
            # Additional checks
            if page_count == 0:
                return False, 0
            
            # Check file size (PDFs should be at least 1KB)
            if file_path.stat().st_size < 1024:
                return False, page_count
            
            return True, page_count
            
        except Exception as e:
            self.logger.debug(f"PDF validation failed: {e}")
            return False, None
    
    def _create_failure_result(self, citation: Citation, source: str, error: str) -> RetrievalResult:
        """Create a failure result"""
        return RetrievalResult(
            citation_id=citation.citation_id,
            source_name=source,
            success=False,
            file_path=None,
            file_size_bytes=None,
            is_valid_pdf=False,
            page_count=None,
            error_message=error,
            retrieval_url=None,
            retrieved_at=datetime.now().isoformat()
        )