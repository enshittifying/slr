"""
R1 Cite Checking Validation Module

This module provides comprehensive citation validation for the R1 (sourcepull) phase,
adapted from the R2 pipeline with full Redbook and Bluebook compliance.
"""

from .citation_validator import CitationValidator
from .quote_verifier import QuoteVerifier
from .support_checker import SupportChecker
from .rule_retrieval import BluebookRuleRetriever, RuleEvidenceValidator
from .llm_interface import LLMInterface
from .validation_reporter import ValidationReporter

__all__ = [
    'CitationValidator',
    'QuoteVerifier',
    'SupportChecker',
    'BluebookRuleRetriever',
    'RuleEvidenceValidator',
    'LLMInterface',
    'ValidationReporter'
]
