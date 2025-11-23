"""
Quote Accuracy Verifier for R1
Verifies quotes character-by-character against source text
Adapted from R2 pipeline
"""
import re
from typing import Dict, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class QuoteIssue:
    """Represents an issue found in a quote."""
    issue_type: str  # 'mismatch', 'bracket', 'ellipsis', 'capitalization', 'punctuation'
    description: str
    position: int  # Character position in quote
    expected: str
    actual: str
    severity: str  # 'critical', 'major', 'minor'


class QuoteVerifier:
    """Verify accuracy of quoted text against source."""

    def __init__(self):
        self.issues: List[QuoteIssue] = []

    def verify_quote(self,
                     quoted_text: str,
                     source_text: str,
                     allow_minor_whitespace: bool = True) -> Dict:
        """
        Verify a quote against its source.

        Args:
            quoted_text: The quote as it appears in the citation
            source_text: The text from the source document
            allow_minor_whitespace: Allow minor whitespace differences

        Returns:
            Dict with verification results
        """
        self.issues = []

        # Clean up for comparison
        quote_clean = self._normalize_text(quoted_text)
        source_clean = self._normalize_text(source_text)

        # Check if quote exists in source
        quote_found = self._find_quote_in_source(quote_clean, source_clean)

        if not quote_found:
            # Try fuzzy matching
            try:
                import Levenshtein
                similarity = Levenshtein.ratio(quote_clean, source_clean)
            except ImportError:
                similarity = 0.5 if quote_clean.lower() in source_clean.lower() else 0.0

            if similarity < 0.85:
                return {
                    "accurate": False,
                    "confidence": 0.0,
                    "similarity": similarity,
                    "issues": [{
                        "issue_type": "not_found",
                        "description": "Quote not found in source text",
                        "severity": "critical"
                    }],
                    "suggested_action": "verify_source_or_page_number"
                }

        # Character-by-character comparison
        self._compare_character_by_character(quoted_text, source_text)

        # Check bracket usage
        self._verify_brackets(quoted_text, source_text)

        # Check ellipsis usage
        self._verify_ellipses(quoted_text, source_text)

        # Check quotation marks
        self._verify_nested_quotes(quoted_text)

        # Calculate accuracy score
        accuracy_score = self._calculate_accuracy_score()

        return {
            "accurate": accuracy_score > 0.95,
            "confidence": accuracy_score,
            "issues": [self._issue_to_dict(issue) for issue in self.issues],
            "suggested_action": self._suggest_action(accuracy_score),
            "quote_clean": quote_clean,
            "source_clean": source_clean
        }

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)
        return text.strip()

    def _find_quote_in_source(self, quote: str, source: str) -> bool:
        """Check if quote appears in source."""
        if quote in source:
            return True
        if quote.lower() in source.lower():
            return True
        quote_no_punct = re.sub(r'[^\w\s]', '', quote)
        source_no_punct = re.sub(r'[^\w\s]', '', source)
        if quote_no_punct in source_no_punct:
            return True
        return False

    def _compare_character_by_character(self, quote: str, source: str):
        """Compare quote and source character by character."""
        quote_clean = self._normalize_text(quote)
        source_clean = self._normalize_text(source)

        pos = source_clean.lower().find(quote_clean.lower())
        if pos == -1:
            return

        actual_source = source_clean[pos:pos+len(quote_clean)]

        for i, (q_char, s_char) in enumerate(zip(quote_clean, actual_source)):
            if q_char != s_char:
                self.issues.append(QuoteIssue(
                    issue_type='mismatch',
                    description=f"Character mismatch at position {i}",
                    position=i,
                    expected=s_char,
                    actual=q_char,
                    severity='major'
                ))

    def _verify_brackets(self, quote: str, source: str):
        """Verify brackets are used correctly for alterations."""
        bracketed = re.finditer(r'\[([^\]]+)\]', quote)

        for match in bracketed:
            bracketed_text = match.group(1)
            position = match.start()

            # Capitalization change
            if len(bracketed_text) == 1 and bracketed_text.isupper():
                continue

            # Explanatory brackets
            if bracketed_text.lower() in ['sic', 'emphasis added', 'emphasis omitted',
                                          'internal quotation marks omitted', 'citations omitted']:
                continue

            # Otherwise, flag for review
            self.issues.append(QuoteIssue(
                issue_type='bracket',
                description=f"Bracketed alteration: [{bracketed_text}] - verify necessity",
                position=position,
                expected='',
                actual=f'[{bracketed_text}]',
                severity='minor'
            ))

    def _verify_ellipses(self, quote: str, source: str):
        """Verify ellipses are properly formatted."""
        ellipses = re.finditer(r'\.{3,4}|\. \. \.|\.\.\.|…', quote)

        for match in ellipses:
            ellipsis = match.group(0)
            position = match.start()
            dot_count = ellipsis.count('.')

            if dot_count == 3:
                if ellipsis not in [' . . . ', '...', '…']:
                    self.issues.append(QuoteIssue(
                        issue_type='ellipsis',
                        description='Ellipsis spacing incorrect (should be " . . . ")',
                        position=position,
                        expected=' . . . ',
                        actual=ellipsis,
                        severity='minor'
                    ))

    def _verify_nested_quotes(self, quote: str):
        """Verify nested quotes use single quotes."""
        double_quotes = [m.start() for m in re.finditer(r'"', quote)]

        if len(double_quotes) >= 4:
            nested_double = re.search(r'"[^"]*"[^"]*"[^"]*"', quote)
            if nested_double:
                self.issues.append(QuoteIssue(
                    issue_type='nested_quotes',
                    description='Nested quote should use single quotes',
                    position=nested_double.start(),
                    expected='single quotes (\')',
                    actual='double quotes (")',
                    severity='major'
                ))

    def _calculate_accuracy_score(self) -> float:
        """Calculate overall accuracy score."""
        if not self.issues:
            return 1.0

        total_penalty = 0.0
        for issue in self.issues:
            if issue.severity == 'critical':
                total_penalty += 0.5
            elif issue.severity == 'major':
                total_penalty += 0.1
            elif issue.severity == 'minor':
                total_penalty += 0.02

        return max(0.0, 1.0 - total_penalty)

    def _suggest_action(self, accuracy_score: float) -> str:
        """Suggest action based on accuracy score."""
        if accuracy_score >= 0.98:
            return 'approve'
        elif accuracy_score >= 0.90:
            return 'review_minor_issues'
        elif accuracy_score >= 0.70:
            return 'review_major_issues'
        else:
            return 'flag_for_human_verification'

    def _issue_to_dict(self, issue: QuoteIssue) -> Dict:
        """Convert QuoteIssue to dict."""
        return {
            'issue_type': issue.issue_type,
            'description': issue.description,
            'position': issue.position,
            'expected': issue.expected,
            'actual': issue.actual,
            'severity': issue.severity
        }
