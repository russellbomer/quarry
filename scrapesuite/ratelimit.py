"""Per-domain rate limiting using token bucket algorithm."""

import threading
import time
from urllib.parse import urlparse


class TokenBucket:
    """
    Token bucket rate limiter for a single domain.

    Allows burst traffic up to capacity, then enforces steady rate.
    """

    def __init__(self, rate: float, capacity: int = 1):
        """
        Initialize token bucket.

        Args:
            rate: Tokens per second (e.g., 2.0 = 2 requests/sec)
            capacity: Maximum burst size (default 1 = no burst)
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_update = time.time()
        self.lock = threading.Lock()

    def consume(self, tokens: int = 1) -> float:
        """
        Consume tokens, blocking until available.

        Returns:
            Time waited in seconds (0 if no wait needed)
        """
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update

            # Refill tokens based on elapsed time
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens >= tokens:
                # Sufficient tokens available
                self.tokens -= tokens
                return 0.0

            # Insufficient tokens - calculate wait time
            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self.rate

            # Sleep outside lock would be better, but simpler to sleep inside for now
            time.sleep(wait_time)

            # After sleeping, update state
            self.tokens = 0.0
            self.last_update = time.time()

            return wait_time


class DomainRateLimiter:
    """
    Manages per-domain rate limiters with token bucket algorithm.

    Thread-safe for concurrent access across multiple domains.
    """

    def __init__(self, default_rps: float = 1.0, rate_limits: dict[str, float] | None = None):
        """
        Initialize domain rate limiter.

        Args:
            default_rps: Default requests per second for unlisted domains
            rate_limits: Dict mapping domain -> rps (e.g., {"fda.gov": 2.0})
        """
        self.default_rps = default_rps
        self.rate_limits = rate_limits or {}
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def _get_domain(self, url: str) -> str:
        """Extract normalized domain from URL."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Strip www. prefix for normalization
        if domain.startswith("www."):
            domain = domain[4:]
        return domain

    def _get_bucket(self, domain: str) -> TokenBucket:
        """Get or create token bucket for domain."""
        with self._lock:
            if domain not in self._buckets:
                # Find matching rate limit (exact or parent domain)
                rps = self.default_rps
                for limit_domain, limit_rps in self.rate_limits.items():
                    normalized_limit = limit_domain.lower()
                    if normalized_limit.startswith("www."):
                        normalized_limit = normalized_limit[4:]

                    if domain == normalized_limit or domain.endswith("." + normalized_limit):
                        rps = limit_rps
                        break

                self._buckets[domain] = TokenBucket(rate=rps, capacity=1)

            return self._buckets[domain]

    def wait_for_url(self, url: str) -> float:
        """
        Wait until URL can be fetched according to rate limits.

        Returns:
            Time waited in seconds
        """
        domain = self._get_domain(url)
        bucket = self._get_bucket(domain)
        return bucket.consume(tokens=1)

    def get_rate(self, url: str) -> float:
        """Get configured rate limit (rps) for URL's domain."""
        domain = self._get_domain(url)

        # Check for explicit rate limit
        for limit_domain, limit_rps in self.rate_limits.items():
            normalized_limit = limit_domain.lower()
            if normalized_limit.startswith("www."):
                normalized_limit = normalized_limit[4:]

            if domain == normalized_limit or domain.endswith("." + normalized_limit):
                return limit_rps

        return self.default_rps
