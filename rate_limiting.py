"""
LeadForge AI - Rate Limiting & Throttling Module
Prevents API abuse and manages resource consumption
"""

import time
import threading
import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from functools import wraps

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for API endpoint protection

    Prevents API abuse and ensures fair resource allocation
    """

    def __init__(self, rate: int, per: float = 60.0):
        """
        Initialize rate limiter

        Args:
            rate: Number of requests allowed
            per: Time period in seconds (default: 60 seconds)
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.time()
        self._lock = threading.Lock()

    def acquire(self, tokens: int = 1) -> Tuple[bool, float]:
        """
        Try to acquire tokens from the bucket

        Args:
            tokens: Number of tokens needed (default: 1)

        Returns:
            (success, wait_time) - Whether acquisition succeeded and time to wait
        """
        with self._lock:
            current = time.time()
            time_passed = current - self.last_check
            self.last_check = current

            # Refill bucket based on time passed
            self.allowance += time_passed * (self.rate / self.per)

            if self.allowance > self.rate:
                self.allowance = self.rate

            if self.allowance >= tokens:
                self.allowance -= tokens
                return True, 0.0
            else:
                # Calculate wait time
                wait_time = (tokens - self.allowance) * (self.per / self.rate)
                return False, wait_time


class APIRateLimitManager:
    """
    Manages rate limits for different API endpoints and clients

    Features:
        - Per-endpoint rate limits
        - Per-IP rate limits
        - Sliding window counter
        - Automatic cleanup
    """

    def __init__(self):
        """Initialize rate limit manager"""
        self.endpoint_limits = {
            '/api/places-search': (10, 60),  # 10 requests per minute
            '/api/sheets-leads': (30, 60),    # 30 requests per minute
            '/api/leads': (60, 60),           # 60 requests per minute
            '/api/health': (120, 60),          # 120 requests per minute
        }

        self.ip_limiters: Dict[str, RateLimiter] = {}
        self.endpoint_limiters: Dict[str, RateLimiter] = {}
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

    def get_ip_limit(self, ip: str, rate: int = 60, per: float = 60.0) -> RateLimiter:
        """Get or create rate limiter for specific IP"""
        if ip not in self.ip_limiters:
            self.ip_limiters[ip] = RateLimiter(rate, per)
        return self.ip_limiters[ip]

    def get_endpoint_limit(self, endpoint: str) -> RateLimiter:
        """Get or create rate limiter for specific endpoint"""
        if endpoint not in self.endpoint_limiters:
            rate, per = self.endpoint_limits.get(endpoint, (60, 60))
            self.endpoint_limiters[endpoint] = RateLimiter(rate, per)
        return self.endpoint_limiters[endpoint]

    def check_rate_limit(
        self,
        endpoint: str,
        ip: str = "default",
        tokens: int = 1
    ) -> Tuple[bool, Optional[float], Optional[str]]:
        """
        Check if request is within rate limits

        Args:
            endpoint: API endpoint path
            ip: Client IP address
            tokens: Number of tokens needed

        Returns:
            (allowed, retry_after, limit_type)
        """
        # Check endpoint limit
        endpoint_limiter = self.get_endpoint_limit(endpoint)
        endpoint_allowed, endpoint_wait = endpoint_limiter.acquire(tokens)

        if not endpoint_allowed:
            return False, endpoint_wait, "endpoint"

        # Check IP limit
        ip_limiter = self.get_ip_limit(ip)
        ip_allowed, ip_wait = ip_limiter.acquire(tokens)

        if not ip_allowed:
            return False, ip_wait, "ip"

        # Record request
        self.request_history[endpoint].append({
            'timestamp': datetime.now(),
            'ip': ip
        })

        return True, None, None

    def get_usage_stats(self, endpoint: str) -> Dict:
        """Get usage statistics for an endpoint"""
        history = self.request_history.get(endpoint, deque())

        if not history:
            return {'requests': 0, 'unique_ips': 0}

        now = datetime.now()
        recent_requests = [
            req for req in history
            if (now - req['timestamp']).total_seconds() < 60
        ]

        unique_ips = set(req['ip'] for req in recent_requests)

        return {
            'requests': len(recent_requests),
            'unique_ips': len(unique_ips),
            'limit': self.endpoint_limits.get(endpoint, (60, 60))[0]
        }


# Global rate limit manager instance
rate_limit_manager = APIRateLimitManager()


def rate_limit(
    rate: int = 60,
    per: float = 60.0,
    key_func: Optional[callable] = None
):
    """
    Decorator to rate limit a function

    Args:
        rate: Number of allowed calls
        per: Time period in seconds
        key_func: Function to extract key for grouping limits

    Example:
        @rate_limit(rate=10, per=60)
        def my_function():
            pass
    """
    limiters = defaultdict(lambda: RateLimiter(rate, per))

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = key_func(*args, **kwargs) if key_func else "default"
            limiter = limiters[key]

            allowed, wait_time = limiter.acquire()
            if not allowed:
                logger.warning(f"Rate limit exceeded for {func.__name__}, wait {wait_time:.1f}s")
                raise Exception(f"Rate limit exceeded, try again in {wait_time:.1f}s")

            return func(*args, **kwargs)
        return wrapper
    return decorator


class Throttler:
    """
    Throttles operations to prevent resource exhaustion

    Similar to rate limiting but focuses on operation speed rather than limits
    """

    def __init__(self, max_operations: int, time_window: float = 1.0):
        """
        Initialize throttler

        Args:
            max_operations: Maximum operations in time window
            time_window: Time window in seconds
        """
        self.max_operations = max_operations
        self.time_window = time_window
        self.operations = deque()
        self._lock = threading.Lock()

    def throttle(self):
        """Block if operation limit exceeded"""
        with self._lock:
            now = time.time()

            # Remove old operations outside time window
            while self.operations and self.operations[0] < now - self.time_window:
                self.operations.popleft()

            # Check if we can proceed
            if len(self.operations) >= self.max_operations:
                sleep_time = self.time_window - (now - self.operations[0])
                if sleep_time > 0:
                    logger.info(f"Throttling: sleeping {sleep_time:.2f}s")
                    time.sleep(sleep_time)
                    # Clean up old operations
                    while self.operations and self.operations[0] < time.time() - self.time_window:
                        self.operations.popleft()

            # Record this operation
            self.operations.append(now)


def throttle(max_calls: int, period: float = 1.0):
    """
    Decorator to throttle function calls

    Args:
        max_calls: Maximum calls per period
        period: Time period in seconds

    Example:
        @throttle(max_calls=10, period=1.0)
        def fast_function():
            pass
    """
    throttlers = defaultdict(lambda: Throttler(max_calls, period))

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = func.__name__
            throttler = throttlers[key]
            throttler.throttle()
            return func(*args, **kwargs)
        return wrapper
    return decorator
