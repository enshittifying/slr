#!/usr/bin/env python3
"""
Comprehensive Bluebook Rule Analyzer
Analyzes all extracted content to identify and categorize citation rules
"""

import json
import re
from pathlib import Path
from collections import defaultdict

class BluebookRuleAnalyzer:
    def __init__(self):
        self.rules_found = defaultdict(list)
        self.rule_patterns = {
            'formatting': [],
            'structure': [],
            'ordering': [],
            'abbreviation': [],
            'punctuation': [],
            'spacing': [],
            'capitalization': [],
            'signals': [],
            'parentheticals': [],
            'cross_references': [],
            'short_forms': [],
            'special_cases': []
        }
        
    def analyze_content(self, text, filename):
        """Extract rules from text content"""
        
        # Look for explicit rule statements
        rule_indicators = [
            r'must\s+be\s+(\w+)',
            r'should\s+be\s+(\w+)',
            r'always\s+(\w+)',
            r'never\s+(\w+)',
            r'use\s+(\w+)\s+when',
            r'cite\s+as\s+follows',
            r'format\s+as',
            r'abbreviated\s+as',
            r'italicize\s+(\w+)',
            r'capitalize\s+(\w+)',
            r'lowercase\s+(\w+)',
            r'separate\s+with\s+(\w+)',
            r'precede\s+with\s+(\w+)',
            r'follow\s+with\s+(\w+)',
            r'omit\s+(\w+)',
            r'include\s+(\w+)',
            r'place\s+(\w+)\s+in',
            r'when\s+citing\s+(\w+)',
            r'citation\s+must\s+include',
            r'required\s+elements',
            r'optional\s+elements'
        ]
        
        # Extract rules based on patterns
        for pattern in rule_indicators:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                context_start = max(0, match.start() - 100)
                context_end = min(len(text), match.end() + 100)
                context = text[context_start:context_end].strip()
                
                self.rules_found[filename].append({
                    'pattern': pattern,
                    'match': match.group(),
                    'context': context
                })
        
        # Look for structural patterns (e.g., numbered rules)
        numbered_rules = re.finditer(r'(?:^|\n)\s*(?:\()?([a-z]|\d+)\)\s*([A-Z][^.]*\.)', text)
        for match in numbered_rules:
            self.rules_found[filename].append({
                'type': 'numbered_rule',
                'number': match.group(1),
                'text': match.group(2).strip()
            })
        
        # Extract examples (crucial for understanding rules)
        examples = re.finditer(r'(?:e\.g\.|for example|example:)\s*([^.]+(?:\.[^.]+)*?)(?=\n|$)', text, re.IGNORECASE)
        for match in examples:
            self.rules_found[filename].append({
                'type': 'example',
                'text': match.group(1).strip()
            })
        
        # Find signal words and their usage
        signals = ['See', 'See also', 'Cf.', 'Compare', 'Contra', 'But see', 'See generally', 'E.g.', 'Accord']
        for signal in signals:
            if signal.lower() in text.lower():
                # Find context around signal
                pattern = rf'\b{re.escape(signal)}\b[^.]*\.'
                signal_matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in signal_matches:
                    self.rules_found[filename].append({
                        'type': 'signal_usage',
                        'signal': signal,
                        'context': match.group()
                    })
        
        return self.rules_found[filename]
    
    def categorize_rules(self):
        """Categorize found rules into logical groups"""
        categories = defaultdict(list)
        
        for filename, rules in self.rules_found.items():
            for rule in rules:
                # Categorization logic
                if 'italicize' in str(rule).lower():
                    categories['formatting'].append(rule)
                elif 'abbreviat' in str(rule).lower():
                    categories['abbreviation'].append(rule)
                elif 'capital' in str(rule).lower():
                    categories['capitalization'].append(rule)
                elif 'signal' in str(rule).lower():
                    categories['signals'].append(rule)
                elif 'parenthetical' in str(rule).lower():
                    categories['parentheticals'].append(rule)
                elif any(word in str(rule).lower() for word in ['order', 'precede', 'follow']):
                    categories['ordering'].append(rule)
                elif any(word in str(rule).lower() for word in ['comma', 'period', 'semicolon', 'colon']):
                    categories['punctuation'].append(rule)
                else:
                    categories['general'].append(rule)
        
        return categories

def main():
    base_dir = Path("/Users/ben/app/SLRinator/captures_extracts")
    analyzer = BluebookRuleAnalyzer()
    
    # Analyze all text files
    text_files = list(base_dir.glob("*.txt"))
    total_rules = 0
    
    print("Analyzing Bluebook Rules")
    print("=" * 60)
    
    for txt_file in text_files[:50]:  # Start with first 50 files
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        rules = analyzer.analyze_content(content, txt_file.stem)
        if rules:
            total_rules += len(rules)
            print(f"Found {len(rules)} rules in {txt_file.stem}")
    
    # Categorize rules
    categories = analyzer.categorize_rules()
    
    # Print summary
    print("\n" + "=" * 60)
    print("RULE CATEGORIES SUMMARY")
    print("=" * 60)
    for category, rules in categories.items():
        print(f"{category}: {len(rules)} rules")
    
    # Save comprehensive analysis
    output = {
        'total_rules_found': total_rules,
        'categories': {k: len(v) for k, v in categories.items()},
        'all_rules': analyzer.rules_found,
        'categorized_rules': {k: v for k, v in categories.items()}
    }
    
    output_file = base_dir.parent / "bluebook_rules_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\nAnalysis saved to: {output_file}")
    
    # Identify key rule types for formal system
    print("\n" + "=" * 60)
    print("KEY RULE TYPES IDENTIFIED")
    print("=" * 60)
    print("1. Structural Rules (how citations are composed)")
    print("2. Formatting Rules (italics, capitalization, etc.)")
    print("3. Abbreviation Rules (standard abbreviations)")
    print("4. Ordering Rules (sequence of elements)")
    print("5. Signal Rules (introductory signals)")
    print("6. Parenthetical Rules (additional information)")
    print("7. Punctuation Rules (commas, periods, etc.)")
    print("8. Short Form Rules (subsequent citations)")
    print("9. Special Case Rules (exceptions and specific scenarios)")
    
    return analyzer

if __name__ == "__main__":
    analyzer = main()