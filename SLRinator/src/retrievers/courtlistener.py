#!/usr/bin/env python3
"""
CourtListener API v4 Integration for Stanford Law Review Sourcepull
Retrieves actual court documents and opinions from CourtListener
"""

import os
import json
import time
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import re
from datetime import datetime

@dataclass
class CourtListenerConfig:
    """Configuration for CourtListener API"""
    api_key: str = ""
    base_url: str = "https://www.courtlistener.com/api/rest/v4"
    rate_limit: float = 0.5  # seconds between requests
    timeout: int = 30
    max_retries: int = 3
    
class CourtListenerRetriever:
    """Retrieves court documents from CourtListener API v4"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.config = CourtListenerConfig()
        self.config.api_key = api_key or os.environ.get('COURTLISTENER_API_KEY', '')
        self.session = requests.Session()
        if self.config.api_key:
            self.session.headers.update({
                'Authorization': f'Token {self.config.api_key}'
            })
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.config.rate_limit:
            time.sleep(self.config.rate_limit - elapsed)
        self.last_request_time = time.time()
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make API request with retries"""
        url = f"{self.config.base_url}/{endpoint}"
        
        for attempt in range(self.config.max_retries):
            try:
                self._rate_limit()
                response = self.session.get(
                    url, 
                    params=params,
                    timeout=self.config.timeout
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited, wait longer
                    wait_time = int(response.headers.get('Retry-After', 60))
                    print(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                elif response.status_code == 401:
                    print("Authentication failed. Please check your API key.")
                    return None
                else:
                    print(f"Request failed with status {response.status_code}")
                    
            except requests.RequestException as e:
                print(f"Request error (attempt {attempt + 1}): {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        return None
        
    def search_opinions(self, case_name: str, year: Optional[int] = None,
                       court: Optional[str] = None) -> Optional[List[Dict]]:
        """Search for court opinions"""
        params = {
            'q': case_name,
            'type': 'o',  # opinions
            'order_by': 'dateFiled desc',
            'stat_Precedential': 'on'
        }
        
        if year:
            params['filed_after'] = f"{year}-01-01"
            params['filed_before'] = f"{year}-12-31"
            
        if court:
            params['court'] = court
            
        result = self._make_request('search/', params)
        if result and 'results' in result:
            return result['results']
        return None
        
    def get_opinion_pdf(self, opinion_id: int, output_path: str) -> bool:
        """Download opinion PDF"""
        try:
            self._rate_limit()
            
            # Get opinion details first
            opinion = self._make_request(f'opinions/{opinion_id}/')
            if not opinion:
                return False
                
            # Check for PDF URL
            pdf_url = None
            if 'download_url' in opinion:
                pdf_url = opinion['download_url']
            elif 'local_path' in opinion:
                pdf_url = f"https://storage.courtlistener.com/{opinion['local_path']}"
                
            if not pdf_url:
                print(f"No PDF available for opinion {opinion_id}")
                return False
                
            # Download PDF
            response = requests.get(pdf_url, timeout=60, stream=True)
            if response.status_code == 200:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Downloaded PDF to {output_path}")
                return True
                
        except Exception as e:
            print(f"Error downloading PDF: {e}")
            
        return False
        
    def get_docket(self, docket_id: int) -> Optional[Dict]:
        """Get docket information"""
        return self._make_request(f'dockets/{docket_id}/')
        
    def get_docket_entries(self, docket_id: int) -> Optional[List[Dict]]:
        """Get docket entries"""
        result = self._make_request(f'docket-entries/', {'docket': docket_id})
        if result and 'results' in result:
            return result['results']
        return None
        
    def search_by_citation(self, volume: str, reporter: str, page: str) -> Optional[Dict]:
        """Search for a case by citation"""
        # Format citation for search
        citation = f"{volume} {reporter} {page}"
        
        params = {
            'q': citation,
            'type': 'o',
            'order_by': 'dateFiled desc'
        }
        
        result = self._make_request('search/', params)
        if result and 'results' in result and len(result['results']) > 0:
            # Return the most relevant result
            return result['results'][0]
        return None
        
    def get_case_by_citation(self, citation: str) -> Optional[Tuple[Dict, str]]:
        """
        Retrieve a case by its citation string
        Returns tuple of (case_data, pdf_path) or None
        """
        # Parse citation
        match = re.match(r'(\d+)\s+([A-Za-z.\s]+)\s+(\d+)', citation)
        if not match:
            print(f"Could not parse citation: {citation}")
            return None
            
        volume, reporter, page = match.groups()
        
        # Search for the case
        case_data = self.search_by_citation(volume, reporter.strip(), page)
        if not case_data:
            print(f"Case not found: {citation}")
            return None
            
        # Try to get the PDF
        if 'id' in case_data:
            output_dir = Path("output/data/Sourcepull/CourtListener")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Clean filename
            case_name = case_data.get('caseName', 'unknown').replace('/', '_')
            pdf_path = output_dir / f"{case_name}_{volume}_{reporter}_{page}.pdf"
            
            if self.get_opinion_pdf(case_data['id'], str(pdf_path)):
                return case_data, str(pdf_path)
                
        return case_data, None
        

class CitationExtractor:
    """Extract citations from law review articles"""
    
    # Common citation patterns
    CASE_PATTERN = re.compile(
        r"([A-Z][A-Za-z\s,.'&]+?)\s+v\.\s+([A-Z][A-Za-z\s,.'&]+?),\s+"
        r"(\d+)\s+([A-Z][A-Za-z.\s]+)\s+(\d+)(?:,\s+(\d+))?\s*\(([^)]+)\)"
    )
    
    STATUTE_PATTERN = re.compile(
        r"(\d+)\s+U\.S\.C\.\s+§+\s*(\d+[a-z]?)"
    )
    
    ARTICLE_PATTERN = re.compile(
        r"([A-Z][A-Za-z\s&.]+?),\s+"
        r"([A-Za-z\s,:()'-]+?),\s+"
        r"(\d+)\s+([A-Z][A-Za-z.\s]+)\s+(\d+)(?:,\s+(\d+))?\s*\((\d{4})\)"
    )
    
    @classmethod
    def extract_from_text(cls, text: str) -> List[Dict]:
        """Extract all citations from text"""
        citations = []
        
        # Extract cases
        for match in cls.CASE_PATTERN.finditer(text):
            citations.append({
                'type': 'case',
                'party1': match.group(1).strip(),
                'party2': match.group(2).strip(),
                'volume': match.group(3),
                'reporter': match.group(4).strip(),
                'page': match.group(5),
                'pincite': match.group(6) if match.group(6) else None,
                'year': match.group(7).strip(),
                'full_citation': match.group(0)
            })
            
        # Extract statutes
        for match in cls.STATUTE_PATTERN.finditer(text):
            citations.append({
                'type': 'statute',
                'title': match.group(1),
                'section': match.group(2),
                'full_citation': match.group(0)
            })
            
        # Extract articles
        for match in cls.ARTICLE_PATTERN.finditer(text):
            citations.append({
                'type': 'article',
                'author': match.group(1).strip(),
                'title': match.group(2).strip(),
                'volume': match.group(3),
                'journal': match.group(4).strip(),
                'page': match.group(5),
                'pincite': match.group(6) if match.group(6) else None,
                'year': match.group(7),
                'full_citation': match.group(0)
            })
            
        return citations


def setup_api_key():
    """Interactive setup for CourtListener API key"""
    print("\n" + "="*60)
    print("CourtListener API Setup")
    print("="*60)
    
    print("\nTo use CourtListener API, you need a free API key.")
    print("Register at: https://www.courtlistener.com/register/")
    print("Then get your API key from: https://www.courtlistener.com/api/")
    
    api_key = input("\nEnter your CourtListener API key (or press Enter to skip): ").strip()
    
    if api_key:
        # Save to environment file
        env_file = Path(".env")
        with open(env_file, 'a') as f:
            f.write(f"\nCOURTLISTENER_API_KEY={api_key}\n")
        print(f"✅ API key saved to {env_file}")
        return api_key
    else:
        print("⚠️ Skipping CourtListener API setup")
        return None


if __name__ == "__main__":
    # Example usage
    api_key = setup_api_key()
    if api_key:
        retriever = CourtListenerRetriever(api_key)
        
        # Test with a known case
        print("\nTesting with Alice Corp. v. CLS Bank...")
        results = retriever.search_opinions("Alice Corp CLS Bank", year=2014, court="scotus")
        
        if results:
            print(f"Found {len(results)} results")
            for r in results[:3]:
                print(f"  - {r.get('caseName', 'Unknown')}")
        else:
            print("No results found")