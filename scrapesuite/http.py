"""Polite HTTP client with retry, backoff, and per-domain rate limiting."""

import random
import time

import requests

from scrapesuite.ratelimit import DomainRateLimiter

# Global rate limiter instance (container to avoid global statement warning)
_RATE_LIMITER_CONTAINER: dict[str, DomainRateLimiter | None] = {"instance": None}


def set_rate_limiter(limiter: DomainRateLimiter) -> None:
    """Set global rate limiter instance."""
    _RATE_LIMITER_CONTAINER["instance"] = limiter


def get_rate_limiter() -> DomainRateLimiter:
    """Get or create global rate limiter with default settings."""
    if _RATE_LIMITER_CONTAINER["instance"] is None:
        _RATE_LIMITER_CONTAINER["instance"] = DomainRateLimiter(default_rps=1.0)
    return _RATE_LIMITER_CONTAINER["instance"]


def get_html(
    url: str,
    *,
    ua: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    timeout: int = 15,
    max_retries: int = 3,
) -> str:
    """
    Fetch HTML with retry, exponential backoff, and per-domain rate limiting.

    Not used in offline mode or tests.
    """
    # Use realistic browser headers to avoid 403 blocks
    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
    limiter = get_rate_limiter()

    for attempt in range(max_retries):
        # Per-domain rate limiting with token bucket
        limiter.wait_for_url(url)

        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.HTTPError as e:
            # Add helpful context to HTTP errors
            if e.response is not None:
                status = e.response.status_code
                server = e.response.headers.get("Server", "unknown")
                
                # Check for common bot detection services
                if status == 403:
                    if "akamai" in server.lower() or "cloudflare" in server.lower():
                        raise requests.HTTPError(
                            f"{status} Client Error: Blocked by {server} bot protection for url: {url}"
                        ) from e
                
            if attempt == max_retries - 1:
                raise

            # Enhanced exponential backoff with jitter
            base_backoff = 0.5 * (2**attempt)  # 0.5, 1, 2 seconds
            jitter = random.uniform(0, 0.1 * base_backoff)  # Add 0-10% jitter
            wait_time = base_backoff + jitter

            # For rate limit errors (429, 503), wait longer
            if isinstance(e, requests.HTTPError) and e.response is not None:
                if e.response.status_code in (429, 503):
                    wait_time *= 3  # Triple the wait for rate limit errors
            
            time.sleep(wait_time)
        
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise
            
            # Backoff for other errors (timeout, connection, etc.)
            base_backoff = 0.5 * (2**attempt)
            jitter = random.uniform(0, 0.1 * base_backoff)
            time.sleep(base_backoff + jitter)

    raise RuntimeError("Unexpected end of retry loop")
