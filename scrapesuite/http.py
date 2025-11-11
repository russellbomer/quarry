"""Polite HTTP client with retry, backoff, and per-domain rate limiting."""

import random
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

from scrapesuite.ratelimit import DomainRateLimiter

# Global rate limiter instance (container to avoid global statement warning)
_RATE_LIMITER_CONTAINER: dict[str, DomainRateLimiter | None] = {"instance": None}

# Cache for robots.txt parsers (domain -> RobotFileParser | None)
# None indicates robots.txt fetch failed, assume allowed
_ROBOTS_CACHE: dict[str, RobotFileParser | None] = {}

# Realistic user agent pool (top browsers by market share)
_USER_AGENTS = [
    # Chrome on Windows (most common)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]


def set_rate_limiter(limiter: DomainRateLimiter) -> None:
    """Set global rate limiter instance."""
    _RATE_LIMITER_CONTAINER["instance"] = limiter


def get_rate_limiter() -> DomainRateLimiter:
    """Get or create global rate limiter with default settings."""
    limiter = _RATE_LIMITER_CONTAINER["instance"]
    if limiter is None:
        limiter = DomainRateLimiter(default_rps=1.0)
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


def _build_browser_headers(url: str, user_agent: str | None = None, referrer: str | None = None) -> dict[str, str]:
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
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    # Add browser-specific headers based on UA
    if "Chrome" in ua or "Edg" in ua:
        headers.update({
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none" if not referrer else "cross-site",
            "Sec-Fetch-User": "?1",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
        })
    
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
    # Check robots.txt if requested
    if respect_robots:
        check_ua = ua or "ScrapeSuite/1.0 (+https://github.com/russellbomer/scrapesuite)"
        if not _check_robots_txt(url, check_ua):
            domain = urlparse(url).netloc
            raise PermissionError(
                f"robots.txt disallows fetching: {url}\n\n"
                f"This site ({domain}) blocks automated access. Options:\n"
                f"  1. For testing/debugging only: get_html(url, respect_robots=False)\n"
                f"  2. Fetch HTML manually and save to a file for testing\n"
                f"  3. Use a bot-friendly alternative site (see docs/USER_TESTING_PLAN.md)\n"
                f"  4. Set SCRAPESUITE_INTERACTIVE=1 to be prompted on blocks\n\n"
                f"Note: Respecting robots.txt is the ethical default and required for production use."
            )
    
    # Build realistic browser headers
    headers = _build_browser_headers(url, user_agent=ua)
    
    # Use provided session or create new one
    http_client = session or requests.Session()
    
    limiter = get_rate_limiter()

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
                            f"{status} Client Error: Blocked by {services} bot protection for url: {url}. "
                            f"Try: slower rate limit, session persistence, or check robots.txt"
                        ) from e
                
            if attempt == max_retries - 1:
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
            
            time.sleep(wait_time)
        
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise
            
            # Backoff for other errors (timeout, connection, etc.)
            # For timeout errors, increase wait time more aggressively
            base_backoff = 0.5 * (2**attempt)
            
            # Timeout errors need longer retry delays
            if isinstance(e, (requests.Timeout, requests.ConnectTimeout, requests.ReadTimeout)):
                base_backoff *= 2  # Double the wait for timeout errors
            
            jitter = random.uniform(0, 0.1 * base_backoff)
            time.sleep(base_backoff + jitter)

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
    session.headers.update({
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "DNT": "1",  # Do Not Track (shows good faith)
    })
    
    return session
