#!/usr/bin/env python3
"""
Compile MASTER Error Detection Framework V2
Enhanced extraction to capture ALL 537+ errors from all analysis files
"""

import json
import re
import os
from pathlib import Path
from typing import Dict, List, Any, Set
from datetime import datetime

class ErrorExtractor:
    def __init__(self):
        self.all_errors = []
        self.error_ids_seen = set()
        self.error_counter = 1

    def add_error(self, error: Dict):
        """Add error with unique ID"""
        error_id = error.get('error_id', f'AUTO_{self.error_counter:04d}')
        if error_id not in self.error_ids_seen:
            self.all_errors.append(error)
            self.error_ids_seen.add(error_id)
            self.error_counter += 1

    def extract_from_rules_5_9_json(self, filepath: Path):
        """Extract from rules 5-9 JSON - comprehensive"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for rule in data.get('rules', []):
                rule_id = rule.get('rule_id', '')
                rule_title = rule.get('rule_title', '')

                for subrule in rule.get('subrules', []):
                    subrule_id = subrule.get('rule_id', '')
                    subrule_title = subrule.get('rule_title', '')

                    # Extract common errors
                    for error in subrule.get('common_errors', []):
                        self.add_error({
                            "error_id": f"BB_{subrule_id}_{error.get('error_id', f'E{self.error_counter:03d}')}",
                            "error_name": error.get('error_type', 'Unknown'),
                            "source_rule": f"BB {subrule_id}",
                            "rule_title": f"{rule_title} - {subrule_title}",
                            "category": self._categorize_error(error.get('error_type', '')),
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
                        })

                    # Extract GPT prompts
                    for prompt in subrule.get('gpt_prompts', []):
                        self.add_error({
                            "error_id": f"BB_{subrule_id}_GPT_{prompt.get('prompt_id', f'P{self.error_counter:03d}')}",
                            "error_name": prompt.get('prompt_id', 'GPT Validation'),
                            "source_rule": f"BB {subrule_id}",
                            "rule_title": f"{rule_title} - {subrule_title}",
                            "category": "gpt_validation",
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
                        })

        except Exception as e:
            print(f"Error in rules 5-9: {e}")

    def extract_from_markdown_comprehensive(self, filepath: Path, rule_prefix: str):
        """Comprehensive markdown extraction with multiple patterns"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Pattern 1: Error Type with code blocks
            pattern1 = r'(?:####|#####)\s*Error Type \d+:\s*([^\n]+)\s*```\s*INCORRECT:\s*([^\n]+)\s*CORRECT:\s*([^\n]+)\s*```'
            for match in re.finditer(pattern1, content, re.MULTILINE):
                self.add_error({
                    "error_id": f"{rule_prefix}_E{self.error_counter:03d}",
                    "error_name": match.group(1).strip(),
                    "source_rule": rule_prefix,
                    "rule_title": filepath.stem,
                    "category": "citation_format",
                    "description": match.group(1).strip(),
                    "regex_detect": "",
                    "regex_validate": "",
                    "severity": "major",
                    "citation_types": ["general"],
                    "auto_fixable": False,
                    "fix_pattern": "",
                    "gpt_validation_prompt": "",
                    "examples": {
                        "incorrect": match.group(2).strip(),
                        "correct": match.group(3).strip()
                    },
                    "requires_gpt": True
                })

            # Pattern 2: Regex Pattern blocks
            regex_pattern = r'\*\*Regex Pattern:\*\*\s*```regex\s*([^`]+)\s*```'
            regex_matches = list(re.finditer(regex_pattern, content, re.MULTILINE))

            # Pattern 3: GPT Prompt blocks
            gpt_pattern = r'\*\*GPT Prompt:\*\*\s*```\s*([^`]+)\s*```'
            gpt_matches = list(re.finditer(gpt_pattern, content, re.MULTILINE))

            for gpt_match in gpt_matches:
                self.add_error({
                    "error_id": f"{rule_prefix}_GPT{self.error_counter:03d}",
                    "error_name": "GPT Validation Check",
                    "source_rule": rule_prefix,
                    "rule_title": filepath.stem,
                    "category": "gpt_validation",
                    "description": "GPT-based validation",
                    "regex_detect": "",
                    "regex_validate": "",
                    "severity": "major",
                    "citation_types": ["general"],
                    "auto_fixable": False,
                    "fix_pattern": "",
                    "gpt_validation_prompt": gpt_match.group(1).strip(),
                    "examples": {"incorrect": "", "correct": ""},
                    "requires_gpt": True
                })

            # Pattern 4: Detection Pattern sections
            detection_pattern = r'(?:####|#####)\s*Detection Pattern[s]?.*?```regex\s*([^`]+)\s*```'
            for match in re.finditer(detection_pattern, content, re.DOTALL):
                self.add_error({
                    "error_id": f"{rule_prefix}_DETECT{self.error_counter:03d}",
                    "error_name": "Pattern Detection",
                    "source_rule": rule_prefix,
                    "rule_title": filepath.stem,
                    "category": "pattern_matching",
                    "description": "Regex pattern for detection",
                    "regex_detect": match.group(1).strip(),
                    "regex_validate": "",
                    "severity": "minor",
                    "citation_types": ["general"],
                    "auto_fixable": True,
                    "fix_pattern": "",
                    "gpt_validation_prompt": "",
                    "examples": {"incorrect": "", "correct": ""},
                    "requires_gpt": False
                })

            # Pattern 5: Common Errors sections
            common_errors_pattern = r'(?:###|####)\s*Common Errors.*?(?=(?:###|####|$))'
            for section in re.finditer(common_errors_pattern, content, re.DOTALL):
                section_text = section.group(0)
                # Extract individual errors
                error_items = re.findall(r'\*\*(?:Incorrect|ERROR):\*\*\s*`([^`]+)`.*?\*\*(?:Correct|RIGHT):\*\*\s*`([^`]+)`', section_text, re.DOTALL)
                for incorrect, correct in error_items:
                    self.add_error({
                        "error_id": f"{rule_prefix}_COMMON{self.error_counter:03d}",
                        "error_name": "Common Error",
                        "source_rule": rule_prefix,
                        "rule_title": filepath.stem,
                        "category": "common_mistake",
                        "description": "Common citation error",
                        "regex_detect": "",
                        "regex_validate": "",
                        "severity": "major",
                        "citation_types": ["general"],
                        "auto_fixable": False,
                        "fix_pattern": "",
                        "gpt_validation_prompt": "",
                        "examples": {
                            "incorrect": incorrect.strip(),
                            "correct": correct.strip()
                        },
                        "requires_gpt": True
                    })

        except Exception as e:
            print(f"Error processing markdown {filepath}: {e}")

    def extract_from_tables_comprehensive(self, filepath: Path, table_range: str):
        """Comprehensive table extraction"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            tables = data.get('tables', {})

            def process_dict_recursively(obj, table_id, path=""):
                """Recursively process nested dictionaries"""
                if isinstance(obj, dict):
                    # Check for common_errors
                    if 'common_errors' in obj:
                        for error in obj['common_errors']:
                            if isinstance(error, str):
                                self.add_error({
                                    "error_id": f"T{table_id}_{path}_E{self.error_counter:03d}",
                                    "error_name": error,
                                    "source_rule": f"Table {table_id}",
                                    "rule_title": f"Table {table_id} - {path}",
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
                                })

                    # Check for gpt_prompts
                    if 'gpt_prompts' in obj:
                        prompts = obj['gpt_prompts']
                        if isinstance(prompts, dict):
                            for prompt_name, prompt_text in prompts.items():
                                if isinstance(prompt_text, str):
                                    self.add_error({
                                        "error_id": f"T{table_id}_{path}_GPT{self.error_counter:03d}",
                                        "error_name": prompt_name,
                                        "source_rule": f"Table {table_id}",
                                        "rule_title": f"Table {table_id} - {path}",
                                        "category": "gpt_validation",
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
                                    })

                    # Check for regex_patterns
                    if 'regex_patterns' in obj:
                        patterns = obj['regex_patterns']
                        if isinstance(patterns, dict):
                            for pattern_name, pattern_value in patterns.items():
                                if isinstance(pattern_value, str):
                                    self.add_error({
                                        "error_id": f"T{table_id}_{path}_REGEX{self.error_counter:03d}",
                                        "error_name": f"Regex: {pattern_name}",
                                        "source_rule": f"Table {table_id}",
                                        "rule_title": f"Table {table_id} - {path}",
                                        "category": "pattern_matching",
                                        "description": pattern_name,
                                        "regex_detect": pattern_value,
                                        "regex_validate": "",
                                        "severity": "minor",
                                        "citation_types": ["general"],
                                        "auto_fixable": True,
                                        "fix_pattern": "",
                                        "gpt_validation_prompt": "",
                                        "examples": {"incorrect": "", "correct": ""},
                                        "requires_gpt": False
                                    })

                    # Recurse into nested dicts
                    for key, value in obj.items():
                        new_path = f"{path}_{key}" if path else key
                        process_dict_recursively(value, table_id, new_path)

                elif isinstance(obj, list):
                    for item in obj:
                        process_dict_recursively(item, table_id, path)

            # Process each table
            for table_id, table_data in tables.items():
                process_dict_recursively(table_data, table_id)

        except Exception as e:
            print(f"Error processing table {filepath}: {e}")

    def _categorize_error(self, error_type: str) -> str:
        """Categorize error based on type"""
        error_lower = error_type.lower()
        if 'format' in error_lower or 'spacing' in error_lower:
            return 'formatting'
        elif 'abbreviation' in error_lower or 'abbrev' in error_lower:
            return 'abbreviation'
        elif 'signal' in error_lower or 'parenthetical' in error_lower:
            return 'signal_parenthetical'
        elif 'quote' in error_lower or 'quotation' in error_lower:
            return 'quotation'
        elif 'capitaliz' in error_lower:
            return 'capitalization'
        elif 'italic' in error_lower:
            return 'italicization'
        elif 'number' in error_lower or 'numeral' in error_lower:
            return 'numerals'
        else:
            return 'content'

def add_comprehensive_bluebook_errors():
    """Add comprehensive Bluebook rule errors manually"""
    errors = []

    # Bluebook Rules 1-4: Citation Structure, Signals, Short Forms
    bb_1_4_errors = [
        {
            "error_id": "BB_1_1_MISSING_PERIOD",
            "error_name": "Citation sentence missing final period",
            "source_rule": "BB 1.1",
            "rule_title": "Citation Sentences and Clauses",
            "category": "punctuation",
            "description": "Citation sentences must end with a period",
            "regex_detect": "^[A-Z][^.]*\\d{1,4}\\s+[A-Z][^.]*\\d+[^.]*\\([12]\\d{3}\\)[^.]*$",
            "severity": "critical",
            "auto_fixable": True,
            "examples": {
                "incorrect": "See Smith v. Jones, 123 U.S. 456 (2000)",
                "correct": "See Smith v. Jones, 123 U.S. 456 (2000)."
            }
        },
        {
            "error_id": "BB_1_2_CF_NO_PAREN",
            "error_name": "Cf. signal without required parenthetical",
            "source_rule": "BB 1.2",
            "rule_title": "Introductory Signals",
            "category": "signal_parenthetical",
            "description": "Cf. signals must include explanatory parenthetical",
            "regex_detect": "\\bCf\\.\s+[^(]+\\([12]\\d{3}\\)\\.(?!\\s*\\()",
            "severity": "critical",
            "auto_fixable": False,
            "requires_gpt": True,
            "examples": {
                "incorrect": "Cf. Smith v. Jones, 123 U.S. 456 (2000).",
                "correct": "Cf. Smith v. Jones, 123 U.S. 456 (2000) (holding similar standard)."
            }
        },
        {
            "error_id": "BB_1_3_SIGNAL_ORDER",
            "error_name": "Signals out of correct order",
            "source_rule": "BB 1.3",
            "rule_title": "Order of Signals",
            "category": "signal_order",
            "description": "Signals must appear in specific Bluebook order",
            "regex_detect": "(See also|Cf\\.)([^;]+);[\\s]*(See)(?!\\s+also|generally)",
            "severity": "major",
            "auto_fixable": False,
            "requires_gpt": True,
            "examples": {
                "incorrect": "See also Smith, 100 U.S. 1 (1990); see Jones, 200 U.S. 2 (2000).",
                "correct": "See Jones, 200 U.S. 2 (2000); see also Smith, 100 U.S. 1 (1990)."
            }
        },
        {
            "error_id": "BB_4_1_ID_NO_PERIOD",
            "error_name": "Id. without period",
            "source_rule": "BB 4.1",
            "rule_title": "Id.",
            "category": "short_form",
            "description": "Id. must always have a period",
            "regex_detect": "\\bId\\s+at\\s+\\d+",
            "severity": "critical",
            "auto_fixable": True,
            "examples": {
                "incorrect": "Id at 123",
                "correct": "Id. at 123"
            }
        },
        {
            "error_id": "RB_4_2_ID_NO_AT",
            "error_name": "Id. without 'at' for pinpoint (Redbook)",
            "source_rule": "RB 4.2",
            "rule_title": "Id. with Pinpoint",
            "category": "short_form",
            "description": "Redbook requires 'at' after Id. when citing different page",
            "regex_detect": "Id\\.\\s+\\d+(?!\\s*n\\.)",
            "severity": "major",
            "auto_fixable": True,
            "examples": {
                "incorrect": "Id. 123",
                "correct": "Id. at 123"
            }
        },
        {
            "error_id": "BB_4_2_SUPRA_FOR_CASES",
            "error_name": "Supra used for case citations",
            "source_rule": "BB 4.2",
            "rule_title": "Supra and Hereinafter",
            "category": "short_form",
            "description": "Do not use supra for cases; use short case name",
            "regex_detect": "[A-Z][a-z]+\\s+v\\.\\s+[A-Z][a-z]+,\\s+supra\\s+note",
            "severity": "critical",
            "auto_fixable": False,
            "requires_gpt": True,
            "examples": {
                "incorrect": "Smith v. Jones, supra note 10, at 123.",
                "correct": "Smith, 100 U.S. at 123."
            }
        }
    ]

    # Bluebook Rule 10: Cases - add comprehensive case errors
    bb_10_errors = [
        {
            "error_id": "BB_10_2_CASE_NAME_THE",
            "error_name": "Case name starts with 'The'",
            "source_rule": "BB 10.2",
            "rule_title": "Case Names",
            "category": "case_names",
            "description": "Omit 'The' as first word of party name",
            "regex_detect": "\\bThe\\s+[A-Z][^\\s]+\\s+v\\.",
            "severity": "major",
            "auto_fixable": True,
            "examples": {
                "incorrect": "The New York Times Co. v. Sullivan",
                "correct": "New York Times Co. v. Sullivan"
            }
        },
        {
            "error_id": "BB_10_2_FIRST_WORD_ABBREV",
            "error_name": "First word of party name abbreviated",
            "source_rule": "BB 10.2",
            "rule_title": "Case Names",
            "category": "case_names",
            "description": "Do not abbreviate first word of party name",
            "regex_detect": "^Ass'n\\s+",
            "severity": "major",
            "auto_fixable": False,
            "requires_gpt": True,
            "examples": {
                "incorrect": "Ass'n of Data Processing v. Camp",
                "correct": "Association of Data Processing v. Camp"
            }
        },
        {
            "error_id": "BB_10_3_REPORTER_SERIES",
            "error_name": "Incorrect reporter series notation",
            "source_rule": "BB 10.3",
            "rule_title": "Reporters",
            "category": "reporters",
            "description": "Use 2d, 3d, 4th (not 2nd, 3rd)",
            "regex_detect": "\\b(2nd|3rd)\\b",
            "severity": "major",
            "auto_fixable": True,
            "examples": {
                "incorrect": "100 F.2nd 200",
                "correct": "100 F.2d 200"
            }
        },
        {
            "error_id": "BB_10_4_MISSING_COURT",
            "error_name": "Missing court designation when required",
            "source_rule": "BB 10.4",
            "rule_title": "Court and Jurisdiction",
            "category": "court_identification",
            "description": "Include court designation when not obvious from reporter",
            "regex_detect": "",
            "severity": "major",
            "auto_fixable": False,
            "requires_gpt": True,
            "examples": {
                "incorrect": "Smith v. Jones, 100 F. Supp. 200 (2000).",
                "correct": "Smith v. Jones, 100 F. Supp. 200 (S.D.N.Y. 2000)."
            }
        }
    ]

    # Bluebook Rules 11-13: Constitutions and Statutes
    bb_11_13_errors = [
        {
            "error_id": "BB_11_CONST_WITH_DATE",
            "error_name": "Constitutional citation includes date",
            "source_rule": "BB 11",
            "rule_title": "Constitutions",
            "category": "constitutions",
            "description": "Never include dates in constitutional citations",
            "regex_detect": "Const\\..*\\([12]\\d{3}\\)",
            "severity": "critical",
            "auto_fixable": True,
            "examples": {
                "incorrect": "U.S. Const. amend. XIV (1868).",
                "correct": "U.S. Const. amend. XIV."
            }
        },
        {
            "error_id": "BB_12_SECTION_NO_SPACE",
            "error_name": "Missing space after section symbol",
            "source_rule": "BB 12",
            "rule_title": "Statutes",
            "category": "statutes",
            "description": "Always include space between § and number",
            "regex_detect": "§\\d",
            "severity": "major",
            "auto_fixable": True,
            "examples": {
                "incorrect": "42 U.S.C. §1983",
                "correct": "42 U.S.C. § 1983"
            }
        },
        {
            "error_id": "BB_12_DOUBLE_SECTION_SINGLE",
            "error_name": "Single § used for multiple sections",
            "source_rule": "BB 12",
            "rule_title": "Statutes",
            "category": "statutes",
            "description": "Use §§ for multiple sections",
            "regex_detect": "§\\s+\\d+\\s*-\\s*\\d+",
            "severity": "major",
            "auto_fixable": True,
            "examples": {
                "incorrect": "42 U.S.C. § 1981-1988",
                "correct": "42 U.S.C. §§ 1981-1988"
            }
        }
    ]

    return bb_1_4_errors + bb_10_errors + bb_11_13_errors

def add_redbook_errors():
    """Add comprehensive Redbook-specific errors"""
    return [
        {
            "error_id": "RB_1_12_CF_MISSING_PAREN",
            "error_name": "'Cf.' signal missing required explanatory parenthetical",
            "source_rule": "RB 1.12",
            "rule_title": "Redbook Rule 1.12 - Signal Parenthetical Requirements",
            "category": "signal_parenthetical",
            "description": "Redbook Rule 1.12 REQUIRES explanatory parentheticals for 'Cf.' and 'But cf.' signals",
            "regex_detect": "\\bCf\\.\s+[^(]+\\([12]\\d{3}\\)\\.(?!\\s*\\()",
            "regex_validate": "\\bCf\\.\s+[^(]+\\([12]\\d{3}\\)\\s*\\([^)]+\\)",
            "severity": "critical",
            "citation_types": ["all"],
            "auto_fixable": False,
            "fix_pattern": "Add explanatory parenthetical after year",
            "gpt_validation_prompt": "Check if 'Cf.' signal has explanatory parenthetical. RB 1.12 REQUIRES this. Return: COMPLIANT or NON_COMPLIANT with suggested parenthetical.",
            "examples": {
                "incorrect": "Cf. Smith v. Jones, 123 U.S. 456 (2000).",
                "correct": "Cf. Smith v. Jones, 123 U.S. 456 (2000) (applying similar standard in contract context)."
            },
            "requires_gpt": True
        },
        {
            "error_id": "RB_1_12_SEE_GENERALLY_WITH_PAREN",
            "error_name": "'See generally' signal incorrectly includes parenthetical",
            "source_rule": "RB 1.12",
            "rule_title": "Redbook Rule 1.12 - Signal Parenthetical Requirements",
            "category": "signal_parenthetical",
            "description": "Redbook Rule 1.12: 'See generally' signals must NOT include explanatory parentheticals",
            "regex_detect": "\\bSee generally\\s+[^(]+\\([12]\\d{3}\\)\\s*\\([^)]+\\)",
            "regex_validate": "\\bSee generally\\s+[^(]+\\([12]\\d{3}\\)\\.?$",
            "severity": "major",
            "citation_types": ["all"],
            "auto_fixable": True,
            "fix_pattern": "Remove explanatory parenthetical",
            "gpt_validation_prompt": "Check if 'See generally' has parenthetical. RB 1.12 FORBIDS this. Return: COMPLIANT or NON_COMPLIANT.",
            "examples": {
                "incorrect": "See generally Smith v. Jones, 123 U.S. 456 (2000) (providing background).",
                "correct": "See generally Smith v. Jones, 123 U.S. 456 (2000)."
            },
            "requires_gpt": False
        },
        {
            "error_id": "RB_1_12_BUT_CF_MISSING_PAREN",
            "error_name": "'But cf.' signal missing required parenthetical",
            "source_rule": "RB 1.12",
            "rule_title": "Redbook Rule 1.12 - Signal Parenthetical Requirements",
            "category": "signal_parenthetical",
            "description": "Redbook Rule 1.12 REQUIRES explanatory parentheticals for 'But cf.' signals",
            "regex_detect": "\\bBut cf\\.\s+[^(]+\\([12]\\d{3}\\)\\.(?!\\s*\\()",
            "regex_validate": "\\bBut cf\\.\s+[^(]+\\([12]\\d{3}\\)\\s*\\([^)]+\\)",
            "severity": "critical",
            "citation_types": ["all"],
            "auto_fixable": False,
            "fix_pattern": "Add explanatory parenthetical",
            "gpt_validation_prompt": "Check if 'But cf.' has parenthetical. RB 1.12 REQUIRES this. Return: COMPLIANT or NON_COMPLIANT with suggested parenthetical.",
            "examples": {
                "incorrect": "But cf. Smith v. Jones, 123 U.S. 456 (2000).",
                "correct": "But cf. Smith v. Jones, 123 U.S. 456 (2000) (reaching opposite conclusion)."
            },
            "requires_gpt": True
        },
        {
            "error_id": "RB_1_4_FOOTNOTE_PLACEMENT",
            "error_name": "Footnote not at end of sentence (Redbook)",
            "source_rule": "RB 1.4",
            "rule_title": "Footnote Placement",
            "category": "footnote_placement",
            "description": "Redbook: Always place footnote at END of sentence, even if supports only part",
            "regex_detect": "",
            "severity": "major",
            "auto_fixable": False,
            "requires_gpt": True,
            "examples": {
                "incorrect": "The court applied strict scrutiny,¹ but upheld the statute.",
                "correct": "The court applied strict scrutiny, but upheld the statute.¹"
            }
        },
        {
            "error_id": "RB_10_9_BEYOND_FIVE_FOOTNOTES",
            "error_name": "Short form used beyond five footnotes",
            "source_rule": "RB 10.9",
            "rule_title": "Five-Footnote Rule",
            "category": "short_form",
            "description": "Redbook: Use full citation if not cited within previous five footnotes",
            "regex_detect": "",
            "severity": "major",
            "auto_fixable": False,
            "requires_gpt": True,
            "examples": {
                "incorrect": "Short form in footnote 20 when last full cite in footnote 14",
                "correct": "Full citation repeated in footnote 20"
            }
        }
    ]

def main():
    """Main compilation function"""
    print("=" * 80)
    print("MASTER ERROR DETECTION FRAMEWORK COMPILER V2")
    print("Comprehensive extraction of ALL citation errors")
    print("=" * 80)

    extractor = ErrorExtractor()
    analysis_dir = Path("/home/user/slr/SLRinator/output/analysis")

    # Extract from all sources
    print("\n1. Extracting from Rules 5-9 JSON...")
    extractor.extract_from_rules_5_9_json(analysis_dir / "rules_5-9_analysis.json")

    print("2. Extracting from Rules 1-4 Markdown...")
    extractor.extract_from_markdown_comprehensive(analysis_dir / "rules_1-4_analysis.md", "BB_1-4")

    print("3. Extracting from Rule 10 Core Markdown...")
    extractor.extract_from_markdown_comprehensive(analysis_dir / "rule_10_cases_core.md", "BB_10_CORE")

    print("4. Extracting from Rule 10 Advanced Markdown...")
    extractor.extract_from_markdown_comprehensive(analysis_dir / "rule_10_cases_advanced.md", "BB_10_ADV")

    print("5. Extracting from Rules 12-13 Markdown...")
    extractor.extract_from_markdown_comprehensive(analysis_dir / "rules_12-13_analysis.md", "BB_12-13")

    print("6. Extracting from Rules 14-16 Markdown...")
    extractor.extract_from_markdown_comprehensive(analysis_dir / "rules_14-16_analysis.md", "BB_14-16")

    print("7. Extracting from Tables 1-5...")
    extractor.extract_from_tables_comprehensive(analysis_dir / "tables_1-5_analysis.json", "T1-5")

    print("8. Extracting from Tables 6-8...")
    extractor.extract_from_tables_comprehensive(analysis_dir / "tables_6-8_analysis.json", "T6-8")

    print("9. Extracting from Tables 9-16...")
    extractor.extract_from_tables_comprehensive(analysis_dir / "tables_9-16_analysis.json", "T9-16")

    print("10. Adding comprehensive Bluebook errors...")
    bb_errors = add_comprehensive_bluebook_errors()
    for error in bb_errors:
        extractor.add_error(error)

    print("11. Adding Redbook-specific errors with RB 1.12 fix...")
    rb_errors = add_redbook_errors()
    for error in rb_errors:
        extractor.add_error(error)

    # Compile final framework
    total_errors = len(extractor.all_errors)
    print("\n" + "=" * 80)
    print(f"TOTAL ERRORS COMPILED: {total_errors}")
    print("=" * 80)

    framework = {
        "metadata": {
            "version": "2.0.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "description": "COMPLETE Master Error Detection Framework - ALL citation errors from Bluebook and Redbook",
            "total_error_types": total_errors,
            "includes_redbook_fixes": True,
            "critical_rb_1_12_fix": "Cf./But cf. REQUIRE parentheticals; See generally must NOT have them"
        },
        "errors": extractor.all_errors
    }

    # Write output
    output_path = Path("/home/user/slr/SLRinator/config/error_detection_framework_COMPLETE.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(framework, f, indent=2, ensure_ascii=False)

    file_size = output_path.stat().st_size
    print(f"\nFramework written to: {output_path}")
    print(f"File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")

    # Statistics
    print("\n" + "=" * 80)
    print("STATISTICS")
    print("=" * 80)

    categories = {}
    severities = {}
    for error in extractor.all_errors:
        cat = error.get('category', 'unknown')
        sev = error.get('severity', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
        severities[sev] = severities.get(sev, 0) + 1

    print("\nBy Category:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat:30s}: {count:4d}")

    print("\nBy Severity:")
    for sev, count in sorted(severities.items(), key=lambda x: x[1], reverse=True):
        print(f"  {sev:30s}: {count:4d}")

    auto_fix = sum(1 for e in extractor.all_errors if e.get('auto_fixable', False))
    needs_gpt = sum(1 for e in extractor.all_errors if e.get('requires_gpt', False))

    print(f"\nAuto-fixable: {auto_fix} ({auto_fix/total_errors*100:.1f}%)")
    print(f"Requires GPT: {needs_gpt} ({needs_gpt/total_errors*100:.1f}%)")

    print("\n" + "=" * 80)
    print("COMPLETE!")
    print("=" * 80)

if __name__ == "__main__":
    main()
