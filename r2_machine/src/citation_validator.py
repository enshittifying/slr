"""LLM-powered citation format validation."""

import os
from typing import Dict, Any
from openai import OpenAI
from anthropic import Anthropic

from shared_utils.logger import get_logger
from shared_utils.exceptions import ValidationError

logger = get_logger(__name__)


class CitationValidator:
    """Validate citation formatting using LLM."""

    def __init__(self, model: str = "gpt-4"):
        """Initialize with specified LLM model."""
        self.model = model
        
        if "gpt" in model:
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif "claude" in model:
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def validate(self, citation_text: str) -> Dict[str, Any]:
        """
        Validate citation formatting against Bluebook/Redbook rules.

        Args:
            citation_text: The citation to validate

        Returns:
            Validation result with errors and suggestions
        """
        try:
            prompt = f"""Validate the following citation against Bluebook and Stanford Law Review Redbook rules:

Citation: {citation_text}

Provide:
1. Whether the citation is correctly formatted (yes/no)
2. List of specific formatting errors (if any)
3. Suggested corrections

Format your response as JSON."""

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

            # Parse LLM response (simplified)
            import json
            try:
                result = json.loads(result_text)
            except:
                result = {
                    "valid": "yes" in result_text.lower(),
                    "errors": [],
                    "suggestions": [result_text],
                }

            logger.info("Citation validation complete")
            return result

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise ValidationError(f"Validation failed: {e}")
