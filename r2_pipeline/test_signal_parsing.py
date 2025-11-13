#!/usr/bin/env python3
"""Test signal parsing with italic markers."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.citation_parser import CitationParser

test_cases = [
    (
        '*See infra* note 111.',
        'Should preserve leading * in signal'
    ),
    (
        '*See infra* notes 83-98 and accompanying text.',
        'Should preserve leading * with multiple words'
    ),
    (
        'Crusey, *supra* note 21 at 515.',
        'Should preserve italics around supra'
    ),
    (
        'Text before; *See* Case1.',
        'Should preserve * after semicolon'
    ),
]

print('SIGNAL PARSING TEST')
print('=' * 80)
print()

all_pass = True

for footnote_text, description in test_cases:
    parser = CitationParser(footnote_text, footnote_num=1)
    citations = parser.parse()

    print(f'Test: {description}')
    print(f'  Input:  "{footnote_text}"')

    if citations:
        for i, cit in enumerate(citations, 1):
            print(f'  Cite {i}: "{cit.full_text}"')

            # Check if asterisks are preserved
            if '*' in footnote_text and '*' not in cit.full_text:
                print(f'  ✗ FAIL: Asterisks lost!')
                all_pass = False
            elif footnote_text.startswith('*') and not cit.full_text.startswith('*'):
                print(f'  ✗ FAIL: Leading asterisk lost!')
                all_pass = False
            else:
                print(f'  ✓ PASS: Formatting preserved')
    else:
        print(f'  ✗ FAIL: No citations parsed!')
        all_pass = False

    print()

print('=' * 80)
if all_pass:
    print('✓ ALL TESTS PASSED')
else:
    print('✗ SOME TESTS FAILED')
    sys.exit(1)
