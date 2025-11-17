"""Open Graph meta tag profile for social media metadata extraction."""

from bs4 import BeautifulSoup, Tag

from quarry.framework_profiles.base import FrameworkProfile
from quarry.lib.bs4_utils import attr_str


class OpenGraphProfile(FrameworkProfile):
    """
    Detect and extract Open Graph meta tags.

    Open Graph is a protocol for social media sharing metadata.
    Meta tags like og:title, og:description, og:image are highly
    structured and reliable for extraction.
    """

    name = "opengraph"

    @classmethod
    def detect(cls, html: str, item_element: Tag | None = None) -> int:
        """
        Detect Open Graph meta tags with confidence scoring.

        Returns:
            Confidence score 0-100. Threshold for detection is 40.
        """
        score = 0

        # Count Open Graph meta tags
        og_count = html.count('property="og:')
        if og_count >= 5:
            score += 50  # Many OG tags = high confidence
        elif og_count >= 3:
            score += 40  # Some OG tags = medium confidence
        elif og_count >= 1:
            score += 25  # Few OG tags = low confidence

        # Check for common Open Graph tags
        if 'property="og:title"' in html:
            score += 15
        if 'property="og:description"' in html:
            score += 10
        if 'property="og:image"' in html:
            score += 10
        if 'property="og:url"' in html:
            score += 10
        if 'property="og:type"' in html:
            score += 5

        return score

    @classmethod
    def get_item_selector_hints(cls) -> list[str]:
        """
        Open Graph tags are in <head>, not item containers.

        Returns:
            Empty list (OG tags don't define item containers)
        """
        # Open Graph is metadata, not container-based
        # Return semantic fallbacks
        return [
            "article",
            "main",
            "[role='main']",
        ]

    @classmethod
    def get_field_mappings(cls) -> dict[str, list[str]]:
        """
        Get field type to Open Graph meta tag mappings.

        Returns:
            Dict mapping field types to OG meta tag selectors.
            Note: These are page-level metadata, not item-level.
        """
        return {
            # Title
            "title": [
                "meta[property='og:title']::attr(content)",
                "meta[name='og:title']::attr(content)",
            ],
            # URL
            "link": [
                "meta[property='og:url']::attr(content)",
                "meta[name='og:url']::attr(content)",
            ],
            "url": [
                "meta[property='og:url']::attr(content)",
                "meta[name='og:url']::attr(content)",
            ],
            # Description
            "description": [
                "meta[property='og:description']::attr(content)",
                "meta[name='og:description']::attr(content)",
            ],
            # Image
            "image": [
                "meta[property='og:image']::attr(content)",
                "meta[property='og:image:url']::attr(content)",
                "meta[name='og:image']::attr(content)",
            ],
            # Type/Category
            "category": [
                "meta[property='og:type']::attr(content)",
                "meta[property='article:section']::attr(content)",
            ],
            # Date
            "date": [
                "meta[property='article:published_time']::attr(content)",
                "meta[property='og:updated_time']::attr(content)",
                "meta[property='article:modified_time']::attr(content)",
            ],
            # Author
            "author": [
                "meta[property='article:author']::attr(content)",
                "meta[property='og:author']::attr(content)",
            ],
            # Site name (publisher)
            "publisher": [
                "meta[property='og:site_name']::attr(content)",
            ],
        }

    @classmethod
    def extract_metadata(cls, html: str) -> dict[str, str]:
        """
        Extract all Open Graph metadata from HTML.

        Args:
            html: Full page HTML

        Returns:
            Dict of {og_property: content} pairs

        Example:
            >>> metadata = OpenGraphProfile.extract_metadata(html)
            >>> print(metadata)
            {'title': 'Article Title', 'description': '...', 'image': 'https://...'}
        """
        soup = BeautifulSoup(html, "html.parser")
        metadata: dict[str, str] = {}

        # Find all OG meta tags
        for tag in soup.find_all(
            "meta", property=lambda x: isinstance(x, str) and x.startswith("og:")
        ):
            prop = attr_str(tag, "property")
            content = attr_str(tag, "content")
            if prop and content:
                # Remove 'og:' prefix for simpler keys
                key = prop.replace("og:", "")
                metadata[key] = content

        # Also check for article: namespace
        for tag in soup.find_all(
            "meta", property=lambda x: isinstance(x, str) and x.startswith("article:")
        ):
            prop = attr_str(tag, "property")
            content = attr_str(tag, "content")
            if prop and content:
                key = prop.replace("article:", "")
                metadata[key] = content

        return metadata
