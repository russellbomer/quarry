"""Tests for per-domain rate limiting."""

import time

from quarry.lib.ratelimit import DomainRateLimiter, TokenBucket

# Test constants
DEFAULT_RPS = 2.0
FDA_RPS = 2.0
FDA_API_RPS = 3.0
WEATHER_RPS = 0.5
MIN_WAIT_TOLERANCE = 0.08
MAX_WAIT_TOLERANCE = 0.15
EXPECTED_RETRY_COUNT = 3
EXPECTED_FAILED_COUNT = 3


def test_token_bucket_single_request():
    """Token bucket allows immediate single request."""
    bucket = TokenBucket(rate=1.0, capacity=1)
    wait_time = bucket.consume(tokens=1)
    assert wait_time == 0.0


def test_token_bucket_enforces_rate():
    """Token bucket enforces rate limit across requests."""
    bucket = TokenBucket(rate=10.0, capacity=1)  # 10 req/sec = 0.1s interval

    # First request immediate
    wait1 = bucket.consume(tokens=1)
    assert wait1 == 0.0

    # Second request should wait ~0.1s
    start = time.time()
    wait2 = bucket.consume(tokens=1)
    elapsed = time.time() - start

    assert wait2 > 0.0  # Had to wait
    assert MIN_WAIT_TOLERANCE < elapsed < MAX_WAIT_TOLERANCE  # ~0.1s with some tolerance


def test_domain_rate_limiter_default():
    """Rate limiter uses default rate for unlisted domains."""
    limiter = DomainRateLimiter(default_rps=DEFAULT_RPS)
    rate = limiter.get_rate("https://example.com/page")
    assert rate == DEFAULT_RPS


def test_domain_rate_limiter_custom():
    """Rate limiter uses custom rate for configured domains."""
    limiter = DomainRateLimiter(
        default_rps=1.0,
        rate_limits={
            "fda.gov": FDA_RPS,
            "weather.gov": WEATHER_RPS,
        },
    )

    assert limiter.get_rate("https://fda.gov/recalls") == FDA_RPS
    assert limiter.get_rate("https://www.fda.gov/recalls") == FDA_RPS  # Strips www.
    assert limiter.get_rate("https://api.weather.gov/alerts") == WEATHER_RPS
    assert limiter.get_rate("https://example.com/page") == 1.0  # Default


def test_domain_rate_limiter_subdomain():
    """Rate limiter matches parent domains."""
    limiter = DomainRateLimiter(
        default_rps=1.0,
        rate_limits={"fda.gov": FDA_API_RPS},
    )

    assert limiter.get_rate("https://api.fda.gov/drug/event.json") == FDA_API_RPS
    assert limiter.get_rate("https://www.fda.gov/recalls") == FDA_API_RPS


def test_domain_rate_limiter_isolation():
    """Different domains have independent rate limits."""
    limiter = DomainRateLimiter(default_rps=100.0)  # Fast to avoid slowdown

    # Both should be immediate (different buckets)
    wait1 = limiter.wait_for_url("https://example.com/page1")
    wait2 = limiter.wait_for_url("https://other.com/page1")

    assert wait1 == 0.0
    assert wait2 == 0.0
