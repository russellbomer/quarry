"""Tests for polish validators module."""

import pytest

from quarry.tools.polish.validators import (
    ValidationError,
    validate_date_format,
    validate_email,
    validate_length,
    validate_pattern,
    validate_range,
    validate_record,
    validate_required,
    validate_url,
)


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_error_message(self):
        """Test ValidationError message format."""
        error = ValidationError("email", "Invalid format")
        assert error.field == "email"
        assert error.message == "Invalid format"
        assert str(error) == "email: Invalid format"


class TestValidateRequired:
    """Tests for validate_required function."""

    def test_valid_field(self):
        """Test valid non-empty field."""
        record = {"name": "Alice"}
        # Should not raise
        validate_required(record, "name")

    def test_missing_field_raises(self):
        """Test missing field raises error."""
        record = {"other": "value"}
        with pytest.raises(ValidationError) as exc_info:
            validate_required(record, "name")
        assert "required but missing" in str(exc_info.value)

    def test_none_field_raises(self):
        """Test None field raises error."""
        record = {"name": None}
        with pytest.raises(ValidationError) as exc_info:
            validate_required(record, "name")
        assert "required but missing" in str(exc_info.value)

    def test_empty_string_raises(self):
        """Test empty string raises error."""
        record = {"name": "  "}
        with pytest.raises(ValidationError) as exc_info:
            validate_required(record, "name")
        assert "required but empty" in str(exc_info.value)


class TestValidateEmail:
    """Tests for validate_email function."""

    def test_valid_email(self):
        """Test valid email addresses."""
        assert validate_email("user@example.com")
        assert validate_email("user.name@example.com")
        assert validate_email("user+tag@example.org")
        assert validate_email("user123@subdomain.example.com")

    def test_invalid_email(self):
        """Test invalid email addresses."""
        assert not validate_email("invalid")
        assert not validate_email("@example.com")
        assert not validate_email("user@")
        assert not validate_email("user@.com")
        assert not validate_email("")

    def test_none_email(self):
        """Test None email returns False."""
        assert not validate_email(None)

    def test_non_string_email(self):
        """Test non-string email returns False."""
        assert not validate_email(123)  # type: ignore


class TestValidateUrl:
    """Tests for validate_url function."""

    def test_valid_url(self):
        """Test valid URLs."""
        assert validate_url("https://example.com")
        assert validate_url("http://example.com")
        assert validate_url("https://example.com/path")
        assert validate_url("https://example.com/path?query=1")

    def test_invalid_url(self):
        """Test invalid URLs."""
        assert not validate_url("example.com")  # No scheme
        assert not validate_url("ftp://example.com")  # Wrong scheme
        assert not validate_url("")
        assert not validate_url("not a url")

    def test_none_url(self):
        """Test None URL returns False."""
        assert not validate_url(None)

    def test_non_string_url(self):
        """Test non-string URL returns False."""
        assert not validate_url(123)  # type: ignore


class TestValidateDateFormat:
    """Tests for validate_date_format function."""

    def test_valid_date(self):
        """Test valid ISO date format."""
        assert validate_date_format("2024-01-15")
        assert validate_date_format("1999-12-31")

    def test_invalid_date(self):
        """Test invalid date formats."""
        assert not validate_date_format("01-15-2024")  # Wrong order
        assert not validate_date_format("2024/01/15")  # Wrong separator
        assert not validate_date_format("2024-1-15")  # Missing leading zero
        assert not validate_date_format("")

    def test_custom_pattern(self):
        """Test custom date pattern."""
        pattern = r"^\d{2}/\d{2}/\d{4}$"
        assert validate_date_format("01/15/2024", pattern)
        assert not validate_date_format("2024-01-15", pattern)

    def test_none_date(self):
        """Test None date returns False."""
        assert not validate_date_format(None)


class TestValidateLength:
    """Tests for validate_length function."""

    def test_valid_length(self):
        """Test valid string lengths."""
        assert validate_length("hello", min_len=1)
        assert validate_length("hello", max_len=10)
        assert validate_length("hello", min_len=1, max_len=10)

    def test_too_short(self):
        """Test string too short."""
        assert not validate_length("hi", min_len=5)

    def test_too_long(self):
        """Test string too long."""
        assert not validate_length("hello world", max_len=5)

    def test_exact_bounds(self):
        """Test exact boundary values."""
        assert validate_length("hello", min_len=5, max_len=5)

    def test_none_value(self):
        """Test None value returns False."""
        assert not validate_length(None, min_len=1)

    def test_non_string_value(self):
        """Test non-string value returns False."""
        assert not validate_length(123, min_len=1)  # type: ignore

    def test_no_constraints(self):
        """Test with no constraints (always valid)."""
        assert validate_length("anything")


class TestValidateRange:
    """Tests for validate_range function."""

    def test_valid_range(self):
        """Test valid numeric ranges."""
        assert validate_range(5, min_val=1, max_val=10)
        assert validate_range(1, min_val=1)
        assert validate_range(10, max_val=10)

    def test_below_min(self):
        """Test value below minimum."""
        assert not validate_range(0, min_val=1)

    def test_above_max(self):
        """Test value above maximum."""
        assert not validate_range(11, max_val=10)

    def test_float_values(self):
        """Test float values."""
        assert validate_range(5.5, min_val=5.0, max_val=6.0)
        assert not validate_range(4.9, min_val=5.0)

    def test_none_value(self):
        """Test None value returns False."""
        assert not validate_range(None, min_val=1)

    def test_non_numeric_value(self):
        """Test non-numeric value returns False."""
        assert not validate_range("five", min_val=1)  # type: ignore


class TestValidatePattern:
    """Tests for validate_pattern function."""

    def test_valid_pattern(self):
        """Test valid pattern matches."""
        assert validate_pattern("abc123", r"^[a-z]+[0-9]+$")
        assert validate_pattern("hello", r"^hello$")

    def test_invalid_pattern(self):
        """Test invalid pattern matches."""
        assert not validate_pattern("123abc", r"^[a-z]+[0-9]+$")

    def test_none_value(self):
        """Test None value returns False."""
        assert not validate_pattern(None, r".*")

    def test_non_string_value(self):
        """Test non-string value returns False."""
        assert not validate_pattern(123, r"\d+")  # type: ignore


class TestValidateRecord:
    """Tests for validate_record function."""

    def test_valid_record(self):
        """Test completely valid record."""
        record = {
            "email": "user@example.com",
            "url": "https://example.com",
            "name": "Alice",
        }
        rules = {
            "email": {"type": "email", "required": True},
            "url": {"type": "url"},
            "name": {"required": True, "min_length": 2},
        }

        errors = validate_record(record, rules)
        assert errors == []

    def test_missing_required_field(self):
        """Test missing required field."""
        record = {"other": "value"}
        rules = {"name": {"required": True}}

        errors = validate_record(record, rules)
        assert len(errors) == 1
        assert errors[0].field == "name"

    def test_invalid_email_type(self):
        """Test invalid email type validation."""
        record = {"email": "not-an-email"}
        rules = {"email": {"type": "email"}}

        errors = validate_record(record, rules)
        assert len(errors) == 1
        assert "email" in errors[0].field

    def test_invalid_url_type(self):
        """Test invalid URL type validation."""
        record = {"url": "not-a-url"}
        rules = {"url": {"type": "url"}}

        errors = validate_record(record, rules)
        assert len(errors) == 1

    def test_invalid_date_type(self):
        """Test invalid date type validation."""
        record = {"date": "invalid-date"}
        rules = {"date": {"type": "date"}}

        errors = validate_record(record, rules)
        assert len(errors) == 1

    def test_length_validation(self):
        """Test length validation."""
        record = {"name": "AB"}
        rules = {"name": {"min_length": 3}}

        errors = validate_record(record, rules)
        assert len(errors) == 1
        assert "Length" in errors[0].message

    def test_range_validation(self):
        """Test range validation."""
        record = {"age": 200}
        rules = {"age": {"min_value": 0, "max_value": 150}}

        errors = validate_record(record, rules)
        assert len(errors) == 1
        assert "range" in errors[0].message

    def test_pattern_validation(self):
        """Test pattern validation."""
        record = {"code": "abc"}
        rules = {"code": {"pattern": r"^\d+$"}}

        errors = validate_record(record, rules)
        assert len(errors) == 1
        assert "pattern" in errors[0].message

    def test_skip_none_non_required(self):
        """Test that None values are skipped for non-required fields."""
        record = {"optional": None}
        rules = {"optional": {"type": "email"}}

        errors = validate_record(record, rules)
        assert errors == []

    def test_multiple_errors(self):
        """Test multiple validation errors."""
        record = {"email": "bad", "url": "bad", "name": ""}
        rules = {
            "email": {"type": "email"},
            "url": {"type": "url"},
            "name": {"required": True},
        }

        errors = validate_record(record, rules)
        assert len(errors) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
