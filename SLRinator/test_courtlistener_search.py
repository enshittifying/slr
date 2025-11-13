#!/usr/bin/env python3

"""Test CourtListener search with actual case names"""

import json
import requests
from pathlib import Path

def main():
    # Load API key
    config_file = Path("config/api_keys.json")
    with open(config_file) as f:
        config = json.load(f)
    
    api_key = config['courtlistener']['token']
    
    # Test cases from footnote 3
    test_cases = [
        "Grunenthal GMBH v. Alkem Lab'ys Ltd.",
        "Takeda Pharms. U.S.A., Inc. v. W.-Ward Pharm. Corp.",
        "AstraZeneca LP v. Apotex, Inc."
    ]
    
    search_url = "https://www.courtlistener.com/api/rest/v3/search/"
    headers = {"Authorization": f"Token {api_key}"}
    
    for case_name in test_cases:
        print(f"\nSearching CourtListener for: {case_name}")
        print("-" * 50)
        
        search_params = {
            "q": case_name,
            "type": "o",  # opinions
            "order_by": "score desc",
            "format": "json"
        }
        
        try:
            response = requests.get(search_url, params=search_params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                print(f"Found {len(results)} results")
                
                for i, result in enumerate(results[:3]):  # Show top 3
                    print(f"  {i+1}. {result.get('caseName', 'N/A')}")
                    print(f"     Court: {result.get('court', 'N/A')}")
                    print(f"     Date: {result.get('dateFiled', 'N/A')}")
                    if result.get('download_url'):
                        print(f"     PDF: {result.get('download_url')}")
                    print()
            else:
                print(f"Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    main()