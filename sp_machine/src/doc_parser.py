"""
Parse Word documents to extract footnotes and build a citation map.
"""
from docx import Document
from typing import Dict

class DocParser:
    """Parse Word documents."""

    def __init__(self, doc_path: str):
        self.doc_path = doc_path
        self.doc = Document(doc_path)
        self.citation_map = self._build_citation_map()

    def _build_citation_map(self) -> Dict[int, str]:
        """Build a map of footnote number to footnote text."""
        citation_map = {}
        try:
            footnotes = self.doc.part.footnotes
            for footnote in footnotes:
                footnote_id = int(footnote.id)
                text = "".join(p.text for p in footnote.paragraphs)
                citation_map[footnote_id] = text
        except AttributeError:
            # No footnotes part exists
            pass
        return citation_map

    def get_citation_map(self) -> Dict[int, str]:
        """Return the citation map."""
        return self.citation_map
