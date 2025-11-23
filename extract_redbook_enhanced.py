#!/usr/bin/env python3
"""
ENHANCED Redbook Rule Extraction Script
Extracts EVERY SINGLE Redbook rule with maximum detail,
properly identifying ALL deviations from Bluebook (red-marked text).
"""

import os
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
from typing import Dict, List, Any

def extract_text_with_formatting(element):
    """Extract text while preserving formatting indicators"""
    if element is None:
        return ""

    result = []
    for item in element.descendants:
        if isinstance(item, NavigableString):
            text = str(item).strip()
            if text:
                result.append(text)

    return ' '.join(result)

def find_red_deviations(soup):
    """Find ALL text marked in red (Bluebook deviations)"""
    deviations = []

    # Look for spans with red color
    red_spans = soup.find_all('span', style=lambda value: value and 'color:#C00000' in value)
    for span in red_spans:
        text = extract_text_with_formatting(span)
        if text and len(text) > 10:  # Avoid trivial matches
            deviations.append({
                "text": text,
                "type": "DEVIATION_FROM_BLUEBOOK",
                "marker": "Red text in original Redbook"
            })

    # Also check for paragraphs containing red spans
    for p in soup.find_all('p'):
        if p.find('span', style=lambda value: value and 'color:#C00000' in value):
            red_content = p.find('span', style=lambda value: value and 'color:#C00000' in value)
            if red_content:
                text = extract_text_with_formatting(red_content)
                # Check if not already captured
                if text and len(text) > 10:
                    if not any(d['text'] == text for d in deviations):
                        deviations.append({
                            "text": text,
                            "type": "DEVIATION_FROM_BLUEBOOK",
                            "marker": "Red paragraph text"
                        })

    return deviations

def extract_correct_incorrect_examples(soup):
    """Extract examples marked as Correct vs Incorrect"""
    correct_examples = []
    incorrect_examples = []

    example_divs = soup.find_all('div', class_='example')
    for div in example_divs:
        text = extract_text_with_formatting(div)

        # Check for correct/incorrect markers
        if 'Correct:' in text or 'class="correct"' in str(div):
            correct_examples.append(text.replace('Correct:', '').strip())
        elif 'Incorrect:' in text or 'class="incorrect"' in str(div):
            incorrect_examples.append(text.replace('Incorrect:', '').strip())
        else:
            # Just a regular example
            correct_examples.append(text)

    return correct_examples, incorrect_examples

def extract_comprehensive_patterns(rule_content, section_number, examples):
    """Generate comprehensive regex patterns based on rule content"""
    patterns = []

    lower_content = rule_content.lower()

    # ID patterns (Section 4.1-4.3)
    if any(x in section_number for x in ['4.1', '4.2', '4.3']) or 'id.' in lower_content:
        patterns.extend([
            {
                "pattern": r"\bId\.\s+at\s+\d+",
                "description": "Id. with page reference (capitalize I)",
                "bluebook_ref": "BB 4.1",
                "example": "Id. at 42"
            },
            {
                "pattern": r"^Id\.",
                "description": "Id. at start of citation",
                "bluebook_ref": "BB 4.1",
                "example": "Id."
            },
            {
                "pattern": r"\bid\.\s+at",
                "description": "Lowercase id. (likely incorrect)",
                "bluebook_ref": "BB 4.1",
                "example": "id. at 42",
                "note": "Should be capitalized: Id."
            }
        ])

    # One space rule (Section 22.7)
    if '22.7' in section_number or 'one space' in lower_content:
        patterns.extend([
            {
                "pattern": r"[.;:]\s{2,}",
                "description": "Multiple spaces after punctuation (SLR violation)",
                "redbook_rule": "RB 22.7",
                "example": ".  ",
                "correction": ". ",
                "severity": "REQUIRED_CHANGE"
            },
            {
                "pattern": r"\.\s(?=\S)",
                "description": "Single space after period (correct SLR style)",
                "redbook_rule": "RB 22.7",
                "example": ". The",
                "severity": "CORRECT"
            }
        ])

    # Et al. patterns (Section 15.1)
    if '15.1' in section_number or 'et al' in lower_content:
        patterns.extend([
            {
                "pattern": r"\bet\s+al\.",
                "description": "Et al. in short form citations",
                "bluebook_ref": "BB 15.1",
                "redbook_note": "RB 15.1 - First citation must include ALL authors",
                "example": "Smith et al."
            },
            {
                "pattern": r"(?:,\s+)([A-Z][a-z]+(?:\s+[A-Z]\.)?\s+[A-Z][a-z]+(?:,\s+[A-Z][a-z]+(?:\s+[A-Z]\.)?\s+[A-Z][a-z]+)*)\s+et\s+al\.",
                "description": "Multiple authors with et al. (check if first citation)",
                "redbook_deviation": "SLR requires ALL authors in first citation",
                "example": "John Smith, Jane Doe et al."
            }
        ])

    # Subtitles (Section 15.2)
    if '15.2' in section_number or 'subtitle' in lower_content:
        patterns.extend([
            {
                "pattern": r":\s*[A-Z]",
                "description": "Colon separator in title:subtitle",
                "redbook_rule": "RB 15.2 - SLR always includes subtitles",
                "example": "Main Title: Subtitle"
            },
            {
                "pattern": r"[—–]\s*[A-Z]",
                "description": "Em dash or en dash in title",
                "redbook_rule": "RB 15.2",
                "example": "Main Title—Subtitle"
            }
        ])

    # Case names (Section 10)
    if section_number.startswith('10') or 'case name' in lower_content:
        patterns.extend([
            {
                "pattern": r"(?:^|\s)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
                "description": "Basic case name pattern",
                "bluebook_ref": "BB 10.2",
                "example": "Smith v. Jones"
            },
            {
                "pattern": r"\b[A-Z][a-z]+\s+v\.\s+Bd\.\s+of\s+",
                "description": "Case name with 'Board' abbreviated",
                "bluebook_ref": "BB 10.2.2",
                "example": "Smith v. Bd. of Education"
            }
        ])

    # Signals as verbs (Section 10.16)
    if '10.16' in section_number or 'signal' in lower_content:
        patterns.extend([
            {
                "pattern": r"\bsee\s+(?!also|generally|e\.g\.|,)[A-Z]",
                "description": "See used as verb (not italicized, case name should be italicized)",
                "redbook_rule": "RB 10.16",
                "example": "see Brown v. Board of Education"
            },
            {
                "pattern": r",\s*see,\s*e\.g\.,\s*[A-Z]",
                "description": "See as citation signal (italicized, case name abbreviated)",
                "bluebook_ref": "BB 1.2",
                "example": ", see, e.g., Brown v. Bd. of Educ."
            }
        ])

    # Quoting/citing parentheticals (Section 1.1)
    if '1.1' in section_number or 'quoting' in lower_content or 'citing' in lower_content:
        patterns.extend([
            {
                "pattern": r"\(quoting\s+[^\)]+\)",
                "description": "Quoting parenthetical (SLR requires when source quotes another)",
                "redbook_rule": "RB 1.1 - ALWAYS required",
                "bluebook_ref": "BB 1.5",
                "example": "(quoting Source, 123 U.S. at 45)"
            },
            {
                "pattern": r"\(citing\s+[^\)]+\)",
                "description": "Citing parenthetical (optional at SLR)",
                "redbook_rule": "RB 1.1 - Never required",
                "bluebook_ref": "BB 1.5",
                "example": "(citing Source, 123 U.S. at 45)"
            }
        ])

    # Pincites (Section 3.6)
    if '3.6' in section_number or 'pincite' in lower_content:
        patterns.extend([
            {
                "pattern": r",\s+at\s+\d+(?:-\d+)?",
                "description": "Pincite reference to page or page range",
                "bluebook_ref": "BB 3.2",
                "example": ", at 123-25"
            },
            {
                "pattern": r",\s+at\s+\d+\s+n\.\d+",
                "description": "Pincite to footnote",
                "bluebook_ref": "BB 3.2(b)",
                "example": ", at 123 n.4"
            }
        ])

    # Hereinafter (Section 4.4)
    if '4.4' in section_number or 'hereinafter' in lower_content:
        patterns.extend([
            {
                "pattern": r"\[hereinafter\s+[^\]]+\]",
                "description": "Hereinafter short form designation",
                "bluebook_ref": "BB 4.2(b)",
                "example": "[hereinafter Short Name]"
            }
        ])

    # Supra references
    if 'supra' in lower_content:
        patterns.extend([
            {
                "pattern": r"\b[A-Z][a-z]+(?:\s+et\s+al\.)?,\s+supra\s+note\s+\d+",
                "description": "Supra note reference",
                "bluebook_ref": "BB 4.2(a)",
                "example": "Smith, supra note 1"
            },
            {
                "pattern": r"\b[A-Z][a-z]+,\s+supra,\s+at\s+\d+",
                "description": "Supra with page reference (no note number)",
                "bluebook_ref": "BB 4.2(a)",
                "example": "Smith, supra, at 45"
            }
        ])

    # Underline vs italic (Section 2.1)
    if '2.1' in section_number or 'underlin' in lower_content:
        patterns.extend([
            {
                "pattern": r"<u>|<span[^>]*text-decoration:\s*underline",
                "description": "Underlined text (SLR does not use underlines)",
                "redbook_deviation": "RB 2.1 - Use italics instead",
                "severity": "REQUIRED_CHANGE"
            }
        ])

    # Et seq. (Section 3.7)
    if '3.7' in section_number or 'et seq' in lower_content:
        patterns.extend([
            {
                "pattern": r"\bet\s+seq\.",
                "description": "Et seq. (SLR does not use)",
                "redbook_deviation": "RB 3.7 - Specify full range instead",
                "bluebook_ref": "BB 3.3(b)",
                "severity": "FORBIDDEN"
            }
        ])

    # Public domain citations (Section 10.15)
    if '10.15' in section_number or 'public domain' in lower_content:
        patterns.append({
            "pattern": r"\d{4}\s+[A-Z]{2}\s+\d+",
            "description": "Public domain citation format (SLR does not use)",
            "redbook_deviation": "RB 10.15 - Do not use public domain citations",
            "example": "2020 VT 123",
            "severity": "FORBIDDEN"
        })

    # Docket numbers (Section 10.12)
    if '10.12' in section_number or 'docket' in lower_content:
        patterns.extend([
            {
                "pattern": r"No\.\s+\d{1,2}:\d{2}-[a-z]{2}-\d+",
                "description": "Docket number with initial digit before colon (remove per SLR)",
                "redbook_rule": "RB 10.12 - Omit digit before colon",
                "example": "No. 2:12-cr-02323",
                "correction_example": "No. 12-cr-02323"
            },
            {
                "pattern": r"No\.\s+\d{2}-[a-z]{2}-\d+(?:\s+\([A-Z]{2,3}\))?",
                "description": "Docket number, possibly with judge initials (remove initials per SLR)",
                "redbook_rule": "RB 10.12 - Omit judge initials",
                "example": "No. 99-839-cv (JPO)"
            }
        ])

    # Federal Register dates (Section 14.1)
    if '14.1' in section_number or 'federal register' in lower_content:
        patterns.append({
            "pattern": r"\d{1,3}\s+Fed\.\s+Reg\.\s+\d+(?:,\s+\d+)?\s+\([A-Za-z]+\.?\s+\d{1,2},\s+\d{4}\)",
            "description": "Federal Register citation with full date",
            "bluebook_ref": "BB 14.2",
            "example": "85 Fed. Reg. 12345 (Mar. 1, 2020)"
        })

    return patterns

def extract_rule_comprehensive(file_path):
    """Extract complete rule with all details"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')

    # Extract section info
    section_info = soup.find('div', class_='section-info')
    section_number = ""
    section_title = ""

    if section_info:
        info_text = section_info.get_text()
        if 'Section' in info_text:
            match = re.search(r'Section\s+([\d.]+):\s*(.+)', info_text)
            if match:
                section_number = match.group(1)
                section_title = match.group(2).strip()
        elif 'Preamble' in info_text:
            section_number = "Preamble"
            section_title = "Preamble - Hierarchy of Rules"

    # Extract main content
    redbook_content = soup.find('div', class_='redbook-content')

    if not redbook_content:
        return None

    # Extract text paragraphs (avoiding duplicates)
    paragraphs = []
    seen_texts = set()

    for element in redbook_content.find_all(['p', 'h3', 'h4', 'h5'], recursive=True):
        text = extract_text_with_formatting(element)
        if text and text not in seen_texts and len(text) > 5:
            paragraphs.append(text)
            seen_texts.add(text)

    # Complete rule text
    complete_text = '\n\n'.join(paragraphs)

    # Extract deviations (red text)
    deviations = find_red_deviations(soup)

    # Extract examples
    correct_examples, incorrect_examples = extract_correct_incorrect_examples(soup)

    # Extract lists
    structured_lists = []
    for ul in redbook_content.find_all(['ul', 'ol']):
        list_items = []
        for li in ul.find_all('li', recursive=False):
            item_text = extract_text_with_formatting(li)
            if item_text:
                list_items.append(item_text)
        if list_items:
            structured_lists.append(list_items)

    # Bluebook references
    bluebook_refs = list(set(re.findall(r'BB\s+[\d.]+(?:\([a-z]\))?', complete_text)))
    cmos_refs = list(set(re.findall(r'CMOS\s+[\d.]+', complete_text)))

    # Generate patterns
    all_examples = correct_examples + incorrect_examples
    patterns = extract_comprehensive_patterns(complete_text, section_number, all_examples)

    # Determine rule type
    is_slr_specific = any(phrase in complete_text for phrase in [
        'SLR always', 'SLR requires', 'SLR never', 'SLR uses', 'SLR does not'
    ])

    is_bluebook_deviation = len(deviations) > 0 or any(phrase in complete_text for phrase in [
        'Contra BB', 'deviates from', 'instead of', 'SLR does not use'
    ])

    # Build comprehensive rule object
    rule = {
        "file": os.path.basename(file_path),
        "section_number": section_number,
        "section_title": section_title,
        "rule_type": "SLR_SPECIFIC" if is_slr_specific else ("BLUEBOOK_DEVIATION" if is_bluebook_deviation else "CLARIFICATION"),
        "rule_summary": paragraphs[0] if paragraphs else "",
        "full_rule_text": complete_text,
        "rule_paragraphs": paragraphs,
        "deviations_from_bluebook": deviations,
        "correct_examples": correct_examples,
        "incorrect_examples": incorrect_examples,
        "structured_lists": structured_lists,
        "bluebook_references": bluebook_refs,
        "cmos_references": cmos_refs,
        "regex_patterns": patterns,
        "metadata": {
            "is_slr_house_style": is_slr_specific,
            "contradicts_bluebook": is_bluebook_deviation,
            "has_examples": len(correct_examples) + len(incorrect_examples) > 0,
            "has_patterns": len(patterns) > 0,
            "has_red_text_deviation": len(deviations) > 0,
            "complexity": "HIGH" if len(paragraphs) > 5 else ("MEDIUM" if len(paragraphs) > 2 else "LOW")
        }
    }

    return rule

def main():
    """Main extraction function"""
    redbook_dir = Path('/home/user/slr/reference_files/redbook_processed')
    redbook_files = sorted(redbook_dir.glob('rb_*.html'))

    print(f"Found {len(redbook_files)} Redbook files")
    print("=" * 70)

    all_rules = []

    for file_path in redbook_files:
        print(f"Processing {file_path.name}...")
        rule = extract_rule_comprehensive(file_path)
        if rule:
            all_rules.append(rule)
            if rule['deviations_from_bluebook']:
                print(f"  → Found {len(rule['deviations_from_bluebook'])} RED-MARKED DEVIATIONS")

    # Organize rules
    categorized = {
        "metadata": {
            "source": "Stanford Law Review Redbook (Volume 78)",
            "description": "COMPREHENSIVE extraction of ALL Redbook rules, completely separate from Bluebook",
            "note": "The Redbook supplements and sometimes OVERRIDES the Bluebook",
            "total_rules": len(all_rules),
            "extraction_date": "2025-11-23",
            "hierarchy": [
                "1. The Redbook (RB) - Stanford Law Review house style - TAKES PRECEDENCE",
                "2. The Bluebook (BB) - General citation guide",
                "3. The Chicago Manual of Style (CMOS)",
                "4. Merriam-Webster"
            ]
        },
        "preamble": None,
        "slr_specific_rules": [],
        "bluebook_deviations": [],
        "clarifications": [],
        "all_rules_by_section": {},
        "quick_reference": {
            "major_deviations": [],
            "forbidden_practices": [],
            "required_practices": []
        }
    }

    # Categorize rules
    for rule in all_rules:
        if rule["section_number"] == "Preamble":
            categorized["preamble"] = rule
        elif rule["rule_type"] == "SLR_SPECIFIC":
            categorized["slr_specific_rules"].append(rule)
        elif rule["rule_type"] == "BLUEBOOK_DEVIATION":
            categorized["bluebook_deviations"].append(rule)
        else:
            categorized["clarifications"].append(rule)

        # Add to section index
        section_key = f"section_{rule['section_number'].replace('.', '_')}"
        categorized["all_rules_by_section"][section_key] = rule

        # Add to quick reference
        if rule.get('deviations_from_bluebook'):
            for dev in rule['deviations_from_bluebook']:
                categorized["quick_reference"]["major_deviations"].append({
                    "section": rule['section_number'],
                    "title": rule['section_title'],
                    "deviation": dev['text']
                })

        # Check for forbidden practices
        if any(word in rule['full_rule_text'] for word in ['does not use', 'never', 'forbidden']):
            if 'et seq' in rule['full_rule_text'].lower():
                categorized["quick_reference"]["forbidden_practices"].append({
                    "practice": "et seq.",
                    "section": rule['section_number'],
                    "note": "Specify full range instead"
                })
            if 'underline' in rule['full_rule_text'].lower():
                categorized["quick_reference"]["forbidden_practices"].append({
                    "practice": "Underlined type",
                    "section": rule['section_number'],
                    "note": "Use italics instead"
                })
            if 'public domain' in rule['full_rule_text'].lower():
                categorized["quick_reference"]["forbidden_practices"].append({
                    "practice": "Public domain citations",
                    "section": rule['section_number'],
                    "note": "Do not use public domain format"
                })

    # Update counts
    categorized["metadata"]["slr_specific_count"] = len(categorized["slr_specific_rules"])
    categorized["metadata"]["bluebook_deviation_count"] = len(categorized["bluebook_deviations"])
    categorized["metadata"]["clarification_count"] = len(categorized["clarifications"])
    categorized["metadata"]["red_marked_deviations"] = len(categorized["quick_reference"]["major_deviations"])

    # Write output
    output_file = Path('/home/user/slr/REDBOOK_ALL_RULES_MASTER.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(categorized, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("EXTRACTION COMPLETE!")
    print("=" * 70)
    print(f"Total rules extracted: {len(all_rules)}")
    print(f"SLR-specific rules: {len(categorized['slr_specific_rules'])}")
    print(f"Bluebook deviations: {len(categorized['bluebook_deviations'])}")
    print(f"Clarifications: {len(categorized['clarifications'])}")
    print(f"Red-marked deviations: {len(categorized['quick_reference']['major_deviations'])}")
    print(f"Forbidden practices: {len(categorized['quick_reference']['forbidden_practices'])}")
    print(f"\nOutput: {output_file}")
    print("=" * 70)

if __name__ == "__main__":
    main()
