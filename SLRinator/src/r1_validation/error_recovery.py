"""
Error Recovery and Resilience System for R1 Validation
Provides comprehensive error handling, retry mechanisms, and graceful degradation
"""
import time
import logging
import functools
from typing import Callable, Any, Dict, Optional, Type
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "critical"  # System cannot continue
    MAJOR = "major"       # Feature unavailable, can continue with degradation
    MINOR = "minor"       # Non-critical issue, full functionality available
    WARNING = "warning"   # Potential issue, no impact


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types."""
    RETRY = "retry"                    # Retry with exponential backoff
    FALLBACK = "fallback"              # Use fallback mechanism
    SKIP = "skip"                      # Skip and continue
    FAIL_FAST = "fail_fast"           # Fail immediately
    DEGRADE = "degrade"               # Continue with reduced functionality


@dataclass
class ErrorContext:
    """Context information for an error."""
    error_type: str
    error_message: str
    severity: ErrorSeverity
    recovery_strategy: RecoveryStrategy
    attempt_number: int
    max_attempts: int
    citation_num: Optional[int] = None
    footnote_num: Optional[int] = None
    additional_info: Optional[Dict] = None


class CircuitBreaker:
    """
    Circuit breaker pattern for API calls.
    Prevents cascading failures by stopping requests after repeated failures.
    """

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting to close circuit
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to call
            *args, **kwargs: Arguments for function

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == "open":
            if time.time() - self.last_failure_time < self.timeout:
                raise Exception("Circuit breaker is OPEN - too many recent failures")
            else:
                # Try to close circuit
                self.state = "half_open"
                logger.info("Circuit breaker entering HALF_OPEN state")

        try:
            result = func(*args, **kwargs)
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
                logger.info("Circuit breaker CLOSED - service recovered")
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error(f"Circuit breaker OPEN after {self.failure_count} failures")

            raise e

    def reset(self):
        """Manually reset circuit breaker."""
        self.state = "closed"
        self.failure_count = 0
        self.last_failure_time = None
        logger.info("Circuit breaker manually reset")


class RetryManager:
    """Manages retry logic with exponential backoff and jitter."""

    @staticmethod
    def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
        """
        Calculate exponential backoff delay with jitter.

        Args:
            attempt: Current attempt number (0-indexed)
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds

        Returns:
            Delay in seconds
        """
        import random
        delay = min(base_delay * (2 ** attempt), max_delay)
        # Add jitter (±20%)
        jitter = delay * 0.2 * (2 * random.random() - 1)
        return delay + jitter

    @staticmethod
    def retry_with_backoff(
        func: Callable,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exceptions: tuple = (Exception,),
        on_retry: Optional[Callable] = None
    ) -> Any:
        """
        Retry function with exponential backoff.

        Args:
            func: Function to retry
            max_attempts: Maximum number of attempts
            base_delay: Base delay between retries
            max_delay: Maximum delay between retries
            exceptions: Tuple of exceptions to catch
            on_retry: Callback called on each retry

        Returns:
            Function result

        Raises:
            Exception: If all retries exhausted
        """
        last_exception = None

        for attempt in range(max_attempts):
            try:
                return func()
            except exceptions as e:
                last_exception = e
                if attempt < max_attempts - 1:
                    delay = RetryManager.exponential_backoff(attempt, base_delay, max_delay)
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    if on_retry:
                        on_retry(attempt, e, delay)
                    time.sleep(delay)
                else:
                    logger.error(f"All {max_attempts} attempts failed")

        raise last_exception


class GracefulDegradation:
    """Manages graceful degradation when features fail."""

    def __init__(self):
        self.degraded_features = set()
        self.degradation_reasons = {}

    def degrade_feature(self, feature_name: str, reason: str):
        """
        Mark a feature as degraded.

        Args:
            feature_name: Name of the feature
            reason: Reason for degradation
        """
        self.degraded_features.add(feature_name)
        self.degradation_reasons[feature_name] = reason
        logger.warning(f"Feature degraded: {feature_name} - {reason}")

    def restore_feature(self, feature_name: str):
        """
        Restore a degraded feature.

        Args:
            feature_name: Name of the feature
        """
        if feature_name in self.degraded_features:
            self.degraded_features.remove(feature_name)
            del self.degradation_reasons[feature_name]
            logger.info(f"Feature restored: {feature_name}")

    def is_degraded(self, feature_name: str) -> bool:
        """Check if a feature is degraded."""
        return feature_name in self.degraded_features

    def get_status(self) -> Dict:
        """Get degradation status."""
        return {
            "degraded_features": list(self.degraded_features),
            "reasons": self.degradation_reasons,
            "fully_operational": len(self.degraded_features) == 0
        }


class ErrorRecoveryManager:
    """Central manager for error recovery across the R1 system."""

    def __init__(self, checkpoint_dir: Path = None):
        """
        Initialize error recovery manager.

        Args:
            checkpoint_dir: Directory for saving checkpoints
        """
        self.checkpoint_dir = checkpoint_dir or Path.cwd() / "output" / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.circuit_breaker = CircuitBreaker()
        self.degradation = GracefulDegradation()
        self.error_log = []

    def log_error(self, context: ErrorContext):
        """
        Log an error with full context.

        Args:
            context: Error context
        """
        self.error_log.append({
            "timestamp": time.time(),
            "error_type": context.error_type,
            "message": context.error_message,
            "severity": context.severity.value,
            "strategy": context.recovery_strategy.value,
            "attempt": context.attempt_number,
            "citation": context.citation_num,
            "footnote": context.footnote_num,
            "info": context.additional_info
        })

        # Log to file
        log_level = {
            ErrorSeverity.CRITICAL: logging.CRITICAL,
            ErrorSeverity.MAJOR: logging.ERROR,
            ErrorSeverity.MINOR: logging.WARNING,
            ErrorSeverity.WARNING: logging.INFO
        }.get(context.severity, logging.INFO)

        logger.log(
            log_level,
            f"[{context.severity.value.upper()}] {context.error_type}: {context.error_message}"
        )

    def save_checkpoint(self, checkpoint_name: str, data: Dict):
        """
        Save checkpoint for recovery.

        Args:
            checkpoint_name: Name of checkpoint
            data: Data to save
        """
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_name}.json"
        with open(checkpoint_path, 'w') as f:
            json.dump({
                "timestamp": time.time(),
                "data": data
            }, f, indent=2)
        logger.info(f"Checkpoint saved: {checkpoint_path}")

    def load_checkpoint(self, checkpoint_name: str) -> Optional[Dict]:
        """
        Load checkpoint for recovery.

        Args:
            checkpoint_name: Name of checkpoint

        Returns:
            Checkpoint data or None
        """
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_name}.json"
        if checkpoint_path.exists():
            with open(checkpoint_path, 'r') as f:
                checkpoint = json.load(f)
            logger.info(f"Checkpoint loaded: {checkpoint_path}")
            return checkpoint.get("data")
        return None

    def get_error_summary(self) -> Dict:
        """Get summary of all errors."""
        if not self.error_log:
            return {"total_errors": 0}

        by_severity = {}
        by_type = {}

        for error in self.error_log:
            severity = error["severity"]
            error_type = error["error_type"]

            by_severity[severity] = by_severity.get(severity, 0) + 1
            by_type[error_type] = by_type.get(error_type, 0) + 1

        return {
            "total_errors": len(self.error_log),
            "by_severity": by_severity,
            "by_type": by_type,
            "recent_errors": self.error_log[-10:],  # Last 10 errors
            "degradation_status": self.degradation.get_status()
        }


def with_retry(max_attempts: int = 3, base_delay: float = 1.0):
    """
    Decorator for automatic retry with exponential backoff.

    Args:
        max_attempts: Maximum retry attempts
        base_delay: Base delay between retries

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return RetryManager.retry_with_backoff(
                lambda: func(*args, **kwargs),
                max_attempts=max_attempts,
                base_delay=base_delay
            )
        return wrapper
    return decorator


def with_fallback(fallback_func: Callable):
    """
    Decorator to provide fallback function on error.

    Args:
        fallback_func: Function to call if primary fails

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Primary function failed: {e}. Using fallback.")
                return fallback_func(*args, **kwargs)
        return wrapper
    return decorator


def resilient_call(
    func: Callable,
    error_recovery: ErrorRecoveryManager,
    citation_num: Optional[int] = None,
    footnote_num: Optional[int] = None,
    max_attempts: int = 3
) -> Dict[str, Any]:
    """
    Execute function with full error recovery support.

    Args:
        func: Function to execute
        error_recovery: Error recovery manager
        citation_num: Citation number for context
        footnote_num: Footnote number for context
        max_attempts: Maximum retry attempts

    Returns:
        Result dict with success status
    """
    for attempt in range(max_attempts):
        try:
            result = error_recovery.circuit_breaker.call(func)
            return {
                "success": True,
                "result": result,
                "attempts": attempt + 1
            }
        except Exception as e:
            context = ErrorContext(
                error_type=type(e).__name__,
                error_message=str(e),
                severity=ErrorSeverity.MAJOR,
                recovery_strategy=RecoveryStrategy.RETRY,
                attempt_number=attempt + 1,
                max_attempts=max_attempts,
                citation_num=citation_num,
                footnote_num=footnote_num
            )
            error_recovery.log_error(context)

            if attempt < max_attempts - 1:
                delay = RetryManager.exponential_backoff(attempt)
                time.sleep(delay)
            else:
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "attempts": max_attempts
                }
