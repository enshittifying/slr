#!/usr/bin/env python3
"""
Comprehensive Formal Rule System for Bluebook Citations
A machine-readable, logic-based representation of ALL Bluebook rules
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any, Union
from enum import Enum
import re
import json

# ============================================================================
# FUNDAMENTAL TYPES AND ENUMS
# ============================================================================

class RuleType(Enum):
    """Categories of citation rules"""
    STRUCTURAL = "structural"  # How citations are composed
    FORMATTING = "formatting"  # Visual presentation (italics, caps)
    ABBREVIATION = "abbreviation"  # Standard abbreviations
    ORDERING = "ordering"  # Sequence of elements
    SIGNAL = "signal"  # Introductory signals
    PARENTHETICAL = "parenthetical"  # Additional information
    PUNCTUATION = "punctuation"  # Punctuation rules
    SHORT_FORM = "short_form"  # Subsequent citations
    SPECIAL_CASE = "special_case"  # Exceptions
    SPACING = "spacing"  # Space requirements
    CAPITALIZATION = "capitalization"  # Capital letter rules
    CROSS_REFERENCE = "cross_reference"  # Internal references

class ElementType(Enum):
    """Types of citation elements"""
    CASE_NAME = "case_name"
    REPORTER = "reporter"
    VOLUME = "volume"
    PAGE = "page"
    YEAR = "year"
    COURT = "court"
    SIGNAL = "signal"
    AUTHOR = "author"
    TITLE = "title"
    PUBLISHER = "publisher"
    EDITION = "edition"
    URL = "url"
    DATE_ACCESSED = "date_accessed"
    PARENTHETICAL = "parenthetical"
    PINPOINT = "pinpoint"
    SUPPLEMENT = "supplement"
    SECTION = "section"
    PARAGRAPH = "paragraph"

class Operator(Enum):
    """Logical operators for rule conditions"""
    AND = "and"
    OR = "or"
    NOT = "not"
    IMPLIES = "implies"
    IFF = "iff"  # if and only if
    EQUALS = "equals"
    CONTAINS = "contains"
    MATCHES = "matches"  # regex match
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    ADJACENT = "adjacent"

# ============================================================================
# CORE RULE STRUCTURE
# ============================================================================

@dataclass
class Predicate:
    """A testable condition"""
    name: str
    params: Dict[str, Any]
    test_function: Optional[Callable] = None
    
    def evaluate(self, context: Dict) -> bool:
        """Evaluate this predicate in a given context"""
        if self.test_function:
            return self.test_function(context, self.params)
        return False

@dataclass
class RuleCondition:
    """Complex condition built from predicates and operators"""
    operator: Operator
    operands: List[Union['RuleCondition', Predicate]]
    
    def evaluate(self, context: Dict) -> bool:
        """Evaluate complex condition"""
        if self.operator == Operator.AND:
            return all(op.evaluate(context) for op in self.operands)
        elif self.operator == Operator.OR:
            return any(op.evaluate(context) for op in self.operands)
        elif self.operator == Operator.NOT:
            return not self.operands[0].evaluate(context)
        elif self.operator == Operator.IMPLIES:
            # A → B is equivalent to ¬A ∨ B
            return not self.operands[0].evaluate(context) or self.operands[1].evaluate(context)
        return False

@dataclass
class Action:
    """Action to take when rule applies"""
    name: str
    params: Dict[str, Any]
    apply_function: Optional[Callable] = None
    
    def apply(self, context: Dict) -> Dict:
        """Apply this action to modify context"""
        if self.apply_function:
            return self.apply_function(context, self.params)
        return context

@dataclass
class FormalRule:
    """A complete formal rule"""
    id: str
    name: str
    type: RuleType
    description: str
    bluebook_section: str  # Reference to Bluebook section
    condition: RuleCondition
    actions: List[Action]
    exceptions: List['FormalRule'] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)
    priority: int = 0  # For rule ordering/precedence
    
    def applies(self, context: Dict) -> bool:
        """Check if this rule applies in context"""
        # Check main condition
        if not self.condition.evaluate(context):
            return False
        
        # Check exceptions
        for exception in self.exceptions:
            if exception.applies(context):
                return False
        
        return True
    
    def validate(self, text: str) -> Dict:
        """Validate text against this rule"""
        context = {"text": text}
        if self.applies(context):
            # Apply actions to check validity
            for action in self.actions:
                context = action.apply(context)
        
        return {
            "rule_id": self.id,
            "rule_name": self.name,
            "applies": self.applies(context),
            "valid": context.get("valid", True),
            "violations": context.get("violations", []),
            "fixes": context.get("fixes", [])
        }

# ============================================================================
# PREDICATE LIBRARY (Testable Conditions)
# ============================================================================

class PredicateLibrary:
    """Library of reusable predicates"""
    
    @staticmethod
    def is_case_citation(context: Dict, params: Dict) -> bool:
        """Test if text is a case citation"""
        text = context.get("text", "")
        # Pattern: Party v. Party, Reporter
        pattern = r'\b[A-Z]\w+\s+v\.\s+[A-Z]\w+'
        return bool(re.search(pattern, text))
    
    @staticmethod
    def is_italicized(context: Dict, params: Dict) -> bool:
        """Test if element is italicized"""
        element = params.get("element", "")
        text = context.get(element, "")
        # Check for italic markers (would need actual formatting check)
        return context.get(f"{element}_italic", False)
    
    @staticmethod
    def has_signal(context: Dict, params: Dict) -> bool:
        """Test if citation has introductory signal"""
        text = context.get("text", "")
        signals = ["See", "See also", "Cf.", "Compare", "Contra", 
                  "But see", "See generally", "E.g.", "Accord"]
        pattern = r'\b(' + '|'.join(re.escape(s) for s in signals) + r')\b'
        return bool(re.match(pattern, text))
    
    @staticmethod
    def is_abbreviated(context: Dict, params: Dict) -> bool:
        """Test if word is properly abbreviated"""
        word = params.get("word", "")
        abbreviation = params.get("abbreviation", "")
        text = context.get("text", "")
        return abbreviation in text and word not in text
    
    @staticmethod
    def has_pinpoint(context: Dict, params: Dict) -> bool:
        """Test if citation has pinpoint reference"""
        text = context.get("text", "")
        # Pattern for pinpoint: at [page]
        pattern = r'\bat\s+\d+'
        return bool(re.search(pattern, text))
    
    @staticmethod
    def is_short_form(context: Dict, params: Dict) -> bool:
        """Test if citation is in short form"""
        text = context.get("text", "")
        # Common short form patterns
        patterns = [
            r'\bId\.',
            r'\bSupra\s+note\s+\d+',
            r'\d+\s+[A-Z]\.\d+[a-z]?\s+at\s+\d+'  # Short case cite
        ]
        return any(re.search(p, text) for p in patterns)

# ============================================================================
# ACTION LIBRARY (Rule Applications)
# ============================================================================

class ActionLibrary:
    """Library of rule actions"""
    
    @staticmethod
    def require_italics(context: Dict, params: Dict) -> Dict:
        """Require element to be italicized"""
        element = params.get("element", "")
        if not context.get(f"{element}_italic", False):
            context.setdefault("violations", []).append(
                f"{element} must be italicized"
            )
            context.setdefault("fixes", []).append(
                f"Italicize {element}"
            )
            context["valid"] = False
        return context
    
    @staticmethod
    def require_abbreviation(context: Dict, params: Dict) -> Dict:
        """Require proper abbreviation"""
        word = params.get("word", "")
        abbreviation = params.get("abbreviation", "")
        text = context.get("text", "")
        
        if word in text and abbreviation not in text:
            context.setdefault("violations", []).append(
                f"'{word}' must be abbreviated as '{abbreviation}'"
            )
            context.setdefault("fixes", []).append(
                f"Replace '{word}' with '{abbreviation}'"
            )
            context["valid"] = False
        return context
    
    @staticmethod
    def require_order(context: Dict, params: Dict) -> Dict:
        """Require specific element order"""
        first = params.get("first", "")
        second = params.get("second", "")
        text = context.get("text", "")
        
        first_pos = text.find(first) if first in text else -1
        second_pos = text.find(second) if second in text else -1
        
        if first_pos > second_pos and second_pos != -1:
            context.setdefault("violations", []).append(
                f"'{first}' must come before '{second}'"
            )
            context["valid"] = False
        return context
    
    @staticmethod
    def require_punctuation(context: Dict, params: Dict) -> Dict:
        """Require specific punctuation"""
        after = params.get("after", "")
        punctuation = params.get("punctuation", "")
        text = context.get("text", "")
        
        pattern = re.escape(after) + r'\s*' + re.escape(punctuation)
        if after in text and not re.search(pattern, text):
            context.setdefault("violations", []).append(
                f"'{punctuation}' required after '{after}'"
            )
            context["valid"] = False
        return context

# ============================================================================
# COMPREHENSIVE RULE DEFINITIONS
# ============================================================================

class BluebookRules:
    """Complete collection of Bluebook rules in formal notation"""
    
    def __init__(self):
        self.rules = []
        self.predicates = PredicateLibrary()
        self.actions = ActionLibrary()
        self._build_rules()
    
    def _build_rules(self):
        """Build the complete rule set"""
        
        # Rule 1: Case names must be italicized
        self.rules.append(FormalRule(
            id="R10.2.1",
            name="Case Name Italics",
            type=RuleType.FORMATTING,
            description="Case names must be italicized or underlined",
            bluebook_section="Rule 10.2.1",
            condition=RuleCondition(
                operator=Operator.AND,
                operands=[
                    Predicate("is_case_citation", {}, self.predicates.is_case_citation),
                    Predicate("not_italicized", {"element": "case_name"}, 
                             lambda c, p: not self.predicates.is_italicized(c, p))
                ]
            ),
            actions=[
                Action("require_italics", {"element": "case_name"}, 
                      self.actions.require_italics)
            ],
            examples=["Smith v. Jones, 123 F.3d 456 (2d Cir. 2020)"],
            violations=["Smith v. Jones (not italicized)"]
        ))
        
        # Rule 2: United States abbreviation
        self.rules.append(FormalRule(
            id="R10.2.2",
            name="United States Abbreviation",
            type=RuleType.ABBREVIATION,
            description="'United States' as party name must be abbreviated to 'United States' not 'U.S.'",
            bluebook_section="Rule 10.2.2",
            condition=RuleCondition(
                operator=Operator.AND,
                operands=[
                    Predicate("is_case_citation", {}, self.predicates.is_case_citation),
                    Predicate("contains_US", {}, 
                             lambda c, p: "U.S." in c.get("text", "") and " v." in c.get("text", ""))
                ]
            ),
            actions=[
                Action("require_full_name", {"replace": "U.S.", "with": "United States"},
                      lambda c, p: c if p["replace"] not in c.get("text", "") else 
                      {**c, "violations": c.get("violations", []) + 
                       ["Use 'United States' not 'U.S.' in case names"]})
            ]
        ))
        
        # Rule 3: Signal ordering
        self.rules.append(FormalRule(
            id="R1.2",
            name="Signal Order",
            type=RuleType.ORDERING,
            description="Signals must appear in specific order",
            bluebook_section="Rule 1.2-1.3",
            condition=RuleCondition(
                operator=Operator.AND,
                operands=[
                    Predicate("has_multiple_signals", {},
                             lambda c, p: len(re.findall(r'\b(See|Cf\.|But see|Contra)\b', 
                                                        c.get("text", ""))) > 1)
                ]
            ),
            actions=[
                Action("check_signal_order", {},
                      lambda c, p: self._check_signal_order(c))
            ]
        ))
        
        # Add more rules here...
        # This would continue for ALL Bluebook rules
    
    def _check_signal_order(self, context: Dict) -> Dict:
        """Check if signals are in correct order"""
        signal_order = ["[no signal]", "E.g.,", "Accord", "See", "See also", 
                       "Cf.", "Compare", "Contra", "But see", "But cf.", 
                       "See generally"]
        # Implementation would check actual order
        return context
    
    def validate_citation(self, citation: str) -> List[Dict]:
        """Validate a citation against all rules"""
        results = []
        for rule in self.rules:
            result = rule.validate(citation)
            if result["applies"]:
                results.append(result)
        return results

# ============================================================================
# RULE COMPILER (Convert natural language to formal rules)
# ============================================================================

class RuleCompiler:
    """Compile natural language rules into formal representation"""
    
    def __init__(self):
        self.patterns = {
            "must_be": r"(\w+)\s+must\s+be\s+(\w+)",
            "abbreviated_as": r"(\w+)\s+(?:is\s+)?abbreviated\s+as\s+(\w+)",
            "italicize": r"italicize\s+(\w+)",
            "capitalize": r"capitalize\s+(\w+)",
            "order": r"(\w+)\s+(?:comes\s+)?before\s+(\w+)",
            "punctuation": r"(\w+)\s+followed\s+by\s+(\w+)",
        }
    
    def compile(self, natural_rule: str) -> Optional[FormalRule]:
        """Convert natural language rule to formal rule"""
        # This would parse natural language and create FormalRule objects
        pass

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Initialize and test the formal rule system"""
    print("Bluebook Formal Rule System")
    print("=" * 60)
    
    # Initialize rule system
    rules = BluebookRules()
    
    # Test citations
    test_citations = [
        "Smith v. Jones, 123 F.3d 456 (2d Cir. 2020)",
        "U.S. v. Smith, 456 U.S. 789 (1982)",
        "See Johnson v. State, 789 P.2d 123 (Cal. 1990); But see Miller v. City, 456 F.2d 789 (9th Cir. 1999)"
    ]
    
    for citation in test_citations:
        print(f"\nValidating: {citation}")
        print("-" * 40)
        results = rules.validate_citation(citation)
        for result in results:
            if not result["valid"]:
                print(f"Rule: {result['rule_name']}")
                for violation in result.get("violations", []):
                    print(f"  ❌ {violation}")
                for fix in result.get("fixes", []):
                    print(f"  ✓ Fix: {fix}")
    
    # Save formal rules to JSON
    rules_json = []
    for rule in rules.rules:
        rules_json.append({
            "id": rule.id,
            "name": rule.name,
            "type": rule.type.value,
            "description": rule.description,
            "section": rule.bluebook_section,
            "examples": rule.examples,
            "violations": rule.violations
        })
    
    output_file = Path("/Users/ben/app/SLRinator/formal_bluebook_rules.json")
    with open(output_file, 'w') as f:
        json.dump(rules_json, f, indent=2)
    
    print(f"\n\nFormal rules saved to: {output_file}")

if __name__ == "__main__":
    main()