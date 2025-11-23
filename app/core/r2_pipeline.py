"""
R2 Pipeline - Citation validation and verification
"""
import sys
from pathlib import Path
import logging
from typing import List, Dict, Callable, Optional
from dataclasses import dataclass
import json
import fitz
from docx import Document

# Add SLRinator to path
slrinator_path = Path(__file__).parent.parent.parent / "SLRinator"
sys.path.insert(0, str(slrinator_path))

from src.processors.footnote_extractor import FootnoteExtractor
from src.core.retrieval_framework import SourceClassifier

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of citation validation"""
    footnote_num: int
    citation_text: str
    format_issues: List[str]
    support_issues: List[str]
    quote_issues: List[str]
    suggested_changes: str
    confidence_score: int
    requires_review: bool


class R2Pipeline:
    """
    R2 Validation Pipeline
    Validates citations using LLM for format and support checking
    """

    def __init__(self, sheets_client, drive_client, llm_client, cache_dir: str = None):
        """
        Initialize R2 Pipeline

        Args:
            sheets_client: Google Sheets client
            drive_client: Google Drive client
            llm_client: LLM client for validation
            cache_dir: Directory for caching
        """
        self.sheets = sheets_client
        self.drive = drive_client
        self.llm = llm_client
        self.cache_dir = Path(cache_dir or "cache/r2")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.footnote_extractor = FootnoteExtractor()
        self.classifier = SourceClassifier()

        # Load prompts
        prompts_dir = Path(__file__).parent.parent / "resources" / "prompts"
        self.format_prompt = (prompts_dir / "citation_format.txt").read_text()
        self.support_prompt = (prompts_dir / "support_check.txt").read_text()

        # Load Bluebook rules
        rules_file = Path(__file__).parent.parent / "resources" / "bluebook_rules.json"
        with open(rules_file, 'r') as f:
            self.bluebook_rules = json.load(f)

    def process_article(self, article_id: str, article_doc_path: str,
                       progress_callback: Optional[Callable[[int, int, str], None]] = None):
        """
        Run R2 validation for an article

        Args:
            article_id: Article identifier
            article_doc_path: Path to article Word document
            progress_callback: Progress callback function

        Returns:
            Dict with validation results
        """
        logger.info(f"Starting R2 validation for article: {article_id}")

        # Extract footnotes from Word doc
        footnotes = self.footnote_extractor.extract_from_docx(article_doc_path)
        total = len(footnotes)

        logger.info(f"Extracted {total} footnotes from article")

        all_results = []
        sources = self.sheets.get_sources_for_article(article_id)

        # Create mapping of footnote numbers to sources
        source_map = {int(s['footnote_num']): s for s in sources if s.get('footnote_num')}

        for i, (fn_num, fn_text) in enumerate(footnotes.items()):
            if progress_callback:
                progress_callback(i, total, f"Validating footnote {fn_num}...")

            try:
                # Parse citations from footnote
                citations = self._parse_citations_from_footnote(fn_text)

                for citation in citations:
                    # Validate each citation
                    result = self.validate_citation(
                        citation,
                        fn_num,
                        fn_text,
                        source_map.get(fn_num)
                    )
                    all_results.append(result)

            except Exception as e:
                logger.error(f"Error validating footnote {fn_num}: {e}", exc_info=True)

        logger.info(f"Validation complete: {len(all_results)} citations checked")

        # Generate outputs
        pdf_files = self.generate_r2_pdfs(all_results, article_id)
        word_doc = self.generate_word_changes(all_results, article_doc_path, article_id)
        html_report = self.generate_review_queue_html(all_results, article_id)

        # Upload to Drive
        upload_results = self.drive.upload_r2_package(
            article_id,
            pdf_files,
            word_doc,
            html_report
        )

        # Update Sheet
        self.sheets.update_article_stage(article_id, 'r2_complete')

        return {
            'citations_checked': len(all_results),
            'issues_found': len([r for r in all_results if r.requires_review]),
            'upload_results': upload_results,
            'results': all_results
        }

    def validate_citation(self, citation: str, footnote_num: int,
                         footnote_text: str, source: Dict = None) -> ValidationResult:
        """
        Validate a single citation

        Args:
            citation: Citation text
            footnote_num: Footnote number
            footnote_text: Full footnote text (for context/proposition)
            source: Source dict from Sheets (if available)

        Returns:
            ValidationResult
        """
        format_issues = []
        support_issues = []
        quote_issues = []
        suggested_changes = ""
        confidence_score = 100

        try:
            # Check format using LLM
            format_result = self.llm.check_format(
                citation,
                self.bluebook_rules,
                self.format_prompt
            )
            format_issues = format_result.get('issues', [])
            suggested_changes = format_result.get('suggestion', '')

            # Check support if we have the source PDF
            if source and source.get('r1_drive_link'):
                # Download R1 PDF
                r1_pdf_path = self.drive.download_file(file_link=source['r1_drive_link'])

                # Extract text from PDF
                source_text = self._extract_pdf_text(r1_pdf_path)

                # Extract proposition from footnote
                proposition = self._extract_proposition(footnote_text, citation)

                # Check support using LLM
                support_result = self.llm.check_support(
                    proposition,
                    source_text,
                    citation,
                    self.support_prompt
                )

                support_issues = support_result.get('issues', [])
                confidence_score = support_result.get('confidence', 50)

                # Check quotes if present
                quotes = self._extract_quotes(citation)
                for quote in quotes:
                    if quote not in source_text:
                        quote_issues.append(f"Quote not found verbatim: {quote[:50]}...")

                # Clean up
                Path(r1_pdf_path).unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"Error validating citation {citation[:50]}: {e}", exc_info=True)
            format_issues.append(f"Validation error: {str(e)}")

        requires_review = (
            len(format_issues) > 0 or
            len(support_issues) > 0 or
            len(quote_issues) > 0 or
            confidence_score < 70
        )

        return ValidationResult(
            footnote_num=footnote_num,
            citation_text=citation,
            format_issues=format_issues,
            support_issues=support_issues,
            quote_issues=quote_issues,
            suggested_changes=suggested_changes,
            confidence_score=confidence_score,
            requires_review=requires_review
        )

    def _parse_citations_from_footnote(self, footnote_text: str) -> List[str]:
        """Extract individual citations from footnote text"""
        # Simple split by semicolon - works for most cases
        # NOTE: Future enhancement - integrate SLRinator citation parser for more complex cases
        parts = footnote_text.split(';')
        return [p.strip() for p in parts if len(p.strip()) > 10]

    def _extract_pdf_text(self, pdf_path: str, max_pages: int = 10) -> str:
        """Extract text from first few pages of PDF"""
        doc = fitz.open(pdf_path)
        text = ""

        for page_num in range(min(len(doc), max_pages)):
            page = doc[page_num]
            text += page.get_text()

        doc.close()
        return text

    def _extract_proposition(self, footnote_text: str, citation: str) -> str:
        """Extract the proposition being supported by this citation"""
        # Simple: return text before the citation
        # NOTE: Future enhancement - use NLP to extract semantic proposition
        citation_pos = footnote_text.find(citation)
        if citation_pos > 0:
            return footnote_text[:citation_pos].strip()
        return footnote_text[:100]  # First 100 chars as fallback

    def _extract_quotes(self, citation: str) -> List[str]:
        """Extract quoted text from citation"""
        import re
        quotes = re.findall(r'"([^"]+)"', citation)
        quotes += re.findall(r'"([^"]+)"', citation)  # Curly quotes
        return quotes

    def generate_r2_pdfs(self, results: List[ValidationResult], article_id: str) -> List[str]:
        """Generate annotated R2 PDFs with validation comments"""
        pdf_files = []
        # NOTE: PDF annotation feature - implement when needed for workflow
        # Current workflow uses review queue HTML instead
        logger.debug("PDF annotation not yet implemented - using HTML review queue")
        return pdf_files

    def generate_word_changes(self, results: List[ValidationResult],
                             article_doc_path: str, article_id: str) -> str:
        """Generate Word doc with tracked changes"""
        output_path = self.cache_dir / f"{article_id}_R2_changes.docx"

        # Load document
        doc = Document(article_doc_path)

        # NOTE: Tracked changes feature - requires python-docx-template or similar
        # Current version creates copy for manual review
        logger.debug("Tracked changes not yet implemented - creating document copy")
        doc.save(output_path)

        return str(output_path)

    def generate_review_queue_html(self, results: List[ValidationResult],
                                   article_id: str) -> str:
        """Generate HTML report of items requiring review"""
        output_path = self.cache_dir / f"{article_id}_review_queue.html"

        review_items = [r for r in results if r.requires_review]

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>R2 Review Queue - {article_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .issue {{ border: 1px solid #ccc; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .format {{ color: #d9534f; }}
        .support {{ color: #f0ad4e; }}
        .quote {{ color: #5bc0de; }}
        .confidence {{ font-weight: bold; }}
        .high {{ color: #5cb85c; }}
        .medium {{ color: #f0ad4e; }}
        .low {{ color: #d9534f; }}
    </style>
</head>
<body>
    <h1>R2 Review Queue for {article_id}</h1>
    <p>{len(review_items)} citations require human review.</p>
"""

        for item in review_items:
            confidence_class = 'high' if item.confidence_score >= 70 else 'medium' if item.confidence_score >= 50 else 'low'

            html += f"""
    <div class="issue">
        <h3>Footnote {item.footnote_num}</h3>
        <p><strong>Citation:</strong> {item.citation_text}</p>
        <p class="confidence {confidence_class}"><strong>Confidence Score:</strong> {item.confidence_score}/100</p>
"""
            if item.format_issues:
                html += f"<p class='format'><strong>Format Issues:</strong> {'; '.join(item.format_issues)}</p>"
            if item.support_issues:
                html += f"<p class='support'><strong>Support Issues:</strong> {'; '.join(item.support_issues)}</p>"
            if item.quote_issues:
                html += f"<p class='quote'><strong>Quote Issues:</strong> {'; '.join(item.quote_issues)}</p>"
            if item.suggested_changes:
                html += f"<p><strong>Suggested:</strong> {item.suggested_changes}</p>"

            html += "    </div>"

        html += """
</body>
</html>"""

        output_path.write_text(html)
        return str(output_path)
