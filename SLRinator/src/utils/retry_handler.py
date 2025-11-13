#!/usr/bin/env python3
"""
Retry Handler with Exponential Backoff
Handles API failures and network errors gracefully
"""

import time
import random
import logging
from typing import Callable, Any, Optional, Dict, List
from functools import wraps
import requests
from requests.exceptions import RequestException


class RetryHandler:
    """
    Sophisticated retry handler with exponential backoff
    """
    
    def __init__(self, 
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential_base: float = 2.0,
                 jitter: bool = True):
        """
        Initialize retry handler
        
        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Initial delay between retries (seconds)
            max_delay: Maximum delay between retries (seconds)
            exponential_base: Base for exponential backoff
            jitter: Add random jitter to prevent thundering herd
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.logger = logging.getLogger(__name__)
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        delay = min(self.base_delay * (self.exponential_base ** attempt), self.max_delay)
        
        if self.jitter:
            # Add random jitter (±25% of delay)
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if operation should be retried
        
        Args:
            exception: The exception that occurred
            attempt: Current attempt number
        
        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.max_retries:
            return False
        
        # Retry on network errors
        if isinstance(exception, (RequestException, ConnectionError, TimeoutError)):
            return True
        
        # Retry on specific HTTP errors
        if isinstance(exception, requests.HTTPError):
            status_code = exception.response.status_code if exception.response else None
            # Retry on 429 (rate limit), 500-599 (server errors), 408 (timeout)
            if status_code in [408, 429] or (status_code and 500 <= status_code < 600):
                return True
        
        # Retry on specific API errors
        error_message = str(exception).lower()
        retry_keywords = ['rate limit', 'timeout', 'connection', 'temporary', 'unavailable']
        if any(keyword in error_message for keyword in retry_keywords):
            return True
        
        return False
    
    def execute_with_retry(self, 
                          func: Callable,
                          *args,
                          operation_name: str = None,
                          **kwargs) -> Any:
        """
        Execute function with retry logic
        
        Args:
            func: Function to execute
            operation_name: Name of operation for logging
            *args, **kwargs: Arguments to pass to function
        
        Returns:
            Result of function execution
        
        Raises:
            Last exception if all retries fail
        """
        operation_name = operation_name or func.__name__
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Log attempt
                if attempt > 0:
                    self.logger.info(f"Retry attempt {attempt}/{self.max_retries} for {operation_name}")
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Success - log if it was a retry
                if attempt > 0:
                    self.logger.info(f"Operation {operation_name} succeeded after {attempt} retries")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Check if should retry
                if not self.should_retry(e, attempt):
                    self.logger.error(f"Operation {operation_name} failed: {e}")
                    raise
                
                # Calculate delay
                delay = self.calculate_delay(attempt)
                
                # Log retry
                self.logger.warning(
                    f"Operation {operation_name} failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}"
                )
                self.logger.info(f"Retrying in {delay:.2f} seconds...")
                
                # Wait before retry
                time.sleep(delay)
        
        # All retries exhausted
        self.logger.error(f"Operation {operation_name} failed after {self.max_retries + 1} attempts")
        raise last_exception


def retry_on_failure(max_retries: int = 3,
                    base_delay: float = 1.0,
                    max_delay: float = 60.0,
                    exponential_base: float = 2.0,
                    jitter: bool = True):
    """
    Decorator to add retry logic to functions
    
    Usage:
        @retry_on_failure(max_retries=5, base_delay=2.0)
        def api_call():
            # Make API call
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = RetryHandler(
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                exponential_base=exponential_base,
                jitter=jitter
            )
            return handler.execute_with_retry(func, *args, **kwargs)
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures
    """
    
    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 expected_exception: type = Exception):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before attempting recovery (seconds)
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open
        
        self.logger = logging.getLogger(__name__)
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function through circuit breaker
        
        Args:
            func: Function to call
            *args, **kwargs: Arguments to pass to function
        
        Returns:
            Result of function call
        
        Raises:
            CircuitOpenError if circuit is open
            Original exception if function fails
        """
        # Check circuit state
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half_open'
                self.logger.info(f"Circuit breaker entering half-open state")
            else:
                raise CircuitOpenError(
                    f"Circuit breaker is open. Retry after {self.recovery_timeout} seconds"
                )
        
        # Attempt call
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return False
        
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        if self.state == 'half_open':
            self.logger.info("Circuit breaker closing after successful call")
        
        self.failure_count = 0
        self.state = 'closed'
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
            self.logger.error(
                f"Circuit breaker opening after {self.failure_count} failures"
            )
        elif self.state == 'half_open':
            self.state = 'open'
            self.logger.warning("Circuit breaker reopening after failure in half-open state")


class CircuitOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class APIRateLimiter:
    """
    Rate limiter for API calls
    """
    
    def __init__(self, 
                 calls_per_second: float = 1.0,
                 burst_size: int = 10):
        """
        Initialize rate limiter
        
        Args:
            calls_per_second: Maximum sustained rate
            burst_size: Maximum burst size
        """
        self.calls_per_second = calls_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self.logger = logging.getLogger(__name__)
    
    def acquire(self, timeout: float = None) -> bool:
        """
        Acquire permission to make API call
        
        Args:
            timeout: Maximum time to wait (seconds)
        
        Returns:
            True if acquired, False if timeout
        """
        start_time = time.time()
        
        while True:
            # Update tokens
            now = time.time()
            elapsed = now - self.last_update
            self.tokens = min(
                self.burst_size,
                self.tokens + elapsed * self.calls_per_second
            )
            self.last_update = now
            
            # Check if token available
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            
            # Check timeout
            if timeout is not None:
                if time.time() - start_time >= timeout:
                    return False
            
            # Calculate wait time
            wait_time = (1 - self.tokens) / self.calls_per_second
            wait_time = min(wait_time, 0.1)  # Cap at 100ms
            
            self.logger.debug(f"Rate limit reached, waiting {wait_time:.3f}s")
            time.sleep(wait_time)


# Global instances for common APIs
_rate_limiters: Dict[str, APIRateLimiter] = {}

def get_rate_limiter(api_name: str, 
                    calls_per_second: float = 1.0,
                    burst_size: int = 10) -> APIRateLimiter:
    """Get or create rate limiter for API"""
    if api_name not in _rate_limiters:
        _rate_limiters[api_name] = APIRateLimiter(calls_per_second, burst_size)
    return _rate_limiters[api_name]


# Example usage functions
def make_api_call_with_retry(api_func: Callable,
                            api_name: str = "default",
                            max_retries: int = 3,
                            rate_limit: float = 1.0) -> Any:
    """
    Make API call with retry logic and rate limiting
    
    Args:
        api_func: Function that makes the API call
        api_name: Name of API for rate limiting
        max_retries: Maximum number of retries
        rate_limit: Calls per second limit
    
    Returns:
        Result of API call
    """
    # Get rate limiter
    limiter = get_rate_limiter(api_name, calls_per_second=rate_limit)
    
    # Create retry handler
    retry_handler = RetryHandler(max_retries=max_retries)
    
    def wrapped_call():
        # Acquire rate limit token
        if not limiter.acquire(timeout=30):
            raise TimeoutError(f"Rate limit timeout for {api_name}")
        
        # Make API call
        return api_func()
    
    # Execute with retry
    return retry_handler.execute_with_retry(
        wrapped_call,
        operation_name=f"{api_name}_api_call"
    )