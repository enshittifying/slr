"""
Auto-fix Implementation Module

Generated implementations for common citation errors.
"""

import re
from typing import Dict, List, Tuple

class AutoFixer:
    """Automatically fix common citation errors."""

    def fix_citation_spacing(self, text: str) -> Tuple[str, List[str]]:
        """Fix spacing between sentence and footnote number.

        Error: BB-1-001
        Pattern: "sentence. 1" → "sentence.1"
        """
        fixes = []

        # Pattern: letter/period + space(s) + digit
        def replacer(match):
            fixes.append(f"Removed space before footnote {match.group(2)}")
            return match.group(1) + '.' + match.group(2)

        fixed = re.sub(r'([a-zA-Z])\.\s+(\d+)', replacer, text)
        return fixed, fixes

    def fix_double_spacing(self, text: str) -> Tuple[str, List[str]]:
        """Fix double spaces.

        Error: Multiple spacing errors
        Pattern: "word  word" → "word word"
        """
        fixes = []
        original_count = text.count('  ')

        if original_count > 0:
            fixed = re.sub(r'\s{2,}', ' ', text)
            fixes.append(f"Fixed {original_count} double space(s)")
            return fixed, fixes

        return text, fixes

    def fix_italicization(self, text: str, terms: List[str]) -> Tuple[str, List[str]]:
        """Add italics markers to specific terms.

        Error: BB7 (various)
        Pattern: "amicus curiae" → "*amicus curiae*"
        """
        fixes = []
        fixed = text

        for term in terms:
            # Check if term is not already italicized
            if term in fixed and f'*{term}*' not in fixed:
                fixed = fixed.replace(term, f'*{term}*')
                fixes.append(f"Italicized '{term}'")

        return fixed, fixes

    def fix_case_name_italics(self, text: str) -> Tuple[str, List[str]]:
        """Italicize case names in format 'X v. Y'.

        Error: BB-2-001
        Pattern: "Smith v. Jones" → "*Smith v. Jones*"
        """
        fixes = []

        # Pattern: Case name (capitalized word v. capitalized word)
        pattern = r'\b([A-Z][a-z]+)\s+v\.\s+([A-Z][a-z]+)\b'

        def replacer(match):
            case_name = match.group(0)
            if f'*{case_name}*' not in text:  # Not already italicized
                fixes.append(f"Italicized case name: {case_name}")
                return f'*{case_name}*'
            return case_name

        fixed = re.sub(pattern, replacer, text)
        return fixed, fixes

    def add_see_generally_comment(self, text: str) -> Tuple[str, List[str]]:
        """Add [AA:] comment for see generally without parenthetical.

        Error: RB_1.12_E1
        Pattern: "See generally Smith..." → "See generally Smith... [AA: Add parenthetical]"
        """
        fixes = []

        # Pattern: "See generally" without following parenthetical
        pattern = r'(See generally\s+[^.]+\.\s*)(?!\()'

        def replacer(match):
            fixes.append("Added [AA:] comment for missing parenthetical")
            return match.group(1) + ' [AA: Add explanatory parenthetical required by RB 1.12] '

        fixed = re.sub(pattern, replacer, text)
        return fixed, fixes

    def fix_block_quote_indentation(self, text: str) -> Tuple[str, List[str]]:
        """Fix block quote indentation to 4 spaces.

        Error: BB5.1.004
        Pattern: Normalize indentation to 4 spaces
        """
        fixes = []
        lines = text.split('\n')
        fixed_lines = []

        for line in lines:
            # Check if line has wrong indentation (1-3 or 9+ spaces)
            if re.match(r'^\s{1,3}[^\s]', line):
                fixed_line = '    ' + line.lstrip()
                fixes.append(f"Fixed indentation: {len(line) - len(line.lstrip())} → 4 spaces")
                fixed_lines.append(fixed_line)
            elif re.match(r'^\s{9,}[^\s]', line):
                fixed_line = '    ' + line.lstrip()
                fixes.append(f"Fixed indentation: {len(line) - len(line.lstrip())} → 4 spaces")
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)

        return '\n'.join(fixed_lines), fixes

    def apply_all_fixes(self, text: str, context: Dict = None) -> Dict:
        """Apply all auto-fixes to text.

        Args:
            text: The citation or text to fix
            context: Optional context (e.g., {'is_citation': True, 'latin_terms': [...]})

        Returns:
            Dict with 'fixed_text', 'fixes_applied', 'confidence'
        """
        fixed = text
        all_fixes = []

        # Apply fixes in order
        fixed, fixes = self.fix_citation_spacing(fixed)
        all_fixes.extend(fixes)

        fixed, fixes = self.fix_double_spacing(fixed)
        all_fixes.extend(fixes)

        # Context-dependent fixes
        if context:
            if context.get('latin_terms'):
                fixed, fixes = self.fix_italicization(fixed, context['latin_terms'])
                all_fixes.extend(fixes)

            if not context.get('is_citation'):  # Only in text, not citations
                fixed, fixes = self.fix_case_name_italics(fixed)
                all_fixes.extend(fixes)

        fixed, fixes = self.add_see_generally_comment(fixed)
        all_fixes.extend(fixes)

        fixed, fixes = self.fix_block_quote_indentation(fixed)
        all_fixes.extend(fixes)

        return {
            'fixed_text': fixed,
            'fixes_applied': all_fixes,
            'confidence': 'high' if all_fixes else 'none',
            'num_fixes': len(all_fixes)
        }


# Common Latin terms that should be italicized
LATIN_TERMS = [
    'amicus curiae', 'certiorari', 'de facto', 'de novo', 'dicta',
    'en banc', 'ex parte', 'habeas corpus', 'in camera', 'in re',
    'inter alia', 'mandamus', 'per curiam', 'per se', 'prima facie',
    'pro bono', 'pro se', 'quid pro quo', 'res judicata', 'stare decisis',
    'sub nom', 'supra', 'ultra vires', 'voir dire'
]


# Usage example:
if __name__ == '__main__':
    fixer = AutoFixer()

    # Test citation spacing fix
    test_text = "This is a sentence. 1 Another sentence. 2"
    result = fixer.apply_all_fixes(test_text)

    print("Original:", test_text)
    print("Fixed:", result['fixed_text'])
    print("Fixes applied:", result['fixes_applied'])
    print("Confidence:", result['confidence'])
