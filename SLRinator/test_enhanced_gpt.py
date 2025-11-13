#!/usr/bin/env python3

"""Direct test of enhanced GPT parser"""

from pathlib import Path
import json
from src.core.enhanced_gpt_parser import EnhancedGPTParser

def main():
    # Load API key
    config_file = Path("config/api_keys.json")
    with open(config_file) as f:
        config = json.load(f)
    api_key = config['openai']['api_key']
    
    # Initialize parser
    parser = EnhancedGPTParser(api_key)
    
    # Test footnote 3 text
    footnote_text = """21 U.S.C. § 355(c)(3)(C);  see also  Grunenthal GMBH v. Alkem Lab'ys Ltd., 919 F.3d 1333, 1339 (Fed. Cir. 2019) ("[W] e ask whether the Hikma and Actavis labels instruct users to treat polyneuropathic...; Takeda Pharms. U.S.A., Inc. v. W.-Ward Pharm. Corp., 785 F.3d 625, 631 (Fed. Cir. 2015); AstraZeneca LP v. Apotex, Inc., 633 F.3d 1042, 1060 (Fed. Cir. 2010)."""
    
    print("Testing Enhanced GPT Parser")
    print("="*50)
    print(f"Input: {footnote_text[:100]}...")
    
    # Parse
    result = parser.parse_footnote(3, footnote_text)
    
    print(f"\nParsed {len(result.citations)} citations:")
    print(f"Confidence: {result.parsing_confidence}")
    print(f"Reasoning: {result.gpt_reasoning}")
    
    for i, citation in enumerate(result.citations, 1):
        print(f"\nCitation {i}:")
        print(f"  ID: {citation.citation_id}")
        print(f"  Type: {citation.citation_type}")
        print(f"  Full text: {citation.full_text}")
        print(f"  Case name: {citation.case_name}")
        print(f"  Volume: {citation.volume}")
        print(f"  Reporter: {citation.reporter}")
        print(f"  Page: {citation.page}")
        print(f"  Court: {citation.court}")
        print(f"  Year: {citation.year}")
        print(f"  Title number: {citation.title_number}")
        print(f"  Code name: {citation.code_name}")
        print(f"  Section: {citation.section}")

if __name__ == "__main__":
    main()