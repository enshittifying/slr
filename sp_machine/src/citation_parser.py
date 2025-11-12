"""Parse citation text to extract metadata."""

import re
from typing import Dict, Any, Optional
from shared_utils.logger import get_logger
from shared_utils.exceptions import CitationParsingError

logger = get_logger(__name__)


class CitationParser:
    """Parse citation text to extract metadata."""

    def parse(self, citation_text: str) -> Dict[str, Any]:
        """
        Parse a citation string to extract metadata.

        Args:
            citation_text: The full citation text

        Returns:
            Dictionary containing citation metadata

        Raises:
            CitationParsingError: If parsing fails
        """
        try:
            citation_data = {
                "raw_text": citation_text,
                "type": self._determine_type(citation_text),
                "title": self._extract_title(citation_text),
                "author": self._extract_author(citation_text),
                "year": self._extract_year(citation_text),
                "volume": self._extract_volume(citation_text),
                "reporter": self._extract_reporter(citation_text),
                "page": self._extract_page(citation_text),
            }

            logger.debug(f"Parsed citation: {citation_data['title']}")
            return citation_data

        except Exception as e:
            logger.error(f"Failed to parse citation: {e}")
            raise CitationParsingError(f"Failed to parse citation: {e}")

    def _determine_type(self, citation: str) -> str:
        """
        Determine the type of citation.

        Returns: 'case', 'article', 'book', 'statute', 'website', or 'unknown'
        """
        citation_lower = citation.lower()

        # Case law indicators
        if any(reporter in citation for reporter in ["U.S.", "F.2d", "F.3d", "F.4th", "S.Ct."]):
            return "case"

        # Law review article indicators
        if any(journal in citation_lower for journal in ["l. rev", "law review", "j.", "harv.", "stan.", "yale"]):
            return "article"

        # Statute indicators
        if any(code in citation for code in ["U.S.C.", "C.F.R.", "Stat."]):
            return "statute"

        # Book indicators
        if "(" in citation and ")" in citation and "," in citation:
            return "book"

        # Website indicators
        if "http" in citation_lower or "www." in citation_lower:
            return "website"

        return "unknown"

    def _extract_title(self, citation: str) -> Optional[str]:
        """Extract the title from a citation."""
        # Simple heuristic: look for quoted text or italicized text
        # This is a placeholder - actual implementation would be more sophisticated

        # Try to find quoted text
        quote_match = re.search(r'"([^"]+)"', citation)
        if quote_match:
            return quote_match.group(1)

        # Try to find text before a comma or reporter
        parts = citation.split(",")
        if parts:
            return parts[0].strip()

        return None

    def _extract_author(self, citation: str) -> Optional[str]:
        """Extract the author from a citation."""
        # Placeholder implementation
        # Real implementation would use more sophisticated parsing
        return None

    def _extract_year(self, citation: str) -> Optional[int]:
        """Extract the year from a citation."""
        year_match = re.search(r'\((\d{4})\)', citation)
        if year_match:
            return int(year_match.group(1))

        # Also try years without parentheses
        year_match = re.search(r'\b(19|20)\d{2}\b', citation)
        if year_match:
            return int(year_match.group(0))

        return None

    def _extract_volume(self, citation: str) -> Optional[str]:
        """Extract the volume number from a citation."""
        # Look for number before a reporter abbreviation
        volume_match = re.search(r'(\d+)\s+[A-Z]', citation)
        if volume_match:
            return volume_match.group(1)

        return None

    def _extract_reporter(self, citation: str) -> Optional[str]:
        """Extract the reporter abbreviation from a citation."""
        # Common reporter abbreviations
        reporters = ["U.S.", "F.2d", "F.3d", "F.4th", "S.Ct.", "L.Ed."]

        for reporter in reporters:
            if reporter in citation:
                return reporter

        return None

    def _extract_page(self, citation: str) -> Optional[str]:
        """Extract the page number from a citation."""
        # Look for number after a reporter
        page_match = re.search(r'[A-Z][a-z\.]+\s+(\d+)', citation)
        if page_match:
            return page_match.group(1)

        return None
