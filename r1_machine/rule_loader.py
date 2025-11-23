"""
Rule loader module for R1 Machine.

This module loads and indexes all Bluebook, Redbook, and Table JSON rules
from the SLRinator directory. It provides efficient lookup and querying
of citation rules for validation.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import defaultdict


logger = logging.getLogger(__name__)


@dataclass
class Rule:
    """Represents a single Bluebook rule."""

    rule_id: str  # e.g., "10-1", "16-4"
    title: str
    category: str  # general, signals, ordering, etc.
    patterns: List[str]  # Regex patterns from rule
    content: Dict[str, Any]  # Full rule content
    examples: List[str]  # Example citations
    source_file: str  # Source JSON file


@dataclass
class TableEntry:
    """Represents an entry from a USC table."""

    table_num: int  # Table number (1-6)
    key: str  # Lookup key
    value: str  # Mapped value
    metadata: Dict[str, Any]  # Additional fields


class RuleLoader:
    """
    Loads and manages all citation rules from JSON files.

    This class provides efficient access to:
    - Bluebook rules organized by section and category
    - Table mappings (USC Tables 1-6)
    - Abbreviation dictionaries
    - Pattern matching for citation types
    """

    def __init__(self, rules_dir: Path):
        """
        Initialize the rule loader.

        Args:
            rules_dir: Path to directory containing rule JSON files
        """
        self.rules_dir = Path(rules_dir)

        # Rule storage
        self.bluebook_rules: Dict[str, List[Rule]] = defaultdict(list)
        self.redbook_rules: Dict[str, List[Rule]] = defaultdict(list)
        self.table_rules: Dict[int, List[TableEntry]] = defaultdict(list)

        # Abbreviation dictionaries
        self.case_name_abbreviations: Dict[str, str] = {}
        self.reporter_abbreviations: Dict[str, str] = {}
        self.court_abbreviations: Dict[str, str] = {}

        # Citation type patterns
        self.citation_type_patterns: Dict[str, List[str]] = {}

        # Statistics
        self.stats = {
            "bluebook_rules_loaded": 0,
            "redbook_rules_loaded": 0,
            "table_entries_loaded": 0,
            "abbreviations_loaded": 0,
        }

        # Load state
        self._loaded = False

    def load_all_rules(self) -> None:
        """
        Load all rules from the rules directory.

        This method loads:
        1. Bluebook rules from captures_extracts/
        2. Table mappings from olrc/output_tables/
        3. Rule analysis data from bluebook_rules_analysis.json

        Raises:
            FileNotFoundError: If rules directory doesn't exist
            ValueError: If required rule files are missing
        """
        if self._loaded:
            logger.info("Rules already loaded, skipping reload")
            return

        logger.info(f"Loading rules from {self.rules_dir}")

        # Load Bluebook rules from captures_extracts
        self._load_bluebook_rules()

        # Load table mappings
        self._load_table_rules()

        # Load rule analysis (patterns and metadata)
        self._load_rule_analysis()

        # Build abbreviation dictionaries
        self._build_abbreviation_dicts()

        # Log statistics
        self._log_statistics()

        self._loaded = True

    def _load_bluebook_rules(self) -> None:
        """Load Bluebook rules from captures_extracts directory."""
        captures_dir = self.rules_dir / "captures_extracts"

        if not captures_dir.exists():
            logger.warning(f"Captures directory not found: {captures_dir}")
            return

        # Find all JSON files in captures_extracts
        json_files = list(captures_dir.glob("*.json"))
        logger.info(f"Found {len(json_files)} rule files")

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Extract rule information
                rule_id = self._extract_rule_id(json_file.stem)
                title = data.get("title", "")
                category = self._categorize_rule(rule_id, title)

                # Extract patterns and examples from content
                patterns = self._extract_patterns(data)
                examples = self._extract_examples(data)

                rule = Rule(
                    rule_id=rule_id,
                    title=title,
                    category=category,
                    patterns=patterns,
                    content=data,
                    examples=examples,
                    source_file=json_file.name
                )

                # Store by category and by rule number
                self.bluebook_rules[category].append(rule)
                self.bluebook_rules[rule_id].append(rule)

                self.stats["bluebook_rules_loaded"] += 1

            except Exception as e:
                logger.error(f"Error loading rule file {json_file}: {e}")

        logger.info(f"Loaded {self.stats['bluebook_rules_loaded']} Bluebook rules")

    def _load_table_rules(self) -> None:
        """Load USC table mappings from olrc/output_tables directory."""
        tables_dir = self.rules_dir / "olrc" / "output_tables"

        if not tables_dir.exists():
            logger.warning(f"Tables directory not found: {tables_dir}")
            return

        # Load tables 1-6
        for table_num in range(1, 7):
            table_file = tables_dir / f"usc_table{table_num}.json"

            if not table_file.exists():
                logger.warning(f"Table {table_num} not found: {table_file}")
                continue

            try:
                with open(table_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                records = data.get("records", [])

                for record in records:
                    # Extract key-value pairs based on table structure
                    entry = self._parse_table_entry(table_num, record)
                    if entry:
                        self.table_rules[table_num].append(entry)
                        self.stats["table_entries_loaded"] += 1

                logger.info(f"Loaded {len(records)} entries from Table {table_num}")

            except Exception as e:
                logger.error(f"Error loading table {table_num}: {e}")

    def _load_rule_analysis(self) -> None:
        """Load rule analysis data with patterns and metadata."""
        analysis_file = self.rules_dir / "bluebook_rules_analysis.json"

        if not analysis_file.exists():
            logger.warning(f"Rule analysis file not found: {analysis_file}")
            return

        try:
            with open(analysis_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract pattern information from all_rules
            all_rules = data.get("all_rules", {})

            for rule_id, rule_patterns in all_rules.items():
                for pattern_info in rule_patterns:
                    # Store pattern by type
                    pattern_type = pattern_info.get("type", "pattern")
                    pattern = pattern_info.get("pattern") or pattern_info.get("text", "")

                    if pattern:
                        if pattern_type not in self.citation_type_patterns:
                            self.citation_type_patterns[pattern_type] = []
                        self.citation_type_patterns[pattern_type].append(pattern)

            logger.info(f"Loaded rule analysis with {len(all_rules)} rule entries")

        except Exception as e:
            logger.error(f"Error loading rule analysis: {e}")

    def _build_abbreviation_dicts(self) -> None:
        """Build abbreviation dictionaries from loaded rules."""
        # This would extract abbreviations from relevant rule files
        # For now, we'll add common ones manually

        # Common case name abbreviations (from Bluebook Rule 10.2.1)
        self.case_name_abbreviations.update({
            "Association": "Ass'n",
            "Administrator": "Adm'r",
            "Incorporated": "Inc.",
            "Corporation": "Corp.",
            "Company": "Co.",
            "Department": "Dep't",
            "Government": "Gov't",
            "United States": "U.S.",
            "versus": "v.",
        })

        # Common reporter abbreviations
        self.reporter_abbreviations.update({
            "United States Reports": "U.S.",
            "Supreme Court Reporter": "S. Ct.",
            "Federal Reporter": "F.",
            "Federal Supplement": "F. Supp.",
            "Federal Reporter Second": "F.2d",
            "Federal Reporter Third": "F.3d",
        })

        # Common court abbreviations
        self.court_abbreviations.update({
            "United States Supreme Court": "U.S.",
            "District of Columbia Circuit": "D.C. Cir.",
            "First Circuit": "1st Cir.",
            "Second Circuit": "2d Cir.",
            "District Court": "D.",
        })

        self.stats["abbreviations_loaded"] = (
            len(self.case_name_abbreviations) +
            len(self.reporter_abbreviations) +
            len(self.court_abbreviations)
        )

    def get_rules_for_type(self, citation_type: str) -> List[Rule]:
        """
        Get all rules applicable to a citation type.

        Args:
            citation_type: Type of citation (case, statute, book, etc.)

        Returns:
            List of applicable Rule objects

        Example:
            >>> loader = RuleLoader(Path("/path/to/rules"))
            >>> loader.load_all_rules()
            >>> case_rules = loader.get_rules_for_type("case")
        """
        # Map citation types to rule sections
        type_to_section = {
            "case": "10",
            "constitution": "11",
            "statute": "12",
            "legislative": "13",
            "administrative": "14",
            "book": "15",
            "periodical": "16",
            "article": "16",
            "unpublished": "17",
            "electronic": "18",
        }

        section = type_to_section.get(citation_type.lower())
        if not section:
            return []

        # Get all rules starting with this section number
        rules = []
        for rule_id, rule_list in self.bluebook_rules.items():
            if rule_id.startswith(section):
                rules.extend(rule_list)

        return rules

    def check_abbreviation(
        self,
        term: str,
        abbreviation_type: str = "case_name"
    ) -> Optional[str]:
        """
        Check if a term should be abbreviated and return the abbreviation.

        Args:
            term: The term to check
            abbreviation_type: Type of abbreviation (case_name, reporter, court)

        Returns:
            Abbreviation if found, None otherwise

        Example:
            >>> loader = RuleLoader(Path("/path/to/rules"))
            >>> loader.load_all_rules()
            >>> loader.check_abbreviation("Corporation", "case_name")
            'Corp.'
        """
        abbrev_dict = {
            "case_name": self.case_name_abbreviations,
            "reporter": self.reporter_abbreviations,
            "court": self.court_abbreviations,
        }.get(abbreviation_type, {})

        return abbrev_dict.get(term)

    def lookup_table(self, table_num: int, key: str) -> Optional[str]:
        """
        Look up a value in a USC table.

        Args:
            table_num: Table number (1-6)
            key: Lookup key

        Returns:
            Mapped value if found, None otherwise

        Example:
            >>> loader = RuleLoader(Path("/path/to/rules"))
            >>> loader.load_all_rules()
            >>> loader.lookup_table(1, "former_section:16:21")
            '101'
        """
        entries = self.table_rules.get(table_num, [])

        for entry in entries:
            if entry.key == key:
                return entry.value

        return None

    def get_examples_for_type(self, citation_type: str) -> List[str]:
        """
        Get example citations for a given type.

        Args:
            citation_type: Type of citation

        Returns:
            List of example citation strings
        """
        rules = self.get_rules_for_type(citation_type)
        examples = []

        for rule in rules:
            examples.extend(rule.examples)

        return examples

    # ========== Helper Methods ==========

    def _extract_rule_id(self, filename: str) -> str:
        """Extract rule ID from filename."""
        # Remove timestamp and extension
        # e.g., "10-1-basic-citation-forms_20250819_153803" -> "10-1"
        parts = filename.split("_")[0].split("-")

        # Handle different formats
        if len(parts) >= 2 and parts[0].isdigit():
            # Format: "10-1-..." -> "10-1"
            return f"{parts[0]}-{parts[1]}"
        elif parts[0].isdigit():
            # Format: "10-..." -> "10"
            return parts[0]
        else:
            return filename

    def _categorize_rule(self, rule_id: str, title: str) -> str:
        """Categorize a rule based on its ID and title."""
        title_lower = title.lower()

        if "signal" in title_lower:
            return "signals"
        elif "order" in title_lower:
            return "ordering"
        elif "parenthetical" in title_lower:
            return "parentheticals"
        elif "abbreviation" in title_lower or "abbrev" in title_lower:
            return "abbreviation"
        elif "format" in title_lower or "typeface" in title_lower:
            return "formatting"
        elif "punctuation" in title_lower:
            return "punctuation"
        elif "capitaliz" in title_lower:
            return "capitalization"
        else:
            return "general"

    def _extract_patterns(self, rule_data: Dict[str, Any]) -> List[str]:
        """Extract regex patterns from rule data."""
        patterns = []

        # Look for patterns in body_text or examples
        body_text = rule_data.get("body_text", "")

        # Extract example citations (simple heuristic)
        # Look for lines with volume numbers, reporters, etc.
        import re
        citation_pattern = r'\b\d+\s+[A-Z][a-z]*\.?\s+\d+'
        matches = re.findall(citation_pattern, body_text)
        patterns.extend(matches[:5])  # Limit to 5 patterns

        return patterns

    def _extract_examples(self, rule_data: Dict[str, Any]) -> List[str]:
        """Extract example citations from rule data."""
        examples = []

        body_text = rule_data.get("body_text", "")

        # Split into lines and look for citation-like patterns
        lines = body_text.split("\n")
        for line in lines:
            line = line.strip()
            # Simple heuristic: lines ending with period and containing v. or §
            if line and ((" v. " in line or " § " in line) and line.endswith(".")):
                examples.append(line)

        return examples[:10]  # Limit to 10 examples

    def _parse_table_entry(
        self,
        table_num: int,
        record: Dict[str, Any]
    ) -> Optional[TableEntry]:
        """Parse a table record into a TableEntry."""
        try:
            if table_num == 1:
                # Table 1: Former to new section mappings
                key = f"{record['former_title']}:{record['former_section']}"
                value = record.get("new_section_text", "")

                return TableEntry(
                    table_num=table_num,
                    key=key,
                    value=value,
                    metadata=record
                )
            else:
                # Other tables - generic handling
                # Use first two fields as key-value
                fields = list(record.values())
                if len(fields) >= 2:
                    return TableEntry(
                        table_num=table_num,
                        key=str(fields[0]),
                        value=str(fields[1]),
                        metadata=record
                    )

        except Exception as e:
            logger.error(f"Error parsing table entry: {e}")

        return None

    def _log_statistics(self) -> None:
        """Log loading statistics."""
        logger.info("="*50)
        logger.info("Rule Loading Statistics")
        logger.info("="*50)
        logger.info(f"Bluebook rules loaded: {self.stats['bluebook_rules_loaded']}")
        logger.info(f"Table entries loaded: {self.stats['table_entries_loaded']}")
        logger.info(f"Abbreviations loaded: {self.stats['abbreviations_loaded']}")

        # Category breakdown
        logger.info("\nRules by category:")
        category_counts = defaultdict(int)
        for rules in self.bluebook_rules.values():
            for rule in rules:
                category_counts[rule.category] += 1

        for category, count in sorted(category_counts.items()):
            logger.info(f"  {category}: {count}")

        logger.info("="*50)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    loader = RuleLoader(Path("/home/user/slr/SLRinator"))
    loader.load_all_rules()

    # Test lookups
    print("\n=== Testing Rule Loader ===\n")

    # Get case rules
    case_rules = loader.get_rules_for_type("case")
    print(f"Found {len(case_rules)} case-related rules")

    # Check abbreviation
    abbrev = loader.check_abbreviation("Corporation", "case_name")
    print(f"Abbreviation for 'Corporation': {abbrev}")

    # Get examples
    examples = loader.get_examples_for_type("case")
    print(f"\nFound {len(examples)} example citations")
    if examples:
        print(f"Example: {examples[0]}")
