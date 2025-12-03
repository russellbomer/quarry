"""Robots.txt parser with caching and User-Agent matching."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import cast
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

_DEFAULT_CACHE_DB = "data/cache/robots.sqlite"
_CACHE_TTL_SECONDS = 86400  # 24 hours
_HTTP_OK = 200


class RobotsCache:
    """
    Cache robots.txt files per domain with TTL-based invalidation.

    Uses SQLite to store parsed robots.txt content and crawl-delay directives.
    """

    def __init__(self, db_path: str | None = None):
        """Initialize robots cache with SQLite backend."""
        self.db_path = db_path or _DEFAULT_CACHE_DB
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Create robots cache table if it doesn't exist."""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS robots_cache (
                domain TEXT PRIMARY KEY,
                robots_txt TEXT,
                crawl_delay REAL,
                fetched_at TEXT
            )
        """
        )
        conn.commit()
        conn.close()

    def _fetch_robots_txt(self, domain: str) -> tuple[str, float]:
        """
        Fetch robots.txt from domain.

        Returns:
            (robots_txt_content, crawl_delay_seconds)
        """
        robots_url = f"https://{domain}/robots.txt"

        try:
            response = requests.get(robots_url, timeout=10)
            if response.status_code == _HTTP_OK:
                robots_txt = response.text
            else:
                # No robots.txt or error - allow all
                robots_txt = ""
        except requests.RequestException:
            # Network error - allow all
            robots_txt = ""

        # Parse crawl-delay from robots.txt
        crawl_delay = 0.0
        for raw_line in robots_txt.split("\n"):
            line = raw_line.strip().lower()
            if line.startswith("crawl-delay:"):
                try:
                    crawl_delay = float(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
                break

        return robots_txt, crawl_delay

    def get_robots(self, domain: str) -> tuple[str, float]:
        """
        Get robots.txt content for domain (cached).

        Returns:
            (robots_txt_content, crawl_delay_seconds)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Check cache
        row = conn.execute(
            "SELECT robots_txt, crawl_delay, fetched_at FROM robots_cache WHERE domain = ?",
            (domain,),
        ).fetchone()

        if row:
            fetched_at = datetime.fromisoformat(row["fetched_at"])
            age = (datetime.now(timezone.utc) - fetched_at).total_seconds()

            if age < _CACHE_TTL_SECONDS:
                conn.close()
                return row["robots_txt"], row["crawl_delay"]

        # Cache miss or expired - fetch fresh
        robots_txt, crawl_delay = self._fetch_robots_txt(domain)

        # Update cache
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO robots_cache (domain, robots_txt, crawl_delay, fetched_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(domain) DO UPDATE SET
                robots_txt = excluded.robots_txt,
                crawl_delay = excluded.crawl_delay,
                fetched_at = excluded.fetched_at
        """,
            (domain, robots_txt, crawl_delay, now),
        )
        conn.commit()
        conn.close()

        return robots_txt, crawl_delay

    def is_allowed(self, url: str, user_agent: str = "Quarry") -> bool:
        """
        Check if URL is allowed by robots.txt for given user agent.

        Args:
            url: Full URL to check
            user_agent: User-Agent string to match against

        Returns:
            True if allowed, False if disallowed
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        robots_txt, _ = self.get_robots(domain)

        if not robots_txt:
            # No robots.txt - allow all
            return True

        # Use stdlib RobotFileParser for proper parsing
        parser = RobotFileParser()
        parser.parse(robots_txt.splitlines())

        return parser.can_fetch(user_agent, url)

    def get_crawl_delay(self, domain: str) -> float:
        """
        Get crawl-delay for domain (seconds).

        Returns 0.0 if no crawl-delay specified.
        """
        _, crawl_delay = self.get_robots(domain)
        return crawl_delay


# Global cache instance (singleton pattern using dict to avoid global statement)
_CACHE_CONTAINER: dict[str, RobotsCache | None] = {"instance": None}


def get_cache(db_path: str | None = None) -> RobotsCache:
    """Get or create global robots cache instance."""
    if _CACHE_CONTAINER["instance"] is None:
        _CACHE_CONTAINER["instance"] = RobotsCache(db_path)
    return cast(RobotsCache, _CACHE_CONTAINER["instance"])


def check_robots(url: str, user_agent: str = "Quarry") -> bool:
    """
    Check if URL is allowed by robots.txt.

    This is the main public API - replaces the stub in policy.py.
    """
    cache = get_cache()
    return cache.is_allowed(url, user_agent)
