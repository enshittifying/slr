#!/usr/bin/env python3
"""
Bluebook Short Form Citation Validator
========================================

This module provides utilities for validating Bluebook short form citations
based on Rule 4 and related rules.

Usage:
    python bluebook_citation_validator.py --citation "Doe, supra note 5, at 100"
    python bluebook_citation_validator.py --file citations.txt
"""

import re
import json
import argparse
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of citation validation"""
    is_valid: bool
    citation_type: Optional[str]
    rule: Optional[str]
    message: str
    issues: List[str]


class BluebookCitationValidator:
    """Validates Bluebook short form citations"""

    # Valid citation patterns organized by type
    VALID_PATTERNS = {
        "id_alone": {
            "pattern": r"^Id\.$",
            "rule": "Rule 4.1",
            "description": "Id. citation alone"
        },
        "id_with_pinpoint": {
            "pattern": r"^Id\.\s+at\s+\d+$",
            "rule": "Rule 4.2",
            "description": "Id. with 'at' pinpoint"
        },
        "id_with_parenthetical": {
            "pattern": r"^Id\.\s*\((?:para|p|pp|page|pages|§)\s*\.?\d+(?:\s*-\s*\d+)?\)$",
            "rule": "Rule 4.1",
            "description": "Id. with parenthetical pinpoint"
        },
        "supra_author": {
            "pattern": r"^[A-Z][a-zA-Z\s']*,\s+supra\s+note\s+\d+(?:,\s+at\s+\d+)?$",
            "rule": "Rule 4.2",
            "description": "Supra citation with author"
        },
        "supra_author_title": {
            "pattern": r"^[A-Z][a-zA-Z\s']*,\s+[A-Z][a-zA-Z\s0-9]*,\s+supra\s+note\s+\d+(?:,\s+at\s+\d+)?$",
            "rule": "Rule 4.2",
            "description": "Supra citation with author and title"
        },
        "case_name": {
            "pattern": r"^[A-Z][a-zA-Z\s']*(?:\s+v\.?\s+[A-Z][a-zA-Z\s']*)?(?:,\s+\d+\s+[A-Z\.]+\s+\d+)?(?:,\s+at\s+\d+)?$",
            "rule": "Rule 10.9",
            "description": "Case name short form"
        },
        "hereinafter_short": {
            "pattern": r"^[A-Z][a-zA-Z\s0-9]*,\s+supra\s+note\s+\d+(?:,\s+(?:art|§|¶)\s+[\d\.]+)?$",
            "rule": "Rule 4.2",
            "description": "Hereinafter abbreviation short form"
        },
        "service_citation": {
            "pattern": r"^[A-Z\.]+\s+[A-Z][a-zA-Z\s0-9\.]*,\s+supra\s+note\s+\d+(?:,\s+¶\s+[\d,]+)?$",
            "rule": "Rule 19.2",
            "description": "Service/looseleaf citation"
        },
        "foreign_source": {
            "pattern": r"^[A-Z][a-zA-Z\s']*(?:\s+(?:Code|Act|Statute|Law|Reporter))?(?:,\s+supra\s+note\s+\d+)?(?:,\s+(?:art|§|¶)\s+[\d\.]+)?$",
            "rule": "Rule 20.7",
            "description": "Foreign source short form"
        },
        "treaty": {
            "pattern": r"^[A-Z][\w\s\.''-]*(?:Charter|Convention|Treaty|Agreement|Protocol|Covenant)[\w\s\.''-]*,\s+supra\s+note\s+\d+(?:,\s+(?:art|¶|§)\s+[\d\.]+)?$",
            "rule": "Rule 21.17",
            "description": "Treaty short form"
        },
        "internet_source": {
            "pattern": r"^[A-Z][A-Za-z\s'-]*(?:Blog|Website|Post|Article)?,\s+supra\s+note\s+\d+(?:,\s+at\s+(?:para|p)\s*\.?\s*\d+)?$",
            "rule": "Rule 18.9",
            "description": "Internet/media source short form"
        },
        "unpublished_source": {
            "pattern": r"^[A-Z][a-zA-Z\s']*(?:\s+(?:Letter|Interview|Manuscript|Paper))?(?:,\s+supra\s+note\s+\d+)?(?:,\s+at\s+\d+)?$",
            "rule": "Rule 17.6",
            "description": "Unpublished source short form"
        }
    }

    # Common invalid patterns to detect
    INVALID_PATTERNS = {
        "lowercase_id": {
            "pattern": r"^id\.",
            "message": "Id. must have uppercase 'I'"
        },
        "missing_period_after_id": {
            "pattern": r"^Id\s+at\s+\d+$",
            "message": "Id. must have a period before 'at'"
        },
        "missing_comma_before_supra": {
            "pattern": r"^[A-Z][a-zA-Z]*\s+supra\s+note\s+\d+$",
            "message": "Missing comma between author and 'supra'"
        },
        "missing_note_keyword": {
            "pattern": r"^[A-Z][a-zA-Z]*,\s+supra\s+\d+$",
            "message": "Missing 'note' keyword between 'supra' and number"
        },
        "supra_for_cases": {
            "pattern": r"^[A-Z][a-zA-Z\s']*\s+v\.\s+[A-Z][a-zA-Z\s']*,\s+supra\s+note\s+\d+$",
            "message": "Cases do NOT use 'supra'. Use case name short form instead."
        },
        "hereinafter_for_cases": {
            "pattern": r"^[A-Z][a-zA-Z\s']*\s+v\.\s+[A-Z][a-zA-Z\s']*,\s+hereinafter\s+",
            "message": "Cases do NOT use 'hereinafter'. Use case name short form only."
        },
        "standalone_at": {
            "pattern": r"^at\s+\d+$",
            "message": "'at' pinpoint cannot stand alone. Must follow authority reference."
        },
        "uppercase_supra": {
            "pattern": r"^[A-Z][a-zA-Z]*,\s+(?:SUPRA|Supra)\s+(?:NOTE|Note)",
            "message": "'supra' and 'note' must be lowercase"
        },
        "misplaced_comma": {
            "pattern": r"^[A-Z][a-zA-Z]*\s+supra,\s+note\s+\d+$",
            "message": "Comma must go between author and 'supra', not between 'supra' and 'note'"
        },
        "quotes_around_author": {
            "pattern": r'^"[A-Z][a-zA-Z]*",\s+supra\s+note\s+\d+$',
            "message": "Author names should not be in quotation marks"
        },
        "double_at": {
            "pattern": r"^[A-Z][a-zA-Z]*,\s+supra\s+note\s+\d+,\s+at\s+\d+,\s+at\s+\d+$",
            "message": "Multiple 'at' clauses in single citation"
        },
        "id_with_author": {
            "pattern": r"^Id\.\s+\([A-Z][a-zA-Z]*\)$",
            "message": "Id. should not include author name in parenthetical"
        },
        "word_note_number": {
            "pattern": r"^[A-Z][a-zA-Z]*,\s+supra\s+note\s+[a-z]+$",
            "message": "Note numbers must be digits, not words"
        },
        "word_page_number": {
            "pattern": r"^[A-Z][a-zA-Z]*,\s+supra\s+note\s+\d+,\s+at\s+[a-z]+$",
            "message": "Page numbers must be digits, not words"
        }
    }

    def validate(self, citation: str) -> ValidationResult:
        """
        Validate a Bluebook short form citation.

        Args:
            citation: The citation string to validate

        Returns:
            ValidationResult object with validation details
        """
        citation = citation.strip()

        # Check for invalid patterns first
        issues = []
        for pattern_name, pattern_info in self.INVALID_PATTERNS.items():
            if re.search(pattern_info["pattern"], citation):
                issues.append(pattern_info["message"])

        if issues:
            return ValidationResult(
                is_valid=False,
                citation_type=None,
                rule=None,
                message=f"Invalid citation: {'; '.join(issues)}",
                issues=issues
            )

        # Check for valid patterns
        for pattern_name, pattern_info in self.VALID_PATTERNS.items():
            if re.match(pattern_info["pattern"], citation):
                return ValidationResult(
                    is_valid=True,
                    citation_type=pattern_name,
                    rule=pattern_info["rule"],
                    message=f"Valid {pattern_info['description']}",
                    issues=[]
                )

        # No pattern matched
        return ValidationResult(
            is_valid=False,
            citation_type=None,
            rule=None,
            message="Citation does not match any known Bluebook short form pattern",
            issues=["Unable to identify citation format"]
        )

    def validate_batch(self, citations: List[str]) -> List[Tuple[str, ValidationResult]]:
        """
        Validate multiple citations.

        Args:
            citations: List of citation strings

        Returns:
            List of (citation, ValidationResult) tuples
        """
        return [(c, self.validate(c)) for c in citations]

    def get_valid_patterns_for_source_type(self, source_type: str) -> Optional[Dict]:
        """
        Get valid patterns for a specific source type.

        Args:
            source_type: Type of source (e.g., 'case_name', 'supra_author')

        Returns:
            Pattern info dict or None if not found
        """
        return self.VALID_PATTERNS.get(source_type)


def main():
    """Command-line interface for citation validator"""
    parser = argparse.ArgumentParser(
        description="Validate Bluebook short form citations"
    )
    parser.add_argument(
        "--citation",
        type=str,
        help="Single citation to validate"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="File containing citations (one per line)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed validation information"
    )
    parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    validator = BluebookCitationValidator()

    # Process single citation
    if args.citation:
        result = validator.validate(args.citation)
        if args.json:
            print(json.dumps({
                "citation": args.citation,
                "is_valid": result.is_valid,
                "citation_type": result.citation_type,
                "rule": result.rule,
                "message": result.message,
                "issues": result.issues
            }, indent=2))
        else:
            print(f"Citation: {args.citation}")
            print(f"Status: {'VALID' if result.is_valid else 'INVALID'}")
            if result.citation_type:
                print(f"Type: {result.citation_type}")
            if result.rule:
                print(f"Rule: {result.rule}")
            print(f"Message: {result.message}")
            if result.issues and args.verbose:
                print("Issues:")
                for issue in result.issues:
                    print(f"  - {issue}")

    # Process file
    elif args.file:
        try:
            with open(args.file, 'r') as f:
                citations = [line.strip() for line in f if line.strip()]

            results = validator.validate_batch(citations)

            if args.json:
                output = []
                for citation, result in results:
                    output.append({
                        "citation": citation,
                        "is_valid": result.is_valid,
                        "citation_type": result.citation_type,
                        "rule": result.rule,
                        "message": result.message,
                        "issues": result.issues
                    })
                print(json.dumps(output, indent=2))
            else:
                valid_count = sum(1 for _, r in results if r.is_valid)
                total_count = len(results)

                print(f"Validation Results: {valid_count}/{total_count} valid\n")

                for citation, result in results:
                    status = "VALID" if result.is_valid else "INVALID"
                    print(f"[{status}] {citation}")
                    if args.verbose or not result.is_valid:
                        print(f"  Message: {result.message}")
                        if result.citation_type:
                            print(f"  Type: {result.citation_type}")
                        if result.rule:
                            print(f"  Rule: {result.rule}")
                        if result.issues:
                            print("  Issues:")
                            for issue in result.issues:
                                print(f"    - {issue}")
                    print()

        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found")
            exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
