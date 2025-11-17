"""Polite HTTP client with retry, backoff, and per-domain rate limiting.

Environment knobs (optional):
- QUARRY_DEFAULT_RPS: float, default RPS for DomainRateLimiter (default 1.0)
- QUARRY_HTTP_TIMEOUT: int seconds, overrides default timeout when unchanged (30)
- QUARRY_HTTP_MAX_RETRIES: int, overrides default retries when unchanged (3)
- QUARRY_MAX_CONTENT_MB: int, maximum response size in MB
    (skip if header missing; otherwise measured content)
- PROXY_URL: http(s) proxy URL; also respects standard HTTP(S)_PROXY envs
"""

import logging
import os
import random
import sys
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

from quarry.lib.ratelimit import DomainRateLimiter

# Global rate limiter instance (container to avoid global statement warning)
_RATE_LIMITER_CONTAINER: dict[str, DomainRateLimiter | None] = {"instance": None}

_LOG = logging.getLogger(__name__)

# Cache for robots.txt parsers (domain -> RobotFileParser | None)
# None indicates robots.txt fetch failed, assume allowed
_ROBOTS_CACHE: dict[str, RobotFileParser | None] = {}

# Realistic user agent pool (top browsers by market share)
_USER_AGENTS = [
    # Chrome on Windows (most common)
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0.0.0 Safari/537.36"
    ),
    # Chrome on macOS
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Safari on macOS
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.1 Safari/605.1.15"
    ),
    # Edge on Windows
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
    ),
]


def set_rate_limiter(limiter: DomainRateLimiter) -> None:
    """Set global rate limiter instance."""
    _RATE_LIMITER_CONTAINER["instance"] = limiter


def get_rate_limiter() -> DomainRateLimiter:
    """Get or create global rate limiter with default settings."""
    limiter = _RATE_LIMITER_CONTAINER["instance"]
    if limiter is None:
        # Allow env override for default RPS
        try:
            default_rps = float(os.environ.get("QUARRY_DEFAULT_RPS", "1.0"))
        except ValueError:
            default_rps = 1.0
        limiter = DomainRateLimiter(default_rps=default_rps)
        _RATE_LIMITER_CONTAINER["instance"] = limiter
    return limiter


def _check_robots_txt(url: str, user_agent: str) -> bool:
    """
    Check if URL is allowed by robots.txt.

    Returns True if allowed, False if disallowed.
    Caches robots.txt per domain for efficiency.
    """
    parsed = urlparse(url)
    domain = f"{parsed.scheme}://{parsed.netloc}"

    # Check cache
    if domain not in _ROBOTS_CACHE:
        rp = RobotFileParser()
        rp.set_url(f"{domain}/robots.txt")
        try:
            rp.read()
        except Exception:
            # If robots.txt fetch fails, assume allowed (be permissive)
            # Cache None to indicate "failed to fetch, allow everything"
            _ROBOTS_CACHE[domain] = None
            return True

        _ROBOTS_CACHE[domain] = rp

    # If cache has None, robots.txt fetch failed previously
    robot_parser = _ROBOTS_CACHE[domain]
    if robot_parser is None:
        return True

    return robot_parser.can_fetch(user_agent, url)


def _prompt_robots_override(url: str, domain: str) -> bool:
    """
    Interactively prompt user to override robots.txt block.

    Only called when QUARRY_INTERACTIVE=1 environment variable is set.

    Args:
        url: The blocked URL
        domain: The domain that's blocking

    Returns:
        True if user wants to proceed anyway, False to respect robots.txt
    """
    print("\n⚠️  robots.txt Policy Block", file=sys.stderr)
    print(f"   Domain: {domain}", file=sys.stderr)
    print(f"   URL: {url}", file=sys.stderr)
    print("\n   This site's robots.txt disallows automated access.", file=sys.stderr)
    print("   Ethical scraping respects this policy.", file=sys.stderr)

    # Flush stderr to ensure prompt appears before input
    sys.stderr.flush()

    try:
        response = input("\n   Proceed anyway? (y/N): ").strip().lower()
        return response in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        # Handle Ctrl+C or EOF gracefully
        print("\n   Cancelled. Respecting robots.txt.", file=sys.stderr)
        return False


def _build_browser_headers(
    url: str, user_agent: str | None = None, referrer: str | None = None
) -> dict[str, str]:
    """
    Build realistic browser headers with variation to avoid fingerprinting.

    Args:
        url: Target URL (used to set referrer intelligently)
        user_agent: Custom UA or None to randomly select
        referrer: Custom referrer or None to simulate search engine/direct

    Returns:
        Dictionary of HTTP headers
    """
    # Select user agent
    ua = user_agent or random.choice(_USER_AGENTS)

    # Base headers that all browsers send
    headers = {
        "User-Agent": ua,
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
            "image/apng,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    # Add browser-specific headers based on UA
    if "Chrome" in ua or "Edg" in ua:
        headers.update(
            {
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none" if not referrer else "cross-site",
                "Sec-Fetch-User": "?1",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
            }
        )

    # Set referrer to simulate natural browsing
    if referrer:
        headers["Referer"] = referrer
    elif random.random() < 0.3:  # 30% of requests come from search engines
        search_engines = [
            f"https://www.google.com/search?q={urlparse(url).netloc}",
            f"https://www.bing.com/search?q={urlparse(url).netloc}",
        ]
        headers["Referer"] = random.choice(search_engines)

    # Occasionally add Cache-Control (like when user hits refresh)
    if random.random() < 0.2:
        headers["Cache-Control"] = "max-age=0"

    return headers


def get_html(
    url: str,
    *,
    ua: str | None = None,
    timeout: int = 30,
    max_retries: int = 3,
    respect_robots: bool = True,
    session: requests.Session | None = None,
) -> str:
    """
    Fetch HTML with retry, exponential backoff, and per-domain rate limiting.

    Uses legitimate bot-evasion techniques:
    - Realistic browser headers with variation
    - User-Agent rotation from real browser pool
    - Respects robots.txt (can be disabled for testing)
    - Session persistence for cookies
    - Natural timing variance in retries
    - Referrer simulation (search engines, direct visits)

    Args:
        url: URL to fetch
        ua: Custom User-Agent (None = random from pool)
        timeout: Request timeout in seconds
        max_retries: Max retry attempts
        respect_robots: Check robots.txt before fetching
        session: Reuse requests.Session for cookie persistence

    Returns:
        HTML content as string

    Not used in offline mode or tests.
    """
    # Check robots.txt if requested (unless --ignore-robots CLI flag set)
    if respect_robots and os.environ.get("QUARRY_IGNORE_ROBOTS") != "1":
        check_ua = ua or "Quarry/2.0 (+https://github.com/russellbomer/quarry)"
        if not _check_robots_txt(url, check_ua):
            domain = urlparse(url).netloc

            # Interactive mode: prompt user for override
            if os.environ.get("QUARRY_INTERACTIVE") == "1":
                if _prompt_robots_override(url, domain):
                    # User chose to proceed anyway - continue to fetching
                    pass
                else:
                    # User chose to respect robots.txt
                    raise PermissionError(f"robots.txt blocks {url} - user chose to respect policy")
            else:
                # Non-interactive mode: raise error with helpful message
                raise PermissionError(
                    f"robots.txt disallows fetching: {url}\n\n"
                    f"This site ({domain}) blocks automated access. Options:\n"
                    f"  1. For testing/debugging only: get_html(url, respect_robots=False)\n"
                    f"  2. Fetch HTML manually and save to a file for testing\n"
                    f"  3. Use a bot-friendly alternative site (see docs/USER_TESTING_PLAN.md)\n"
                    f"  4. Set QUARRY_INTERACTIVE=1 to be prompted on blocks\n\n"
                    f"Note: Respecting robots.txt is the ethical default "
                    f"and required for production use."
                )

    # Allow env overrides when using defaults
    try:
        env_timeout = int(os.environ.get("QUARRY_HTTP_TIMEOUT", ""))
        if timeout == 30 and env_timeout > 0:
            timeout = env_timeout
    except ValueError:
        pass
    try:
        env_retries = int(os.environ.get("QUARRY_HTTP_MAX_RETRIES", ""))
        if max_retries == 3 and env_retries > 0:
            max_retries = env_retries
    except ValueError:
        pass

    # Build realistic browser headers
    headers = _build_browser_headers(url, user_agent=ua)

    # Use provided session or create new one
    http_client = session or requests.Session()
    # Optional proxy override via PROXY_URL (requests also honors *_PROXY)
    proxy_url = os.environ.get("PROXY_URL")
    if proxy_url:
        http_client.proxies.update({"http": proxy_url, "https": proxy_url})

    limiter = get_rate_limiter()

    _LOG.info("fetch.start url=%s timeout=%s retries=%s", url, timeout, max_retries)
    for attempt in range(max_retries):
        # Per-domain rate limiting with token bucket
        # Add natural variance to timing (humans don't click at exact intervals)
        limiter.wait_for_url(url)

        # Add small random delay (0-200ms) to mimic human behavior
        if random.random() < 0.7:  # 70% of requests have this micro-delay
            time.sleep(random.uniform(0, 0.2))

        try:
            response = http_client.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()

            # Optional content size guard
            max_mb_s = os.environ.get("QUARRY_MAX_CONTENT_MB")
            if max_mb_s:
                try:
                    max_bytes = int(max_mb_s) * 1024 * 1024
                    # Prefer Content-Length if present
                    clen = response.headers.get("Content-Length")
                    if clen and clen.isdigit():
                        size = int(clen)
                    else:
                        size = len(response.content)
                    if size > max_bytes:
                        raise ValueError(f"Response too large: {size} bytes > {max_bytes} bytes")
                except ValueError:
                    # If env unparsable, ignore guard
                    pass

            _LOG.info(
                "fetch.ok url=%s status=%s bytes=%s",
                url,
                response.status_code,
                response.headers.get("Content-Length") or len(response.content),
            )
            return response.text
        except requests.HTTPError as e:
            # Add helpful context to HTTP errors
            if e.response is not None:
                status = e.response.status_code
                server = e.response.headers.get("Server", "unknown")

                # Check for common bot detection services
                if status == 403:
                    bot_detection_hints = []
                    if "akamai" in server.lower():
                        bot_detection_hints.append("Akamai")
                    if "cloudflare" in server.lower():
                        bot_detection_hints.append("Cloudflare")
                    if "cf-ray" in e.response.headers:
                        bot_detection_hints.append("Cloudflare")

                    if bot_detection_hints:
                        services = "/".join(bot_detection_hints)
                        raise requests.HTTPError(
                            f"{status} Client Error: Blocked by {services} bot protection "
                            f"for url: {url}. "
                            f"Try: slower rate limit, session persistence, or check robots.txt"
                        ) from e

            if attempt == max_retries - 1:
                _LOG.error(
                    "fetch.http_error url=%s status=%s",
                    url,
                    getattr(e.response, "status_code", None),
                )
                raise

            # Enhanced exponential backoff with jitter (more human-like)
            base_backoff = 0.5 * (2**attempt)  # 0.5, 1, 2 seconds
            jitter = random.uniform(0, 0.3 * base_backoff)  # Add 0-30% jitter
            wait_time = base_backoff + jitter

            # For rate limit errors (429, 503), wait longer
            if isinstance(e, requests.HTTPError) and e.response is not None:
                if e.response.status_code in (429, 503):
                    wait_time *= 3  # Triple the wait for rate limit errors

                    # Check for Retry-After header (RFC 7231)
                    retry_after = e.response.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        wait_time = max(wait_time, int(retry_after))

            _LOG.debug("fetch.backoff url=%s attempt=%s wait=%.2fs", url, attempt + 1, wait_time)
            time.sleep(wait_time)

        except requests.RequestException as e:
            # Provide helpful context for different error types
            if isinstance(e, (requests.Timeout, requests.ConnectTimeout, requests.ReadTimeout)):
                timeout_type = type(e).__name__
                domain = urlparse(url).netloc

                # If this is the last attempt, provide detailed timeout guidance
                if attempt == max_retries - 1:
                    _LOG.error("fetch.timeout url=%s attempt=%s", url, attempt + 1)
                    raise requests.Timeout(
                        f"{timeout_type} after {timeout}s for {url}\n\n"
                        f"This site ({domain}) is slow or rate-limiting. Try:\n"
                        f"  1. Increase timeout: get_html(url, timeout=60)  # default is 30s\n"
                        f"  2. Reduce rate limit in job YAML (slower requests)\n"
                        f"  3. Check if site blocks automated access (may need session/cookies)\n"
                        f"  4. Some sites (Best Buy, Walmart) have aggressive rate limits\n\n"
                        f"Current settings: timeout={timeout}s, attempt={attempt + 1}/{max_retries}"
                    ) from e

                # For retries, wait longer for timeout errors
                base_backoff = 0.5 * (2**attempt) * 2  # Double wait for timeouts
                jitter = random.uniform(0, 0.1 * base_backoff)
                wait = base_backoff + jitter
                _LOG.debug(
                    "fetch.backoff-timeout url=%s attempt=%s wait=%.2fs", url, attempt + 1, wait
                )
                time.sleep(wait)

            elif attempt == max_retries - 1:
                # Last attempt for other errors - re-raise with context
                _LOG.error(
                    "fetch.error url=%s attempt=%s err=%s", url, attempt + 1, type(e).__name__
                )
                raise

            else:
                # Generic backoff for other connection errors
                base_backoff = 0.5 * (2**attempt)
                jitter = random.uniform(0, 0.1 * base_backoff)
                wait = base_backoff + jitter
                _LOG.debug(
                    "fetch.backoff-generic url=%s attempt=%s wait=%.2fs", url, attempt + 1, wait
                )
                time.sleep(wait)

    _LOG.error("fetch.unexpected_end url=%s", url)
    raise RuntimeError("Unexpected end of retry loop")


def create_session() -> requests.Session:
    """
    Create a requests.Session with persistent cookies and realistic settings.

    Using a session across multiple requests:
    1. Maintains cookies (like a real browser)
    2. Reuses TCP connections (faster, more natural)
    3. Can accumulate session state (logged in users, preferences, etc.)

    Returns:
        Configured requests.Session
    """
    session = requests.Session()

    # Set default headers that persist across requests
    session.headers.update(
        {
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
                "*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "DNT": "1",  # Do Not Track (shows good faith)
        }
    )

    return session
