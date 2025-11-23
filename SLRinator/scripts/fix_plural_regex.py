#!/usr/bin/env python3
"""
Fix Plural Handling in Regex Patterns

Converts improper plural notation to proper regex:
❌ Bad:  "court(s)"  - matches literal "(s)"
✅ Good: "courts?"   - matches "court" or "courts"
✅ Good: "(court|courts)" - explicit OR
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

def find_improper_plurals(pattern: str) -> List[Tuple[str, str]]:
    """Find patterns with improper plural notation like (s), (es), (ies)."""
    issues = []

    # Check for common improper plural patterns
    improper_patterns = [
        (r'(\w+)\(s\)', r'\1s?'),  # word(s) → words?
        (r'(\w+)\(es\)', r'\1(es)?'),  # word(es) → word(es)?
        (r'(\w+)y\(ies\)', r'(\1y|\1ies)'),  # wordy(ies) → (wordy|wordies)
        (r'(\w+)\(\'s\)', r"\1('s)?"),  # word('s) → word('s)?
    ]

    for improper, proper_template in improper_patterns:
        matches = re.finditer(improper, pattern)
        for match in matches:
            bad_part = match.group(0)
            # Generate the proper fix
            if '(s)' in bad_part:
                good_part = bad_part.replace('(s)', 's?')
            elif '(es)' in bad_part:
                good_part = bad_part.replace('(es)', '(es)?')
            elif '(ies)' in bad_part:
                base = match.group(1)
                good_part = f'({base}y|{base}ies)'
            elif "('s)" in bad_part:
                good_part = bad_part.replace("('s)", "('s)?")
            else:
                good_part = bad_part

            issues.append((bad_part, good_part))

    return issues

def fix_regex_pattern(pattern: str) -> Tuple[str, List[str]]:
    """Fix improper plural notation in a regex pattern."""
    if not pattern:
        return pattern, []

    fixes = []
    fixed_pattern = pattern

    # Fix (s) → s?
    if '(s)' in fixed_pattern and '?' not in fixed_pattern[fixed_pattern.index('(s)')+3:fixed_pattern.index('(s)')+4] if fixed_pattern.index('(s)')+3 < len(fixed_pattern) else True:
        old = fixed_pattern
        fixed_pattern = fixed_pattern.replace('(s)', 's?')
        if old != fixed_pattern:
            fixes.append("Changed '(s)' to 's?' for proper optional plural")

    # Fix (es) → (es)?
    if '(es)' in fixed_pattern and not fixed_pattern.startswith('(') or '|(es)' in fixed_pattern:
        # This might be intentional OR statement, check context
        if re.search(r'\w+\(es\)', fixed_pattern):
            old = fixed_pattern
            fixed_pattern = re.sub(r'(\w+)\(es\)', r'\1(es)?', fixed_pattern)
            if old != fixed_pattern:
                fixes.append("Changed word(es) to word(es)? for optional plural")

    # Fix wordy(ies) → (wordy|wordies)
    if '(ies)' in fixed_pattern:
        old = fixed_pattern
        fixed_pattern = re.sub(r'(\w+)y\(ies\)', r'(\1y|\1ies)', fixed_pattern)
        if old != fixed_pattern:
            fixes.append("Changed wordy(ies) to (wordy|wordies) for proper plural")

    # Fix word('s) → word('s)?
    if "('s)" in fixed_pattern:
        old = fixed_pattern
        fixed_pattern = re.sub(r"(\w+)\('s\)", r"\1('s)?", fixed_pattern)
        if old != fixed_pattern:
            fixes.append("Changed word('s) to word('s)? for optional possessive")

    return fixed_pattern, fixes

def analyze_framework_plurals():
    """Analyze the framework for improper plural handling."""

    framework_path = Path(__file__).parent.parent / "config" / "error_detection_framework_ENHANCED.json"

    with open(framework_path, 'r') as f:
        framework = json.load(f)

    print("="*80)
    print("ANALYZING REGEX PATTERNS FOR IMPROPER PLURAL NOTATION")
    print("="*80)

    all_errors = framework['bluebook_errors'] + framework['redbook_errors']

    issues_found = []

    for error in all_errors:
        pattern = error.get('regex_detect')
        if not pattern:
            continue

        # Check for improper plurals
        improper = find_improper_plurals(pattern)

        if improper:
            issues_found.append({
                'error_id': error.get('error_id'),
                'rule': error.get('rule_id'),
                'description': error.get('description', '')[:60],
                'pattern': pattern,
                'issues': improper
            })

    print(f"\n📊 Found {len(issues_found)} patterns with improper plural notation\n")

    if issues_found:
        print("Sample Issues:\n")
        for i, issue in enumerate(issues_found[:10], 1):
            print(f"{i}. {issue['error_id']} [{issue['rule']}]")
            print(f"   Description: {issue['description']}...")
            print(f"   Pattern: {issue['pattern'][:80]}...")
            for bad, good in issue['issues']:
                print(f"   ❌ Found: {bad}")
                print(f"   ✅ Should be: {good}")
            print()

    return issues_found

def fix_framework_plurals():
    """Fix all improper plural patterns in the framework."""

    framework_path = Path(__file__).parent.parent / "config" / "error_detection_framework_ENHANCED.json"

    with open(framework_path, 'r') as f:
        framework = json.load(f)

    print("\n" + "="*80)
    print("FIXING PLURAL PATTERNS IN FRAMEWORK")
    print("="*80 + "\n")

    total_fixes = 0
    errors_fixed = 0

    # Fix Bluebook errors
    for error in framework['bluebook_errors']:
        pattern = error.get('regex_detect')
        if pattern:
            fixed, fixes = fix_regex_pattern(pattern)
            if fixes:
                error['regex_detect'] = fixed
                error['regex_fixes_applied'] = fixes
                total_fixes += len(fixes)
                errors_fixed += 1

    # Fix Redbook errors
    for error in framework['redbook_errors']:
        pattern = error.get('regex_detect')
        if pattern:
            fixed, fixes = fix_regex_pattern(pattern)
            if fixes:
                error['regex_detect'] = fixed
                error['regex_fixes_applied'] = fixes
                total_fixes += len(fixes)
                errors_fixed += 1

    # Update metadata
    framework['version'] = '3.2.0'
    if 'enhancements' not in framework:
        framework['enhancements'] = {}

    framework['enhancements']['plural_regex_fixes'] = {
        'errors_fixed': errors_fixed,
        'total_fixes': total_fixes,
        'date': '2025-11-23',
        'description': 'Fixed improper plural notation in regex patterns (s) → s?'
    }

    # Save fixed framework
    output_path = framework_path
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(framework, f, indent=2, ensure_ascii=False)

    print(f"✅ Fixed {errors_fixed} error patterns")
    print(f"✅ Applied {total_fixes} total fixes")
    print(f"✅ Saved to: {output_path.name}")

    return errors_fixed, total_fixes

def check_common_legal_terms():
    """Check common legal terms that should handle plurals properly."""

    print("\n" + "="*80)
    print("COMMON LEGAL TERMS WITH PLURAL FORMS")
    print("="*80 + "\n")

    common_terms = {
        'court': ['court', 'courts'],
        'case': ['case', 'cases'],
        'statute': ['statute', 'statutes'],
        'regulation': ['regulation', 'regulations'],
        'article': ['article', 'articles'],
        'section': ['section', 'sections'],
        'subsection': ['subsection', 'subsections'],
        'paragraph': ['paragraph', 'paragraphs'],
        'party': ['party', 'parties'],
        'authority': ['authority', 'authorities'],
        'entity': ['entity', 'entities'],
        'agency': ['agency', 'agencies'],
    }

    print("Recommended Regex Patterns:\n")

    for singular, forms in common_terms.items():
        if len(forms) == 2:
            singular, plural = forms
            # Generate different pattern options
            patterns = [
                f"{singular}s?",  # Simple optional s
                f"({singular}|{plural})",  # Explicit OR
            ]

            # Handle irregular plurals
            if singular + 's' != plural:
                print(f"⚠️  {singular.upper()} (irregular plural)")
                print(f"   ✅ Use: ({singular}|{plural})")
                print(f"   ❌ Avoid: {singular}(ies) or similar")
            else:
                print(f"✓  {singular.upper()} (regular plural)")
                print(f"   ✅ Use: {singular}s?")
                print(f"   ✅ Or: ({singular}|{plural})")
            print()

if __name__ == '__main__':
    # Analyze first
    issues = analyze_framework_plurals()

    # Show common terms guide
    check_common_legal_terms()

    # Fix if issues found
    if issues:
        print("\n" + "="*80)
        print("APPLYING FIXES")
        print("="*80)

        response = input("\nApply fixes to framework? (y/n): ")
        if response.lower() == 'y':
            errors_fixed, total_fixes = fix_framework_plurals()

            print(f"\n{'='*80}")
            print("SUMMARY")
            print(f"{'='*80}")
            print(f"✅ Framework updated to v3.2.0")
            print(f"✅ Fixed {errors_fixed} error patterns with improper plurals")
            print(f"✅ Total regex improvements: {total_fixes}")
            print(f"\nChanges:")
            print(f"  • (s) → s? (optional plural)")
            print(f"  • (es) → (es)? (optional plural)")
            print(f"  • y(ies) → (y|ies) (irregular plural)")
            print(f"  • ('s) → ('s)? (optional possessive)")
            print(f"{'='*80}\n")
        else:
            print("\nNo changes made.")
    else:
        print("\n✅ No improper plural patterns found! All regex patterns are correct.")
