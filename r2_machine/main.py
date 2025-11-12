#!/usr/bin/env python
"""
R2 Machine: Main entry point

This machine performs LLM-powered validation of citations including:
1. Bluebook/Redbook formatting verification
2. Proposition support checking
3. Quote accuracy verification
4. Generation of annotated R2 documents
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared_utils import load_config, setup_logger
from r2_machine.src.pdf_processor import R2PDFProcessor
from r2_machine.src.citation_validator import CitationValidator
from r2_machine.src.support_checker import SupportChecker
from r2_machine.src.quote_verifier import QuoteVerifier
from r2_machine.src.r2_generator import R2Generator


def main():
    """Main entry point for the R2 Machine."""
    parser = argparse.ArgumentParser(
        description="R2 Machine: LLM-powered citation validation"
    )
    parser.add_argument(
        "--article-id",
        required=True,
        help="Article ID (e.g., '79.1.article_name')",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input directory containing R1 PDFs",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for R2 PDFs (defaults to r2_machine/output)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4",
        choices=["gpt-4", "gpt-4-turbo", "claude-3-opus", "claude-3-sonnet"],
        help="LLM model to use for validation",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Set up logger
    logger = setup_logger("r2_machine", log_level=args.log_level)
    logger.info(f"Starting R2 Machine for article: {args.article_id}")
    logger.info(f"Using LLM model: {args.model}")

    # Load configuration
    config = load_config()

    # Set up directories
    input_dir = Path(args.input)
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        sys.exit(1)

    output_dir = args.output_dir or config.r2_machine_output_dir
    output_path = Path(output_dir) / args.article_id
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_path}")

    # Initialize components
    pdf_processor = R2PDFProcessor()
    citation_validator = CitationValidator(model=args.model)
    support_checker = SupportChecker(model=args.model)
    quote_verifier = QuoteVerifier()
    r2_generator = R2Generator(output_path)

    try:
        # Find all R1 PDFs in input directory
        r1_pdfs = list(input_dir.glob("R1-*.pdf"))
        logger.info(f"Found {len(r1_pdfs)} R1 PDFs to validate")

        # Track results
        results = {
            "timestamp": datetime.now().isoformat(),
            "article_id": args.article_id,
            "model": args.model,
            "validations": [],
        }

        for i, pdf_path in enumerate(r1_pdfs, 1):
            logger.info(f"\nValidating {i}/{len(r1_pdfs)}: {pdf_path.name}")

            try:
                # Step 1: Extract text and metadata from R1 PDF
                logger.info("  Step 1: Extracting content...")
                content = pdf_processor.extract_content(pdf_path)

                # Step 2: Validate citation formatting
                logger.info("  Step 2: Validating Bluebook formatting...")
                format_result = citation_validator.validate(content["citation_text"])

                # Step 3: Check proposition support
                logger.info("  Step 3: Checking proposition support...")
                support_result = support_checker.check_support(
                    proposition=content["proposition"],
                    source_text=content["source_text"],
                )

                # Step 4: Verify quotes
                logger.info("  Step 4: Verifying quoted text...")
                quote_result = quote_verifier.verify_quotes(
                    article_quotes=content["quotes"],
                    source_text=content["source_text"],
                )

                # Compile validation result
                validation = {
                    "source_number": pdf_path.stem,
                    "format_valid": format_result["valid"],
                    "format_errors": format_result.get("errors", []),
                    "format_suggestions": format_result.get("suggestions", []),
                    "support_valid": support_result["supported"],
                    "support_explanation": support_result.get("explanation", ""),
                    "support_confidence": support_result.get("confidence", 0),
                    "quotes_accurate": quote_result["all_accurate"],
                    "quote_errors": quote_result.get("errors", []),
                    "requires_review": (
                        not format_result["valid"]
                        or not support_result["supported"]
                        or not quote_result["all_accurate"]
                    ),
                }

                results["validations"].append(validation)

                # Generate R2 PDF with annotations
                logger.info("  Step 5: Generating R2 PDF...")
                r2_generator.generate_r2_pdf(pdf_path, validation)

                if validation["requires_review"]:
                    logger.warning(f"  ⚠️  Requires human review")
                else:
                    logger.info(f"  ✓ Validation passed")

            except Exception as e:
                logger.error(f"  ✗ Error validating {pdf_path.name}: {e}")
                results["validations"].append({
                    "source_number": pdf_path.stem,
                    "error": str(e),
                    "requires_review": True,
                })

        # Generate summary report
        logger.info("\nGenerating summary report...")
        r2_generator.generate_report(results)

        # Summary
        total = len(results["validations"])
        requires_review = sum(1 for v in results["validations"] if v.get("requires_review", False))
        passed = total - requires_review

        logger.info(f"\n{'='*60}")
        logger.info(f"R2 validation complete!")
        logger.info(f"  Passed: {passed}")
        logger.info(f"  Requires Review: {requires_review}")
        logger.info(f"  Total: {total}")
        logger.info(f"  Output directory: {output_path}")
        logger.info(f"{'='*60}")

        sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
