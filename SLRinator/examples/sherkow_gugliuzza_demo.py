#!/usr/bin/env python3
"""
Demo: Perform Sourcepull and Redboxing for Sherkow & Gugliuzza Article
Simplified version that demonstrates the core functionality
"""

import sys
import os
from pathlib import Path
import json
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from stage1.citation_parser import CitationParser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Sample citations from a patent law article (Sherkow & Gugliuzza style)
SAMPLE_CITATIONS = [
    # Supreme Court Cases - Patent Eligibility
    {
        'id': '001',
        'short_name': 'Alice_Corp',
        'citation': 'Alice Corp. v. CLS Bank International, 573 U.S. 208 (2014)',
        'type': 'case',
        'quote': 'whoever invents or discovers any new and useful process'
    },
    {
        'id': '002', 
        'short_name': 'Mayo_v_Prometheus',
        'citation': 'Mayo Collaborative Services v. Prometheus Laboratories, Inc., 566 U.S. 66 (2012)',
        'type': 'case',
        'quote': 'laws of nature, natural phenomena, and abstract ideas'
    },
    {
        'id': '003',
        'short_name': 'Diamond_v_Chakrabarty',
        'citation': 'Diamond v. Chakrabarty, 447 U.S. 303 (1980)',
        'type': 'case',
        'quote': 'anything under the sun that is made by man'
    },
    
    # Patent Statutes
    {
        'id': '004',
        'short_name': 'Patent_Act_101',
        'citation': '35 U.S.C. § 101 (2018)',
        'type': 'statute',
        'quote': 'Whoever invents or discovers any new and useful process, machine, manufacture'
    },
    {
        'id': '005',
        'short_name': 'Patent_Act_103',
        'citation': '35 U.S.C. § 103 (2018)',
        'type': 'statute',
        'quote': 'obvious to a person having ordinary skill in the art'
    },
    
    # Law Review Articles
    {
        'id': '006',
        'short_name': 'Lemley_Software_Patents',
        'citation': 'Mark A. Lemley, Software Patents and the Return of Functional Claiming, 2013 Wis. L. Rev. 905 (2013)',
        'type': 'article',
        'quote': 'functional claiming'
    },
    {
        'id': '007',
        'short_name': 'Gugliuzza_Fed_Circuit',
        'citation': 'Paul R. Gugliuzza, The Federal Circuit as a Federal Court, 54 Wm. & Mary L. Rev. 1791 (2013)',
        'type': 'article',
        'quote': 'specialized jurisdiction'
    },
    
    # Federal Circuit Cases
    {
        'id': '008',
        'short_name': 'CLS_Bank',
        'citation': 'CLS Bank International v. Alice Corp., 717 F.3d 1269 (Fed. Cir. 2013) (en banc)',
        'type': 'case',
        'quote': 'inventive concept'
    },
    
    # USPTO Guidance
    {
        'id': '009',
        'short_name': 'USPTO_101_Guidance',
        'citation': '2019 Revised Patent Subject Matter Eligibility Guidance, 84 Fed. Reg. 50 (Jan. 7, 2019)',
        'type': 'regulation',
        'quote': 'practical application'
    },
    
    # Online Sources
    {
        'id': '010',
        'short_name': 'Patently_O',
        'citation': 'Dennis Crouch, Patently-O Patent Law Blog, https://patentlyo.com (last visited Dec. 1, 2023)',
        'type': 'web',
        'quote': 'patent prosecution statistics'
    }
]


def create_mock_pdf_with_redboxing(citation_data, output_dir):
    """Create a mock PDF with redboxing for demonstration"""
    try:
        import fitz  # PyMuPDF
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename
        filename = f"SP-{citation_data['id']}-{citation_data['short_name']}.pdf"
        filepath = output_dir / filename
        
        # Create PDF
        doc = fitz.open()
        page = doc.new_page(width=612, height=792)  # Letter size
        
        # Add header
        page.insert_text(
            (50, 50),
            f"Source ID: {citation_data['id']}",
            fontsize=10,
            color=(0, 0, 0)
        )
        
        # Add citation (and redbox it)
        citation_rect = fitz.Rect(50, 80, 550, 120)
        page.insert_textbox(
            citation_rect,
            citation_data['citation'],
            fontsize=12,
            color=(0, 0, 0)
        )
        # Add redbox around citation
        page.draw_rect(citation_rect, color=(1, 0, 0), width=2)
        
        # Add content based on type
        y_pos = 150
        
        if citation_data['type'] == 'case':
            # Add case header
            page.insert_text((50, y_pos), "SUPREME COURT OF THE UNITED STATES", fontsize=14, fontname="Helvetica-Bold")
            y_pos += 30
            
            # Extract case name and redbox it
            case_name = citation_data['citation'].split(',')[0]
            name_rect = fitz.Rect(50, y_pos, 400, y_pos + 25)
            page.insert_textbox(name_rect, case_name, fontsize=12)
            page.draw_rect(name_rect, color=(1, 0, 0), width=2)
            y_pos += 40
            
            # Add year and redbox it
            import re
            year_match = re.search(r'\((\d{4})\)', citation_data['citation'])
            if year_match:
                year = year_match.group(1)
                year_rect = fitz.Rect(50, y_pos, 150, y_pos + 20)
                page.insert_textbox(year_rect, f"Decided: {year}", fontsize=11)
                page.draw_rect(year_rect, color=(1, 0, 0), width=2)
                y_pos += 40
            
            # Add sample opinion text
            page.insert_text((50, y_pos), "OPINION", fontsize=12, fontname="Helvetica-Bold")
            y_pos += 25
            
            opinion_text = (
                f"This case presents important questions regarding patent eligibility. "
                f"The Court has long held that '{citation_data['quote']}' represents "
                f"a fundamental principle of patent law. The patent system aims to foster "
                f"innovation while ensuring that the basic tools of scientific and "
                f"technological work remain free for all to use."
            )
            
            text_rect = fitz.Rect(50, y_pos, 550, y_pos + 100)
            page.insert_textbox(text_rect, opinion_text, fontsize=11)
            
            # Redbox the quote if it appears
            if citation_data['quote'] in opinion_text:
                # This is simplified - in real implementation would find exact position
                quote_rect = fitz.Rect(100, y_pos + 10, 500, y_pos + 30)
                page.draw_rect(quote_rect, color=(1, 0, 0), width=1)
            
        elif citation_data['type'] == 'statute':
            # Add statute header
            page.insert_text((50, y_pos), "UNITED STATES CODE", fontsize=14, fontname="Helvetica-Bold")
            y_pos += 30
            
            # Extract title and section
            import re
            title_match = re.search(r'(\d+)\s+U\.S\.C\.\s+§\s*(\d+)', citation_data['citation'])
            if title_match:
                title = title_match.group(1)
                section = title_match.group(2)
                
                # Redbox title
                title_rect = fitz.Rect(50, y_pos, 200, y_pos + 20)
                page.insert_textbox(title_rect, f"Title {title}", fontsize=12)
                page.draw_rect(title_rect, color=(1, 0, 0), width=2)
                y_pos += 30
                
                # Redbox section
                section_rect = fitz.Rect(50, y_pos, 200, y_pos + 20)
                page.insert_textbox(section_rect, f"Section {section}", fontsize=12)
                page.draw_rect(section_rect, color=(1, 0, 0), width=2)
                y_pos += 40
            
            # Add statute text
            statute_text = (
                f"§ {citation_data['id']}. Inventions patentable\n\n"
                f"{citation_data['quote']} shall be patentable subject to the "
                f"conditions and requirements of this title."
            )
            
            text_rect = fitz.Rect(50, y_pos, 550, y_pos + 100)
            page.insert_textbox(text_rect, statute_text, fontsize=11)
            
        elif citation_data['type'] == 'article':
            # Add article header
            page.insert_text((50, y_pos), "LAW REVIEW ARTICLE", fontsize=14, fontname="Helvetica-Bold")
            y_pos += 30
            
            # Extract author and redbox
            author = citation_data['citation'].split(',')[0]
            author_rect = fitz.Rect(50, y_pos, 300, y_pos + 20)
            page.insert_textbox(author_rect, f"Author: {author}", fontsize=11)
            page.draw_rect(author_rect, color=(1, 0, 0), width=2)
            y_pos += 30
            
            # Extract title (simplified)
            parts = citation_data['citation'].split(',')
            if len(parts) > 1:
                title = parts[1].strip()
                title_rect = fitz.Rect(50, y_pos, 550, y_pos + 40)
                page.insert_textbox(title_rect, f"Title: {title}", fontsize=11)
                page.draw_rect(title_rect, color=(1, 0, 0), width=2)
                y_pos += 50
            
            # Add abstract
            abstract_text = (
                f"Abstract: This article examines the concept of '{citation_data['quote']}' "
                f"in modern patent law. We argue that recent developments in technology "
                f"require a fundamental rethinking of traditional patent doctrines."
            )
            
            text_rect = fitz.Rect(50, y_pos, 550, y_pos + 80)
            page.insert_textbox(text_rect, abstract_text, fontsize=11)
        
        # Add footer with redbox legend
        page.insert_text((50, 720), "Red boxes indicate citation elements for verification", 
                        fontsize=9, color=(0.5, 0.5, 0.5))
        
        # Save PDF
        doc.save(str(filepath))
        doc.close()
        
        return str(filepath)
        
    except ImportError:
        logger.warning("PyMuPDF not installed - creating text file instead")
        
        # Fallback: create text file
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"SP-{citation_data['id']}-{citation_data['short_name']}.txt"
        filepath = output_dir / filename
        
        content = f"""Source ID: {citation_data['id']}
Short Name: {citation_data['short_name']}
Citation: {citation_data['citation']}
Type: {citation_data['type']}

[REDBOX] Citation: {citation_data['citation']}

Content:
This document would contain the full text of the source.
Key quote to verify: "{citation_data['quote']}"

[REDBOX elements would be highlighted in the actual PDF]
- Case/Article name
- Year
- Court/Journal
- Key quotes
"""
        
        filepath.write_text(content)
        return str(filepath)


def perform_demo_sourcepull():
    """Perform demonstration sourcepull with redboxing"""
    
    print("\n" + "="*80)
    print("SHERKOW & GUGLIUZZA SOURCEPULL AND REDBOXING DEMONSTRATION")
    print("="*80)
    print("\nArticle: 'The History and Future of Patent Eligibility'")
    print("Authors: Jacob S. Sherkow & Paul R. Gugliuzza")
    print("="*80)
    
    # Initialize citation parser
    parser = CitationParser()
    
    # Output directory
    output_dir = Path("output/data/Sourcepull")
    
    print(f"\n📚 Processing {len(SAMPLE_CITATIONS)} citations...")
    print("-" * 60)
    
    successful = []
    failed = []
    
    for i, cite_data in enumerate(SAMPLE_CITATIONS, 1):
        print(f"\n[{i}/{len(SAMPLE_CITATIONS)}] {cite_data['short_name']}")
        print(f"  📖 Citation: {cite_data['citation'][:80]}...")
        
        try:
            # Parse citation
            citation = parser.parse_citation(
                cite_data['citation'],
                cite_data['id'],
                cite_data['short_name']
            )
            
            print(f"  ✅ Parsed as: {citation.type.value}")
            
            # Validate parsed type matches expected
            if citation.type.value != cite_data['type']:
                print(f"  ⚠️  Type mismatch: expected {cite_data['type']}, got {citation.type.value}")
            
            # Display parsed metadata
            if citation.metadata.authors:
                print(f"  👤 Authors: {', '.join(citation.metadata.authors)}")
            if citation.metadata.title:
                print(f"  📑 Title: {citation.metadata.title[:50]}...")
            if citation.metadata.year:
                print(f"  📅 Year: {citation.metadata.year}")
            if citation.metadata.reporter:
                print(f"  📚 Reporter: {citation.metadata.reporter}")
            
            # Create mock PDF with redboxing
            print(f"  🔴 Creating PDF with redboxing...")
            filepath = create_mock_pdf_with_redboxing(cite_data, output_dir)
            
            print(f"  ✅ Created: {Path(filepath).name}")
            
            # Track quote for verification
            print(f"  🔍 Quote to verify: \"{cite_data['quote'][:50]}...\"")
            
            successful.append({
                'id': cite_data['id'],
                'short_name': cite_data['short_name'],
                'type': citation.type.value,
                'file': filepath
            })
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed.append(cite_data['id'])
    
    # Summary
    print("\n" + "="*80)
    print("SOURCEPULL SUMMARY")
    print("="*80)
    
    print(f"\n📊 Results:")
    print(f"  ✅ Successful: {len(successful)}/{len(SAMPLE_CITATIONS)}")
    print(f"  ❌ Failed: {len(failed)}/{len(SAMPLE_CITATIONS)}")
    
    if successful:
        print(f"\n📁 Files created in: {output_dir}/")
        for item in successful:
            print(f"  - {Path(item['file']).name} ({item['type']})")
    
    # Create summary report
    report_path = Path("data/sherkow_gugliuzza_report.json")
    report = {
        'timestamp': datetime.now().isoformat(),
        'article': 'The History and Future of Patent Eligibility',
        'authors': 'Jacob S. Sherkow & Paul R. Gugliuzza',
        'total_citations': len(SAMPLE_CITATIONS),
        'successful': len(successful),
        'failed': len(failed),
        'citations_processed': successful,
        'citation_types': {
            'case': len([s for s in successful if s['type'] == 'case']),
            'statute': len([s for s in successful if s['type'] == 'statute']),
            'article': len([s for s in successful if s['type'] == 'article']),
            'regulation': len([s for s in successful if s['type'] == 'regulation']),
            'web': len([s for s in successful if s['type'] == 'web'])
        }
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Report saved to: {report_path}")
    
    print("\n✨ Demonstration Complete!")
    print("\nKey Features Demonstrated:")
    print("  ✅ Citation parsing (cases, statutes, articles, web sources)")
    print("  ✅ Metadata extraction (authors, titles, years, courts)")
    print("  ✅ PDF creation with content")
    print("  ✅ Redboxing of citation elements")
    print("  ✅ Quote identification for verification")
    
    return successful


def main():
    """Main execution"""
    print("\n🚀 SLRinator - Sherkow & Gugliuzza Patent Law Article")
    print("    Sourcepull and Redboxing Demonstration")
    
    results = perform_demo_sourcepull()
    
    print("\n" + "="*80)
    print("Next steps for a real implementation:")
    print("1. Add API keys for real source retrieval (CourtListener, CrossRef, etc.)")
    print("2. Connect to actual article Word document for footnote extraction")
    print("3. Implement quote verification against retrieved sources")
    print("4. Run Bluebook compliance checking")
    print("5. Generate final report for editors")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())