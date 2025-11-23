"""
Comprehensive Rule Processor for ALL Bluebook/Redbook Content
Processes rules, tables, abbreviations, citation forms - EVERYTHING
"""
import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


@dataclass
class TableEntryDetection:
    """Detection methods for a table entry (abbreviation, court name, etc.)."""
    table_id: str
    table_name: str
    entry_key: str  # The term being abbreviated
    entry_value: str  # The abbreviation or expanded form
    category: str  # Type of entry

    # Detection methods
    regex_long_to_short: str  # Regex to find long form and suggest short
    regex_short_to_long: str  # Regex to find short form and verify
    gpt_query: str  # GPT query for validation

    # Metadata
    keywords: List[str]
    citation_types: List[str]
    examples: List[Dict[str, str]]

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CitationFormDetection:
    """Detection methods for citation forms (short cite, long cite, etc.)."""
    form_type: str  # "short_cite", "long_cite", "id_cite", "supra_cite"
    citation_type: str  # "case", "statute", "article", etc.
    pattern_template: str  # Template pattern
    required_elements: List[str]
    optional_elements: List[str]

    # Detection
    regex_pattern: str
    gpt_validation_query: str

    # Examples
    correct_examples: List[str]
    incorrect_examples: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


class ComprehensiveRuleProcessor:
    """
    Processes EVERYTHING in Bluebook.json:
    - All rules (rules + children recursively)
    - All tables (T1-T16)
    - All abbreviations
    - All citation forms (short, long, id., supra)
    - All court names
    - All explanatory phrases
    - Everything else
    """

    def __init__(self, bluebook_path: Path = None):
        """Initialize comprehensive processor."""
        self.bluebook_path = bluebook_path or Path.cwd() / "config" / "rules" / "Bluebook.json"
        self.rules_data = self._load_rules()

        # Storage for all processed items
        self.processed_rules = []
        self.processed_tables = []
        self.processed_abbreviations = []
        self.processed_court_names = []
        self.processed_citation_forms = []
        self.processed_explanatory_phrases = []

    def _load_rules(self) -> Dict:
        """Load rules from Bluebook.json."""
        with open(self.bluebook_path) as f:
            return json.load(f)

    def process_all_tables(self) -> List[TableEntryDetection]:
        """
        Process all Bluebook tables (T1-T16).

        Returns:
            List of processed table entries
        """
        if "bluebook" not in self.rules_data or "tables" not in self.rules_data["bluebook"]:
            logger.warning("No tables found in Bluebook data")
            return []

        tables = self.rules_data["bluebook"]["tables"]
        all_entries = []

        logger.info(f"Processing {len(tables)} Bluebook tables...")

        for table_id in sorted(tables.keys()):
            table_data = tables[table_id]

            if table_id == "T6":  # Common Words
                all_entries.extend(self._process_table_t6(table_id, table_data))
            elif table_id == "T7":  # Court Names
                all_entries.extend(self._process_table_t7(table_id, table_data))
            elif table_id == "T8":  # Explanatory Phrases
                all_entries.extend(self._process_table_t8(table_id, table_data))
            elif table_id == "T13":  # Institutional Names
                all_entries.extend(self._process_table_t13(table_id, table_data))
            elif table_id == "T1":  # Jurisdictions
                all_entries.extend(self._process_table_t1(table_id, table_data))
            else:
                all_entries.extend(self._process_generic_table(table_id, table_data))

        logger.info(f"Processed {len(all_entries)} table entries")
        self.processed_tables = all_entries
        return all_entries

    def _process_table_t6(self, table_id: str, table_data: Dict) -> List[TableEntryDetection]:
        """Process Table 6: Common Words in Case Names (299 words!)."""
        entries = []

        # T6 has 299 abbreviations for common words
        for word, abbrev in table_data.items():
            if not isinstance(abbrev, str):
                continue

            # Create regex to detect unabbreviated form
            regex_long = rf'\b{re.escape(word)}\b'
            regex_short = rf'\b{re.escape(abbrev)}\b'

            # GPT query
            gpt_query = f"""Validate abbreviation usage in case name.

Rule: Table 6 - Common Words in Case Names
Word: {word}
Correct Abbreviation: {abbrev}

Check if the citation correctly abbreviates "{word}" as "{abbrev}" in the case name.

Citation: {{citation_text}}

Return JSON: {{"is_correct": boolean, "error_description": string if error}}"""

            entry = TableEntryDetection(
                table_id="T6",
                table_name="Common Words in Case Names",
                entry_key=word,
                entry_value=abbrev,
                category="case_name_abbreviation",
                regex_long_to_short=regex_long,
                regex_short_to_long=regex_short,
                gpt_query=gpt_query,
                keywords=[word.lower(), abbrev.lower(), "case name", "abbreviation"],
                citation_types=["case"],
                examples=[{
                    "incorrect": f"{word} Corp. v. Smith",
                    "correct": f"{abbrev} v. Smith" if word != "versus" else f"{abbrev} Smith"
                }]
            )
            entries.append(entry)

        logger.info(f"Processed T6: {len(entries)} common word abbreviations")
        return entries

    def _process_table_t7(self, table_id: str, table_data: Dict) -> List[TableEntryDetection]:
        """Process Table 7: Court Names (111 courts!)."""
        entries = []

        for court_name, abbrev in table_data.items():
            if not isinstance(abbrev, str):
                continue

            # Regex patterns
            regex_long = rf'{re.escape(court_name)}'
            regex_short = rf'{re.escape(abbrev)}'

            # GPT query
            gpt_query = f"""Validate court name abbreviation.

Rule: Table 7 - Court Names
Full Name: {court_name}
Correct Abbreviation: {abbrev}

Check if the citation correctly abbreviates "{court_name}" as "{abbrev}".

Citation: {{citation_text}}

Return JSON: {{"is_correct": boolean, "court_name_correct": boolean}}"""

            entry = TableEntryDetection(
                table_id="T7",
                table_name="Court Names",
                entry_key=court_name,
                entry_value=abbrev,
                category="court_abbreviation",
                regex_long_to_short=regex_long,
                regex_short_to_long=regex_short,
                gpt_query=gpt_query,
                keywords=[court_name.lower(), abbrev.lower(), "court"],
                citation_types=["case"],
                examples=[{
                    "incorrect": f"({court_name})",
                    "correct": f"({abbrev})"
                }]
            )
            entries.append(entry)

        logger.info(f"Processed T7: {len(entries)} court name abbreviations")
        self.processed_court_names = entries
        return entries

    def _process_table_t8(self, table_id: str, table_data: Dict) -> List[TableEntryDetection]:
        """Process Table 8: Explanatory Phrases (41 phrases)."""
        entries = []

        for phrase, abbrev in table_data.items():
            if not isinstance(abbrev, str):
                continue

            # These are parenthetical explanatory phrases
            regex_pattern = rf'\({re.escape(phrase)}'

            gpt_query = f"""Validate explanatory phrase usage.

Rule: Table 8 - Explanatory Phrases
Full Phrase: {phrase}
Abbreviation: {abbrev}

Check if parenthetical uses correct form.

Citation: {{citation_text}}

Return JSON: {{"is_correct": boolean, "phrase_correct": boolean}}"""

            entry = TableEntryDetection(
                table_id="T8",
                table_name="Explanatory Phrases",
                entry_key=phrase,
                entry_value=abbrev,
                category="explanatory_phrase",
                regex_long_to_short=regex_pattern,
                regex_short_to_long=rf'{re.escape(abbrev)}',
                gpt_query=gpt_query,
                keywords=[phrase.lower(), abbrev.lower(), "parenthetical"],
                citation_types=["case", "general"],
                examples=[{
                    "full_form": f"({phrase})",
                    "abbreviated": f"({abbrev})"
                }]
            )
            entries.append(entry)

        logger.info(f"Processed T8: {len(entries)} explanatory phrases")
        self.processed_explanatory_phrases = entries
        return entries

    def _process_table_t13(self, table_id: str, table_data: Dict) -> List[TableEntryDetection]:
        """Process Table 13: Institutional Names in Periodical Titles (36 institutions)."""
        entries = []

        for institution, abbrev in table_data.items():
            if not isinstance(abbrev, str):
                continue

            regex_long = rf'{re.escape(institution)}'
            regex_short = rf'{re.escape(abbrev)}'

            gpt_query = f"""Validate institutional name abbreviation in periodical title.

Rule: Table 13 - Institutional Names in Periodicals
Full Name: {institution}
Abbreviation: {abbrev}

Citation: {{citation_text}}

Return JSON: {{"is_correct": boolean}}"""

            entry = TableEntryDetection(
                table_id="T13",
                table_name="Institutional Names in Periodical Titles",
                entry_key=institution,
                entry_value=abbrev,
                category="periodical_institution",
                regex_long_to_short=regex_long,
                regex_short_to_long=regex_short,
                gpt_query=gpt_query,
                keywords=[institution.lower(), abbrev.lower(), "periodical", "journal"],
                citation_types=["article"],
                examples=[{
                    "full": institution,
                    "abbreviated": abbrev
                }]
            )
            entries.append(entry)

        logger.info(f"Processed T13: {len(entries)} institutional names")
        return entries

    def _process_table_t1(self, table_id: str, table_data: Dict) -> List[TableEntryDetection]:
        """Process Table 1: Federal and State Jurisdictions."""
        entries = []

        # T1 has multiple sections
        for section_name, section_data in table_data.items():
            if not isinstance(section_data, dict):
                continue

            logger.info(f"Processing T1 section: {section_name} ({len(section_data)} items)")

            for jurisdiction, abbrev_data in section_data.items():
                # abbrev_data could be string or dict
                abbrev = abbrev_data if isinstance(abbrev_data, str) else str(abbrev_data)

                entry = TableEntryDetection(
                    table_id="T1",
                    table_name=f"Table 1: {section_name}",
                    entry_key=jurisdiction,
                    entry_value=abbrev,
                    category="jurisdiction",
                    regex_long_to_short=rf'{re.escape(jurisdiction)}',
                    regex_short_to_long=rf'{re.escape(abbrev)}',
                    gpt_query=f"Validate jurisdiction abbreviation: {jurisdiction} -> {abbrev}",
                    keywords=[jurisdiction.lower(), "jurisdiction"],
                    citation_types=["case", "statute"],
                    examples=[]
                )
                entries.append(entry)

        logger.info(f"Processed T1: {len(entries)} jurisdictions")
        return entries

    def _process_generic_table(self, table_id: str, table_data: Any) -> List[TableEntryDetection]:
        """Process other tables generically."""
        entries = []

        if isinstance(table_data, dict):
            for key, value in table_data.items():
                if isinstance(value, dict):
                    # Nested structure
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, str):
                            entry = TableEntryDetection(
                                table_id=table_id,
                                table_name=f"Table {table_id}: {key}",
                                entry_key=sub_key,
                                entry_value=sub_value,
                                category=f"table_{table_id.lower()}",
                                regex_long_to_short=rf'{re.escape(sub_key)}',
                                regex_short_to_long=rf'{re.escape(sub_value)}',
                                gpt_query=f"Validate {key}: {sub_key} -> {sub_value}",
                                keywords=[sub_key.lower()],
                                citation_types=["general"],
                                examples=[]
                            )
                            entries.append(entry)
                elif isinstance(value, str):
                    entry = TableEntryDetection(
                        table_id=table_id,
                        table_name=f"Table {table_id}",
                        entry_key=key,
                        entry_value=value,
                        category=f"table_{table_id.lower()}",
                        regex_long_to_short=rf'{re.escape(key)}',
                        regex_short_to_long=rf'{re.escape(value)}',
                        gpt_query=f"Validate {table_id}: {key} -> {value}",
                        keywords=[key.lower()],
                        citation_types=["general"],
                        examples=[]
                    )
                    entries.append(entry)

        logger.info(f"Processed {table_id}: {len(entries)} entries")
        return entries

    def generate_citation_forms(self) -> List[CitationFormDetection]:
        """
        Generate detection methods for all citation forms.

        Returns:
            List of citation form detection methods
        """
        forms = []

        # Case citations
        forms.extend(self._generate_case_citation_forms())

        # Statute citations
        forms.extend(self._generate_statute_citation_forms())

        # Article citations
        forms.extend(self._generate_article_citation_forms())

        # Short citation forms (id., supra)
        forms.extend(self._generate_short_citation_forms())

        logger.info(f"Generated {len(forms)} citation form patterns")
        self.processed_citation_forms = forms
        return forms

    def _generate_case_citation_forms(self) -> List[CitationFormDetection]:
        """Generate case citation form patterns."""
        forms = []

        # Full case citation
        forms.append(CitationFormDetection(
            form_type="long_cite",
            citation_type="case",
            pattern_template="Party v. Party, Volume Reporter Page (Court Year)",
            required_elements=["party_names", "volume", "reporter", "page", "year"],
            optional_elements=["court", "parenthetical"],
            regex_pattern=r'[A-Z][^,]+\s+v\.\s+[A-Z][^,]+,\s+\d+\s+[A-Z][^,]+\s+\d+\s+\([^)]+\s+\d{4}\)',
            gpt_validation_query="Validate full case citation format per Bluebook Rule 10",
            correct_examples=["Smith v. Jones, 123 F.3d 456 (9th Cir. 2020)"],
            incorrect_examples=["Smith v Jones 123 F.3d 456 (2020)"]
        ))

        # Short case citation (id.)
        forms.append(CitationFormDetection(
            form_type="short_cite",
            citation_type="case",
            pattern_template="Id. at Page",
            required_elements=["id", "page"],
            optional_elements=[],
            regex_pattern=r'Id\.\s+at\s+\d+',
            gpt_validation_query="Validate Id. short citation per Bluebook Rule 4.1",
            correct_examples=["Id. at 789"],
            incorrect_examples=["id. at 789", "Id at 789"]
        ))

        return forms

    def _generate_statute_citation_forms(self) -> List[CitationFormDetection]:
        """Generate statute citation form patterns."""
        forms = []

        # U.S.C. citation
        forms.append(CitationFormDetection(
            form_type="long_cite",
            citation_type="statute",
            pattern_template="Title U.S.C. § Section (Year)",
            required_elements=["title", "section", "year"],
            optional_elements=[],
            regex_pattern=r'\d+\s+U\.S\.C\.\s+§\s+\d+.*?\(\d{4}\)',
            gpt_validation_query="Validate U.S.C. citation per Bluebook Rule 12",
            correct_examples=["42 U.S.C. § 1983 (2018)"],
            incorrect_examples=["42 USC § 1983", "42 U.S.C. §1983"]
        ))

        return forms

    def _generate_article_citation_forms(self) -> List[CitationFormDetection]:
        """Generate article citation form patterns."""
        forms = []

        # Law review article
        forms.append(CitationFormDetection(
            form_type="long_cite",
            citation_type="article",
            pattern_template="Author, Title, Volume Journal Page (Year)",
            required_elements=["author", "title", "volume", "journal", "page", "year"],
            optional_elements=["pinpoint"],
            regex_pattern=r'[A-Z][^,]+,\s+[^,]+,\s+\d+\s+[A-Z][^,]+\s+\d+.*?\(\d{4}\)',
            gpt_validation_query="Validate article citation per Bluebook Rule 16",
            correct_examples=["John Doe, Patent Law, 100 HARV. L. REV. 123 (2020)"],
            incorrect_examples=["John Doe, Patent Law, Harv. L. Rev. 100, 123 (2020)"]
        ))

        return forms

    def _generate_short_citation_forms(self) -> List[CitationFormDetection]:
        """Generate short citation form patterns (id., supra, etc.)."""
        forms = []

        # Supra citation
        forms.append(CitationFormDetection(
            form_type="short_cite",
            citation_type="general",
            pattern_template="Author, supra note N, at Page",
            required_elements=["author", "note_num"],
            optional_elements=["page"],
            regex_pattern=r'[A-Z][^,]+,\s+supra\s+note\s+\d+',
            gpt_validation_query="Validate supra citation per Bluebook Rule 4.2",
            correct_examples=["Doe, supra note 5, at 10"],
            incorrect_examples=["Doe, Supra note 5", "Doe supra note 5"]
        ))

        return forms

    def process_everything_parallel(self, max_workers: int = 20) -> Dict[str, Any]:
        """
        Process EVERYTHING in parallel:
        - All rules
        - All tables
        - All citation forms

        Args:
            max_workers: Number of parallel workers

        Returns:
            Dict with all processed data
        """
        logger.info("Starting comprehensive parallel processing...")

        # Import the original rule processor for rules
        from .rule_processor import RuleProcessor
        rule_processor = RuleProcessor(self.bluebook_path)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all processing tasks
            futures = {
                'rules': executor.submit(rule_processor.process_all_rules_parallel, max_workers),
                'tables': executor.submit(self.process_all_tables),
                'citation_forms': executor.submit(self.generate_citation_forms)
            }

            # Collect results
            results = {}
            for name, future in futures.items():
                try:
                    results[name] = future.result()
                    logger.info(f"Completed processing {name}")
                except Exception as e:
                    logger.error(f"Error processing {name}: {e}")
                    results[name] = []

        # Update instance variables
        self.processed_rules = results.get('rules', [])
        self.processed_tables = results.get('tables', [])
        self.processed_citation_forms = results.get('citation_forms', [])

        return results

    def save_comprehensive_data(self, output_path: Path = None) -> Path:
        """Save all processed data to comprehensive JSON file."""
        if output_path is None:
            output_dir = Path.cwd() / "config" / "rules"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "comprehensive_bluebook.json"

        data = {
            "schema_version": "3.0.0",
            "generated_at": self.rules_data.get("generated_at"),
            "comprehensive": True,

            # Statistics
            "statistics": {
                "total_rules": len(self.processed_rules),
                "total_table_entries": len(self.processed_tables),
                "total_citation_forms": len(self.processed_citation_forms),
                "total_items": len(self.processed_rules) + len(self.processed_tables) + len(self.processed_citation_forms)
            },

            # All data
            "rules": [r.to_dict() if hasattr(r, 'to_dict') else r for r in self.processed_rules],
            "tables": [t.to_dict() for t in self.processed_tables],
            "citation_forms": [f.to_dict() for f in self.processed_citation_forms],

            # Breakdowns
            "table_breakdown": {
                "T6_common_words": len([t for t in self.processed_tables if t.table_id == "T6"]),
                "T7_court_names": len([t for t in self.processed_tables if t.table_id == "T7"]),
                "T8_explanatory_phrases": len([t for t in self.processed_tables if t.table_id == "T8"]),
                "T13_institutions": len([t for t in self.processed_tables if t.table_id == "T13"]),
                "other_tables": len([t for t in self.processed_tables if t.table_id not in ["T6", "T7", "T8", "T13"]])
            }
        }

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved comprehensive data to {output_path}")
        logger.info(f"  Rules: {data['statistics']['total_rules']}")
        logger.info(f"  Table Entries: {data['statistics']['total_table_entries']}")
        logger.info(f"  Citation Forms: {data['statistics']['total_citation_forms']}")
        logger.info(f"  TOTAL ITEMS: {data['statistics']['total_items']}")

        return output_path
