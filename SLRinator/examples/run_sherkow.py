#!/usr/bin/env python3
"""
Perform Sourcepull and Redboxing for Sherkow & Gugliuzza Article
This demonstrates the SLRinator system with real patent law citations
"""

import sys
import os
from pathlib import Path
import pandas as pd
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from stage1.citation_parser import CitationParser
from stage1.source_retriever import SourceRetriever
from stage1.pdf_processor import PDFProcessor
from stage1.spreadsheet_manager import SpreadsheetManager
from utils import PerformanceMonitor, ErrorHandler, CacheManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sherkow_gugliuzza_master_sheet():
    """Create Master Sheet with typical patent law citations"""
    
    # Typical citations from a patent law article
    sourcepull_data = {
        'Source ID': [f'{i:03d}' for i in range(1, 26)],
        'Short Name': [
            'Alice_Corp',
            'Mayo_v_Prometheus',
            'Diamond_v_Chakrabarty',
            'KSR_v_Teleflex',
            'eBay_v_MercExchange',
            'USPTO_101_Guidance',
            'Lemley_Software_Patents',
            'Fed_Cir_Statistics',
            'Patent_Act_101',
            'Patent_Act_102',
            'Patent_Act_103',
            'Patent_Act_112',
            'TRIPS_Agreement',
            'Bilski_v_Kappos',
            'Myriad_Genetics',
            'CLS_Bank',
            'Akamai_v_Limelight',
            'Nautilus_v_Biosig',
            'TC_Heartland',
            'Oil_States',
            'PTAB_Statistics',
            'Crouch_Patent_Blog',
            'Nature_Biotech',
            'Science_CRISPR',
            'Harvard_LR_Note'
        ],
        'Full Citation': [
            # Supreme Court Cases
            'Alice Corp. v. CLS Bank International, 573 U.S. 208 (2014)',
            'Mayo Collaborative Services v. Prometheus Laboratories, Inc., 566 U.S. 66 (2012)',
            'Diamond v. Chakrabarty, 447 U.S. 303 (1980)',
            'KSR International Co. v. Teleflex Inc., 550 U.S. 398 (2007)',
            'eBay Inc. v. MercExchange, L.L.C., 547 U.S. 388 (2006)',
            
            # Administrative Materials
            '2019 Revised Patent Subject Matter Eligibility Guidance, 84 Fed. Reg. 50 (Jan. 7, 2019)',
            
            # Law Review Articles
            'Mark A. Lemley, Software Patents and the Return of Functional Claiming, 2013 Wis. L. Rev. 905 (2013)',
            'Paul R. Gugliuzza, The Federal Circuit as a Federal Court, 54 Wm. & Mary L. Rev. 1791 (2013)',
            
            # Statutes
            '35 U.S.C. § 101 (2018)',
            '35 U.S.C. § 102 (2018)',
            '35 U.S.C. § 103 (2018)',
            '35 U.S.C. § 112 (2018)',
            
            # Treaties
            'Agreement on Trade-Related Aspects of Intellectual Property Rights, Apr. 15, 1994, 1869 U.N.T.S. 299',
            
            # Federal Circuit Cases
            'Bilski v. Kappos, 561 U.S. 593 (2010)',
            'Association for Molecular Pathology v. Myriad Genetics, Inc., 569 U.S. 576 (2013)',
            'CLS Bank International v. Alice Corp., 717 F.3d 1269 (Fed. Cir. 2013) (en banc)',
            'Akamai Technologies, Inc. v. Limelight Networks, Inc., 797 F.3d 1020 (Fed. Cir. 2015) (en banc)',
            'Nautilus, Inc. v. Biosig Instruments, Inc., 572 U.S. 898 (2014)',
            'TC Heartland LLC v. Kraft Foods Group Brands LLC, 137 S. Ct. 1514 (2017)',
            'Oil States Energy Services, LLC v. Greene\'s Energy Group, LLC, 138 S. Ct. 1365 (2018)',
            
            # Reports and Statistics
            'USPTO, Patent Trial and Appeal Board Statistics (2023)',
            
            # Blogs and Online Sources
            'Dennis Crouch, Patently-O Patent Law Blog, https://patentlyo.com (last visited Dec. 1, 2023)',
            
            # Scientific Journals
            'Jennifer Doudna & Emmanuelle Charpentier, The New Frontier of Genome Engineering with CRISPR-Cas9, 346 Science 1258096 (2014)',
            'George Church et al., CRISPR Gene Editing in Human Embryos, 36 Nature Biotechnology 5 (2018)',
            
            # Student Notes
            'Student Note, The Future of Patent Eligibility, 137 Harv. L. Rev. 2234 (2024)'
        ],
        'Completed?': [''] * 25,
        'Location': [''] * 25,
        'File Name': [''] * 25,
        'Problems/Comments': [''] * 25,
        'Source Type': [
            'case', 'case', 'case', 'case', 'case',
            'regulation', 'article', 'article',
            'statute', 'statute', 'statute', 'statute',
            'treaty', 'case', 'case', 'case', 'case', 'case', 'case', 'case',
            'report', 'web', 'article', 'article', 'article'
        ]
    }
    
    # Create Excel file
    excel_path = Path("data/Sherkow_Gugliuzza_Master_Sheet.xlsx")
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # Sourcepull sheet
        df_sourcepull = pd.DataFrame(sourcepull_data)
        df_sourcepull.to_excel(writer, sheet_name='Sourcepull', index=False)
        
        # CC Round 1 sheet (sample)
        cc_data = {
            'Footnote #': [1, 1, 2, 3, 3, 4, 5, 5],
            'Cite Order': [1, 2, 1, 1, 2, 1, 1, 2],
            'Source ID': ['001', '002', '003', '004', '005', '009', '001', '007'],
            'Quote': [
                '"whoever invents or discovers any new and useful process"',
                '"laws of nature, natural phenomena, and abstract ideas"',
                '"anything under the sun that is made by man"',
                '"obvious to try"',
                '"automatic injunction"',
                '"[a] person shall be entitled to a patent unless"',
                '"without significantly more"',
                '"functional claiming"'
            ],
            'Supported?': [''] * 8,
            'Issues': [''] * 8,
            'Notes': [''] * 8,
            'Page Found': [''] * 8
        }
        df_cc = pd.DataFrame(cc_data)
        df_cc.to_excel(writer, sheet_name='CC_Round1', index=False)
    
    logger.info(f"✅ Created Master Sheet: {excel_path}")
    return str(excel_path)


def perform_sourcepull_with_redboxing():
    """Perform the actual sourcepull and redboxing process"""
    
    print("\n" + "="*80)
    print("SHERKOW & GUGLIUZZA SOURCEPULL AND REDBOXING")
    print("="*80)
    
    # Initialize components
    config = {
        'paths': {
            'master_sheet': './data/Sherkow_Gugliuzza_Master_Sheet.xlsx',
            'sourcepull_folder': './output/data/Sourcepull/',
            'cache_dir': './cache/',
            'output_dir': './output/data/Sourcepull/'
        },
        'apis': {
            'courtlistener': '',  # Would need real API key
            'crossref': 'slr@stanford.edu',
            'govinfo': '',  # Would need real API key
        },
        'preferences': {
            'remove_heinonline_covers': True,
            'remove_westlaw_headers': True,
            'enable_ocr': True,
            'clean_pdf': True,
            'add_annotations': True
        }
    }
    
    # Initialize modules
    parser = CitationParser()
    retriever = SourceRetriever(config)
    pdf_processor = PDFProcessor(config)
    spreadsheet_manager = SpreadsheetManager(config)
    monitor = PerformanceMonitor()
    error_handler = ErrorHandler()
    cache = CacheManager(cache_dir=config['paths']['cache_dir'])
    
    print("\n📚 Loading citations from Master Sheet...")
    citations_data = spreadsheet_manager.load_sourcepull_citations()
    
    if not citations_data:
        print("❌ No citations found in Master Sheet")
        return
    
    print(f"Found {len(citations_data)} citations to process\n")
    
    # Parse and process each citation
    results = []
    successful_retrievals = []
    
    for i, (raw_text, source_id, short_name) in enumerate(citations_data, 1):
        print(f"\n[{i}/{len(citations_data)}] Processing: {short_name}")
        print(f"  Citation: {raw_text[:100]}...")
        
        op_id = monitor.start_operation(f"process_{source_id}")
        
        try:
            # Parse citation
            citation = parser.parse_citation(raw_text, source_id, short_name)
            print(f"  ✅ Parsed as: {citation.type.value}")
            
            # Check cache first
            cache_key = f"source_{source_id}"
            cached_result = cache.get(cache_key)
            
            if cached_result:
                print(f"  📦 Found in cache")
                retrieval_result = cached_result
            else:
                # Retrieve source (simulate for demo)
                print(f"  🔍 Attempting retrieval...")
                retrieval_result = retriever.retrieve(citation)
                
                # Cache the result
                if retrieval_result.status.value in ['success', 'cached']:
                    cache.set(cache_key, retrieval_result)
            
            print(f"  Status: {retrieval_result.status.value}")
            
            if retrieval_result.status.value in ['success', 'cached']:
                successful_retrievals.append((citation, retrieval_result))
                
                # For demo, create a mock PDF file
                if not retrieval_result.file_path:
                    mock_pdf_path = Path(config['paths']['sourcepull_folder']) / f"SP-{source_id}-{short_name}.pdf"
                    mock_pdf_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Create a simple mock PDF using PyMuPDF
                    try:
                        import fitz
                        doc = fitz.open()
                        page = doc.new_page()
                        
                        # Add mock content based on citation type
                        text = f"Mock PDF for: {citation.raw_text}\n\n"
                        
                        if citation.type.value == 'case':
                            text += f"UNITED STATES SUPREME COURT\n\n"
                            text += f"{citation.metadata.title}\n\n"
                            text += f"No. XX-XXXX\n\n"
                            text += f"Decided {citation.metadata.year}\n\n"
                            text += f"JUSTICE EXAMPLE delivered the opinion of the Court.\n\n"
                            text += f"This case presents the question of patent eligibility...\n"
                            text += f'"whoever invents or discovers any new and useful process"\n'
                            text += f"The laws of nature, natural phenomena, and abstract ideas are not patentable.\n"
                        elif citation.type.value == 'statute':
                            text += f"UNITED STATES CODE\n\n"
                            text += f"Title {citation.metadata.title}\n"
                            text += f"Section {citation.metadata.section}\n\n"
                            text += f"[a] person shall be entitled to a patent unless...\n"
                        elif citation.type.value == 'article':
                            text += f"LAW REVIEW ARTICLE\n\n"
                            text += f"Authors: {', '.join(citation.metadata.authors)}\n"
                            text += f"Title: {citation.metadata.title}\n"
                            text += f"Journal: {citation.metadata.reporter}\n"
                            text += f"Year: {citation.metadata.year}\n\n"
                            text += f"Abstract: This article examines functional claiming in software patents...\n"
                        
                        # Insert text
                        page.insert_text((50, 50), text, fontsize=11)
                        
                        # Add redboxing for key elements
                        if citation.type.value == 'case':
                            # Redbox the case name
                            rect = fitz.Rect(50, 80, 300, 100)
                            page.draw_rect(rect, color=(1, 0, 0), width=2)
                            
                            # Redbox the year
                            rect = fitz.Rect(100, 140, 150, 155)
                            page.draw_rect(rect, color=(1, 0, 0), width=2)
                        
                        doc.save(str(mock_pdf_path))
                        doc.close()
                        
                        retrieval_result.file_path = str(mock_pdf_path)
                        print(f"  📄 Created mock PDF: {mock_pdf_path.name}")
                        
                        # Process PDF for redboxing
                        print(f"  🔴 Adding redboxes...")
                        pdf_result = pdf_processor.process_pdf(
                            str(mock_pdf_path),
                            citation,
                            str(mock_pdf_path)
                        )
                        
                        if pdf_result['success']:
                            print(f"  ✅ Added {pdf_result['redboxes_added']} redboxes")
                        
                    except ImportError:
                        print(f"  ⚠️  PyMuPDF not available for demo PDF creation")
                
            else:
                print(f"  ⚠️  {retrieval_result.message}")
            
            results.append((citation, retrieval_result))
            monitor.end_operation(op_id, success=True)
            
        except Exception as e:
            error_handler.handle_error(e, f"process_{source_id}")
            monitor.end_operation(op_id, success=False, error=str(e))
            print(f"  ❌ Error: {e}")
    
    # Update spreadsheet
    print("\n📊 Updating Master Sheet...")
    success = spreadsheet_manager.update_sourcepull_results(results)
    if success:
        print("✅ Master Sheet updated successfully")
    
    # Generate statistics
    stats = monitor.get_statistics()
    print("\n" + "="*80)
    print("SOURCEPULL COMPLETE")
    print("="*80)
    print(f"\n📈 Statistics:")
    print(f"  Total Citations: {len(citations_data)}")
    print(f"  Successfully Retrieved: {len(successful_retrievals)}")
    print(f"  Failed/Manual Required: {len(citations_data) - len(successful_retrievals)}")
    print(f"  Average Processing Time: {stats['average_duration']:.2f}s")
    print(f"  Total Time: {stats['uptime']:.1f}s")
    
    # List successful files
    if successful_retrievals:
        print(f"\n✅ Successfully processed files:")
        for citation, result in successful_retrievals[:10]:  # Show first 10
            if result.file_path:
                print(f"  - {Path(result.file_path).name}")
        if len(successful_retrievals) > 10:
            print(f"  ... and {len(successful_retrievals) - 10} more")
    
    # Generate report
    report_path = Path("data/sourcepull_report.json")
    monitor.generate_report(str(report_path))
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    return results


def main():
    """Main execution"""
    print("\n🚀 SLRinator - Sherkow & Gugliuzza Sourcepull Demo")
    print("="*80)
    
    # Step 1: Create Master Sheet
    print("\n📝 Step 1: Creating Master Sheet with patent law citations...")
    master_sheet_path = create_sherkow_gugliuzza_master_sheet()
    print(f"   Created: {master_sheet_path}")
    
    # Step 2: Perform Sourcepull and Redboxing
    print("\n🔄 Step 2: Performing Sourcepull and Redboxing...")
    results = perform_sourcepull_with_redboxing()
    
    print("\n✨ Process Complete!")
    print("\nNext steps:")
    print("1. Check output/data/Sourcepull/ for retrieved PDFs with redboxing")
    print("2. Review the updated Master Sheet for completion status")
    print("3. Check data/sourcepull_report.json for detailed metrics")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())