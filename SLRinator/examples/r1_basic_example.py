#!/usr/bin/env python3
"""
Basic R1 Validation Example
Demonstrates how to use R1 validation components directly
"""
import sys
from pathlib import Path

# Add SLRinator to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.r1_validation import (
    LLMInterface,
    CitationValidator,
    QuoteVerifier,
    Citation
)


def example_citation_validation():
    """Example: Validate a citation for format compliance."""
    print("="*70)
    print("Example 1: Citation Format Validation")
    print("="*70)

    # Initialize validator
    llm = LLMInterface()
    validator = CitationValidator(llm)

    # Create a citation
    citation = Citation(
        full_text='Alice Corp. v. CLS Bank Int\'l, 573 U.S. 208 (2014)',
        citation_type='case',
        footnote_num=1,
        citation_num=1
    )

    print(f"\nValidating citation: {citation.full_text}")
    print("\nRunning validation...")

    # Validate
    result = validator.validate_citation(citation)

    # Display results
    if result['success']:
        validation = result['validation']
        if validation['is_correct']:
            print("\n✓ Citation is correctly formatted!")
        else:
            print(f"\n✗ Found {len(validation['errors'])} formatting errors:")
            for i, error in enumerate(validation['errors'], 1):
                print(f"\n  Error {i}:")
                print(f"    Type: {error['error_type']}")
                print(f"    Rule: {error.get('rb_rule') or error.get('bluebook_rule')}")
                print(f"    Description: {error['description']}")
                print(f"    Current: {error['current']}")
                print(f"    Correct: {error['correct']}")

        print(f"\nAPI Cost: ${validation.get('gpt_cost', 0):.4f}")
        print(f"Tokens: {validation.get('gpt_tokens', 0)}")
    else:
        print(f"\n✗ Validation failed: {result['error']}")


def example_quote_verification():
    """Example: Verify quote accuracy."""
    print("\n\n" + "="*70)
    print("Example 2: Quote Verification")
    print("="*70)

    verifier = QuoteVerifier()

    quoted_text = "patents are important to innovation"
    source_text = """
    In our view, patents are important to innovation and economic growth.
    They provide incentives for inventors to create new technologies.
    """

    print(f"\nQuoted text: '{quoted_text}'")
    print("\nChecking against source...")

    result = verifier.verify_quote(quoted_text, source_text)

    if result['accurate']:
        print(f"\n✓ Quote verified! (Confidence: {result['confidence']:.0%})")
    else:
        print(f"\n✗ Quote accuracy issues detected:")
        print(f"   Confidence: {result['confidence']:.0%}")
        print(f"   Issues:")
        for issue in result['issues']:
            print(f"     - {issue['severity']}: {issue['description']}")
        print(f"   Suggested action: {result['suggested_action']}")


def example_with_errors():
    """Example: Citation with formatting errors."""
    print("\n\n" + "="*70)
    print("Example 3: Citation with Errors")
    print("="*70)

    llm = LLMInterface()
    validator = CitationValidator(llm)

    # Citation with straight quotes (should be curly)
    citation = Citation(
        full_text='John Doe, Patent Law, 100 HARV. L. REV. 123 (2020) ("patents are important").',
        citation_type='article',
        footnote_num=2,
        citation_num=2
    )

    print(f"\nValidating citation with straight quotes:")
    print(f"  {citation.full_text}")

    result = validator.validate_citation(citation)

    if result['success']:
        validation = result['validation']
        print(f"\nFound {len(validation.get('errors', []))} errors:")
        for error in validation.get('errors', []):
            if error['error_type'] == 'curly_quotes_error':
                print(f"\n  ✗ Curly Quotes Error (Rule {error['rb_rule']})")
                print(f"    {error['description']}")
                print(f"    Current: {error['current']}")
                print(f"    Correct: {error['correct']}")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("R1 Validation Examples")
    print("Stanford Law Review Cite Checking")
    print("="*70)

    try:
        # Example 1: Basic citation validation
        example_citation_validation()

        # Example 2: Quote verification
        example_quote_verification()

        # Example 3: Citation with errors
        example_with_errors()

        print("\n\n" + "="*70)
        print("Examples Complete!")
        print("="*70)
        print("\nFor more information, see:")
        print("  - R1_CITE_CHECKING_README.md")
        print("  - tests/test_r1_validation.py")
        print("\n")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
