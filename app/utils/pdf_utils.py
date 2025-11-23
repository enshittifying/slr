"""
PDF utilities for text extraction, manipulation, and validation
"""
import logging
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Utilities for PDF processing"""

    @staticmethod
    def extract_text(pdf_path: str, max_pages: int = None) -> str:
        """
        Extract text from PDF

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum number of pages to extract (None = all)

        Returns:
            Extracted text
        """
        try:
            logger.debug(f"Extracting text from: {pdf_path}")

            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")

            doc = fitz.open(pdf_path)
            text = ""

            page_count = min(len(doc), max_pages) if max_pages else len(doc)

            for page_num in range(page_count):
                try:
                    page = doc[page_num]
                    text += page.get_text()
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {e}")
                    continue

            doc.close()

            logger.info(f"Extracted {len(text)} characters from {page_count} pages")
            return text

        except fitz.FileDataError:
            logger.error(f"Corrupted or invalid PDF: {pdf_path}")
            raise
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}", exc_info=True)
            raise

    @staticmethod
    def extract_text_by_page(pdf_path: str) -> List[str]:
        """
        Extract text from each page separately

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of text strings, one per page
        """
        try:
            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")

            doc = fitz.open(pdf_path)
            pages = []

            for page_num in range(len(doc)):
                try:
                    page = doc[page_num]
                    pages.append(page.get_text())
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num}: {e}")
                    pages.append("")

            doc.close()

            logger.info(f"Extracted text from {len(pages)} pages")
            return pages

        except Exception as e:
            logger.error(f"Error extracting PDF pages: {e}", exc_info=True)
            raise

    @staticmethod
    def get_metadata(pdf_path: str) -> Dict:
        """
        Extract PDF metadata

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary of metadata
        """
        try:
            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")

            doc = fitz.open(pdf_path)
            metadata = {
                'page_count': len(doc),
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'subject': doc.metadata.get('subject', ''),
                'creator': doc.metadata.get('creator', ''),
                'producer': doc.metadata.get('producer', ''),
                'creation_date': doc.metadata.get('creationDate', ''),
                'modification_date': doc.metadata.get('modDate', ''),
                'encrypted': doc.is_encrypted,
                'pdf_version': doc.pdf_version(),
            }
            doc.close()

            logger.debug(f"Extracted metadata from {pdf_path}")
            return metadata

        except Exception as e:
            logger.error(f"Error extracting PDF metadata: {e}", exc_info=True)
            raise

    @staticmethod
    def remove_pages(pdf_path: str, output_path: str, pages_to_remove: List[int]):
        """
        Remove specific pages from PDF

        Args:
            pdf_path: Path to input PDF
            output_path: Path to output PDF
            pages_to_remove: List of page numbers to remove (0-indexed)
        """
        try:
            logger.info(f"Removing {len(pages_to_remove)} pages from {pdf_path}")

            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")

            doc = fitz.open(pdf_path)

            # Sort in reverse order to avoid index shifting
            for page_num in sorted(pages_to_remove, reverse=True):
                if 0 <= page_num < len(doc):
                    doc.delete_page(page_num)
                else:
                    logger.warning(f"Invalid page number: {page_num}")

            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            doc.save(output_path)
            doc.close()

            logger.info(f"Saved modified PDF to {output_path}")

        except Exception as e:
            logger.error(f"Error removing pages: {e}", exc_info=True)
            raise

    @staticmethod
    def extract_page_range(pdf_path: str, output_path: str, start_page: int, end_page: int):
        """
        Extract a range of pages to a new PDF

        Args:
            pdf_path: Path to input PDF
            output_path: Path to output PDF
            start_page: First page to extract (0-indexed)
            end_page: Last page to extract (0-indexed, inclusive)
        """
        try:
            logger.info(f"Extracting pages {start_page}-{end_page} from {pdf_path}")

            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")

            doc = fitz.open(pdf_path)

            if end_page >= len(doc):
                logger.warning(f"End page {end_page} exceeds document length {len(doc)}")
                end_page = len(doc) - 1

            # Create new document with selected pages
            new_doc = fitz.open()
            for page_num in range(start_page, end_page + 1):
                if 0 <= page_num < len(doc):
                    new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            new_doc.save(output_path)
            new_doc.close()
            doc.close()

            logger.info(f"Saved {end_page - start_page + 1} pages to {output_path}")

        except Exception as e:
            logger.error(f"Error extracting page range: {e}", exc_info=True)
            raise

    @staticmethod
    def merge_pdfs(pdf_paths: List[str], output_path: str):
        """
        Merge multiple PDFs into one

        Args:
            pdf_paths: List of PDF file paths to merge
            output_path: Path to output merged PDF
        """
        try:
            logger.info(f"Merging {len(pdf_paths)} PDFs")

            merged_doc = fitz.open()

            for pdf_path in pdf_paths:
                if not Path(pdf_path).exists():
                    logger.warning(f"PDF not found, skipping: {pdf_path}")
                    continue

                try:
                    doc = fitz.open(pdf_path)
                    merged_doc.insert_pdf(doc)
                    doc.close()
                except Exception as e:
                    logger.error(f"Error merging {pdf_path}: {e}")
                    continue

            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            merged_doc.save(output_path)
            merged_doc.close()

            logger.info(f"Saved merged PDF to {output_path}")

        except Exception as e:
            logger.error(f"Error merging PDFs: {e}", exc_info=True)
            raise

    @staticmethod
    def add_highlight(pdf_path: str, output_path: str, page_num: int,
                     rect: Tuple[float, float, float, float], color: Tuple[float, float, float] = (1, 1, 0)):
        """
        Add a highlight annotation to a PDF

        Args:
            pdf_path: Path to input PDF
            output_path: Path to output PDF
            page_num: Page number (0-indexed)
            rect: Rectangle coordinates (x0, y0, x1, y1)
            color: RGB color tuple (default: yellow)
        """
        try:
            logger.debug(f"Adding highlight to page {page_num} of {pdf_path}")

            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")

            doc = fitz.open(pdf_path)

            if page_num >= len(doc):
                raise ValueError(f"Page {page_num} exceeds document length {len(doc)}")

            page = doc[page_num]
            highlight = page.add_highlight_annot(rect)
            highlight.set_colors(stroke=color)
            highlight.update()

            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            doc.save(output_path, incremental=False, encryption=fitz.PDF_ENCRYPT_NONE)
            doc.close()

            logger.debug(f"Added highlight and saved to {output_path}")

        except Exception as e:
            logger.error(f"Error adding highlight: {e}", exc_info=True)
            raise

    @staticmethod
    def search_text(pdf_path: str, search_term: str, case_sensitive: bool = False) -> List[Dict]:
        """
        Search for text in PDF and return locations

        Args:
            pdf_path: Path to PDF file
            search_term: Text to search for
            case_sensitive: Whether search should be case-sensitive

        Returns:
            List of dicts with page_num and rect coordinates
        """
        try:
            logger.debug(f"Searching for '{search_term}' in {pdf_path}")

            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")

            doc = fitz.open(pdf_path)
            results = []

            flags = 0 if case_sensitive else fitz.TEXT_PRESERVE_WHITESPACE

            for page_num in range(len(doc)):
                page = doc[page_num]
                text_instances = page.search_for(search_term, flags=flags)

                for rect in text_instances:
                    results.append({
                        'page_num': page_num,
                        'rect': tuple(rect),
                        'text': search_term
                    })

            doc.close()

            logger.info(f"Found {len(results)} instances of '{search_term}'")
            return results

        except Exception as e:
            logger.error(f"Error searching PDF: {e}", exc_info=True)
            raise

    @staticmethod
    def rotate_pages(pdf_path: str, output_path: str, rotation: int, page_nums: List[int] = None):
        """
        Rotate pages in PDF

        Args:
            pdf_path: Path to input PDF
            output_path: Path to output PDF
            rotation: Degrees to rotate (90, 180, or 270)
            page_nums: List of page numbers to rotate (None = all pages)
        """
        try:
            if rotation not in [90, 180, 270, -90, -180, -270]:
                raise ValueError(f"Invalid rotation: {rotation}. Must be ±90, ±180, or ±270")

            logger.info(f"Rotating pages by {rotation}° in {pdf_path}")

            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")

            doc = fitz.open(pdf_path)

            pages_to_rotate = page_nums if page_nums else range(len(doc))

            for page_num in pages_to_rotate:
                if 0 <= page_num < len(doc):
                    page = doc[page_num]
                    page.set_rotation(rotation)
                else:
                    logger.warning(f"Invalid page number: {page_num}")

            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

            doc.save(output_path)
            doc.close()

            logger.info(f"Saved rotated PDF to {output_path}")

        except Exception as e:
            logger.error(f"Error rotating pages: {e}", exc_info=True)
            raise


# Convenience functions
def extract_text_from_pdf(pdf_path: str, max_pages: int = None) -> str:
    """Convenience function to extract text from PDF"""
    processor = PDFProcessor()
    return processor.extract_text(pdf_path, max_pages)


def get_pdf_page_count(pdf_path: str) -> int:
    """Get number of pages in PDF"""
    try:
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        return count
    except Exception as e:
        logger.error(f"Error getting page count: {e}", exc_info=True)
        raise
