#!/usr/bin/env python3
"""Test markdown consecutive marker merging."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.markdown_utils import normalize_markdown_spacing

test_cases = [
    ('*See** infra*', '*See infra*', 'Merge consecutive italics with space (Word XML format)'),
    ('*See**infra*', '*Seeinfra*', 'Merge consecutive italics without space'),
    ('**bold****text**', '**boldtext**', 'Merge consecutive bold'),
    ('[SC]small[/SC][SC]caps[/SC]', '[SC]smallcaps[/SC]', 'Merge consecutive small caps'),
    ('*See** infra* note 131.', '*See infra* note 131.', 'Real-world case from FN82'),
    ('*supra *note', '*supra* note', 'Move trailing space outside'),
]

print('MARKDOWN CONSECUTIVE MARKER MERGING TEST')
print('=' * 80)
print()

all_pass = True

for input_text, expected, description in test_cases:
    result = normalize_markdown_spacing(input_text)
    passes = (result == expected)

    status = '✓ PASS' if passes else '✗ FAIL'
    if not passes:
        all_pass = False

    print(f'{status}: {description}')
    print(f'       Input:    "{input_text}"')
    print(f'       Expected: "{expected}"')
    print(f'       Got:      "{result}"')
    print()

print('=' * 80)
if all_pass:
    print('✓ ALL TESTS PASSED')
else:
    print('✗ SOME TESTS FAILED')
    sys.exit(1)
