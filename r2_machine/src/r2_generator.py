"""Generate R2 output documents."""

import json
from pathlib import Path
from typing import Dict, Any
import fitz

from shared_utils.logger import get_logger

logger = get_logger(__name__)


class R2Generator:
    """Generate R2 PDFs and reports."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def generate_r2_pdf(self, r1_pdf_path: Path, validation: Dict[str, Any]) -> None:
        """Generate annotated R2 PDF from R1 PDF with validation results."""
        try:
            doc = fitz.open(r1_pdf_path)
            
            # Add validation annotations to first page
            page = doc[0]
            
            # Add validation status
            text = f"Validation: {'PASSED' if not validation['requires_review'] else 'REVIEW REQUIRED'}"
            page.insert_text((50, 50), text, fontsize=12, color=(1, 0, 0))
            
            # Save R2 PDF
            output_name = r1_pdf_path.name.replace("R1-", "R2-")
            output_path = self.output_dir / output_name
            doc.save(output_path)
            doc.close()
            
            logger.info(f"Generated R2 PDF: {output_path}")

        except Exception as e:
            logger.error(f"Failed to generate R2 PDF: {e}")

    def generate_report(self, results: Dict[str, Any]) -> None:
        """Generate summary report."""
        report_path = self.output_dir / "validation_report.json"
        
        with open(report_path, "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Generated report: {report_path}")
