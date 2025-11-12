"""Redbox engine for highlighting citation metadata in PDFs."""

from typing import List, Tuple, Dict, Any
from pathlib import Path
import fitz  # PyMuPDF
import re

from shared_utils.logger import get_logger
from shared_utils.exceptions import PDFProcessingError

logger = get_logger(__name__)


class RedboxEngine:
    """Engine for drawing red boxes around citation metadata in PDFs."""

    # Citation metadata patterns to identify
    METADATA_PATTERNS = {
        "volume": r"\b\d+\b",  # Volume numbers
        "reporter": r"\b[A-Z][a-z\.]+\s+\d+\b",  # Reporter citations
        "year": r"\((\d{4})\)",  # Years in parentheses
        "page": r"\bat\s+\d+\b",  # Page numbers
        "court": r"\b(Supreme Court|Circuit|District)\b",  # Court names
    }

    def __init__(self):
        """Initialize the redbox engine."""
        self.red_color = (1, 0, 0)  # RGB red

    def redbox_metadata(self, pdf_bytes: bytes) -> bytes:
        """
        Draw red boxes around citation metadata in a PDF.

        Args:
            pdf_bytes: PDF content as bytes

        Returns:
            Modified PDF with redboxes as bytes

        Raises:
            PDFProcessingError: If redboxing fails
        """
        try:
            # Open PDF from bytes
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            # Process first 3 pages (where metadata typically appears)
            pages_to_process = min(3, doc.page_count)

            for page_num in range(pages_to_process):
                page = doc[page_num]
                self._redbox_page(page)

            # Save modified PDF
            output = doc.write()
            doc.close()

            logger.info("Completed metadata redboxing")
            return output

        except Exception as e:
            logger.error(f"Failed to redbox metadata: {e}")
            raise PDFProcessingError(f"Failed to redbox metadata: {e}")

    def _redbox_page(self, page: fitz.Page) -> None:
        """
        Draw red boxes around metadata on a single page.

        Args:
            page: PyMuPDF page object
        """
        text_instances = page.get_text("dict")

        for block in text_instances["blocks"]:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"]
                    bbox = fitz.Rect(span["bbox"])

                    # Check if this text matches any metadata pattern
                    if self._is_metadata(text):
                        # Draw red rectangle
                        annot = page.add_rect_annot(bbox)
                        annot.set_colors(stroke=self.red_color)
                        annot.set_border(width=2)
                        annot.update()

                        logger.debug(f"Redboxed: {text}")

    def _is_metadata(self, text: str) -> bool:
        """
        Check if text matches citation metadata patterns.

        Args:
            text: Text to check

        Returns:
            True if text appears to be citation metadata
        """
        # Check against known patterns
        for pattern_name, pattern in self.METADATA_PATTERNS.items():
            if re.search(pattern, text):
                return True

        # Additional heuristics
        # - Short text with numbers and capitals
        # - Legal abbreviations
        if len(text) < 30 and re.search(r"\d", text) and re.search(r"[A-Z]", text):
            return True

        return False

    def redbox_custom_regions(
        self, pdf_bytes: bytes, regions: List[Tuple[int, Tuple[float, float, float, float]]]
    ) -> bytes:
        """
        Draw red boxes around custom regions.

        Args:
            pdf_bytes: PDF content as bytes
            regions: List of (page_num, (x0, y0, x1, y1)) tuples

        Returns:
            Modified PDF with redboxes

        Raises:
            PDFProcessingError: If redboxing fails
        """
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            for page_num, (x0, y0, x1, y1) in regions:
                if 0 <= page_num < doc.page_count:
                    page = doc[page_num]
                    rect = fitz.Rect(x0, y0, x1, y1)

                    annot = page.add_rect_annot(rect)
                    annot.set_colors(stroke=self.red_color)
                    annot.set_border(width=2)
                    annot.update()

                    logger.debug(f"Redboxed custom region on page {page_num}")

            output = doc.write()
            doc.close()

            return output

        except Exception as e:
            logger.error(f"Failed to redbox custom regions: {e}")
            raise PDFProcessingError(f"Failed to redbox custom regions: {e}")
