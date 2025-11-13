#!/usr/bin/env python3
"""
Main Sourcepull Execution Script for Stanford Law Review
Processes footnotes from a Word document or list of citations
"""

import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.sourcepull_system import SourcepullSystem
from src.processors.footnote_extractor import extract_footnotes_from_docx


def load_citations_from_file(file_path: str) -> List[tuple]:
    """Load citations from a text file (one per line with footnote number)"""
    citations = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Format: "FN# Citation text" or just "Citation text"
                if line.startswith('FN'):
                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        fn_num = int(parts[0][2:])
                        citation = parts[1]
                        citations.append((fn_num, citation))
                else:
                    # Auto-number if no FN prefix
                    citations.append((len(citations) + 1, line))
    return citations


def load_citations_from_json(file_path: str) -> List[tuple]:
    """Load citations from a JSON file"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    citations = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                fn = item.get('footnote', len(citations) + 1)
                cite = item.get('citation', '')
                if cite:
                    citations.append((fn, cite))
            elif isinstance(item, str):
                citations.append((len(citations) + 1, item))
    elif isinstance(data, dict):
        # Assume it's a mapping of footnote numbers to citations
        for fn, cite in data.items():
            citations.append((int(fn), cite))
    
    return citations


def print_banner():
    """Print the SLRinator banner"""
    print("\n" + "="*70)
    print(" "*20 + "STANFORD LAW REVIEW")
    print(" "*15 + "SOURCEPULL AUTOMATION SYSTEM")
    print("="*70)
    print()


def print_summary(results, report):
    """Print a summary of the sourcepull results"""
    print("\n" + "="*70)
    print("SOURCEPULL SUMMARY")
    print("="*70)
    
    print(f"\nTotal Sources Processed: {report['summary']['total_sources']}")
    print(f"Successfully Retrieved: {report['summary']['successful']}")
    print(f"Failed to Retrieve: {report['summary']['failed']}")
    print(f"Success Rate: {report['summary']['success_rate']}")
    
    # Show breakdown by source type
    if report['by_source_type']:
        print("\nBreakdown by Source Type:")
        print("-" * 40)
        for source_type, stats in report['by_source_type'].items():
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"  {source_type:25} {stats['success']:3}/{stats['total']:3} ({success_rate:.0f}%)")
    
    # Show which retrieval sources worked best
    if report['retrieval_sources']:
        print("\nRetrieval Source Performance:")
        print("-" * 40)
        for source, stats in sorted(report['retrieval_sources'].items(), 
                                   key=lambda x: x[1]['successes'], reverse=True):
            if stats['attempts'] > 0:
                success_rate = (stats['successes'] / stats['attempts'] * 100)
                print(f"  {source:25} {stats['successes']:3}/{stats['attempts']:3} attempts ({success_rate:.0f}%)")
    
    # Show manual retrieval needed
    if report['manual_required']:
        print(f"\n⚠️  Manual Retrieval Required: {len(report['manual_required'])} sources")
        print("-" * 40)
        for item in report['manual_required'][:10]:  # Show first 10
            print(f"  FN{item['footnote']:3}: {item['citation'][:50]}...")
            print(f"         → {item['instructions']}")
        if len(report['manual_required']) > 10:
            print(f"  ... and {len(report['manual_required']) - 10} more")
    
    print("\n" + "="*70)


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Stanford Law Review Sourcepull System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a Word document
  python run_sourcepull.py --docx article.docx
  
  # Process specific footnotes from a Word document
  python run_sourcepull.py --docx article.docx --footnotes 1-50
  
  # Process citations from a text file
  python run_sourcepull.py --file citations.txt
  
  # Process citations from a JSON file
  python run_sourcepull.py --json citations.json
  
  # Test with sample citations
  python run_sourcepull.py --test
  
  # Use custom API keys file
  python run_sourcepull.py --docx article.docx --config my_api_keys.json
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--docx', type=str, help='Word document to process')
    input_group.add_argument('--file', type=str, help='Text file with citations (one per line)')
    input_group.add_argument('--json', type=str, help='JSON file with citations')
    input_group.add_argument('--test', action='store_true', help='Run with test citations')
    
    # Processing options
    parser.add_argument('--footnotes', type=str, help='Footnote range to process (e.g., "1-50" or "1,3,5-10")')
    parser.add_argument('--config', type=str, default='config/api_keys.json', 
                       help='Path to API keys configuration file')
    parser.add_argument('--output-dir', type=str, default='output/data/Sourcepull',
                       help='Output directory for retrieved sources')
    parser.add_argument('--report', type=str, default='sourcepull_report.json',
                       help='Output filename for report')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    print_banner()
    
    # Load citations based on input type
    citations = []
    
    if args.test:
        print("Running with test citations...")
        citations = [
            (1, "Alice Corp. v. CLS Bank Int'l, 573 U.S. 208, 216 (2014)"),
            (2, "Mayo Collaborative Servs. v. Prometheus Labs., Inc., 566 U.S. 66, 72 (2012)"),
            (3, "35 U.S.C. § 101 (2018)"),
            (4, "17 C.F.R. § 240.10b-5 (2021)"),
            (5, "Mark A. Lemley, Software Patents and the Return of Functional Claiming, 2013 Wis. L. Rev. 905"),
            (6, "Diamond v. Chakrabarty, 447 U.S. 303, 309 (1980)"),
            (7, "Apple Inc. v. Samsung Elecs. Co., 839 F.3d 1034, 1040 (Fed. Cir. 2016)"),
            (8, "H.R. Rep. No. 114-114, at 2 (2015)"),
        ]
    
    elif args.docx:
        print(f"Loading citations from Word document: {args.docx}")
        docx_path = Path(args.docx)
        if not docx_path.exists():
            print(f"Error: File not found: {args.docx}")
            return 1
        
        # Extract footnotes
        try:
            footnotes = extract_footnotes_from_docx(str(docx_path))
            citations = list(footnotes.items())
            print(f"  Found {len(citations)} footnotes")
        except Exception as e:
            print(f"Error extracting footnotes: {e}")
            return 1
        
        # Filter by footnote range if specified
        if args.footnotes:
            selected = parse_footnote_range(args.footnotes)
            citations = [(fn, text) for fn, text in citations if fn in selected]
            print(f"  Processing {len(citations)} selected footnotes")
    
    elif args.file:
        print(f"Loading citations from text file: {args.file}")
        try:
            citations = load_citations_from_file(args.file)
            print(f"  Loaded {len(citations)} citations")
        except Exception as e:
            print(f"Error loading file: {e}")
            return 1
    
    elif args.json:
        print(f"Loading citations from JSON file: {args.json}")
        try:
            citations = load_citations_from_json(args.json)
            print(f"  Loaded {len(citations)} citations")
        except Exception as e:
            print(f"Error loading JSON: {e}")
            return 1
    
    if not citations:
        print("No citations to process")
        return 1
    
    # Initialize the sourcepull system
    print(f"\nInitializing sourcepull system...")
    print(f"  Config: {args.config}")
    print(f"  Output: {args.output_dir}")
    
    try:
        system = SourcepullSystem(config_path=args.config)
    except Exception as e:
        print(f"Error initializing system: {e}")
        return 1
    
    # Process citations
    print(f"\nProcessing {len(citations)} citations...")
    print("-" * 60)
    
    results = []
    for i, (fn_num, citation_text) in enumerate(citations, 1):
        if args.verbose:
            print(f"\n[{i}/{len(citations)}] FN{fn_num}: {citation_text[:80]}...")
        else:
            print(f"  [{i}/{len(citations)}] Processing FN{fn_num}...", end="")
        
        try:
            result = system.process_citation(fn_num, citation_text)
            results.append(result)
            
            if args.verbose:
                print(f"  → Type: {result.source_type.value}")
                print(f"  → Status: {result.final_status}")
                if result.final_file_path:
                    print(f"  → File: {Path(result.final_file_path).name}")
            else:
                status_symbol = "✓" if result.final_status == "success" else "✗"
                print(f" {status_symbol}")
                
        except Exception as e:
            print(f" Error: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
    
    # Generate and save report
    print("\nGenerating report...")
    report = system.generate_report(results)
    report_path = system.save_report(report, args.report)
    print(f"  Report saved to: {report_path}")
    
    # Save detailed results
    detailed_results_path = Path(args.output_dir) / "detailed_results.json"
    with open(detailed_results_path, 'w') as f:
        json.dump([{
            'footnote_number': r.footnote_number,
            'citation_text': r.citation_text,
            'source_type': r.source_type.value,
            'final_status': r.final_status,
            'final_file_path': r.final_file_path,
            'requires_manual': r.requires_manual,
            'manual_instructions': r.manual_instructions,
            'attempts': len(r.retrieval_attempts)
        } for r in results], f, indent=2)
    print(f"  Detailed results saved to: {detailed_results_path}")
    
    # Print summary
    print_summary(results, report)
    
    # Create manual retrieval list if needed
    if report['manual_required']:
        manual_list_path = Path(args.output_dir) / "manual_retrieval_required.txt"
        with open(manual_list_path, 'w') as f:
            f.write("STANFORD LAW REVIEW - MANUAL RETRIEVAL REQUIRED\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60 + "\n\n")
            
            for item in report['manual_required']:
                f.write(f"FN{item['footnote']:03d}\n")
                f.write(f"  Citation: {item['citation']}\n")
                f.write(f"  Instructions: {item['instructions']}\n")
                f.write("-"*40 + "\n")
        
        print(f"\n📋 Manual retrieval list saved to: {manual_list_path}")
    
    print("\n✅ Sourcepull process complete!")
    return 0


def parse_footnote_range(range_str: str) -> set:
    """Parse a footnote range string like '1-50' or '1,3,5-10' into a set of numbers"""
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


if __name__ == "__main__":
    sys.exit(main())