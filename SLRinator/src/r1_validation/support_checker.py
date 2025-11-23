"""
Support Checker for R1
Checks if redboxed source text supports the main text proposition
Adapted from R2 pipeline
"""
from typing import Dict
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.r1_validation.llm_interface import LLMInterface

logger = logging.getLogger(__name__)


class SupportChecker:
    """Check if source supports proposition using LLM."""

    def __init__(self, llm: LLMInterface):
        self.llm = llm
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load support check prompt template."""
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "r1" / "support_check.txt"
        try:
            with open(prompt_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.warning(f"Prompt template not found at {prompt_path}")
            return self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """Return default prompt if file not found."""
        return """Evaluate if the source text supports the proposition.

Proposition: {proposition}
Source text: {source_text}

Respond in JSON with:
- support_level: "yes" | "maybe" | "no"
- confidence: float
- reasoning: string
- supported_elements: list
- unsupported_elements: list
- suggested_action: string
- missing_context: string
"""

    def check_support(self,
                     proposition: str,
                     source_text: str,
                     citation_text: str,
                     context: Dict = None) -> Dict:
        """
        Check if source supports proposition.

        Args:
            proposition: Main text claim
            source_text: Text from redboxed source
            citation_text: Full citation
            context: Additional context (optional)

        Returns:
            Dict with support analysis
        """
        system_prompt = """You are a legal research expert. Carefully evaluate whether source text
supports a legal proposition. Be rigorous - require DIRECT support, not just tangential relevance."""

        user_prompt = self.prompt_template.format(
            proposition=proposition,
            source_text=source_text,
            citation_text=citation_text
        )

        result = self.llm.call_gpt(system_prompt, user_prompt, response_format="json")

        if not result["success"]:
            logger.error(f"GPT call failed for support check: {result['error']}")
            return {
                "success": False,
                "analysis": None,
                "error": result["error"]
            }

        analysis = result["data"]
        analysis["proposition"] = proposition
        analysis["source_text_preview"] = source_text[:200] + "..." if len(source_text) > 200 else source_text
        analysis["gpt_tokens"] = result["tokens"]
        analysis["gpt_cost"] = result["cost"]

        return {
            "success": True,
            "analysis": analysis,
            "error": None
        }

    def check_batch(self, checks: list) -> Dict:
        """
        Check multiple proposition-source pairs.

        Args:
            checks: List of dicts with 'proposition', 'source_text', 'citation_text'

        Returns:
            Dict with batch results
        """
        results = []
        total_cost = 0.0
        total_tokens = 0

        for check in checks:
            result = self.check_support(
                proposition=check["proposition"],
                source_text=check["source_text"],
                citation_text=check["citation_text"],
                context=check.get("context")
            )
            results.append(result)

            if result["success"]:
                total_cost += result["analysis"]["gpt_cost"]
                total_tokens += result["analysis"]["gpt_tokens"]

        support_levels = [r["analysis"]["support_level"] for r in results if r["success"]]

        return {
            "results": results,
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "success_rate": sum(1 for r in results if r["success"]) / len(results) if results else 0,
            "support_breakdown": {
                "yes": support_levels.count("yes"),
                "maybe": support_levels.count("maybe"),
                "no": support_levels.count("no")
            }
        }
