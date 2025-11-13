#!/usr/bin/env python3
"""
Comprehensive Bluebook Rule Extractor
Extracts ALL rules from Bluebook content and converts to formal notation
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import yaml

class ComprehensiveRuleExtractor:
    def __init__(self):
        self.all_rules = []
        self.rule_patterns = self._define_extraction_patterns()
        self.element_patterns = self._define_element_patterns()
        
    def _define_extraction_patterns(self) -> Dict:
        """Define patterns for extracting different types of rules"""
        return {
            # Mandatory rules
            'must': r'(?:must|shall|should|always)\s+([^.]+?)(?:\.|;|:|$)',
            'must_be': r'(\w+(?:\s+\w+)*?)\s+(?:must|shall)\s+be\s+([^.]+?)(?:\.|;|:|$)',
            'must_include': r'(?:must|shall)\s+include\s+([^.]+?)(?:\.|;|:|$)',
            
            # Prohibitions
            'never': r'(?:never|cannot|may not|must not|do not)\s+([^.]+?)(?:\.|;|:|$)',
            'omit': r'(?:omit|exclude|drop)\s+([^.]+?)(?:\.|;|:|$)',
            
            # Formatting rules
            'italicize': r'(?:italicize|italicized|italic)\s+([^.]+?)(?:\.|;|:|$)',
            'capitalize': r'(?:capitalize|capitalized|capital)\s+([^.]+?)(?:\.|;|:|$)',
            'lowercase': r'(?:lowercase|lower case)\s+([^.]+?)(?:\.|;|:|$)',
            'quotes': r'(?:quote|quotation marks?|enclosed in)\s+([^.]+?)(?:\.|;|:|$)',
            
            # Abbreviation rules
            'abbreviate': r'(?:abbreviate|abbreviated as|abbr\.?)\s+"?([^"]+?)"?\s+(?:as|to)\s+"?([^"]+?)"?',
            'abbr_table': r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+[=→]\s+([A-Z][a-z]*\.?(?:\s+[A-Z][a-z]*\.?)*)',
            
            # Ordering rules
            'precede': r'([^,]+?)\s+(?:precedes?|comes? before|appears? before)\s+([^.]+?)(?:\.|;|:|$)',
            'follow': r'([^,]+?)\s+(?:follows?|comes? after|appears? after)\s+([^.]+?)(?:\.|;|:|$)',
            'order_list': r'(?:in the following order|ordered as follows?):\s*([^.]+?)(?:\.|;|$)',
            
            # Punctuation rules
            'comma': r'(?:comma|,)\s+(?:after|before|between)\s+([^.]+?)(?:\.|;|:|$)',
            'period': r'(?:period|\.)\s+(?:after|before)\s+([^.]+?)(?:\.|;|:|$)',
            'semicolon': r'(?:semicolon|;)\s+(?:after|before|between)\s+([^.]+?)(?:\.|;|:|$)',
            'colon': r'(?:colon|:)\s+(?:after|before)\s+([^.]+?)(?:\.|;|:|$)',
            'parentheses': r'(?:parentheses|parenthetical|in parens?)\s+([^.]+?)(?:\.|;|:|$)',
            
            # Spacing rules
            'space': r'(?:space|spacing)\s+(?:between|after|before)\s+([^.]+?)(?:\.|;|:|$)',
            'no_space': r'no\s+space\s+(?:between|after|before)\s+([^.]+?)(?:\.|;|:|$)',
            
            # Conditional rules
            'when': r'(?:when|if|where)\s+([^,]+?),\s+([^.]+?)(?:\.|;|:|$)',
            'unless': r'unless\s+([^,]+?),\s+([^.]+?)(?:\.|;|:|$)',
            'except': r'except\s+(?:when|if|for)\s+([^.]+?)(?:\.|;|:|$)',
            
            # Signal rules
            'signal': r'(?:signal|introductory signal)\s+"?([^"]+?)"?\s+(?:indicates?|means?|used?)\s+([^.]+?)(?:\.|;|:|$)',
            
            # Examples
            'example': r'(?:e\.g\.|for example|example:|such as)\s*([^.]+?)(?:\.|;|$)',
            
            # Structure patterns
            'citation_format': r'(?:cite as|citation format|formatted as):\s*([^.]+?)(?:\.|;|$)',
            'components': r'(?:consists? of|includes?|contains?)\s+([^.]+?)(?:\.|;|:|$)',
        }
    
    def _define_element_patterns(self) -> Dict:
        """Define patterns for citation elements"""
        return {
            'case_name': r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            'reporter': r'\d+\s+([A-Z][a-z]*\.?\s*\d*[a-z]*)',
            'page': r'(?:at\s+)?(\d+(?:-\d+)?)',
            'year': r'\((\d{4})\)',
            'court': r'\(([A-Z][a-z]*\.?\s*(?:Cir\.|Dist\.|App\.|Sup\.|Ct\.)?)\s*\d{4}\)',
            'volume': r'^(\d+)\s+',
            'section_symbol': r'§§?\s*(\d+(?:\.\d+)?)',
            'url': r'https?://[^\s]+',
            'id_cite': r'\bId\.\s*(?:at\s+\d+)?',
            'supra_cite': r'\bsupra\s+note\s+\d+',
            'infra_cite': r'\binfra\s+note\s+\d+',
        }
    
    def extract_rules_from_text(self, text: str, filename: str) -> List[Dict]:
        """Extract all rules from a text"""
        rules = []
        
        # Clean text
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        
        # Extract rules by pattern type
        for rule_type, pattern in self.rule_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                rule = {
                    'source_file': filename,
                    'rule_type': rule_type,
                    'raw_text': match.group(0),
                    'components': match.groups(),
                    'context_start': max(0, match.start() - 100),
                    'context_end': min(len(text), match.end() + 100),
                    'context': text[max(0, match.start() - 100):min(len(text), match.end() + 100)]
                }
                
                # Convert to formal rule
                formal_rule = self._convert_to_formal_rule(rule)
                if formal_rule:
                    rules.append(formal_rule)
        
        return rules
    
    def _convert_to_formal_rule(self, raw_rule: Dict) -> Optional[Dict]:
        """Convert extracted rule to formal notation"""
        rule_type = raw_rule['rule_type']
        components = raw_rule['components']
        
        formal_rule = {
            'id': f"{raw_rule['source_file']}_{len(self.all_rules)}",
            'source': raw_rule['source_file'],
            'raw_text': raw_rule['raw_text'],
            'type': rule_type,
        }
        
        # Convert based on rule type
        if rule_type == 'must_be':
            formal_rule['subject'] = components[0] if components else None
            formal_rule['requirement'] = components[1] if len(components) > 1 else None
            formal_rule['predicate'] = f"is({components[1]})" if len(components) > 1 else None
            formal_rule['action'] = f"require_{components[1]}" if len(components) > 1 else None
            
        elif rule_type == 'italicize':
            formal_rule['subject'] = components[0] if components else None
            formal_rule['predicate'] = f"is_italicized({components[0]})" if components else None
            formal_rule['action'] = f"apply_italics({components[0]})" if components else None
            
        elif rule_type == 'abbreviate':
            if len(components) >= 2:
                formal_rule['full_form'] = components[0]
                formal_rule['abbreviated_form'] = components[1]
                formal_rule['predicate'] = f"contains('{components[0]}')"
                formal_rule['action'] = f"replace('{components[0]}', '{components[1]}')"
                
        elif rule_type == 'precede' or rule_type == 'follow':
            if len(components) >= 2:
                formal_rule['first_element'] = components[0] if rule_type == 'precede' else components[1]
                formal_rule['second_element'] = components[1] if rule_type == 'precede' else components[0]
                formal_rule['predicate'] = f"order({components[0]}, {components[1]})"
                formal_rule['action'] = f"enforce_order('{formal_rule['first_element']}', '{formal_rule['second_element']}')"
                
        elif rule_type == 'when':
            if len(components) >= 2:
                formal_rule['condition'] = components[0]
                formal_rule['consequence'] = components[1]
                formal_rule['predicate'] = f"if({components[0]}) then({components[1]})"
                formal_rule['action'] = f"apply_conditional_rule"
                
        elif rule_type == 'signal':
            if components:
                formal_rule['signal_name'] = components[0] if components else None
                formal_rule['signal_meaning'] = components[1] if len(components) > 1 else None
                formal_rule['predicate'] = f"has_signal('{components[0]}')" if components else None
                
        # Add regex pattern for validation
        formal_rule['validation_regex'] = self._generate_validation_regex(formal_rule)
        
        return formal_rule
    
    def _generate_validation_regex(self, rule: Dict) -> Optional[str]:
        """Generate regex pattern for rule validation"""
        if rule['type'] == 'abbreviate' and 'abbreviated_form' in rule:
            return rf"\b{re.escape(rule['abbreviated_form'])}\b"
        elif rule['type'] == 'italicize' and 'subject' in rule:
            # This would need actual formatting detection
            return rf"<i>{re.escape(rule['subject'])}</i>|_{re.escape(rule['subject'])}_"
        elif rule['type'] in ['precede', 'follow'] and 'first_element' in rule and 'second_element' in rule:
            return rf"{re.escape(rule['first_element'])}.*{re.escape(rule['second_element'])}"
        return None
    
    def extract_from_all_files(self, directory: Path) -> Dict:
        """Extract rules from all text files in directory"""
        all_extracted_rules = {
            'total_rules': 0,
            'by_type': {},
            'by_source': {},
            'rules': []
        }
        
        text_files = list(directory.glob("*.txt"))
        print(f"Processing {len(text_files)} files...")
        
        for txt_file in text_files:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            rules = self.extract_rules_from_text(content, txt_file.stem)
            
            if rules:
                all_extracted_rules['rules'].extend(rules)
                all_extracted_rules['by_source'][txt_file.stem] = len(rules)
                
                for rule in rules:
                    rule_type = rule.get('type', 'unknown')
                    all_extracted_rules['by_type'][rule_type] = \
                        all_extracted_rules['by_type'].get(rule_type, 0) + 1
        
        all_extracted_rules['total_rules'] = len(all_extracted_rules['rules'])
        
        return all_extracted_rules

def main():
    print("Comprehensive Bluebook Rule Extraction")
    print("=" * 60)
    
    extractor = ComprehensiveRuleExtractor()
    extracts_dir = Path("/Users/ben/app/SLRinator/captures_extracts")
    
    # Extract all rules
    print("Extracting rules from all files...")
    results = extractor.extract_from_all_files(extracts_dir)
    
    # Print summary
    print(f"\nTotal rules extracted: {results['total_rules']}")
    print("\nRules by type:")
    for rule_type, count in sorted(results['by_type'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {rule_type}: {count}")
    
    print("\nTop sources:")
    for source, count in sorted(results['by_source'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {source}: {count} rules")
    
    # Save comprehensive rule database
    output_file = Path("/Users/ben/app/SLRinator/comprehensive_bluebook_rules.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nComprehensive rule database saved to: {output_file}")
    
    # Also save in YAML for better readability
    yaml_file = Path("/Users/ben/app/SLRinator/comprehensive_bluebook_rules.yaml")
    with open(yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(results, f, default_flow_style=False)
    
    print(f"YAML version saved to: {yaml_file}")
    
    # Generate validation functions
    print("\nGenerating validation functions...")
    validation_file = Path("/Users/ben/app/SLRinator/bluebook_validators.py")
    generate_validators(results['rules'], validation_file)
    print(f"Validators saved to: {validation_file}")

def generate_validators(rules: List[Dict], output_file: Path):
    """Generate Python validation functions from rules"""
    validator_code = '''#!/usr/bin/env python3
"""
Auto-generated Bluebook Citation Validators
Generated from comprehensive rule extraction
"""

import re
from typing import Dict, List, Tuple

class BluebookValidator:
    def __init__(self):
        self.rules = self._load_rules()
    
    def _load_rules(self) -> List[Dict]:
        """Load validation rules"""
        return [
'''
    
    # Add rule definitions
    for i, rule in enumerate(rules[:100]):  # First 100 rules
        if rule.get('validation_regex'):
            validator_code += f'''            {{
                'id': '{rule.get('id', i)}',
                'type': '{rule.get('type', 'unknown')}',
                'pattern': r'{rule.get('validation_regex', '')}',
                'message': '{rule.get('raw_text', '').replace("'", "\\'")}',
            }},
'''
    
    validator_code += '''        ]
    
    def validate(self, text: str) -> List[Dict]:
        """Validate text against all rules"""
        violations = []
        for rule in self.rules:
            if rule.get('pattern'):
                if not re.search(rule['pattern'], text):
                    violations.append({
                        'rule_id': rule['id'],
                        'type': rule['type'],
                        'message': rule['message']
                    })
        return violations
'''
    
    with open(output_file, 'w') as f:
        f.write(validator_code)

if __name__ == "__main__":
    main()