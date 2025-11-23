#!/usr/bin/env python3
"""
Verify completeness of Redbook analysis
"""

import json
from pathlib import Path

analysis_path = Path("/home/user/slr/SLRinator/output/analysis/redbook_ALL_115_RULES_FIXED.json")
bluebook_path = Path("/home/user/slr/SLRinator/config/rules/Bluebook.json")

# Load files
with open(analysis_path, 'r') as f:
    analysis = json.load(f)

with open(bluebook_path, 'r') as f:
    bluebook = json.load(f)

# Verify completeness
redbook_rules = bluebook['redbook']['rules']
analysis_rules = analysis['rules']

print("=" * 70)
print("REDBOOK ANALYSIS VERIFICATION REPORT")
print("=" * 70)
print()

# Check rule count
print(f"✓ Source rules count: {len(redbook_rules)}")
print(f"✓ Analysis rules count: {len(analysis_rules)}")
print(f"✓ Match: {len(redbook_rules) == len(analysis_rules)}")
print()

# Verify all rule IDs present
source_ids = set(r['id'] for r in redbook_rules)
analysis_ids = set(r['id'] for r in analysis_rules)
missing_ids = source_ids - analysis_ids
extra_ids = analysis_ids - source_ids

if missing_ids:
    print(f"✗ MISSING RULE IDs: {missing_ids}")
else:
    print(f"✓ All {len(source_ids)} rule IDs present in analysis")

if extra_ids:
    print(f"✗ EXTRA RULE IDs: {extra_ids}")
print()

# Error type statistics
total_errors = sum(len(r['error_types']) for r in analysis_rules)
print(f"✓ Total error types: {total_errors}")
print(f"✓ Minimum requirement (200): {'PASS' if total_errors >= 200 else 'FAIL'}")
print(f"✓ Exceeds requirement by: {total_errors - 200}")
print()

# Verify RB 1.12 critical fix
rb_1_12 = next((r for r in analysis_rules if r['id'] == '1.12'), None)
if rb_1_12:
    has_critical_fix = rb_1_12.get('critical_fix', False)
    has_required_text = 'CRITICAL FIX APPLIED' in rb_1_12['text']
    has_see_generally_error = any('see_generally' in e['name'] for e in rb_1_12['error_types'])
    
    print("RB 1.12 Critical Fix Verification:")
    print(f"  ✓ Rule found: True")
    print(f"  ✓ critical_fix flag: {has_critical_fix}")
    print(f"  ✓ Text contains CRITICAL FIX: {has_required_text}")
    print(f"  ✓ Has see_generally error types: {has_see_generally_error}")
    print(f"  ✓ Error type count: {len(rb_1_12['error_types'])}")
    
    # Show error types for RB 1.12
    print(f"\n  RB 1.12 Error Types:")
    for et in rb_1_12['error_types']:
        print(f"    - {et['name']} ({et['severity']})")
else:
    print("✗ RB 1.12 NOT FOUND")
print()

# Pattern and example coverage
rules_with_patterns = sum(1 for r in analysis_rules if r['patterns']['detect'] or r['patterns']['validate'])
rules_with_examples = sum(1 for r in analysis_rules if r['examples']['incorrect'] or r['examples']['correct'])

print("Coverage Statistics:")
print(f"  ✓ Rules with detection patterns: {rules_with_patterns}/{len(analysis_rules)} ({100*rules_with_patterns/len(analysis_rules):.1f}%)")
print(f"  ✓ Rules with examples: {rules_with_examples}/{len(analysis_rules)} ({100*rules_with_examples/len(analysis_rules):.1f}%)")
print()

# Severity distribution
severity_counts = {}
for rule in analysis_rules:
    for error in rule['error_types']:
        severity = error['severity']
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

print("Error Severity Distribution:")
for severity, count in sorted(severity_counts.items()):
    pct = 100 * count / total_errors
    print(f"  ✓ {severity.capitalize()}: {count} ({pct:.1f}%)")
print()

# Auto-fix capability
autofix_counts = {}
for rule in analysis_rules:
    for error in rule['error_types']:
        autofix = error.get('auto_fix', 'unknown')
        autofix_counts[autofix] = autofix_counts.get(autofix, 0) + 1

print("Auto-Fix Capability:")
for capability, count in sorted(autofix_counts.items()):
    pct = 100 * count / total_errors
    print(f"  ✓ {capability}: {count} ({pct:.1f}%)")
print()

print("=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)
print()
print(f"Analysis file: {analysis_path}")
print(f"Summary file: {analysis_path.parent / 'REDBOOK_ANALYSIS_SUMMARY.md'}")

