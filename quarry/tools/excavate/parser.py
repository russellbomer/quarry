"""Schema-driven HTML parser for Forge tool."""

from typing import Any

from bs4 import BeautifulSoup, Tag

from quarry.lib.bs4_utils import attr_str, select_list
from quarry.lib.schemas import ExtractionSchema, FieldSchema


class SchemaParser:
    """
    Parse HTML using an ExtractionSchema.

    Extracts structured data from HTML by:
    1. Finding item containers using item_selector
    2. Extracting fields from each item using field selectors
    3. Handling attributes, defaults, and required fields
    """

    def __init__(self, schema: ExtractionSchema):
        """
        Initialize parser with schema.

        Args:
            schema: ExtractionSchema defining what to extract
        """
        self.schema = schema

    def parse(self, html: str) -> list[dict[str, Any]]:
        """
        Extract items from HTML using schema.

        Args:
            html: HTML content to parse

        Returns:
            List of extracted items (dicts)
        """
        if not html or not html.strip():
            return []

        soup = BeautifulSoup(html, "html.parser")

        # Find all item containers
        try:
            item_elements = select_list(soup, self.schema.item_selector)
        except Exception as e:
            raise ValueError(f"Invalid item selector '{self.schema.item_selector}': {e}") from e

        if not item_elements:
            return []

        # Extract data from each item
        results = []
        for item_elem in item_elements:
            try:
                record = self._extract_item(item_elem)
                results.append(record)
            except Exception:
                # Skip items that fail extraction
                continue

        return results

    def _extract_item(self, item_element: Tag) -> dict[str, Any]:
        """
        Extract all fields from a single item element.

        Args:
            item_element: BeautifulSoup Tag for one item

        Returns:
            Dictionary of extracted field values

        Raises:
            ValueError: If a required field is missing
        """
        record = {}

        for field_name, field_schema in self.schema.fields.items():
            value = self._extract_field(item_element, field_schema)

            # Check if required field is missing
            if field_schema.required and value is None:
                raise ValueError(f"Required field '{field_name}' is missing")

            record[field_name] = value

        return record

    def _extract_field(self, item_element: Tag, field_schema: FieldSchema) -> Any:
        """
        Extract a single field from an item element.

        Args:
            item_element: BeautifulSoup Tag for the item
            field_schema: FieldSchema defining how to extract

        Returns:
            Extracted value, default value, or None
        """
        try:
            # Find element(s) within this item
            if field_schema.multiple:
                elements = select_list(item_element, field_schema.selector)
            else:
                elements = select_list(item_element, field_schema.selector)[:1]

            if not elements:
                # No match found
                return field_schema.default if not field_schema.required else None

            # Extract value(s)
            if field_schema.multiple:
                values = []
                for elem in elements:
                    value = self._extract_value(elem, field_schema.attribute)
                    if value is not None:
                        values.append(value)
                return values if values else field_schema.default
            else:
                # Single value
                value = self._extract_value(elements[0], field_schema.attribute)
                return value if value is not None else field_schema.default

        except Exception:
            # Field extraction failed
            return field_schema.default if not field_schema.required else None

    def _extract_value(self, element: Tag, attribute: str | None) -> str | None:
        """
        Extract text or attribute value from element.

        Args:
            element: BeautifulSoup Tag
            attribute: Optional attribute name to extract (e.g., 'href', 'src')

        Returns:
            Extracted string value or None
        """
        if attribute:
            # Extract attribute value as strict string
            value = attr_str(element, attribute)
            return value or None
        else:
            # Extract text content
            text = element.get_text(strip=True)
            return text if text else None
