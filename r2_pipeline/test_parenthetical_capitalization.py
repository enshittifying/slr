"""
Test parenthetical capitalization detection - verify direct quotes are NOT flagged.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.citation_validator import CitationValidator
from src.llm_interface import LLMInterface
from src.citation_parser import Citation

# Test cases
TEST_CASES = [
    {
        "name": "Direct quote with capital - FN78-03",
        "citation": 'Crusey, *supra* note 21 at 515 ("Unlike a copyright infringement claim under Section 501, a Section 1202 claim requires no prerequisite copyright registration.").',
        "should_flag": False,
        "reason": "Direct quote parenthetical - capitalization preserved"
    },
    {
        "name": "Direct quote with curly quotes",
        "citation": 'Smith, 123 F.3d 456 ("The new rules are complex.").',
        "should_flag": False,
        "reason": "Direct quote - capitalization preserved"
    },
    {
        "name": "Non-quote uppercase parenthetical",
        "citation": 'Smith v. Jones, 123 F.3d 456 (Discussing the issue).',
        "should_flag": True,
        "reason": "Not a quote - should be lowercase"
    },
    {
        "name": "Lowercase parenthetical (correct)",
        "citation": 'Smith v. Jones, 123 F.3d 456 (discussing the issue).',
        "should_flag": False,
        "reason": "Correctly lowercase"
    },
    {
        "name": "Nested quote in citing",
        "citation": 'Smith, 123 F.3d 456 (citing Jones, 789 F.2d 123 ("quoted text")).',
        "should_flag": False,
        "reason": "Contains direct quote - should not flag"
    },
    {
        "name": "Id. parenthetical (exception)",
        "citation": '*Id.* at 789 (Id. referring to previous cite).',
        "should_flag": False,
        "reason": "Starts with Id. - exception"
    },
    {
        "name": "Year only parenthetical",
        "citation": 'Smith v. Jones (2020).',
        "should_flag": False,
        "reason": "Year only - not explanatory"
    }
]

def run_tests():
    """Run deterministic capitalization tests."""
    print("=" * 80)
    print("PARENTHETICAL CAPITALIZATION TEST SUITE")
    print("=" * 80)

    # Create validator instance (without LLM for deterministic tests only)
    llm = LLMInterface()
    validator = CitationValidator(llm)

    passing = 0
    failing = 0

    for i, test in enumerate(TEST_CASES, 1):
        print(f"\nTest {i}: {test['name']}")
        print(f"Citation: {test['citation'][:80]}...")
        print(f"Expected: {'FLAG' if test['should_flag'] else 'NO FLAG'}")

        # Run deterministic check
        errors = validator._check_parenthetical_capitalization(test['citation'])
        has_cap_error = any(err['error_type'] == 'parenthetical_capitalization_error' for err in errors)

        # Check result
        if has_cap_error == test['should_flag']:
            print(f"✅ PASS - {test['reason']}")
            passing += 1
        else:
            print(f"❌ FAIL - Expected {'flag' if test['should_flag'] else 'no flag'}, got {'flag' if has_cap_error else 'no flag'}")
            print(f"   Reason: {test['reason']}")
            if errors:
                print(f"   Error details: {errors}")
            failing += 1

    # Summary
    total = len(TEST_CASES)
    print("\n" + "=" * 80)
    print(f"RESULTS: {passing}/{total} passing ({passing * 100 // total}%)")
    if failing > 0:
        print(f"FAILURES: {failing}")
    print("=" * 80)

    return failing == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
