"""Quote accuracy verification."""

from typing import Dict, Any, List
from difflib import SequenceMatcher

from shared_utils.logger import get_logger

logger = get_logger(__name__)


class QuoteVerifier:
    """Verify quoted text accuracy character-by-character."""

    def verify_quotes(self, article_quotes: List[str], source_text: str) -> Dict[str, Any]:
        """
        Verify that quoted text matches source exactly.

        Returns:
            Dictionary with 'all_accurate' and 'errors'
        """
        errors = []

        for i, quote in enumerate(article_quotes):
            if quote not in source_text:
                # Find closest match
                similarity = self._find_similarity(quote, source_text)
                errors.append({
                    "quote_number": i + 1,
                    "quote": quote[:50] + "...",
                    "error": "Quote not found in source",
                    "similarity": similarity,
                })

        return {
            "all_accurate": len(errors) == 0,
            "errors": errors,
        }

    def _find_similarity(self, quote: str, source: str) -> float:
        """Find similarity between quote and closest match in source."""
        matcher = SequenceMatcher(None, quote, source)
        return matcher.ratio() * 100
