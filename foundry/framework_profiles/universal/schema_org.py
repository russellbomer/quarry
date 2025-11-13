"""Schema.org microdata and JSON-LD profile for structured data extraction."""

import json
from typing import Any

from bs4 import BeautifulSoup, Tag

from foundry.framework_profiles.base import FrameworkProfile


class SchemaOrgProfile(FrameworkProfile):
    """
    Detect and extract Schema.org structured data.
    
    Schema.org provides a universal vocabulary for structured data.
    This profile supports both:
    1. Microdata attributes (itemscope, itemprop) - legacy format
    2. JSON-LD scripts - modern format preferred by Google
    
    JSON-LD is now the preferred format and scores higher.
    """

    name = "schema_org"

    @classmethod
    def _extract_json_ld(cls, html: str) -> list[dict[str, Any]]:
        """
        Extract and parse JSON-LD script blocks.
        
        Returns:
            List of parsed JSON-LD objects (may be empty)
        """
        soup = BeautifulSoup(html, "html.parser")
        json_ld_scripts = soup.find_all("script", type="application/ld+json")
        
        parsed_objects = []
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                # Handle both single objects and arrays
                if isinstance(data, list):
                    parsed_objects.extend(data)
                else:
                    parsed_objects.append(data)
            except (json.JSONDecodeError, AttributeError, TypeError):
                # Skip malformed JSON-LD
                continue
        
        return parsed_objects

    @classmethod
    def detect(cls, html: str, item_element: Tag | None = None) -> int:
        """
        Detect Schema.org structured data with confidence scoring.

        Returns:
            Confidence score 0-100. Threshold for detection is 40.
        """
        score = 0

        # JSON-LD structured data (modern, preferred format)
        json_ld_blocks = cls._extract_json_ld(html)
        if json_ld_blocks:
            score += 50  # Primary indicator for modern Schema.org
            # Bonus for multiple blocks (richer structured data)
            if len(json_ld_blocks) > 1:
                score += min(20, len(json_ld_blocks) * 5)

        # Microdata attributes (legacy format, still supported)
        if "itemscope" in html:
            score += 30  # Secondary indicator
        if "itemprop=" in html:
            score += 25  # Property definitions
        if "itemtype=" in html:
            score += 20  # Type definitions

        # Common Schema.org types (add confidence if present)
        schema_types = [
            ("Article", 15),
            ("Product", 15),
            ("NewsArticle", 12),
            ("BlogPosting", 12),
            ("Recipe", 10),
            ("Event", 10),
            ("Person", 10),
            ("Organization", 10),
        ]
        
        for schema_type, type_score in schema_types:
            if f"schema.org/{schema_type}" in html or f'"@type":"{schema_type}"' in html:
                score += type_score
                break  # Only add bonus once

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
        Get field type to Schema.org mappings.

        Returns:
            Dict mapping field types to list of selector patterns.
            
        Note: This returns microdata selectors. For JSON-LD extraction,
        use extract_json_ld_fields() method instead (see below).
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

    @classmethod
    def extract_json_ld_fields(cls, html: str) -> dict[str, Any]:
        """
        Extract common fields from JSON-LD structured data.
        
        Modern Schema.org implementations use JSON-LD instead of microdata.
        This method extracts fields from JSON-LD scripts.
        
        Args:
            html: HTML content containing JSON-LD scripts
            
        Returns:
            Dict with extracted fields. Keys are standardized field names,
            values are extracted from JSON-LD @type objects.
            
        Example:
            >>> html = '<script type="application/ld+json">{"@type":"Article","headline":"Test"}</script>'
            >>> fields = SchemaOrgProfile.extract_json_ld_fields(html)
            >>> fields['title']
            'Test'
        """
        json_ld_blocks = cls._extract_json_ld(html)
        if not json_ld_blocks:
            return {}
        
        # Field mapping: our standard names -> JSON-LD property names
        field_mappings = {
            "title": ["headline", "name", "title"],
            "description": ["description", "articleBody", "text"],
            "author": ["author", "creator"],
            "date": ["datePublished", "dateCreated", "startDate", "dateModified"],
            "url": ["url", "mainEntityOfPage"],
            "image": ["image", "thumbnailUrl"],
            "price": ["price", "lowPrice", "highPrice"],
            "category": ["category", "genre", "articleSection"],
            "rating": ["ratingValue"],
            "publisher": ["publisher"],
        }
        
        extracted = {}
        
        # Try to extract each field from JSON-LD blocks
        for our_field, json_properties in field_mappings.items():
            for block in json_ld_blocks:
                for json_prop in json_properties:
                    if json_prop in block:
                        value = block[json_prop]
                        
                        # Handle nested objects (e.g., author: {name: "John"})
                        if isinstance(value, dict):
                            if "name" in value:
                                extracted[our_field] = value["name"]
                            elif "@id" in value:
                                extracted[our_field] = value["@id"]
                        # Handle arrays (take first element)
                        elif isinstance(value, list) and value:
                            extracted[our_field] = value[0] if isinstance(value[0], str) else str(value[0])
                        # Direct string/number value
                        else:
                            extracted[our_field] = str(value)
                        
                        break  # Found this field, move to next
                
                if our_field in extracted:
                    break  # Found in a block, don't check others
        
        return extracted
