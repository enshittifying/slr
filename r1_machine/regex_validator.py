"""
Regex validator module for R1 Machine (Stage 1).

This module provides fast initial validation using regex patterns.
It's designed to quickly identify obviously correct or incorrect citations
without expensive rule lookups or API calls.
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

from citation_extractor import Citation


logger = logging.getLogger(__name__)


@dataclass
class RegexValidationResult:
    """
    Result of regex-based validation.

    Attributes:
        is_valid: Whether citation passed basic regex checks
        confidence: Confidence score (0.0-1.0)
        detected_type: Detected citation type
        errors: List of error messages
        warnings: List of warning messages
        matched_patterns: List of pattern names that matched
        processing_time_ms: Time taken to validate (milliseconds)
    """

    is_valid: bool
    confidence: float
    detected_type: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    matched_patterns: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0


class RegexValidator:
    """
    Fast regex-based citation validator (Stage 1).

    This validator uses regex patterns to quickly check for:
    - Basic structural elements (case name, reporter, year)
    - Common formatting patterns
    - Obvious errors (missing components, malformed citations)

    Performance target: < 10ms per citation
    """

    def __init__(self):
        """Initialize regex validator with pattern library."""
        # Compile regex patterns for speed
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile all regex patterns for fast matching."""

        # === Case Citation Patterns ===
        # Full case citation: Case Name, Volume Reporter Page (Court Year)
        self.case_full = re.compile(
            r'\*?([^*,]+?)\*?\s+v\.\s+\*?([^*,]+?)\*?,?\s+'  # Case name
            r'(\d+)\s+'  # Volume
            r'([A-Z][a-z.]*\s*[A-Z0-9.]*)\s+'  # Reporter
            r'(\d+)'  # Page
            r'(?:,\s*(\d+))?'  # Optional pinpoint
            r'\s*\(([^)]+)\s+(\d{4})\)',  # Court and year
            re.IGNORECASE
        )

        # Short form case: Case Name, Volume Reporter at Page
        self.case_short = re.compile(
            r'([A-Za-z]+)\s*,\s*(\d+)\s+([A-Z][a-z.]*)\s+at\s+(\d+)',
            re.IGNORECASE
        )

        # === Statute Citation Patterns ===
        # Federal statute: Title U.S.C. § Section (Year)
        self.statute_usc = re.compile(
            r'(\d+)\s+U\.S\.C\.\s+§§?\s*([\d-]+(?:\([a-z]\))?)',
            re.IGNORECASE
        )

        # State statute
        self.statute_state = re.compile(
            r'([A-Z][a-z.]+)\s+[A-Z][a-z.]*\s+[A-Z][a-z.]*\s+§§?\s*([\d-]+)',
            re.IGNORECASE
        )

        # === Constitution Patterns ===
        self.constitution = re.compile(
            r'(U\.S\.|[A-Z][a-z.]+)\s+Const\.\s+art\.\s+([IVX]+)',
            re.IGNORECASE
        )

        # === Book Citation Patterns ===
        # Author, Title (Edition Year)
        self.book = re.compile(
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z.]+)*)\s*,\s*'  # Author
            r'([^,]+?)\s*'  # Title
            r'\((?:\d+[a-z]{2}\s+ed\.\s+)?(\d{4})\)',  # Year with optional edition
            re.IGNORECASE
        )

        # === Article Citation Patterns ===
        # Author, Title, Volume Journal Page (Year)
        self.article = re.compile(
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z.]+)*)\s*,\s*'  # Author
            r'([^,]+?)\s*,\s*'  # Title
            r'(\d+)\s+'  # Volume
            r'([A-Z][a-z.]+(?:\s+[A-Z][a-z.]+)*)\s+'  # Journal
            r'(\d+)'  # Page
            r'(?:\s*,\s*(\d+))?'  # Optional pinpoint
            r'\s*\((\d{4})\)',  # Year
            re.IGNORECASE
        )

        # === Common Elements ===
        self.year_pattern = re.compile(r'\((\d{4})\)')
        self.volume_pattern = re.compile(r'\b(\d+)\s+[A-Z]')
        self.italics_pattern = re.compile(r'\*([^*]+)\*')
        self.section_symbol = re.compile(r'§§?')

    def validate(self, citation: Citation) -> RegexValidationResult:
        """
        Validate a citation using regex patterns.

        Args:
            citation: Citation object to validate

        Returns:
            RegexValidationResult with validation details

        Example:
            >>> validator = RegexValidator()
            >>> citation = Citation(...)
            >>> result = validator.validate(citation)
            >>> if result.confidence >= 0.9:
            ...     print("Citation is valid!")
        """
        import time
        start_time = time.time()

        text = citation.full_text
        errors = []
        warnings = []
        matched_patterns = []
        confidence = 0.0

        # Detect citation type and validate accordingly
        detected_type = citation.type if citation.type != "unknown" else self._detect_type(text)

        if detected_type == "case":
            is_valid, conf, errs, warns, patterns = self._validate_case(text)
        elif detected_type == "statute":
            is_valid, conf, errs, warns, patterns = self._validate_statute(text)
        elif detected_type == "constitution":
            is_valid, conf, errs, warns, patterns = self._validate_constitution(text)
        elif detected_type == "book":
            is_valid, conf, errs, warns, patterns = self._validate_book(text)
        elif detected_type == "article":
            is_valid, conf, errs, warns, patterns = self._validate_article(text)
        else:
            is_valid = False
            conf = 0.3
            errs = ["Could not determine citation type"]
            warns = []
            patterns = []

        errors.extend(errs)
        warnings.extend(warns)
        matched_patterns.extend(patterns)
        confidence = conf

        # General validation checks
        if len(text) < 15:
            errors.append("Citation is too short")
            confidence *= 0.5

        if len(text) > 500:
            warnings.append("Citation is unusually long")
            confidence *= 0.9

        # Check for year
        if not self.year_pattern.search(text):
            errors.append("Missing year in parentheses")
            confidence *= 0.7

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        return RegexValidationResult(
            is_valid=is_valid and len(errors) == 0,
            confidence=min(confidence, 1.0),
            detected_type=detected_type,
            errors=errors,
            warnings=warnings,
            matched_patterns=matched_patterns,
            processing_time_ms=processing_time
        )

    def _detect_type(self, text: str) -> str:
        """Detect citation type from text."""
        # Try each pattern
        if self.case_full.search(text) or self.case_short.search(text) or " v. " in text:
            return "case"
        if self.statute_usc.search(text) or self.statute_state.search(text):
            return "statute"
        if self.constitution.search(text):
            return "constitution"
        if self.article.search(text):
            return "article"
        if self.book.search(text):
            return "book"

        return "unknown"

    def _validate_case(self, text: str) -> Tuple[bool, float, List[str], List[str], List[str]]:
        """Validate a case citation."""
        errors = []
        warnings = []
        patterns = []
        confidence = 0.5

        # Check for full citation pattern
        match = self.case_full.search(text)
        if match:
            patterns.append("case_full")
            confidence = 0.95

            # Validate components
            plaintiff = match.group(1).strip()
            defendant = match.group(2).strip()
            volume = match.group(3)
            reporter = match.group(4).strip()
            page = match.group(5)

            # Check italicization of case name
            if not ("*" in text[:50]):  # Expect italics near start
                errors.append("Case name should be italicized")
                confidence *= 0.9

            # Check reporter format
            if not reporter[0].isupper():
                errors.append("Reporter should be capitalized")
                confidence *= 0.95

        else:
            # Try short form
            short_match = self.case_short.search(text)
            if short_match:
                patterns.append("case_short")
                confidence = 0.85
            else:
                # Check for " v. " which indicates case
                if " v. " in text:
                    errors.append("Case citation structure not recognized")
                    confidence = 0.4
                else:
                    errors.append("Missing 'v.' in case citation")
                    confidence = 0.2

        # Check for common errors
        if " vs. " in text or " vs " in text:
            errors.append("Use 'v.' not 'vs.' in case citations")
            confidence *= 0.8

        is_valid = len(errors) == 0
        return is_valid, confidence, errors, warnings, patterns

    def _validate_statute(self, text: str) -> Tuple[bool, float, List[str], List[str], List[str]]:
        """Validate a statute citation."""
        errors = []
        warnings = []
        patterns = []
        confidence = 0.5

        # Check for USC pattern
        match = self.statute_usc.search(text)
        if match:
            patterns.append("statute_usc")
            confidence = 0.92

            title = match.group(1)
            section = match.group(2)

            # Validate title is reasonable
            if int(title) > 54:
                warnings.append(f"USC title {title} is unusually high")
                confidence *= 0.95

        else:
            # Try state statute
            state_match = self.statute_state.search(text)
            if state_match:
                patterns.append("statute_state")
                confidence = 0.88
            else:
                errors.append("Statute citation structure not recognized")
                confidence = 0.3

        # Check for section symbol
        if not self.section_symbol.search(text):
            errors.append("Missing section symbol (§)")
            confidence *= 0.6

        is_valid = len(errors) == 0
        return is_valid, confidence, errors, warnings, patterns

    def _validate_constitution(self, text: str) -> Tuple[bool, float, List[str], List[str], List[str]]:
        """Validate a constitution citation."""
        errors = []
        warnings = []
        patterns = []
        confidence = 0.5

        match = self.constitution.search(text)
        if match:
            patterns.append("constitution")
            confidence = 0.95
        else:
            if "Const." in text or "Constitution" in text:
                errors.append("Constitution citation structure not recognized")
                confidence = 0.4
            else:
                errors.append("Missing 'Const.' in constitution citation")
                confidence = 0.2

        is_valid = len(errors) == 0
        return is_valid, confidence, errors, warnings, patterns

    def _validate_book(self, text: str) -> Tuple[bool, float, List[str], List[str], List[str]]:
        """Validate a book citation."""
        errors = []
        warnings = []
        patterns = []
        confidence = 0.5

        match = self.book.search(text)
        if match:
            patterns.append("book")
            confidence = 0.88

            author = match.group(1)
            title = match.group(2)
            year = match.group(3)

            # Check title should be italicized
            if "*" not in title and "*" not in text:
                warnings.append("Book title should be italicized")
                confidence *= 0.95

        else:
            # Check if it looks like a book but doesn't match
            if "(" in text and ")" in text and "," in text:
                errors.append("Book citation structure not recognized")
                confidence = 0.4
            else:
                errors.append("Missing required book citation elements")
                confidence = 0.2

        is_valid = len(errors) == 0
        return is_valid, confidence, errors, warnings, patterns

    def _validate_article(self, text: str) -> Tuple[bool, float, List[str], List[str], List[str]]:
        """Validate an article citation."""
        errors = []
        warnings = []
        patterns = []
        confidence = 0.5

        match = self.article.search(text)
        if match:
            patterns.append("article")
            confidence = 0.90

            author = match.group(1)
            title = match.group(2)
            volume = match.group(3)
            journal = match.group(4)
            page = match.group(5)
            year = match.group(7)

            # Validate volume is reasonable
            if int(volume) > 500:
                warnings.append(f"Volume number {volume} is unusually high")
                confidence *= 0.95

        else:
            errors.append("Article citation structure not recognized")
            confidence = 0.3

        is_valid = len(errors) == 0
        return is_valid, confidence, errors, warnings, patterns


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    validator = RegexValidator()

    # Test citations
    test_cases = [
        Citation(1, 1, "*Brown* v. *Board of Education*, 347 U.S. 483 (1954)", "case"),
        Citation(2, 1, "42 U.S.C. § 1983 (2018)", "statute"),
        Citation(3, 1, "U.S. Const. art. I, § 8", "constitution"),
        Citation(4, 1, "Richard A. Posner, Economic Analysis of Law (9th ed. 2014)", "book"),
        Citation(5, 1, "John Doe, Sample Article, 100 Yale L.J. 1 (1990)", "article"),
        Citation(6, 1, "Bad citation", "unknown"),
    ]

    print("\n=== Regex Validation Tests ===\n")

    for citation in test_cases:
        result = validator.validate(citation)
        print(f"Citation: {citation.full_text}")
        print(f"  Valid: {result.is_valid}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Type: {result.detected_type}")
        print(f"  Errors: {result.errors}")
        print(f"  Warnings: {result.warnings}")
        print(f"  Time: {result.processing_time_ms:.2f}ms")
        print()
