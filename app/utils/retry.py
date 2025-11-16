"""
Retry logic with exponential backoff
Comprehensive error handling for API calls and network operations
"""
import time
import logging
import functools
from typing import Callable, TypeVar, Optional, Tuple, Type
import random

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior"""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        """
        Initialize retry configuration

        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay between retries (seconds)
            max_delay: Maximum delay between retries (seconds)
            exponential_base: Base for exponential backoff (2.0 = double each time)
            jitter: Add random jitter to delay
            retryable_exceptions: Tuple of exception types to retry on
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )

        if self.jitter:
            # Add random jitter (±25%)
            jitter_amount = delay * 0.25
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)


def with_retry(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
):
    """
    Decorator to add retry logic to a function

    Args:
        config: RetryConfig instance (uses defaults if None)
        on_retry: Optional callback called on each retry(exception, attempt, delay)

    Example:
        @with_retry(RetryConfig(max_attempts=5))
        def fetch_data():
            return api.get_data()
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)

                except config.retryable_exceptions as e:
                    last_exception = e

                    if attempt < config.max_attempts - 1:
                        delay = config.calculate_delay(attempt)

                        logger.warning(
                            f"Retry attempt {attempt + 1}/{config.max_attempts} "
                            f"for {func.__name__}: {type(e).__name__}: {str(e)}"
                            f" - retrying in {delay:.2f}s"
                        )

                        if on_retry:
                            on_retry(e, attempt + 1, delay)

                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_attempts} retry attempts failed "
                            f"for {func.__name__}: {type(e).__name__}: {str(e)}"
                        )

            # All retries exhausted
            raise last_exception

        return wrapper
    return decorator


class APIRetryConfig(RetryConfig):
    """Specialized config for API calls"""

    def __init__(self):
        # Common API errors
        from requests.exceptions import (
            ConnectionError,
            Timeout,
            HTTPError
        )

        try:
            from googleapiclient.errors import HttpError
            from openai import APIError, RateLimitError, APIConnectionError

            retryable = (
                ConnectionError,
                Timeout,
                HttpError,
                APIError,
                RateLimitError,
                APIConnectionError
            )
        except ImportError:
            # Fallback if imports fail
            retryable = (ConnectionError, Timeout, HTTPError)

        super().__init__(
            max_attempts=4,
            initial_delay=2.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True,
            retryable_exceptions=retryable
        )


class FileOperationRetryConfig(RetryConfig):
    """Specialized config for file operations"""

    def __init__(self):
        super().__init__(
            max_attempts=3,
            initial_delay=0.5,
            max_delay=5.0,
            exponential_base=2.0,
            jitter=False,
            retryable_exceptions=(OSError, IOError, PermissionError)
        )


# Convenience decorators
def retry_api_call(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for API calls with appropriate retry config"""
    return with_retry(APIRetryConfig())(func)


def retry_file_operation(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for file operations with appropriate retry config"""
    return with_retry(FileOperationRetryConfig())(func)


# Manual retry function for use in loops
def retry_operation(
    operation: Callable[[], T],
    config: Optional[RetryConfig] = None,
    operation_name: str = "operation"
) -> T:
    """
    Manually retry an operation

    Args:
        operation: Callable that performs the operation
        config: RetryConfig (uses defaults if None)
        operation_name: Name for logging

    Returns:
        Result of operation

    Raises:
        Last exception if all retries fail

    Example:
        result = retry_operation(
            lambda: api.fetch_data(),
            APIRetryConfig(),
            "fetch_data"
        )
    """
    if config is None:
        config = RetryConfig()

    last_exception = None

    for attempt in range(config.max_attempts):
        try:
            return operation()

        except config.retryable_exceptions as e:
            last_exception = e

            if attempt < config.max_attempts - 1:
                delay = config.calculate_delay(attempt)

                logger.warning(
                    f"Retry attempt {attempt + 1}/{config.max_attempts} "
                    f"for {operation_name}: {type(e).__name__}: {str(e)}"
                    f" - retrying in {delay:.2f}s"
                )

                time.sleep(delay)
            else:
                logger.error(
                    f"All {config.max_attempts} retry attempts failed "
                    f"for {operation_name}: {type(e).__name__}: {str(e)}"
                )

    raise last_exception


# Circuit breaker for failing services
class CircuitBreaker:
    """
    Circuit breaker pattern for failing services
    Stops trying after too many consecutive failures
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying again
            expected_exception: Exception type to track
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Call function through circuit breaker

        Args:
            func: Function to call
            *args, **kwargs: Arguments to pass

        Returns:
            Function result

        Raises:
            Exception if circuit is open
        """
        if self.state == "open":
            # Check if we should try again
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = "half-open"
                logger.info(f"Circuit breaker half-open for {func.__name__}")
            else:
                raise Exception(
                    f"Circuit breaker open for {func.__name__} "
                    f"({self.failure_count} consecutive failures)"
                )

        try:
            result = func(*args, **kwargs)

            # Success - reset if we were half-open
            if self.state == "half-open":
                self.failure_count = 0
                self.state = "closed"
                logger.info(f"Circuit breaker closed for {func.__name__}")

            return result

        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error(
                    f"Circuit breaker opened for {func.__name__} "
                    f"after {self.failure_count} failures"
                )

            raise


# Rate limiter
class RateLimiter:
    """
    Rate limiter to avoid API rate limits
    """

    def __init__(self, max_calls: int, period: float):
        """
        Initialize rate limiter

        Args:
            max_calls: Maximum calls allowed
            period: Period in seconds
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()

        # Remove old calls outside the period
        self.calls = [call_time for call_time in self.calls if now - call_time < self.period]

        if len(self.calls) >= self.max_calls:
            # Calculate wait time
            oldest_call = min(self.calls)
            wait_time = self.period - (now - oldest_call)

            if wait_time > 0:
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                time.sleep(wait_time)

        self.calls.append(time.time())

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Use as decorator"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            self.wait_if_needed()
            return func(*args, **kwargs)
        return wrapper
