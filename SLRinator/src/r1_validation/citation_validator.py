"""
Citation Format Validator for R1
Validates citations against Bluebook and Redbook rules
Adapted from R2 pipeline
"""
from typing import Dict, Optional, Any
import logging
import re
import json
from pathlib import Path
import sys

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.r1_validation.llm_interface import LLMInterface
from src.r1_validation.rule_retrieval import BluebookRuleRetriever, RuleEvidenceValidator
from config.validation_settings import BLUEBOOK_JSON_PATH

logger = logging.getLogger(__name__)


class Citation:
    """Citation object for validation (compatible with SLRinator's existing citation structure)."""
    def __init__(self, full_text: str, citation_type: str = "unknown",
                 footnote_num: int = 0, citation_num: int = 0):
        self.full_text = full_text
        self.type = citation_type
        self.footnote_num = footnote_num
        self.citation_num = citation_num


class CitationValidator:
    """Validate citations against Bluebook rules using hybrid deterministic + AI approach."""

    def __init__(self, llm: LLMInterface, use_deterministic_retrieval: bool = True,
                 prefer_vector_assistant: bool = True):
        self.llm = llm
        self.prefer_vector_assistant = prefer_vector_assistant
        self.prompt_template = self._load_prompt_template()
        self.bluebook_json_full = None

        # Deterministic rule retrieval
        self.use_deterministic_retrieval = use_deterministic_retrieval
        self.retriever = None
        self.evidence_validator = None

        if use_deterministic_retrieval:
            try:
                self.retriever = BluebookRuleRetriever(str(BLUEBOOK_JSON_PATH))
                self.evidence_validator = RuleEvidenceValidator(self.retriever)

                # Load full Bluebook.json for fallback
                with open(BLUEBOOK_JSON_PATH, 'r') as f:
                    bluebook_data = json.load(f)
                    self.bluebook_json_full = json.dumps(bluebook_data, indent=2)
                logger.info(f"Loaded Bluebook.json ({len(self.bluebook_json_full)} chars)")
            except Exception as e:
                logger.warning(f"Failed to initialize rule retriever: {e}")
                self.use_deterministic_retrieval = False

    def _load_prompt_template(self) -> str:
        """Load citation format prompt template."""
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "r1" / "citation_format.txt"
        try:
            with open(prompt_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"Prompt template not found at {prompt_path}")
            return self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        return """You are an expert legal citation checker. Validate the following citation against Bluebook rules.

Citation: {citation_text}
Type: {citation_type}
Context: Footnote {footnote_num}, Citation #{citation_num}, Position: {position}

Respond in JSON format with: is_correct, errors[], corrected_version, notes"""

    def _check_curly_quotes(self, text: str) -> list:
        """Deterministically check for curly quotes."""
        errors = []
        if '"' in text:
            errors.append({
                "error_type": "curly_quotes_error",
                "description": "Use curly double quotes (" ") instead of straight quotes (\" \").",
                "rb_rule": "24.4",
                "bluebook_rule": None,
                "rule_source": "redbook",
                "confidence": 1.0,
                "current": '"..."',
                "correct": '"..."'
            })
        if "'" in text:
            errors.append({
                "error_type": "curly_quotes_error",
                "description": "Use curly single quotes (' ') instead of straight quotes (').",
                "rb_rule": "24.4",
                "bluebook_rule": None,
                "rule_source": "redbook",
                "confidence": 1.0,
                "current": "'...'",
                "correct": "'...'"
            })
        return errors

    def _check_non_breaking_spaces(self, text: str) -> list:
        """Deterministically check for non-breaking spaces (Redbook 24.8)."""
        errors = []
        patterns = {
            r"([§¶])(\s)(\d)": "Symbol '{g1}' must be followed by a non-breaking space.",
            r"(\(\d+\))(\s)([A-Za-z])": "List item '{g1}' must be followed by a non-breaking space.",
            r"(\d{1,2}:\d{2})(\s)(AM|PM)": "Time '{g1}' must be followed by a non-breaking space.",
            r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.)(\s)(\d{1,2})": "Month '{g1}' must be followed by a non-breaking space.",
            r"(\w)(\s)(v\.)": "There must be a non-breaking space before 'v.' in a case name.",
            r"(\b(?:Part|Figure|Table|Title|Proposition|No\.|section|notes|art\.|cl\.|Exhibit))(\s)([A-Z0-9\.\-]+)": "Identifier '{g1}' must be followed by a non-breaking space."
        }

        for pattern, desc_template in patterns.items():
            for match in re.finditer(pattern, text):
                space_char = match.group(2)
                if space_char == ' ':
                    errors.append({
                        "error_type": "non_breaking_space_error",
                        "description": desc_template.format(g1=match.group(1)),
                        "rb_rule": "24.8",
                        "bluebook_rule": None,
                        "rule_source": "redbook",
                        "confidence": 1.0,
                        "current": match.group(0),
                        "correct": match.group(0).replace(' ', '\u00a0', 1)
                    })

        return [dict(t) for t in {tuple(sorted(d.items())) for d in errors}] if errors else []

    def _check_parenthetical_capitalization(self, text: str) -> list:
        """Check final explanatory parenthetical begins with lowercase (Bluebook 10.2.1)."""
        errors = []
        parentheticals = re.findall(r"\(([^)]+)\)", text)
        if not parentheticals:
            return []

        last_paren_text = parentheticals[-1].strip()
        if not last_paren_text:
            return []

        # Skip subsequent history
        history_terms = ['aff\'d', 'rev\'d', 'cert. denied', 'sub nom.']
        if any(term in last_paren_text for term in history_terms):
            return []

        # Skip known patterns
        if any(last_paren_text.startswith(x) for x in ['Id.', 'citing', 'quoting', 'alterations in original']):
            return []

        first_char = last_paren_text[0]

        # Quotation marks are OK
        if first_char in ('"', '"', '"', "'", "'", "'", '"', "'"):
            return []

        # Capital letter = error
        if first_char.isalpha() and first_char.isupper():
            errors.append({
                "error_type": "parenthetical_capitalization_error",
                "description": "Final explanatory parenthetical should begin with lowercase (Bluebook 10.2.1).",
                "rb_rule": "1.16",
                "bluebook_rule": "10.2.1",
                "rule_source": "bluebook",
                "confidence": 0.9,
                "current": last_paren_text,
                "correct": first_char.lower() + last_paren_text[1:]
            })

        return errors

    def validate_citation(self, citation: Citation, position: str = "middle") -> Dict:
        """Validate a single citation using hybrid deterministic + AI approach."""
        # Step 1: Deterministic checks
        quote_errors = self._check_curly_quotes(citation.full_text)
        nbsp_errors = self._check_non_breaking_spaces(citation.full_text)
        cap_errors = self._check_parenthetical_capitalization(citation.full_text)
        deterministic_errors = quote_errors + nbsp_errors + cap_errors

        # Step 2: Retrieve rules
        retrieved_rules = []
        coverage = {}
        rules_context = ""

        if self.use_deterministic_retrieval and self.retriever:
            try:
                retrieved_rules, coverage = self.retriever.retrieve_rules(
                    citation.full_text,
                    max_redbook=115,
                    max_bluebook=239
                )
                rules_context = self.retriever.format_rules_for_prompt(retrieved_rules)
                logger.info(f"Retrieved {len(retrieved_rules)} rules")
            except Exception as e:
                logger.warning(f"Rule retrieval failed: {e}")

        # Step 3: Prepare AI prompt
        user_prompt = self.prompt_template.format(
            citation_text=citation.full_text,
            citation_type=citation.type,
            footnote_num=citation.footnote_num,
            citation_num=citation.citation_num,
            position=position
        )

        if rules_context:
            user_prompt = f"{rules_context}\n\n---\n\n{user_prompt}"

        # Step 4: Call AI (prefer vector assistant)
        used_vector = False
        if self.prefer_vector_assistant and getattr(self.llm, 'assistant_id', None):
            result = self.llm.call_assistant_with_search(
                query=user_prompt,
                response_format="json",
                max_retries=8
            )
            used_vector = True
        else:
            system_prompt = self._get_system_prompt_with_all_rules()
            result = self.llm.call_gpt(system_prompt, user_prompt, response_format="json", max_retries=5)

        result["used_vector_assistant"] = used_vector
        result["rules_included"] = len(retrieved_rules)

        if not result["success"]:
            if deterministic_errors:
                return {
                    "success": True,
                    "validation": {
                        "is_correct": False,
                        "errors": deterministic_errors,
                        "corrected_version": None,
                        "notes": "AI validation failed. Showing deterministic errors only.",
                        "citation_text_original": citation.full_text,
                        "citation_type": citation.type,
                        "gpt_tokens": 0,
                        "gpt_cost": 0,
                        "coverage": coverage
                    },
                    "error": result["error"]
                }
            return {"success": False, "validation": None, "error": result["error"]}

        # Step 5: Validate evidence
        validation = result["data"]

        if self.use_deterministic_retrieval and self.evidence_validator and retrieved_rules:
            evidence_result = self.evidence_validator.require_evidence(validation, retrieved_rules)
            if not evidence_result.get("success"):
                logger.warning(f"Evidence validation failed")
                validation["evidence_validation_failed"] = True
                validation["evidence_issues"] = evidence_result.get("issues", [])

        # Step 6: Merge deterministic + AI errors
        if "errors" in validation and isinstance(validation["errors"], list):
            validation["errors"].extend(deterministic_errors)
        else:
            validation["errors"] = deterministic_errors

        if validation["errors"]:
            validation["is_correct"] = False

        validation["citation_text_original"] = citation.full_text
        validation["citation_type"] = citation.type
        validation["gpt_tokens"] = result["tokens"]
        validation["gpt_cost"] = result["cost"]
        validation["coverage"] = coverage
        validation["rules_retrieved"] = len(retrieved_rules)

        return {"success": True, "validation": validation, "error": None}

    def _get_system_prompt_with_all_rules(self) -> str:
        """System prompt for GPT with all rules."""
        return """You are an expert in Bluebook (21st edition) citation formatting.

**RULE PRIORITY (CRITICAL)**:
- REDBOOK RULES TAKE PRECEDENCE over Bluebook rules
- Always cite Redbook rule numbers first
- Only use Bluebook rules when Redbook doesn't address the issue

**YOUR TASK**:
1. Analyze the citation against ALL provided rules
2. Identify ANY formatting violations
3. Cite specific rule numbers for each error (Redbook first!)
4. Provide precise corrections

**CRITICAL for Law Journal Quality**:
- Flag ALL violations (this is for publication)
- Be thorough
- Cite exact rule numbers
- Only create errors backed by cited rules
- Prioritize Redbook citations

The user message contains the complete rule set followed by the citation to validate."""

    def validate_batch(self, citations: list) -> Dict:
        """Validate multiple citations."""
        results = []
        for citation in citations:
            results.append(self.validate_citation(citation))
        return {"results": results}
