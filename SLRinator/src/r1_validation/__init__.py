"""
R1 Cite Checking Validation Module

This module provides comprehensive citation validation for the R1 (sourcepull) phase,
adapted from the R2 pipeline with full Redbook and Bluebook compliance.
"""

# Core validation components
from .citation_validator import CitationValidator
from .quote_verifier import QuoteVerifier
from .support_checker import SupportChecker
from .rule_retrieval import BluebookRuleRetriever, RuleEvidenceValidator
from .llm_interface import LLMInterface
from .validation_reporter import ValidationReporter

# Robustness and resilience components
from .error_recovery import (
    ErrorRecoveryManager,
    CircuitBreaker,
    RetryManager,
    GracefulDegradation,
    ErrorContext,
    ErrorSeverity,
    RecoveryStrategy,
    with_retry,
    with_fallback,
    resilient_call
)
from .progress_tracker import (
    ProgressTracker,
    WorkflowProgress,
    CitationProgress
)
from .health_check import (
    HealthCheckManager,
    HealthStatus,
    ComponentType,
    HealthCheckResult,
    SystemHealth
)
from .logging_config import (
    setup_logging,
    StructuredFormatter,
    PerformanceLogger,
    AuditLogger,
    CostTracker,
    log_function_call,
    log_citation_processing
)
from .input_validation import (
    InputValidator,
    ValidationResult,
    ValidationError,
    ValidationSeverity
)
from .resource_monitor import (
    ResourceMonitor,
    BackgroundResourceMonitor,
    ResourceLimits,
    ResourceSnapshot,
    ResourceError,
    with_resource_check,
    monitor_resources,
    check_sufficient_resources
)

__all__ = [
    # Core validation
    'CitationValidator',
    'QuoteVerifier',
    'SupportChecker',
    'BluebookRuleRetriever',
    'RuleEvidenceValidator',
    'LLMInterface',
    'ValidationReporter',

    # Error recovery
    'ErrorRecoveryManager',
    'CircuitBreaker',
    'RetryManager',
    'GracefulDegradation',
    'ErrorContext',
    'ErrorSeverity',
    'RecoveryStrategy',
    'with_retry',
    'with_fallback',
    'resilient_call',

    # Progress tracking
    'ProgressTracker',
    'WorkflowProgress',
    'CitationProgress',

    # Health checks
    'HealthCheckManager',
    'HealthStatus',
    'ComponentType',
    'HealthCheckResult',
    'SystemHealth',

    # Logging
    'setup_logging',
    'StructuredFormatter',
    'PerformanceLogger',
    'AuditLogger',
    'CostTracker',
    'log_function_call',
    'log_citation_processing',

    # Input validation
    'InputValidator',
    'ValidationResult',
    'ValidationError',
    'ValidationSeverity',

    # Resource monitoring
    'ResourceMonitor',
    'BackgroundResourceMonitor',
    'ResourceLimits',
    'ResourceSnapshot',
    'ResourceError',
    'with_resource_check',
    'monitor_resources',
    'check_sufficient_resources'
]
