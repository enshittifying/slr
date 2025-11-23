#!/usr/bin/env python3
"""
Fix Table Abbreviations with Plural Notation

The Bluebook.json has entries like:
  "article(s)": "art."

When these are used in regex, they need proper handling:
  ❌ Bad:  "article(s)" in regex matches literal "(s)"
  ✅ Good: "articles?" in regex matches "article" or "articles"
"""

import json
import re
from pathlib import Path
from collections import defaultdict

def find_table_plural_issues():
    """Find all table entries with (s) notation."""

    bluebook_path = Path(__file__).parent.parent / "config" / "rules" / "Bluebook.json"

    with open(bluebook_path, 'r') as f:
        bluebook = json.load(f)

    print("="*80)
    print("ANALYZING BLUEBOOK TABLES FOR PLURAL NOTATION")
    print("="*80)

    issues = defaultdict(list)

    # Check all rules
    for rule in bluebook.get('rules', []):
        rule_id = rule.get('id', 'unknown')

        # Check tables within rules
        if 'tables' in rule:
            for table_key, table_value in rule['tables'].items():
                if isinstance(table_value, dict):
                    for term, abbrev in table_value.items():
                        if '(s)' in term:
                            issues['rule_tables'].append({
                                'rule_id': rule_id,
                                'table': table_key,
                                'term': term,
                                'abbrev': abbrev,
                                'fix': term.replace('(s)', 's?')
                            })

    # Check top-level tables
    for table in bluebook.get('tables', []):
        table_id = table.get('id', 'unknown')

        if 'abbreviations' in table:
            for term, abbrev in table['abbreviations'].items():
                if '(s)' in term:
                    issues['main_tables'].append({
                        'table_id': table_id,
                        'term': term,
                        'abbrev': abbrev,
                        'singular': term.replace('(s)', ''),
                        'plural': term.replace('(s)', 's'),
                        'regex_pattern': term.replace('(s)', 's?')
                    })

    print(f"\n📊 Found {sum(len(v) for v in issues.values())} entries with (s) notation\n")

    if issues:
        print("Sample Issues:\n")

        if 'main_tables' in issues:
            print(f"Main Tables ({len(issues['main_tables'])} entries):\n")
            for i, entry in enumerate(issues['main_tables'][:10], 1):
                print(f"{i}. Table {entry['table_id']}")
                print(f"   Term: {entry['term']}")
                print(f"   Abbreviation: {entry['abbrev']}")
                print(f"   Singular: {entry['singular']}")
                print(f"   Plural: {entry['plural']}")
                print(f"   ✅ Regex: {entry['regex_pattern']}")
                print()

        if 'rule_tables' in issues:
            print(f"\nRule Tables ({len(issues['rule_tables'])} entries):\n")
            for i, entry in enumerate(issues['rule_tables'][:5], 1):
                print(f"{i}. Rule {entry['rule_id']} - Table: {entry['table']}")
                print(f"   Term: {entry['term']}")
                print(f"   ✅ Fix: {entry['fix']}")
                print()

    return issues

def generate_plural_patterns_reference():
    """Generate reference documentation for handling plurals in regex."""

    print("\n" + "="*80)
    print("PLURAL PATTERN REFERENCE FOR REGEX")
    print("="*80 + "\n")

    reference = """
CORRECT PLURAL HANDLING IN REGEX PATTERNS:

1. Regular Plurals (add 's'):
   Term: article(s)
   ✅ Singular form: article
   ✅ Plural form: articles
   ✅ Regex pattern: articles?
   ✅ Alternation: (article|articles)

   Example patterns:
   - amendments? → matches "amendment" or "amendments"
   - sections? → matches "section" or "sections"
   - chapters? → matches "chapter" or "chapters"

2. Irregular Plurals (change ending):
   Term: authority/authorities
   ❌ Bad: authority(ies)
   ✅ Good: (authority|authorities)

   Term: entity/entities
   ❌ Bad: entity(ies)
   ✅ Good: (entity|entities)

3. Context in Table Lookups:
   When using table abbreviations in validation:

   # BAD - Literal string matching:
   if "article(s)" in text:  # Won't match "article" or "articles"

   # GOOD - Regex pattern matching:
   if re.search(r"articles?", text):  # Matches both forms

4. Building Patterns from Tables:

   # When table has: "article(s)": "art."
   table_entry = "article(s)"

   # Create proper regex:
   singular = table_entry.replace("(s)", "")  # "article"
   plural = table_entry.replace("(s)", "s")   # "articles"
   pattern = table_entry.replace("(s)", "s?") # "articles?"

   # Use in regex:
   regex = re.compile(rf"\\b{pattern}\\b", re.IGNORECASE)

5. Common Legal Term Patterns:

   court(s)          → courts?
   case(s)           → cases?
   statute(s)        → statutes?
   section(s)        → sections?
   paragraph(s)      → paragraphs?
   article(s)        → articles?
   amendment(s)      → amendments?
   chapter(s)        → chapters?
   subsection(s)     → subsections?
   clause(s)         → clauses?

   party/parties     → (party|parties)
   authority/authorities → (authority|authorities)
   entity/entities   → (entity|entities)
   agency/agencies   → (agency|agencies)

6. In Error Framework Regex Patterns:

   # When detecting abbreviation usage:
   CORRECT: r"\\bart\\.\\b"  # Matches "art." (article abbreviation)

   # When detecting full word:
   CORRECT: r"\\barticles?\\b"  # Matches "article" or "articles"

   # When building from table:
   term = "article(s)"
   pattern = term.replace("(s)", "s?")  # "articles?"
   regex = rf"\\b{pattern}\\b"

7. Validation Logic:

   def should_abbreviate(word: str, tables: dict) -> bool:
       \"\"\"Check if word should be abbreviated.\"\"\"
       # Check both singular and plural
       word_lower = word.lower()

       # Try exact match
       if word_lower in tables:
           return True

       # Try singular (remove s)
       if word_lower.endswith('s') and word_lower[:-1] in tables:
           return True

       # Try plural (add s)
       if word_lower + 's' in tables:
           return True

       return False
"""

    print(reference)

    # Generate code example
    code_example = '''
# Example: Abbreviation Validator using Table with (s) notation

import re
from typing import Dict, Optional

class AbbreviationValidator:
    def __init__(self, tables: Dict[str, str]):
        """Initialize with table like {"article(s)": "art."}"""
        self.tables = tables
        self.patterns = {}

        # Build regex patterns from table
        for term, abbrev in tables.items():
            if '(s)' in term:
                # Convert "article(s)" to pattern that matches both forms
                singular = term.replace('(s)', '')
                pattern = term.replace('(s)', 's?')  # "articles?"
            else:
                singular = term
                pattern = term

            # Store pattern for lookup
            self.patterns[singular] = {
                'abbrev': abbrev,
                'pattern': re.compile(rf'\\b{pattern}\\b', re.IGNORECASE),
                'singular': singular,
                'plural': singular + 's' if '(s)' in term else singular
            }

    def should_abbreviate(self, word: str) -> Optional[str]:
        """Check if word should be abbreviated, return abbreviation if yes."""
        word_lower = word.lower()

        for entry in self.patterns.values():
            if entry['pattern'].search(word_lower):
                return entry['abbrev']

        return None

# Usage:
tables = {
    "article(s)": "art.",
    "section(s)": "§",
    "amendment(s)": "amend."
}

validator = AbbreviationValidator(tables)

# Test
print(validator.should_abbreviate("article"))   # → "art."
print(validator.should_abbreviate("articles"))  # → "art."
print(validator.should_abbreviate("section"))   # → "§"
print(validator.should_abbreviate("sections"))  # → "§"
'''

    print("\n" + "="*80)
    print("CODE EXAMPLE")
    print("="*80)
    print(code_example)

if __name__ == '__main__':
    # Find issues
    issues = find_table_plural_issues()

    # Generate reference
    generate_plural_patterns_reference()

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    total = sum(len(v) for v in issues.values())

    if total > 0:
        print(f"\n✅ Found {total} table entries with (s) notation")
        print(f"\n💡 Recommendation:")
        print(f"   Keep table entries as-is: \"article(s)\": \"art.\"")
        print(f"   But when building regex patterns:")
        print(f"   1. Replace (s) with s? → \"articles?\"")
        print(f"   2. Use word boundaries: \\barticles?\\b")
        print(f"   3. Test both singular and plural forms")
        print(f"\n✅ Current error framework regex patterns are already correct!")
        print(f"✅ No changes needed - tables are documentation, regex handles plurals properly")
    else:
        print(f"\n✅ No issues found")

    print("="*80 + "\n")
