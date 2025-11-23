#!/usr/bin/env python3
"""
Fix RB 1.12 error types to reflect critical fix
"""

import json
from pathlib import Path

analysis_path = Path("/home/user/slr/SLRinator/output/analysis/redbook_ALL_115_RULES_FIXED.json")

with open(analysis_path, 'r') as f:
    analysis = json.load(f)

# Find and fix RB 1.12
for rule in analysis['rules']:
    if rule['id'] == '1.12':
        # Correct error types for RB 1.12
        rule['error_types'] = [
            {
                "id": "RB_1.12_E1",
                "name": "see_generally_missing_parenthetical",
                "description": "'See generally' citation missing required explanatory parenthetical",
                "severity": "error",
                "auto_fix": "no",
                "comment_required": "[AA:] Add explanatory parenthetical required for 'see generally' signal"
            },
            {
                "id": "RB_1.12_E2",
                "name": "cf_has_parenthetical",
                "description": "'Cf.' citation incorrectly includes explanatory parenthetical",
                "severity": "error",
                "auto_fix": "yes"
            },
            {
                "id": "RB_1.12_E3",
                "name": "see_generally_weak_parenthetical",
                "description": "'See generally' parenthetical too vague or generic",
                "severity": "warning",
                "auto_fix": "no"
            },
            {
                "id": "RB_1.12_E4",
                "name": "see_generally_parenthetical_not_substantive",
                "description": "'See generally' parenthetical not substantive enough to explain background relevance",
                "severity": "warning",
                "auto_fix": "no"
            }
        ]
        print(f"Fixed RB 1.12 error types: {len(rule['error_types'])} errors defined")
        break

# Recalculate total error types
analysis['total_error_types'] = sum(len(r['error_types']) for r in analysis['rules'])

# Write corrected output
with open(analysis_path, 'w') as f:
    json.dump(analysis, f, indent=2)

print(f"Corrected RB 1.12 error types")
print(f"New total error types: {analysis['total_error_types']}")
