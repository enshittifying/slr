#!/usr/bin/env python3

"""Debug the AstraZeneca case specifically"""

import json
import requests
import urllib3
from pathlib import Path
from src.core.enhanced_gpt_parser import Citation

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_astrazeneca():
    citation = Citation(
        citation_id="4",
        citation_type="case",
        full_text="AstraZeneca LP v. Apotex, Inc., 633 F.3d 1042, 1060 (Fed. Cir. 2010)",
        case_name="AstraZeneca LP v. Apotex, Inc.",
        volume="633",
        reporter="F.3d",
        page="1042",
        court="Fed. Cir.",
        year="2010"
    )
    
    print(f"Debugging: {citation.case_name}")
    print("="*60)
    
    config_file = Path("config/api_keys.json")
    with open(config_file) as f:
        config = json.load(f)
    api_key = config['courtlistener']['token']
    
    # Try CourtListener search
    search_url = "https://www.courtlistener.com/api/rest/v3/search/"
    headers = {"Authorization": f"Token {api_key}"}
    
    search_params = {
        "q": citation.case_name,
        "type": "o",
        "order_by": "score desc",
        "format": "json"
    }
    
    response = requests.get(search_url, params=search_params, headers=headers, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])
        
        print(f"Found {len(results)} results on CourtListener")
        
        for i, result in enumerate(results[:5]):
            case_name = result.get('caseName', '')
            date = result.get('dateFiled', '')
            court = result.get('court', '')
            download_url = result.get('download_url', '')
            absolute_url = result.get('absolute_url', '')
            
            print(f"\n{i+1}. {case_name}")
            print(f"   Date: {date}")
            print(f"   Court: {court}")
            print(f"   Download URL: {download_url or 'NONE'}")
            print(f"   Web URL: {absolute_url}")
            
            # If this is our target case but no download URL, try alternatives
            if citation.year in date and 'AstraZeneca' in case_name and not download_url:
                print(f"   ⚠️  Found target case but no PDF download!")
                
                # Try to find alternative sources
                # Check if there are related documents
                if 'id' in result:
                    opinion_id = result['id']
                    print(f"   Opinion ID: {opinion_id}")
                    
                    # Try to get more details about this opinion
                    detail_url = f"https://www.courtlistener.com/api/rest/v3/opinions/{opinion_id}/"
                    try:
                        detail_response = requests.get(detail_url, headers=headers, timeout=10)
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            print(f"   Detail available: {bool(detail_data)}")
                            if detail_data.get('download_url'):
                                print(f"   Detail PDF URL: {detail_data['download_url']}")
                            if detail_data.get('html'):
                                print(f"   HTML available: {len(detail_data['html'])} chars")
                            if detail_data.get('plain_text'):
                                print(f"   Plain text available: {len(detail_data['plain_text'])} chars")
                    except Exception as e:
                        print(f"   Detail fetch failed: {e}")
    
    # Try searching Google Scholar as alternative
    print(f"\n" + "="*60)
    print("TRYING ALTERNATIVE: Google Scholar search")
    
    # Simple Google Scholar search (would need selenium for full access)
    scholar_query = f"{citation.case_name} {citation.volume} F.3d {citation.page}"
    print(f"Would search: {scholar_query}")
    
    # Try Justia search (free legal database)
    print(f"\n" + "="*60)
    print("TRYING ALTERNATIVE: Justia search")
    
    justia_query = citation.case_name.replace(' v. ', ' v ')
    justia_search_url = f"https://law.justia.com/search/?cx=004471346742245944130%3A-felt3rre8i&cof=FORID%3A11&q={justia_query}&sa=Search"
    print(f"Justia search URL: {justia_search_url}")
    
    # Note: Justia would require web scraping to get actual PDFs
    print("   (Note: Would need web scraping to access Justia PDFs)")

if __name__ == "__main__":
    test_astrazeneca()