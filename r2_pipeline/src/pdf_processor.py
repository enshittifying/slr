"""
Extract text and annotations from R1 PDFs.
Detects redboxed regions and extracts their content.
"""
import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
import re
import tempfile

logger = logging.getLogger(__name__)

# Try to import OCR dependencies
try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("OCR libraries not available. Install with: pip install pytesseract pillow")
    logger.warning("Also install tesseract: brew install tesseract (macOS) or apt-get install tesseract-ocr (Linux)")

class TextQualityChecker:
    """
    Detect poor OCR quality in extracted text.
    Identifies garbage characters, missing spaces, and other OCR artifacts.
    """

    @staticmethod
    def assess_text_quality(text: str) -> Dict:
        """
        Assess the quality of extracted text and detect OCR issues.

        Args:
            text: The text to assess

        Returns:
            Dict with quality score (0-1), issues list, and is_corrupted flag
        """
        if not text or len(text.strip()) == 0:
            return {
                "score": 0.0,
                "is_corrupted": True,
                "issues": ["Empty or whitespace-only text"],
                "warnings": []
            }

        issues = []
        warnings = []

        # Calculate various quality metrics
        total_chars = len(text)

        # 1. Check ratio of alphanumeric characters
        alphanumeric_chars = sum(c.isalnum() or c.isspace() for c in text)
        alphanumeric_ratio = alphanumeric_chars / total_chars if total_chars > 0 else 0

        # 2. Check for excessive special characters
        special_chars = sum(not c.isalnum() and not c.isspace() and c not in ".,;:!?-\"'()" for c in text)
        special_char_ratio = special_chars / total_chars if total_chars > 0 else 0

        # 3. Check for garbage character sequences (random non-word patterns)
        garbage_patterns = [
            r'[^a-zA-Z0-9\s]{5,}',  # 5+ consecutive non-alphanumeric chars
            r'[a-z]{15,}',  # 15+ consecutive lowercase letters (likely OCR error)
            r'\b[a-z]{1,2}\s[a-z]{1,2}\s[a-z]{1,2}\s[a-z]{1,2}\b',  # Many single/double letter "words"
            r'[\x00-\x1f]',  # Control characters
        ]

        garbage_matches = 0
        for pattern in garbage_patterns:
            garbage_matches += len(re.findall(pattern, text))

        # 4. Check average word length (very short or very long suggests OCR issues)
        words = text.split()
        if words:
            avg_word_length = sum(len(w) for w in words) / len(words)
            if avg_word_length < 2:
                warnings.append(f"Suspiciously short average word length: {avg_word_length:.1f}")
            elif avg_word_length > 12:
                warnings.append(f"Suspiciously long average word length: {avg_word_length:.1f}")
        else:
            issues.append("No recognizable words found")

        # 5. Check for excessive whitespace or missing spaces
        excessive_whitespace = len(re.findall(r'\s{5,}', text))
        missing_spaces = len(re.findall(r'[a-z][A-Z]', text))  # lowercase followed by uppercase

        # Scoring logic
        score = 1.0

        if alphanumeric_ratio < 0.6:
            issues.append(f"Low alphanumeric ratio: {alphanumeric_ratio:.2%} (expected >60%)")
            score -= 0.3
        elif alphanumeric_ratio < 0.75:
            warnings.append(f"Below-average alphanumeric ratio: {alphanumeric_ratio:.2%}")
            score -= 0.1

        if special_char_ratio > 0.15:
            issues.append(f"High special character ratio: {special_char_ratio:.2%} (expected <15%)")
            score -= 0.3

        if garbage_matches > 3:
            issues.append(f"Found {garbage_matches} garbage character sequences")
            score -= 0.4
        elif garbage_matches > 0:
            warnings.append(f"Found {garbage_matches} potential garbage sequences")
            score -= 0.1

        if excessive_whitespace > len(text) / 500:  # More than 1 per 500 chars is suspicious
            warnings.append(f"Excessive whitespace detected ({excessive_whitespace} instances)")
            score -= 0.1

        if missing_spaces > len(text) / 100:  # More than 1% missing spaces
            warnings.append(f"Possible missing spaces ({missing_spaces} instances)")
            score -= 0.1

        # Clamp score to 0-1 range
        score = max(0.0, min(1.0, score))

        # Determine if corrupted (score below threshold)
        is_corrupted = score < 0.5 or len(issues) > 0

        return {
            "score": score,
            "is_corrupted": is_corrupted,
            "issues": issues,
            "warnings": warnings,
            "metrics": {
                "alphanumeric_ratio": alphanumeric_ratio,
                "special_char_ratio": special_char_ratio,
                "garbage_sequences": garbage_matches,
                "excessive_whitespace": excessive_whitespace,
                "missing_spaces": missing_spaces
            }
        }

class PDFProcessor:
    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        try:
            # Suppress MuPDF warnings/errors
            fitz.TOOLS.mupdf_display_errors(False)
            self.doc = fitz.open(pdf_path)
            self.num_pages = len(self.doc)
        except Exception as e:
            logger.error(f"Failed to open PDF {pdf_path}: {e}")
            raise

    def extract_text_with_coordinates(self) -> List[Dict]:
        """
        Extract all text with bounding box coordinates.
        Returns list of text blocks with position info.
        """
        text_blocks = []

        for page_num in range(self.num_pages):
            page = self.doc[page_num]
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                if block["type"] == 0:  # Text block
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text_blocks.append({
                                "page": page_num,
                                "text": span["text"],
                                "bbox": span["bbox"],  # (x0, y0, x1, y1)
                                "font": span["font"],
                                "size": span["size"]
                            })

        return text_blocks

    def extract_annotations(self) -> List[Dict]:
        """
        Extract all annotations (redboxes, highlights, etc).
        Returns list of annotation objects with their locations.
        """
        annotations = []

        for page_num in range(self.num_pages):
            page = self.doc[page_num]
            annots = page.annots()

            if annots:
                for annot in annots:
                    annot_dict = {
                        "page": page_num,
                        "type": annot.type[1],  # Type name (e.g., 'Square', 'Highlight')
                        "rect": annot.rect,  # Bounding box (x0, y0, x1, y1)
                        "color": annot.colors,
                        "content": annot.info.get("content", "")
                    }
                    annotations.append(annot_dict)
                    logger.debug(f"Found annotation on page {page_num}: {annot.type[1]}")

        return annotations

    def extract_redboxed_text(self, annotations: List[Dict],
                               text_blocks: List[Dict],
                               tolerance: int = 20) -> List[Dict]:
        """
        Match annotations to text blocks and extract redboxed content.

        Args:
            annotations: List of annotation dicts
            text_blocks: List of text block dicts
            tolerance: Pixel tolerance for overlap detection (increased default)

        Returns:
            List of redboxed text regions with content
        """
        redboxed_regions = []

        for annot in annotations:
            # Look for any type of annotation (Square, Highlight, Ink, etc.)
            annot_rect = annot["rect"]
            matched_text = []

            # Find all text blocks that overlap with this annotation
            for block in text_blocks:
                if block["page"] != annot["page"]:
                    continue

                block_bbox = block["bbox"]

                # Check if bounding boxes overlap
                if self._boxes_overlap(annot_rect, block_bbox, tolerance):
                    matched_text.append(block["text"])

            if matched_text:
                full_text = " ".join(matched_text)
                logger.info(f"Extracted redboxed text on page {annot['page']}: {full_text[:200]}...")
                redboxed_regions.append({
                    "page": annot["page"],
                    "rect": annot_rect,
                    "text": full_text,
                    "annotation_type": annot["type"],
                    "annotation_content": annot["content"]
                })

        return redboxed_regions

    def _boxes_overlap(self, rect1: Tuple, rect2: Tuple, tolerance: int = 5) -> bool:
        """
        Check if two bounding boxes overlap.
        rect format: (x0, y0, x1, y1)
        """
        x0_1, y0_1, x1_1, y1_1 = rect1
        x0_2, y0_2, x1_2, y1_2 = rect2

        # Expand rect1 by tolerance
        x0_1 -= tolerance
        y0_1 -= tolerance
        x1_1 += tolerance
        y1_1 += tolerance

        # Check overlap
        return not (x1_1 < x0_2 or x1_2 < x0_1 or y1_1 < y0_2 or y1_2 < y0_1)

    def get_full_page_text(self, page_num: int) -> str:
        """Extract all text from a specific page."""
        page = self.doc[page_num]
        return page.get_text()

    def extract_text_by_region(self) -> List[Dict]:
        """
        Fallback method: Extract text from typical redbox regions.
        Looks for text in the top portion of the first page.
        """
        regions = []

        # Check first page for redbox (typically at top)
        if self.num_pages > 0:
            page = self.doc[0]
            page_rect = page.rect

            # Define a region at the top of the page (top 40% of page)
            top_region = fitz.Rect(
                0,
                0,
                page_rect.width,
                page_rect.height * 0.4
            )

            # Extract text from this region
            text = page.get_textbox(top_region)

            if text and text.strip():
                logger.info(f"Extracted text from top region of page 0: {text[:150]}...")
                regions.append({
                    "page": 0,
                    "rect": top_region,
                    "text": text.strip(),
                    "annotation_type": "region_extraction",
                    "annotation_content": "Fallback extraction from top region"
                })

        # Also check for any colored rectangles or highlights in the PDF structure
        for page_num in range(min(3, self.num_pages)):  # Check first 3 pages
            page = self.doc[page_num]

            # Get drawing commands to find rectangles
            drawings = page.get_drawings()
            for drawing in drawings:
                if drawing.get("type") == "f" or drawing.get("fill"):  # Filled shape
                    rect = drawing.get("rect")
                    if rect:
                        # Extract text within this rectangle
                        try:
                            text = page.get_textbox(rect)
                            if text and text.strip() and len(text.strip()) > 20:
                                regions.append({
                                    "page": page_num,
                                    "rect": rect,
                                    "text": text.strip(),
                                    "annotation_type": "drawing_extraction",
                                    "annotation_content": "Extracted from colored rectangle"
                                })
                        except:
                            pass

        return regions

    def extract_metadata(self) -> Dict:
        """Extract PDF metadata."""
        return {
            "filename": self.pdf_path.name,
            "num_pages": self.num_pages,
            "title": self.doc.metadata.get("title", ""),
            "author": self.doc.metadata.get("author", ""),
            "creation_date": self.doc.metadata.get("creationDate", "")
        }

    def re_ocr_region(self, page_num: int, rect: fitz.Rect, dpi: int = 300) -> Optional[str]:
        """
        Re-OCR a specific region of a page using Tesseract.

        Args:
            page_num: Page number (0-indexed)
            rect: Rectangle defining the region to OCR
            dpi: Resolution for image extraction (higher = better quality)

        Returns:
            Extracted text or None if OCR fails
        """
        if not OCR_AVAILABLE:
            logger.error("Cannot re-OCR: pytesseract not available")
            return None

        try:
            page = self.doc[page_num]

            # Extract the page region as a high-res image
            # zoom factor: 300dpi / 72dpi = 4.167
            zoom = dpi / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, clip=rect)

            # Convert PyMuPDF pixmap to PIL Image
            # PyMuPDF uses RGB or RGBA, convert to PIL
            if pix.alpha:
                mode = "RGBA"
            else:
                mode = "RGB"

            img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)

            # Run Tesseract OCR
            logger.info(f"Re-OCRing page {page_num}, region at {dpi} DPI...")
            text = pytesseract.image_to_string(img, config='--psm 6')  # Assume uniform text block

            logger.info(f"Re-OCR extracted {len(text)} characters")
            return text.strip()

        except Exception as e:
            logger.error(f"Failed to re-OCR region: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def close(self):
        """Close the PDF document."""
        self.doc.close()

# Convenience function
def process_r1_pdf(pdf_path: Path) -> Dict:
    """
    Main function to process an R1 PDF and extract all relevant data.

    Returns:
        Dict with metadata, full_text, redboxed_regions, annotations
    """
    processor = PDFProcessor(pdf_path)

    try:
        metadata = processor.extract_metadata()
        logger.info(f"Processing PDF: {metadata['filename']}, Pages: {metadata['num_pages']}")

        text_blocks = processor.extract_text_with_coordinates()
        logger.info(f"Extracted {len(text_blocks)} text blocks")

        annotations = processor.extract_annotations()
        logger.info(f"Found {len(annotations)} annotations")

        # Try annotation-based extraction first
        redboxed_regions = processor.extract_redboxed_text(annotations, text_blocks)

        # If no redboxed regions found via annotations, try alternative methods
        if not redboxed_regions:
            logger.warning("No redboxed regions found via annotations, trying alternative extraction...")
            # Fallback: look for text in typical redbox locations (top of first page, etc.)
            redboxed_regions = processor.extract_text_by_region()

        logger.info(f"Extracted {len(redboxed_regions)} redboxed region(s)")

        # Check text quality for each redboxed region and re-OCR if needed
        quality_checker = TextQualityChecker()
        has_quality_issues = False

        for i, region in enumerate(redboxed_regions):
            logger.info(f"  Region {i+1} (page {region['page']}): {region['text'][:150]}...")

            # Assess text quality
            quality = quality_checker.assess_text_quality(region['text'])
            region['quality_assessment'] = quality

            # Log quality issues and attempt re-OCR
            if quality['is_corrupted']:
                has_quality_issues = True
                logger.error(f"  ⚠️  BAD OCR DETECTED in Region {i+1}!")
                logger.error(f"      Quality score: {quality['score']:.2f}/1.0")
                for issue in quality['issues']:
                    logger.error(f"      - {issue}")

                # Attempt to re-OCR this region
                if OCR_AVAILABLE:
                    logger.info(f"  🔄 Attempting to re-OCR Region {i+1} using Tesseract...")
                    new_text = processor.re_ocr_region(region['page'], region['rect'])

                    if new_text:
                        # Re-assess the quality of the new text
                        new_quality = quality_checker.assess_text_quality(new_text)
                        logger.info(f"      Re-OCR quality score: {new_quality['score']:.2f}/1.0")

                        if new_quality['score'] > quality['score']:
                            logger.info(f"      ✓ Re-OCR improved quality! Replacing text.")
                            region['text'] = new_text
                            region['quality_assessment'] = new_quality
                            region['was_re_ocred'] = True

                            # If quality is now acceptable, remove the corrupted flag
                            if not new_quality['is_corrupted']:
                                has_quality_issues = False  # At least attempted fix
                        else:
                            logger.warning(f"      ✗ Re-OCR did not improve quality. Keeping original.")
                            region['was_re_ocred'] = False
                    else:
                        logger.error(f"      ✗ Re-OCR failed.")
                        region['was_re_ocred'] = False
                else:
                    logger.error(f"      ✗ Cannot re-OCR: Tesseract not available")
                    region['was_re_ocred'] = False

            elif quality['warnings']:
                logger.warning(f"  ⚠️  Quality warnings for Region {i+1}:")
                logger.warning(f"      Quality score: {quality['score']:.2f}/1.0")
                for warning in quality['warnings']:
                    logger.warning(f"      - {warning}")

        # Get full text for each page
        full_text = []
        for page_num in range(processor.num_pages):
            full_text.append({
                "page": page_num,
                "text": processor.get_full_page_text(page_num)
            })

        return {
            "success": True,
            "metadata": metadata,
            "full_text": full_text,
            "redboxed_regions": redboxed_regions,
            "annotations": annotations,
            "text_blocks": text_blocks,
            "has_quality_issues": has_quality_issues,
            "error": None
        }

    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "metadata": {},
            "full_text": [],
            "redboxed_regions": [],
            "annotations": [],
            "text_blocks": [],
            "error": str(e)
        }

    finally:
        processor.close()
