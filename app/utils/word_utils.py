"""
Word document utilities for footnote extraction and manipulation
"""
import re
import json
import logging
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class Footnote:
    """Represents a footnote with its citations"""
    number: int
    text: str
    citations: List[Dict] = None

    def __post_init__(self):
        if self.citations is None:
            self.citations = []


class FootnoteExtractor:
    """Extract footnotes from Word documents"""

    @staticmethod
    def extract_from_docx(docx_path: str, range_filter: Tuple[int, int] = None) -> List[Footnote]:
        """
        Extract footnotes from a Word document

        Args:
            docx_path: Path to .docx file
            range_filter: Optional tuple (start, end) to filter footnote numbers

        Returns:
            List of Footnote objects
        """
        try:
            logger.info(f"Extracting footnotes from: {docx_path}")

            if not Path(docx_path).exists():
                logger.error(f"Document not found: {docx_path}")
                raise FileNotFoundError(f"Document not found: {docx_path}")

            # First try XML extraction (most reliable)
            footnote_texts = FootnoteExtractor._extract_footnotes_from_xml(docx_path)

            # If no XML footnotes, try paragraph extraction
            if not footnote_texts:
                logger.debug("No XML footnotes found, trying paragraph extraction")
                footnote_texts = FootnoteExtractor._extract_from_paragraphs(docx_path)

            # Process footnotes
            footnotes = []
            for i, text in enumerate(footnote_texts, 1):
                if text:
                    # Apply range filter if specified
                    if range_filter and (i < range_filter[0] or i > range_filter[1]):
                        continue

                    footnote = Footnote(
                        number=i,
                        text=text,
                        citations=FootnoteExtractor.extract_citations(text)
                    )
                    footnotes.append(footnote)

            logger.info(f"Extracted {len(footnotes)} footnotes from {docx_path}")
            return footnotes

        except Exception as e:
            logger.error(f"Error extracting footnotes: {e}", exc_info=True)
            raise

    @staticmethod
    def _extract_footnotes_from_xml(docx_path: str) -> List[str]:
        """
        Extract footnotes directly from Word XML

        Args:
            docx_path: Path to .docx file

        Returns:
            List of footnote text strings
        """
        try:
            footnotes = []

            with zipfile.ZipFile(docx_path, 'r') as docx:
                # Check if footnotes.xml exists
                if 'word/footnotes.xml' not in docx.namelist():
                    logger.debug("No footnotes.xml found in document")
                    return []

                with docx.open('word/footnotes.xml') as f:
                    tree = ET.parse(f)
                    root = tree.getroot()

                    # Define namespaces
                    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

                    # Find all footnotes
                    for footnote in root.findall('.//w:footnote', ns):
                        # Skip separator and continuation footnotes
                        fn_type = footnote.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type')
                        if fn_type in ['separator', 'continuationSeparator']:
                            continue

                        # Extract text from all paragraphs in footnote
                        text_parts = []
                        for para in footnote.findall('.//w:p', ns):
                            for text_elem in para.findall('.//w:t', ns):
                                if text_elem.text:
                                    text_parts.append(text_elem.text)

                        if text_parts:
                            footnotes.append(' '.join(text_parts))

            logger.debug(f"Extracted {len(footnotes)} footnotes from XML")
            return footnotes

        except zipfile.BadZipFile:
            logger.error(f"Invalid or corrupted Word document: {docx_path}")
            raise
        except ET.ParseError as e:
            logger.error(f"Error parsing footnotes XML: {e}")
            return []
        except Exception as e:
            logger.error(f"Could not extract from XML: {e}", exc_info=True)
            return []

    @staticmethod
    def _extract_from_paragraphs(docx_path: str) -> List[str]:
        """
        Fallback: extract footnotes from document paragraphs

        Args:
            docx_path: Path to .docx file

        Returns:
            List of footnote text strings
        """
        try:
            from docx import Document

            doc = Document(docx_path)
            footnotes = []
            current_footnote = None

            for para in doc.paragraphs:
                text = para.text.strip()

                # Check if this looks like a footnote start (e.g., "1. ")
                if re.match(r'^\d+\.\s+', text):
                    if current_footnote:
                        footnotes.append(current_footnote)

                    match = re.match(r'^(\d+)\.\s+(.+)', text)
                    if match:
                        current_footnote = match.group(2)
                elif current_footnote and text:
                    # Continue current footnote
                    current_footnote += ' ' + text

            # Append last footnote
            if current_footnote:
                footnotes.append(current_footnote)

            logger.debug(f"Extracted {len(footnotes)} footnotes from paragraphs")
            return footnotes

        except ImportError:
            logger.error("python-docx not installed - cannot extract from paragraphs")
            raise
        except Exception as e:
            logger.error(f"Error extracting from paragraphs: {e}", exc_info=True)
            return []

    @staticmethod
    def extract_citations(text: str) -> List[Dict]:
        """
        Extract citations from footnote text

        Args:
            text: Footnote text

        Returns:
            List of citation dicts
        """
        citations = []

        try:
            # Case citations (v. or vs.)
            case_pattern = re.compile(
                r"([A-Z][A-Za-z\s,.'&-]+?)\s+v[s]?\.\s+([A-Z][A-Za-z\s,.'&-]+?),\s*"
                r"(\d+)\s+([A-Z][A-Za-z.\s]+?)\s+(\d+)(?:,\s+(\d+[-–]\d+|\d+))?"
                r"(?:\s*\(([^)]+)\))?"
            )

            for match in case_pattern.finditer(text):
                citations.append({
                    'type': 'case',
                    'party1': match.group(1).strip(),
                    'party2': match.group(2).strip(),
                    'volume': match.group(3),
                    'reporter': match.group(4).strip(),
                    'page': match.group(5),
                    'pincite': match.group(6) if match.group(6) else None,
                    'parenthetical': match.group(7) if match.group(7) else None,
                    'full': match.group(0)
                })

            # Statutes (e.g., 35 U.S.C. § 101)
            statute_pattern = re.compile(
                r'(\d+)\s+U\.S\.C\.\s+§+\s*(\d+[a-z]?(?:-\d+[a-z]?)?)'
            )

            for match in statute_pattern.finditer(text):
                citations.append({
                    'type': 'statute',
                    'title': match.group(1),
                    'section': match.group(2),
                    'full': match.group(0)
                })

            # Law review articles
            article_pattern = re.compile(
                r'([A-Z][^,]+?),\s+([^,]+?),\s+'
                r'(\d+)\s+([A-Z][A-Za-z.\s]+?)\s+(\d+)(?:,\s+(\d+[-–]\d+|\d+))?'
                r'\s*\((\d{4})\)'
            )

            for match in article_pattern.finditer(text):
                citations.append({
                    'type': 'article',
                    'author': match.group(1).strip(),
                    'title': match.group(2).strip(),
                    'volume': match.group(3),
                    'journal': match.group(4).strip(),
                    'page': match.group(5),
                    'pincite': match.group(6) if match.group(6) else None,
                    'year': match.group(7),
                    'full': match.group(0)
                })

            # Books
            book_pattern = re.compile(
                r'([A-Z][^,]+?),\s+([A-Z][^(]+?)\s*\((\d{4})\)'
            )

            for match in book_pattern.finditer(text):
                # Make sure this isn't already captured as an article
                if not any(c['full'] == match.group(0) for c in citations if c['type'] == 'article'):
                    citations.append({
                        'type': 'book',
                        'author': match.group(1).strip(),
                        'title': match.group(2).strip(),
                        'year': match.group(3),
                        'full': match.group(0)
                    })

            logger.debug(f"Extracted {len(citations)} citations from text")
            return citations

        except Exception as e:
            logger.error(f"Error extracting citations: {e}", exc_info=True)
            return []


def extract_footnotes_from_docx(docx_path: str, range_filter: Tuple[int, int] = None) -> Dict[int, str]:
    """
    Convenience function to extract footnotes from a Word document

    Args:
        docx_path: Path to .docx file
        range_filter: Optional tuple (start, end) to filter footnote numbers

    Returns:
        Dictionary mapping footnote numbers to text
    """
    extractor = FootnoteExtractor()
    footnotes = extractor.extract_from_docx(docx_path, range_filter)
    return {fn.number: fn.text for fn in footnotes}


def save_footnotes_to_json(footnotes: List[Footnote], output_path: str):
    """
    Save footnotes to JSON file

    Args:
        footnotes: List of Footnote objects
        output_path: Path to output JSON file
    """
    try:
        data = {
            'footnotes_count': len(footnotes),
            'citations_count': sum(len(f.citations) for f in footnotes),
            'footnotes': [asdict(f) for f in footnotes]
        }

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(footnotes)} footnotes to {output_path}")

    except Exception as e:
        logger.error(f"Error saving footnotes to JSON: {e}", exc_info=True)
        raise
