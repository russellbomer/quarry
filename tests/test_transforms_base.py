"""Tests for transforms base module."""

import pytest

from quarry.transforms.base import safe_to_iso


class TestSafeToIso:
    """Tests for safe_to_iso function."""

    def test_valid_iso_datetime(self):
        """Test valid ISO datetime string."""
        result = safe_to_iso("2024-01-15T10:30:00Z")
        assert result is not None
        assert "2024-01-15" in result

    def test_valid_date_only(self):
        """Test valid date-only string."""
        result = safe_to_iso("2024-01-15")
        assert result is not None
        assert "2024-01-15" in result

    def test_valid_datetime_no_tz(self):
        """Test datetime without timezone."""
        result = safe_to_iso("2024-01-15 10:30:00")
        assert result is not None
        assert "2024-01-15" in result

    def test_various_formats(self):
        """Test various date formats."""
        # These should all be parseable by pandas
        valid_dates = [
            "January 15, 2024",
            "15 Jan 2024",
            "2024/01/15",
        ]
        for date_str in valid_dates:
            result = safe_to_iso(date_str)
            assert result is not None, f"Failed to parse: {date_str}"

    def test_none_input(self):
        """Test None input returns None."""
        assert safe_to_iso(None) is None

    def test_empty_string(self):
        """Test empty string returns None."""
        assert safe_to_iso("") is None

    def test_invalid_date(self):
        """Test invalid date string returns None."""
        assert safe_to_iso("not a date") is None
        assert safe_to_iso("abc123") is None

    def test_result_is_iso_format(self):
        """Test that result is in ISO format."""
        result = safe_to_iso("2024-01-15")
        assert result is not None
        # ISO format should contain T or be parseable
        assert "2024" in result
        assert "01" in result
        assert "15" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
