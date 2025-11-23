#!/usr/bin/env python3
"""
Compile MASTER Error Detection Framework
Reads ALL analysis files and creates comprehensive error framework with ALL 537+ errors
"""

import json
import re
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

def load_json_file(filepath: str) -> Dict:
    """Load JSON file safely"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return {}

def extract_errors_from_rules_5_9(data: Dict) -> List[Dict]:
    """Extract all errors from rules 5-9 analysis"""
    errors = []
    error_counter = 1

    for rule in data.get('rules', []):
        rule_id = rule.get('rule_id', '')
        rule_title = rule.get('rule_title', '')

        for subrule in rule.get('subrules', []):
            subrule_id = subrule.get('rule_id', '')
            subrule_title = subrule.get('rule_title', '')

            for error in subrule.get('common_errors', []):
                error_obj = {
                    "error_id": f"BB_{rule_id}_{error.get('error_id', f'ERR{error_counter:03d}')}",
                    "error_name": error.get('error_type', 'Unknown Error'),
                    "source_rule": f"BB {subrule_id}",
                    "rule_title": f"{rule_title} - {subrule_title}",
                    "category": "formatting" if "format" in error.get('error_type', '').lower() else "content",
                    "description": error.get('description', ''),
                    "regex_detect": error.get('regex_pattern', ''),
                    "regex_validate": "",
                    "severity": error.get('severity', 'major'),
                    "citation_types": ["general"],
                    "auto_fixable": error.get('auto_fixable', False),
                    "fix_pattern": error.get('fix_instructions', ''),
                    "gpt_validation_prompt": "",
                    "examples": {
                        "incorrect": error.get('incorrect_example', ''),
                        "correct": error.get('correct_example', '')
                    },
                    "requires_gpt": error.get('requires_gpt', False)
                }
                errors.append(error_obj)
                error_counter += 1

            # Add GPT prompts as additional validation
            for prompt in subrule.get('gpt_prompts', []):
                error_obj = {
                    "error_id": f"BB_{rule_id}_GPT_{prompt.get('prompt_id', f'P{error_counter:03d}')}",
                    "error_name": prompt.get('prompt_id', 'GPT Validation'),
                    "source_rule": f"BB {subrule_id}",
                    "rule_title": f"{rule_title} - {subrule_title}",
                    "category": "validation",
                    "description": prompt.get('use_case', ''),
                    "regex_detect": "",
                    "regex_validate": "",
                    "severity": "major",
                    "citation_types": ["general"],
                    "auto_fixable": False,
                    "fix_pattern": "",
                    "gpt_validation_prompt": prompt.get('prompt', ''),
                    "examples": {"incorrect": "", "correct": ""},
                    "requires_gpt": True
                }
                errors.append(error_obj)
                error_counter += 1

    return errors

def extract_errors_from_markdown(filepath: str, rule_prefix: str) -> List[Dict]:
    """Extract errors from markdown analysis files"""
    errors = []
    error_counter = 1

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract error types using regex
        error_pattern = r'(?:#### Error Type \d+:|##### Error Type \d+:)\s*([^\n]+)\s*```\s*INCORRECT:\s*([^\n]+)\s*CORRECT:\s*([^\n]+)\s*```\s*(?:\*\*Regex Pattern:\*\*\s*```regex\s*([^`]+)\s*```)?(?:\s*\*\*GPT Prompt:\*\*\s*```\s*([^`]+)\s*```)?'

        matches = re.finditer(error_pattern, content, re.MULTILINE | re.DOTALL)

        for match in matches:
            error_name = match.group(1).strip()
            incorrect = match.group(2).strip()
            correct = match.group(3).strip()
            regex = match.group(4).strip() if match.group(4) else ""
            gpt_prompt = match.group(5).strip() if match.group(5) else ""

            error_obj = {
                "error_id": f"{rule_prefix}_ERR{error_counter:03d}",
                "error_name": error_name,
                "source_rule": rule_prefix,
                "rule_title": os.path.basename(filepath).replace('.md', ''),
                "category": "citation_structure",
                "description": error_name,
                "regex_detect": regex,
                "regex_validate": "",
                "severity": "major",
                "citation_types": ["cases"],
                "auto_fixable": bool(regex and not gpt_prompt),
                "fix_pattern": "",
                "gpt_validation_prompt": gpt_prompt,
                "examples": {
                    "incorrect": incorrect,
                    "correct": correct
                },
                "requires_gpt": bool(gpt_prompt)
            }
            errors.append(error_obj)
            error_counter += 1

    except Exception as e:
        print(f"Error processing markdown file {filepath}: {e}")

    return errors

def extract_errors_from_tables(data: Dict, table_range: str) -> List[Dict]:
    """Extract errors from table analysis files"""
    errors = []
    error_counter = 1

    # Extract from metadata
    tables = data.get('tables', {})

    for table_id, table_data in tables.items():
        if isinstance(table_data, dict):
            # Process subsections
            for subsection_name, subsection_data in table_data.get('subsections', {}).items():
                if isinstance(subsection_data, dict):
                    # Extract common errors
                    common_errors = subsection_data.get('common_errors', [])
                    for error in common_errors:
                        if isinstance(error, str):
                            error_obj = {
                                "error_id": f"T{table_id}_ERR{error_counter:03d}",
                                "error_name": error,
                                "source_rule": f"Table {table_id}",
                                "rule_title": table_data.get('name', ''),
                                "category": "abbreviation",
                                "description": error,
                                "regex_detect": "",
                                "regex_validate": "",
                                "severity": "major",
                                "citation_types": ["general"],
                                "auto_fixable": False,
                                "fix_pattern": "",
                                "gpt_validation_prompt": "",
                                "examples": {"incorrect": "", "correct": ""},
                                "requires_gpt": True
                            }
                            errors.append(error_obj)
                            error_counter += 1

                    # Extract GPT prompts
                    gpt_prompts = subsection_data.get('gpt_prompts', {})
                    for prompt_name, prompt_text in gpt_prompts.items():
                        if isinstance(prompt_text, str):
                            error_obj = {
                                "error_id": f"T{table_id}_GPT{error_counter:03d}",
                                "error_name": prompt_name,
                                "source_rule": f"Table {table_id}",
                                "rule_title": table_data.get('name', ''),
                                "category": "validation",
                                "description": prompt_name,
                                "regex_detect": "",
                                "regex_validate": "",
                                "severity": "major",
                                "citation_types": ["general"],
                                "auto_fixable": False,
                                "fix_pattern": "",
                                "gpt_validation_prompt": prompt_text,
                                "examples": {"incorrect": "", "correct": ""},
                                "requires_gpt": True
                            }
                            errors.append(error_obj)
                            error_counter += 1

    return errors

def add_redbook_rb_1_12_fix() -> List[Dict]:
    """Add critical fix for RB 1.12 parenthetical requirements"""
    return [
        {
            "error_id": "RB_1_12_CF_MISSING_PAREN",
            "error_name": "'Cf.' signal missing required explanatory parenthetical",
            "source_rule": "RB 1.12",
            "rule_title": "Redbook Rule 1.12 - Signal Parenthetical Requirements",
            "category": "signal_parenthetical",
            "description": "Redbook Rule 1.12 REQUIRES explanatory parentheticals for 'Cf.' and 'But cf.' signals. The parenthetical must explain the analogy.",
            "regex_detect": "\\bCf\\.\s+[^(]+\\([12]\\d{3}\\)\\.(?!\\s*\\()",
            "regex_validate": "\\bCf\\.\s+[^(]+\\([12]\\d{3}\\)\\s*\\([^)]+\\)",
            "severity": "critical",
            "citation_types": ["all"],
            "auto_fixable": False,
            "fix_pattern": "Add explanatory parenthetical after year: (explaining how source supports by analogy)",
            "gpt_validation_prompt": "Check if 'Cf.' or 'But cf.' signal has an explanatory parenthetical. According to Redbook 1.12, these signals REQUIRE parentheticals explaining the analogy. Return: COMPLIANT or NON_COMPLIANT with suggested parenthetical.",
            "examples": {
                "incorrect": "Cf. Smith v. Jones, 123 U.S. 456 (2000).",
                "correct": "Cf. Smith v. Jones, 123 U.S. 456 (2000) (applying similar standard in contract context)."
            },
            "requires_gpt": True
        },
        {
            "error_id": "RB_1_12_SEE_GENERALLY_WITH_PAREN",
            "error_name": "'See generally' signal incorrectly includes explanatory parenthetical",
            "source_rule": "RB 1.12",
            "rule_title": "Redbook Rule 1.12 - Signal Parenthetical Requirements",
            "category": "signal_parenthetical",
            "description": "Redbook Rule 1.12 states that 'See generally' signals must NOT include explanatory parentheticals. The signal itself indicates background material.",
            "regex_detect": "\\bSee generally\\s+[^(]+\\([12]\\d{3}\\)\\s*\\([^)]+\\)",
            "regex_validate": "\\bSee generally\\s+[^(]+\\([12]\\d{3}\\)\\.?$",
            "severity": "major",
            "citation_types": ["all"],
            "auto_fixable": True,
            "fix_pattern": "Remove explanatory parenthetical after 'See generally' citations",
            "gpt_validation_prompt": "Check if 'See generally' signal has an explanatory parenthetical. According to Redbook 1.12, 'See generally' signals must NOT have explanatory parentheticals. Return: COMPLIANT or NON_COMPLIANT.",
            "examples": {
                "incorrect": "See generally Smith v. Jones, 123 U.S. 456 (2000) (providing background on the issue).",
                "correct": "See generally Smith v. Jones, 123 U.S. 456 (2000)."
            },
            "requires_gpt": False
        },
        {
            "error_id": "RB_1_12_BUT_CF_MISSING_PAREN",
            "error_name": "'But cf.' signal missing required explanatory parenthetical",
            "source_rule": "RB 1.12",
            "rule_title": "Redbook Rule 1.12 - Signal Parenthetical Requirements",
            "category": "signal_parenthetical",
            "description": "Redbook Rule 1.12 REQUIRES explanatory parentheticals for 'But cf.' signals (contradicts by analogy).",
            "regex_detect": "\\bBut cf\\.\s+[^(]+\\([12]\\d{3}\\)\\.(?!\\s*\\()",
            "regex_validate": "\\bBut cf\\.\s+[^(]+\\([12]\\d{3}\\)\\s*\\([^)]+\\)",
            "severity": "critical",
            "citation_types": ["all"],
            "auto_fixable": False,
            "fix_pattern": "Add explanatory parenthetical explaining how source contradicts by analogy",
            "gpt_validation_prompt": "Check if 'But cf.' signal has an explanatory parenthetical. According to Redbook 1.12, this signal REQUIRES a parenthetical. Return: COMPLIANT or NON_COMPLIANT with suggested parenthetical.",
            "examples": {
                "incorrect": "But cf. Smith v. Jones, 123 U.S. 456 (2000).",
                "correct": "But cf. Smith v. Jones, 123 U.S. 456 (2000) (reaching opposite conclusion in analogous situation)."
            },
            "requires_gpt": True
        }
    ]

def compile_master_framework():
    """Compile complete error detection framework from all sources"""

    print("Starting master framework compilation...")
    print("=" * 80)

    analysis_dir = Path("/home/user/slr/SLRinator/output/analysis")
    all_errors = []

    # 1. Load Rules 5-9 (JSON)
    print("\n1. Loading Rules 5-9...")
    rules_5_9 = load_json_file(analysis_dir / "rules_5-9_analysis.json")
    errors_5_9 = extract_errors_from_rules_5_9(rules_5_9)
    all_errors.extend(errors_5_9)
    print(f"   Found {len(errors_5_9)} errors from Rules 5-9")

    # 2. Load Rules 1-4 (Markdown)
    print("\n2. Loading Rules 1-4...")
    errors_1_4 = extract_errors_from_markdown(
        analysis_dir / "rules_1-4_analysis.md",
        "BB_1-4"
    )
    all_errors.extend(errors_1_4)
    print(f"   Found {len(errors_1_4)} errors from Rules 1-4")

    # 3. Load Rule 10 Cases Core (Markdown)
    print("\n3. Loading Rule 10 Cases Core...")
    errors_10_core = extract_errors_from_markdown(
        analysis_dir / "rule_10_cases_core.md",
        "BB_10_CORE"
    )
    all_errors.extend(errors_10_core)
    print(f"   Found {len(errors_10_core)} errors from Rule 10 Core")

    # 4. Load Rule 10 Advanced (Markdown)
    print("\n4. Loading Rule 10 Advanced...")
    errors_10_adv = extract_errors_from_markdown(
        analysis_dir / "rule_10_cases_advanced.md",
        "BB_10_ADV"
    )
    all_errors.extend(errors_10_adv)
    print(f"   Found {len(errors_10_adv)} errors from Rule 10 Advanced")

    # 5. Load Rules 12-13 (Markdown)
    print("\n5. Loading Rules 12-13...")
    errors_12_13 = extract_errors_from_markdown(
        analysis_dir / "rules_12-13_analysis.md",
        "BB_12-13"
    )
    all_errors.extend(errors_12_13)
    print(f"   Found {len(errors_12_13)} errors from Rules 12-13")

    # 6. Load Rules 14-16 (Markdown)
    print("\n6. Loading Rules 14-16...")
    errors_14_16 = extract_errors_from_markdown(
        analysis_dir / "rules_14-16_analysis.md",
        "BB_14-16"
    )
    all_errors.extend(errors_14_16)
    print(f"   Found {len(errors_14_16)} errors from Rules 14-16")

    # 7. Load Tables 1-5 (JSON)
    print("\n7. Loading Tables 1-5...")
    tables_1_5 = load_json_file(analysis_dir / "tables_1-5_analysis.json")
    errors_t1_5 = extract_errors_from_tables(tables_1_5, "1-5")
    all_errors.extend(errors_t1_5)
    print(f"   Found {len(errors_t1_5)} errors from Tables 1-5")

    # 8. Load Tables 6-8 (JSON)
    print("\n8. Loading Tables 6-8...")
    tables_6_8 = load_json_file(analysis_dir / "tables_6-8_analysis.json")
    errors_t6_8 = extract_errors_from_tables(tables_6_8, "6-8")
    all_errors.extend(errors_t6_8)
    print(f"   Found {len(errors_t6_8)} errors from Tables 6-8")

    # 9. Load Tables 9-16 (JSON)
    print("\n9. Loading Tables 9-16...")
    tables_9_16 = load_json_file(analysis_dir / "tables_9-16_analysis.json")
    errors_t9_16 = extract_errors_from_tables(tables_9_16, "9-16")
    all_errors.extend(errors_t9_16)
    print(f"   Found {len(errors_t9_16)} errors from Tables 9-16")

    # 10. Add Redbook RB 1.12 Critical Fix
    print("\n10. Adding Redbook RB 1.12 Critical Fixes...")
    rb_fixes = add_redbook_rb_1_12_fix()
    all_errors.extend(rb_fixes)
    print(f"   Added {len(rb_fixes)} Redbook 1.12 fixes")

    # Compile final framework
    print("\n" + "=" * 80)
    print(f"TOTAL ERRORS COMPILED: {len(all_errors)}")
    print("=" * 80)

    framework = {
        "metadata": {
            "version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "description": "Complete Master Error Detection Framework - ALL 537+ citation errors from Bluebook and Redbook",
            "source_files": [
                "rules_1-4_analysis.md",
                "rules_5-9_analysis.json",
                "rule_10_cases_core.md",
                "rule_10_cases_advanced.md",
                "rules_12-13_analysis.md",
                "rules_14-16_analysis.md",
                "tables_1-5_analysis.json",
                "tables_6-8_analysis.json",
                "tables_9-16_analysis.json"
            ],
            "total_error_types": len(all_errors),
            "includes_redbook_fixes": True,
            "critical_fixes": [
                "RB 1.12: Cf. and But cf. REQUIRE parentheticals",
                "RB 1.12: See generally must NOT have parentheticals"
            ]
        },
        "error_categories": {
            "signal_parenthetical": "Errors related to signal and parenthetical usage",
            "formatting": "Citation formatting errors",
            "content": "Citation content errors",
            "abbreviation": "Abbreviation and style errors",
            "validation": "GPT-based validation checks",
            "citation_structure": "Overall citation structure errors"
        },
        "severity_levels": {
            "critical": "Changes meaning or violates mandatory rules - immediate fix required",
            "major": "Clear Bluebook/Redbook violation - should be fixed",
            "minor": "Style issue or optional improvement"
        },
        "errors": all_errors
    }

    # Write to output file
    output_path = Path("/home/user/slr/SLRinator/config/error_detection_framework_COMPLETE.json")
    print(f"\nWriting complete framework to: {output_path}")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(framework, f, indent=2, ensure_ascii=False)

    file_size = output_path.stat().st_size
    print(f"Framework file size: {file_size:,} bytes ({file_size/1024:.1f} KB)")

    # Generate statistics
    print("\n" + "=" * 80)
    print("STATISTICS:")
    print("=" * 80)

    # Count by category
    categories = {}
    for error in all_errors:
        cat = error.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1

    print("\nErrors by Category:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat:30s}: {count:4d}")

    # Count by severity
    severities = {}
    for error in all_errors:
        sev = error.get('severity', 'unknown')
        severities[sev] = severities.get(sev, 0) + 1

    print("\nErrors by Severity:")
    for sev, count in sorted(severities.items(), key=lambda x: x[1], reverse=True):
        print(f"  {sev:30s}: {count:4d}")

    # Count auto-fixable
    auto_fixable = sum(1 for e in all_errors if e.get('auto_fixable', False))
    requires_gpt = sum(1 for e in all_errors if e.get('requires_gpt', False))

    print("\nFixability:")
    print(f"  Auto-fixable:                   {auto_fixable:4d} ({auto_fixable/len(all_errors)*100:.1f}%)")
    print(f"  Requires GPT validation:        {requires_gpt:4d} ({requires_gpt/len(all_errors)*100:.1f}%)")
    print(f"  Manual review needed:           {len(all_errors) - auto_fixable:4d} ({(len(all_errors)-auto_fixable)/len(all_errors)*100:.1f}%)")

    print("\n" + "=" * 80)
    print("COMPLETE! Master framework generated successfully.")
    print("=" * 80)

    return framework

if __name__ == "__main__":
    compile_master_framework()
