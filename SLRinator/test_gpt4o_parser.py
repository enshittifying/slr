#!/usr/bin/env python3
"""
Test the updated GPT-4o parser
"""

import json
from pathlib import Path
from src.core.enhanced_gpt_parser import EnhancedGPTParser

def test_parser():
    """Test GPT-4o parser"""
    
    # Load API key
    config_file = Path("config/api_keys.json")
    with open(config_file) as f:
        config = json.load(f)
    api_key = config['openai']['api_key']
    
    parser = EnhancedGPTParser(api_key)
    
    # Test simple citation
    print("=" * 60)
    print("TESTING GPT-4o PARSER")
    print("=" * 60)
    
    test_cases = [
        "See Smith v. Jones, 123 U.S. 456 (1995).",
        "21 U.S.C. § 355(c)(3)(C).",
        "See Smith v. Jones, 123 U.S. 456 (1995); 21 U.S.C. § 355(c)."
    ]
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{test_text}'")
        try:
            result = parser.parse_footnote(i, test_text)
            print(f"  Citations found: {len(result.citations)}")
            print(f"  Confidence: {result.parsing_confidence}")
            
            for j, cite in enumerate(result.citations):
                print(f"    {j+1}. {cite.citation_type}: {cite.full_text}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    test_parser()