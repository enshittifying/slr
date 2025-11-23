"""
Citation extractor module for R1 Machine.

This module extracts citations from Word document footnotes, reusing
the R2 pipeline's proven footnote extraction approach. It preserves
formatting information and parses multi-citation footnotes.
"""

import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from docx import Document
from lxml import etree


logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """
    Represents a single citation with all metadata.

    Attributes:
        footnote_num: The footnote number in the document
        citation_num: The citation number within the footnote (1-indexed)
        full_text: The complete citation text
        type: Detected citation type (case, statute, book, etc.)
        components: Parsed components of the citation
        formatting: Formatting information (italic ranges, bold, etc.)
        raw_footnote: The original footnote text
    """

    footnote_num: int
    citation_num: int
    full_text: str
    type: str = "unknown"
    components: Dict[str, str] = field(default_factory=dict)
    formatting: Dict[str, List[Tuple[int, int]]] = field(default_factory=dict)
    raw_footnote: str = ""

    def __repr__(self) -> str:
        return f"Citation(FN{self.footnote_num}-{self.citation_num}: {self.full_text[:50]}...)"


class CitationExtractor:
    """
    Extracts citations from Word document footnotes.

    This class reuses the R2 pipeline's footnote extraction logic,
    which handles XML parsing, formatting preservation, and multi-citation
    footnote splitting.
    """

    def __init__(self, word_doc_path: Path):
        """
        Initialize the citation extractor.

        Args:
            word_doc_path: Path to Word document (.docx)

        Raises:
            FileNotFoundError: If document doesn't exist
            ValueError: If document is not a valid .docx file
        """
        self.word_doc_path = Path(word_doc_path)

        if not self.word_doc_path.exists():
            raise FileNotFoundError(f"Word document not found: {word_doc_path}")

        if not self.word_doc_path.suffix == ".docx":
            raise ValueError(f"Document must be .docx format: {word_doc_path}")

        self.doc = None
        self.footnotes_part = None

    def extract_citations(
        self,
        target_footnotes: Optional[List[int]] = None
    ) -> List[Citation]:
        """
        Extract all citations from the Word document.

        Args:
            target_footnotes: Optional list of specific footnote numbers to extract.
                            If None, extracts all footnotes.

        Returns:
            List of Citation objects

        Example:
            >>> extractor = CitationExtractor(Path("/path/to/doc.docx"))
            >>> citations = extractor.extract_citations(target_footnotes=[1, 2, 3])
            >>> print(f"Extracted {len(citations)} citations")
        """
        logger.info(f"Extracting citations from {self.word_doc_path}")

        # Load document
        self.doc = Document(self.word_doc_path)

        # Extract footnotes
        footnotes = self._extract_footnotes(target_footnotes)

        # Parse citations from footnotes
        all_citations = []
        for footnote_num, footnote_text in footnotes:
            citations = self._parse_footnote(footnote_num, footnote_text)
            all_citations.extend(citations)

        logger.info(f"Extracted {len(all_citations)} citations from {len(footnotes)} footnotes")

        return all_citations

    def _extract_footnotes(
        self,
        target_footnotes: Optional[List[int]] = None
    ) -> List[Tuple[int, str]]:
        """
        Extract footnotes from Word document.

        This method reuses the R2 pipeline's approach of parsing the
        footnotes.xml part directly to preserve formatting.

        Args:
            target_footnotes: Optional list of specific footnote numbers

        Returns:
            List of (footnote_number, footnote_text) tuples

        Raises:
            ValueError: If no footnotes found in document
        """
        footnotes = []

        try:
            # Get the footnotes part through relationships
            doc_part = self.doc.part
            footnotes_part = None

            for rel in doc_part.rels.values():
                if "footnotes" in rel.target_ref:
                    footnotes_part = rel.target_part
                    break

            if not footnotes_part:
                raise ValueError("No footnotes part found in document")

            # Parse footnotes XML
            footnotes_xml = footnotes_part.blob
            root = etree.fromstring(footnotes_xml)

            # Define namespace
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

            # Find all footnote elements
            for footnote in root.findall('.//w:footnote', ns):
                fn_id = footnote.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')

                if fn_id is None:
                    continue

                # Word XML IDs are off-by-one from displayed footnote numbers
                # Displayed footnote number = XML ID - 1
                footnote_num = int(fn_id) - 1

                # Skip if not in target list
                if target_footnotes and footnote_num not in target_footnotes:
                    continue

                # Extract text from all paragraphs in this footnote WITH formatting
                footnote_text = self._extract_footnote_text(footnote, ns)

                if footnote_text.strip():
                    footnotes.append((footnote_num, footnote_text))

        except Exception as e:
            logger.error(f"Error extracting footnotes: {e}")
            raise ValueError(f"Failed to extract footnotes: {e}")

        if not footnotes:
            logger.warning("No footnotes found in document")

        return footnotes

    def _extract_footnote_text(
        self,
        footnote_element,
        ns: Dict[str, str]
    ) -> str:
        """
        Extract text from a footnote element, preserving formatting.

        Args:
            footnote_element: XML element for footnote
            ns: XML namespace dictionary

        Returns:
            Footnote text with formatting markers
        """
        footnote_text = ""

        for para in footnote_element.findall('.//w:p', ns):
            para_text = []

            for run in para.findall('.//w:r', ns):
                # Check for formatting
                rPr = run.find('./w:rPr', ns)
                is_italic = False
                is_bold = False
                is_smallcaps = False

                if rPr is not None:
                    is_italic = rPr.find('./w:i', ns) is not None
                    is_bold = rPr.find('./w:b', ns) is not None
                    is_smallcaps = rPr.find('./w:smallCaps', ns) is not None

                # Get text and apply formatting markers
                for text_elem in run.findall('.//w:t', ns):
                    if text_elem.text:
                        text = text_elem.text
                        if is_italic:
                            text = f"*{text}*"
                        if is_bold:
                            text = f"**{text}**"
                        if is_smallcaps:
                            text = f"[SC]{text}[/SC]"
                        para_text.append(text)

            footnote_text += ''.join(para_text) + " "

        # Normalize spacing (move spaces outside formatting markers)
        footnote_text = self._normalize_markdown_spacing(footnote_text.strip())

        return footnote_text

    def _normalize_markdown_spacing(self, text: str) -> str:
        """
        Normalize markdown spacing by moving spaces outside formatting markers.

        Example:
            "word *italic * word" -> "word *italic* word"

        Args:
            text: Text with markdown formatting

        Returns:
            Normalized text
        """
        import re

        # Move trailing spaces outside closing markers
        text = re.sub(r'(\s+)(\*+|\[/SC\])', r'\2\1', text)

        # Move leading spaces outside opening markers
        text = re.sub(r'(\*+|\[SC\])(\s+)', r'\2\1', text)

        return text

    def _parse_footnote(
        self,
        footnote_num: int,
        footnote_text: str
    ) -> List[Citation]:
        """
        Parse a footnote into individual citations.

        Handles multi-citation footnotes by splitting on signals and
        semicolons.

        Args:
            footnote_num: Footnote number
            footnote_text: Full footnote text

        Returns:
            List of Citation objects (one or more per footnote)
        """
        citations = []

        # Split on signals and semicolons
        # Common signals: see, see also, cf., but see, etc.
        signal_pattern = r'(?:^|;\s*)(?:see also|see|cf\.|but see|see generally|accord|compare|contra|but cf\.)\s+'

        import re
        parts = re.split(signal_pattern, footnote_text, flags=re.IGNORECASE)

        # If no signals found, treat as single citation
        if len(parts) == 1:
            citation = Citation(
                footnote_num=footnote_num,
                citation_num=1,
                full_text=footnote_text,
                raw_footnote=footnote_text
            )
            citation.type = self._detect_citation_type(footnote_text)
            citation.components = self._parse_components(footnote_text, citation.type)
            citation.formatting = self._extract_formatting(footnote_text)
            citations.append(citation)
        else:
            # Multiple citations - split and number them
            for i, part in enumerate(parts, start=1):
                if not part.strip():
                    continue

                citation = Citation(
                    footnote_num=footnote_num,
                    citation_num=i,
                    full_text=part.strip(),
                    raw_footnote=footnote_text
                )
                citation.type = self._detect_citation_type(part)
                citation.components = self._parse_components(part, citation.type)
                citation.formatting = self._extract_formatting(part)
                citations.append(citation)

        return citations

    def _detect_citation_type(self, citation_text: str) -> str:
        """
        Detect the type of citation.

        Args:
            citation_text: Citation text

        Returns:
            Citation type (case, statute, book, article, etc.)
        """
        import re

        # Case citation patterns
        if re.search(r'\*[^*]+\*\s+v\.\s+\*[^*]+\*', citation_text):
            return "case"
        if " v. " in citation_text and re.search(r'\d+\s+[A-Z][a-z]*\.?\s+\d+', citation_text):
            return "case"

        # Statute citation patterns
        if re.search(r'\d+\s+U\.S\.C\.\s+§', citation_text):
            return "statute"
        if " § " in citation_text or " §§ " in citation_text:
            return "statute"

        # Constitution
        if "Const." in citation_text or "Constitution" in citation_text:
            return "constitution"

        # Book citation patterns
        if re.search(r',\s+\d+\s+\(\d{4}\)', citation_text) and not " v. " in citation_text:
            # Likely a book: "Author, Title (Year)"
            return "book"

        # Article/periodical patterns
        if re.search(r',\s+\d+\s+[A-Z].*?\s+\d+,\s+\d+\s+\(\d{4}\)', citation_text):
            # Likely article: "Author, Title, 100 Journal 1 (2020)"
            return "article"

        return "unknown"

    def _parse_components(
        self,
        citation_text: str,
        citation_type: str
    ) -> Dict[str, str]:
        """
        Parse citation into components based on type.

        Args:
            citation_text: Citation text
            citation_type: Detected type

        Returns:
            Dictionary of parsed components
        """
        components = {}

        if citation_type == "case":
            components = self._parse_case_components(citation_text)
        elif citation_type == "statute":
            components = self._parse_statute_components(citation_text)
        elif citation_type == "book":
            components = self._parse_book_components(citation_text)
        elif citation_type == "article":
            components = self._parse_article_components(citation_text)

        return components

    def _parse_case_components(self, citation_text: str) -> Dict[str, str]:
        """Parse case citation components."""
        import re

        components = {}

        # Try to extract case name (text before first volume number)
        match = re.search(r'^(.+?)\s+(\d+)\s+([A-Z][a-z.]*\s*[A-Z0-9.]*)\s+(\d+)', citation_text)
        if match:
            components["case_name"] = match.group(1).strip()
            components["volume"] = match.group(2)
            components["reporter"] = match.group(3)
            components["page"] = match.group(4)

        # Extract year
        year_match = re.search(r'\((\d{4})\)', citation_text)
        if year_match:
            components["year"] = year_match.group(1)

        return components

    def _parse_statute_components(self, citation_text: str) -> Dict[str, str]:
        """Parse statute citation components."""
        import re

        components = {}

        # Extract title, code, section
        match = re.search(r'(\d+)\s+([A-Z.]+)\s+§\s*([\d-]+)', citation_text)
        if match:
            components["title"] = match.group(1)
            components["code"] = match.group(2)
            components["section"] = match.group(3)

        # Extract year
        year_match = re.search(r'\((\d{4})\)', citation_text)
        if year_match:
            components["year"] = year_match.group(1)

        return components

    def _parse_book_components(self, citation_text: str) -> Dict[str, str]:
        """Parse book citation components."""
        components = {}

        # Simple extraction - would need more sophisticated parsing
        parts = citation_text.split(",")
        if len(parts) >= 1:
            components["author"] = parts[0].strip()
        if len(parts) >= 2:
            components["title"] = parts[1].strip()

        return components

    def _parse_article_components(self, citation_text: str) -> Dict[str, str]:
        """Parse article citation components."""
        components = {}

        # Simple extraction
        parts = citation_text.split(",")
        if len(parts) >= 1:
            components["author"] = parts[0].strip()
        if len(parts) >= 2:
            components["title"] = parts[1].strip()

        return components

    def _extract_formatting(self, text: str) -> Dict[str, List[Tuple[int, int]]]:
        """
        Extract formatting ranges from text.

        Args:
            text: Text with markdown formatting

        Returns:
            Dictionary mapping format type to list of (start, end) ranges
        """
        import re

        formatting = {
            "italic": [],
            "bold": [],
            "smallcaps": []
        }

        # Find italic ranges (*text*)
        for match in re.finditer(r'\*([^*]+)\*', text):
            formatting["italic"].append((match.start(), match.end()))

        # Find bold ranges (**text**)
        for match in re.finditer(r'\*\*([^*]+)\*\*', text):
            formatting["bold"].append((match.start(), match.end()))

        # Find smallcaps ranges
        for match in re.finditer(r'\[SC\]([^\[]+)\[/SC\]', text):
            formatting["smallcaps"].append((match.start(), match.end()))

        return formatting


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Test with a Word document
    doc_path = Path("/home/user/slr/test_document.docx")

    if doc_path.exists():
        extractor = CitationExtractor(doc_path)
        citations = extractor.extract_citations(target_footnotes=[1, 2, 3])

        print(f"\n=== Extracted {len(citations)} citations ===\n")

        for citation in citations:
            print(f"FN{citation.footnote_num}-{citation.citation_num}:")
            print(f"  Type: {citation.type}")
            print(f"  Text: {citation.full_text[:100]}...")
            print(f"  Components: {citation.components}")
            print()
    else:
        print(f"Test document not found: {doc_path}")
