"""
Enhanced Source Retriever for Stanford Law Review
Retrieves actual legal sources from multiple databases and APIs for proper sourcepull
"""

import os
import re
import time
import json
import logging
import hashlib
import requests
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiohttp
from datetime import datetime
from urllib.parse import urljoin, quote

from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class SourceType(Enum):
    CASE = "case"
    STATUTE = "statute"
    REGULATION = "regulation"
    ARTICLE = "article"
    BOOK = "book"
    WEB = "web"
    LEGISLATIVE = "legislative"


@dataclass
class LegalSource:
    """Represents a legal source to be retrieved"""
    id: str
    citation: str
    short_name: str
    source_type: SourceType
    metadata: Dict[str, Any]
    required_elements: List[str]  # Elements that need redboxing


@dataclass
class RetrievalResult:
    """Result of source retrieval with redboxing information"""
    source_id: str
    status: str  # success, partial, failed, manual_required
    file_path: Optional[str] = None
    source_url: Optional[str] = None
    file_type: str = "pdf"  # pdf, html, txt
    message: str = ""
    metadata: Dict[str, Any] = None
    redbox_elements: List[Dict[str, Any]] = None
    requires_manual_review: bool = False


class EnhancedSourceRetriever:
    """Enhanced source retriever with multiple API integrations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = Path(config.get('output_dir', './output/data/Sourcepull'))
        self.cache_dir = Path(config.get('cache_dir', './cache'))
        
        # API configurations
        self.apis = config.get('apis', {})
        
        # Legal database configurations
        self.courtlistener_api = self.apis.get('courtlistener')
        self.justia_api = self.apis.get('justia')
        self.govinfo_api = self.apis.get('govinfo')
        self.crossref_api = self.apis.get('crossref')
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # HTTP session setup
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Stanford Law Review Editorial System/2.0',
            'Accept': 'application/pdf, application/json, text/html, */*'
        })
        
        # Statistics
        self.stats = {
            'total_retrieved': 0,
            'successful_pdfs': 0,
            'partial_retrievals': 0,
            'failed_retrievals': 0,
            'cached_hits': 0
        }
    
    def retrieve_sherkow_gugliuzza_sources(self) -> List[RetrievalResult]:
        """Retrieve the specific sources needed for Sherkow & Gugliuzza article"""
        sources = [
            LegalSource(
                id="001",
                citation="Alice Corp. v. CLS Bank International, 573 U.S. 208 (2014)",
                short_name="Alice_Corp",
                source_type=SourceType.CASE,
                metadata={
                    'case_name': 'Alice Corp. v. CLS Bank International',
                    'volume': '573',
                    'reporter': 'U.S.',
                    'page': '208',
                    'year': '2014',
                    'court': 'Supreme Court',
                    'key_quote': 'Laws of nature, natural phenomena, and abstract ideas are not patentable subject matter under § 101.'
                },
                required_elements=['case_name', 'volume', 'reporter', 'page', 'year', 'key_quote']
            ),
            LegalSource(
                id="002",
                citation="Mayo Collaborative Services v. Prometheus Laboratories, Inc., 566 U.S. 66 (2012)",
                short_name="Mayo",
                source_type=SourceType.CASE,
                metadata={
                    'case_name': 'Mayo Collaborative Services v. Prometheus Laboratories, Inc.',
                    'volume': '566',
                    'reporter': 'U.S.',
                    'page': '66',
                    'year': '2012',
                    'court': 'Supreme Court',
                    'key_quote': 'The Court has long held that laws of nature are not patentable.'
                },
                required_elements=['case_name', 'volume', 'reporter', 'page', 'year', 'key_quote']
            ),
            LegalSource(
                id="003",
                citation="Diamond v. Chakrabarty, 447 U.S. 303 (1980)",
                short_name="Diamond",
                source_type=SourceType.CASE,
                metadata={
                    'case_name': 'Diamond v. Chakrabarty',
                    'volume': '447',
                    'reporter': 'U.S.',
                    'page': '303',
                    'year': '1980',
                    'court': 'Supreme Court',
                    'key_quote': 'Congress intended statutory subject matter to include anything under the sun that is made by man.'
                },
                required_elements=['case_name', 'volume', 'reporter', 'page', 'year', 'key_quote']
            ),
            LegalSource(
                id="004",
                citation="35 U.S.C. § 101 (2018)",
                short_name="35USC101",
                source_type=SourceType.STATUTE,
                metadata={
                    'title': '35',
                    'code': 'U.S.C.',
                    'section': '101',
                    'year': '2018',
                    'statute_text': 'Whoever invents or discovers any new and useful process, machine, manufacture, or composition of matter, or any new and useful improvement thereof, may obtain a patent therefor, subject to the conditions and requirements of this title.'
                },
                required_elements=['title', 'section', 'statute_text']
            ),
            LegalSource(
                id="005",
                citation="Mark A. Lemley, Software Patents and the Return of Functional Claiming, 2013 Wis. L. Rev. 905",
                short_name="Lemley",
                source_type=SourceType.ARTICLE,
                metadata={
                    'author': 'Mark A. Lemley',
                    'title': 'Software Patents and the Return of Functional Claiming',
                    'journal': 'Wis. L. Rev.',
                    'volume': '2013',
                    'page': '905',
                    'year': '2013',
                    'key_quote': 'The real problem with software patents is not subject matter but functional claiming.'
                },
                required_elements=['author', 'title', 'journal', 'volume', 'page', 'year', 'key_quote']
            )
        ]
        
        results = []
        for source in sources:
            logger.info(f"Retrieving source: {source.short_name}")
            result = self.retrieve_source(source)
            results.append(result)
            
        return results
    
    def retrieve_source(self, source: LegalSource) -> RetrievalResult:
        """Retrieve a single source document"""
        self.stats['total_retrieved'] += 1
        
        # Check cache first
        cached_result = self._check_cache(source)
        if cached_result:
            self.stats['cached_hits'] += 1
            return cached_result
        
        # Route to appropriate retrieval method
        if source.source_type == SourceType.CASE:
            return self._retrieve_case_document(source)
        elif source.source_type == SourceType.STATUTE:
            return self._retrieve_statute_document(source)
        elif source.source_type == SourceType.ARTICLE:
            return self._retrieve_article_document(source)
        else:
            return RetrievalResult(
                source_id=source.id,
                status="failed",
                message=f"Unsupported source type: {source.source_type}"
            )
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _retrieve_case_document(self, source: LegalSource) -> RetrievalResult:
        """Retrieve Supreme Court case documents"""
        metadata = source.metadata
        
        # Strategy 1: Try Supreme Court website directly
        result = self._try_supremecourt_gov(source)
        if result.status == "success":
            return result
        
        # Strategy 2: Try CourtListener API
        if self.courtlistener_api:
            result = self._try_courtlistener_api(source)
            if result.status == "success":
                return result
        
        # Strategy 3: Try Justia for Supreme Court cases
        result = self._try_justia_supreme_court(source)
        if result.status == "success":
            return result
        
        # Strategy 4: Try Case.law (Harvard)
        result = self._try_caselaw_harvard(source)
        if result.status in ["success", "partial"]:
            return result
        
        # Strategy 5: Try Google Scholar as last resort
        result = self._try_google_scholar_case(source)
        if result.status in ["success", "partial"]:
            return result
        
        self.stats['failed_retrievals'] += 1
        return RetrievalResult(
            source_id=source.id,
            status="manual_required",
            message=f"Could not retrieve case document: {source.citation}",
            requires_manual_review=True
        )
    
    def _try_supremecourt_gov(self, source: LegalSource) -> RetrievalResult:
        """Try to get PDF from supremecourt.gov"""
        metadata = source.metadata
        
        try:
            # Supreme Court opinions are available at predictable URLs
            # Format: https://www.supremecourt.gov/opinions/boundvolumes/[volume]US.pdf
            volume = metadata.get('volume')
            
            if volume and int(volume) >= 500:  # Modern cases have PDFs available
                pdf_url = f"https://www.supremecourt.gov/opinions/boundvolumes/{volume}US.pdf"
                
                response = self.session.get(pdf_url, timeout=60, stream=True)
                
                if response.status_code == 200:
                    output_path = self._generate_output_path(source)
                    
                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # Cache the file
                    self._cache_file(source, output_path)
                    
                    self.stats['successful_pdfs'] += 1
                    return RetrievalResult(
                        source_id=source.id,
                        status="success",
                        file_path=str(output_path),
                        source_url=pdf_url,
                        file_type="pdf",
                        message="Retrieved full volume PDF from Supreme Court website",
                        metadata={'volume_pdf': True, 'start_page': metadata.get('page')},
                        redbox_elements=self._prepare_redbox_elements(source),
                        requires_manual_review=False
                    )
        
        except Exception as e:
            logger.error(f"Supreme Court website retrieval failed: {e}")
        
        return RetrievalResult(source_id=source.id, status="failed")
    
    def _try_courtlistener_api(self, source: LegalSource) -> RetrievalResult:
        """Try CourtListener API for case documents"""
        if not self.courtlistener_api:
            return RetrievalResult(source_id=source.id, status="failed", message="No CourtListener API key")
        
        metadata = source.metadata
        
        try:
            # Search for the case using CourtListener API
            headers = {'Authorization': f'Token {self.courtlistener_api}'}
            search_url = "https://www.courtlistener.com/api/rest/v3/search/"
            
            search_params = {
                'q': f'"{metadata["case_name"]}"',
                'type': 'o',  # opinions
                'court': 'scotus' if metadata.get('court') == 'Supreme Court' else None,
                'format': 'json'
            }
            
            response = self.session.get(search_url, params=search_params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    # Get the first matching result
                    opinion = results[0]
                    
                    # Try to get the PDF
                    if opinion.get('download_url'):
                        pdf_response = self.session.get(
                            opinion['download_url'], 
                            headers=headers, 
                            timeout=60
                        )
                        
                        if pdf_response.status_code == 200:
                            output_path = self._generate_output_path(source)
                            output_path.write_bytes(pdf_response.content)
                            
                            self._cache_file(source, output_path)
                            
                            self.stats['successful_pdfs'] += 1
                            return RetrievalResult(
                                source_id=source.id,
                                status="success",
                                file_path=str(output_path),
                                source_url=opinion['download_url'],
                                file_type="pdf",
                                message="Retrieved PDF from CourtListener",
                                metadata={'courtlistener_id': opinion.get('id')},
                                redbox_elements=self._prepare_redbox_elements(source),
                                requires_manual_review=False
                            )
        
        except Exception as e:
            logger.error(f"CourtListener API retrieval failed: {e}")
        
        return RetrievalResult(source_id=source.id, status="failed")
    
    def _try_justia_supreme_court(self, source: LegalSource) -> RetrievalResult:
        """Try Justia for Supreme Court cases"""
        metadata = source.metadata
        
        try:
            # Justia has a predictable URL structure for Supreme Court cases
            # Format: https://supreme.justia.com/cases/federal/us/[volume]/[page]/
            volume = metadata.get('volume')
            page = metadata.get('page')
            
            if volume and page:
                case_url = f"https://supreme.justia.com/cases/federal/us/{volume}/{page}/"
                
                response = self.session.get(case_url, timeout=30)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for PDF download link
                    pdf_link = soup.find('a', href=lambda h: h and 'pdf' in h.lower())
                    
                    if pdf_link:
                        pdf_url = urljoin(case_url, pdf_link['href'])
                        
                        pdf_response = self.session.get(pdf_url, timeout=60)
                        
                        if pdf_response.status_code == 200:
                            output_path = self._generate_output_path(source)
                            output_path.write_bytes(pdf_response.content)
                            
                            self._cache_file(source, output_path)
                            
                            self.stats['successful_pdfs'] += 1
                            return RetrievalResult(
                                source_id=source.id,
                                status="success",
                                file_path=str(output_path),
                                source_url=pdf_url,
                                file_type="pdf",
                                message="Retrieved PDF from Justia",
                                metadata={'justia_url': case_url},
                                redbox_elements=self._prepare_redbox_elements(source),
                                requires_manual_review=False
                            )
                    
                    # If no PDF, save HTML content
                    else:
                        # Extract case text from HTML
                        case_content = soup.find('div', {'class': 'case-content'}) or soup.find('div', {'id': 'opinion'})
                        
                        if case_content:
                            output_path = self._generate_output_path(source, extension='.html')
                            
                            # Create clean HTML with metadata
                            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{metadata['case_name']}</title>
    <meta name="citation" content="{source.citation}">
    <meta name="retrieved_from" content="{case_url}">
    <meta name="retrieved_date" content="{datetime.now().isoformat()}">
</head>
<body>
    <h1>{metadata['case_name']}</h1>
    <p><strong>Citation:</strong> {source.citation}</p>
    <hr>
    {case_content}
</body>
</html>"""
                            
                            output_path.write_text(html_content, encoding='utf-8')
                            
                            self.stats['partial_retrievals'] += 1
                            return RetrievalResult(
                                source_id=source.id,
                                status="partial",
                                file_path=str(output_path),
                                source_url=case_url,
                                file_type="html",
                                message="Retrieved HTML from Justia (PDF not available)",
                                metadata={'justia_url': case_url},
                                redbox_elements=self._prepare_redbox_elements(source),
                                requires_manual_review=True
                            )
        
        except Exception as e:
            logger.error(f"Justia retrieval failed: {e}")
        
        return RetrievalResult(source_id=source.id, status="failed")
    
    def _retrieve_statute_document(self, source: LegalSource) -> RetrievalResult:
        """Retrieve U.S.C. statute documents"""
        metadata = source.metadata
        
        # Try GovInfo API first
        if self.govinfo_api:
            result = self._try_govinfo_usc(source)
            if result.status == "success":
                return result
        
        # Try uscode.house.gov
        result = self._try_uscode_house_gov(source)
        if result.status in ["success", "partial"]:
            return result
        
        # Try Legal Information Institute (Cornell)
        result = self._try_cornell_lii_usc(source)
        if result.status in ["success", "partial"]:
            return result
        
        self.stats['failed_retrievals'] += 1
        return RetrievalResult(
            source_id=source.id,
            status="manual_required",
            message=f"Could not retrieve statute: {source.citation}",
            requires_manual_review=True
        )
    
    def _try_govinfo_usc(self, source: LegalSource) -> RetrievalResult:
        """Try GovInfo API for U.S.C. documents"""
        if not self.govinfo_api:
            return RetrievalResult(source_id=source.id, status="failed")
        
        metadata = source.metadata
        title = metadata.get('title')
        section = metadata.get('section')
        
        try:
            # GovInfo search API
            search_url = "https://api.govinfo.gov/collections/USCODE/search"
            params = {
                'api_key': self.govinfo_api,
                'query': f'title:{title} AND section:{section}',
                'pageSize': 10
            }
            
            response = self.session.get(search_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    doc = results[0]
                    
                    # Get PDF download link
                    pdf_link = doc.get('download', {}).get('pdfLink')
                    
                    if pdf_link:
                        pdf_response = self.session.get(
                            pdf_link,
                            params={'api_key': self.govinfo_api},
                            timeout=60
                        )
                        
                        if pdf_response.status_code == 200:
                            output_path = self._generate_output_path(source)
                            output_path.write_bytes(pdf_response.content)
                            
                            self._cache_file(source, output_path)
                            
                            self.stats['successful_pdfs'] += 1
                            return RetrievalResult(
                                source_id=source.id,
                                status="success",
                                file_path=str(output_path),
                                source_url=pdf_link,
                                file_type="pdf",
                                message="Retrieved PDF from GovInfo",
                                metadata={'govinfo_id': doc.get('packageId')},
                                redbox_elements=self._prepare_redbox_elements(source),
                                requires_manual_review=False
                            )
        
        except Exception as e:
            logger.error(f"GovInfo USC retrieval failed: {e}")
        
        return RetrievalResult(source_id=source.id, status="failed")
    
    def _try_uscode_house_gov(self, source: LegalSource) -> RetrievalResult:
        """Try House.gov for U.S.C. documents"""
        metadata = source.metadata
        title = metadata.get('title', '').zfill(2)
        section = metadata.get('section')
        
        try:
            # House.gov URL format
            url = f"https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title{title}-section{section}"
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find the section content
                content_div = soup.find('div', {'class': 'section-content'}) or soup.find('main')
                
                if content_div:
                    output_path = self._generate_output_path(source, extension='.html')
                    
                    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title} U.S.C. § {section}</title>
    <meta name="citation" content="{source.citation}">
    <meta name="retrieved_from" content="{url}">
    <meta name="retrieved_date" content="{datetime.now().isoformat()}">
</head>
<body>
    <h1>{title} U.S.C. § {section}</h1>
    <p><strong>Citation:</strong> {source.citation}</p>
    <hr>
    {content_div}
</body>
</html>"""
                    
                    output_path.write_text(html_content, encoding='utf-8')
                    
                    self.stats['partial_retrievals'] += 1
                    return RetrievalResult(
                        source_id=source.id,
                        status="partial",
                        file_path=str(output_path),
                        source_url=url,
                        file_type="html",
                        message="Retrieved HTML from uscode.house.gov",
                        metadata={'house_gov_url': url},
                        redbox_elements=self._prepare_redbox_elements(source),
                        requires_manual_review=True
                    )
        
        except Exception as e:
            logger.error(f"House.gov USC retrieval failed: {e}")
        
        return RetrievalResult(source_id=source.id, status="failed")
    
    def _retrieve_article_document(self, source: LegalSource) -> RetrievalResult:
        """Retrieve law review article"""
        metadata = source.metadata
        
        # Try SSRN first for academic articles
        result = self._try_ssrn_article(source)
        if result.status == "success":
            return result
        
        # Try Google Scholar
        result = self._try_google_scholar_article(source)
        if result.status in ["success", "partial"]:
            return result
        
        # Try law review's own website
        result = self._try_law_review_website(source)
        if result.status in ["success", "partial"]:
            return result
        
        self.stats['failed_retrievals'] += 1
        return RetrievalResult(
            source_id=source.id,
            status="manual_required",
            message=f"Could not retrieve article: {source.citation}",
            requires_manual_review=True
        )
    
    def _try_ssrn_article(self, source: LegalSource) -> RetrievalResult:
        """Try SSRN for academic articles"""
        metadata = source.metadata
        author = metadata.get('author', '')
        title = metadata.get('title', '')
        
        try:
            # Search SSRN
            search_url = "https://papers.ssrn.com/sol3/results.cfm"
            params = {
                'form_name': 'journalBrowse',
                'txtKeywords': f"{author} {title}",
                'journal_id': '0',
                'pubType': 'pub'
            }
            
            response = self.session.get(search_url, params=params, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for paper links
                paper_links = soup.find_all('a', class_='title')
                
                for link in paper_links[:3]:  # Check first 3 results
                    paper_url = urljoin("https://papers.ssrn.com", link.get('href', ''))
                    
                    # Get paper page to find download link
                    paper_response = self.session.get(paper_url, timeout=30)
                    
                    if paper_response.status_code == 200:
                        paper_soup = BeautifulSoup(paper_response.text, 'html.parser')
                        
                        # Look for PDF download link
                        download_link = paper_soup.find('a', string=lambda s: s and 'download' in s.lower())
                        
                        if download_link:
                            pdf_url = urljoin(paper_url, download_link.get('href', ''))
                            
                            pdf_response = self.session.get(pdf_url, timeout=60)
                            
                            if pdf_response.status_code == 200:
                                output_path = self._generate_output_path(source)
                                output_path.write_bytes(pdf_response.content)
                                
                                self._cache_file(source, output_path)
                                
                                self.stats['successful_pdfs'] += 1
                                return RetrievalResult(
                                    source_id=source.id,
                                    status="success",
                                    file_path=str(output_path),
                                    source_url=pdf_url,
                                    file_type="pdf",
                                    message="Retrieved PDF from SSRN",
                                    metadata={'ssrn_url': paper_url},
                                    redbox_elements=self._prepare_redbox_elements(source),
                                    requires_manual_review=False
                                )
        
        except Exception as e:
            logger.error(f"SSRN retrieval failed: {e}")
        
        return RetrievalResult(source_id=source.id, status="failed")
    
    def _prepare_redbox_elements(self, source: LegalSource) -> List[Dict[str, Any]]:
        """Prepare redbox element information for the document"""
        elements = []
        
        for element_key in source.required_elements:
            if element_key in source.metadata:
                elements.append({
                    'name': element_key,
                    'value': source.metadata[element_key],
                    'type': 'text',  # text, quote, citation_element
                    'priority': 'high' if element_key in ['case_name', 'citation', 'key_quote'] else 'medium'
                })
        
        return elements
    
    def _generate_output_path(self, source: LegalSource, extension: str = '.pdf') -> Path:
        """Generate output file path"""
        filename = f"SP-{source.id}-{source.short_name}{extension}"
        return self.output_dir / filename
    
    def _check_cache(self, source: LegalSource) -> Optional[RetrievalResult]:
        """Check if document is already cached"""
        cache_key = hashlib.md5(source.citation.encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.pdf"
        
        if cache_file.exists():
            # Copy to output directory
            output_path = self._generate_output_path(source)
            output_path.write_bytes(cache_file.read_bytes())
            
            return RetrievalResult(
                source_id=source.id,
                status="success",
                file_path=str(output_path),
                file_type="pdf",
                message="Retrieved from cache",
                redbox_elements=self._prepare_redbox_elements(source)
            )
        
        return None
    
    def _cache_file(self, source: LegalSource, file_path: Path) -> None:
        """Cache a retrieved file"""
        cache_key = hashlib.md5(source.citation.encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.pdf"
        
        if file_path.suffix.lower() == '.pdf':
            cache_file.write_bytes(file_path.read_bytes())
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics"""
        return self.stats.copy()


# Placeholder implementations for missing methods
def _try_caselaw_harvard(self, source: LegalSource) -> RetrievalResult:
    """Try Case.law (Harvard) - placeholder"""
    return RetrievalResult(source_id=source.id, status="failed")

def _try_google_scholar_case(self, source: LegalSource) -> RetrievalResult:
    """Try Google Scholar for cases - placeholder"""
    return RetrievalResult(source_id=source.id, status="failed")

def _try_cornell_lii_usc(self, source: LegalSource) -> RetrievalResult:
    """Try Cornell LII for USC - placeholder"""
    return RetrievalResult(source_id=source.id, status="failed")

def _try_google_scholar_article(self, source: LegalSource) -> RetrievalResult:
    """Try Google Scholar for articles - placeholder"""
    return RetrievalResult(source_id=source.id, status="failed")

def _try_law_review_website(self, source: LegalSource) -> RetrievalResult:
    """Try law review's own website - placeholder"""
    return RetrievalResult(source_id=source.id, status="failed")


# Add missing methods to the class
EnhancedSourceRetriever._try_caselaw_harvard = _try_caselaw_harvard
EnhancedSourceRetriever._try_google_scholar_case = _try_google_scholar_case
EnhancedSourceRetriever._try_cornell_lii_usc = _try_cornell_lii_usc
EnhancedSourceRetriever._try_google_scholar_article = _try_google_scholar_article
EnhancedSourceRetriever._try_law_review_website = _try_law_review_website