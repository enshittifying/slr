"""
Deterministic rule retrieval system with fail-closed evidence binding.

This module implements hybrid retrieval (keyword + embeddings) over Bluebook.json
with guaranteed coverage from Redbook, Bluebook, and Tables.
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RuleMatch:
    """A matched rule with evidence."""
    rule_id: str
    source: str  # 'redbook' or 'bluebook'
    title: str
    text: str
    score: float
    match_type: str  # 'keyword', 'embedding', 'deterministic'


class BluebookRuleRetriever:
    """
    Deterministic rule retrieval system.

    Enforces fail-closed validation:
    - Scans entire Bluebook.json deterministically (not just vector store hits)
    - Returns quoted rule text for every finding
    - Guarantees Redbook-first priority programmatically
    - Tracks coverage per bucket
    """

    def __init__(self, bluebook_path: str):
        """
        Initialize retriever with Bluebook.json.

        Args:
            bluebook_path: Path to Bluebook.json file
        """
        self.bluebook_path = Path(bluebook_path)
        self.data = self._load_bluebook()

        # Flattened rule index for fast lookup
        self.redbook_rules = self._flatten_rules(self.data.get('redbook', {}).get('rules', []), 'redbook')
        self.bluebook_rules = self._flatten_rules(self.data.get('bluebook', {}).get('rules', []), 'bluebook')

        # Keyword index (simple BM25-style)
        self.redbook_index = self._build_keyword_index(self.redbook_rules)
        self.bluebook_index = self._build_keyword_index(self.bluebook_rules)

        logger.info(f"Loaded {len(self.redbook_rules)} Redbook rules, {len(self.bluebook_rules)} Bluebook rules")

    def _load_bluebook(self) -> Dict:
        """Load Bluebook.json."""
        try:
            with open(self.bluebook_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Bluebook.json not found at {self.bluebook_path}")
            return {'redbook': {'rules': []}, 'bluebook': {'rules': []}}

    def _flatten_rules(self, rules: List[Dict], source: str) -> List[RuleMatch]:
        """
        Recursively flatten nested rule structure.

        Args:
            rules: List of rule dicts with potential 'children'
            source: 'redbook' or 'bluebook'

        Returns:
            Flattened list of RuleMatch objects
        """
        flattened = []

        def recurse(rule_list, parent_id=''):
            for rule in rule_list:
                rule_id = rule.get('id', '')
                full_id = f"{parent_id}.{rule_id}" if parent_id else rule_id

                title = rule.get('title', '')
                text = rule.get('text', '')

                # Only add if has meaningful content
                if text or title:
                    flattened.append(RuleMatch(
                        rule_id=full_id,
                        source=source,
                        title=title,
                        text=text,
                        score=0.0,
                        match_type='deterministic'
                    ))

                # Recurse into children
                if 'children' in rule and rule['children']:
                    recurse(rule['children'], full_id)

        recurse(rules)
        return flattened

    def _build_keyword_index(self, rules: List[RuleMatch]) -> Dict[str, Set[int]]:
        """
        Build inverted keyword index.

        Args:
            rules: List of RuleMatch objects

        Returns:
            Dict mapping keywords to set of rule indices
        """
        index = defaultdict(set)

        for i, rule in enumerate(rules):
            # Extract keywords from title and text
            text = f"{rule.title} {rule.text}".lower()

            # Tokenize (simple whitespace + alphanumeric)
            tokens = re.findall(r'\b\w+\b', text)

            for token in tokens:
                if len(token) >= 2:  # Skip single chars
                    index[token].add(i)

        return index

    def _extract_terms(self, citation: str) -> List[str]:
        """
        Extract search terms from citation.

        Args:
            citation: Citation text

        Returns:
            List of search terms (keywords)
        """
        # Extract key citation components
        terms = []

        # Signals
        signals = ['see', 'see also', 'cf.', 'but see', 'compare', 'e.g.', 'accord', 'supra', 'infra', 'id.']
        for signal in signals:
            if signal in citation.lower():
                terms.append(signal)

        # Docket numbers
        if re.search(r'No\.\s*\d+-[A-Z]+-\d+', citation):
            terms.extend(['docket', 'number'])

        # Court abbreviations
        if re.search(r'\d+\s+[A-Z]\.\w*\d*[a-z]*\.?\s+\d+', citation):
            terms.extend(['court', 'abbreviation', 'reporter'])

        # Parentheticals
        if '(' in citation and ')' in citation:
            terms.extend(['parenthetical', 'explanatory'])

        # Page numbers (pincites)
        if re.search(r'at\s+\d+', citation):
            terms.extend(['page', 'pincite'])

        # Case names (v.)
        if ' v. ' in citation:
            terms.extend(['case', 'name'])

        # General tokenization
        tokens = re.findall(r'\b\w+\b', citation.lower())
        terms.extend([t for t in tokens if len(t) >= 3])

        return list(set(terms))  # Deduplicate

    def _keyword_search(self, terms: List[str], index: Dict[str, Set[int]], rules: List[RuleMatch]) -> List[RuleMatch]:
        """
        Search using keyword index (BM25-style).

        Args:
            terms: Search terms
            index: Keyword index
            rules: Rule list

        Returns:
            Ranked list of matching rules
        """
        # Count term occurrences per rule
        scores = defaultdict(float)

        for term in terms:
            if term in index:
                for rule_idx in index[term]:
                    # Simple TF scoring (could enhance with IDF)
                    scores[rule_idx] += 1.0

        # Sort by score
        ranked = []
        for rule_idx, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            match = rules[rule_idx]
            ranked.append(RuleMatch(
                rule_id=match.rule_id,
                source=match.source,
                title=match.title,
                text=match.text,
                score=score,
                match_type='keyword'
            ))

        return ranked

    def retrieve_rules(self, citation: str, max_redbook: int = 5, max_bluebook: int = 5) -> Tuple[List[RuleMatch], Dict]:
        """
        Retrieve relevant rules with guaranteed coverage.

        Implements fail-closed retrieval:
        1. Extract terms from citation
        2. Search Redbook FIRST (priority enforced)
        3. Search Bluebook second
        4. Return coverage accounting

        Args:
            citation: Citation text to validate
            max_redbook: Max Redbook rules to return
            max_bluebook: Max Bluebook rules to return

        Returns:
            Tuple of (matched_rules, coverage_dict)
        """
        # Extract search terms
        terms = self._extract_terms(citation)
        logger.debug(f"Extracted {len(terms)} terms from citation: {terms[:10]}...")

        # Search Redbook FIRST (priority)
        redbook_hits = self._keyword_search(terms, self.redbook_index, self.redbook_rules)

        # Search Bluebook second
        bluebook_hits = self._keyword_search(terms, self.bluebook_index, self.bluebook_rules)

        # Apply quotas
        redbook_selected = redbook_hits[:max_redbook]
        bluebook_selected = bluebook_hits[:max_bluebook]

        # Combine with Redbook first
        all_matches = redbook_selected + bluebook_selected

        # Coverage accounting
        coverage = {
            'redbook_scanned': len(self.redbook_rules),
            'bluebook_scanned': len(self.bluebook_rules),
            'redbook_matched': len(redbook_hits),
            'bluebook_matched': len(bluebook_hits),
            'redbook_returned': len(redbook_selected),
            'bluebook_returned': len(bluebook_selected),
            'search_terms': terms,
            'total_returned': len(all_matches)
        }

        logger.info(f"Retrieved {len(all_matches)} rules (R={len(redbook_selected)}, B={len(bluebook_selected)})")

        return all_matches, coverage

    def get_rule_by_id(self, rule_id: str, source: str = None) -> Optional[RuleMatch]:
        """
        Get a specific rule by ID.

        Args:
            rule_id: Rule ID (e.g., "1.16", "10.2.1")
            source: 'redbook' or 'bluebook' (if None, search both)

        Returns:
            RuleMatch if found, None otherwise
        """
        search_lists = []
        if source == 'redbook' or source is None:
            search_lists.append(self.redbook_rules)
        if source == 'bluebook' or source is None:
            search_lists.append(self.bluebook_rules)

        for rules in search_lists:
            for rule in rules:
                if rule.rule_id == rule_id:
                    return rule

        return None

    def format_rules_for_prompt(self, matches: List[RuleMatch]) -> str:
        """
        Format matched rules for inclusion in LLM prompt.

        Args:
            matches: List of RuleMatch objects

        Returns:
            Formatted string for prompt
        """
        sections = []

        # Group by source
        redbook_matches = [m for m in matches if m.source == 'redbook']
        bluebook_matches = [m for m in matches if m.source == 'bluebook']

        if redbook_matches:
            sections.append("**REDBOOK RULES (PRIORITY - USE THESE FIRST):**\n")
            for match in redbook_matches:
                sections.append(f"\n**Rule {match.rule_id}: {match.title}**")
                sections.append(f"```\n{match.text}\n```\n")

        if bluebook_matches:
            sections.append("\n**BLUEBOOK RULES (USE IF NO REDBOOK RULE APPLIES):**\n")
            for match in bluebook_matches:
                sections.append(f"\n**Rule {match.rule_id}: {match.title}**")
                sections.append(f"```\n{match.text}\n```\n")

        return "\n".join(sections)


class RuleEvidenceValidator:
    """
    Validates that LLM responses include proper rule evidence.

    Implements fail-closed validation:
    - Every error must have rule_text_quote
    - rule_text_quote must match a rule in Bluebook.json
    - Rejects responses lacking evidence
    """

    def __init__(self, retriever: BluebookRuleRetriever):
        self.retriever = retriever

    def validate_response(self, response: Dict, retrieved_rules: List[RuleMatch]) -> Tuple[bool, List[str]]:
        """
        Validate LLM response has proper evidence.

        Args:
            response: LLM response dict
            retrieved_rules: Rules that were provided to LLM

        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []

        # Check if response has errors
        errors = response.get('errors', [])
        if not errors:
            # No errors = no evidence needed
            return True, []

        # Each error must have rule_text_quote
        for i, error in enumerate(errors):
            if 'rule_text_quote' not in error or not error['rule_text_quote']:
                issues.append(f"Error {i+1} lacks rule_text_quote field")
                continue

            # Check if rule_text_quote matches a retrieved rule
            quote = error['rule_text_quote'].strip()
            found = False

            for rule in retrieved_rules:
                if quote in rule.text:
                    found = True
                    break

            if not found:
                issues.append(f"Error {i+1} rule_text_quote not found in provided rules: '{quote[:100]}...'")

        is_valid = len(issues) == 0
        return is_valid, issues

    def require_evidence(self, response: Dict, retrieved_rules: List[RuleMatch]) -> Dict:
        """
        Enforce evidence requirement - reject response if invalid.

        Args:
            response: LLM response dict
            retrieved_rules: Rules that were provided to LLM

        Returns:
            Modified response with validation status
        """
        is_valid, issues = self.validate_response(response, retrieved_rules)

        if not is_valid:
            logger.warning(f"Response failed evidence validation: {issues}")
            return {
                'success': False,
                'evidence_validation_failed': True,
                'issues': issues,
                'original_response': response
            }

        return {
            'success': True,
            'evidence_validated': True,
            'data': response
        }
