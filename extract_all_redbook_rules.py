#!/usr/bin/env python3
"""
Comprehensive Redbook Rule Extraction Script
Extracts EVERY SINGLE Redbook rule from all HTML files,
separating them from Bluebook rules.
"""

import os
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, List, Any

def extract_text_preserving_formatting(element):
    """Extract text while preserving important formatting indicators"""
    if element is None:
        return ""

    # Get all text but note italics and emphasis
    text_parts = []
    for child in element.descendants:
        if isinstance(child, str):
            text_parts.append(str(child))
        elif child.name == 'em':
            text_parts.append(f"__{child.get_text()}__")
        elif child.name == 'strong':
            text_parts.append(f"**{child.get_text()}**")

    return ''.join(text_parts)

def is_deviation_from_bluebook(element):
    """Check if content is marked as deviation from Bluebook (red text)"""
    if element is None:
        return False

    # Check for red color styling
    style = element.get('style', '')
    if 'color' in style and ('C00000' in style or 'red' in style.lower()):
        return True

    # Check span elements with color
    for span in element.find_all('span', style=True):
        if 'color' in span['style'] and ('C00000' in span['style'] or 'red' in span['style'].lower()):
            return True

    # Check if parent paragraph contains red text indicator
    text = element.get_text()
    if 'marked in red' in text.lower():
        return True

    return False

def extract_examples(soup):
    """Extract all examples from the document"""
    examples = []

    # Find all example divs
    example_divs = soup.find_all('div', class_='example')
    for div in example_divs:
        example_text = div.get_text(strip=True)
        examples.append(example_text)

    return examples

def extract_lists_and_bullets(element):
    """Extract structured lists and bullet points"""
    lists = []

    if element is None:
        return lists

    for ul in element.find_all(['ul', 'ol']):
        list_items = []
        for li in ul.find_all('li', recursive=False):
            list_items.append(li.get_text(strip=True))
        if list_items:
            lists.append(list_items)

    return lists

def generate_regex_patterns(rule_content, section_number):
    """Generate regex patterns based on rule content"""
    patterns = []

    # Pattern for Id. usage (Section 4.1)
    if '4.1' in section_number and 'id.' in rule_content.lower():
        patterns.append({
            "pattern": r"\b[Ii]d\.\s+at\s+\d+",
            "description": "Id. with page reference",
            "example": "Id. at 42"
        })
        patterns.append({
            "pattern": r"^[Ii]d\.",
            "description": "Id. at start of citation",
            "example": "Id."
        })

    # Pattern for one space rule (Section 22.7)
    if '22.7' in section_number and 'one space' in rule_content.lower():
        patterns.append({
            "pattern": r"[.;:]\s{2,}",
            "description": "Multiple spaces after punctuation (should be single space)",
            "example": ".  " ,
            "correction": ". "
        })

    # Pattern for et al. (Section 15.1)
    if '15.1' in section_number or 'et al' in rule_content.lower():
        patterns.append({
            "pattern": r"\bet\s+al\.",
            "description": "Et al. usage in citations",
            "example": "John Doe et al."
        })

    # Pattern for hereinafter (Section 4.4)
    if '4.4' in section_number or 'hereinafter' in rule_content.lower():
        patterns.append({
            "pattern": r"\[hereinafter\s+[^\]]+\]",
            "description": "Hereinafter short form designation",
            "example": "[hereinafter Short Name]"
        })

    # Pattern for supra (short citation forms)
    if 'supra' in rule_content.lower():
        patterns.append({
            "pattern": r"\b\w+,\s+supra\s+note\s+\d+",
            "description": "Supra note reference",
            "example": "Smith, supra note 1"
        })

    # Pattern for case names
    if 'case name' in rule_content.lower() or section_number.startswith('10'):
        patterns.append({
            "pattern": r"[A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+",
            "description": "Basic case name pattern",
            "example": "Smith v. Jones"
        })

    # Pattern for quotation parentheticals
    if 'quoting' in rule_content.lower() or 'citing' in rule_content.lower():
        patterns.append({
            "pattern": r"\(quoting\s+[^\)]+\)",
            "description": "Quoting parenthetical",
            "example": "(quoting Source, 123 U.S. at 45)"
        })
        patterns.append({
            "pattern": r"\(citing\s+[^\)]+\)",
            "description": "Citing parenthetical",
            "example": "(citing Source, 123 U.S. at 45)"
        })

    # Pattern for pincites
    if 'pincite' in rule_content.lower() or 'at' in rule_content:
        patterns.append({
            "pattern": r",\s+at\s+\d+",
            "description": "Pincite reference",
            "example": ", at 123"
        })

    return patterns

def extract_rule_from_file(file_path):
    """Extract complete rule information from a single Redbook HTML file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')

    # Extract section info
    section_info = soup.find('div', class_='section-info')
    section_number = ""
    section_title = ""

    if section_info:
        info_text = section_info.get_text()
        # Extract section number and title
        if 'Section' in info_text:
            match = re.search(r'Section\s+([\d.]+):\s*(.+)', info_text)
            if match:
                section_number = match.group(1)
                section_title = match.group(2).strip()
        elif 'Preamble' in info_text:
            section_number = "Preamble"
            section_title = "Preamble"

    # Extract main content
    redbook_content = soup.find('div', class_='redbook-content')

    if not redbook_content:
        return None

    # Extract all paragraphs and headings
    rule_text = []
    deviations = []

    for element in redbook_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'div']):
        text = element.get_text(strip=True)
        if text:
            # Check if this is a deviation from Bluebook
            if is_deviation_from_bluebook(element):
                deviations.append(text)
            rule_text.append(text)

    # Extract examples
    examples = extract_examples(soup)

    # Extract lists
    lists = extract_lists_and_bullets(redbook_content)

    # Get complete text for pattern generation
    complete_text = '\n'.join(rule_text)

    # Generate regex patterns
    patterns = generate_regex_patterns(complete_text, section_number)

    # Determine if this is SLR-specific or a Bluebook deviation
    is_slr_specific = False
    is_bluebook_deviation = len(deviations) > 0

    if any(phrase in complete_text for phrase in ['SLR always', 'SLR requires', 'SLR never', 'SLR uses']):
        is_slr_specific = True

    # Extract cross-references to Bluebook
    bluebook_refs = re.findall(r'BB\s+[\d.]+', complete_text)

    # Build the rule object
    rule = {
        "file": os.path.basename(file_path),
        "section_number": section_number,
        "section_title": section_title,
        "rule_type": "SLR_SPECIFIC" if is_slr_specific else ("BLUEBOOK_DEVIATION" if is_bluebook_deviation else "CLARIFICATION"),
        "rule_content": complete_text,
        "rule_paragraphs": rule_text,
        "deviations_from_bluebook": deviations,
        "examples": examples,
        "structured_lists": lists,
        "bluebook_references": bluebook_refs,
        "regex_patterns": patterns,
        "metadata": {
            "is_slr_house_style": is_slr_specific,
            "contradicts_bluebook": is_bluebook_deviation,
            "has_examples": len(examples) > 0,
            "has_patterns": len(patterns) > 0
        }
    }

    return rule

def main():
    """Main extraction function"""
    redbook_dir = Path('/home/user/slr/reference_files/redbook_processed')

    # Get all redbook HTML files
    redbook_files = sorted(redbook_dir.glob('rb_*.html'))

    print(f"Found {len(redbook_files)} Redbook files")

    all_rules = []

    for file_path in redbook_files:
        print(f"Processing {file_path.name}...")
        rule = extract_rule_from_file(file_path)
        if rule:
            all_rules.append(rule)

    # Organize rules by category
    categorized_rules = {
        "metadata": {
            "source": "Stanford Law Review Redbook (Volume 78)",
            "description": "Complete extraction of ALL Redbook rules, separate from Bluebook",
            "total_rules": len(all_rules),
            "extraction_date": "2025-11-23",
            "hierarchy": [
                "1. The Redbook (RB) - SLR-specific rules and house style",
                "2. The Bluebook (BB) - Referenced but not included here",
                "3. The Chicago Manual of Style (CMOS)",
                "4. Merriam-Webster"
            ]
        },
        "preamble": {},
        "slr_specific_rules": [],
        "bluebook_deviations": [],
        "clarifications": [],
        "all_rules_by_section": {}
    }

    for rule in all_rules:
        # Add to appropriate category
        if rule["section_number"] == "Preamble":
            categorized_rules["preamble"] = rule
        elif rule["rule_type"] == "SLR_SPECIFIC":
            categorized_rules["slr_specific_rules"].append(rule)
        elif rule["rule_type"] == "BLUEBOOK_DEVIATION":
            categorized_rules["bluebook_deviations"].append(rule)
        else:
            categorized_rules["clarifications"].append(rule)

        # Add to section index
        section_key = f"section_{rule['section_number'].replace('.', '_')}"
        categorized_rules["all_rules_by_section"][section_key] = rule

    # Update metadata counts
    categorized_rules["metadata"]["slr_specific_count"] = len(categorized_rules["slr_specific_rules"])
    categorized_rules["metadata"]["bluebook_deviation_count"] = len(categorized_rules["bluebook_deviations"])
    categorized_rules["metadata"]["clarification_count"] = len(categorized_rules["clarifications"])

    # Write to JSON file
    output_file = Path('/home/user/slr/REDBOOK_ALL_RULES_MASTER.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(categorized_rules, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"EXTRACTION COMPLETE!")
    print(f"{'='*60}")
    print(f"Total rules extracted: {len(all_rules)}")
    print(f"SLR-specific rules: {len(categorized_rules['slr_specific_rules'])}")
    print(f"Bluebook deviations: {len(categorized_rules['bluebook_deviations'])}")
    print(f"Clarifications: {len(categorized_rules['clarifications'])}")
    print(f"\nOutput written to: {output_file}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
