#!/usr/bin/env python
"""
R1 Machine: Main entry point

This machine prepares source PDFs for review by:
1. Cleaning PDFs (removing cover pages)
2. Performing metadata redboxing (highlighting citation elements)
3. Preparing R1 PDFs for the validation stage
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared_utils import load_config, setup_logger
from r1_machine.src.pdf_processor import PDFProcessor
from r1_machine.src.redbox_engine import RedboxEngine
from r1_machine.src.pdf_cleaner import PDFCleaner


def main():
    """Main entry point for the R1 Machine."""
    parser = argparse.ArgumentParser(
        description="R1 Machine: Prepare and redbox source PDFs"
    )
    parser.add_argument(
        "--article-id",
        required=True,
        help="Article ID (e.g., '79.1.article_name')",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input directory containing SP PDFs",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for R1 PDFs (defaults to r1_machine/output)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Set up logger
    logger = setup_logger("r1_machine", log_level=args.log_level)
    logger.info(f"Starting R1 Machine for article: {args.article_id}")

    # Load configuration
    config = load_config()

    # Set up directories
    input_dir = Path(args.input)
    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        sys.exit(1)

    output_dir = args.output_dir or config.r1_machine_output_dir
    output_path = Path(output_dir) / args.article_id
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_path}")

    # Initialize components
    pdf_processor = PDFProcessor()
    pdf_cleaner = PDFCleaner()
    redbox_engine = RedboxEngine()

    try:
        # Find all SP PDFs in input directory
        sp_pdfs = list(input_dir.glob("*.pdf"))
        logger.info(f"Found {len(sp_pdfs)} PDFs to process")

        successful = 0
        failed = 0

        for i, pdf_path in enumerate(sp_pdfs, 1):
            logger.info(f"\nProcessing PDF {i}/{len(sp_pdfs)}: {pdf_path.name}")

            try:
                # Step 1: Clean PDF (remove cover pages)
                logger.info("  Step 1: Cleaning PDF...")
                cleaned_pdf = pdf_cleaner.clean(pdf_path)

                # Step 2: Perform metadata redboxing
                logger.info("  Step 2: Performing metadata redboxing...")
                redboxed_pdf = redbox_engine.redbox_metadata(cleaned_pdf)

                # Step 3: Save R1 PDF
                output_filename = f"R1-{pdf_path.stem}.pdf"
                output_file = output_path / output_filename

                with open(output_file, "wb") as f:
                    f.write(redboxed_pdf)

                logger.info(f"  ✓ Saved R1 PDF: {output_file}")
                successful += 1

            except Exception as e:
                logger.error(f"  ✗ Error processing {pdf_path.name}: {e}")
                failed += 1

        # Summary
        logger.info(f"\n{'='*60}")
        logger.info(f"R1 preparation complete!")
        logger.info(f"  Successful: {successful}")
        logger.info(f"  Failed: {failed}")
        logger.info(f"  Total: {len(sp_pdfs)}")
        logger.info(f"  Output directory: {output_path}")
        logger.info(f"{'='*60}")

        sys.exit(0 if failed == 0 else 1)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
