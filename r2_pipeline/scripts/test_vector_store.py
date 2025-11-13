#!/usr/bin/env python3
"""
Test script to verify Bluebook vector store integration.
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Test the vector store integration."""
    logger.info("Testing Bluebook vector store integration...")

    # Initialize LLM interface with vector store
    llm = LLMInterface(use_vector_store=True)

    if not llm.assistant_id:
        logger.error("No assistant found! Run setup_vector_store.py first.")
        return

    logger.info(f"Using assistant: {llm.assistant_id}")

    # Test 1: Citation with error
    test_citation_1 = Citation(
        full_text='Crusey, supra note 21 at 483 ("Test quote")',
        footnote_num=80,
        citation_num=1,
        type="secondary_source"
    )

    # Test 2: Correct citation
    test_citation_2 = Citation(
        full_text='Crusey, supra note 21, at 483.',
        footnote_num=80,
        citation_num=2,
        type="secondary_source"
    )

    # Initialize validator
    validator = CitationValidator(llm)

    # Test 1: Citation with error
    logger.info(f"\n" + "="*60)
    logger.info(f"TEST 1: Citation with formatting error")
    logger.info(f"="*60)
    logger.info(f"Citation: {test_citation_1.full_text}")

    result = validator.validate_citation(test_citation_1)

    if result["success"]:
        validation = result["validation"]
        logger.info(f"\n✓ Validation successful!")
        logger.info(f"  Is correct: {validation.get('is_correct', 'N/A')}")
        logger.info(f"  Overall confidence: {validation.get('overall_confidence', validation.get('confidence', 'N/A'))}")
        logger.info(f"  Errors: {len(validation.get('errors', []))} found")
        if validation.get('errors'):
            for i, error in enumerate(validation['errors'], 1):
                logger.info(f"    Error #{i}:")
                logger.info(f"      Type: {error.get('error_type', 'N/A')}")
                logger.info(f"      Description: {error.get('description', 'Unknown error')}")
                logger.info(f"      Bluebook Rule: {error.get('bluebook_rule', 'N/A')}")
                logger.info(f"      Confidence: {error.get('confidence', 'N/A')}")
                logger.info(f"      Current: '{error.get('current', 'N/A')}'")
                logger.info(f"      Correct: '{error.get('correct', 'N/A')}'")
        logger.info(f"  Corrected: {validation.get('corrected_version', 'N/A')}")
        logger.info(f"  Notes: {validation.get('notes', 'None')}")
        logger.info(f"  Tokens: {validation.get('gpt_tokens', 0)}")
        logger.info(f"  Cost: ${validation.get('gpt_cost', 0):.4f}")
    else:
        logger.error(f"✗ Validation failed: {result['error']}")

    # Test 2: Correct citation
    logger.info(f"\n" + "="*60)
    logger.info(f"TEST 2: Correctly formatted citation")
    logger.info(f"="*60)
    logger.info(f"Citation: {test_citation_2.full_text}")

    result2 = validator.validate_citation(test_citation_2)

    if result2["success"]:
        validation2 = result2["validation"]
        logger.info(f"\n✓ Validation successful!")
        logger.info(f"  Is correct: {validation2.get('is_correct', 'N/A')}")
        logger.info(f"  Overall confidence: {validation2.get('overall_confidence', validation2.get('confidence', 'N/A'))}")
        logger.info(f"  Errors: {len(validation2.get('errors', []))} found")
        if validation2.get('errors'):
            for i, error in enumerate(validation2['errors'], 1):
                logger.info(f"    Error #{i}:")
                logger.info(f"      Type: {error.get('error_type', 'N/A')}")
                logger.info(f"      Description: {error.get('description', 'Unknown error')}")
                logger.info(f"      Bluebook Rule: {error.get('bluebook_rule', 'N/A')}")
                logger.info(f"      Confidence: {error.get('confidence', 'N/A')}")
                logger.info(f"      Current: '{error.get('current', 'N/A')}'")
                logger.info(f"      Correct: '{error.get('correct', 'N/A')}'")
        else:
            logger.info(f"  ✓ No formatting errors found!")
        logger.info(f"  Corrected: {validation2.get('corrected_version', 'N/A')}")
        logger.info(f"  Notes: {validation2.get('notes', 'None')}")
        logger.info(f"  Tokens: {validation2.get('gpt_tokens', 0)}")
        logger.info(f"  Cost: ${validation2.get('gpt_cost', 0):.4f}")
    else:
        logger.error(f"✗ Validation failed: {result2['error']}")

    # Show overall stats
    stats = llm.get_stats()
    logger.info(f"\n" + "="*60)
    logger.info(f"=== Overall Stats ===")
    logger.info(f"="*60)
    logger.info(f"Total calls: {stats['total_calls']}")
    logger.info(f"Total tokens: {stats['total_tokens']}")
    logger.info(f"Total cost: ${stats['total_cost']:.4f}")


if __name__ == "__main__":
    main()
