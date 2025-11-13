"""
Source Retriever Module for Stanford Law Review
Retrieves legal sources from various APIs and databases
"""

import os
import re
import time
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiohttp

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime

from citation_parser import Citation, CitationType

logger = logging.getLogger(__name__)


class RetrievalStatus(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    MANUAL_REQUIRED = "manual_required"
    CACHED = "cached"


@dataclass
class RetrievalResult:
    """Result of a source retrieval attempt"""
    status: RetrievalStatus
    file_path: Optional[str] = None
    source_url: Optional[str] = None
    message: str = ""
    metadata: Dict[str, Any] = None
    requires_ocr: bool = False
    page_count: int = 0
    

class SourceRetriever:
    """Main class for retrieving legal sources"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache_dir = Path(config.get('cache_dir', './cache'))
        self.output_dir = Path(config.get('output_dir', './output/data/Sourcepull'))
        self.apis = config.get('apis', {})
        
        # Create directories
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Stanford Law Review Editorial System/1.0'
        })
        
        # Track retrieval statistics
        self.stats = {
            'total_attempts': 0,
            'successful': 0,
            'failed': 0,
            'cached': 0,
            'manual_required': 0
        }
    
    def retrieve(self, citation: Citation) -> RetrievalResult:
        """Main entry point for retrieving a source"""
        self.stats['total_attempts'] += 1
        
        # Check cache first
        cached_result = self._check_cache(citation)
        if cached_result.status == RetrievalStatus.CACHED:
            self.stats['cached'] += 1
            return cached_result
        
        # Route to appropriate retrieval method based on citation type
        result = None
        if citation.type == CitationType.CASE:
            result = self._retrieve_case(citation)
        elif citation.type == CitationType.STATUTE:
            result = self._retrieve_statute(citation)
        elif citation.type == CitationType.REGULATION:
            result = self._retrieve_regulation(citation)
        elif citation.type == CitationType.ARTICLE:
            result = self._retrieve_article(citation)
        elif citation.type == CitationType.BOOK:
            result = self._retrieve_book(citation)
        elif citation.type == CitationType.WEB:
            result = self._retrieve_web(citation)
        elif citation.type == CitationType.LEGISLATIVE:
            result = self._retrieve_legislative(citation)
        else:
            result = RetrievalResult(
                status=RetrievalStatus.MANUAL_REQUIRED,
                message=f"Unknown citation type: {citation.type}"
            )
        
        # Update statistics
        if result.status == RetrievalStatus.SUCCESS:
            self.stats['successful'] += 1
        elif result.status == RetrievalStatus.FAILED:
            self.stats['failed'] += 1
        elif result.status == RetrievalStatus.MANUAL_REQUIRED:
            self.stats['manual_required'] += 1
        
        return result
    
    def _check_cache(self, citation: Citation) -> RetrievalResult:
        """Check if source is already cached"""
        cache_key = self._generate_cache_key(citation)
        cache_file = self.cache_dir / f"{cache_key}.pdf"
        
        if cache_file.exists():
            # Copy to output directory with proper naming
            output_file = self._generate_output_path(citation)
            if not output_file.exists():
                import shutil
                shutil.copy2(cache_file, output_file)
            
            return RetrievalResult(
                status=RetrievalStatus.CACHED,
                file_path=str(output_file),
                message="Retrieved from cache"
            )
        
        return RetrievalResult(status=RetrievalStatus.FAILED)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _retrieve_case(self, citation: Citation) -> RetrievalResult:
        """Retrieve case documents"""
        metadata = citation.metadata
        
        # Try CourtListener API first
        if self.apis.get('courtlistener'):
            result = self._try_courtlistener(citation)
            if result.status == RetrievalStatus.SUCCESS:
                return result
        
        # Try Google Scholar
        result = self._try_google_scholar_case(citation)
        if result.status == RetrievalStatus.SUCCESS:
            return result
        
        # Try Case.law (Harvard)
        result = self._try_caselaw(citation)
        if result.status == RetrievalStatus.SUCCESS:
            return result
        
        # If all fail, mark for manual retrieval
        return RetrievalResult(
            status=RetrievalStatus.MANUAL_REQUIRED,
            message=f"Could not retrieve case: {metadata.title} {metadata.reporter} {metadata.page}"
        )
    
    def _try_courtlistener(self, citation: Citation) -> RetrievalResult:
        """Try to retrieve from CourtListener API"""
        api_key = self.apis.get('courtlistener')
        if not api_key:
            return RetrievalResult(status=RetrievalStatus.FAILED, message="No CourtListener API key")
        
        metadata = citation.metadata
        base_url = "https://www.courtlistener.com/api/rest/v3"
        
        try:
            # Search for the case
            search_params = {
                'q': f'"{metadata.title}"',
                'type': 'o',  # opinions
                'order_by': 'score desc',
                'format': 'json'
            }
            
            headers = {'Authorization': f'Token {api_key}'}
            response = self.session.get(
                f"{base_url}/search/",
                params=search_params,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                results = response.json()
                if results.get('results'):
                    # Get the first result
                    case_data = results['results'][0]
                    
                    # Try to get PDF
                    if case_data.get('download_url'):
                        pdf_response = self.session.get(
                            case_data['download_url'],
                            headers=headers,
                            timeout=60
                        )
                        
                        if pdf_response.status_code == 200:
                            # Save PDF
                            output_path = self._generate_output_path(citation)
                            output_path.write_bytes(pdf_response.content)
                            
                            # Cache it
                            self._cache_file(citation, pdf_response.content)
                            
                            return RetrievalResult(
                                status=RetrievalStatus.SUCCESS,
                                file_path=str(output_path),
                                source_url=case_data['download_url'],
                                metadata={'courtlistener_id': case_data.get('id')}
                            )
        
        except Exception as e:
            logger.error(f"CourtListener retrieval failed: {e}")
        
        return RetrievalResult(status=RetrievalStatus.FAILED, message="CourtListener retrieval failed")
    
    def _try_google_scholar_case(self, citation: Citation) -> RetrievalResult:
        """Try to retrieve case from Google Scholar"""
        metadata = citation.metadata
        
        try:
            # Construct Google Scholar search URL
            query = f"{metadata.title} {metadata.reporter} {metadata.page}"
            search_url = f"https://scholar.google.com/scholar?q={requests.utils.quote(query)}&btnG="
            
            # Add delay to avoid rate limiting
            time.sleep(2)
            
            response = self.session.get(search_url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for PDF links
                pdf_links = soup.find_all('a', href=True, text=lambda t: t and '[PDF]' in t)
                
                for link in pdf_links:
                    pdf_url = link['href']
                    if pdf_url.startswith('/'):
                        pdf_url = f"https://scholar.google.com{pdf_url}"
                    
                    # Try to download PDF
                    pdf_response = self.session.get(pdf_url, timeout=60)
                    
                    if pdf_response.status_code == 200:
                        output_path = self._generate_output_path(citation)
                        output_path.write_bytes(pdf_response.content)
                        
                        self._cache_file(citation, pdf_response.content)
                        
                        return RetrievalResult(
                            status=RetrievalStatus.SUCCESS,
                            file_path=str(output_path),
                            source_url=pdf_url,
                            metadata={'source': 'google_scholar'}
                        )
        
        except Exception as e:
            logger.error(f"Google Scholar retrieval failed: {e}")
        
        return RetrievalResult(status=RetrievalStatus.FAILED, message="Google Scholar retrieval failed")
    
    def _try_caselaw(self, citation: Citation) -> RetrievalResult:
        """Try to retrieve from Case.law (Harvard Law School)"""
        metadata = citation.metadata
        
        try:
            # Case.law API endpoint
            base_url = "https://api.case.law/v1"
            
            # Search for the case
            search_params = {
                'search': f"{metadata.title}",
                'jurisdiction': 'us' if not metadata.court else metadata.court.lower(),
                'decision_date_min': f"{int(metadata.year) - 1}-01-01" if metadata.year else None,
                'decision_date_max': f"{int(metadata.year) + 1}-12-31" if metadata.year else None,
            }
            
            # Remove None values
            search_params = {k: v for k, v in search_params.items() if v is not None}
            
            response = self.session.get(
                f"{base_url}/cases/",
                params=search_params,
                timeout=30
            )
            
            if response.status_code == 200:
                results = response.json()
                if results.get('results'):
                    case_data = results['results'][0]
                    
                    # Get case text (Case.law provides text, not PDF)
                    case_url = case_data.get('url')
                    if case_url:
                        case_response = self.session.get(case_url, timeout=30)
                        
                        if case_response.status_code == 200:
                            case_json = case_response.json()
                            
                            # Create a text file instead of PDF
                            output_path = self._generate_output_path(citation, extension='.txt')
                            
                            # Format the case text
                            case_text = self._format_caselaw_text(case_json)
                            output_path.write_text(case_text, encoding='utf-8')
                            
                            return RetrievalResult(
                                status=RetrievalStatus.PARTIAL,
                                file_path=str(output_path),
                                source_url=case_url,
                                message="Retrieved as text from Case.law (PDF not available)",
                                metadata={'caselaw_id': case_data.get('id')}
                            )
        
        except Exception as e:
            logger.error(f"Case.law retrieval failed: {e}")
        
        return RetrievalResult(status=RetrievalStatus.FAILED, message="Case.law retrieval failed")
    
    def _retrieve_statute(self, citation: Citation) -> RetrievalResult:
        """Retrieve statute documents"""
        metadata = citation.metadata
        
        # Try GovInfo API
        if 'U.S.C.' in metadata.reporter:
            result = self._try_govinfo_usc(citation)
            if result.status == RetrievalStatus.SUCCESS:
                return result
        
        # Try U.S. Code website
        result = self._try_uscode_house_gov(citation)
        if result.status == RetrievalStatus.SUCCESS:
            return result
        
        return RetrievalResult(
            status=RetrievalStatus.MANUAL_REQUIRED,
            message=f"Could not retrieve statute: {metadata.title} § {metadata.section}"
        )
    
    def _try_govinfo_usc(self, citation: Citation) -> RetrievalResult:
        """Try to retrieve U.S. Code from GovInfo"""
        metadata = citation.metadata
        api_key = self.apis.get('govinfo')
        
        try:
            # Extract title number
            title_match = re.search(r'(\d+)', metadata.title)
            if not title_match:
                return RetrievalResult(status=RetrievalStatus.FAILED, message="Could not parse title number")
            
            title_num = title_match.group(1)
            
            # GovInfo API endpoint
            base_url = "https://api.govinfo.gov"
            
            # Search for the statute
            search_url = f"{base_url}/collections/USCODE/search"
            params = {
                'api_key': api_key,
                'query': f'title:{title_num} AND section:{metadata.section}',
                'pageSize': 10
            }
            
            response = self.session.get(search_url, params=params, timeout=30)
            
            if response.status_code == 200:
                results = response.json()
                if results.get('results'):
                    # Get the first result
                    doc = results['results'][0]
                    
                    # Get PDF link
                    pdf_link = doc.get('download', {}).get('pdfLink')
                    if pdf_link:
                        pdf_response = self.session.get(
                            pdf_link,
                            params={'api_key': api_key},
                            timeout=60
                        )
                        
                        if pdf_response.status_code == 200:
                            output_path = self._generate_output_path(citation)
                            output_path.write_bytes(pdf_response.content)
                            
                            self._cache_file(citation, pdf_response.content)
                            
                            return RetrievalResult(
                                status=RetrievalStatus.SUCCESS,
                                file_path=str(output_path),
                                source_url=pdf_link,
                                metadata={'govinfo_id': doc.get('packageId')}
                            )
        
        except Exception as e:
            logger.error(f"GovInfo retrieval failed: {e}")
        
        return RetrievalResult(status=RetrievalStatus.FAILED, message="GovInfo retrieval failed")
    
    def _try_uscode_house_gov(self, citation: Citation) -> RetrievalResult:
        """Try to retrieve from uscode.house.gov"""
        metadata = citation.metadata
        
        try:
            # Extract title number
            title_match = re.search(r'(\d+)', metadata.title)
            if not title_match:
                return RetrievalResult(status=RetrievalStatus.FAILED)
            
            title_num = title_match.group(1).zfill(2)
            
            # Construct URL
            url = f"https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title{title_num}-section{metadata.section}"
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract statute text
                content_div = soup.find('div', {'class': 'section-content'})
                if content_div:
                    # Save as HTML file
                    output_path = self._generate_output_path(citation, extension='.html')
                    output_path.write_text(str(content_div), encoding='utf-8')
                    
                    return RetrievalResult(
                        status=RetrievalStatus.PARTIAL,
                        file_path=str(output_path),
                        source_url=url,
                        message="Retrieved as HTML from uscode.house.gov",
                        metadata={'source': 'uscode_house_gov'}
                    )
        
        except Exception as e:
            logger.error(f"uscode.house.gov retrieval failed: {e}")
        
        return RetrievalResult(status=RetrievalStatus.FAILED)
    
    def _retrieve_regulation(self, citation: Citation) -> RetrievalResult:
        """Retrieve regulation documents"""
        metadata = citation.metadata
        
        # Try eCFR
        result = self._try_ecfr(citation)
        if result.status == RetrievalStatus.SUCCESS:
            return result
        
        # Try GovInfo for CFR
        result = self._try_govinfo_cfr(citation)
        if result.status == RetrievalStatus.SUCCESS:
            return result
        
        return RetrievalResult(
            status=RetrievalStatus.MANUAL_REQUIRED,
            message=f"Could not retrieve regulation: {metadata.title} § {metadata.section}"
        )
    
    def _try_ecfr(self, citation: Citation) -> RetrievalResult:
        """Try to retrieve from eCFR.gov"""
        metadata = citation.metadata
        
        try:
            # Extract title number
            title_match = re.search(r'(\d+)', metadata.title)
            if not title_match:
                return RetrievalResult(status=RetrievalStatus.FAILED)
            
            title_num = title_match.group(1)
            
            # eCFR API endpoint
            url = f"https://www.ecfr.gov/api/versioner/v1/full/{metadata.year or 'current'}/title-{title_num}.xml"
            
            response = self.session.get(url, timeout=60)
            
            if response.status_code == 200:
                # Save as XML
                output_path = self._generate_output_path(citation, extension='.xml')
                output_path.write_bytes(response.content)
                
                return RetrievalResult(
                    status=RetrievalStatus.PARTIAL,
                    file_path=str(output_path),
                    source_url=url,
                    message="Retrieved as XML from eCFR",
                    metadata={'source': 'ecfr'}
                )
        
        except Exception as e:
            logger.error(f"eCFR retrieval failed: {e}")
        
        return RetrievalResult(status=RetrievalStatus.FAILED)
    
    def _retrieve_article(self, citation: Citation) -> RetrievalResult:
        """Retrieve article documents"""
        metadata = citation.metadata
        
        # Try CrossRef first
        result = self._try_crossref(citation)
        if result.status == RetrievalStatus.SUCCESS:
            return result
        
        # Try SSRN
        result = self._try_ssrn(citation)
        if result.status == RetrievalStatus.SUCCESS:
            return result
        
        # Try Google Scholar
        result = self._try_google_scholar_article(citation)
        if result.status == RetrievalStatus.SUCCESS:
            return result
        
        return RetrievalResult(
            status=RetrievalStatus.MANUAL_REQUIRED,
            message=f"Could not retrieve article: {', '.join(metadata.authors)} - {metadata.title}"
        )
    
    def _try_crossref(self, citation: Citation) -> RetrievalResult:
        """Try to retrieve article metadata from CrossRef"""
        metadata = citation.metadata
        
        try:
            # CrossRef API
            base_url = "https://api.crossref.org/works"
            
            # Search by title and author
            params = {
                'query.title': metadata.title,
                'query.author': metadata.authors[0] if metadata.authors else None,
                'rows': 5
            }
            
            # Remove None values
            params = {k: v for k, v in params.items() if v}
            
            response = self.session.get(base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('message', {}).get('items', [])
                
                if items:
                    article = items[0]
                    
                    # Check for full text link
                    links = article.get('link', [])
                    for link in links:
                        if link.get('content-type') == 'application/pdf':
                            pdf_url = link.get('URL')
                            if pdf_url:
                                # Try to download PDF
                                pdf_response = self.session.get(pdf_url, timeout=60)
                                
                                if pdf_response.status_code == 200:
                                    output_path = self._generate_output_path(citation)
                                    output_path.write_bytes(pdf_response.content)
                                    
                                    self._cache_file(citation, pdf_response.content)
                                    
                                    return RetrievalResult(
                                        status=RetrievalStatus.SUCCESS,
                                        file_path=str(output_path),
                                        source_url=pdf_url,
                                        metadata={'doi': article.get('DOI')}
                                    )
                    
                    # If no PDF, save metadata
                    output_path = self._generate_output_path(citation, extension='.json')
                    output_path.write_text(json.dumps(article, indent=2), encoding='utf-8')
                    
                    return RetrievalResult(
                        status=RetrievalStatus.PARTIAL,
                        file_path=str(output_path),
                        message="Retrieved metadata only from CrossRef",
                        metadata={'doi': article.get('DOI')}
                    )
        
        except Exception as e:
            logger.error(f"CrossRef retrieval failed: {e}")
        
        return RetrievalResult(status=RetrievalStatus.FAILED)
    
    def _try_ssrn(self, citation: Citation) -> RetrievalResult:
        """Try to retrieve from SSRN"""
        metadata = citation.metadata
        
        try:
            # Search SSRN
            query = f"{' '.join(metadata.authors)} {metadata.title}"
            search_url = f"https://papers.ssrn.com/sol3/results.cfm"
            
            params = {
                'form_name': 'journalBrowse',
                'journal_id': '0',
                'txtKeywords': query,
                'pubType': 'pub'
            }
            
            response = self.session.get(search_url, params=params, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for paper links
                paper_links = soup.find_all('a', {'class': 'title'})
                
                for link in paper_links[:3]:  # Check first 3 results
                    paper_url = link.get('href')
                    if paper_url:
                        # Get paper page
                        paper_response = self.session.get(paper_url, timeout=30)
                        
                        if paper_response.status_code == 200:
                            paper_soup = BeautifulSoup(paper_response.text, 'html.parser')
                            
                            # Look for download button
                            download_btn = paper_soup.find('a', {'class': 'download-button'})
                            if download_btn:
                                pdf_url = download_btn.get('href')
                                if pdf_url:
                                    if not pdf_url.startswith('http'):
                                        pdf_url = f"https://papers.ssrn.com{pdf_url}"
                                    
                                    # Download PDF
                                    pdf_response = self.session.get(pdf_url, timeout=60)
                                    
                                    if pdf_response.status_code == 200:
                                        output_path = self._generate_output_path(citation)
                                        output_path.write_bytes(pdf_response.content)
                                        
                                        self._cache_file(citation, pdf_response.content)
                                        
                                        return RetrievalResult(
                                            status=RetrievalStatus.SUCCESS,
                                            file_path=str(output_path),
                                            source_url=pdf_url,
                                            metadata={'source': 'ssrn', 'paper_url': paper_url}
                                        )
        
        except Exception as e:
            logger.error(f"SSRN retrieval failed: {e}")
        
        return RetrievalResult(status=RetrievalStatus.FAILED)
    
    def _retrieve_book(self, citation: Citation) -> RetrievalResult:
        """Retrieve book documents"""
        metadata = citation.metadata
        
        # Try Google Books
        result = self._try_google_books(citation)
        if result.status == RetrievalStatus.SUCCESS:
            return result
        
        # Try HathiTrust
        result = self._try_hathitrust(citation)
        if result.status == RetrievalStatus.SUCCESS:
            return result
        
        # Try OpenLibrary
        result = self._try_openlibrary(citation)
        if result.status == RetrievalStatus.SUCCESS:
            return result
        
        return RetrievalResult(
            status=RetrievalStatus.MANUAL_REQUIRED,
            message=f"Could not retrieve book: {', '.join(metadata.authors)} - {metadata.title}"
        )
    
    def _try_google_books(self, citation: Citation) -> RetrievalResult:
        """Try to retrieve from Google Books"""
        metadata = citation.metadata
        
        try:
            # Google Books API
            api_key = self.apis.get('google_books')
            base_url = "https://www.googleapis.com/books/v1/volumes"
            
            # Search for the book
            query = f"{' '.join(metadata.authors)} {metadata.title}"
            params = {
                'q': query,
                'maxResults': 5
            }
            
            if api_key:
                params['key'] = api_key
            
            response = self.session.get(base_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                
                if items:
                    book = items[0]
                    volume_info = book.get('volumeInfo', {})
                    
                    # Check for preview or full view
                    access_info = book.get('accessInfo', {})
                    if access_info.get('viewability') in ['PARTIAL', 'ALL_PAGES']:
                        # Save book metadata and preview link
                        output_path = self._generate_output_path(citation, extension='.json')
                        
                        book_data = {
                            'title': volume_info.get('title'),
                            'authors': volume_info.get('authors'),
                            'publisher': volume_info.get('publisher'),
                            'publishedDate': volume_info.get('publishedDate'),
                            'previewLink': volume_info.get('previewLink'),
                            'infoLink': volume_info.get('infoLink'),
                            'pageCount': volume_info.get('pageCount'),
                            'viewability': access_info.get('viewability')
                        }
                        
                        output_path.write_text(json.dumps(book_data, indent=2), encoding='utf-8')
                        
                        return RetrievalResult(
                            status=RetrievalStatus.PARTIAL,
                            file_path=str(output_path),
                            source_url=volume_info.get('previewLink'),
                            message=f"Google Books preview available ({access_info.get('viewability')})",
                            metadata={'google_books_id': book.get('id')}
                        )
        
        except Exception as e:
            logger.error(f"Google Books retrieval failed: {e}")
        
        return RetrievalResult(status=RetrievalStatus.FAILED)
    
    def _retrieve_web(self, citation: Citation) -> RetrievalResult:
        """Retrieve web sources"""
        metadata = citation.metadata
        
        if not metadata.url:
            return RetrievalResult(
                status=RetrievalStatus.FAILED,
                message="No URL found in citation"
            )
        
        try:
            # Download the web page
            response = self.session.get(metadata.url, timeout=30)
            
            if response.status_code == 200:
                # Save as HTML
                output_path = self._generate_output_path(citation, extension='.html')
                
                # Add metadata header
                html_content = f"""
                <!-- 
                Source URL: {metadata.url}
                Retrieved: {datetime.now().isoformat()}
                Title: {metadata.title}
                Authors: {', '.join(metadata.authors)}
                -->
                {response.text}
                """
                
                output_path.write_text(html_content, encoding='utf-8')
                
                # Also try to create PDF using wkhtmltopdf or similar if available
                pdf_path = self._convert_html_to_pdf(output_path, citation)
                
                if pdf_path:
                    return RetrievalResult(
                        status=RetrievalStatus.SUCCESS,
                        file_path=str(pdf_path),
                        source_url=metadata.url,
                        metadata={'original_html': str(output_path)}
                    )
                else:
                    return RetrievalResult(
                        status=RetrievalStatus.PARTIAL,
                        file_path=str(output_path),
                        source_url=metadata.url,
                        message="Retrieved as HTML (PDF conversion failed)"
                    )
        
        except Exception as e:
            logger.error(f"Web retrieval failed for {metadata.url}: {e}")
        
        return RetrievalResult(
            status=RetrievalStatus.FAILED,
            message=f"Could not retrieve web source: {metadata.url}"
        )
    
    def _retrieve_legislative(self, citation: Citation) -> RetrievalResult:
        """Retrieve legislative materials"""
        metadata = citation.metadata
        
        # Try Congress.gov API
        result = self._try_congress_gov(citation)
        if result.status == RetrievalStatus.SUCCESS:
            return result
        
        # Try GovInfo for legislative materials
        result = self._try_govinfo_legislative(citation)
        if result.status == RetrievalStatus.SUCCESS:
            return result
        
        return RetrievalResult(
            status=RetrievalStatus.MANUAL_REQUIRED,
            message=f"Could not retrieve legislative material: {metadata.reporter} {metadata.title}"
        )
    
    def _generate_output_path(self, citation: Citation, extension: str = '.pdf') -> Path:
        """Generate output file path for a citation"""
        # Format: SP-[source_id:03d]-[short_name]
        filename = f"SP-{citation.source_id:03d}-{self._sanitize_filename(citation.short_name)}{extension}"
        return self.output_dir / filename
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize filename to remove invalid characters"""
        import re
        # Remove invalid characters
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        # Replace spaces with underscores
        name = name.replace(' ', '_')
        # Limit length
        return name[:50]
    
    def _generate_cache_key(self, citation: Citation) -> str:
        """Generate cache key for a citation"""
        # Create hash of citation text
        hash_input = f"{citation.type.value}:{citation.raw_text}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def _cache_file(self, citation: Citation, content: bytes) -> None:
        """Cache a retrieved file"""
        cache_key = self._generate_cache_key(citation)
        cache_file = self.cache_dir / f"{cache_key}.pdf"
        cache_file.write_bytes(content)
    
    def _format_caselaw_text(self, case_json: Dict) -> str:
        """Format Case.law JSON into readable text"""
        lines = []
        
        # Add header
        lines.append(f"Case: {case_json.get('name', 'Unknown')}")
        lines.append(f"Citation: {case_json.get('citations', [{}])[0].get('cite', 'Unknown')}")
        lines.append(f"Court: {case_json.get('court', {}).get('name', 'Unknown')}")
        lines.append(f"Date: {case_json.get('decision_date', 'Unknown')}")
        lines.append("=" * 80)
        lines.append("")
        
        # Add case text
        for opinion in case_json.get('casebody', {}).get('data', {}).get('opinions', []):
            lines.append(f"Opinion by: {opinion.get('author', 'Unknown')}")
            lines.append(opinion.get('text', ''))
            lines.append("")
        
        return "\n".join(lines)
    
    def _convert_html_to_pdf(self, html_path: Path, citation: Citation) -> Optional[Path]:
        """Convert HTML file to PDF (requires wkhtmltopdf or similar)"""
        # This is a placeholder - implement based on available tools
        # Options: wkhtmltopdf, weasyprint, or headless Chrome
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get retrieval statistics"""
        return self.stats.copy()
    
    async def retrieve_batch_async(self, citations: List[Citation]) -> List[RetrievalResult]:
        """Retrieve multiple citations asynchronously"""
        tasks = []
        for citation in citations:
            task = asyncio.create_task(self._retrieve_async(citation))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results
    
    async def _retrieve_async(self, citation: Citation) -> RetrievalResult:
        """Async wrapper for retrieve method"""
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.retrieve, citation)