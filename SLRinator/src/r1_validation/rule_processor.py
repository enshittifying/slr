"""
Comprehensive Rule Processor for Bluebook and Redbook Rules
Generates regex patterns, GPT queries, and multiple detection methods for each rule
"""
import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class RuleDetectionMethods:
    """Complete detection methods for a single rule."""
    rule_id: str
    rule_title: str
    rule_text: str
    source: str  # "bluebook" or "redbook"

    # Detection methods
    regex_patterns: List[Dict[str, str]]  # List of {pattern, description, example}
    gpt_query: str  # Primary GPT-4o query
    gpt_fallback_query: str  # Fallback GPT-4o-mini query
    deterministic_checks: List[Dict[str, Any]]  # Deterministic validation functions

    # Metadata
    keywords: List[str]  # Keywords for rule retrieval
    citation_types: List[str]  # Applicable citation types
    handbook_references: List[str]  # Member handbook references
    complexity: str  # "simple", "moderate", "complex"
    examples: List[Dict[str, str]]  # {correct, incorrect, explanation}

    # Cross-references
    related_rules: List[str]  # Related rule IDs
    supersedes: List[str]  # Rules this overrides (for Redbook)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class RuleProcessor:
    """
    Processes Bluebook and Redbook rules to generate comprehensive detection methods.
    """

    def __init__(self, bluebook_path: Path = None):
        """
        Initialize rule processor.

        Args:
            bluebook_path: Path to Bluebook.json
        """
        self.bluebook_path = bluebook_path or Path.cwd() / "config" / "rules" / "Bluebook.json"
        self.rules_data = self._load_rules()
        self.processed_rules: List[RuleDetectionMethods] = []

    def _load_rules(self) -> Dict:
        """Load rules from Bluebook.json."""
        with open(self.bluebook_path) as f:
            return json.load(f)

    def _flatten_rule_hierarchy(self, rules: List[Dict], source: str, parent_id: str = "") -> List[Dict]:
        """
        Flatten hierarchical rule structure.

        Args:
            rules: List of rule dicts
            source: "bluebook" or "redbook"
            parent_id: Parent rule ID

        Returns:
            Flattened list of rules
        """
        flattened = []

        for rule in rules:
            rule_id = parent_id + rule.get("id", "")

            # Add current rule if it has text
            if rule.get("text"):
                flattened.append({
                    "id": rule_id,
                    "title": rule.get("title", ""),
                    "text": rule["text"],
                    "source": source
                })

            # Recursively process children
            if rule.get("children"):
                flattened.extend(
                    self._flatten_rule_hierarchy(
                        rule["children"],
                        source,
                        rule_id + "."
                    )
                )

        return flattened

    def get_all_rules(self) -> List[Dict]:
        """Get all rules from both Bluebook and Redbook."""
        all_rules = []

        # Bluebook rules
        if "bluebook" in self.rules_data and "rules" in self.rules_data["bluebook"]:
            bluebook_rules = self._flatten_rule_hierarchy(
                self.rules_data["bluebook"]["rules"],
                "bluebook"
            )
            all_rules.extend(bluebook_rules)

        # Redbook rules
        if "redbook" in self.rules_data and "rules" in self.rules_data["redbook"]:
            redbook_rules = self._flatten_rule_hierarchy(
                self.rules_data["redbook"]["rules"],
                "redbook"
            )
            all_rules.extend(redbook_rules)

        logger.info(f"Loaded {len(all_rules)} total rules")
        return all_rules

    def _generate_regex_patterns(self, rule_text: str, rule_id: str) -> List[Dict[str, str]]:
        """
        Generate regex patterns for rule detection.

        Args:
            rule_text: Rule text
            rule_id: Rule ID

        Returns:
            List of regex pattern dicts
        """
        patterns = []

        # Pattern 1: Curly quotes (Redbook 24.4)
        if "curly" in rule_text.lower() or "smart quote" in rule_text.lower():
            patterns.append({
                "pattern": r'"[^"]*"',
                "description": "Detect straight double quotes (should be curly)",
                "example": '"text"',
                "correct_example": '"text"'
            })
            patterns.append({
                "pattern": r"'[^']*'",
                "description": "Detect straight single quotes (should be curly)",
                "example": "'text'",
                "correct_example": "'text'"
            })

        # Pattern 2: Non-breaking spaces (Redbook 24.8)
        if "non-breaking space" in rule_text.lower() or "nbsp" in rule_text.lower():
            patterns.append({
                "pattern": r'(\d+)\s+(U\.S\.|F\.\d+d|S\.\s*Ct\.)',
                "description": "Detect regular space before reporter (should be nbsp)",
                "example": "573 U.S. 208",
                "correct_example": "573 U.S. 208"  # Would use \u00A0
            })

        # Pattern 3: Parenthetical capitalization (Bluebook 10.2.1)
        if "parenthetical" in rule_text.lower() and "capitaliz" in rule_text.lower():
            patterns.append({
                "pattern": r'\([a-z][^)]*\)',
                "description": "Detect lowercase start in parenthetical",
                "example": "(holding that...)",
                "correct_example": "(holding that...)"  # Actually correct per Bluebook
            })

        # Pattern 4: Id. formatting
        if rule_id.startswith("4") or "id." in rule_text.lower():
            patterns.append({
                "pattern": r'\bId\b',
                "description": "Detect 'Id' without period",
                "example": "Id at 123",
                "correct_example": "Id. at 123"
            })
            patterns.append({
                "pattern": r'\bid\.',
                "description": "Detect lowercase 'id.'",
                "example": "id. at 123",
                "correct_example": "Id. at 123"
            })

        # Pattern 5: Case name italicization (Bluebook 10.2)
        if "italicize" in rule_text.lower() and ("case" in rule_text.lower() or "party" in rule_text.lower()):
            patterns.append({
                "pattern": r'\b[A-Z][a-z]+\s+v\.\s+[A-Z][a-z]+\b',
                "description": "Detect case name (check if italicized)",
                "example": "Smith v. Jones",
                "correct_example": "Smith v. Jones"  # Should be italicized
            })

        # Pattern 6: "at" in pinpoint citations
        if "pinpoint" in rule_text.lower() or rule_id.startswith("3"):
            patterns.append({
                "pattern": r',\s*(\d+)',
                "description": "Detect missing 'at' before page number",
                "example": "123 U.S. 456, 789",
                "correct_example": "123 U.S. 456, 789"  # May or may not need 'at' depending on context
            })

        # Pattern 7: Comma before year in case citations
        if rule_id.startswith("10") and "case" in rule_text.lower():
            patterns.append({
                "pattern": r'\)\s*\(\d{4}\)',
                "description": "Detect missing comma before year",
                "example": ") (2014)",
                "correct_example": ", (2014)"
            })

        # Pattern 8: Periods in abbreviations
        if "abbreviat" in rule_text.lower():
            patterns.append({
                "pattern": r'\b(Inc|Ltd|Co|Corp)\b(?!\.)',
                "description": "Detect abbreviation without period",
                "example": "Corp",
                "correct_example": "Corp."
            })

        # Pattern 9: Ellipsis formatting (Redbook 5.3)
        if "ellipsis" in rule_text.lower() or "ellipses" in rule_text.lower():
            patterns.append({
                "pattern": r'\.\.\.',
                "description": "Detect three periods without spaces (should be spaced)",
                "example": "text...more",
                "correct_example": "text . . . more"
            })

        # Pattern 10: Supra formatting (Bluebook 4.2)
        if "supra" in rule_text.lower():
            patterns.append({
                "pattern": r'\bSupra\b',
                "description": "Detect capitalized 'Supra' (should be lowercase in most contexts)",
                "example": "See Supra note 5",
                "correct_example": "See supra note 5"
            })

        return patterns

    def _generate_gpt_query(self, rule: Dict) -> str:
        """
        Generate GPT-4o query for rule validation.

        Args:
            rule: Rule dict

        Returns:
            GPT prompt
        """
        rule_id = rule["id"]
        rule_title = rule["title"]
        rule_text = rule["text"]
        source = rule["source"]

        prompt = f"""You are a legal citation expert specializing in {source.upper()} citation rules.

Rule ID: {rule_id}
Rule Title: {rule_title}
Rule Text: {rule_text}

Task: Validate if the given citation complies with this specific rule.

Instructions:
1. Analyze the citation text carefully
2. Check for compliance with the rule above
3. If there are errors, provide:
   - Error type
   - Description of the error
   - The current (incorrect) form
   - The correct form
   - Confidence level (0.0-1.0)
4. Return JSON with:
   {{
     "is_correct": boolean,
     "errors": [
       {{
         "error_type": "string",
         "description": "string",
         "rule_id": "{rule_id}",
         "current": "string",
         "correct": "string",
         "confidence": float
       }}
     ],
     "rule_applied": "{rule_id}"
   }}

Citation to validate: {{citation_text}}

Respond with only the JSON object, no additional text."""

        return prompt

    def _generate_fallback_query(self, rule: Dict) -> str:
        """Generate simplified GPT-4o-mini fallback query."""
        rule_id = rule["id"]
        rule_text = rule["text"]

        prompt = f"""Check if this citation follows rule {rule_id}: {rule_text[:200]}...

Citation: {{citation_text}}

Return JSON: {{"is_correct": true/false, "error_description": "string if error"}}"""

        return prompt

    def _extract_keywords(self, rule_text: str, rule_title: str) -> List[str]:
        """Extract keywords for rule retrieval."""
        # Combine title and text
        combined = f"{rule_title} {rule_text}".lower()

        # Common legal citation keywords
        keywords = []

        keyword_patterns = {
            "id.": ["id.", "short citation", "subsequent"],
            "supra": ["supra"],
            "case": ["case", "court", "decision", "holding"],
            "statute": ["statute", "code", "act"],
            "article": ["article", "journal", "law review"],
            "book": ["book", "treatise"],
            "italics": ["italic", "italicize"],
            "abbreviation": ["abbreviat", "abbrev"],
            "parenthetical": ["parenthetical"],
            "quote": ["quote", "quotation"],
            "signal": ["signal", "see", "cf.", "e.g."],
            "page": ["page", "pinpoint", "at"],
            "comma": ["comma"],
            "period": ["period"],
            "citation": ["citation", "cite"]
        }

        for keyword, patterns in keyword_patterns.items():
            if any(p in combined for p in patterns):
                keywords.append(keyword)

        # Add any capitalized words from title (likely important terms)
        title_words = re.findall(r'\b[A-Z][a-z]+\b', rule_title)
        keywords.extend([w.lower() for w in title_words if len(w) > 3])

        return list(set(keywords))

    def _determine_complexity(self, rule_text: str) -> str:
        """Determine rule complexity based on text analysis."""
        # Simple heuristics
        word_count = len(rule_text.split())
        has_examples = "e.g.," in rule_text.lower() or "example" in rule_text.lower()
        has_exceptions = "however" in rule_text.lower() or "except" in rule_text.lower()

        if word_count < 50 and not has_exceptions:
            return "simple"
        elif word_count < 150 and not has_examples:
            return "moderate"
        else:
            return "complex"

    def _identify_citation_types(self, rule_text: str, rule_id: str) -> List[str]:
        """Identify applicable citation types for this rule."""
        types = []

        type_keywords = {
            "case": ["case", "court", "decision"],
            "statute": ["statute", "code", "u.s.c."],
            "article": ["article", "journal", "law review"],
            "book": ["book", "treatise"],
            "constitution": ["constitution"],
            "regulation": ["regulation", "c.f.r."],
            "internet": ["internet", "website", "url"]
        }

        for cit_type, keywords in type_keywords.items():
            if any(kw in rule_text.lower() for kw in keywords):
                types.append(cit_type)

        # Rule-based type identification
        if rule_id.startswith("10"):
            types.append("case")
        elif rule_id.startswith("12"):
            types.append("statute")
        elif rule_id.startswith("16"):
            types.append("article")

        return list(set(types)) if types else ["general"]

    def process_rule(self, rule: Dict) -> RuleDetectionMethods:
        """
        Process a single rule to generate all detection methods.

        Args:
            rule: Rule dict

        Returns:
            RuleDetectionMethods
        """
        rule_id = rule["id"]
        rule_title = rule["title"]
        rule_text = rule["text"]
        source = rule["source"]

        # Generate detection methods
        regex_patterns = self._generate_regex_patterns(rule_text, rule_id)
        gpt_query = self._generate_gpt_query(rule)
        gpt_fallback = self._generate_fallback_query(rule)
        keywords = self._extract_keywords(rule_text, rule_title)
        complexity = self._determine_complexity(rule_text)
        citation_types = self._identify_citation_types(rule_text, rule_id)

        # Placeholder for deterministic checks (would be implemented per-rule)
        deterministic_checks = []
        if "curly" in rule_text.lower():
            deterministic_checks.append({
                "function": "check_curly_quotes",
                "description": "Check for straight vs curly quotes"
            })

        # Placeholder for handbook references (would need member handbook cross-reference)
        handbook_refs = []
        if source == "redbook":
            handbook_refs.append(f"See Member Handbook Section on R1 Cite Checking")

        # Create detection methods object
        detection = RuleDetectionMethods(
            rule_id=rule_id,
            rule_title=rule_title,
            rule_text=rule_text,
            source=source,
            regex_patterns=regex_patterns,
            gpt_query=gpt_query,
            gpt_fallback_query=gpt_fallback,
            deterministic_checks=deterministic_checks,
            keywords=keywords,
            citation_types=citation_types,
            handbook_references=handbook_refs,
            complexity=complexity,
            examples=[],  # Would be populated from rule examples
            related_rules=[],  # Would be computed from cross-references
            supersedes=[]  # Would be specified in Redbook
        )

        logger.debug(f"Processed rule {rule_id} ({source})")
        return detection

    def process_all_rules_parallel(self, max_workers: int = 10) -> List[RuleDetectionMethods]:
        """
        Process all rules in parallel.

        Args:
            max_workers: Maximum number of parallel workers

        Returns:
            List of processed rules
        """
        all_rules = self.get_all_rules()
        processed = []

        logger.info(f"Processing {len(all_rules)} rules with {max_workers} workers...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(self.process_rule, rule): rule
                for rule in all_rules
            }

            # Collect results as they complete
            for i, future in enumerate(as_completed(futures), 1):
                try:
                    result = future.result()
                    processed.append(result)

                    if i % 50 == 0:
                        logger.info(f"Processed {i}/{len(all_rules)} rules")

                except Exception as e:
                    rule = futures[future]
                    logger.error(f"Error processing rule {rule.get('id', 'unknown')}: {e}")

        logger.info(f"Completed processing {len(processed)} rules")
        self.processed_rules = processed
        return processed

    def save_processed_rules(self, output_path: Path = None):
        """
        Save processed rules to JSON file.

        Args:
            output_path: Output file path
        """
        if output_path is None:
            output_dir = Path.cwd() / "config" / "rules"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "enhanced_rules.json"

        # Convert to dicts
        rules_data = {
            "schema_version": "2.0.0",
            "generated_at": self.rules_data.get("generated_at"),
            "enhanced": True,
            "total_rules": len(self.processed_rules),
            "rules": [rule.to_dict() for rule in self.processed_rules]
        }

        # Group by source
        bluebook_rules = [r for r in self.processed_rules if r.source == "bluebook"]
        redbook_rules = [r for r in self.processed_rules if r.source == "redbook"]

        rules_data["statistics"] = {
            "total": len(self.processed_rules),
            "bluebook": len(bluebook_rules),
            "redbook": len(redbook_rules),
            "by_complexity": {
                "simple": len([r for r in self.processed_rules if r.complexity == "simple"]),
                "moderate": len([r for r in self.processed_rules if r.complexity == "moderate"]),
                "complex": len([r for r in self.processed_rules if r.complexity == "complex"])
            }
        }

        with open(output_path, 'w') as f:
            json.dump(rules_data, f, indent=2)

        logger.info(f"Saved {len(self.processed_rules)} processed rules to {output_path}")
        return output_path

    def generate_summary_report(self) -> str:
        """Generate summary report of processed rules."""
        if not self.processed_rules:
            return "No rules processed yet"

        lines = [
            "="*80,
            "RULE PROCESSING SUMMARY",
            "="*80,
            f"Total Rules Processed: {len(self.processed_rules)}",
            ""
        ]

        # Group by source
        bluebook = [r for r in self.processed_rules if r.source == "bluebook"]
        redbook = [r for r in self.processed_rules if r.source == "redbook"]

        lines.append(f"Bluebook Rules: {len(bluebook)}")
        lines.append(f"Redbook Rules: {len(redbook)}")
        lines.append("")

        # Complexity breakdown
        simple = len([r for r in self.processed_rules if r.complexity == "simple"])
        moderate = len([r for r in self.processed_rules if r.complexity == "moderate"])
        complex_count = len([r for r in self.processed_rules if r.complexity == "complex"])

        lines.append("Complexity Distribution:")
        lines.append(f"  Simple: {simple} ({simple/len(self.processed_rules)*100:.1f}%)")
        lines.append(f"  Moderate: {moderate} ({moderate/len(self.processed_rules)*100:.1f}%)")
        lines.append(f"  Complex: {complex_count} ({complex_count/len(self.processed_rules)*100:.1f}%)")
        lines.append("")

        # Regex patterns generated
        total_patterns = sum(len(r.regex_patterns) for r in self.processed_rules)
        lines.append(f"Total Regex Patterns Generated: {total_patterns}")
        lines.append(f"Average Patterns per Rule: {total_patterns/len(self.processed_rules):.1f}")
        lines.append("")

        # Detection methods
        lines.append("Detection Methods per Rule:")
        lines.append(f"  Regex Patterns: {total_patterns}")
        lines.append(f"  GPT Queries: {len(self.processed_rules)}")
        lines.append(f"  Fallback Queries: {len(self.processed_rules)}")
        lines.append("")

        lines.append("="*80)

        return "\n".join(lines)
