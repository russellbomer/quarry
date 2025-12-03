"""Tests for robots.txt parsing and policy enforcement."""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quarry.lib.policy import is_allowed_domain
from quarry.lib.robots import RobotsCache, check_robots, get_cache, _CACHE_CONTAINER


class TestIsAllowedDomain:
    """Tests for domain allowlist checking."""

    def test_empty_allowlist_allows_all(self):
        """Empty allowlist should allow all domains."""
        assert is_allowed_domain("https://example.com/page", []) is True
        assert is_allowed_domain("https://any-domain.org/path", []) is True

    def test_exact_domain_match(self):
        """Should match exact domain."""
        allowlist = ["example.com"]
        assert is_allowed_domain("https://example.com/page", allowlist) is True
        assert is_allowed_domain("https://other.com/page", allowlist) is False

    def test_subdomain_match(self):
        """Should match subdomains of allowed domain."""
        allowlist = ["example.com"]
        assert is_allowed_domain("https://sub.example.com/page", allowlist) is True
        assert is_allowed_domain("https://deep.sub.example.com/page", allowlist) is True

    def test_www_prefix_handling(self):
        """Should handle www prefix consistently."""
        allowlist = ["example.com"]
        assert is_allowed_domain("https://www.example.com/page", allowlist) is True

        # Allowlist with www should also work
        allowlist_www = ["www.example.com"]
        assert is_allowed_domain("https://example.com/page", allowlist_www) is True
        assert is_allowed_domain("https://www.example.com/page", allowlist_www) is True

    def test_case_insensitive(self):
        """Should be case-insensitive."""
        allowlist = ["Example.COM"]
        assert is_allowed_domain("https://example.com/page", allowlist) is True
        assert is_allowed_domain("https://EXAMPLE.COM/page", allowlist) is True

    def test_multiple_allowed_domains(self):
        """Should check against all domains in allowlist."""
        allowlist = ["example.com", "allowed.org", "test.net"]
        assert is_allowed_domain("https://example.com/page", allowlist) is True
        assert is_allowed_domain("https://allowed.org/page", allowlist) is True
        assert is_allowed_domain("https://test.net/page", allowlist) is True
        assert is_allowed_domain("https://blocked.com/page", allowlist) is False

    def test_partial_match_not_allowed(self):
        """Should not match partial domain names."""
        allowlist = ["example.com"]
        # notexample.com should NOT match example.com
        assert is_allowed_domain("https://notexample.com/page", allowlist) is False
        assert is_allowed_domain("https://example.com.evil.net/page", allowlist) is False

    def test_allowlist_with_whitespace(self):
        """Should handle whitespace in allowlist entries."""
        allowlist = ["  example.com  ", "other.org"]
        assert is_allowed_domain("https://example.com/page", allowlist) is True


class TestRobotsCache:
    """Tests for RobotsCache class."""

    def test_init_creates_db(self):
        """Should create SQLite database on init."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "robots.sqlite"
            cache = RobotsCache(str(db_path))

            assert db_path.exists()

    def test_init_creates_table(self):
        """Should create robots_cache table."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "robots.sqlite"
            cache = RobotsCache(str(db_path))

            conn = sqlite3.connect(str(db_path))
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='robots_cache'"
            )
            assert cursor.fetchone() is not None
            conn.close()

    def test_init_creates_parent_dirs(self):
        """Should create parent directories for database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "nested" / "dir" / "robots.sqlite"
            cache = RobotsCache(str(db_path))

            assert db_path.exists()

    @patch("quarry.lib.robots.requests.get")
    def test_fetch_robots_txt_success(self, mock_get):
        """Should fetch and parse robots.txt."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nDisallow: /private\nCrawl-delay: 2"
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "robots.sqlite"
            cache = RobotsCache(str(db_path))

            robots_txt, crawl_delay = cache._fetch_robots_txt("example.com")

            assert "Disallow: /private" in robots_txt
            assert crawl_delay == 2.0

    @patch("quarry.lib.robots.requests.get")
    def test_fetch_robots_txt_404(self, mock_get):
        """Should return empty string for 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "robots.sqlite"
            cache = RobotsCache(str(db_path))

            robots_txt, crawl_delay = cache._fetch_robots_txt("example.com")

            assert robots_txt == ""
            assert crawl_delay == 0.0

    @patch("quarry.lib.robots.requests.get")
    def test_fetch_robots_txt_network_error(self, mock_get):
        """Should return empty string on network error."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "robots.sqlite"
            cache = RobotsCache(str(db_path))

            robots_txt, crawl_delay = cache._fetch_robots_txt("example.com")

            assert robots_txt == ""
            assert crawl_delay == 0.0

    @patch("quarry.lib.robots.requests.get")
    def test_get_robots_caches_result(self, mock_get):
        """Should cache robots.txt and not refetch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nDisallow: /secret"
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "robots.sqlite"
            cache = RobotsCache(str(db_path))

            # First call - fetches
            result1 = cache.get_robots("example.com")
            # Second call - uses cache
            result2 = cache.get_robots("example.com")

            assert result1 == result2
            assert mock_get.call_count == 1  # Only one HTTP request

    @patch("quarry.lib.robots.requests.get")
    def test_is_allowed_with_disallow(self, mock_get):
        """Should respect Disallow rules."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nDisallow: /private/"
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "robots.sqlite"
            cache = RobotsCache(str(db_path))

            assert cache.is_allowed("https://example.com/public/page") is True
            assert cache.is_allowed("https://example.com/private/secret") is False

    @patch("quarry.lib.robots.requests.get")
    def test_is_allowed_no_robots(self, mock_get):
        """Should allow all when no robots.txt."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "robots.sqlite"
            cache = RobotsCache(str(db_path))

            assert cache.is_allowed("https://example.com/any/path") is True

    @patch("quarry.lib.robots.requests.get")
    def test_get_crawl_delay(self, mock_get):
        """Should extract crawl-delay from robots.txt."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nCrawl-delay: 5"
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "robots.sqlite"
            cache = RobotsCache(str(db_path))

            delay = cache.get_crawl_delay("example.com")

            assert delay == 5.0

    @patch("quarry.lib.robots.requests.get")
    def test_get_crawl_delay_not_specified(self, mock_get):
        """Should return 0 when no crawl-delay."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nDisallow: /private"
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "robots.sqlite"
            cache = RobotsCache(str(db_path))

            delay = cache.get_crawl_delay("example.com")

            assert delay == 0.0


class TestCheckRobots:
    """Tests for the check_robots public API."""

    def setup_method(self):
        """Reset global cache before each test."""
        _CACHE_CONTAINER["instance"] = None

    @patch("quarry.lib.robots.requests.get")
    def test_check_robots_allowed(self, mock_get):
        """Should return True for allowed URLs."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nAllow: /"
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "robots.sqlite"
            # Reset and set cache path
            _CACHE_CONTAINER["instance"] = RobotsCache(str(db_path))

            result = check_robots("https://example.com/page")

            assert result is True

    @patch("quarry.lib.robots.requests.get")
    def test_check_robots_disallowed(self, mock_get):
        """Should return False for disallowed URLs."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nDisallow: /"
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "robots.sqlite"
            _CACHE_CONTAINER["instance"] = RobotsCache(str(db_path))

            result = check_robots("https://example.com/page")

            assert result is False


class TestGetCache:
    """Tests for get_cache singleton."""

    def setup_method(self):
        """Reset global cache before each test."""
        _CACHE_CONTAINER["instance"] = None

    def test_get_cache_creates_instance(self):
        """Should create cache instance on first call."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "robots.sqlite"
            
            # Manually set to test get_cache
            cache = get_cache(str(db_path))

            assert cache is not None
            assert isinstance(cache, RobotsCache)

    def test_get_cache_returns_same_instance(self):
        """Should return same instance on subsequent calls."""
        cache1 = get_cache()
        cache2 = get_cache()

        assert cache1 is cache2
