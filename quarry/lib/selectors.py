"""
Robust CSS selector utilities for handling modern frameworks.

Provides:
- SelectorChain: Multi-tier selector fallbacks for resilience
- build_robust_selector(): Smart selector building avoiding dynamic classes
- validate_selector(): Pre-deployment selector testing
- Utilities for handling CSS-in-JS and dynamic frameworks
"""

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from quarry.lib.bs4_utils import class_tokens

MIN_DYNAMIC_NAME_LEN = 3


class SelectorChain:
    """
    Multi-tier selector with fallbacks for resilience against CSS changes.

    Example:
        chain = SelectorChain([
            "h3.css-17p10p8 a",     # Specific (brittle)
            "h3 a",                  # Structural (more resilient)
            "article a:first-of-type"  # Semantic (most resilient)
        ])
        value = chain.select_one(element)
    """

    def __init__(self, selectors: list[str]):
        """
        Initialize selector chain.

        Args:
            selectors: List of selectors ordered from most to least specific
        """
        self.selectors = selectors

    def select_one(self, element: Tag) -> Tag | None:
        """Try selectors in order until one matches."""
        for selector in self.selectors:
            try:
                result = element.select_one(selector)
                if result:
                    return result
            except Exception:
                continue
        return None

    def select(self, element: Tag) -> list[Tag]:
        """Try selectors in order until one finds elements."""
        for selector in self.selectors:
            try:
                results = element.select(selector)
                if results:
                    return results
            except Exception:
                continue
        return []


def build_robust_selector(element: Tag, root: Tag | None = None) -> str:
    """
    Build a robust CSS selector that works despite structural changes.

    Uses stable markers (semantic tags, stable classes, IDs) and avoids
    relying on exact nesting depth or dynamic class names.

    Args:
        element: Target element to select
        root: Container element to build selector from (optional)

    Returns:
        CSS selector string
    """
    if not element or not hasattr(element, 'name'):
        return ""

    # If element has an ID, that's the most stable selector
    elem_id_val = element.get("id")
    elem_id = elem_id_val if isinstance(elem_id_val, str) else None
    if elem_id and not _looks_dynamic(elem_id):
        return f"#{elem_id}"

    # Build path from root to element using stable markers
    path_parts: list[str] = []
    current: Tag | None = element
    max_depth = 15  # Prevent infinite loops
    depth = 0

    while current is not None and current.name and depth < max_depth:
        depth += 1

        # If this is the root, add it and stop
        if root is not None and current == root:
            marker = _get_stable_marker(current)
            if marker and marker not in ["div", "span"]:
                path_parts.insert(0, marker)
            break

        # Get stable marker for current element
        marker = _get_stable_marker(current)
        if marker:
            # Skip generic divs/spans without classes (reduces noise in deep nesting)
            if marker not in ["div", "span"]:
                path_parts.insert(0, marker)

            # If we found a very stable marker (ID, semantic tag with unique class),
            # we can stop here UNLESS we have a root to reach
            if _is_very_stable(marker) and not root:
                break

        parent = current.parent if isinstance(current.parent, Tag) else None
        current = parent

    # Join with descendant combinator (space) for flexibility
    # This works even if intermediate elements are added/removed
    if path_parts:
        return " ".join(path_parts)

    # Fallback: just the tag name
    return element.name


def _get_stable_marker(element: Tag) -> str | None:
    """
    Get the most stable identifier for an element.

    Priority:
    1. Non-dynamic ID
    2. Semantic tag (article, header, nav, etc.)
    3. Stable class name (not hash-like)
    4. Tag name
    """
    # Check for stable ID
    elem_id_val = element.get("id")
    elem_id = elem_id_val if isinstance(elem_id_val, str) else None
    if elem_id and not _looks_dynamic(elem_id):
        return f"#{elem_id}"

    # Semantic tags are very stable
    semantic_tags = {
        "article",
        "header",
        "footer",
        "nav",
        "aside",
        "main",
        "section",
        "time",
        "figure",
        "figcaption",
    }

    if element.name in semantic_tags:
        # Combine with stable class if available
        stable_classes = [c for c in class_tokens(element) if not _looks_dynamic(c)]
        if stable_classes:
            return f"{element.name}.{stable_classes[0]}"
        return element.name

    # Look for stable class names
    stable_classes = [c for c in class_tokens(element) if not _looks_dynamic(c)]

    if stable_classes:
        # Prefer semantic class names
        semantic_keywords = [
            "title",
            "heading",
            "content",
            "article",
            "post",
            "item",
            "container",
            "wrapper",
            "card",
            "list",
            "meta",
            "author",
            "date",
        ]

        for cls in stable_classes:
            if any(keyword in cls.lower() for keyword in semantic_keywords):
                return f".{cls}"

        # Return first stable class
        return f".{stable_classes[0]}"

    # Fallback: tag name with nth-of-type if needed
    # (but only for common container tags)
    if element.name in ["div", "span", "li", "tr", "td"]:
        # Check if there are siblings with same tag
        parent = element.parent if isinstance(element.parent, Tag) else None
        siblings = [
            s
            for s in (parent.children if parent else [])
            if hasattr(s, 'name') and s.name == element.name
        ]
        if len(siblings) > 1:
            index = siblings.index(element) + 1  # nth-of-type is 1-indexed
            return f"{element.name}:nth-of-type({index})"

    return element.name


def _looks_dynamic(name: str) -> bool:
    """
    Check if a class/ID name looks dynamically generated.

    Examples of dynamic names:
    - Random hashes: "css-1a2b3c4", "sc-1x2y3z"
    - UUIDs: "elem-550e8400-e29b-41d4"
    - Build artifacts: "jsx-2871293847"
    """
    if not name:
        return True

    # Very short names are often dynamic
    if len(name) < MIN_DYNAMIC_NAME_LEN:
        return True

    # Check for common dynamic prefixes
    dynamic_prefixes = ["css-", "sc-", "jsx-", "styled-", "emotion-", "MuiBox-"]
    if any(name.startswith(prefix) for prefix in dynamic_prefixes):
        return True

    # Count hex-like segments (common in hashes)
    hex_segments = re.findall(r'[0-9a-f]{6,}', name.lower())
    if hex_segments:
        return True

    # UUID pattern
    if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', name.lower()):
        return True

    # Long numeric suffixes often dynamic
    if re.search(r'-?\d{8,}$', name):
        return True

    return False


def _is_very_stable(marker: str) -> bool:
    """Check if a marker is very stable (can stop path building)."""
    # IDs are very stable
    if marker.startswith("#"):
        return True

    # Semantic tags with specific classes are stable
    semantic_tags = ["article", "header", "footer", "nav", "main"]
    if any(marker.startswith(tag) for tag in semantic_tags) and "." in marker:
        return True

    return False


def simplify_selector(selector: str) -> str:
    """
    Simplify a selector by removing redundant parts.

    Example: "div.container > div > div > a" -> ".container a"
    """
    parts = selector.split()

    # Remove generic divs and spans
    filtered = []
    for part in parts:
        if part in [">", "+"]:
            continue  # Remove direct child combinators
        if part in ["div", "span"]:
            continue  # Remove generic tags

        # Remove tag from tag.class patterns (keep just .class)
        if "." in part and not part.startswith("."):
            # "div.container" -> ".container"
            parts_split = part.split(".", 1)
            if parts_split[0] in ["div", "span"]:
                filtered.append(f".{parts_split[1]}")
            else:
                filtered.append(part)
        else:
            filtered.append(part)

    # Return simplified selector
    return " ".join(filtered) if filtered else selector


def extract_structural_pattern(selector: str) -> str:
    """
    Convert specific selector to structural pattern by removing dynamic classes.

    Examples:
        "h3.css-17p10p8 a" -> "h3 a"
        ".css-1jydbgl article" -> "article"
        "div.emotion-abc > span" -> "div > span"

    Args:
        selector: CSS selector string

    Returns:
        Selector with dynamic classes removed
    """
    # Remove dynamic classes
    pattern = re.sub(r'\.(css-[a-z0-9]+|emotion-[a-z0-9]+|_[a-z0-9]{6,})', '', selector)

    # Clean up extra spaces
    pattern = re.sub(r'\s+', ' ', pattern).strip()

    # Remove attribute selectors that might be dynamic
    pattern = re.sub(r'\[data-[a-z]+-[a-z0-9]{6,}.*?\]', '', pattern)

    return pattern


def validate_selector(
    soup: BeautifulSoup | Tag, selector: str, expected_count: int | None = None
) -> dict[str, Any]:
    """
    Validate that a selector works correctly on HTML.

    Args:
        soup: BeautifulSoup object or Tag to test selector on
        selector: CSS selector to validate
        expected_count: Optional expected number of matches

    Returns:
        Dict with validation results:
        {
            "valid": bool,
            "count": int,
            "sample_texts": list[str],
            "warnings": list[str]
        }
    """
    warnings = []

    try:
        elements = soup.select(selector)
        count = len(elements)

        # Get sample texts
        sample_texts = []
        for elem in elements[:3]:
            text = elem.get_text(strip=True)[:100]
            if text:
                sample_texts.append(text)

        # Check if count matches expectations
        if expected_count is not None and count != expected_count:
            warnings.append(f"Expected {expected_count} matches, got {count}")

        # Check if we got any matches
        if count == 0:
            warnings.append("Selector matched no elements")

        # Check if all matches are empty
        if count > 0 and not sample_texts:
            warnings.append("All matched elements are empty")

        # Check for dynamic classes in selector
        if re.search(r'\.(css-[a-z0-9]+|emotion-[a-z0-9]+)', selector):
            warnings.append("Selector contains dynamic CSS classes (may break on rebuild)")

        return {
            "valid": len(warnings) == 0,
            "count": count,
            "sample_texts": sample_texts,
            "warnings": warnings,
        }

    except Exception as e:
        return {
            "valid": False,
            "count": 0,
            "sample_texts": [],
            "warnings": [f"Selector parsing failed: {e}"],
        }


def build_fallback_chain(primary_selector: str, context: list[str] | None = None) -> SelectorChain:
    """
    Build a fallback chain from a specific selector.

    Args:
        primary_selector: The ideal/specific selector
        context: Optional context hints (e.g., ["class", "tag", "id"])

    Returns:
        SelectorChain with fallback selectors from most to least specific
    """
    chain = [primary_selector]

    # Add structural variant (without dynamic classes)
    structural = extract_structural_pattern(primary_selector)
    if structural and structural != primary_selector:
        chain.append(structural)

    # Add tag-only variant
    # Extract just the tag names
    tags = re.findall(r'\b(h[1-6]|article|section|div|span|a|p|time|img)\b', primary_selector)
    if tags:
        # Build hierarchy from tags
        tag_chain = " ".join(tags)
        if tag_chain not in chain:
            chain.append(tag_chain)

        # Also add just the final tag
        if len(tags) > 1 and tags[-1] not in chain:
            chain.append(tags[-1])

    return SelectorChain(chain)
