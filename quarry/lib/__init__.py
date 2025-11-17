"""
Quarry Core Library

Provides foundational utilities used by all scraping tools:
- HTTP client with rate limiting, retry logic, robots.txt compliance
- Token bucket rate limiter for per-domain request throttling
- CSS selector utilities for robust element targeting
- Robots.txt parsing and policy enforcement
- Interactive prompts with validation and retry logic
"""

from .http import create_session, get_html, get_rate_limiter, set_rate_limiter
from .policy import check_robots, is_allowed_domain
from .prompts import (
    RetryablePrompt,
    prompt_choice,
    prompt_confirm,
    prompt_file,
    prompt_text,
    prompt_url,
)
from .ratelimit import DomainRateLimiter, TokenBucket
from .robots import RobotsCache
from .selectors import (
    SelectorChain,
    build_fallback_chain,
    build_robust_selector,
    extract_structural_pattern,
    simplify_selector,
    validate_selector,
)

__all__ = [
    "DomainRateLimiter",
    "RetryablePrompt",
    "RobotsCache",
    "SelectorChain",
    "TokenBucket",
    "build_fallback_chain",
    "build_robust_selector",
    "check_robots",
    "create_session",
    "extract_structural_pattern",
    "get_html",
    "get_rate_limiter",
    "is_allowed_domain",
    "prompt_choice",
    "prompt_confirm",
    "prompt_file",
    "prompt_text",
    "prompt_url",
    "set_rate_limiter",
    "simplify_selector",
    "validate_selector",
]
