#!/usr/bin/env python3
"""
Example validation scripts demonstrating how to use the T6-T8 analysis data.
Shows practical applications of the regex patterns and error detection.
"""

import json
import re
from pathlib import Path

def load_analysis():
    """Load the T6-T8 analysis data."""
    analysis_path = Path("/home/user/slr/SLRinator/output/analysis/tables_6-8_analysis.json")
    with open(analysis_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_t6_in_case_name(case_name, analysis_data):
    """
    Validate T6 abbreviations in a case name.
    Returns list of violations found.
    """
    violations = []

    for entry in analysis_data['T6']:
        word = entry['word']
        abbr = entry['abbreviation']
        regex_long = entry['regex_long']

        # Check if unabbreviated form exists
        pattern = re.compile(regex_long)
        matches = pattern.findall(case_name)

        if matches:
            violations.append({
                'word': word,
                'expected_abbr': abbr,
                'found': matches,
                'error': f"Use '{abbr}' instead of '{word}' in case names",
                'location': case_name
            })

    return violations

def validate_t7_court_name(court_name, analysis_data):
    """
    Validate T7 court name abbreviations.
    Returns list of violations found.
    """
    violations = []

    for entry in analysis_data['T7']:
        full_name = entry['word']
        abbr = entry['abbreviation']
        regex_long = entry['regex_long']

        # Remove parenthetical notes for matching
        full_name_clean = re.sub(r'\s*\([^)]+\)', '', full_name)

        # Check if unabbreviated form exists
        if full_name_clean.lower() in court_name.lower():
            violations.append({
                'court': full_name,
                'expected_abbr': abbr,
                'found': court_name,
                'error': f"Use '{abbr}' instead of full court name",
                'location': court_name
            })

    return violations

def validate_t8_explanatory_phrase(parenthetical, analysis_data):
    """
    Validate T8 explanatory phrase abbreviations.
    Returns list of violations found.
    """
    violations = []

    for entry in analysis_data['T8']:
        phrase = entry['word']
        abbr = entry['abbreviation']

        # Skip if phrase doesn't require abbreviation
        if phrase == abbr:
            continue

        # Check if unabbreviated form exists
        if phrase.lower() in parenthetical.lower():
            violations.append({
                'phrase': phrase,
                'expected_abbr': abbr,
                'found': parenthetical,
                'error': f"Use '{abbr}' instead of '{phrase}'",
                'location': parenthetical
            })

    return violations

def check_missing_apostrophes(text, analysis_data):
    """
    Check for common apostrophe errors in abbreviations.
    """
    errors = []

    # Check T6 entries with apostrophes
    for entry in analysis_data['T6']:
        abbr = entry['abbreviation']
        if "'" not in abbr:
            continue

        # Create pattern for version without apostrophe
        no_apos = abbr.replace("'", "")
        pattern = r'\b' + re.escape(no_apos) + r'\b'

        matches = re.finditer(pattern, text)
        for match in matches:
            errors.append({
                'found': match.group(),
                'expected': abbr,
                'position': match.start(),
                'error': f"Missing apostrophe: use '{abbr}' instead of '{no_apos}'"
            })

    return errors

def example_case_name_validation():
    """Example: Validate case names."""
    print("=" * 60)
    print("EXAMPLE 1: Case Name Validation (T6)")
    print("=" * 60)

    analysis = load_analysis()

    test_cases = [
        "Association of American Railroads v. Department of Transportation",
        "International Business Machines Corporation v. United States",
        "Committee for Public Education v. Superintendent of Documents",
        "Federal Communications Commission v. AT&T Inc."  # Correct
    ]

    for case_name in test_cases:
        print(f"\nCase: {case_name}")
        violations = validate_t6_in_case_name(case_name, analysis)

        if violations:
            print(f"  ❌ Found {len(violations)} violation(s):")
            for v in violations:
                print(f"     - {v['error']}")
        else:
            print("  ✓ All T6 abbreviations correct")

def example_court_name_validation():
    """Example: Validate court names."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Court Name Validation (T7)")
    print("=" * 60)

    analysis = load_analysis()

    test_courts = [
        "United States Supreme Court",
        "District Court for the Southern District of New York",
        "Court of Appeals for the Second Circuit",
        "Bankruptcy Court"  # Correct (needs more context)
    ]

    for court in test_courts:
        print(f"\nCourt: {court}")
        violations = validate_t7_court_name(court, analysis)

        if violations:
            print(f"  ❌ Found {len(violations)} violation(s):")
            for v in violations[:3]:  # Show first 3
                print(f"     - {v['error']}")
        else:
            print("  ✓ Court name appears acceptable")

def example_explanatory_phrase_validation():
    """Example: Validate explanatory phrases."""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Explanatory Phrase Validation (T8)")
    print("=" * 60)

    analysis = load_analysis()

    test_phrases = [
        "(certiorari denied)",  # Should be "cert. denied"
        "(reversed on other grounds)",  # Should be "rev'd on other grounds"
        "(affirmed)",  # Should be "aff'd"
        "(cert. denied)",  # Correct
        "(vacated)"  # Correct (no abbreviation needed)
    ]

    for phrase in test_phrases:
        print(f"\nPhrase: {phrase}")
        violations = validate_t8_explanatory_phrase(phrase, analysis)

        if violations:
            print(f"  ❌ Found {len(violations)} violation(s):")
            for v in violations:
                print(f"     - {v['error']}")
        else:
            print("  ✓ Phrase is correctly abbreviated")

def example_apostrophe_checking():
    """Example: Check for missing apostrophes."""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Missing Apostrophe Detection")
    print("=" * 60)

    analysis = load_analysis()

    test_text = """
    The Assn filed a motion with the Commn. The Atty for the Dept
    argued that the Intl treaty required Natl compliance.
    """

    print(f"\nText: {test_text.strip()}")
    errors = check_missing_apostrophes(test_text, analysis)

    if errors:
        print(f"\n❌ Found {len(errors)} apostrophe error(s):")
        for err in errors:
            print(f"   - {err['error']}")
    else:
        print("\n✓ No apostrophe errors found")

def show_statistics():
    """Show statistics from the analysis."""
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)

    analysis = load_analysis()

    print(f"\nTotal entries: {analysis['metadata']['total_entries']}")

    # Count entries with apostrophes
    t6_with_apos = sum(1 for e in analysis['T6'] if "'" in e['abbreviation'])
    t7_with_apos = sum(1 for e in analysis['T7'] if "'" in e['abbreviation'])
    t8_with_apos = sum(1 for e in analysis['T8'] if "'" in e['abbreviation'])

    print(f"\nEntries with apostrophes:")
    print(f"  T6: {t6_with_apos}/{len(analysis['T6'])}")
    print(f"  T7: {t7_with_apos}/{len(analysis['T7'])}")
    print(f"  T8: {t8_with_apos}/{len(analysis['T8'])}")

    # Count entries where phrase = abbreviation (no abbreviation needed)
    t8_no_abbr = sum(1 for e in analysis['T8'] if e['word'] == e['abbreviation'])
    print(f"\nT8 phrases requiring NO abbreviation: {t8_no_abbr}/{len(analysis['T8'])}")

    # Most complex regex patterns
    print("\nMost complex regex patterns:")
    complex_entries = sorted(analysis['T6'], key=lambda x: len(x['regex_long']), reverse=True)[:3]
    for i, entry in enumerate(complex_entries, 1):
        print(f"  {i}. {entry['word']}: {entry['regex_long'][:60]}...")

def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("BLUEBOOK T6-T8 VALIDATION EXAMPLES")
    print("=" * 60)

    example_case_name_validation()
    example_court_name_validation()
    example_explanatory_phrase_validation()
    example_apostrophe_checking()
    show_statistics()

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
