#!/usr/bin/env python3
"""
Test the new deterministic rule retrieval system.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.rule_retrieval import BluebookRuleRetriever, RuleEvidenceValidator
from config.settings import BLUEBOOK_JSON_PATH

def test_retriever():
    """Test rule retrieval system."""
    print("=" * 80)
    print("RULE RETRIEVAL SYSTEM TEST")
    print("=" * 80)

    # Initialize retriever
    print(f"\n1. Loading Bluebook.json from: {BLUEBOOK_JSON_PATH}")
    retriever = BluebookRuleRetriever(str(BLUEBOOK_JSON_PATH))

    print(f"   ✓ Loaded {len(retriever.redbook_rules)} Redbook rules")
    print(f"   ✓ Loaded {len(retriever.bluebook_rules)} Bluebook rules")

    # Test citation examples
    test_citations = [
        'Crusey, *supra* note 21 at 515 ("Unlike a copyright infringement claim under Section 501, a Section 1202 claim requires no prerequisite copyright registration.").',
        'Smith v. Jones, 123 F.3d 456 (9th Cir. 2020).',
        '*See* Smith, 789 F.2d 123, 456 (discussing the issue).',
        'No. 21-CV-6425 (S.D.N.Y. 2021).',
    ]

    print("\n2. Testing rule retrieval for sample citations:\n")

    for i, citation in enumerate(test_citations, 1):
        print(f"   Citation {i}: {citation[:60]}...")
        matches, coverage = retriever.retrieve_rules(citation)

        print(f"   Coverage:")
        print(f"      - Scanned: {coverage['redbook_scanned']} Redbook, {coverage['bluebook_scanned']} Bluebook")
        print(f"      - Matched: {coverage['redbook_matched']} Redbook, {coverage['bluebook_matched']} Bluebook")
        print(f"      - Returned: {coverage['redbook_returned']} Redbook, {coverage['bluebook_returned']} Bluebook")
        print(f"      - Terms: {coverage['search_terms'][:5]}...")

        if matches:
            print(f"   Top 3 matches:")
            for j, match in enumerate(matches[:3], 1):
                print(f"      {j}. [{match.source}] Rule {match.rule_id}: {match.title[:50]}")
                print(f"         Score: {match.score:.2f}")
        print()

    # Test specific rule lookup
    print("3. Testing specific rule lookup:\n")

    test_rules = [
        ("1.16", "redbook"),
        ("10.2.1", "bluebook"),
        ("24.4", "redbook"),
    ]

    for rule_id, source in test_rules:
        rule = retriever.get_rule_by_id(rule_id, source)
        if rule:
            print(f"   ✓ Found {source} rule {rule_id}: {rule.title}")
            print(f"     Text: {rule.text[:100]}...")
        else:
            print(f"   ✗ Could not find {source} rule {rule_id}")
        print()

    # Test evidence validator
    print("4. Testing evidence validation:\n")

    validator = RuleEvidenceValidator(retriever)

    # Create mock response with evidence
    valid_response = {
        "is_correct": False,
        "errors": [
            {
                "error_type": "test_error",
                "description": "Test error with evidence",
                "rb_rule": "1.16",
                "rule_text_quote": "Explanatory parentheticals should begin with a lowercase letter"
            }
        ]
    }

    # Get some matches for validation
    matches, _ = retriever.retrieve_rules('test citation (Example)')

    is_valid, issues = validator.validate_response(valid_response, matches)
    print(f"   Valid response with evidence: {'✓ PASS' if is_valid else '✗ FAIL'}")
    if issues:
        print(f"   Issues: {issues}")

    # Create mock response WITHOUT evidence
    invalid_response = {
        "is_correct": False,
        "errors": [
            {
                "error_type": "test_error",
                "description": "Test error WITHOUT evidence",
                "rb_rule": "1.16"
                # Missing rule_text_quote!
            }
        ]
    }

    is_valid, issues = validator.validate_response(invalid_response, matches)
    print(f"   Invalid response without evidence: {'✗ FAIL (expected)' if not is_valid else '✓ PASS (unexpected!)'}")
    if issues:
        print(f"   Issues: {issues}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

    return True

if __name__ == "__main__":
    try:
        success = test_retriever()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
