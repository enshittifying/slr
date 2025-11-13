#!/usr/bin/env python3
"""
PDF Redboxer for Stanford Law Review
Adds red boxes around citation elements in retrieved PDFs
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("⚠️ PyMuPDF not installed. Install with: pip install PyMuPDF")


@dataclass
class RedboxElement:
    """Element to be redboxed in a PDF"""
    text: str
    page_num: int
    x0: float
    y0: float
    x1: float
    y1: float
    priority: str = 'high'  # high, medium, low
    

class PDFRedboxer:
    """Add red boxes to PDFs for Stanford Law Review editorial review"""
    
    def __init__(self):
        self.redbox_color = (1, 0, 0)  # Red in RGB
        self.redbox_width = 2.0  # Line width
        self.high_priority_width = 2.0
        self.medium_priority_width = 1.5
        self.low_priority_width = 1.0
        
    def redbox_pdf(self, input_path: str, output_path: str, 
                   search_terms: List[str], add_metadata: bool = True) -> bool:
        """
        Add red boxes to a PDF around specified search terms
        
        Args:
            input_path: Path to input PDF
            output_path: Path for output PDF with redboxes
            search_terms: List of terms to search for and redbox
            add_metadata: Whether to add a metadata page
            
        Returns:
            True if successful, False otherwise
        """
        if not PYMUPDF_AVAILABLE:
            print("PyMuPDF not available")
            return False
            
        try:
            # Open the PDF
            doc = fitz.open(input_path)
            
            # Find and redbox elements
            elements = self._find_elements(doc, search_terms)
            
            # Add red boxes
            self._add_redboxes(doc, elements)
            
            # Add metadata page if requested
            if add_metadata:
                self._add_metadata_page(doc, elements, search_terms)
                
            # Save the modified PDF
            doc.save(output_path)
            doc.close()
            
            return True
            
        except Exception as e:
            print(f"Error redboxing PDF: {e}")
            return False
            
    def _find_elements(self, doc: fitz.Document, search_terms: List[str]) -> List[RedboxElement]:
        """Find all instances of search terms in the document"""
        elements = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            for term in search_terms:
                if not term:
                    continue
                    
                # Search for the term
                text_instances = page.search_for(term)
                
                for inst in text_instances:
                    # Determine priority based on term type
                    priority = self._determine_priority(term)
                    
                    element = RedboxElement(
                        text=term,
                        page_num=page_num,
                        x0=inst.x0,
                        y0=inst.y0,
                        x1=inst.x1,
                        y1=inst.y1,
                        priority=priority
                    )
                    elements.append(element)
                    
                # Also try case-insensitive search
                if not text_instances:
                    text_instances = page.search_for(term, flags=fitz.TEXT_DEHYPHENATE)
                    for inst in text_instances:
                        element = RedboxElement(
                            text=term,
                            page_num=page_num,
                            x0=inst.x0,
                            y0=inst.y0,
                            x1=inst.x1,
                            y1=inst.y1,
                            priority='medium'
                        )
                        elements.append(element)
                        
        return elements
        
    def _determine_priority(self, term: str) -> str:
        """Determine the priority level for redboxing"""
        # High priority: case names, statute sections
        if ' v. ' in term or ' v ' in term or '§' in term:
            return 'high'
        # Medium priority: years, volumes, reporters
        elif term.isdigit() or re.match(r'^\d{4}$', term):
            return 'medium'
        # Low priority: other terms
        else:
            return 'low'
            
    def _add_redboxes(self, doc: fitz.Document, elements: List[RedboxElement]):
        """Add red boxes to the document"""
        for element in elements:
            page = doc[element.page_num]
            
            # Determine line width based on priority
            if element.priority == 'high':
                width = self.high_priority_width
            elif element.priority == 'medium':
                width = self.medium_priority_width
            else:
                width = self.low_priority_width
                
            # Create rectangle
            rect = fitz.Rect(element.x0, element.y0, element.x1, element.y1)
            
            # Expand rectangle slightly for better visibility
            rect = rect + (-1, -1, 1, 1)
            
            # Draw the red box
            page.draw_rect(rect, color=self.redbox_color, width=width)
            
    def _add_metadata_page(self, doc: fitz.Document, elements: List[RedboxElement], 
                           search_terms: List[str]):
        """Add a metadata page at the beginning of the document"""
        # Create new page at the beginning
        page = doc.new_page(pno=0, width=612, height=792)
        
        # Add title
        title = "STANFORD LAW REVIEW - REDBOXING REPORT"
        page.insert_text((72, 72), title, fontsize=16, fontname="Helvetica-Bold")
        
        # Add timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        page.insert_text((72, 100), f"Generated: {timestamp}", fontsize=10)
        
        # Add search terms
        y = 140
        page.insert_text((72, y), "Search Terms:", fontsize=12, fontname="Helvetica-Bold")
        y += 20
        
        for term in search_terms[:20]:  # Limit to first 20 terms
            if term:
                page.insert_text((90, y), f"• {term[:80]}", fontsize=10)
                y += 15
                
        # Add statistics
        y += 20
        page.insert_text((72, y), "Redboxing Statistics:", fontsize=12, fontname="Helvetica-Bold")
        y += 20
        
        high_count = sum(1 for e in elements if e.priority == 'high')
        medium_count = sum(1 for e in elements if e.priority == 'medium')
        low_count = sum(1 for e in elements if e.priority == 'low')
        
        page.insert_text((90, y), f"• High Priority (2pt): {high_count} elements", fontsize=10)
        y += 15
        page.insert_text((90, y), f"• Medium Priority (1.5pt): {medium_count} elements", fontsize=10)
        y += 15
        page.insert_text((90, y), f"• Low Priority (1pt): {low_count} elements", fontsize=10)
        y += 15
        page.insert_text((90, y), f"• Total Redboxed: {len(elements)} elements", fontsize=10)
        
        # Add instructions
        y += 30
        page.insert_text((72, y), "Editorial Instructions:", fontsize=12, fontname="Helvetica-Bold")
        y += 20
        
        instructions = [
            "1. Review all redboxed elements for accuracy",
            "2. Verify case names and citations are correct",
            "3. Check statute sections match the article",
            "4. Confirm years and page numbers",
            "5. Note any missing or incorrect citations"
        ]
        
        for instruction in instructions:
            page.insert_text((90, y), instruction, fontsize=10)
            y += 15
            
        # Add footer
        page.insert_text((72, 720), "Stanford Law Review - Editorial Use Only", 
                        fontsize=8, color=(0.5, 0.5, 0.5))
                        

class SmartRedboxer(PDFRedboxer):
    """Enhanced redboxer with intelligent citation detection"""
    
    def redbox_citation(self, input_path: str, output_path: str, 
                        citation_type: str, citation_data: Dict) -> bool:
        """
        Redbox a PDF based on citation type and data
        
        Args:
            input_path: Path to input PDF
            output_path: Path for output PDF
            citation_type: Type of citation (case, statute, article)
            citation_data: Dictionary with citation components
            
        Returns:
            True if successful
        """
        search_terms = []
        
        if citation_type == 'case':
            # Add case name components
            if 'party1' in citation_data:
                search_terms.append(citation_data['party1'])
            if 'party2' in citation_data:
                search_terms.append(citation_data['party2'])
            # Add citation components
            if 'volume' in citation_data:
                search_terms.append(str(citation_data['volume']))
            if 'reporter' in citation_data:
                search_terms.append(citation_data['reporter'])
            if 'page' in citation_data:
                search_terms.append(str(citation_data['page']))
            if 'year' in citation_data:
                search_terms.append(str(citation_data['year']))
                
        elif citation_type == 'statute':
            # Add statute components
            if 'title' in citation_data:
                search_terms.append(f"{citation_data['title']} U.S.C.")
            if 'section' in citation_data:
                search_terms.append(f"§ {citation_data['section']}")
                search_terms.append(f"Section {citation_data['section']}")
                
        elif citation_type == 'article':
            # Add article components
            if 'author' in citation_data:
                # Add last name
                author_parts = citation_data['author'].split()
                if author_parts:
                    search_terms.append(author_parts[-1])
            if 'title' in citation_data:
                # Add first few words of title
                title_words = citation_data['title'].split()[:5]
                search_terms.append(' '.join(title_words))
            if 'journal' in citation_data:
                search_terms.append(citation_data['journal'])
            if 'year' in citation_data:
                search_terms.append(str(citation_data['year']))
                
        # Remove empty strings
        search_terms = [t for t in search_terms if t]
        
        return self.redbox_pdf(input_path, output_path, search_terms)


def test_redboxer():
    """Test the redboxer with a sample PDF"""
    redboxer = SmartRedboxer()
    
    # Test data
    test_citation = {
        'party1': 'Alice Corp.',
        'party2': 'CLS Bank',
        'volume': '573',
        'reporter': 'U.S.',
        'page': '208',
        'year': '2014'
    }
    
    # Find a test PDF
    test_pdfs = list(Path("output/data/Sourcepull/Retrieved").glob("*.pdf"))
    if test_pdfs:
        input_pdf = test_pdfs[0]
        output_pdf = Path("output/data/Sourcepull/Redboxed") / f"TEST_{input_pdf.name}"
        output_pdf.parent.mkdir(parents=True, exist_ok=True)
        
        success = redboxer.redbox_citation(
            str(input_pdf),
            str(output_pdf),
            'case',
            test_citation
        )
        
        if success:
            print(f"✅ Test successful! Output: {output_pdf}")
        else:
            print("❌ Test failed")
    else:
        print("No test PDFs found")


if __name__ == "__main__":
    test_redboxer()