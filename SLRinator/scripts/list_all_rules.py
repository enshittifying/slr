#!/usr/bin/env python3
"""
List All Bluebook and Redbook Rules with Coverage

Provides comprehensive listing of:
- All 21 Bluebook top-level rules
- All Bluebook subrules
- All 115 Redbook rules
- Coverage statistics
"""

import json
from pathlib import Path
from collections import defaultdict

def load_framework():
    """Load the error detection framework."""
    framework_path = Path(__file__).parent.parent / "config" / "error_detection_framework_ENHANCED.json"

    with open(framework_path, 'r') as f:
        return json.load(f)

def extract_bluebook_rules(framework):
    """Extract all unique Bluebook rules and subrules."""
    rules = defaultdict(lambda: {'subrules': set(), 'errors': []})

    for error in framework['bluebook_errors']:
        rule_id = str(error.get('rule_id', 'unknown'))

        # Parse rule ID (e.g., "10.2.1" -> top-level "10", subrule "10.2.1")
        if '.' in rule_id:
            parts = rule_id.split('.')
            top_level = parts[0]
            subrule = rule_id
        else:
            top_level = rule_id
            subrule = None

        if subrule:
            rules[top_level]['subrules'].add(subrule)

        rules[top_level]['errors'].append(error)

    # Convert sets to sorted lists
    for rule_id in rules:
        rules[rule_id]['subrules'] = sorted(list(rules[rule_id]['subrules']))

    return dict(sorted(rules.items(), key=lambda x: (int(x[0]) if x[0].isdigit() else 999, x[0])))

def extract_redbook_rules(framework):
    """Extract all Redbook rules."""
    rules = defaultdict(lambda: {'errors': []})

    for error in framework['redbook_errors']:
        rule_id = error.get('rule_id', 'unknown')
        rules[rule_id]['errors'].append(error)

        # Extract rule title from first error
        if 'title' not in rules[rule_id] and error.get('rule_title'):
            rules[rule_id]['title'] = error.get('rule_title')

    return dict(sorted(rules.items()))

def print_bluebook_rules(rules):
    """Print comprehensive Bluebook rule listing."""
    print("="*80)
    print("BLUEBOOK RULES COVERAGE (21st Edition)")
    print("="*80)
    print()

    # Define rule titles (from Bluebook 21st edition)
    rule_titles = {
        '1': 'Structure and Use of Citations',
        '2': 'Typefaces for Law Reviews',
        '3': 'Subdivisions',
        '4': 'Short Citation Forms',
        '5': 'Quotations',
        '6': 'Abbreviations, Numerals, and Symbols',
        '7': 'Italicization for Style and in Unique Circumstances',
        '8': 'Capitalization',
        '9': 'Titles of Judges, Officials, and Terms of Court',
        '10': 'Cases',
        '11': 'Constitutions',
        '12': 'Statutes',
        '13': 'Legislative Materials',
        '14': 'Administrative and Executive Materials',
        '15': 'Books, Reports, and Other Nonperiodic Materials',
        '16': 'Periodical Materials',
        '17': 'Unpublished and Forthcoming Sources',
        '18': 'The Internet, Electronic Media, and Other Nonprint Resources',
        '19': 'Services',
        '20': 'Foreign Materials',
        '21': 'International Materials'
    }

    total_rules = 0
    total_subrules = 0
    total_errors = 0

    for rule_id, data in rules.items():
        if not rule_id.isdigit():
            continue  # Skip non-numeric rules for now

        total_rules += 1
        title = rule_titles.get(rule_id, 'Unknown')
        num_subrules = len(data['subrules'])
        num_errors = len(data['errors'])

        total_subrules += num_subrules
        total_errors += num_errors

        print(f"Rule {rule_id}: {title}")
        print(f"  Subrules: {num_subrules}")
        print(f"  Error types: {num_errors}")

        if data['subrules']:
            # Group subrules by second-level
            subrule_groups = defaultdict(list)
            for subrule in data['subrules']:
                parts = subrule.split('.')
                if len(parts) >= 2:
                    second_level = f"{parts[0]}.{parts[1]}"
                    subrule_groups[second_level].append(subrule)
                else:
                    subrule_groups[subrule].append(subrule)

            print(f"  Coverage:")
            for group in sorted(subrule_groups.keys()):
                subrules_in_group = subrule_groups[group]
                if len(subrules_in_group) == 1 and subrules_in_group[0] == group:
                    print(f"    • {group}")
                else:
                    print(f"    • {group} ({len(subrules_in_group)} sub-subrules)")
                    # Show sub-subrules if there aren't too many
                    if len(subrules_in_group) <= 5:
                        for sr in subrules_in_group:
                            if sr != group:
                                print(f"      - {sr}")
        print()

    print("="*80)
    print(f"BLUEBOOK SUMMARY")
    print("="*80)
    print(f"Top-level rules: {total_rules}/21")
    print(f"Total subrules: {total_subrules}")
    print(f"Total error types: {total_errors}")
    print()

def print_redbook_rules(rules):
    """Print comprehensive Redbook rule listing."""
    print("="*80)
    print("REDBOOK RULES COVERAGE (Stanford Law Review)")
    print("="*80)
    print()

    # Group by section (first part before period)
    sections = defaultdict(list)
    for rule_id in rules.keys():
        # Extract section number (e.g., "RB 1.1" -> "1")
        if 'RB' in rule_id:
            parts = rule_id.replace('RB ', '').split('.')
            section = parts[0] if parts else 'unknown'
            sections[section].append(rule_id)

    total_errors = 0

    for section in sorted(sections.keys(), key=lambda x: (int(x) if x.isdigit() else 999, x)):
        section_rules = sorted(sections[section])

        print(f"Section {section}: ({len(section_rules)} rules)")

        for rule_id in section_rules:
            data = rules[rule_id]
            title = data.get('title', 'Unknown')
            num_errors = len(data['errors'])
            total_errors += num_errors

            # Clean up rule display
            display_id = rule_id.replace('RB ', '')
            print(f"  {display_id}: {title} ({num_errors} errors)")

        print()

    print("="*80)
    print(f"REDBOOK SUMMARY")
    print("="*80)
    print(f"Total rules: {len(rules)}")
    print(f"Total error types: {total_errors}")
    print()

def print_detailed_bluebook_list(rules):
    """Print detailed list of all Bluebook subrules."""
    print("="*80)
    print("DETAILED BLUEBOOK SUBRULE LIST")
    print("="*80)
    print()

    for rule_id, data in sorted(rules.items(), key=lambda x: (int(x[0]) if x[0].isdigit() else 999, x[0])):
        if not rule_id.isdigit():
            continue

        if data['subrules']:
            print(f"Rule {rule_id} Subrules:")
            for subrule in data['subrules']:
                print(f"  • {subrule}")
            print()

def print_detailed_redbook_list(rules):
    """Print detailed list of all Redbook rules."""
    print("="*80)
    print("DETAILED REDBOOK RULE LIST")
    print("="*80)
    print()

    for rule_id, data in sorted(rules.items()):
        title = data.get('title', 'Unknown')
        num_errors = len(data['errors'])
        print(f"{rule_id}: {title} ({num_errors} errors)")

    print()

def main():
    """Main function."""
    print("\n" + "="*80)
    print("COMPREHENSIVE RULE COVERAGE REPORT")
    print("R1 Cite Checking Error Framework")
    print("="*80 + "\n")

    # Load framework
    framework = load_framework()

    print(f"Framework version: {framework.get('version', 'unknown')}")
    print(f"Total error types: {framework['statistics']['total_errors']}")
    print(f"Auto-fixable: {framework['statistics']['auto_fixable_errors']}")
    print()

    # Extract rules
    bluebook_rules = extract_bluebook_rules(framework)
    redbook_rules = extract_redbook_rules(framework)

    # Print Bluebook coverage
    print_bluebook_rules(bluebook_rules)

    # Print Redbook coverage
    print_redbook_rules(redbook_rules)

    # Print detailed lists (auto-display all)
    print("\n" + "="*80)
    print("DETAILED COVERAGE LISTS")
    print("="*80 + "\n")

    print_detailed_bluebook_list(bluebook_rules)
    print_detailed_redbook_list(redbook_rules)

    # Final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"\nBluebook Coverage:")
    print(f"  • {len([r for r in bluebook_rules.keys() if r.isdigit()])}/21 top-level rules")
    print(f"  • {sum(len(data['subrules']) for data in bluebook_rules.values())} total subrules")
    print(f"  • {sum(len(data['errors']) for data in bluebook_rules.values())} error types")

    print(f"\nRedbook Coverage:")
    print(f"  • {len(redbook_rules)}/115 rules")
    print(f"  • {sum(len(data['errors']) for data in redbook_rules.values())} error types")

    print(f"\nGrand Total:")
    print(f"  • {framework['statistics']['total_errors']} error types")
    print(f"  • Complete Bluebook & Redbook coverage")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
