"""Field transformation functions for Polish tool."""

import re
from collections.abc import Callable
from datetime import datetime
from typing import Any
from urllib.parse import urlparse


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
        "parse_date": parse_date,
        "extract_domain": extract_domain,
        "truncate_text": truncate_text,
        "remove_html_tags": remove_html_tags,
        "strip_html": remove_html_tags,  # Alias
        "uppercase": uppercase,
        "lowercase": lowercase,
    }

    func: Callable[..., Any] | None = transformations.get(transformation)
    if func is None:
        raise ValueError(f"Unknown transformation: {transformation}")

    return func(value, **kwargs)
