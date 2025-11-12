"""Clean PDFs by removing extraneous pages."""

from pathlib import Path
from typing import List
import fitz  # PyMuPDF

from shared_utils.logger import get_logger
from shared_utils.exceptions import PDFProcessingError

logger = get_logger(__name__)


class PDFCleaner:
    """Clean PDFs for the R1 stage."""

    # Common cover page indicators for legal databases
    COVER_PAGE_INDICATORS = [
        "HeinOnline",
        "Westlaw",
        "LexisNexis",
        "JSTOR",
        "Downloaded from",
        "Copyright",
        "Terms of Use",
    ]

    def clean(self, pdf_path: Path) -> bytes:
        """
        Clean a PDF by removing cover pages and extraneous content.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Cleaned PDF as bytes

        Raises:
            PDFProcessingError: If cleaning fails
        """
        try:
            doc = fitz.open(pdf_path)
            pages_to_delete = []

            # Check each page for cover page indicators
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text = page.get_text()

                # Check if this looks like a cover page
                if self._is_cover_page(text):
                    pages_to_delete.append(page_num)
                    logger.debug(f"Marking page {page_num} for deletion (cover page)")

            # Delete marked pages
            for page_num in sorted(pages_to_delete, reverse=True):
                doc.delete_page(page_num)

            # Save cleaned PDF
            output = doc.write()
            doc.close()

            if pages_to_delete:
                logger.info(f"Cleaned PDF: removed {len(pages_to_delete)} cover pages")
            else:
                logger.info("No cover pages detected")

            return output

        except Exception as e:
            logger.error(f"Failed to clean PDF: {e}")
            raise PDFProcessingError(f"Failed to clean PDF: {e}")

    def _is_cover_page(self, page_text: str) -> bool:
        """
        Determine if a page is likely a cover page.

        Args:
            page_text: Extracted text from the page

        Returns:
            True if the page appears to be a cover page
        """
        # Check for common cover page indicators
        for indicator in self.COVER_PAGE_INDICATORS:
            if indicator.lower() in page_text.lower():
                return True

        # Check if page has very little content (< 100 characters)
        if len(page_text.strip()) < 100:
            return True

        return False
