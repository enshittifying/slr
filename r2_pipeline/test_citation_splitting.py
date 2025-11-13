"""
Test script for semicolon-based citation splitting.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.citation_parser import CitationParser

def test_split_citations():
    """Test the citation splitting logic."""

    test_cases = [
        {
            "name": "Simple semicolon split",
            "input": "citation first; citation second; citation third",
            "expected_count": 3
        },
        {
            "name": "Semicolon in parenthetical (should NOT split)",
            "input": "citation first; citation second (quote; something); citation third",
            "expected_count": 3
        },
        {
            "name": "Semicolon in straight quotes (should NOT split)",
            "input": 'citation first; citation with "quote; text" inside; citation third',
            "expected_count": 3
        },
        {
            "name": "Semicolon in curly quotes (should NOT split)",
            "input": "citation first; citation with \u201cquote; text\u201d inside; citation third",
            "expected_count": 3
        },
        {
            "name": "Complex: quotes and parens",
            "input": 'First cite; Second "has; semicolon"; Third (also; has); Fourth',
            "expected_count": 4
        },
        {
            "name": "Single citation (no split)",
            "input": "Single citation with no semicolons",
            "expected_count": 1
        },
        {
            "name": "Nested quotes and parens",
            "input": 'Cite one; Cite two ("quoted; text" and more); Cite three',
            "expected_count": 3
        }
    ]

    print("="*60)
    print("CITATION SPLITTING TEST")
    print("="*60)

    all_passed = True
    for i, test in enumerate(test_cases, 1):
        parser = CitationParser(test["input"], footnote_num=1)
        citations = parser.parse()

        passed = len(citations) == test["expected_count"]
        all_passed = all_passed and passed

        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"\nTest {i}: {test['name']}")
        print(f"Status: {status}")
        print(f"Input: {test['input']}")
        print(f"Expected: {test['expected_count']} citations")
        print(f"Got: {len(citations)} citations")

        if not passed or True:  # Always show splits for debugging
            for j, cite in enumerate(citations, 1):
                print(f"  [{j}] {cite.full_text}")

    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*60)

if __name__ == "__main__":
    test_split_citations()
