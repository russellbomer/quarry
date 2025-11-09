"""ScrapeSuite: A reusable Python toolkit for web/data collection."""

__version__ = "1.0.0"

from scrapesuite.core import run_job
from scrapesuite.ratelimit import DomainRateLimiter
from scrapesuite.robots import RobotsCache, check_robots
from scrapesuite.state import get_failed_urls, record_failed_url

__all__ = [
    "DomainRateLimiter",
    "RobotsCache",
    "__version__",
    "check_robots",
    "get_failed_urls",
    "record_failed_url",
    "run_job",
]
