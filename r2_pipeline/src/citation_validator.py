"""
Validate citation formatting using GPT-4o-mini.
"""
from typing import Dict, Optional
import logging
import re
import json
from pathlib import Path
from src.llm_interface import LLMInterface
from src.citation_parser import Citation
from src.rule_retrieval import BluebookRuleRetriever, RuleEvidenceValidator
from config.settings import BLUEBOOK_JSON_PATH

logger = logging.getLogger(__name__)

class CitationValidator:
    """Validate citations against Bluebook rules using LLM.
    Prefers vector-assistant with File Search when available, falls back to direct LLM calls.
    """

    def __init__(self, llm: LLMInterface, use_deterministic_retrieval: bool = True, prefer_vector_assistant: bool = True):
        self.llm = llm
        self.prefer_vector_assistant = prefer_vector_assistant
        self.prompt_template = self._load_prompt_template()
        self.bluebook_json_full = None  # Full Bluebook.json text for fallback

        # Initialize deterministic rule retrieval
        self.use_deterministic_retrieval = use_deterministic_retrieval
        self.retriever = None
        self.evidence_validator = None

        if use_deterministic_retrieval:
            try:
                self.retriever = BluebookRuleRetriever(str(BLUEBOOK_JSON_PATH))
                self.evidence_validator = RuleEvidenceValidator(self.retriever)

                # Load full Bluebook.json for fallback to regular GPT
                with open(BLUEBOOK_JSON_PATH, 'r') as f:
                    bluebook_data = json.load(f)
                    self.bluebook_json_full = json.dumps(bluebook_data, indent=2)
                logger.info(f"Loaded full Bluebook.json ({len(self.bluebook_json_full)} chars) for GPT fallback")
                logger.info("Deterministic rule retrieval enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize rule retriever: {e}. Falling back to vector search only.")
                self.use_deterministic_retrieval = False

    def _load_prompt_template(self) -> str:
        """Load citation format prompt template."""
        prompt_path = Path(__file__).parent.parent / "prompts" / "citation_format.txt"
        try:
            with open(prompt_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"Prompt template not found at {prompt_path}")
            return self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        return """You are an expert legal citation checker...""" # Abridged

    def _check_curly_quotes(self, text: str) -> list:
        """Deterministically check for straight vs. curly quotes."""
        errors = []
        if '"' in text:
            errors.append({
                "error_type": "curly_quotes_error",
                "description": "The citation contains straight double quotes (\" ) instead of curly double quotes (\u201c \u201d).",
                "rb_rule": "24.4", "bluebook_rule": None, "rule_source": "redbook", "confidence": 1.0,
                "current": '"..."', "correct": '“...”'
            })
        if "'" in text:
            errors.append({
                "error_type": "curly_quotes_error",
                "description": "The citation contains straight single quotes (') instead of curly single quotes (\u2018 \u2019).",
                "rb_rule": "24.4", "bluebook_rule": None, "rule_source": "redbook", "confidence": 1.0,
                "current": "'... '", "correct": "‘...’"
            })
        return errors

    def _check_non_breaking_spaces(self, text: str) -> list:
        """Deterministically check for non-breaking spaces based on Redbook 24.8."""
        errors = []
        patterns = {
            r"([§¶])(\s)(\d)": ("Symbol '{g1}' must be followed by a non-breaking space."),
            r"(\(\d+\))(\s)([A-Za-z])": ("List item '{g1}' must be followed by a non-breaking space."),
            r"(\d{1,2}:\d{2})(\s)(AM|PM)": ("Time '{g1}' must be followed by a non-breaking space."),
            r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.)(\s)(\d{1,2})": ("Month '{g1}' must be followed by a non-breaking space."),
            r"(\w)(\s)(v\.)": ("There must be a non-breaking space before 'v.' in a case name."),
            r"(\b(?:Part|Figure|Table|Title|Proposition|No\.|section|notes|art\.|cl\.|Exhibit))(\s)([A-Z0-9\.\-]+)": ("Identifier '{g1}' must be followed by a non-breaking space.")
        }

        for pattern, desc_template in patterns.items():
            for match in re.finditer(pattern, text):
                space_char = match.group(2)
                if space_char == ' ':
                    errors.append({
                        "error_type": "non_breaking_space_error",
                        "description": desc_template.format(g1=match.group(1)),
                        "rb_rule": "24.8", "bluebook_rule": None, "rule_source": "redbook", "confidence": 1.0,
                        "current": match.group(0),
                        "correct": match.group(0).replace(' ', '\u00a0', 1)
                    })
        
        if not errors:
            return []
        return [dict(t) for t in {tuple(sorted(d.items())) for d in errors}]

    def _check_parenthetical_capitalization(self, text: str) -> list:
        """
        Check that the final explanatory parenthetical begins with lowercase.

        RULE: For the LAST parenthetical, check the FIRST character after (:
        - If it's a CAPITAL LETTER → FLAG IT
        - If it's lowercase → CORRECT
        - If it's a quotation mark → CORRECT (direct quote)
        """
        errors = []

        # Find all parentheticals - rule applies only to last one
        parentheticals = re.findall(r"\(([^)]+)\)", text)
        if not parentheticals:
            return []

        last_paren_text = parentheticals[-1].strip()
        if not last_paren_text:
            return []

        # Skip subsequent history parentheticals
        history_terms = ['aff\'d', 'rev\'d', 'cert. denied', 'sub nom.']
        if any(term in last_paren_text for term in history_terms):
            return []

        # Skip known legal citation patterns
        if any(last_paren_text.startswith(x) for x in ['Id.', 'citing', 'quoting', 'alterations in original']):
            return []

        # THE RULE: Check first character
        first_char = last_paren_text[0]

        # If it's a quotation mark → CORRECT (direct quote)
        if first_char in ('"', '"', '"', "'", "'", "'", '"', "'"):
            return []

        # If it's a CAPITAL LETTER → FLAG IT
        if first_char.isalpha() and first_char.isupper():
            errors.append({
                "error_type": "parenthetical_capitalization_error",
                "description": "The final explanatory parenthetical phrase should begin with a lowercase letter (Bluebook 10.2.1).",
                "rb_rule": "1.16",
                "bluebook_rule": "10.2.1",
                "rule_source": "bluebook",
                "confidence": 0.9,
                "current": last_paren_text,
                "correct": first_char.lower() + last_paren_text[1:]
            })

        return errors

    def validate_citation(self, citation: Citation, position: str = "middle") -> Dict:
        """Validate a single citation using a hybrid deterministic and AI approach."""
        # Step 1: Deterministically check for errors that don't require AI.
        quote_errors = self._check_curly_quotes(citation.full_text)
        nbsp_errors = self._check_non_breaking_spaces(citation.full_text)
        cap_errors = self._check_parenthetical_capitalization(citation.full_text)
        deterministic_errors = quote_errors + nbsp_errors + cap_errors

        # Step 2: Retrieve relevant rules (if deterministic retrieval enabled)
        retrieved_rules = []
        coverage = {}
        rules_context = ""

        if self.use_deterministic_retrieval and self.retriever:
            try:
                # Retrieve ALL rules (115 Redbook + 239 Bluebook) for comprehensive validation
                retrieved_rules, coverage = self.retriever.retrieve_rules(
                    citation.full_text,
                    max_redbook=115,
                    max_bluebook=239
                )
                rules_context = self.retriever.format_rules_for_prompt(retrieved_rules)
                logger.info(f"Retrieved ALL {len(retrieved_rules)} rules for comprehensive validation")
            except Exception as e:
                logger.warning(f"Rule retrieval failed: {e}. Proceeding without deterministic retrieval.")

        # Step 3: Prepare prompt for AI to check for other, more subjective errors.
        user_prompt = self.prompt_template.format(
            citation_text=citation.full_text, citation_type=citation.type,
            footnote_num=citation.footnote_num, citation_num=citation.citation_num, position=position
        )

        # Add retrieved rules to prompt if available
        if rules_context:
            user_prompt = f"{rules_context}\n\n---\n\n{user_prompt}"

        # Step 4: Prefer vector assistant with File Search if available
        used_vector = False
        if self.prefer_vector_assistant and getattr(self.llm, 'assistant_id', None):
            # Send the composed prompt as the query; assistant has File Search + instructions
            result = self.llm.call_assistant_with_search(
                query=user_prompt,
                response_format="json",
                max_retries=8
            )
            used_vector = True
        else:
            # Fallback: direct Chat Completions with retrieved rules context
            system_prompt = self._get_system_prompt_with_all_rules()
            result = self.llm.call_gpt(system_prompt, user_prompt, response_format="json", max_retries=5)

        # Annotate result for downstream awareness
        result["used_vector_assistant"] = used_vector
        result["has_all_rules"] = False
        result["rules_included"] = len(retrieved_rules)

        if not result["success"]:
            if deterministic_errors:
                 return {
                    "success": True,
                    "validation": {
                        "is_correct": False, "errors": deterministic_errors, "corrected_version": None,
                        "notes": "AI validation failed. Errors shown are from deterministic checks only.",
                        "citation_text_original": citation.full_text, "citation_type": citation.type,
                        "gpt_tokens": 0, "gpt_cost": 0, "coverage": coverage
                    },
                    "error": result["error"]
                }
            return { "success": False, "validation": None, "error": result["error"] }

        # Step 5: Validate evidence if deterministic retrieval was used
        validation = result["data"]

        if self.use_deterministic_retrieval and self.evidence_validator and retrieved_rules:
            evidence_result = self.evidence_validator.require_evidence(validation, retrieved_rules)

            if not evidence_result.get("success"):
                logger.warning(f"Evidence validation failed: {evidence_result.get('issues')}")
                # Mark response as needing review
                validation["evidence_validation_failed"] = True
                validation["evidence_issues"] = evidence_result.get("issues", [])
                # Don't reject completely - still merge with deterministic errors

        # If vector assistant wasn't used, note lack of direct file access
        if not result.get("used_vector_assistant"):
            validation["file_access_status"] = "no_file_access"
            validation["notes"] = validation.get("notes", "") + " [Validated without Bluebook File Search]"

        # Step 6: Merge deterministic errors with AI-found errors.
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
        """Get system prompt for GPT-5-nano with ALL 354 rules included."""
        return """You are an expert in Bluebook (21st edition) citation formatting for law journal validation.

You have been provided with ALL 354 Bluebook and Redbook rules in the user message.
This is COMPREHENSIVE coverage - every rule from both sources is included.

**RULE PRIORITY (CRITICAL)**:
- **REDBOOK RULES TAKE PRECEDENCE** over Bluebook rules when they conflict
- Always cite Redbook rule numbers first
- Only use Bluebook rules when Redbook doesn't address the issue

**YOUR TASK**:
1. Analyze the citation against ALL provided rules
2. Identify ANY formatting violations, no matter how minor
3. Cite the specific rule number(s) for each error (Redbook first!)
4. Provide precise corrections

**CRITICAL for Law Journal Quality**:
- Flag ALL violations (this is for publication)
- Be thorough - check every aspect of the citation
- Cite exact rule numbers from the provided rules
- Only create errors you can back up with a cited rule
- **Prioritize Redbook citations** when applicable

The user message contains the complete rule set followed by the citation to validate."""

    def validate_batch(self, citations: list) -> Dict:
        """Validate multiple citations with progress tracking."""
        results = []
        for citation in citations:
            results.append(self.validate_citation(citation))
        return {"results": results}
