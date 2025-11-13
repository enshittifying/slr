#!/usr/bin/env python3

"""Debug statute retrieval specifically"""

from pathlib import Path
import json
from src.core.enhanced_gpt_parser import Citation
from src.core.pdf_retriever import PDFRetriever

def main():
    # Load API keys
    config_file = Path("config/api_keys.json")
    with open(config_file) as f:
        config = json.load(f)
    
    # Create retriever
    output_dir = Path("debug_statute_output")
    output_dir.mkdir(exist_ok=True)
    
    retriever = PDFRetriever(api_keys=config, output_dir=output_dir)
    
    # Test citation with full structured data
    citation = Citation(
        citation_id="statute_test",
        citation_type="statute",
        full_text="21 U.S.C. § 355(c)(3)(C)",
        title_number="21",
        code_name="U.S.C.",
        section="355(c)(3)(C)"
    )
    
    print("Testing statute retrieval...")
    print(f"Citation: {citation.full_text}")
    print(f"Title: {citation.title_number}")
    print(f"Code: {citation.code_name}")
    print(f"Section: {citation.section}")
    print("="*50)
    
    # Test retrieval
    result = retriever.retrieve_citation(citation)
    
    print(f"Success: {result.success}")
    print(f"Source: {result.source_name}")
    print(f"Error: {result.error_message}")
    if result.file_path:
        print(f"File: {result.file_path}")
        print(f"Size: {result.file_size_bytes} bytes")
        print(f"Valid PDF: {result.is_valid_pdf}")

if __name__ == "__main__":
    main()