"""
PDF Processor Module for Stanford Law Review
Handles PDF manipulation, redboxing, and annotation
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

from citation_parser import Citation, CitationType

logger = logging.getLogger(__name__)


@dataclass
class RedboxElement:
    """Represents an element to be redboxed in a PDF"""
    text: str
    page_num: int
    x0: float
    y0: float
    x1: float
    y1: float
    element_type: str  # 'author', 'title', 'year', 'volume', 'page', 'court', 'judge'
    confidence: float = 1.0


class PDFProcessor:
    """Handles PDF processing, cleaning, and redboxing"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.remove_heinonline_covers = self.config.get('remove_heinonline_covers', True)
        self.remove_westlaw_headers = self.config.get('remove_westlaw_headers', True)
        self.ocr_threshold = self.config.get('ocr_threshold', 0.7)
        self.redbox_color = (1, 0, 0)  # Red in RGB (0-1 scale)
        self.redbox_width = 2
        
    def process_pdf(self, input_path: str, citation: Citation, output_path: str = None) -> Dict[str, Any]:
        """Main entry point for processing a PDF"""
        input_path = Path(input_path)
        if not output_path:
            output_path = input_path
        else:
            output_path = Path(output_path)
        
        result = {
            'success': False,
            'input_path': str(input_path),
            'output_path': str(output_path),
            'pages_processed': 0,
            'pages_removed': 0,
            'redboxes_added': 0,
            'ocr_performed': False,
            'errors': []
        }
        
        try:
            # Open PDF
            doc = fitz.open(str(input_path))
            
            # Clean the PDF
            if self.config.get('clean_pdf', True):
                doc = self._clean_pdf(doc, result)
            
            # Find citation elements
            elements = self._find_citation_elements(doc, citation, result)
            
            # Add redboxes
            if elements:
                self._add_redboxes(doc, elements, result)
            
            # Save the processed PDF
            doc.save(str(output_path))
            doc.close()
            
            result['success'] = True
            result['pages_processed'] = len(doc)
            
        except Exception as e:
            logger.error(f"Error processing PDF {input_path}: {e}")
            result['errors'].append(str(e))
        
        return result
    
    def _clean_pdf(self, doc: fitz.Document, result: Dict) -> fitz.Document:
        """Remove unnecessary pages and content from PDF"""
        pages_to_remove = []
        
        # Check for HeinOnline covers
        if self.remove_heinonline_covers:
            pages_to_remove.extend(self._find_heinonline_pages(doc))
        
        # Check for Westlaw headers/footers
        if self.remove_westlaw_headers:
            self._remove_westlaw_headers(doc)
        
        # Remove pages in reverse order to maintain indices
        for page_num in sorted(pages_to_remove, reverse=True):
            doc.delete_page(page_num)
            result['pages_removed'] += 1
        
        return doc
    
    def _find_heinonline_pages(self, doc: fitz.Document) -> List[int]:
        """Identify HeinOnline cover pages to remove"""
        pages_to_remove = []
        
        heinonline_patterns = [
            r'HeinOnline',
            r'Copyright.*HeinOnline',
            r'www\.heinonline\.org',
            r'Citation:.*provided by.*HeinOnline'
        ]
        
        for page_num in range(min(3, len(doc))):  # Check first 3 pages
            page = doc[page_num]
            text = page.get_text()
            
            for pattern in heinonline_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    pages_to_remove.append(page_num)
                    break
        
        # Also check last page
        if len(doc) > 3:
            last_page = doc[-1]
            text = last_page.get_text()
            for pattern in heinonline_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    pages_to_remove.append(len(doc) - 1)
                    break
        
        return pages_to_remove
    
    def _remove_westlaw_headers(self, doc: fitz.Document) -> None:
        """Remove Westlaw headers and footers from pages"""
        westlaw_patterns = [
            r'Westlaw',
            r'© \d{4} Thomson Reuters',
            r'West Reporter Image',
            r'KeyCite.*Status'
        ]
        
        for page in doc:
            # Get text blocks
            blocks = page.get_text("blocks")
            
            for block in blocks:
                x0, y0, x1, y1, text = block[:5]
                
                # Check if block is in header/footer region
                page_height = page.rect.height
                is_header = y0 < 100  # Top 100 points
                is_footer = y1 > page_height - 100  # Bottom 100 points
                
                if is_header or is_footer:
                    for pattern in westlaw_patterns:
                        if re.search(pattern, text, re.IGNORECASE):
                            # Add white rectangle to cover the text
                            rect = fitz.Rect(x0, y0, x1, y1)
                            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                            break
    
    def _find_citation_elements(self, doc: fitz.Document, citation: Citation, result: Dict) -> List[RedboxElement]:
        """Find citation elements in the PDF"""
        elements = []
        metadata = citation.metadata
        
        # Define what to search for based on citation type
        search_terms = self._get_search_terms(citation)
        
        for page_num, page in enumerate(doc):
            # Try text-based search first
            page_elements = self._search_page_text(page, page_num, search_terms)
            elements.extend(page_elements)
            
            # If no results and OCR is enabled, try OCR
            if not page_elements and self.config.get('enable_ocr', True):
                ocr_elements = self._search_page_ocr(page, page_num, search_terms, result)
                elements.extend(ocr_elements)
        
        return elements
    
    def _get_search_terms(self, citation: Citation) -> Dict[str, List[str]]:
        """Get search terms based on citation type"""
        terms = {}
        metadata = citation.metadata
        
        if citation.type == CitationType.CASE:
            if metadata.title:
                terms['title'] = [metadata.title]
                # Also search for individual party names
                if ' v. ' in metadata.title:
                    parties = metadata.title.split(' v. ')
                    terms['parties'] = parties
            if metadata.court:
                terms['court'] = [metadata.court]
            if metadata.year:
                terms['year'] = [metadata.year]
            if metadata.judge:
                terms['judge'] = [metadata.judge]
        
        elif citation.type == CitationType.ARTICLE:
            if metadata.authors:
                terms['author'] = metadata.authors
                # Also search for last names only
                terms['author_lastname'] = [author.split()[-1] for author in metadata.authors]
            if metadata.title:
                terms['title'] = [metadata.title]
                # Also search for key phrases from title
                title_words = metadata.title.split()
                if len(title_words) > 5:
                    # Search for first and last few words
                    terms['title_partial'] = [
                        ' '.join(title_words[:4]),
                        ' '.join(title_words[-4:])
                    ]
            if metadata.year:
                terms['year'] = [metadata.year]
            if metadata.reporter:
                terms['journal'] = [metadata.reporter]
        
        elif citation.type == CitationType.BOOK:
            if metadata.authors:
                terms['author'] = metadata.authors
            if metadata.title:
                terms['title'] = [metadata.title]
            if metadata.year:
                terms['year'] = [metadata.year]
            if metadata.publisher:
                terms['publisher'] = [metadata.publisher]
        
        elif citation.type in [CitationType.STATUTE, CitationType.REGULATION]:
            if metadata.title:
                terms['title'] = [metadata.title]
            if metadata.section:
                terms['section'] = [f"§ {metadata.section}", f"Section {metadata.section}"]
        
        return terms
    
    def _search_page_text(self, page: fitz.Page, page_num: int, search_terms: Dict[str, List[str]]) -> List[RedboxElement]:
        """Search for terms in page text"""
        elements = []
        
        for element_type, terms in search_terms.items():
            for term in terms:
                # Search for the term
                rects = page.search_for(term, hit_max=10)
                
                for rect in rects:
                    element = RedboxElement(
                        text=term,
                        page_num=page_num,
                        x0=rect.x0,
                        y0=rect.y0,
                        x1=rect.x1,
                        y1=rect.y1,
                        element_type=element_type,
                        confidence=1.0
                    )
                    elements.append(element)
        
        return elements
    
    def _search_page_ocr(self, page: fitz.Page, page_num: int, search_terms: Dict[str, List[str]], result: Dict) -> List[RedboxElement]:
        """Use OCR to search for terms in page"""
        elements = []
        
        try:
            # Convert page to image
            mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Convert to PIL Image
            img = Image.open(io.BytesIO(img_data))
            
            # Perform OCR with bounding boxes
            ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            
            # Search for terms in OCR results
            n_boxes = len(ocr_data['text'])
            
            for element_type, terms in search_terms.items():
                for term in terms:
                    term_lower = term.lower()
                    
                    # Search through OCR text
                    for i in range(n_boxes):
                        text = ocr_data['text'][i]
                        conf = float(ocr_data['conf'][i]) / 100.0
                        
                        if conf < self.ocr_threshold:
                            continue
                        
                        if term_lower in text.lower():
                            # Get bounding box (scaled back from 2x zoom)
                            x0 = ocr_data['left'][i] / 2
                            y0 = ocr_data['top'][i] / 2
                            x1 = x0 + ocr_data['width'][i] / 2
                            y1 = y0 + ocr_data['height'][i] / 2
                            
                            element = RedboxElement(
                                text=text,
                                page_num=page_num,
                                x0=x0,
                                y0=y0,
                                x1=x1,
                                y1=y1,
                                element_type=element_type,
                                confidence=conf
                            )
                            elements.append(element)
            
            if elements:
                result['ocr_performed'] = True
        
        except Exception as e:
            logger.error(f"OCR failed on page {page_num}: {e}")
            result['errors'].append(f"OCR error on page {page_num}: {str(e)}")
        
        return elements
    
    def _add_redboxes(self, doc: fitz.Document, elements: List[RedboxElement], result: Dict) -> None:
        """Add red boxes around found elements"""
        for element in elements:
            try:
                page = doc[element.page_num]
                
                # Create rectangle
                rect = fitz.Rect(element.x0, element.y0, element.x1, element.y1)
                
                # Add red box
                page.draw_rect(
                    rect,
                    color=self.redbox_color,
                    width=self.redbox_width
                )
                
                # Optionally add annotation
                if self.config.get('add_annotations', True):
                    point = fitz.Point(element.x1 + 5, element.y0)
                    text = f"{element.element_type}: {element.text[:30]}..."
                    page.insert_text(
                        point,
                        text,
                        fontsize=8,
                        color=(1, 0, 0)
                    )
                
                result['redboxes_added'] += 1
            
            except Exception as e:
                logger.error(f"Failed to add redbox: {e}")
                result['errors'].append(f"Redbox error: {str(e)}")
    
    def batch_process(self, pdf_citations: List[Tuple[str, Citation, str]]) -> List[Dict[str, Any]]:
        """Process multiple PDFs
        Args:
            pdf_citations: List of tuples (input_path, citation, output_path)
        """
        results = []
        
        for input_path, citation, output_path in pdf_citations:
            logger.info(f"Processing PDF: {input_path}")
            result = self.process_pdf(input_path, citation, output_path)
            results.append(result)
        
        return results
    
    def merge_pdfs(self, pdf_paths: List[str], output_path: str) -> bool:
        """Merge multiple PDFs into one"""
        try:
            result = fitz.open()
            
            for pdf_path in pdf_paths:
                pdf = fitz.open(pdf_path)
                result.insert_pdf(pdf)
                pdf.close()
            
            result.save(output_path)
            result.close()
            return True
        
        except Exception as e:
            logger.error(f"Failed to merge PDFs: {e}")
            return False
    
    def extract_text_with_positions(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract text with position information for advanced processing"""
        doc = fitz.open(pdf_path)
        text_data = []
        
        for page_num, page in enumerate(doc):
            # Get detailed text information
            blocks = page.get_text("dict")
            
            for block in blocks.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text_data.append({
                                'page': page_num,
                                'text': span.get("text", ""),
                                'bbox': span.get("bbox", []),
                                'font': span.get("font", ""),
                                'size': span.get("size", 0),
                                'flags': span.get("flags", 0)
                            })
        
        doc.close()
        return text_data
    
    def add_custom_redbox(self, pdf_path: str, page_num: int, x0: float, y0: float, 
                         x1: float, y1: float, color: Tuple[float, float, float] = None,
                         label: str = "") -> bool:
        """Add a custom redbox to a specific location"""
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num]
            
            rect = fitz.Rect(x0, y0, x1, y1)
            page.draw_rect(
                rect,
                color=color or self.redbox_color,
                width=self.redbox_width
            )
            
            if label:
                point = fitz.Point(x1 + 5, y0)
                page.insert_text(point, label, fontsize=8, color=color or self.redbox_color)
            
            doc.save(pdf_path)
            doc.close()
            return True
        
        except Exception as e:
            logger.error(f"Failed to add custom redbox: {e}")
            return False