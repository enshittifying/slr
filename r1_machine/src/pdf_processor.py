"""PDF processing utilities for R1 machine."""

from typing import Optional, List, Tuple
from pathlib import Path
import fitz  # PyMuPDF

from shared_utils.logger import get_logger
from shared_utils.exceptions import PDFProcessingError

logger = get_logger(__name__)


class PDFProcessor:
    """Process PDFs for the R1 stage."""

    def __init__(self):
        """Initialize the PDF processor."""
        pass

    def extract_text(self, pdf_path: Path) -> str:
        """
        Extract all text from a PDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text as string

        Raises:
            PDFProcessingError: If extraction fails
        """
        try:
            doc = fitz.open(pdf_path)
            text = ""

            for page in doc:
                text += page.get_text()

            doc.close()
            logger.debug(f"Extracted {len(text)} characters from {pdf_path.name}")
            return text

        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise PDFProcessingError(f"Failed to extract text: {e}")

    def get_page_count(self, pdf_path: Path) -> int:
        """Get the number of pages in a PDF."""
        try:
            doc = fitz.open(pdf_path)
            count = doc.page_count
            doc.close()
            return count
        except Exception as e:
            logger.error(f"Failed to get page count: {e}")
            raise PDFProcessingError(f"Failed to get page count: {e}")

    def delete_pages(self, pdf_path: Path, pages_to_delete: List[int]) -> bytes:
        """
        Delete specific pages from a PDF.

        Args:
            pdf_path: Path to the PDF file
            pages_to_delete: List of page numbers (0-indexed) to delete

        Returns:
            Modified PDF as bytes

        Raises:
            PDFProcessingError: If deletion fails
        """
        try:
            doc = fitz.open(pdf_path)

            # Sort in reverse to avoid index shifting issues
            for page_num in sorted(pages_to_delete, reverse=True):
                if 0 <= page_num < doc.page_count:
                    doc.delete_page(page_num)

            output = doc.write()
            doc.close()

            logger.info(f"Deleted {len(pages_to_delete)} pages from PDF")
            return output

        except Exception as e:
            logger.error(f"Failed to delete pages: {e}")
            raise PDFProcessingError(f"Failed to delete pages: {e}")

    def merge_pdfs(self, pdf_paths: List[Path]) -> bytes:
        """
        Merge multiple PDFs into one.

        Args:
            pdf_paths: List of PDF file paths to merge

        Returns:
            Merged PDF as bytes

        Raises:
            PDFProcessingError: If merging fails
        """
        try:
            merged_doc = fitz.open()

            for pdf_path in pdf_paths:
                doc = fitz.open(pdf_path)
                merged_doc.insert_pdf(doc)
                doc.close()

            output = merged_doc.write()
            merged_doc.close()

            logger.info(f"Merged {len(pdf_paths)} PDFs")
            return output

        except Exception as e:
            logger.error(f"Failed to merge PDFs: {e}")
            raise PDFProcessingError(f"Failed to merge PDFs: {e}")

    def extract_page_as_image(self, pdf_path: Path, page_num: int) -> bytes:
        """
        Extract a single page as an image.

        Args:
            pdf_path: Path to the PDF file
            page_num: Page number (0-indexed)

        Returns:
            Image as bytes (PNG format)

        Raises:
            PDFProcessingError: If extraction fails
        """
        try:
            doc = fitz.open(pdf_path)
            page = doc[page_num]

            # Render page to image
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")

            doc.close()
            logger.debug(f"Extracted page {page_num} as image")
            return img_bytes

        except Exception as e:
            logger.error(f"Failed to extract page as image: {e}")
            raise PDFProcessingError(f"Failed to extract page: {e}")
