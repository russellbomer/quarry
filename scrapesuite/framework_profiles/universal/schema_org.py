"""Schema.org microdata profile for structured data extraction."""

from bs4 import Tag

from scrapesuite.framework_profiles.base import FrameworkProfile


class SchemaOrgProfile(FrameworkProfile):
    """
    Detect and extract Schema.org microdata.
    
    Schema.org provides a universal vocabulary for structured data.
    This profile prioritizes microdata attributes (itemscope, itemprop)
    which are highly reliable for field extraction.
    """

    name = "schema_org"

    @classmethod
    def detect(cls, html: str, item_element: Tag | None = None) -> int:
        """
        Detect Schema.org microdata with confidence scoring.

        Returns:
            Confidence score 0-100. Threshold for detection is 40.
        """
        score = 0

        # Strong indicators (microdata attributes)
        if "itemscope" in html:
            score += 40  # Primary microdata marker
        if "itemprop=" in html:
            score += 35  # Property definitions
        if "itemtype=" in html:
            score += 30  # Type definitions

        # Common Schema.org types (add confidence if present)
        if "schema.org/Article" in html:
            score += 15
        if "schema.org/Product" in html:
            score += 15
        if "schema.org/Event" in html:
            score += 10
        if "schema.org/Recipe" in html:
            score += 10
        if "schema.org/Person" in html:
            score += 10

        # JSON-LD structured data (alternative format)
        if 'type="application/ld+json"' in html:
            score += 25

        return score

    @classmethod
    def get_item_selector_hints(cls) -> list[str]:
        """
        Get CSS selector patterns likely to match Schema.org items.

        Returns:
            List of selector patterns to try
        """
        return [
            "[itemscope]",
            "[itemscope][itemtype]",
            "[itemtype*='schema.org/Article']",
            "[itemtype*='schema.org/Product']",
            "[itemtype*='schema.org/Event']",
            "[itemtype*='schema.org/BlogPosting']",
            "[itemtype*='schema.org/NewsArticle']",
            "article[itemscope]",
            "div[itemscope]",
        ]

    @classmethod
    def get_field_mappings(cls) -> dict[str, list[str]]:
        """
        Get field type to Schema.org itemprop mappings.

        Returns:
            Dict mapping field types to list of selector patterns.
            Uses itemprop attributes which are highly reliable.
        """
        return {
            # Title/Name fields
            "title": [
                "[itemprop='headline']",
                "[itemprop='name']",
                "[itemprop='title']",
                "h1[itemprop='headline']",
                "h2[itemprop='name']",
            ],
            # Link/URL fields
            "link": [
                "[itemprop='url']::attr(href)",
                "a[itemprop='url']::attr(href)",
                "[itemprop='mainEntityOfPage']::attr(href)",
                "link[itemprop='url']::attr(href)",
            ],
            "url": [
                "[itemprop='url']::attr(href)",
                "a[itemprop='url']::attr(href)",
                "[itemprop='mainEntityOfPage']::attr(href)",
                "link[itemprop='url']::attr(href)",
            ],
            # Date fields
            "date": [
                "[itemprop='datePublished']",
                "time[itemprop='datePublished']",
                "[itemprop='dateCreated']",
                "[itemprop='startDate']",
                "time[itemprop='datePublished']::attr(datetime)",
                "[itemprop='dateModified']",
            ],
            # Description fields
            "description": [
                "[itemprop='description']",
                "[itemprop='articleBody']",
                "p[itemprop='description']",
                "div[itemprop='description']",
                "[itemprop='text']",
            ],
            # Author fields
            "author": [
                "[itemprop='author']",
                "[itemprop='author'] [itemprop='name']",
                "span[itemprop='author']",
                "a[itemprop='author']",
                "[itemprop='creator']",
            ],
            # Image fields
            "image": [
                "[itemprop='image']::attr(src)",
                "img[itemprop='image']::attr(src)",
                "[itemprop='thumbnailUrl']::attr(src)",
                "[itemprop='image']::attr(content)",
                "meta[itemprop='image']::attr(content)",
            ],
            # Price fields (for products)
            "price": [
                "[itemprop='price']",
                "[itemprop='price']::attr(content)",
                "meta[itemprop='price']::attr(content)",
                "span[itemprop='price']",
                "[itemprop='lowPrice']",
                "[itemprop='highPrice']",
            ],
            # Category/Genre fields
            "category": [
                "[itemprop='category']",
                "[itemprop='genre']",
                "a[itemprop='category']",
                "[itemprop='articleSection']",
            ],
            # Rating fields
            "rating": [
                "[itemprop='ratingValue']",
                "[itemprop='ratingValue']::attr(content)",
                "meta[itemprop='ratingValue']::attr(content)",
                "[itemprop='reviewRating'] [itemprop='ratingValue']",
            ],
            # Publisher fields
            "publisher": [
                "[itemprop='publisher']",
                "[itemprop='publisher'] [itemprop='name']",
                "span[itemprop='publisher']",
            ],
            # Location fields
            "location": [
                "[itemprop='location']",
                "[itemprop='location'] [itemprop='name']",
                "[itemprop='address']",
                "[itemprop='contentLocation']",
            ],
        }
