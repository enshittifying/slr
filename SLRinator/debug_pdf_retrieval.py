#!/usr/bin/env python3

"""Debug PDF retrieval step by step"""

import json
import requests
import urllib3
from pathlib import Path
from src.core.enhanced_gpt_parser import Citation

# Suppress SSL warnings for government sites
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_pdf_retrieval():
    # Load API key
    config_file = Path("config/api_keys.json")
    with open(config_file) as f:
        config = json.load(f)
    
    api_key = config['courtlistener']['token']
    
    # Create test citation from our GPT results
    citation = Citation(
        citation_id="2",
        citation_type="case",
        full_text="Grunenthal GMBH v. Alkem Lab'ys Ltd., 919 F.3d 1333, 1339 (Fed. Cir. 2019)",
        case_name="Grunenthal GMBH v. Alkem Lab'ys Ltd.",
        volume="919",
        reporter="F.3d",
        page="1333",
        pincite="1339",
        court="Fed. Cir.",
        year="2019"
    )
    
    print(f"Testing retrieval for: {citation.case_name}")
    print(f"Citation: {citation.full_text}")
    print("=" * 60)
    
    # Step 1: Search CourtListener with improved query
    search_url = "https://www.courtlistener.com/api/rest/v3/search/"
    
    # Try multiple search strategies
    search_strategies = [
        # Strategy 1: Just case name
        citation.case_name,
        # Strategy 2: Case name + year  
        f"{citation.case_name} {citation.year}",
        # Strategy 3: Simplified case name
        citation.case_name.replace('GMBH', '').replace('Ltd.', ''),
        # Strategy 4: Just party names
        "Grunenthal Alkem"
    ]
    
    headers = {"Authorization": f"Token {api_key}"}
    
    for i, search_query in enumerate(search_strategies, 1):
        print(f"\nStrategy {i} - Search query: {search_query}")
        
        search_params = {
            "q": search_query,
            "type": "o",  # opinions
            "order_by": "score desc",
            "format": "json"
        }
        
        search_response = requests.get(search_url, params=search_params, headers=headers, timeout=10)
        
        if search_response.status_code != 200:
            print(f"Search failed: {search_response.status_code}")
            continue
        
        search_data = search_response.json()
        results = search_data.get("results", [])
        print(f"Found {len(results)} results")
        
        if len(results) > 0:
            print("Using this strategy for PDF download...")
            break
    
    if len(results) == 0:
        print("No results found with any search strategy")
        return
    
    # Step 2: Try each result for PDF download
    for i, result in enumerate(results[:3]):
        print(f"\nResult {i+1}: {result.get('caseName', 'N/A')}")
        print(f"  Date: {result.get('dateFiled', 'N/A')}")
        print(f"  Court: {result.get('court', 'N/A')}")
        
        download_url = result.get("download_url")
        if download_url:
            print(f"  PDF URL: {download_url}")
            
            # Try to download with SSL bypass for government sites
            try:
                if 'gov' in download_url:
                    pdf_response = requests.get(download_url, headers=headers, timeout=30, verify=False)
                else:
                    pdf_response = requests.get(download_url, headers=headers, timeout=30)
                print(f"  PDF Response: {pdf_response.status_code}")
                print(f"  Content Type: {pdf_response.headers.get('content-type', 'N/A')}")
                print(f"  Content Length: {len(pdf_response.content)} bytes")
                
                if pdf_response.status_code == 200:
                    content_type = pdf_response.headers.get("content-type", "")
                    if content_type.startswith("application/pdf"):
                        print(f"  ✅ Valid PDF downloaded!")
                        
                        # Save for testing
                        test_file = Path(f"debug_test_{i+1}.pdf")
                        with open(test_file, 'wb') as f:
                            f.write(pdf_response.content)
                        print(f"  Saved as: {test_file}")
                    else:
                        print(f"  ❌ Not a PDF: {content_type}")
                        if len(pdf_response.content) < 500:
                            print(f"  Content: {pdf_response.content[:200]}")
                else:
                    print(f"  ❌ Download failed: {pdf_response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Exception: {e}")
        else:
            print(f"  ❌ No download_url")

if __name__ == "__main__":
    test_pdf_retrieval()