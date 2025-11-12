#!/usr/bin/env python
"""
Sourcepull Machine: Main entry point

This machine retrieves raw, format-preserving source files based on citations
from the master spreadsheet.
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared_utils import load_config, setup_logger
from sp_machine.src.spreadsheet_parser import SpreadsheetParser
from sp_machine.src.citation_parser import CitationParser
from sp_machine.src.source_puller import SourcePuller


def main():
    """Main entry point for the Sourcepull Machine."""
    parser = argparse.ArgumentParser(
        description="Sourcepull Machine: Retrieve source files for citations"
    )
    parser.add_argument(
        "--article-id",
        required=True,
        help="Article ID (e.g., '79.1.article_name')",
    )
    parser.add_argument(
        "--spreadsheet-id",
        help="Google Sheets ID (defaults to env var GOOGLE_SHEETS_ID)",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for source PDFs (defaults to sp_machine/output)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )

    args = parser.parse_args()

    # Set up logger
    logger = setup_logger("sp_machine", log_level=args.log_level)
    logger.info(f"Starting Sourcepull Machine for article: {args.article_id}")

    # Load configuration
    config = load_config()

    # Set output directory
    output_dir = args.output_dir or config.sp_machine_output_dir
    output_path = Path(output_dir) / args.article_id
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_path}")

    # Initialize components
    spreadsheet_id = args.spreadsheet_id or config.google_sheets_id
    if not spreadsheet_id:
        logger.error("No spreadsheet ID provided")
        sys.exit(1)

    spreadsheet_parser = SpreadsheetParser(spreadsheet_id)
    citation_parser = CitationParser()
    source_puller = SourcePuller(output_dir=str(output_path))

    try:
        # Parse citations from spreadsheet
        logger.info("Parsing citations from spreadsheet...")
        citations = spreadsheet_parser.get_citations_for_article(args.article_id)
        logger.info(f"Found {len(citations)} citations")

        # Process each citation
        successful = 0
        failed = 0

        for i, citation_row in enumerate(citations, 1):
            logger.info(f"\nProcessing citation {i}/{len(citations)}")

            try:
                # Parse citation
                citation_text = citation_row.get("citation_text", "")
                citation_data = citation_parser.parse(citation_text)
                logger.info(f"  Citation: {citation_data.get('title', 'Unknown')}")

                # Pull source
                result = source_puller.pull_source(citation_data, citation_row)

                if result["success"]:
                    logger.info(f"  ✓ Successfully retrieved: {result['file_path']}")
                    successful += 1
                else:
                    logger.warning(f"  ✗ Failed: {result['error']}")
                    failed += 1

            except Exception as e:
                logger.error(f"  Error processing citation: {e}")
                failed += 1

        # Summary
        logger.info(f"\n{'='*60}")
        logger.info(f"Sourcepull complete!")
        logger.info(f"  Successful: {successful}")
        logger.info(f"  Failed: {failed}")
        logger.info(f"  Total: {len(citations)}")
        logger.info(f"  Output directory: {output_path}")
        logger.info(f"{'='*60}")

        sys.exit(0 if failed == 0 else 1)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
