"""
Test suite for R1 validation components
"""
import unittest
import sys
from pathlib import Path

# Add SLRinator to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.r1_validation import (
    Citation,
    CitationValidator,
    QuoteVerifier,
    SupportChecker,
    BluebookRuleRetriever,
    LLMInterface
)


class TestCitationValidator(unittest.TestCase):
    """Test citation validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.llm = LLMInterface(use_vector_store=False)
        self.validator = CitationValidator(self.llm, use_deterministic_retrieval=False)

    def test_curly_quotes_detection(self):
        """Test detection of straight quotes."""
        errors = self.validator._check_curly_quotes('See "quoted text" here')
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['error_type'], 'curly_quotes_error')
        self.assertEqual(errors[0]['rb_rule'], '24.4')

    def test_curly_quotes_correct(self):
        """Test that curly quotes don't trigger errors."""
        errors = self.validator._check_curly_quotes('See "quoted text" here')
        self.assertEqual(len(errors), 0)

    def test_non_breaking_space_detection(self):
        """Test detection of missing non-breaking spaces."""
        # v. should have non-breaking space before it
        errors = self.validator._check_non_breaking_spaces('Alice v. Bob')
        self.assertTrue(len(errors) > 0)
        self.assertTrue(any(e['error_type'] == 'non_breaking_space_error' for e in errors))

    def test_parenthetical_capitalization(self):
        """Test parenthetical capitalization check."""
        # Final explanatory parenthetical should be lowercase
        errors = self.validator._check_parenthetical_capitalization(
            'Alice v. Bob, 123 U.S. 456 (2020) (Holding that X is true).'
        )
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['error_type'], 'parenthetical_capitalization_error')

    def test_parenthetical_capitalization_correct(self):
        """Test correct parenthetical capitalization."""
        errors = self.validator._check_parenthetical_capitalization(
            'Alice v. Bob, 123 U.S. 456 (2020) (holding that X is true).'
        )
        self.assertEqual(len(errors), 0)


class TestQuoteVerifier(unittest.TestCase):
    """Test quote verification."""

    def setUp(self):
        """Set up test fixtures."""
        self.verifier = QuoteVerifier()

    def test_exact_quote_match(self):
        """Test exact quote matching."""
        result = self.verifier.verify_quote(
            quoted_text="the quick brown fox",
            source_text="The quick brown fox jumps over the lazy dog."
        )
        self.assertTrue(result['accurate'])
        self.assertGreater(result['confidence'], 0.95)

    def test_quote_not_found(self):
        """Test quote not in source."""
        result = self.verifier.verify_quote(
            quoted_text="completely different text",
            source_text="The quick brown fox jumps over the lazy dog."
        )
        self.assertFalse(result['accurate'])
        self.assertEqual(result['issues'][0]['issue_type'], 'not_found')

    def test_bracket_detection(self):
        """Test bracket alteration detection."""
        result = self.verifier.verify_quote(
            quoted_text="The [plaintiff] argued that...",
            source_text="The defendant argued that..."
        )
        # Should detect bracketed alteration
        bracket_issues = [i for i in result['issues'] if i['issue_type'] == 'bracket']
        self.assertTrue(len(bracket_issues) > 0)

    def test_ellipsis_formatting(self):
        """Test ellipsis formatting check."""
        result = self.verifier.verify_quote(
            quoted_text="The court held... that X is true",
            source_text="The court held on this matter that X is true"
        )
        # May detect ellipsis spacing issues
        self.assertIn('issues', result)


class TestSupportChecker(unittest.TestCase):
    """Test support checking (requires API key)."""

    def setUp(self):
        """Set up test fixtures."""
        self.llm = LLMInterface(use_vector_store=False)
        self.checker = SupportChecker(self.llm)

    @unittest.skip("Requires OpenAI API key")
    def test_direct_support(self):
        """Test direct support detection."""
        result = self.checker.check_support(
            proposition="The court held that X is true",
            source_text="In this case, we hold that X is true and binding.",
            citation_text="Test v. Case, 123 U.S. 456 (2020)"
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['analysis']['support_level'], 'yes')

    @unittest.skip("Requires OpenAI API key")
    def test_no_support(self):
        """Test no support detection."""
        result = self.checker.check_support(
            proposition="The court held that X is true",
            source_text="We decline to address whether X is true.",
            citation_text="Test v. Case, 123 U.S. 456 (2020)"
        )
        self.assertTrue(result['success'])
        self.assertEqual(result['analysis']['support_level'], 'no')


class TestBluebookRuleRetriever(unittest.TestCase):
    """Test rule retrieval."""

    def setUp(self):
        """Set up test fixtures."""
        # Use a mock Bluebook.json path or create a minimal test file
        self.test_bluebook = Path(__file__).parent / "test_bluebook.json"
        if not self.test_bluebook.exists():
            # Create minimal test file
            import json
            test_data = {
                "redbook": {
                    "rules": [
                        {
                            "id": "1.1",
                            "title": "Test Redbook Rule",
                            "text": "This is a test redbook rule about citations."
                        }
                    ]
                },
                "bluebook": {
                    "rules": [
                        {
                            "id": "10.1",
                            "title": "Test Bluebook Rule",
                            "text": "This is a test bluebook rule about case names."
                        }
                    ]
                }
            }
            with open(self.test_bluebook, 'w') as f:
                json.dump(test_data, f)

        self.retriever = BluebookRuleRetriever(str(self.test_bluebook))

    def test_rule_loading(self):
        """Test that rules are loaded."""
        self.assertGreater(len(self.retriever.redbook_rules), 0)
        self.assertGreater(len(self.retriever.bluebook_rules), 0)

    def test_keyword_extraction(self):
        """Test keyword extraction from citation."""
        terms = self.retriever._extract_terms("Alice v. Bob, 123 U.S. 456 (2020)")
        self.assertIn('case', terms)
        self.assertIn('name', terms)

    def test_rule_retrieval(self):
        """Test rule retrieval."""
        rules, coverage = self.retriever.retrieve_rules("Alice v. Bob")
        self.assertGreater(len(rules), 0)
        self.assertIn('redbook_scanned', coverage)
        self.assertIn('bluebook_scanned', coverage)

    def tearDown(self):
        """Clean up test files."""
        if hasattr(self, 'test_bluebook') and self.test_bluebook.exists():
            self.test_bluebook.unlink()


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
