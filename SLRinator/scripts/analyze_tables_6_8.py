#!/usr/bin/env python3
"""
Comprehensive analysis of Bluebook Tables T6, T7, and T8.
Processes all 451 entries to create regex patterns, error patterns, and GPT prompts.
"""

import json
import re
from pathlib import Path

def escape_regex(text):
    """Escape special regex characters while preserving word boundaries."""
    # Characters that need escaping in regex
    special_chars = r'\.^$*+?{}[]()|\/'
    escaped = ''.join('\\' + c if c in special_chars else c for c in text)
    return escaped

def create_regex_long(word):
    """Create regex pattern for unabbreviated form."""
    # Handle special cases
    if word == "and":
        return r"\band\b"

    # Split on slashes and parentheses to get all variants
    variants = []

    # Handle slash variants (e.g., "Accountant/Accounting/Accountancy")
    if "/" in word:
        parts = word.split("/")
        variants.extend(parts)
    else:
        variants.append(word)

    # Handle parenthetical variants (e.g., "Business(es)")
    expanded_variants = []
    for variant in variants:
        if "(" in variant:
            # Extract base and optional parts
            base = variant.split("(")[0]
            optional = variant[variant.find("(")+1:variant.find(")")]
            expanded_variants.append(base)
            expanded_variants.append(base + optional)
        else:
            expanded_variants.append(variant)

    # Create regex pattern
    if len(expanded_variants) > 1:
        # Multiple variants: create alternation
        escaped_variants = [escape_regex(v.strip()) for v in expanded_variants]
        pattern = r"\b(" + "|".join(escaped_variants) + r")\b"
    else:
        # Single variant
        escaped = escape_regex(expanded_variants[0].strip())
        pattern = r"\b" + escaped + r"\b"

    return pattern

def create_regex_short(abbr):
    """Create regex pattern for abbreviated form."""
    # Remove explanatory notes in parentheses (e.g., "(name county if needed)")
    # But keep brackets that are part of the abbreviation (e.g., "[denied]")
    if "(" in abbr and ")" in abbr:
        # Check if this is an explanatory note or part of the abbreviation
        paren_content = abbr[abbr.find("(")+1:abbr.find(")")]
        if any(word in paren_content.lower() for word in ["name", "if", "needed", "other"]):
            # This is an explanatory note, remove it
            abbr = abbr[:abbr.find("(")].strip()

    # Handle multiple abbreviations (e.g., "Adm'r, Adm'x")
    if "," in abbr:
        abbrs = [a.strip() for a in abbr.split(",")]
        escaped_abbrs = [escape_regex(a) for a in abbrs]
        pattern = r"\b(" + "|".join(escaped_abbrs) + r")\b"
    elif "/" in abbr and " / " in abbr:
        # Handle "Ct. Gen. Sess. / Ct. Spec. Sess."
        abbrs = [a.strip() for a in abbr.split("/")]
        escaped_abbrs = [escape_regex(a) for a in abbrs]
        pattern = r"\b(" + "|".join(escaped_abbrs) + r")\b"
    else:
        # Handle special markers like <Name> before escaping
        abbr_clean = abbr.strip()
        if "<Name>" in abbr_clean:
            # Replace <Name> with regex pattern for proper noun
            abbr_clean = abbr_clean.replace("<Name>", "<<<NAME_PLACEHOLDER>>>")
            escaped = escape_regex(abbr_clean)
            escaped = escaped.replace("<<<NAME_PLACEHOLDER>>>", r"[A-Z][a-zA-Z]+")
        else:
            escaped = escape_regex(abbr_clean)
        pattern = r"\b" + escaped + r"\b"

    return pattern

def create_error_pattern(word, abbr, table_type):
    """Create common error pattern description."""
    errors = []

    if table_type == "T6":
        # Common word abbreviation errors
        if "'" in abbr:
            no_apos = abbr.replace("'", "")
            errors.append(f"Missing apostrophe (e.g., '{no_apos}' instead of '{abbr}')")
        if abbr.endswith("."):
            no_period = abbr[:-1]
            errors.append(f"Missing period (e.g., '{no_period}' instead of '{abbr}')")
        errors.append(f"Using full form '{word}' instead of abbreviated '{abbr}' in case names")
        if "/" in word:
            errors.append(f"Inconsistent abbreviation across variants: {word}")

    elif table_type == "T7":
        # Court name errors
        errors.append(f"Using full form '{word}' instead of '{abbr}'")
        if "Ct." not in abbr and "Court" in word:
            errors.append(f"Misspelling or incorrect abbreviation of 'Court'")
        if abbr.count(".") > 0:
            errors.append(f"Missing periods in abbreviation")

    elif table_type == "T8":
        # Explanatory phrase errors
        if "'" in abbr:
            no_apos = abbr.replace("'", "")
            errors.append(f"Missing apostrophe in contraction (e.g., '{no_apos}' instead of '{abbr}')")
        if word != abbr:
            errors.append(f"Using full phrase '{word}' in parenthetical instead of '{abbr}'")
        else:
            errors.append(f"No abbreviation needed - use as-is: '{abbr}'")

    return " | ".join(errors) if errors else "No common errors identified"

def create_gpt_prompt(word, abbr, table_type):
    """Create GPT validation prompt for this entry."""
    if table_type == "T6":
        prompt = f"""Verify that all instances of "{word}" in case names, institutional names, or periodical titles are properly abbreviated as "{abbr}".

Check for:
1. Unabbreviated forms of "{word}" that should be "{abbr}"
2. Incorrect abbreviations (missing apostrophes, periods, or wrong letters)
3. Inconsistent abbreviation within the same citation
4. Context: Only abbreviate in case names/titles, not in explanatory text

Return instances that violate Bluebook Table T6 rules."""

    elif table_type == "T7":
        prompt = f"""Verify that all instances of the court name "{word}" are properly abbreviated as "{abbr}".

Check for:
1. Full court name "{word}" used instead of abbreviation "{abbr}"
2. Incorrect abbreviation format (missing periods, wrong spacing)
3. Inconsistent court name abbreviations within the same document
4. Proper use of jurisdictional identifiers with court abbreviations

Return instances that violate Bluebook Table T7 court name abbreviation rules."""

    elif table_type == "T8":
        if word == abbr:
            prompt = f"""Verify that the explanatory phrase "{word}" is used correctly in parenthetical explanations.

Check for:
1. Proper placement in parenthetical (after case citation)
2. Correct capitalization and punctuation
3. Appropriate context for use of this phrase
4. No unnecessary abbreviation (this phrase should not be abbreviated)

Return instances that violate Bluebook Table T8 explanatory phrase rules."""
        else:
            prompt = f"""Verify that all instances of the explanatory phrase "{word}" are properly abbreviated as "{abbr}" in parenthetical explanations.

Check for:
1. Full phrase "{word}" used instead of abbreviation "{abbr}"
2. Incorrect abbreviation (missing apostrophes or wrong contraction)
3. Proper placement in parenthetical (after case citation)
4. Correct punctuation and spacing

Return instances that violate Bluebook Table T8 explanatory phrase abbreviation rules."""

    return prompt

def process_table(table_data, table_name):
    """Process a single table and return structured entries."""
    entries = []

    for section_name, section_data in table_data.items():
        for word, abbr in section_data.items():
            entry = {
                "word": word,
                "abbreviation": abbr,
                "regex_long": create_regex_long(word),
                "regex_short": create_regex_short(abbr),
                "error_pattern": create_error_pattern(word, abbr, table_name),
                "gpt_prompt": create_gpt_prompt(word, abbr, table_name),
                "section": section_name
            }
            entries.append(entry)

    return entries

def main():
    """Main processing function."""
    # Load Bluebook.json
    bluebook_path = Path("/home/user/slr/SLRinator/config/rules/Bluebook.json")
    with open(bluebook_path, 'r', encoding='utf-8') as f:
        bluebook_data = json.load(f)

    # Extract tables (note: lowercase 'tables' under 'bluebook' key)
    tables = bluebook_data.get("bluebook", {}).get("tables", {})
    t6_data = tables.get("T6", {})
    t7_data = tables.get("T7", {})
    t8_data = tables.get("T8", {})

    # Process each table
    print("Processing T6: Common Words in Case Names...")
    t6_entries = process_table(t6_data, "T6")
    print(f"  Processed {len(t6_entries)} entries")

    print("Processing T7: Court Names...")
    t7_entries = process_table(t7_data, "T7")
    print(f"  Processed {len(t7_entries)} entries")

    print("Processing T8: Explanatory Phrases...")
    t8_entries = process_table(t8_data, "T8")
    print(f"  Processed {len(t8_entries)} entries")

    # Create output structure
    output = {
        "metadata": {
            "description": "Comprehensive analysis of Bluebook Tables T6, T7, and T8",
            "total_entries": len(t6_entries) + len(t7_entries) + len(t8_entries),
            "tables": {
                "T6": {
                    "name": "Common Words in Case Names, Institutional Names, and Periodical Titles",
                    "entries": len(t6_entries)
                },
                "T7": {
                    "name": "Court Names",
                    "entries": len(t7_entries)
                },
                "T8": {
                    "name": "Explanatory Phrases",
                    "entries": len(t8_entries)
                }
            },
            "generated": "2025-11-23"
        },
        "T6": t6_entries,
        "T7": t7_entries,
        "T8": t8_entries
    }

    # Ensure output directory exists
    output_dir = Path("/home/user/slr/SLRinator/output/analysis")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write output
    output_path = output_dir / "tables_6-8_analysis.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nAnalysis complete!")
    print(f"Total entries processed: {output['metadata']['total_entries']}")
    print(f"Output written to: {output_path}")

    # Print summary statistics
    print("\n=== SUMMARY STATISTICS ===")
    print(f"T6 entries: {len(t6_entries)}")
    print(f"T7 entries: {len(t7_entries)}")
    print(f"T8 entries: {len(t8_entries)}")
    print(f"Total: {len(t6_entries) + len(t7_entries) + len(t8_entries)}")

    # Sample entries from each table
    print("\n=== SAMPLE ENTRIES ===")
    print("\nT6 Sample (Association):")
    sample_t6 = next((e for e in t6_entries if e["word"] == "Association"), None)
    if sample_t6:
        print(json.dumps(sample_t6, indent=2))

    print("\nT7 Sample (Supreme Court):")
    sample_t7 = next((e for e in t7_entries if "Supreme Court (federal)" in e["word"]), None)
    if sample_t7:
        print(json.dumps(sample_t7, indent=2))

    print("\nT8 Sample (certiorari denied):")
    sample_t8 = next((e for e in t8_entries if e["word"] == "certiorari denied"), None)
    if sample_t8:
        print(json.dumps(sample_t8, indent=2))

if __name__ == "__main__":
    main()
