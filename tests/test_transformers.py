"""Tests for polish transformers module."""

import pytest

from quarry.tools.polish.transformers import (
    apply_transformation,
    clean_whitespace,
    extract_domain,
    lowercase,
    normalize_text,
    parse_date,
    remove_html_tags,
    truncate_text,
    uppercase,
)


class TestNormalizeText:
    """Tests for normalize_text function."""

    def test_removes_extra_whitespace(self):
        """Test collapsing extra whitespace."""
        assert normalize_text("hello   world") == "hello world"
        assert normalize_text("  hello  world  ") == "hello world"

    def test_strips_leading_trailing(self):
        """Test stripping leading/trailing whitespace."""
        assert normalize_text("  hello  ") == "hello"

    def test_handles_tabs_newlines(self):
        """Test handling tabs and newlines."""
        assert normalize_text("hello\n\tworld") == "hello world"

    def test_none_input(self):
        """Test None input returns None."""
        assert normalize_text(None) is None

    def test_non_string_input(self):
        """Test non-string input returned as-is."""
        assert normalize_text(123) == 123  # type: ignore

    def test_empty_result_returns_none(self):
        """Test empty result returns None."""
        assert normalize_text("   ") is None


class TestCleanWhitespace:
    """Tests for clean_whitespace function."""

    def test_collapses_whitespace(self):
        """Test collapsing whitespace."""
        assert clean_whitespace("hello   world") == "hello world"

    def test_none_input(self):
        """Test None input returns None."""
        assert clean_whitespace(None) is None

    def test_non_string_returns_as_is(self):
        """Test non-string returns as-is."""
        assert clean_whitespace(123) == 123  # type: ignore


class TestParseDate:
    """Tests for parse_date function."""

    def test_iso_format(self):
        """Test ISO format date."""
        assert parse_date("2024-01-15") == "2024-01-15"

    def test_us_format(self):
        """Test US format date (MM/DD/YYYY)."""
        assert parse_date("01/15/2024") == "2024-01-15"

    def test_long_format(self):
        """Test long format date."""
        assert parse_date("January 15, 2024") == "2024-01-15"

    def test_short_month_format(self):
        """Test short month format."""
        assert parse_date("Jan 15, 2024") == "2024-01-15"

    def test_datetime_format(self):
        """Test datetime format."""
        assert parse_date("2024-01-15T10:30:00") == "2024-01-15"

    def test_custom_formats(self):
        """Test custom format list."""
        result = parse_date("15-01-2024", formats=["%d-%m-%Y"])
        assert result == "2024-01-15"

    def test_none_input(self):
        """Test None input returns None."""
        assert parse_date(None) is None

    def test_non_string_input(self):
        """Test non-string input returns None."""
        assert parse_date(123) is None  # type: ignore

    def test_invalid_date(self):
        """Test invalid date returns None."""
        assert parse_date("not a date") is None


class TestExtractDomain:
    """Tests for extract_domain function."""

    def test_full_url(self):
        """Test extracting domain from full URL."""
        assert extract_domain("https://example.com/path") == "example.com"

    def test_with_www(self):
        """Test removing www prefix."""
        assert extract_domain("https://www.example.com") == "example.com"

    def test_http_url(self):
        """Test HTTP URL."""
        assert extract_domain("http://example.com") == "example.com"

    def test_without_scheme(self):
        """Test URL without scheme."""
        assert extract_domain("example.com/path") == "example.com"

    def test_subdomain(self):
        """Test URL with subdomain."""
        assert extract_domain("https://blog.example.com") == "blog.example.com"

    def test_none_input(self):
        """Test None input returns None."""
        assert extract_domain(None) is None

    def test_non_string_input(self):
        """Test non-string input returns None."""
        assert extract_domain(123) is None  # type: ignore


class TestTruncateText:
    """Tests for truncate_text function."""

    def test_short_text_unchanged(self):
        """Test short text is unchanged."""
        assert truncate_text("hello", max_length=10) == "hello"

    def test_truncates_long_text(self):
        """Test truncating long text."""
        result = truncate_text("hello world", max_length=5)
        assert result == "hello..."

    def test_default_length(self):
        """Test default max length is 100."""
        text = "a" * 50
        assert truncate_text(text) == text  # Under 100, unchanged

    def test_none_input(self):
        """Test None input returns None."""
        assert truncate_text(None) is None

    def test_non_string_input(self):
        """Test non-string input returned as-is."""
        assert truncate_text(123) == 123  # type: ignore


class TestRemoveHtmlTags:
    """Tests for remove_html_tags function."""

    def test_removes_tags(self):
        """Test removing HTML tags."""
        assert remove_html_tags("<p>Hello</p>") == "Hello"

    def test_removes_nested_tags(self):
        """Test removing nested tags."""
        assert remove_html_tags("<div><p>Hello</p></div>") == "Hello"

    def test_removes_tags_with_attrs(self):
        """Test removing tags with attributes."""
        result = remove_html_tags('<a href="https://example.com">Link</a>')
        assert result == "Link"

    def test_preserves_text(self):
        """Test preserving text content."""
        result = remove_html_tags("<b>Bold</b> and <i>italic</i>")
        assert result == "Bold and italic"

    def test_none_input(self):
        """Test None input returns None."""
        assert remove_html_tags(None) is None


class TestUppercase:
    """Tests for uppercase function."""

    def test_converts_to_upper(self):
        """Test converting to uppercase."""
        assert uppercase("hello") == "HELLO"

    def test_mixed_case(self):
        """Test mixed case input."""
        assert uppercase("Hello World") == "HELLO WORLD"

    def test_none_input(self):
        """Test None input returns None."""
        assert uppercase(None) is None

    def test_non_string_input(self):
        """Test non-string input returned as-is."""
        assert uppercase(123) == 123  # type: ignore


class TestLowercase:
    """Tests for lowercase function."""

    def test_converts_to_lower(self):
        """Test converting to lowercase."""
        assert lowercase("HELLO") == "hello"

    def test_mixed_case(self):
        """Test mixed case input."""
        assert lowercase("Hello World") == "hello world"

    def test_none_input(self):
        """Test None input returns None."""
        assert lowercase(None) is None


class TestApplyTransformation:
    """Tests for apply_transformation function."""

    def test_normalize_text(self):
        """Test applying normalize_text."""
        result = apply_transformation("  hello  world  ", "normalize_text")
        assert result == "hello world"

    def test_clean_whitespace(self):
        """Test applying clean_whitespace."""
        result = apply_transformation("  hello  ", "clean_whitespace")
        assert result == "hello"

    def test_parse_date(self):
        """Test applying parse_date."""
        result = apply_transformation("2024-01-15", "parse_date")
        assert result == "2024-01-15"

    def test_extract_domain(self):
        """Test applying extract_domain."""
        result = apply_transformation("https://example.com/path", "extract_domain")
        assert result == "example.com"

    def test_truncate_text_with_kwargs(self):
        """Test applying truncate_text with kwargs."""
        result = apply_transformation("hello world", "truncate_text", max_length=5)
        assert result == "hello..."

    def test_remove_html_tags(self):
        """Test applying remove_html_tags."""
        result = apply_transformation("<p>Hello</p>", "remove_html_tags")
        assert result == "Hello"

    def test_strip_html_alias(self):
        """Test strip_html alias for remove_html_tags."""
        result = apply_transformation("<b>Bold</b>", "strip_html")
        assert result == "Bold"

    def test_uppercase(self):
        """Test applying uppercase."""
        result = apply_transformation("hello", "uppercase")
        assert result == "HELLO"

    def test_lowercase(self):
        """Test applying lowercase."""
        result = apply_transformation("HELLO", "lowercase")
        assert result == "hello"

    def test_unknown_transformation_raises(self):
        """Test unknown transformation raises error."""
        with pytest.raises(ValueError) as exc_info:
            apply_transformation("value", "unknown_transform")
        assert "Unknown transformation" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
