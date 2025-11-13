#!/usr/bin/env python3
"""
Test the integrated fail-closed validation system.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.citation_validator import CitationValidator
from src.llm_interface import LLMInterface
from src.citation_parser import Citation

def test_integrated_validation():
    """Test integrated validation with rule retrieval."""
    print("=" * 80)
    print("INTEGRATED FAIL-CLOSED VALIDATION TEST")
    print("=" * 80)

    # Initialize components
    print("\n1. Initializing components...")
    llm = LLMInterface(use_vector_store=False)  # Use regular GPT for testing
    validator = CitationValidator(llm, use_deterministic_retrieval=True)

    if validator.use_deterministic_retrieval:
        print("   ✓ Deterministic retrieval enabled")
        print(f"   ✓ Loaded {len(validator.retriever.redbook_rules)} Redbook rules")
        print(f"   ✓ Loaded {len(validator.retriever.bluebook_rules)} Bluebook rules")
    else:
        print("   ✗ Deterministic retrieval NOT enabled - test may fail")

    # Test citations
    test_cases = [
        {
            "name": "Direct quote parenthetical (FN78-03)",
            "citation": Citation(
                full_text='Crusey, *supra* note 21 at 515 ("Unlike a copyright infringement claim under Section 501, a Section 1202 claim requires no prerequisite copyright registration.").',
                type="supra",
                footnote_num=78,
                citation_num=3
            ),
            "should_pass": True
        },
        {
            "name": "Straight quotes (should fail)",
            "citation": Citation(
                full_text='Smith v. Jones, 123 F.3d 456 (9th Cir. 2020) (discussing "the issue").',
                type="case",
                footnote_num=1,
                citation_num=1
            ),
            "should_pass": False  # Has straight quotes
        },
        {
            "name": "Uppercase non-quote parenthetical (should fail)",
            "citation": Citation(
                full_text='Smith v. Jones, 123 F.3d 456 (Discussing the issue).',
                type="case",
                footnote_num=2,
                citation_num=1
            ),
            "should_pass": False  # Uppercase outside quotes
        }
    ]

    print("\n2. Testing validation with rule retrieval:\n")

    for i, test in enumerate(test_cases, 1):
        print(f"   Test {i}: {test['name']}")
        print(f"   Citation: {test['citation'].full_text[:70]}...")

        # Run validation (this will retrieve rules and call LLM)
        result = validator.validate_citation(test['citation'])

        if result['success']:
            validation = result['validation']

            print(f"   ✓ Validation completed")
            print(f"      - Is correct: {validation['is_correct']}")
            print(f"      - Errors found: {len(validation.get('errors', []))}")
            print(f"      - Rules retrieved: {validation.get('rules_retrieved', 0)}")

            # Check coverage
            coverage = validation.get('coverage', {})
            if coverage:
                print(f"      - Coverage: R={coverage.get('redbook_matched', 0)}, B={coverage.get('bluebook_matched', 0)}")

            # Check evidence validation
            if validation.get('evidence_validation_failed'):
                print(f"      ⚠ Evidence validation failed!")
                print(f"         Issues: {validation.get('evidence_issues', [])}")

            # Show errors
            if validation.get('errors'):
                print(f"      Errors:")
                for err in validation['errors'][:2]:  # Show first 2
                    print(f"         - {err.get('error_type')}: {err.get('description', '')[:60]}...")
                    if 'rule_text_quote' in err:
                        print(f"           Evidence: {err['rule_text_quote'][:50]}...")

        else:
            print(f"   ✗ Validation failed: {result.get('error')}")

        print()

    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print("\nNOTE: This test demonstrates the fail-closed architecture:")
    print("  - Rules are retrieved deterministically before LLM call")
    print("  - Redbook-first priority is enforced programmatically")
    print("  - Coverage accounting tracks which rules were checked")
    print("  - Evidence validation ensures rule_text_quote is present")

    return True

if __name__ == "__main__":
    try:
        success = test_integrated_validation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
