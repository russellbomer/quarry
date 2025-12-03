"""Tests for HTTP client utilities."""

import os
from unittest.mock import MagicMock, patch

import pytest

from quarry.lib.http import (
    _build_browser_headers,
    get_rate_limiter,
    set_rate_limiter,
    _check_robots_txt,
    _USER_AGENTS,
    _RATE_LIMITER_CONTAINER,
    _ROBOTS_CACHE,
)
from quarry.lib.ratelimit import DomainRateLimiter


class TestRateLimiter:
    """Tests for rate limiter management."""

    def setup_method(self):
        """Reset global rate limiter before each test."""
        _RATE_LIMITER_CONTAINER["instance"] = None

    def test_get_rate_limiter_creates_instance(self):
        """Should create rate limiter on first call."""
        limiter = get_rate_limiter()

        assert limiter is not None
        assert isinstance(limiter, DomainRateLimiter)

    def test_get_rate_limiter_returns_same_instance(self):
        """Should return same instance on subsequent calls."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()

        assert limiter1 is limiter2

    def test_set_rate_limiter(self):
        """Should set custom rate limiter."""
        custom_limiter = DomainRateLimiter(default_rps=5.0)
        set_rate_limiter(custom_limiter)

        result = get_rate_limiter()

        assert result is custom_limiter

    def test_get_rate_limiter_uses_env_var(self):
        """Should use QUARRY_DEFAULT_RPS env var."""
        with patch.dict(os.environ, {"QUARRY_DEFAULT_RPS": "2.5"}):
            _RATE_LIMITER_CONTAINER["instance"] = None
            limiter = get_rate_limiter()

            assert limiter.default_rps == 2.5

    def test_get_rate_limiter_invalid_env_var(self):
        """Should fallback to 1.0 for invalid env var."""
        with patch.dict(os.environ, {"QUARRY_DEFAULT_RPS": "invalid"}):
            _RATE_LIMITER_CONTAINER["instance"] = None
            limiter = get_rate_limiter()

            assert limiter.default_rps == 1.0


class TestBuildBrowserHeaders:
    """Tests for browser header generation."""

    def test_returns_dict(self):
        """Should return dictionary of headers."""
        headers = _build_browser_headers("https://example.com")

        assert isinstance(headers, dict)

    def test_contains_required_headers(self):
        """Should include core browser headers."""
        headers = _build_browser_headers("https://example.com")

        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers
        assert "Accept-Encoding" in headers

    def test_uses_custom_user_agent(self):
        """Should use provided user agent."""
        custom_ua = "CustomBot/1.0"
        headers = _build_browser_headers("https://example.com", user_agent=custom_ua)

        assert headers["User-Agent"] == custom_ua

    def test_selects_random_user_agent(self):
        """Should select from user agent pool when not specified."""
        headers = _build_browser_headers("https://example.com")

        assert headers["User-Agent"] in _USER_AGENTS

    def test_chrome_specific_headers(self):
        """Should add Chrome-specific headers for Chrome UA."""
        chrome_ua = _USER_AGENTS[0]  # First is Chrome
        headers = _build_browser_headers("https://example.com", user_agent=chrome_ua)

        assert "Sec-Fetch-Dest" in headers

    def test_accept_language_present(self):
        """Should include Accept-Language header."""
        headers = _build_browser_headers("https://example.com")

        assert "en-US" in headers["Accept-Language"]


class TestCheckRobotsTxt:
    """Tests for robots.txt checking."""

    def setup_method(self):
        """Clear robots cache before each test."""
        _ROBOTS_CACHE.clear()

    @patch("quarry.lib.http.RobotFileParser")
    def test_allowed_url(self, mock_parser_class):
        """Should return True for allowed URLs."""
        mock_parser = MagicMock()
        mock_parser.can_fetch.return_value = True
        mock_parser_class.return_value = mock_parser

        result = _check_robots_txt("https://example.com/public", "TestBot")

        assert result is True

    @patch("quarry.lib.http.RobotFileParser")
    def test_disallowed_url(self, mock_parser_class):
        """Should return False for disallowed URLs."""
        mock_parser = MagicMock()
        mock_parser.can_fetch.return_value = False
        mock_parser_class.return_value = mock_parser

        result = _check_robots_txt("https://example.com/private", "TestBot")

        assert result is False

    @patch("quarry.lib.http.RobotFileParser")
    def test_caches_robots_per_domain(self, mock_parser_class):
        """Should cache robots.txt parser per domain."""
        mock_parser = MagicMock()
        mock_parser.can_fetch.return_value = True
        mock_parser_class.return_value = mock_parser

        # First call
        _check_robots_txt("https://example.com/page1", "TestBot")
        # Second call same domain
        _check_robots_txt("https://example.com/page2", "TestBot")

        # Should only create parser once
        assert mock_parser_class.call_count == 1

    @patch("quarry.lib.http.RobotFileParser")
    def test_separate_cache_per_domain(self, mock_parser_class):
        """Should have separate cache entries per domain."""
        mock_parser = MagicMock()
        mock_parser.can_fetch.return_value = True
        mock_parser_class.return_value = mock_parser

        _check_robots_txt("https://example.com/page", "TestBot")
        _check_robots_txt("https://other.com/page", "TestBot")

        # Should create parser for each domain
        assert mock_parser_class.call_count == 2

    @patch("quarry.lib.http.RobotFileParser")
    def test_robots_fetch_failure_allows_access(self, mock_parser_class):
        """Should allow access if robots.txt fetch fails."""
        mock_parser = MagicMock()
        mock_parser.read.side_effect = Exception("Network error")
        mock_parser_class.return_value = mock_parser

        result = _check_robots_txt("https://example.com/page", "TestBot")

        assert result is True

    @patch("quarry.lib.http.RobotFileParser")
    def test_robots_fetch_failure_caches_none(self, mock_parser_class):
        """Should cache None for failed robots.txt fetch."""
        mock_parser = MagicMock()
        mock_parser.read.side_effect = Exception("Network error")
        mock_parser_class.return_value = mock_parser

        _check_robots_txt("https://failed.com/page", "TestBot")

        assert "https://failed.com" in _ROBOTS_CACHE
        assert _ROBOTS_CACHE["https://failed.com"] is None

    @patch("quarry.lib.http.RobotFileParser")
    def test_cached_none_returns_true(self, mock_parser_class):
        """Should return True for cached None (failed fetch)."""
        # Pre-populate cache with None
        _ROBOTS_CACHE["https://cached.com"] = None

        result = _check_robots_txt("https://cached.com/page", "TestBot")

        assert result is True
        # Should not create new parser
        mock_parser_class.assert_not_called()


class TestUserAgents:
    """Tests for user agent pool."""

    def test_user_agents_not_empty(self):
        """User agent pool should not be empty."""
        assert len(_USER_AGENTS) > 0

    def test_user_agents_are_strings(self):
        """All user agents should be strings."""
        for ua in _USER_AGENTS:
            assert isinstance(ua, str)

    def test_user_agents_contain_browser_name(self):
        """User agents should contain recognizable browser names."""
        browser_names = ["Chrome", "Firefox", "Safari", "Edge"]
        for ua in _USER_AGENTS:
            assert any(browser in ua for browser in browser_names)

    def test_user_agents_contain_mozilla(self):
        """All user agents should start with Mozilla/5.0."""
        for ua in _USER_AGENTS:
            assert ua.startswith("Mozilla/5.0")
