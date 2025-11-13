#!/usr/bin/env python3
"""
SLRinator Complete Workflow
1. Intake DOCX file
2. Parse footnotes with GPT-5
3. Run sourcepull with proper naming
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.processors.footnote_extractor import extract_footnotes_from_docx
from src.core.gpt_citation_parser import GPTCitationParser, ParsedFootnote, ParsedCitation
from src.core.sourcepull_system import SourcepullSystem
from src.core.source_identifier import CitationComponents, SourceType


def setup_logging():
    """Setup logging configuration"""
    log_dir = Path("output/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"slrinator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def generate_source_name(citation: ParsedCitation) -> str:
    """Generate a short name for the source file"""
    if citation.citation_type == "case" and citation.party1 and citation.party2:
        # Clean party names
        party1 = citation.party1.replace(".", "").replace(",", "").split()[0]
        party2 = citation.party2.replace(".", "").replace(",", "").split()[0]
        return f"{party1}_v_{party2}"
    
    elif citation.citation_type == "statute":
        return f"{citation.title_number}USC{citation.section}".replace(".", "_")
    
    elif citation.citation_type == "regulation":
        return f"{citation.title_number}CFR{citation.section}".replace(".", "_")
    
    elif citation.citation_type == "article" and citation.author:
        # Use last name of first author
        author_name = citation.author.split()[-1] if citation.author else "Article"
        return author_name.replace(",", "")
    
    elif citation.citation_type == "book" and (citation.author or citation.book_title):
        if citation.author:
            return citation.author.split()[-1].replace(",", "")
        else:
            return citation.book_title.split()[0] if citation.book_title else "Book"
    
    else:
        # Generic name
        return f"{citation.citation_type}_{datetime.now().strftime('%H%M%S')}"


def convert_parsed_to_components(citation: ParsedCitation) -> CitationComponents:
    """Convert ParsedCitation to CitationComponents for sourcepull"""
    components = CitationComponents()
    
    # Map fields
    components.party1 = citation.party1
    components.party2 = citation.party2
    components.volume = citation.volume
    components.reporter = citation.reporter
    components.page = citation.page
    components.pincite = citation.pincite
    components.court = citation.court
    components.year = citation.year
    components.title_number = citation.title_number
    components.code_name = citation.code_type
    components.section = citation.section
    components.author = citation.author
    components.article_title = citation.article_title
    components.journal = citation.journal
    components.book_title = citation.book_title
    components.url = citation.url
    
    return components


def process_document(docx_path: str, 
                     footnote_range: Optional[str] = None,
                     use_gpt: bool = True,
                     output_dir: str = "output/data/Sourcepull") -> Dict:
    """
    Process a complete document through the SLRinator workflow
    
    Args:
        docx_path: Path to the Word document
        footnote_range: Optional range of footnotes to process (e.g., "1-50")
        use_gpt: Whether to use GPT for parsing (requires API key)
        output_dir: Output directory for PDFs
        
    Returns:
        Dictionary with processing results
    """
    logger = setup_logging()
    logger.info(f"Starting SLRinator workflow for: {docx_path}")
    
    # Step 1: Extract footnotes from DOCX
    logger.info("Step 1: Extracting footnotes from document...")
    footnotes = extract_footnotes_from_docx(docx_path)
    
    # Filter by range if specified
    if footnote_range:
        selected = parse_footnote_range(footnote_range)
        footnotes = {fn: text for fn, text in footnotes.items() if fn in selected}
    
    logger.info(f"  Extracted {len(footnotes)} footnotes")
    
    # Step 2: Parse citations with GPT
    logger.info("Step 2: Parsing citations with GPT-5...")
    
    if use_gpt:
        parser = GPTCitationParser()
        parsed_footnotes = parser.parse_footnotes_batch(footnotes)
        
        # Export parsed citations for review
        parser.export_to_json(parsed_footnotes)
    else:
        # Use basic parsing
        parser = GPTCitationParser()
        parsed_footnotes = {}
        for fn_num, fn_text in footnotes.items():
            parsed_footnotes[fn_num] = parser._basic_parse(fn_num, fn_text)
    
    # Count total citations
    total_citations = sum(len(pf.citations) for pf in parsed_footnotes.values())
    logger.info(f"  Found {total_citations} citations across {len(parsed_footnotes)} footnotes")
    
    # Step 3: Run sourcepull for each citation
    logger.info("Step 3: Running sourcepull...")
    
    system = SourcepullSystem()
    results = []
    source_counter = 1  # For SP-XXX numbering
    
    # Process each footnote's citations
    for fn_num, parsed_fn in sorted(parsed_footnotes.items()):
        for citation in parsed_fn.citations:
            # Skip non-substantive citations
            if citation.is_short_form or citation.citation_type in ["other", "unknown"]:
                continue
            
            # Generate source ID and name
            source_id = f"SP-{source_counter:03d}"
            source_name = generate_source_name(citation)
            
            logger.info(f"  Processing {source_id}: {citation.citation_text[:50]}...")
            
            # Convert to components for sourcepull
            components = convert_parsed_to_components(citation)
            
            # Map citation type to SourceType
            source_type_map = {
                "case": SourceType.UNKNOWN,  # Will be refined by identifier
                "statute": SourceType.FEDERAL_STATUTE,
                "regulation": SourceType.FEDERAL_REGULATION,
                "article": SourceType.LAW_REVIEW_ARTICLE,
                "book": SourceType.BOOK,
                "website": SourceType.WEBSITE,
                "legislative": SourceType.CONGRESSIONAL_RECORD,
                "brief": SourceType.BRIEF,
            }
            
            # Run sourcepull
            result = system.process_citation(fn_num, citation.citation_text)
            
            # If successful, rename the file
            if result.final_status == "success" and result.final_file_path:
                old_path = Path(result.final_file_path)
                new_filename = f"{source_id}-{source_name}.pdf"
                new_path = old_path.parent / new_filename
                
                try:
                    old_path.rename(new_path)
                    result.final_file_path = str(new_path)
                    logger.info(f"    ✓ Retrieved and saved as: {new_filename}")
                except Exception as e:
                    logger.error(f"    Error renaming file: {e}")
            
            # Store result with metadata
            results.append({
                "source_id": source_id,
                "footnote": fn_num,
                "citation": citation.citation_text,
                "type": citation.citation_type,
                "status": result.final_status,
                "file": result.final_file_path,
                "source_name": source_name
            })
            
            source_counter += 1
    
    # Step 4: Generate summary report
    logger.info("Step 4: Generating report...")
    
    report = {
        "document": str(Path(docx_path).name),
        "processed_at": datetime.now().isoformat(),
        "statistics": {
            "total_footnotes": len(footnotes),
            "total_citations": total_citations,
            "sources_processed": len(results),
            "successful_retrievals": sum(1 for r in results if r["status"] == "success"),
            "failed_retrievals": sum(1 for r in results if r["status"] == "failed")
        },
        "sources": results
    }
    
    # Save report
    report_path = Path(output_dir) / "sourcepull_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Create spreadsheet-ready CSV
    create_sourcepull_spreadsheet(results, output_dir)
    
    logger.info(f"✅ Workflow complete! Report saved to: {report_path}")
    
    return report


def create_sourcepull_spreadsheet(results: List[Dict], output_dir: str):
    """Create a CSV file ready for import to Google Sheets"""
    import csv
    
    csv_path = Path(output_dir) / "sourcepull_spreadsheet.csv"
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header row
        writer.writerow([
            "Source ID",
            "Footnote",
            "Short Name",
            "Full Citation",
            "Type",
            "Status",
            "File Name",
            "Date Retrieved"
        ])
        
        # Data rows
        for result in results:
            writer.writerow([
                result["source_id"],
                result["footnote"],
                result["source_name"],
                result["citation"],
                result["type"],
                "✓" if result["status"] == "success" else "✗",
                Path(result["file"]).name if result["file"] else "",
                datetime.now().strftime("%Y-%m-%d")
            ])
    
    return csv_path


def parse_footnote_range(range_str: str) -> set:
    """Parse a footnote range string like '1-50' or '1,3,5-10'"""
    selected = set()
    parts = range_str.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            selected.update(range(int(start), int(end) + 1))
        else:
            selected.add(int(part))
    
    return selected


def main():
    """Main entry point for SLRinator workflow"""
    parser = argparse.ArgumentParser(
        description="SLRinator - Stanford Law Review Sourcepull Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process entire document with GPT parsing
  python slrinator_workflow.py article.docx
  
  # Process specific footnotes
  python slrinator_workflow.py article.docx --footnotes 1-50
  
  # Process without GPT (basic parsing only)
  python slrinator_workflow.py article.docx --no-gpt
  
  # Custom output directory
  python slrinator_workflow.py article.docx --output ~/Desktop/Sourcepull
        """
    )
    
    parser.add_argument('docx', help='Path to Word document')
    parser.add_argument('--footnotes', type=str, help='Footnote range (e.g., "1-50" or "1,3,5-10")')
    parser.add_argument('--no-gpt', action='store_true', help='Disable GPT parsing')
    parser.add_argument('--output', type=str, default='output/data/Sourcepull',
                       help='Output directory for PDFs')
    parser.add_argument('--config', type=str, default='config/api_keys.json',
                       help='Path to API keys configuration')
    
    args = parser.parse_args()
    
    # Check if DOCX exists
    if not Path(args.docx).exists():
        print(f"Error: File not found: {args.docx}")
        return 1
    
    print("\n" + "="*70)
    print(" "*20 + "SLRINATOR WORKFLOW")
    print(" "*15 + "Stanford Law Review Sourcepull")
    print("="*70 + "\n")
    
    # Run the workflow
    try:
        report = process_document(
            docx_path=args.docx,
            footnote_range=args.footnotes,
            use_gpt=not args.no_gpt,
            output_dir=args.output
        )
        
        # Print summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Total Footnotes: {report['statistics']['total_footnotes']}")
        print(f"Total Citations: {report['statistics']['total_citations']}")
        print(f"Sources Retrieved: {report['statistics']['successful_retrievals']}/{report['statistics']['sources_processed']}")
        
        success_rate = (report['statistics']['successful_retrievals'] / 
                       report['statistics']['sources_processed'] * 100 
                       if report['statistics']['sources_processed'] > 0 else 0)
        print(f"Success Rate: {success_rate:.1f}%")
        
        print(f"\nOutput Directory: {args.output}")
        print(f"Report: {args.output}/sourcepull_report.json")
        print(f"Spreadsheet: {args.output}/sourcepull_spreadsheet.csv")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())