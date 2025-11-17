"""Base class for framework-specific detection profiles."""

from bs4 import Tag


def _get_element_classes(element: Tag) -> str:
    """
    Get element's classes as a space-separated string.

    Args:
        element: BeautifulSoup Tag element

    Returns:
        Space-separated class names, or empty string if no classes
    """
    classes = element.get("class")
    if classes is None:
        return ""
    if isinstance(classes, list):
        return " ".join(classes)
    return str(classes)


class FrameworkProfile:
    """Base class for framework-specific detection profiles."""

    name: str = "generic"

    @classmethod
    def detect(cls, html: str, item_element: Tag | None = None) -> int:
        """
        Detect if this framework is being used with confidence scoring.

        Args:
            html: Full page HTML
            item_element: Optional item container element

        Returns:
            Confidence score (0-100). 0 = not detected, 100 = very confident.
            Threshold for detection is typically 50.
        """
        raise NotImplementedError

    @classmethod
    def get_item_selector_hints(cls) -> list[str]:
        """
        Get CSS selector patterns likely to match item containers.

        Returns:
            List of selector patterns to try
        """
        return []

    @classmethod
    def get_field_mappings(cls) -> dict[str, list[str]]:
        """
        Get field type to CSS selector/class pattern mappings.

        Returns:
            Dict mapping field types to list of selector patterns
        """
        return {}

    @classmethod
    def generate_field_selector(cls, item_element: Tag, field_type: str) -> str | None:
        """
        Generate field selector using framework-specific knowledge.

        Args:
            item_element: Item container element
            field_type: Field type to detect

        Returns:
            CSS selector string or None
        """
        mappings = cls.get_field_mappings()
        patterns = mappings.get(field_type, [])

        for pattern in patterns:
            # Handle ::attr() syntax for attribute extraction
            has_attr = "::attr(" in pattern
            if has_attr:
                # Split pattern and attr
                base_pattern = pattern.split("::attr(")[0].strip()
                # attr_name = pattern.split("::attr(")[1].rstrip(")")
            else:
                base_pattern = pattern

            # Try to find element matching pattern
            if base_pattern.startswith("."):
                # Class selector
                class_name = base_pattern[1:].split()[0]  # Get first class if pattern has spaces

                # Handle patterns like ".class a" (selector with descendant)
                if " " in base_pattern:
                    # Split into parent and child
                    parts = base_pattern.split()
                    parent_selector = parts[0][1:]  # Remove leading dot from first part
                    child_selector = " ".join(parts[1:])

                    # Find parent element
                    parent = item_element.find(class_=parent_selector)
                    if parent:
                        # Check if child exists
                        if child_selector == "a":
                            if parent.find("a", href=True):
                                return pattern  # Return original with ::attr if present
                        elif child_selector.startswith("img"):
                            if parent.find("img"):
                                return pattern
                        elif child_selector.startswith("time"):
                            if parent.find("time"):
                                return pattern
                        # Try generic tag search
                        elif parent.find(child_selector.split()[0]):
                            return pattern
                else:
                    # Simple class selector
                    elem = item_element.find(class_=class_name)
                    if elem:
                        return pattern
            elif base_pattern.count(".") > 0 and not base_pattern.startswith("["):
                # Handle tag.class patterns like "th.field-__str__"
                if " " in base_pattern:
                    # Complex selector with descendants
                    parts = base_pattern.split()
                    first_part = parts[0]

                    # Parse tag.class
                    if "." in first_part:
                        tag_name, class_name = first_part.split(".", 1)
                        parent = item_element.find(tag_name, class_=class_name)
                    else:
                        parent = item_element.find(class_=first_part)

                    if parent:
                        # Check for descendant
                        child_selector = " ".join(parts[1:])
                        if child_selector == "a":
                            if parent.find("a", href=True):
                                return pattern
                        elif parent.find(child_selector.split()[0]):
                            return pattern
                else:
                    # Simple tag.class pattern
                    tag_name, class_name = base_pattern.split(".", 1)
                    elem = item_element.find(tag_name, class_=class_name)
                    if elem:
                        return pattern
            elif base_pattern.startswith("["):
                # Attribute selector - parse it
                # Simple implementation for common cases
                if "*=" in base_pattern:
                    # Partial match selector like [class*='title']
                    attr_name = base_pattern.split("*=")[0].replace("[", "").strip()
                    search_value = (
                        base_pattern.split("*=")[1]
                        .replace("]", "")
                        .replace("'", "")
                        .replace('"', "")
                        .strip()
                    )

                    # Find element with attribute containing value
                    for elem in item_element.find_all():
                        attr_val = elem.get(attr_name, "")
                        if isinstance(attr_val, list):
                            attr_val = " ".join(attr_val)
                        if search_value.lower() in str(attr_val).lower():
                            return pattern
                elif "=" in base_pattern:
                    attr_name = base_pattern.split("=")[0].replace("[", "").strip()
                    elem = item_element.find(attrs={attr_name: True})
                    if elem:
                        return pattern
            else:
                # Tag selector or more complex selector
                # Try to find element by tag name
                elem = item_element.find(
                    base_pattern.split()[0]
                )  # Get first part for tag selectors
                if elem:
                    return pattern

        return None
