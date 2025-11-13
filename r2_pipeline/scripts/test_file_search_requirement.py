#!/usr/bin/env python3
"""
Test that the assistant actually uses File Search and quotes the Bluebook.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from src.llm_interface import LLMInterface
from src.citation_parser import Citation
from src.citation_validator import CitationValidator
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Test that File Search is actually being used."""
    logger.info("Testing File Search requirement...")

    # Initialize LLM interface with vector store
    llm = LLMInterface(use_vector_store=True)

    if not llm.assistant_id:
        logger.error("No assistant found! Run setup_vector_store.py first.")
        return

    logger.info(f"Using assistant: {llm.assistant_id}")

    # Test citation that needs supra rule
    test_citation = Citation(
        full_text='Crusey, *supra* note 21 at 483.',
        footnote_num=80,
        citation_num=1,
        type="secondary_source"
    )

    # Initialize validator
    validator = CitationValidator(llm)

    logger.info(f"\n{'='*60}")
    logger.info(f"Testing Citation: {test_citation.full_text}")
    logger.info(f"{'='*60}")

    result = validator.validate_citation(test_citation)

    if result["success"]:
        validation = result["validation"]
        logger.info(f"\n✓ Validation successful!")
        logger.info(f"  Is correct: {validation.get('is_correct', 'N/A')}")
        logger.info(f"  Overall confidence: {validation.get('overall_confidence', 'N/A')}")

        # Check for file search confirmation
        if 'file_search_confirmation' in validation:
            logger.info(f"\n✓ FILE SEARCH CONFIRMATION:")
            logger.info(f"  {validation['file_search_confirmation']}")
        else:
            logger.warning(f"\n⚠ NO FILE SEARCH CONFIRMATION FOUND!")

        logger.info(f"\n  Errors: {len(validation.get('errors', []))} found")
        if validation.get('errors'):
            for i, error in enumerate(validation['errors'], 1):
                logger.info(f"\n    Error #{i}:")
                logger.info(f"      Type: {error.get('error_type', 'N/A')}")
                logger.info(f"      Bluebook Rule: {error.get('bluebook_rule', 'N/A')}")

                # Check for rule text quote
                if 'rule_text_quote' in error:
                    logger.info(f"      ✓ Rule Quote: {error['rule_text_quote'][:150]}...")
                else:
                    logger.warning(f"      ⚠ NO RULE QUOTE FOUND (assistant may not have searched file)")

                logger.info(f"      Confidence: {error.get('confidence', 'N/A')}")
                logger.info(f"      Description: {error.get('description', 'N/A')}")

        # Print full JSON for debugging
        logger.info(f"\n{'='*60}")
        logger.info(f"FULL VALIDATION RESPONSE:")
        logger.info(f"{'='*60}")
        print(json.dumps(validation, indent=2))

    else:
        logger.error(f"✗ Validation failed: {result['error']}")


if __name__ == "__main__":
    main()
