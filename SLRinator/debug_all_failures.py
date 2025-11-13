#!/usr/bin/env python3

"""Debug all 3 failing citations"""

import json
import requests
import urllib3
from pathlib import Path
from src.core.enhanced_gpt_parser import Citation

# Suppress SSL warnings 
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_statute_retrieval():
    """Test statute citation: 21 U.S.C. § 355(c)(3)(C)"""
    print("="*60)
    print("TESTING STATUTE: 21 U.S.C. § 355(c)(3)(C)")
    print("="*60)
    
    citation = Citation(
        citation_id="1",
        citation_type="statute",
        full_text="21 U.S.C. § 355(c)(3)(C)",
        title_number="21",
        code_name="U.S.C.",
        section="355(c)(3)(C)"
    )
    
    # Try legal information institute
    lii_url = f"https://www.law.cornell.edu/uscode/text/{citation.title_number}/{citation.section.split('(')[0]}"
    print(f"Testing LII URL: {lii_url}")
    
    try:
        response = requests.get(lii_url, timeout=10)
        print(f"LII Response: {response.status_code}")
        if response.status_code == 200:
            print("✅ LII has the statute text")
        else:
            print("❌ LII failed")
    except Exception as e:
        print(f"❌ LII exception: {e}")
    
    # Try house.gov
    house_url = f"https://uscode.house.gov/view.xhtml?req=granule:USC-prelim-title{citation.title_number}-section{citation.section.split('(')[0]}"
    print(f"\nTesting House URL: {house_url}")
    
    try:
        response = requests.get(house_url, timeout=10)
        print(f"House Response: {response.status_code}")
        if response.status_code == 200:
            print("✅ House.gov has the statute")
    except Exception as e:
        print(f"❌ House.gov exception: {e}")

def test_case_retrieval():
    """Test the failing case citations"""
    config_file = Path("config/api_keys.json")
    with open(config_file) as f:
        config = json.load(f)
    api_key = config['courtlistener']['token']
    
    failing_cases = [
        Citation(
            citation_id="3",
            citation_type="case",
            full_text="Takeda Pharms. U.S.A., Inc. v. W.-Ward Pharm. Corp., 785 F.3d 625, 631 (Fed. Cir. 2015)",
            case_name="Takeda Pharms. U.S.A., Inc. v. W.-Ward Pharm. Corp.",
            volume="785",
            reporter="F.3d",
            page="625",
            court="Fed. Cir.",
            year="2015"
        ),
        Citation(
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
    ]
    
    search_url = "https://www.courtlistener.com/api/rest/v3/search/"
    headers = {"Authorization": f"Token {api_key}"}
    
    for citation in failing_cases:
        print("="*60)
        print(f"TESTING CASE: {citation.case_name} ({citation.year})")
        print("="*60)
        
        # Try multiple search strategies
        search_strategies = [
            citation.case_name,  # Full name
            citation.case_name.split(' v. ')[0],  # Just plaintiff
            f"{citation.case_name} {citation.year}",  # With year
        ]
        
        found_results = False
        for strategy in search_strategies:
            print(f"\nTrying search: {strategy}")
            
            search_params = {
                "q": strategy,
                "type": "o", 
                "order_by": "score desc",
                "format": "json"
            }
            
            try:
                response = requests.get(search_url, params=search_params, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])
                    print(f"Found {len(results)} results")
                    
                    # Look for exact matches
                    for i, result in enumerate(results[:5]):
                        case_name = result.get('caseName', '')
                        date = result.get('dateFiled', '')
                        court = result.get('court', '')
                        download_url = result.get('download_url', '')
                        
                        print(f"  {i+1}. {case_name}")
                        print(f"     Date: {date}")
                        print(f"     Court: {court}")
                        
                        if citation.year in date and 'Fed' in court:
                            print(f"     ✅ POTENTIAL MATCH!")
                            if download_url:
                                print(f"     PDF: {download_url}")
                                # Test PDF download
                                try:
                                    if 'gov' in download_url:
                                        pdf_response = requests.get(download_url, headers=headers, timeout=30, verify=False)
                                    else:
                                        pdf_response = requests.get(download_url, headers=headers, timeout=30)
                                    
                                    if pdf_response.status_code == 200 and pdf_response.headers.get("content-type", "").startswith("application/pdf"):
                                        print(f"     ✅ PDF download works: {len(pdf_response.content)} bytes")
                                        found_results = True
                                    else:
                                        print(f"     ❌ PDF failed: {pdf_response.status_code}")
                                except Exception as e:
                                    print(f"     ❌ PDF exception: {e}")
                            else:
                                print(f"     ❌ No download URL")
                        print()
                    
                    if found_results:
                        break
                else:
                    print(f"Search failed: {response.status_code}")
            except Exception as e:
                print(f"Search exception: {e}")
        
        if not found_results:
            print("❌ No working PDFs found for this case")

if __name__ == "__main__":
    test_statute_retrieval()
    test_case_retrieval()