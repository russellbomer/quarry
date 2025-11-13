"""Validation functions for Polish tool."""

import re
from typing import Any


class ValidationError(Exception):
    """Exception raised when validation fails."""
    
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def validate_required(record: dict[str, Any], field: str) -> None:
    """
    Validate that a field exists and is not None/empty.
    
    Args:
        record: Record to validate
        field: Field name
    
    Raises:
        ValidationError: If field is missing or empty
    """
    value = record.get(field)
    
    if value is None:
        raise ValidationError(field, "Field is required but missing")
    
    if isinstance(value, str) and not value.strip():
        raise ValidationError(field, "Field is required but empty")


def validate_email(value: str | None) -> bool:
    """
    Validate email format.
    
    Args:
        value: Email string
    
    Returns:
        True if valid email format
    """
    if value is None or not isinstance(value, str):
        return False
    
    # Simple email pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, value))


def validate_url(value: str | None) -> bool:
    """
    Validate URL format.
    
    Args:
        value: URL string
    
    Returns:
        True if valid URL format
    """
    if value is None or not isinstance(value, str):
        return False
    
    # URL pattern
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, value, re.IGNORECASE))


def validate_date_format(value: str | None, format_pattern: str = r"^\d{4}-\d{2}-\d{2}$") -> bool:
    """
    Validate date format.
    
    Args:
        value: Date string
        format_pattern: Regex pattern for date format
    
    Returns:
        True if matches pattern
    """
    if value is None or not isinstance(value, str):
        return False
    
    return bool(re.match(format_pattern, value))


def validate_length(value: str | None, min_len: int | None = None, max_len: int | None = None) -> bool:
    """
    Validate string length.
    
    Args:
        value: String to validate
        min_len: Minimum length (inclusive)
        max_len: Maximum length (inclusive)
    
    Returns:
        True if length is within bounds
    """
    if value is None or not isinstance(value, str):
        return False
    
    length = len(value)
    
    if min_len is not None and length < min_len:
        return False
    
    if max_len is not None and length > max_len:
        return False
    
    return True


def validate_range(value: float | int | None, min_val: float | None = None, max_val: float | None = None) -> bool:
    """
    Validate numeric range.
    
    Args:
        value: Number to validate
        min_val: Minimum value (inclusive)
        max_val: Maximum value (inclusive)
    
    Returns:
        True if value is within range
    """
    if value is None:
        return False
    
    if not isinstance(value, (int, float)):
        return False
    
    if min_val is not None and value < min_val:
        return False
    
    if max_val is not None and value > max_val:
        return False
    
    return True


def validate_pattern(value: str | None, pattern: str) -> bool:
    """
    Validate against regex pattern.
    
    Args:
        value: String to validate
        pattern: Regex pattern
    
    Returns:
        True if matches pattern
    """
    if value is None or not isinstance(value, str):
        return False
    
    return bool(re.match(pattern, value))


def validate_record(
    record: dict[str, Any],
    rules: dict[str, dict[str, Any]],
) -> list[ValidationError]:
    """
    Validate a record against multiple rules.
    
    Args:
        record: Record to validate
        rules: Dictionary of field -> validation rules
               Example: {
                   "email": {"type": "email"},
                   "url": {"type": "url"},
                   "title": {"required": True, "min_length": 5},
               }
    
    Returns:
        List of ValidationError objects (empty if valid)
    """
    errors = []
    
    for field, field_rules in rules.items():
        value = record.get(field)
        
        # Check required
        if field_rules.get("required"):
            try:
                validate_required(record, field)
            except ValidationError as e:
                errors.append(e)
                continue
        
        # Skip other validations if value is None and not required
        if value is None and not field_rules.get("required"):
            continue
        
        # Type-specific validation
        validation_type = field_rules.get("type")
        if validation_type == "email":
            if not validate_email(value):
                errors.append(ValidationError(field, "Invalid email format"))
        
        elif validation_type == "url":
            if not validate_url(value):
                errors.append(ValidationError(field, "Invalid URL format"))
        
        elif validation_type == "date":
            pattern = field_rules.get("pattern", r"^\d{4}-\d{2}-\d{2}$")
            if not validate_date_format(value, pattern):
                errors.append(ValidationError(field, "Invalid date format"))
        
        # Length validation
        if "min_length" in field_rules or "max_length" in field_rules:
            if not validate_length(
                value,
                min_len=field_rules.get("min_length"),
                max_len=field_rules.get("max_length"),
            ):
                errors.append(ValidationError(field, "Length out of bounds"))
        
        # Range validation
        if "min_value" in field_rules or "max_value" in field_rules:
            if not validate_range(
                value,
                min_val=field_rules.get("min_value"),
                max_val=field_rules.get("max_value"),
            ):
                errors.append(ValidationError(field, "Value out of range"))
        
        # Pattern validation
        if "pattern" in field_rules and validation_type != "date":
            if not validate_pattern(value, field_rules["pattern"]):
                errors.append(ValidationError(field, "Does not match pattern"))
    
    return errors
