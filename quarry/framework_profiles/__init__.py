"""Framework-specific HTML structure profiles for better field detection."""

from bs4 import Tag

from .base import FrameworkProfile, _get_element_classes
from .cms import DrupalViewsProfile, WordPressProfile
from .css import BootstrapProfile, TailwindProfile
from .ecommerce import ShopifyProfile, WooCommerceProfile
from .frameworks import (
    DjangoAdminProfile,
    NextJSProfile,
    ReactComponentProfile,
    VueJSProfile,
)
from .universal import OpenGraphProfile, SchemaOrgProfile, TwitterCardsProfile

# Registry of all available profiles
# Order matters: More specific frameworks should come before generic ones
FRAMEWORK_PROFILES: list[type[FrameworkProfile]] = [
    # Universal/meta profiles (high priority - structured data)
    SchemaOrgProfile,  # Schema.org microdata (universal)
    OpenGraphProfile,  # Open Graph meta tags (universal)
    TwitterCardsProfile,  # Twitter Card meta tags (universal)
    # Framework-specific profiles
    DjangoAdminProfile,  # Very specific (Django admin)
    NextJSProfile,  # Specific (Next.js apps)
    ReactComponentProfile,  # Specific (React apps)
    VueJSProfile,  # Specific (Vue.js apps)
    DrupalViewsProfile,  # Specific CMS
    WooCommerceProfile,  # E-commerce (WordPress plugin)
    ShopifyProfile,  # E-commerce platform
    TailwindProfile,  # Framework/utility CSS
    BootstrapProfile,  # Component library
    WordPressProfile,  # Generic CMS (might match "post" class from others)
]


def detect_framework(html: str, item_element: Tag | None = None) -> type[FrameworkProfile] | None:
    """
    Detect which framework is being used (returns best match above threshold).

    Args:
        html: Full page HTML
        item_element: Optional item container element

    Returns:
        Detected framework profile class or None if no match above threshold (40)
    """
    best_score = 0
    best_profile = None

    for profile_class in FRAMEWORK_PROFILES:
        score = profile_class.detect(html, item_element)
        if score > best_score:
            best_score = score
            best_profile = profile_class

    # Return best match if above threshold (lowered to 40 for better detection)
    return best_profile if best_score >= 40 else None


def detect_all_frameworks(
    html: str, item_element: Tag | None = None
) -> list[tuple[type[FrameworkProfile], int]]:
    """
    Detect all frameworks with their confidence scores.

    Args:
        html: Full page HTML
        item_element: Optional item container element

    Returns:
        List of (profile_class, score) tuples sorted by score (highest first).
        Only includes profiles with score > 0.
    """
    results = []

    for profile_class in FRAMEWORK_PROFILES:
        score = profile_class.detect(html, item_element)
        if score > 0:
            results.append((profile_class, score))

    # Sort by score descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def get_framework_field_selector(
    framework: type[FrameworkProfile],
    item_element: Tag,
    field_type: str,
) -> str | None:
    """
    Get field selector using framework-specific knowledge.

    Args:
        framework: Framework profile class
        item_element: Item container element
        field_type: Field type to detect

    Returns:
        CSS selector string or None
    """
    return framework.generate_field_selector(item_element, field_type)


def is_framework_pattern(selector: str, framework: type[FrameworkProfile] | None) -> bool:
    """
    Check if a selector matches known framework patterns.

    Args:
        selector: CSS selector to check
        framework: Detected framework profile class or None

    Returns:
        True if selector matches framework patterns
    """
    if not framework:
        return False

    # Check if selector matches any container pattern
    for pattern in framework.get_item_selector_hints():
        if pattern in selector or selector in pattern:
            return True

    # Check if selector matches any field mapping pattern
    for field_patterns in framework.get_field_mappings().values():
        for pattern in field_patterns:
            # Remove ::attr() suffix for comparison
            base_pattern = pattern.split("::attr(")[0] if "::attr(" in pattern else pattern
            if base_pattern in selector or selector in base_pattern:
                return True

    return False


__all__ = [
    "FRAMEWORK_PROFILES",
    "BootstrapProfile",
    "DjangoAdminProfile",
    "FrameworkProfile",
    "NextJSProfile",
    "OpenGraphProfile",
    "ReactComponentProfile",
    "SchemaOrgProfile",
    "ShopifyProfile",
    "TailwindProfile",
    "TwitterCardsProfile",
    "VueJSProfile",
    "WooCommerceProfile",
    "WordPressProfile",
    "_get_element_classes",
    "detect_all_frameworks",
    "detect_framework",
    "get_framework_field_selector",
    "is_framework_pattern",
]
