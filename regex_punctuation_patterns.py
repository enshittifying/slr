"""
BLUEBOOK PUNCTUATION ERROR DETECTION - PYTHON REGEX PATTERNS
Extracted from: /home/user/slr/reference_files/Bluebook.json

Usage: Apply these patterns to legal documents to detect common punctuation errors
Priority levels: CRITICAL > HIGH > MEDIUM > LOW
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from datetime import datetime


@dataclass
class PunctuationError:
    """Data class for punctuation errors"""
    priority: str
    type: str
    description: str
    index: int
    line: int
    match: str
    context: str
    fix: Optional[str] = None


# ============================================================================
# CRITICAL PRIORITY - Must Fix
# ============================================================================

CRITICAL_PATTERNS = {
    'nested_parentheses': {
        'pattern': r'\([^)]*\([^)]*\)[^)]*\)',
        'description': 'Nested parentheses detected. Use square brackets for inner parenthetical.',
        'example': 'Wrong: (citing (for example, ...)); Right: (citing [for example, ...])',
        'regex_obj': None  # Will be compiled
    },

    'four_dots': {
        'pattern': r'\.\.\.\.',
        'description': 'Four dots detected. Use exactly three dots for ellipsis.',
        'example': 'Wrong: ....; Right: ...',
        'regex_obj': None
    },

    'missing_degrees_periods': {
        'pattern': r'\b(JD|PhD|MBA|LLM|LLD|MSL|BCL)(?!\.)',
        'description': 'Degree abbreviation missing periods per SLR Rule.',
        'example': 'Wrong: PhD; Right: Ph.D.',
        'regex_obj': None
    },

    'signal_comma_vs_semicolon': {
        'pattern': r'(See|Accord|See also|But see)\s+[^;]*\d{1,4}\s*\)\s*,\s*(See|Accord|See also|But see)\s+',
        'description': 'Multiple sources with same signal should be separated by semicolon, not comma.',
        'example': 'Wrong: See X, Y; Right: See X; See Y or See X, Y, and Z',
        'regex_obj': None,
        'note': 'Context-aware checking recommended'
    },

    'compare_contrast_comma': {
        'pattern': r'Compare\s+[^;]*\),\s*with\s+[^;]*\)',
        'description': 'Compare/contrast citations must be separated by semicolon, not comma.',
        'example': 'Wrong: Compare X, with Y; Right: Compare X; with Y',
        'regex_obj': None
    },

    'double_section_symbol_range': {
        'pattern': r'§§\s*\d+-\d+',
        'description': 'Hyphenated ranges use single § symbol, not double.',
        'example': 'Wrong: §§ 4001-03; Right: § 4001-03',
        'regex_obj': None
    },

    'missing_comma_repeated_digits': {
        'pattern': r'§\s*\d+([a-z])\1(?!\s*,)',
        'description': 'Repeated digits in statute must be separated by comma.',
        'example': 'Wrong: § 1490dd; Right: § 1490, dd',
        'regex_obj': None
    }
}


# ============================================================================
# HIGH PRIORITY - Important Spacing & Formatting
# ============================================================================

HIGH_PRIORITY_PATTERNS = {
    'period_after_section_symbol': {
        'pattern': r'([§¶]\s*\d+)\.',
        'description': 'No period after section or paragraph symbols.',
        'example': 'Wrong: § 1234.; Right: § 1234',
        'regex_obj': None
    },

    'no_space_after_comma': {
        'pattern': r',([^\s\d.\n])',
        'description': 'Missing space after comma.',
        'example': 'Wrong: Smith,Johnson; Right: Smith, Johnson',
        'regex_obj': None
    },

    'space_before_comma': {
        'pattern': r'\s+,',
        'description': 'Space before comma not allowed.',
        'example': 'Wrong: text ,citation; Right: text, citation',
        'regex_obj': None
    },

    'no_space_after_semicolon': {
        'pattern': r';([^\s.\n])',
        'description': 'Missing space after semicolon.',
        'example': 'Wrong: X;Y; Right: X; Y',
        'regex_obj': None
    },

    'double_punctuation': {
        'pattern': r'([.,;:?!])\1+',
        'description': 'Consecutive duplicate punctuation marks.',
        'example': 'Wrong: citation..; Right: citation.',
        'regex_obj': None
    },

    'space_before_period': {
        'pattern': r'\s+\.(?!\.)',
        'description': 'Space before period not allowed.',
        'example': 'Wrong: text .; Right: text.',
        'regex_obj': None
    },

    'multiple_spaces': {
        'pattern': r'  +',
        'description': 'Multiple consecutive spaces.',
        'example': 'Wrong: text  citation; Right: text citation',
        'regex_obj': None
    },

    'em_dash_spacing': {
        'pattern': r'(\w+)\s+—\s+(\()',
        'description': 'Em dash before parenthetical should have single space.',
        'example': 'Check em dash spacing around parentheticals',
        'regex_obj': None
    }
}


# ============================================================================
# MEDIUM PRIORITY - Style & Consistency Issues
# ============================================================================

MEDIUM_PRIORITY_PATTERNS = {
    'ellipsis_at_quote_start': {
        'pattern': r'[""]\.\.\.\s',
        'description': 'Do not start quote with ellipsis if material starts midsentence.',
        'example': 'Wrong: "...the case"; Right: "[t]he case"',
        'regex_obj': None,
        'note': 'Requires context-aware checking'
    },

    'capital_in_parenthetical': {
        'pattern': r'\(\s*[A-Z]',
        'description': 'Parentheticals should start with lowercase unless proper noun.',
        'example': 'Wrong: (Finding that...); Right: (finding that...)',
        'regex_obj': None
    },

    'missing_at_page': {
        'pattern': r'(\d+\s+[A-Z][\w\s]*)\s+(\d{4})\s+(\d+)',
        'description': 'Missing "at" before page number in periodical citation.',
        'example': 'Wrong: 23 Nat\'l L.J. (2020) 12; Right: 23 Nat\'l L.J., at 12 (2020)',
        'regex_obj': None,
        'note': 'Check format: Volume Name Year at Page'
    },

    'comma_missing_semicolon': {
        'pattern': r'(See|Accord|But see|Cf)\s+[^;]*\),\s+([A-Z](?:See|Accord|But|Cf))',
        'description': 'Citations of same signal type should use semicolon, not comma.',
        'example': 'Wrong: See X, But see Y; Right: See X; But see Y',
        'regex_obj': None
    },

    'mismatched_quotes': {
        'pattern': r'["""][^"]*\'[^\']*["""]|\'\'[^\']*"[^"]*\'\'',
        'description': 'Inconsistent quotation mark pairing.',
        'example': 'Wrong: "...\' ...\" \'; Right: "...\' ...\'"',
        'regex_obj': None
    },

    'improperly_situated_brackets': {
        'pattern': r'\[\s*[a-z][^\[\]]*\s*\](?!\s*\))',
        'description': 'Brackets should primarily appear within parentheticals.',
        'regex_obj': None,
        'note': 'May have false positives for other uses of brackets'
    },

    'missing_comma_before_no': {
        'pattern': r'\d+\s+[A-Z][\w\s]*(?:no|number)\s+\d+',
        'description': 'Comma required before issue number in periodicals.',
        'example': 'Wrong: 23 Nat\'l L.J. no. 5; Right: 23 Nat\'l L.J., no. 5',
        'regex_obj': None
    },

    'dash_instead_of_colon_subtitle': {
        'pattern': r'([A-Z][\w\s]*)\s+–\s+([A-Z][\w\s]*)',
        'description': 'Subtitles should use colon, not dash or en-dash.',
        'example': 'Wrong: Title – Subtitle; Right: Title: Subtitle',
        'regex_obj': None
    }
}


# ============================================================================
# LOW PRIORITY - Minor Style Preferences
# ============================================================================

LOW_PRIORITY_PATTERNS = {
    'usc_spacing': {
        'pattern': r'U\s*\.\s*S\s*\.\s*C\s*\.',
        'description': 'Correct spacing in U.S.C. abbreviation.',
        'example': 'Should be: U.S.C. (with periods)',
        'regex_obj': None
    },

    'id_formatting': {
        'pattern': r'\bId\b(?!\.)',
        'description': 'Id. requires a period.',
        'example': 'Wrong: Id; Right: Id.',
        'regex_obj': None
    },

    'long_parenthetical': {
        'pattern': r'\([^)]{200,}\)',
        'description': 'Parentheticals should be under 50 words (~300 characters).',
        'example': 'Consider breaking into separate sentence if over 50 words',
        'regex_obj': None
    },

    'year_in_parentheses': {
        'pattern': r'([A-Z]\.S\.\s+\d+)\s+(\d{4})',
        'description': 'Year should be in parentheses at end of citation.',
        'example': 'Wrong: 410 U.S. 113 1973; Right: 410 U.S. 113 (1973)',
        'regex_obj': None
    }
}


# ============================================================================
# COMPOSITE PATTERNS - Multi-element checks
# ============================================================================

COMPOSITE_PATTERNS = {
    'case_citation_format': {
        'pattern': r'([A-Za-z\s]+v\.\s+[A-Za-z\s]+),\s+(\d+)\s+([A-Z]\.[\w\.]+)\s+(\d+)(?:\s*,?\s*(\d+))?\s+\(([^)]+)\)',
        'description': 'Verify complete case citation: Name, Vol. Reporter Page (Court Year)',
        'components': ['caseName', 'volume', 'reporter', 'firstPage', 'pinpoint', 'courtYear'],
        'regex_obj': None
    },

    'statute_citation_format': {
        'pattern': r'(\d+)\s+(U\.S\.C\.(?:\s*\w+)?)\s+([§¶])\s+(\d+[\w\-\.]*)',
        'description': 'Verify statute format: Volume Code § Section',
        'components': ['volume', 'code', 'symbol', 'section'],
        'regex_obj': None
    },

    'periodical_citation_format': {
        'pattern': r'(\d+)\s+([A-Z][\w\'.\s]+?),\s+(?:no\.\s+(\d+),\s+)?at\s+(\d+)\s+\((\d{4})\)',
        'description': 'Verify periodical format: Vol. Name, [no. X,] at Page (Year)',
        'components': ['volume', 'journal', 'issueNum', 'page', 'year'],
        'regex_obj': None
    },

    'url_formatting': {
        'pattern': r'(https?:\/\/[^\s)]+)(?:\s+\((?:last\s+visited\s+)?([^)]+)\))?',
        'description': 'Verify URL with optional date: http://...url... (last visited Date)',
        'components': ['url', 'date'],
        'regex_obj': None
    }
}


# ============================================================================
# INITIALIZATION - Compile all patterns
# ============================================================================

def _compile_patterns():
    """Pre-compile all regex patterns for better performance"""
    for patterns_dict in [CRITICAL_PATTERNS, HIGH_PRIORITY_PATTERNS, MEDIUM_PRIORITY_PATTERNS, LOW_PRIORITY_PATTERNS, COMPOSITE_PATTERNS]:
        for key, pattern_obj in patterns_dict.items():
            pattern_obj['regex_obj'] = re.compile(pattern_obj['pattern'])


_compile_patterns()


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def find_punctuation_errors(text: str, pattern: Dict, context_length: int = 50) -> List[Tuple[int, int, str]]:
    """
    Find all matches of a pattern with line numbers and context.

    Args:
        text: The text to search
        pattern: Pattern dictionary with 'regex_obj' key
        context_length: Characters before/after match for context

    Returns:
        List of tuples: (index, line_number, match_text, context)
    """
    matches = []
    regex = pattern['regex_obj']

    for match in regex.finditer(text):
        line_num = text[:match.start()].count('\n') + 1
        start = max(0, match.start() - context_length)
        end = min(len(text), match.end() + context_length)
        context = text[start:end]

        matches.append({
            'index': match.start(),
            'line': line_num,
            'match': match.group(0),
            'context': context,
            'column': match.start() - text.rfind('\n', 0, match.start())
        })

    return matches


def check_critical_punctuation(text: str) -> List[PunctuationError]:
    """
    Check text for all critical punctuation errors.

    Args:
        text: The text to check

    Returns:
        List of PunctuationError objects
    """
    errors = []

    for key, pattern_obj in CRITICAL_PATTERNS.items():
        matches = find_punctuation_errors(text, pattern_obj)

        for match in matches:
            error = PunctuationError(
                priority='CRITICAL',
                type=key,
                description=pattern_obj['description'],
                **match
            )
            errors.append(error)

    return errors


def check_all_punctuation(text: str) -> Dict[str, List[PunctuationError]]:
    """
    Check text for all punctuation errors across all priority levels.

    Args:
        text: The text to check

    Returns:
        Dictionary with priority levels as keys, error lists as values
    """
    errors = {
        'critical': [],
        'high': [],
        'medium': [],
        'low': []
    }

    # Check critical patterns
    for key, pattern_obj in CRITICAL_PATTERNS.items():
        matches = find_punctuation_errors(text, pattern_obj)
        for match in matches:
            error = PunctuationError(
                priority='CRITICAL',
                type=key,
                description=pattern_obj['description'],
                **match
            )
            errors['critical'].append(error)

    # Check high priority patterns
    for key, pattern_obj in HIGH_PRIORITY_PATTERNS.items():
        matches = find_punctuation_errors(text, pattern_obj)
        for match in matches:
            error = PunctuationError(
                priority='HIGH',
                type=key,
                description=pattern_obj['description'],
                **match
            )
            errors['high'].append(error)

    # Check medium priority patterns
    for key, pattern_obj in MEDIUM_PRIORITY_PATTERNS.items():
        matches = find_punctuation_errors(text, pattern_obj)
        for match in matches:
            error = PunctuationError(
                priority='MEDIUM',
                type=key,
                description=pattern_obj['description'],
                **match
            )
            errors['medium'].append(error)

    # Check low priority patterns
    for key, pattern_obj in LOW_PRIORITY_PATTERNS.items():
        matches = find_punctuation_errors(text, pattern_obj)
        for match in matches:
            error = PunctuationError(
                priority='LOW',
                type=key,
                description=pattern_obj['description'],
                **match
            )
            errors['low'].append(error)

    return errors


def generate_punctuation_report(text: str) -> Dict:
    """
    Generate comprehensive punctuation error report.

    Args:
        text: The text to analyze

    Returns:
        Dictionary with error report and summary statistics
    """
    errors_by_priority = check_all_punctuation(text)

    report = {
        'timestamp': datetime.now().isoformat(),
        'text_length': len(text),
        'errors': errors_by_priority,
        'summary': {
            'critical_count': len(errors_by_priority['critical']),
            'high_count': len(errors_by_priority['high']),
            'medium_count': len(errors_by_priority['medium']),
            'low_count': len(errors_by_priority['low']),
            'total_errors': (
                len(errors_by_priority['critical']) +
                len(errors_by_priority['high']) +
                len(errors_by_priority['medium']) +
                len(errors_by_priority['low'])
            )
        }
    }

    return report


def print_error_report(report: Dict, include_context: bool = True) -> str:
    """
    Format error report as readable string.

    Args:
        report: Report dictionary from generate_punctuation_report
        include_context: Whether to include match context

    Returns:
        Formatted report string
    """
    output = []
    output.append(f"Punctuation Error Report - {report['timestamp']}")
    output.append(f"Text length: {report['text_length']} characters")
    output.append("")

    # Summary
    summary = report['summary']
    output.append("SUMMARY:")
    output.append(f"  Critical errors: {summary['critical_count']}")
    output.append(f"  High priority: {summary['high_count']}")
    output.append(f"  Medium priority: {summary['medium_count']}")
    output.append(f"  Low priority: {summary['low_count']}")
    output.append(f"  Total: {summary['total_errors']}")
    output.append("")

    # Detailed errors by priority
    for priority in ['critical', 'high', 'medium', 'low']:
        errors = report['errors'][priority]
        if errors:
            output.append(f"\n{priority.upper()} PRIORITY ERRORS ({len(errors)}):")
            output.append("-" * 70)

            for error in errors:
                output.append(f"\nType: {error.type}")
                output.append(f"Line: {error.line}")
                output.append(f"Description: {error.description}")
                output.append(f"Match: {repr(error.match)}")
                if include_context:
                    output.append(f"Context: ...{error.context}...")
                output.append("")

    return "\n".join(output)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example text with errors
    example_text = """
    See Smith v. Jones, 410 U.S. 113, 115 (1973), Doe v. Bolton, 410 U.S. 179 (1973).

    The statute provides that 42 U.S.C. § 1234. must be followed.

    (citing (for example, the Hippocratic Oath)).

    The author noted "...the case was important" in the article.
    """

    # Generate report
    report = generate_punctuation_report(example_text)

    # Print report
    print(print_error_report(report))
