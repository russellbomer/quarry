"""Quarry: A reusable Python toolkit for web/data collection."""

__version__ = "2.0.0"

from quarry.core import run_job
from quarry.lib.http import create_session, get_html
from quarry.lib.policy import check_robots, is_allowed_domain
from quarry.lib.ratelimit import DomainRateLimiter
from quarry.lib.robots import RobotsCache
from quarry.state import get_failed_urls, record_failed_url

__all__ = [
    "DomainRateLimiter",
    "RobotsCache",
    "check_robots",
    "create_session",
    "get_failed_urls",
    "get_html",
    "is_allowed_domain",
    "record_failed_url",
    "run_job",
]
