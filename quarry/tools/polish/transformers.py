"""Field transformation functions for Polish tool."""

import re
from collections.abc import Callable
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

# Custom transform registry
_CUSTOM_TRANSFORMS: dict[str, Callable[..., Any]] = {}


def register_transform(name: str):
    """
    Decorator to register a custom transformation function.

    Allows users to add custom transformations that can be used
    in the Polish tool via CLI or programmatically.

    Args:
        name: Name of the transformation (used in --transform)

    Returns:
        Decorator function

    Example:
        >>> from quarry.tools.polish.transformers import register_transform
        >>> @register_transform("custom_clean")
        ... def custom_clean(value):
        ...     return value.strip().replace("  ", " ")
        >>> # Now usable: quarry.polish data.jsonl --transform title:custom_clean
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        _CUSTOM_TRANSFORMS[name] = func
        return func

    return decorator


def normalize_text(text: str | None) -> str | None:
    """
    Normalize text by removing extra whitespace and standardizing.

    - Strips leading/trailing whitespace
    - Collapses multiple spaces to single space
    - Converts to lowercase (optional)

    Args:
        text: Input text

    Returns:
        Normalized text or None
    """
    if text is None or not isinstance(text, str):
        return text

    # Strip and collapse whitespace
    normalized = " ".join(text.split())
    return normalized if normalized else None


def clean_whitespace(text: str | None) -> str | None:
    """
    Clean whitespace without changing case.

    Args:
        text: Input text

    Returns:
        Cleaned text or None
    """
    if text is None or not isinstance(text, str):
        return text

    # Remove leading/trailing whitespace and collapse internal
    cleaned = " ".join(text.split())
    return cleaned if cleaned else None


def parse_date(
    date_str: str | None,
    formats: list[str] | None = None,
    default_format: str = "%Y-%m-%d",
) -> str | None:
    """
    Parse date string into ISO format.

    Args:
        date_str: Date string to parse
        formats: List of date format strings to try
        default_format: Default format to try first

    Returns:
        ISO format date string (YYYY-MM-DD) or None
    """
    if date_str is None or not isinstance(date_str, str):
        return None

    if formats is None:
        formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d %B %Y",
            "%d %b %Y",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ]

    # Try each format
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def extract_domain(url: str | None) -> str | None:
    """
    Extract domain from URL.

    Args:
        url: URL string

    Returns:
        Domain name or None
    """
    if url is None or not isinstance(url, str):
        return None

    try:
        # Handle relative URLs
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        parsed = urlparse(url)
        domain = parsed.netloc

        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]

        return domain if domain else None
    except Exception:
        return None


def truncate_text(text: str | None, max_length: int = 100) -> str | None:
    """
    Truncate text to maximum length.

    Args:
        text: Input text
        max_length: Maximum character length

    Returns:
        Truncated text or None
    """
    if text is None or not isinstance(text, str):
        return text

    if len(text) <= max_length:
        return text

    return text[:max_length].rstrip() + "..."


def remove_html_tags(text: str | None) -> str | None:
    """
    Remove HTML tags from text.

    Args:
        text: Input text with HTML

    Returns:
        Text without HTML tags
    """
    if text is None or not isinstance(text, str):
        return text

    # Simple regex to remove tags
    clean = re.sub(r"<[^>]+>", "", text)
    return clean_whitespace(clean)


def uppercase(text: str | None) -> str | None:
    """
    Convert text to uppercase.

    Args:
        text: Input text

    Returns:
        Uppercase text or None
    """
    if text is None or not isinstance(text, str):
        return text
    return text.upper()


def lowercase(text: str | None) -> str | None:
    """
    Convert text to lowercase.

    Args:
        text: Input text

    Returns:
        Lowercase text or None
    """
    if text is None or not isinstance(text, str):
        return text
    return text.lower()


def extract_number(text: str | None) -> float | None:
    """
    Extract numeric value from text.

    Handles currency symbols, commas, and other formatting.
    Examples: "$99.99" -> 99.99, "1,234.56" -> 1234.56

    Args:
        text: Input text containing numbers

    Returns:
        Extracted number or None
    """
    if text is None or not isinstance(text, str):
        return None

    # First remove commas (thousand separators)
    text = text.replace(",", "")

    # Extract all digits, decimal point, and minus sign
    cleaned = re.sub(r"[^0-9.-]", "", text)

    # Handle multiple decimals or minus signs
    if not cleaned:
        return None

    # Remove extra decimals (keep only the first one)
    if cleaned.count(".") > 1:
        parts = cleaned.split(".")
        cleaned = parts[0] + "." + "".join(parts[1:])

    # Handle multiple minus signs (keep only if at start)
    if cleaned.count("-") > 0:
        is_negative = cleaned[0] == "-"
        cleaned = cleaned.replace("-", "")
        if is_negative:
            cleaned = "-" + cleaned

    try:
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def to_boolean(value: str | bool | int | None) -> bool | None:
    """
    Convert string to boolean.

    Recognizes: yes/no, true/false, y/n, 1/0, on/off

    Args:
        value: Input value to convert

    Returns:
        Boolean value or None
    """
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return bool(value)

    if not isinstance(value, str):
        return None

    normalized = value.lower().strip()
    true_values = {"yes", "true", "y", "1", "on", "t"}
    false_values = {"no", "false", "n", "0", "off", "f"}

    if normalized in true_values:
        return True
    elif normalized in false_values:
        return False
    else:
        return None


def round_number(value: float | int | str | None, decimals: int = 0) -> float | None:
    """
    Round numeric value to specified decimal places.

    Args:
        value: Input value to round
        decimals: Number of decimal places (default: 0)

    Returns:
        Rounded number or None
    """
    if value is None:
        return None

    try:
        num = float(value) if isinstance(value, str) else value
        return round(float(num), decimals)
    except (ValueError, TypeError):
        return None


def to_absolute_url(url: str | None, base_url: str) -> str | None:
    """
    Convert relative URL to absolute URL.

    Args:
        url: Relative or absolute URL
        base_url: Base URL to resolve relative URLs against

    Returns:
        Absolute URL or None
    """
    if url is None or not isinstance(url, str):
        return None

    if not base_url:
        return url

    # Already absolute
    if url.startswith("http://") or url.startswith("https://"):
        return url

    from urllib.parse import urljoin

    try:
        return urljoin(base_url, url)
    except Exception:
        return None


def apply_transformation(
    value: Any,
    transformation: str,
    **kwargs: Any,
) -> Any:
    """
    Apply named transformation to a value.

    Args:
        value: Input value
        transformation: Transformation name
        **kwargs: Additional arguments for transformation

    Returns:
        Transformed value
    """
    transformations: dict[str, Callable[..., Any]] = {
        "normalize_text": normalize_text,
        "clean_whitespace": clean_whitespace,
        "clean_text": clean_whitespace,  # Alias for documentation compatibility
        "parse_date": parse_date,
        "extract_domain": extract_domain,
        "extract_number": extract_number,
        "truncate_text": truncate_text,
        "remove_html_tags": remove_html_tags,
        "strip_html": remove_html_tags,  # Alias
        "uppercase": uppercase,
        "to_uppercase": uppercase,  # Alias for documentation compatibility
        "lowercase": lowercase,
        "to_lowercase": lowercase,  # Alias for documentation compatibility
        "to_boolean": to_boolean,
        "round": round_number,
        "to_absolute": to_absolute_url,
    }

    # Include custom registered transforms
    transformations.update(_CUSTOM_TRANSFORMS)

    func: Callable[..., Any] | None = transformations.get(transformation)
    if func is None:
        raise ValueError(f"Unknown transformation: {transformation}")

    return func(value, **kwargs)
