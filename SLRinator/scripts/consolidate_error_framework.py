#!/usr/bin/env python3
"""
Consolidate all error analysis files into a single master error detection framework.
Combines Bluebook Rules 1-21, Redbook Rules 1-115, and Tables into comprehensive JSON.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

def load_json(file_path: Path) -> Dict:
    """Load and parse JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_bluebook_errors(rules_data: Dict) -> List[Dict]:
    """Extract errors from Bluebook rules files."""
    errors = []

    # Structure 1: Direct error_types array (rules_5-9_ALL_ERRORS.json, etc.)
    if 'error_types' in rules_data:
        for error in rules_data['error_types']:
            errors.append({
                'error_id': error.get('error_id'),
                'rule_id': error.get('source_rule') or error.get('rule_id'),
                'rule_title': error.get('error_name'),
                'description': error.get('description'),
                'regex_detect': error.get('regex_pattern'),
                'regex_validate': None,
                'incorrect_example': error.get('incorrect_example'),
                'correct_example': error.get('correct_example'),
                'severity': error.get('severity', 'medium'),
                'auto_fixable': error.get('auto_fixable'),
                'gpt_prompt': error.get('gpt_prompt'),
                'gpt_system': error.get('gpt_system'),
                'fix_instructions': error.get('fix_instructions'),
                'category': error.get('category'),
                'source': 'Bluebook'
            })

    # Structure 2: subrules with nested error_types (rule_10_ALL_20_SUBRULES.json)
    elif 'subrules' in rules_data:
        for subrule_id, subrule in rules_data['subrules'].items():
            for error in subrule.get('error_types', []):
                errors.append({
                    'error_id': error.get('id') or error.get('error_id'),
                    'rule_id': subrule.get('id') or subrule_id,
                    'rule_title': subrule.get('title'),
                    'description': error.get('description') or error.get('error_type'),
                    'regex_detect': error.get('regex_pattern'),
                    'regex_validate': None,
                    'incorrect_example': error.get('incorrect_example'),
                    'correct_example': error.get('correct_example'),
                    'severity': error.get('severity', 'medium'),
                    'auto_fixable': error.get('auto_fixable'),
                    'gpt_prompt': error.get('gpt_prompt'),
                    'category': error.get('category'),
                    'source': 'Bluebook'
                })

    # Structure 3: error_categories with rule-specific errors (rules_11-13_ALL_ERRORS.json, rules_14-16)
    elif 'error_categories' in rules_data:
        for category_key, category_data in rules_data['error_categories'].items():
            if isinstance(category_data, dict):
                rule_id = category_data.get('rule_id')
                rule_title = category_data.get('rule_title')

                # Handle 'errors' field
                if 'errors' in category_data:
                    for error in category_data['errors']:
                        errors.append({
                            'error_id': error.get('error_id'),
                            'rule_id': str(rule_id) if rule_id else None,
                            'rule_title': rule_title,
                            'description': error.get('description'),
                            'regex_detect': error.get('regex_pattern'),
                            'regex_validate': None,
                            'incorrect_example': error.get('example_incorrect'),
                            'correct_example': error.get('example_correct'),
                            'severity': error.get('severity', 'medium'),
                            'auto_fixable': None,
                            'category': error.get('category'),
                            'error_code': error.get('error_code'),
                            'remediation': error.get('remediation'),
                            'source': 'Bluebook'
                        })

                # Handle 'error_types' field (rules_14-16)
                elif 'error_types' in category_data:
                    for error in category_data['error_types']:
                        errors.append({
                            'error_id': error.get('error_id'),
                            'rule_id': str(rule_id) if rule_id else error.get('subrule'),
                            'rule_title': rule_title or error.get('subrule_title'),
                            'description': error.get('description') or error.get('error_type'),
                            'regex_detect': error.get('regex_pattern'),
                            'regex_validate': None,
                            'incorrect_example': error.get('example_incorrect'),
                            'correct_example': error.get('example_correct'),
                            'severity': error.get('severity', 'medium'),
                            'auto_fixable': error.get('auto_fixable'),
                            'category': error.get('category'),
                            'source': 'Bluebook'
                        })

    # Structure 3b: Rule-specific keys with subrule_errors (rules_17-19)
    # Check for keys like 'rule_17_unpublished_forthcoming_sources'
    else:
        for key, value in rules_data.items():
            if isinstance(value, dict) and key.startswith('rule_'):
                rule_id = value.get('rule_id')
                rule_title = value.get('title')

                # Handle subrule_errors field
                if 'subrule_errors' in value:
                    for error in value['subrule_errors']:
                        errors.append({
                            'error_id': error.get('error_id'),
                            'rule_id': str(rule_id) if rule_id else error.get('subrule'),
                            'rule_title': rule_title,
                            'description': error.get('description') or error.get('error_type'),
                            'regex_detect': error.get('regex_pattern'),
                            'regex_validate': None,
                            'incorrect_example': error.get('incorrect_example'),
                            'correct_example': error.get('correct_example'),
                            'severity': error.get('severity', 'medium'),
                            'auto_fixable': error.get('auto_fixable'),
                            'category': error.get('category'),
                            'source': 'Bluebook'
                        })

    # Structure 4: rules array with nested errors (rules_1-4_ALL_ERRORS.json)
    if 'rules' in rules_data:
        for rule in rules_data['rules']:
            rule_id = rule.get('rule_id') or rule.get('id')

            # Extract errors from various structures
            rule_errors = []
            if 'errors' in rule:
                rule_errors = rule['errors']
            elif 'error_types' in rule:
                rule_errors = rule['error_types']
            elif 'common_errors' in rule:
                rule_errors = rule['common_errors']

            for error in rule_errors:
                errors.append({
                    'error_id': error.get('error_id') or error.get('id'),
                    'rule_id': rule_id,
                    'rule_title': rule.get('title') or rule.get('rule_title'),
                    'description': error.get('description') or error.get('name'),
                    'regex_detect': error.get('regex_detect') or error.get('regex_pattern') or error.get('pattern'),
                    'regex_validate': error.get('regex_validate') or error.get('regex_correct'),
                    'incorrect_example': error.get('incorrect_example'),
                    'correct_example': error.get('correct_example'),
                    'severity': error.get('severity', 'medium'),
                    'auto_fixable': error.get('auto_fixable') or error.get('auto_fix'),
                    'gpt_prompt': error.get('gpt_prompt'),
                    'gpt_system': error.get('gpt_system'),
                    'comment_required': error.get('comment_required'),
                    'fix_pattern': error.get('fix_pattern'),
                    'category': error.get('category'),
                    'source': 'Bluebook'
                })

    return errors

def extract_redbook_errors(redbook_data: Dict) -> List[Dict]:
    """Extract errors from Redbook file."""
    errors = []

    if 'rules' in redbook_data:
        for rule in redbook_data['rules']:
            rule_id = rule.get('id') or rule.get('rule_id')

            # Extract error_types
            error_types = rule.get('error_types', [])

            for error in error_types:
                # Extract patterns
                patterns = rule.get('patterns', {})
                detect_patterns = patterns.get('detect', [])
                validate_patterns = patterns.get('validate', [])

                # Get first regex pattern if available
                regex_detect = None
                if detect_patterns and len(detect_patterns) > 0:
                    regex_detect = detect_patterns[0].get('regex')

                regex_validate = None
                if validate_patterns and len(validate_patterns) > 0:
                    regex_validate = validate_patterns[0].get('regex')

                # Get examples
                examples = rule.get('examples', {})
                incorrect_examples = examples.get('incorrect', [])
                correct_examples = examples.get('correct', [])

                errors.append({
                    'error_id': error.get('id'),
                    'rule_id': f"RB {rule_id}",
                    'rule_title': rule.get('title'),
                    'description': error.get('description') or error.get('name'),
                    'regex_detect': regex_detect,
                    'regex_validate': regex_validate,
                    'incorrect_example': incorrect_examples[0] if incorrect_examples else None,
                    'correct_example': correct_examples[0] if correct_examples else None,
                    'severity': error.get('severity', 'medium'),
                    'auto_fixable': error.get('auto_fix'),
                    'comment_required': error.get('comment_required'),
                    'precedence_level': rule.get('precedence_level'),
                    'bluebook_difference': rule.get('bluebook_difference'),
                    'source': 'Redbook'
                })

    return errors

def extract_table_entries(tables_data: Dict) -> List[Dict]:
    """Extract table entries as reference data."""
    # Tables have complex nested structures - we'll just count them for now
    # The actual table data is preserved in the original analysis files
    entries = []

    if 'tables' in tables_data and isinstance(tables_data['tables'], dict):
        # Count entries across all table structures
        for table_id, table_data in tables_data['tables'].items():
            if isinstance(table_data, dict):
                entries.append({
                    'table_id': table_id,
                    'table_name': table_data.get('name', table_id),
                    'description': table_data.get('description', ''),
                    'source': 'Bluebook Tables'
                })

    return entries

def consolidate_all_errors():
    """Main consolidation function."""

    base_path = Path('/home/user/slr/SLRinator/output/analysis')

    # Define file groups
    bluebook_files = [
        'rules_1-4_ALL_ERRORS.json',
        'rules_5-9_ALL_ERRORS.json',
        'rule_10_ALL_20_SUBRULES.json',
        'rules_11-13_ALL_ERRORS.json',
        'rules_14-16_ALL_ERRORS.json',
        'rules_17-19_ALL_ERRORS.json',
        'rules_20-21_ALL_ERRORS.json'
    ]

    redbook_file = 'redbook_ALL_115_RULES_FIXED.json'

    table_files = [
        'tables_1-5_analysis.json',
        'tables_6-8_analysis.json',
        'tables_9-16_analysis.json'
    ]

    # Consolidate Bluebook errors
    all_bluebook_errors = []
    for filename in bluebook_files:
        file_path = base_path / filename
        if file_path.exists():
            print(f"Processing {filename}...")
            data = load_json(file_path)
            errors = extract_bluebook_errors(data)
            all_bluebook_errors.extend(errors)
            print(f"  Extracted {len(errors)} errors")

    # Consolidate Redbook errors
    print(f"\nProcessing {redbook_file}...")
    redbook_path = base_path / redbook_file
    redbook_data = load_json(redbook_path)
    all_redbook_errors = extract_redbook_errors(redbook_data)
    print(f"  Extracted {len(all_redbook_errors)} errors")

    # Consolidate table entries
    all_table_entries = []
    for filename in table_files:
        file_path = base_path / filename
        if file_path.exists():
            print(f"\nProcessing {filename}...")
            data = load_json(file_path)
            entries = extract_table_entries(data)
            all_table_entries.extend(entries)
            print(f"  Extracted {len(entries)} entries")

    # Create master framework
    master_framework = {
        'schema_version': '3.0.0',
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'description': 'Consolidated error detection framework for Stanford Law Review R1 cite checking',
        'coverage': {
            'bluebook_rules': '1-21 (all 21 top-level rules)',
            'bluebook_subrules': 216,
            'redbook_rules': '1-115 (all 115 rules)',
            'table_entries': len(all_table_entries),
            'total_error_types': len(all_bluebook_errors) + len(all_redbook_errors)
        },
        'statistics': {
            'bluebook_errors': len(all_bluebook_errors),
            'redbook_errors': len(all_redbook_errors),
            'table_entries': len(all_table_entries),
            'total_errors': len(all_bluebook_errors) + len(all_redbook_errors),
            'errors_with_regex': sum(1 for e in all_bluebook_errors + all_redbook_errors if e.get('regex_detect')),
            'auto_fixable_errors': sum(1 for e in all_bluebook_errors + all_redbook_errors if e.get('auto_fixable') in [True, 'yes', 'manual'])
        },
        'bluebook_errors': all_bluebook_errors,
        'redbook_errors': all_redbook_errors,
        'table_entries': all_table_entries,
        'critical_fixes_applied': [
            {
                'rule': 'RB 1.12',
                'issue': 'Rule incorrectly stated see generally FORBIDS parentheticals',
                'fix': 'Corrected to REQUIRE parentheticals for see generally citations',
                'date': '2025-11-23'
            }
        ],
        'usage_notes': {
            'precedence': 'Redbook rules take precedence over Bluebook when both apply',
            'validation_order': [
                '1. Check Redbook rules first (all_redbook_errors)',
                '2. Check Bluebook rules (all_bluebook_errors)',
                '3. Reference table entries for abbreviations and formatting',
                '4. Use regex_detect for fast pattern matching',
                '5. Use gpt_prompt for semantic validation when regex insufficient'
            ],
            'integration': 'This framework is designed for SLRinator/src/r1_validation/citation_validator.py'
        }
    }

    # Write master framework
    output_path = Path('/home/user/slr/SLRinator/config/error_detection_framework_MASTER.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(master_framework, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"MASTER ERROR DETECTION FRAMEWORK CREATED")
    print(f"{'='*80}")
    print(f"Output: {output_path}")
    print(f"\nStatistics:")
    print(f"  Bluebook Errors: {len(all_bluebook_errors)}")
    print(f"  Redbook Errors: {len(all_redbook_errors)}")
    print(f"  Table Entries: {len(all_table_entries)}")
    print(f"  TOTAL ERRORS: {len(all_bluebook_errors) + len(all_redbook_errors)}")
    print(f"  Errors with Regex: {master_framework['statistics']['errors_with_regex']}")
    print(f"  Auto-fixable: {master_framework['statistics']['auto_fixable_errors']}")
    print(f"\nFile size: {output_path.stat().st_size / 1024:.1f} KB")
    print(f"{'='*80}\n")

    return master_framework

if __name__ == '__main__':
    consolidate_all_errors()
