"""
Generate R2 PDFs with validation annotations.
"""
import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class R2Generator:
    """Generate R2 PDFs with annotations."""

    def __init__(self, r1_pdf_path: Path, output_dir: Path):
        self.r1_pdf_path = r1_pdf_path
        self.output_dir = output_dir
        self.doc = fitz.open(r1_pdf_path)

    def add_validation_annotations(self, validation_results: Dict) -> None:
        """
        Add validation results as annotations to PDF.

        Args:
            validation_results: Dict with validation info to annotate
        """
        # Add annotation on first page as a small note icon (doesn't obscure content)
        first_page = self.doc[0]

        # Create text box with validation summary
        summary_text = self._create_validation_summary(validation_results)

        # Add a small note/comment annotation in top-right corner (doesn't block content)
        # This creates a clickable icon that shows the text when clicked
        point = fitz.Point(first_page.rect.width - 30, 20)  # Top-right corner
        annot = first_page.add_text_annot(
            point,
            summary_text,
            icon="Note"  # Small note icon
        )
        annot.update()

        logger.info(f"Added validation note icon to first page (top-right corner)")

    def _create_validation_summary(self, results: Dict) -> str:
        """Create validation summary text."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        summary = f"R2 VALIDATION - {timestamp}\n\n"

        # Citation format check
        if results.get("citation_validation"):
            cv = results["citation_validation"]
            if cv.get("is_correct"):
                summary += "✓ Citation format: CORRECT\n"
            else:
                summary += f"✗ Citation format: {len(cv.get('errors', []))} errors found\n"

        # Support check
        if results.get("support_analysis"):
            sa = results["support_analysis"]
            support = sa.get("support_level", "unknown")
            confidence = sa.get("confidence", 0)
            summary += f"{'✓' if support == 'yes' else '⚠' if support == 'maybe' else '✗'} "
            summary += f"Support: {support.upper()} (confidence: {confidence:.2f})\n"

        # Quote accuracy
        if results.get("quote_verification"):
            qv = results["quote_verification"]
            if qv.get("accurate"):
                summary += "✓ Quote accuracy: VERIFIED\n"
            else:
                summary += f"✗ Quote accuracy: {len(qv.get('issues', []))} issues\n"

        # Overall recommendation
        summary += "\n"
        if results.get("recommendation"):
            summary += f"Recommendation: {results['recommendation'].upper()}"

        return summary

    def highlight_issues(self, issues: List[Dict]) -> None:
        """
        Add highlight annotations for specific issues.

        Args:
            issues: List of issue dicts with page, rect, description
        """
        for issue in issues:
            page_num = issue.get("page", 0)
            if page_num >= len(self.doc):
                continue

            page = self.doc[page_num]

            # Add highlight annotation
            if "rect" in issue:
                rect = fitz.Rect(issue["rect"])
                highlight = page.add_highlight_annot(rect)
                highlight.set_colors(stroke=(1, 0, 0))  # Red highlight
                highlight.set_info(content=issue.get("description", "Issue"))
                highlight.update()

    def save_r2_pdf(self, filename: str = None) -> Path:
        """
        Save the R2 PDF with annotations.

        Args:
            filename: Output filename (auto-generated if None)

        Returns:
            Path to saved PDF
        """
        if filename is None:
            # Generate filename: R2-[fn]-[cite]-[sp]-[name].pdf
            base_name = self.r1_pdf_path.stem
            # Remove R1- prefix if present
            if base_name.startswith("R1-"):
                base_name = base_name[3:]
            filename = f"R2-{base_name}.pdf"

        output_path = self.output_dir / filename
        self.doc.save(output_path)
        logger.info(f"Saved R2 PDF to {output_path}")

        return output_path

    def close(self):
        """Close the PDF document."""
        self.doc.close()
