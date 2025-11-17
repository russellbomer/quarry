"""Twitter Cards meta tag profile for social media metadata extraction."""

from bs4 import BeautifulSoup, Tag

from quarry.framework_profiles.base import FrameworkProfile
from quarry.lib.bs4_utils import attr_str


class TwitterCardsProfile(FrameworkProfile):
    """
    Detect and extract Twitter Cards meta tags.

    Twitter Cards provide social media metadata similar to Open Graph.
    Meta tags like twitter:title, twitter:description are structured
    and reliable for extraction.
    """

    name = "twitter_cards"

    @classmethod
    def detect(cls, html: str, item_element: Tag | None = None) -> int:
        """
        Detect Twitter Cards meta tags with confidence scoring.

        Returns:
            Confidence score 0-100. Threshold for detection is 40.
        """
        score = 0

        # Count Twitter Card meta tags
        twitter_count = html.count('name="twitter:')
        if twitter_count >= 5:
            score += 50  # Many Twitter tags = high confidence
        elif twitter_count >= 3:
            score += 40  # Some Twitter tags = medium confidence
        elif twitter_count >= 1:
            score += 25  # Few Twitter tags = low confidence

        # Check for common Twitter Card tags
        if 'name="twitter:card"' in html:
            score += 20  # Card type is required
        if 'name="twitter:title"' in html:
            score += 15
        if 'name="twitter:description"' in html:
            score += 10
        if 'name="twitter:image"' in html:
            score += 10
        if 'name="twitter:site"' in html or 'name="twitter:creator"' in html:
            score += 10

        return score

    @classmethod
    def get_item_selector_hints(cls) -> list[str]:
        """
        Twitter Cards are in <head>, not item containers.

        Returns:
            Empty list (Twitter Cards don't define item containers)
        """
        # Twitter Cards are metadata, not container-based
        # Return semantic fallbacks
        return [
            "article",
            "main",
            "[role='main']",
        ]

    @classmethod
    def get_field_mappings(cls) -> dict[str, list[str]]:
        """
        Get field type to Twitter Card meta tag mappings.

        Returns:
            Dict mapping field types to Twitter Card meta tag selectors.
            Note: These are page-level metadata, not item-level.
        """
        return {
            # Title
            "title": [
                "meta[name='twitter:title']::attr(content)",
                "meta[property='twitter:title']::attr(content)",
            ],
            # URL
            "link": [
                "meta[name='twitter:url']::attr(content)",
                "meta[property='twitter:url']::attr(content)",
            ],
            "url": [
                "meta[name='twitter:url']::attr(content)",
                "meta[property='twitter:url']::attr(content)",
            ],
            # Description
            "description": [
                "meta[name='twitter:description']::attr(content)",
                "meta[property='twitter:description']::attr(content)",
            ],
            # Image
            "image": [
                "meta[name='twitter:image']::attr(content)",
                "meta[name='twitter:image:src']::attr(content)",
                "meta[property='twitter:image']::attr(content)",
            ],
            # Author (creator)
            "author": [
                "meta[name='twitter:creator']::attr(content)",
                "meta[property='twitter:creator']::attr(content)",
            ],
            # Publisher (site)
            "publisher": [
                "meta[name='twitter:site']::attr(content)",
                "meta[property='twitter:site']::attr(content)",
            ],
        }

    @classmethod
    def extract_metadata(cls, html: str) -> dict[str, str]:
        """
        Extract all Twitter Card metadata from HTML.

        Args:
            html: Full page HTML

        Returns:
            Dict of {twitter_property: content} pairs

        Example:
            >>> metadata = TwitterCardsProfile.extract_metadata(html)
            >>> print(metadata)
            {'title': 'Article Title', 'description': '...', 'image': 'https://...'}
        """
        soup = BeautifulSoup(html, "html.parser")
        metadata: dict[str, str] = {}

        # Find all Twitter Card meta tags (name attribute)
        for tag in soup.find_all(
            "meta", attrs={"name": lambda x: isinstance(x, str) and x.startswith("twitter:")}
        ):
            name = attr_str(tag, "name")
            content = attr_str(tag, "content")
            if name and content:
                # Remove 'twitter:' prefix for simpler keys
                key = name.replace("twitter:", "")
                metadata[key] = content

        # Also check property attribute (less common but valid)
        for tag in soup.find_all(
            "meta", property=lambda x: isinstance(x, str) and x.startswith("twitter:")
        ):
            prop = attr_str(tag, "property")
            content = attr_str(tag, "content")
            if prop and content:
                key = prop.replace("twitter:", "")
                # Don't overwrite if already set from name attribute
                if key not in metadata:
                    metadata[key] = content

        return metadata
