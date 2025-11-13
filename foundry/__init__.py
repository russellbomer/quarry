"""Foundry: A reusable Python toolkit for web/data collection."""

__version__ = "1.0.0"

from foundry.core import run_job
from foundry.lib.http import create_session, get_html
from foundry.lib.policy import check_robots, is_allowed_domain
from foundry.lib.ratelimit import DomainRateLimiter
from foundry.lib.robots import RobotsCache
from foundry.state import get_failed_urls, record_failed_url

__all__ = [
    "DomainRateLimiter",
    "RobotsCache",
    "check_robots",
    "create_session",
    "get_html",
    "get_failed_urls",
    "is_allowed_domain",
    "record_failed_url",
    "run_job",
]
