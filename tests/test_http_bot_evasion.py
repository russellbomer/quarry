"""Tests for bot evasion techniques in HTTP client."""

from unittest.mock import Mock, patch

import pytest

from quarry.lib.http import _build_browser_headers, _check_robots_txt, create_session, get_html


def test_user_agent_rotation():
    """User agents are selected from realistic browser pool."""
    headers1 = _build_browser_headers("https://example.com")
    headers2 = _build_browser_headers("https://example.com")
    
    # Both should have User-Agent
    assert "User-Agent" in headers1
    assert "User-Agent" in headers2
    
    # Should be realistic (contain browser name)
    assert any(browser in headers1["User-Agent"] for browser in ["Chrome", "Firefox", "Safari", "Edg"])


def test_browser_headers_variation():
    """Headers vary to avoid fingerprinting."""
    # Generate multiple header sets
    header_sets = [_build_browser_headers("https://example.com") for _ in range(10)]
    
    # All should have core headers
    for headers in header_sets:
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers
    
    # Some should have referrer, some shouldn't (natural variation)
    referrer_counts = sum(1 for h in header_sets if "Referer" in h)
    assert 0 < referrer_counts < 10  # Not all or none


def test_chrome_specific_headers():
    """Chrome user agents get Chrome-specific headers."""
    chrome_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    headers = _build_browser_headers("https://example.com", user_agent=chrome_ua)
    
    # Chrome sends Sec-Ch-Ua headers
    assert "Sec-Ch-Ua" in headers
    assert "Sec-Ch-Ua-Mobile" in headers
    assert "Sec-Ch-Ua-Platform" in headers


def test_custom_referrer():
    """Custom referrer is respected."""
    headers = _build_browser_headers("https://example.com", referrer="https://google.com")
    assert headers["Referer"] == "https://google.com"


def test_robots_txt_allowed():
    """URLs allowed by robots.txt pass check."""
    # Mock successful robots.txt fetch
    with patch("quarry.lib.http.RobotFileParser") as mock_parser_class:
        mock_parser = Mock()
        mock_parser.can_fetch.return_value = True
        mock_parser_class.return_value = mock_parser
        
        # Clear cache to ensure fresh check
        from quarry.lib.http import _ROBOTS_CACHE
        _ROBOTS_CACHE.clear()
        
        result = _check_robots_txt("https://example.com/page", "TestBot/1.0")
        assert result is True


def test_robots_txt_disallowed():
    """URLs disallowed by robots.txt fail check."""
    with patch("quarry.lib.http.RobotFileParser") as mock_parser_class:
        mock_parser = Mock()
        mock_parser.can_fetch.return_value = False
        mock_parser_class.return_value = mock_parser
        
        # Clear cache to ensure fresh check
        from quarry.lib.http import _ROBOTS_CACHE
        _ROBOTS_CACHE.clear()
        
        result = _check_robots_txt("https://example.com/admin", "TestBot/1.0")
        assert result is False


def test_robots_txt_fetch_failure():
    """If robots.txt fetch fails, assume allowed (permissive)."""
    with patch("quarry.lib.http.RobotFileParser") as mock_parser_class:
        mock_parser = Mock()
        mock_parser.read.side_effect = Exception("Network error")
        mock_parser_class.return_value = mock_parser
        
        # Clear cache to ensure fresh check
        from quarry.lib.http import _ROBOTS_CACHE
        _ROBOTS_CACHE.clear()
        
        # Should not raise, should assume allowed
        result = _check_robots_txt("https://example.com/page", "TestBot/1.0")
        assert result is True


def test_create_session():
    """Session factory creates configured session."""
    session = create_session()
    
    # Should have default headers
    assert "Accept" in session.headers
    assert "Accept-Language" in session.headers
    assert "DNT" in session.headers  # Do Not Track shows good faith


def test_get_html_respects_robots_txt():
    """get_html checks robots.txt when respect_robots=True."""
    with patch("quarry.lib.http._check_robots_txt") as mock_check:
        mock_check.return_value = False
        
        with pytest.raises(PermissionError, match="robots.txt disallows"):
            get_html("https://example.com/blocked", respect_robots=True)


def test_get_html_can_skip_robots_txt():
    """get_html can skip robots.txt check for testing."""
    with patch("quarry.lib.http._check_robots_txt") as mock_check:
        with patch("quarry.lib.http.requests.Session.get") as mock_get:
            mock_response = Mock()
            mock_response.text = "<html>Test</html>"
            mock_get.return_value = mock_response
            
            # Should not call robots.txt check
            get_html("https://example.com/page", respect_robots=False)
            mock_check.assert_not_called()
