#!/usr/bin/env python3
"""Test parenthetical capitalization fix."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.citation_validator import CitationValidator

# Test the deterministic check directly
validator = CitationValidator.__new__(CitationValidator)

test_cases = [
    ('Crusey, supra note 21 at 515 ("Unlike a copyright infringement claim under Section 501, a Section 1202 claim requires no prerequisite copyright registration.").',
     'Should NOT flag - starts with quote mark'),
    ('Smith v. Jones (Discussing the issue).',
     'SHOULD flag - capital D outside quotes'),
    ('Smith v. Jones (discussing the issue).',
     'Should NOT flag - lowercase d'),
    ('Smith v. Jones ("The court held...").',
     'Should NOT flag - starts with quote mark'),
]

print('DETERMINISTIC PARENTHETICAL CHECK TEST')
print('=' * 70)
print()

all_pass = True

for citation, expected in test_cases:
    errors = validator._check_parenthetical_capitalization(citation)

    # Determine if test passes
    should_flag = 'SHOULD flag' in expected
    did_flag = len(errors) > 0
    passes = (should_flag == did_flag)

    status = '✓ PASS' if passes else '✗ FAIL'
    if not passes:
        all_pass = False

    print(f'{status}: {citation[:60]}...')
    print(f'       Expected: {expected}')
    print(f'       Got: {len(errors)} error(s)')
    if errors:
        print(f'       Error: {errors[0]["error_type"]}')
    print()

print('=' * 70)
if all_pass:
    print('✓ ALL TESTS PASSED')
else:
    print('✗ SOME TESTS FAILED')
    sys.exit(1)
