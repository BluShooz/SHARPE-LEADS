"""
LeadForge AI - Error Handling & Resilience Module
Provides retry logic, graceful error handling, and recovery mechanisms
"""

import time
import functools
from typing import Callable, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RetryError(Exception):
    """Raised when all retry attempts are exhausted"""
    pass


def retry_on_failure(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
) -> Callable:
    """
    Decorator to retry a function on failure with exponential backoff

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for exponential backoff
        initial_delay: Initial delay in seconds
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback function called on each retry

    Returns:
        Decorated function with retry logic

    Example:
        @retry_on_failure(max_retries=3, exceptions=(ConnectionError,))
        def fetch_api():
            return requests.get(url)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"All {max_retries} retry attempts failed for {func.__name__}")
                        raise RetryError(f"Failed after {max_retries} retries: {str(e)}") from e

                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {delay:.1f}s..."
                    )

                    if on_retry:
                        on_retry(attempt, e)

                    time.sleep(delay)
                    delay *= backoff_factor

            # This should never be reached, but just in case
            raise RetryError("Unexpected error in retry logic")

        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    default_value: Any = None,
    error_message: str = "Operation failed",
    raise_on_error: bool = False
) -> Any:
    """
    Safely execute a function with error handling

    Args:
        func: Function to execute
        default_value: Value to return on error
        error_message: Message to log on error
        raise_on_error: Whether to raise the exception or return default

    Returns:
        Function result or default_value on error

    Example:
        result = safe_execute(
            lambda: risky_operation(),
            default_value=[],
            error_message="Failed to fetch leads"
        )
    """
    try:
        return func()
    except Exception as e:
        logger.error(f"{error_message}: {str(e)}")
        if raise_on_error:
            raise
        return default_value


class CircuitBreaker:
    """
    Circuit Breaker pattern to prevent cascading failures

    States:
        - CLOSED: Normal operation, requests pass through
        - OPEN: Failure threshold exceeded, requests fail immediately
        - HALF_OPEN: Testing if service has recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Exception = Exception
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying again
            expected_exception: Exception type that counts as failure
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is OPEN or function fails
        """
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise Exception("Circuit breaker is OPEN - requests blocked")

        try:
            result = func(*args, **kwargs)

            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failure_count = 0
                logger.info("Circuit breaker reset to CLOSED state")

            return result

        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
                logger.error(f"Circuit breaker opened after {self.failure_count} failures")

            raise


# Global circuit breaker instances
_circuit_breakers = {}


def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    """
    Get or create a circuit breaker instance

    Args:
        name: Unique name for the circuit breaker
        **kwargs: Arguments to pass to CircuitBreaker constructor

    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(**kwargs)
    return _circuit_breakers[name]


def with_circuit_breaker(
    breaker_name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0
) -> Callable:
    """
    Decorator to add circuit breaker protection to a function

    Args:
        breaker_name: Name of the circuit breaker
        failure_threshold: Failures before opening circuit
        recovery_timeout: Seconds before trying again

    Returns:
        Decorated function with circuit breaker
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            breaker = get_circuit_breaker(
                breaker_name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout
            )
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator
