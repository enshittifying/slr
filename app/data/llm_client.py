"""
LLM client interface for OpenAI and Anthropic
"""
from abc import ABC, abstractmethod
from typing import Dict, List
import openai
import anthropic
import logging

from ..utils.retry import retry_api_call

logger = logging.getLogger(__name__)


class LLMClient(ABC):
    """Abstract LLM client interface"""

    @abstractmethod
    def check_format(self, citation_text: str, format_rules: dict, prompt_template: str) -> dict:
        """Check citation format"""
        pass

    @abstractmethod
    def check_support(self, proposition: str, source_text: str, citation_text: str,
                     prompt_template: str) -> dict:
        """Check if source supports proposition"""
        pass


class OpenAIClient(LLMClient):
    """OpenAI API client"""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize OpenAI client

        Args:
            api_key: OpenAI API key
            model: Model to use
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    @retry_api_call
    def check_format(self, citation_text: str, format_rules: dict, prompt_template: str) -> dict:
        """
        Check citation format using GPT

        Args:
            citation_text: Citation to check
            format_rules: Bluebook rules
            prompt_template: Prompt template with {citation} and {bluebook_rules} placeholders

        Returns:
            Dict with 'issues' and 'suggestion' fields
        """
        prompt = prompt_template.format(
            citation=citation_text,
            bluebook_rules=str(format_rules)
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Bluebook citation expert. Analyze citations and return JSON with 'issues' (list of problems) and 'suggestion' (corrected citation)."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Format check completed for: {citation_text[:50]}...")
            return result

        except Exception as e:
            logger.error(f"OpenAI format check failed: {e}")
            return {"issues": [f"API Error: {str(e)}"], "suggestion": ""}

    @retry_api_call
    def check_support(self, proposition: str, source_text: str, citation_text: str,
                     prompt_template: str) -> dict:
        """
        Check if source supports proposition

        Args:
            proposition: Claim being made
            source_text: Text from source document
            citation_text: Citation
            prompt_template: Prompt template

        Returns:
            Dict with 'issues' and 'confidence' fields
        """
        prompt = prompt_template.format(
            proposition=proposition,
            source_text=source_text[:4000],  # Limit context
            citation=citation_text
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a legal research expert. Analyze whether a source supports a proposition. Return JSON with 'issues' (list of problems) and 'confidence' (score 0-100)."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Support check completed for: {citation_text[:50]}...")
            return result

        except Exception as e:
            logger.error(f"OpenAI support check failed: {e}")
            return {"issues": [f"API Error: {str(e)}"], "confidence": 0}


class AnthropicClient(LLMClient):
    """Anthropic API client"""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize Anthropic client

        Args:
            api_key: Anthropic API key
            model: Model to use
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    @retry_api_call
    def check_format(self, citation_text: str, format_rules: dict, prompt_template: str) -> dict:
        """
        Check citation format using Claude

        Args:
            citation_text: Citation to check
            format_rules: Bluebook rules
            prompt_template: Prompt template

        Returns:
            Dict with 'issues' and 'suggestion' fields
        """
        prompt = prompt_template.format(
            citation=citation_text,
            bluebook_rules=str(format_rules)
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": f"You are a Bluebook citation expert. Analyze this citation and return JSON with 'issues' (list of problems) and 'suggestion' (corrected citation).\n\n{prompt}"
                }]
            )

            import json
            # Extract JSON from response
            content = response.content[0].text
            # Find JSON block
            if '```json' in content:
                json_str = content.split('```json')[1].split('```')[0].strip()
            elif '{' in content:
                json_str = content[content.find('{'):content.rfind('}')+1]
            else:
                json_str = content

            result = json.loads(json_str)
            logger.info(f"Format check completed for: {citation_text[:50]}...")
            return result

        except Exception as e:
            logger.error(f"Anthropic format check failed: {e}")
            return {"issues": [f"API Error: {str(e)}"], "suggestion": ""}

    @retry_api_call
    def check_support(self, proposition: str, source_text: str, citation_text: str,
                     prompt_template: str) -> dict:
        """
        Check if source supports proposition

        Args:
            proposition: Claim being made
            source_text: Text from source document
            citation_text: Citation
            prompt_template: Prompt template

        Returns:
            Dict with 'issues' and 'confidence' fields
        """
        prompt = prompt_template.format(
            proposition=proposition,
            source_text=source_text[:4000],
            citation=citation_text
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": f"You are a legal research expert. Analyze whether this source supports the proposition. Return JSON with 'issues' (list of problems) and 'confidence' (score 0-100).\n\n{prompt}"
                }]
            )

            import json
            content = response.content[0].text
            if '```json' in content:
                json_str = content.split('```json')[1].split('```')[0].strip()
            elif '{' in content:
                json_str = content[content.find('{'):content.rfind('}')+1]
            else:
                json_str = content

            result = json.loads(json_str)
            logger.info(f"Support check completed for: {citation_text[:50]}...")
            return result

        except Exception as e:
            logger.error(f"Anthropic support check failed: {e}")
            return {"issues": [f"API Error: {str(e)}"], "confidence": 0}


def create_llm_client(provider: str, api_key: str, model: str = None) -> LLMClient:
    """
    Factory function to create LLM client

    Args:
        provider: 'openai' or 'anthropic'
        api_key: API key
        model: Model name (optional)

    Returns:
        LLM client instance
    """
    if provider.lower() == 'openai':
        return OpenAIClient(api_key, model or "gpt-4o-mini")
    elif provider.lower() == 'anthropic':
        return AnthropicClient(api_key, model or "claude-3-5-sonnet-20241022")
    else:
        raise ValueError(f"Unknown provider: {provider}")
