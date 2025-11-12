"""LLM-powered proposition support checking."""

import os
from typing import Dict, Any
from openai import OpenAI
from anthropic import Anthropic

from shared_utils.logger import get_logger

logger = get_logger(__name__)


class SupportChecker:
    """Check if source text supports the legal proposition."""

    def __init__(self, model: str = "gpt-4"):
        self.model = model
        if "gpt" in model:
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif "claude" in model:
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def check_support(self, proposition: str, source_text: str) -> Dict[str, Any]:
        """
        Check if source text supports the proposition.

        Returns:
            Dictionary with 'supported', 'explanation', 'confidence'
        """
        try:
            prompt = f"""Does the following source text support the legal proposition?

Proposition: {proposition}

Source Text: {source_text[:2000]}

Provide:
1. Whether the source supports the proposition (yes/no)
2. Explanation of your reasoning
3. Confidence level (0-100%)"""

            if "gpt" in self.model:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                )
                result_text = response.choices[0].message.content
            else:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                )
                result_text = response.content[0].text

            # Parse response
            supported = "yes" in result_text.lower() or "supported" in result_text.lower()
            
            return {
                "supported": supported,
                "explanation": result_text,
                "confidence": 85 if supported else 60,
            }

        except Exception as e:
            logger.error(f"Support check failed: {e}")
            return {"supported": False, "explanation": str(e), "confidence": 0}
