"""
R1 Workflow with Cite Checking
Complete R1 (sourcepull + validation) workflow for Stanford Law Review
"""
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import SLRinator components
from src.processors.footnote_extractor import extract_footnotes_from_docx
from src.core.gpt_citation_parser import parse_citations_with_gpt
from src.retrievers.unified_retriever import SourceRetriever

# Import R1 validation components
from src.r1_validation import (
    LLMInterface,
    CitationValidator,
    QuoteVerifier,
    SupportChecker,
    ValidationReporter,
    Citation
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class R1Workflow:
    """Complete R1 workflow: sourcepull + cite checking validation."""

    def __init__(self, enable_validation: bool = True, enable_quote_check: bool = True,
                 enable_support_check: bool = False):
        """
        Initialize R1 workflow.

        Args:
            enable_validation: Enable citation format validation
            enable_quote_check: Enable quote accuracy verification
            enable_support_check: Enable proposition support checking
        """
        self.enable_validation = enable_validation
        self.enable_quote_check = enable_quote_check
        self.enable_support_check = enable_support_check

        # Initialize components
        self.retriever = SourceRetriever()
        self.reporter = ValidationReporter()

        # Initialize validation components
        if enable_validation or enable_support_check:
            self.llm = LLMInterface()
            self.citation_validator = CitationValidator(self.llm) if enable_validation else None
            self.support_checker = SupportChecker(self.llm) if enable_support_check else None

        if enable_quote_check:
            self.quote_verifier = QuoteVerifier()

        logger.info(f"R1 Workflow initialized (validation={enable_validation}, quotes={enable_quote_check}, support={enable_support_check})")

    def process_document(self, docx_path: str, footnote_range: str = None,
                        output_dir: str = None) -> Dict[str, Any]:
        """
        Process entire document through R1 workflow.

        Args:
            docx_path: Path to Word document
            footnote_range: Optional range (e.g., "1-50" or "1-50,100-150")
            output_dir: Output directory for reports and PDFs

        Returns:
            Complete R1 report
        """
        logger.info("="*70)
        logger.info("         R1 WORKFLOW: SOURCEPULL + CITE CHECKING")
        logger.info("              Stanford Law Review Automation")
        logger.info("="*70)
        logger.info(f"Processing: {docx_path}")

        # Step 1: Extract footnotes
        logger.info("\n[STEP 1] Extracting footnotes from document...")
        footnotes = extract_footnotes_from_docx(docx_path)
        logger.info(f"  Extracted {len(footnotes)} footnotes")

        # Filter by range if specified
        if footnote_range:
            footnotes = self._filter_footnotes_by_range(footnotes, footnote_range)
            logger.info(f"  Filtered to {len(footnotes)} footnotes in range {footnote_range}")

        # Step 2: Parse citations
        logger.info("\n[STEP 2] Parsing citations...")
        all_citations = []
        for fn_num, fn_text in footnotes.items():
            parsed = parse_citations_with_gpt(fn_text)
            for cit in parsed:
                cit['footnote_num'] = fn_num
                all_citations.append(cit)
        logger.info(f"  Found {len(all_citations)} citations across {len(footnotes)} footnotes")

        # Step 3: Process each citation (retrieve + validate)
        logger.info("\n[STEP 3] Processing citations (retrieval + validation)...")
        results = []
        for i, cit_data in enumerate(all_citations, 1):
            logger.info(f"\n  [{i}/{len(all_citations)}] Processing citation...")
            result = self._process_citation(cit_data, i)
            results.append(result)

        # Step 4: Generate reports
        logger.info("\n[STEP 4] Generating reports...")
        report = self.reporter.generate_report(
            citations=results,
            metadata={
                "document_path": str(docx_path),
                "footnote_range": footnote_range or "all",
                "validation_enabled": self.enable_validation,
                "quote_check_enabled": self.enable_quote_check,
                "support_check_enabled": self.enable_support_check
            }
        )

        # Save reports
        json_path = self.reporter.save_report(report)
        html_path = self.reporter.generate_html_report(report)

        logger.info(f"\n  JSON report: {json_path}")
        logger.info(f"  HTML report: {html_path}")

        # Print summary
        self._print_summary(report)

        return report

    def _process_citation(self, cit_data: Dict, citation_num: int) -> Dict[str, Any]:
        """Process a single citation: retrieve + validate."""
        citation_text = cit_data.get('text', '')
        citation_type = cit_data.get('type', 'unknown')
        footnote_num = cit_data.get('footnote_num', 0)

        logger.info(f"    Citation: {citation_text[:80]}...")

        result = {
            "citation_num": citation_num,
            "footnote_num": footnote_num,
            "text": citation_text,
            "type": citation_type,
            "retrieval_status": "not_attempted",
            "pdf_path": None,
            "validation_result": None,
            "quote_verification": None,
            "support_check": None,
            "needs_human_review": False,
            "review_reasons": []
        }

        # Pre-retrieval validation (citation format)
        if self.enable_validation and self.citation_validator:
            logger.info("    [Validation] Checking citation format...")
            cit_obj = Citation(
                full_text=citation_text,
                citation_type=citation_type,
                footnote_num=footnote_num,
                citation_num=citation_num
            )
            validation_result = self.citation_validator.validate_citation(cit_obj)
            result['validation_result'] = validation_result

            if validation_result.get('success'):
                val = validation_result.get('validation', {})
                if not val.get('is_correct'):
                    logger.warning(f"    [Validation] Found {len(val.get('errors', []))} formatting errors")
                    result['needs_human_review'] = True
                    result['review_reasons'].append("citation_format_error")
                    # Add to review queue
                    for error in val.get('errors', []):
                        self.reporter.add_to_review_queue(
                            citation_num=citation_num,
                            footnote_num=footnote_num,
                            issue="Citation format error",
                            severity="minor",
                            details=error.get('description', '')
                        )
                else:
                    logger.info("    [Validation] Citation format OK")

        # Retrieval
        logger.info("    [Retrieval] Attempting to retrieve source...")
        try:
            pdf_path = self.retriever.retrieve_source(citation_num, citation_text)
            if pdf_path and Path(pdf_path).exists():
                result['retrieval_status'] = "success"
                result['pdf_path'] = str(pdf_path)
                logger.info(f"    [Retrieval] ✓ Retrieved: {Path(pdf_path).name}")
            else:
                result['retrieval_status'] = "failed"
                logger.warning("    [Retrieval] ✗ Could not retrieve source")
                result['needs_human_review'] = True
                result['review_reasons'].append("retrieval_failed")
        except Exception as e:
            result['retrieval_status'] = "error"
            result['retrieval_error'] = str(e)
            logger.error(f"    [Retrieval] Error: {e}")

        # Post-retrieval validation (quotes, support)
        if result['retrieval_status'] == 'success' and result['pdf_path']:
            # Quote verification
            if self.enable_quote_check and self.quote_verifier:
                quotes = self._extract_quotes(citation_text)
                if quotes:
                    logger.info("    [Quote Check] Verifying quotes...")
                    # Extract text from PDF
                    try:
                        source_text = self._extract_pdf_text(result['pdf_path'])
                        for quote in quotes:
                            quote_result = self.quote_verifier.verify_quote(quote, source_text)
                            result['quote_verification'] = quote_result
                            if not quote_result.get('accurate'):
                                logger.warning("    [Quote Check] Quote accuracy issue detected")
                                result['needs_human_review'] = True
                                result['review_reasons'].append("quote_accuracy_issue")
                                self.reporter.add_to_review_queue(
                                    citation_num=citation_num,
                                    footnote_num=footnote_num,
                                    issue="Quote accuracy issue",
                                    severity="major",
                                    details=f"Confidence: {quote_result.get('confidence', 0):.2f}"
                                )
                            else:
                                logger.info("    [Quote Check] ✓ Quote verified")
                    except Exception as e:
                        logger.error(f"    [Quote Check] Error: {e}")

            # Support checking (if enabled and proposition available)
            if self.enable_support_check and self.support_checker:
                proposition = self._extract_proposition(cit_data)
                if proposition:
                    logger.info("    [Support Check] Checking proposition support...")
                    try:
                        source_text = self._extract_pdf_text(result['pdf_path'])
                        support_result = self.support_checker.check_support(
                            proposition=proposition,
                            source_text=source_text,
                            citation_text=citation_text
                        )
                        result['support_check'] = support_result
                        if support_result.get('success'):
                            support_level = support_result.get('analysis', {}).get('support_level')
                            if support_level != 'yes':
                                logger.warning(f"    [Support Check] Support level: {support_level}")
                                result['needs_human_review'] = True
                                result['review_reasons'].append("support_questionable")
                            else:
                                logger.info("    [Support Check] ✓ Support confirmed")
                    except Exception as e:
                        logger.error(f"    [Support Check] Error: {e}")

        return result

    def _filter_footnotes_by_range(self, footnotes: Dict, range_str: str) -> Dict:
        """Filter footnotes by range string (e.g., '1-50,100-150')."""
        footnote_numbers = set()
        for part in range_str.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                footnote_numbers.update(range(start, end + 1))
            else:
                footnote_numbers.add(int(part))

        return {k: v for k, v in footnotes.items() if k in footnote_numbers}

    def _extract_quotes(self, citation_text: str) -> List[str]:
        """Extract quoted text from citation."""
        import re
        # Find text in quotes
        quotes = re.findall(r'"([^"]+)"', citation_text)
        return quotes

    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF."""
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text

    def _extract_proposition(self, cit_data: Dict) -> str:
        """Extract proposition from citation data (if available)."""
        # This would require main text analysis - placeholder for now
        return None

    def _print_summary(self, report: Dict):
        """Print summary statistics."""
        summary = report['validation_summary']
        costs = report['cost_analysis']
        queue = report.get('human_review_queue', [])

        logger.info("\n" + "="*70)
        logger.info("                        SUMMARY")
        logger.info("="*70)
        logger.info(f"Total Citations: {summary['total_citations']}")
        logger.info(f"  Validated: {summary['citations_validated']}")
        logger.info(f"  Correct: {summary['citations_correct']}")
        logger.info(f"  With Errors: {summary['citations_with_errors']}")
        logger.info(f"  Accuracy: {summary['accuracy_rate']}")
        logger.info("")
        logger.info(f"Quote Checks: {summary['quotes_checked']}")
        logger.info(f"  Accurate: {summary['quotes_accurate']}")
        logger.info(f"  Accuracy: {summary['quote_accuracy_rate']}")
        logger.info("")
        logger.info(f"Cost: {costs.get('total_cost', '$0.00')} ({costs.get('total_tokens', 0):,} tokens)")
        logger.info(f"  Avg per citation: {costs.get('avg_cost_per_citation', '$0.00')}")
        logger.info("")
        logger.info(f"Human Review Queue: {len(queue)} items")
        logger.info("="*70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="R1 Workflow with Cite Checking")
    parser.add_argument("document", help="Path to Word document")
    parser.add_argument("--footnotes", help="Footnote range (e.g., '1-50' or '1-50,100-150')")
    parser.add_argument("--no-validation", action="store_true", help="Disable citation validation")
    parser.add_argument("--no-quotes", action="store_true", help="Disable quote checking")
    parser.add_argument("--enable-support", action="store_true", help="Enable support checking")
    parser.add_argument("--output", help="Output directory")

    args = parser.parse_args()

    # Create workflow
    workflow = R1Workflow(
        enable_validation=not args.no_validation,
        enable_quote_check=not args.no_quotes,
        enable_support_check=args.enable_support
    )

    # Process document
    workflow.process_document(
        docx_path=args.document,
        footnote_range=args.footnotes,
        output_dir=args.output
    )


if __name__ == "__main__":
    main()
