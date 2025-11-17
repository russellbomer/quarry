"""Preview extraction results before saving schema."""

from typing import Any

from bs4 import BeautifulSoup, Tag

from quarry.lib.bs4_utils import attr_str, select_list
from quarry.lib.schemas import ExtractionSchema


def preview_extraction(html: str, schema: ExtractionSchema, limit: int = 5) -> list[dict[str, Any]]:
    """
    Preview extraction using a schema.

    Args:
        html: HTML content to extract from
        schema: ExtractionSchema to use
        limit: Maximum number of items to extract (default 5)

    Returns:
        List of extracted items (dicts)
    """
    if not html or not html.strip():
        return []

    soup = BeautifulSoup(html, "html.parser")
    items: list[dict[str, Any]] = []

    # Find all item containers
    try:
        item_elements = select_list(soup, schema.item_selector)
    except Exception as e:
        raise ValueError(f"Invalid item selector '{schema.item_selector}': {e}") from e

    if not item_elements:
        return []

    # Extract data from each item
    for item_elem in item_elements[:limit]:
        item_data: dict[str, Any] = {}

        for field_name, field_schema in schema.fields.items():
            try:
                # Find element(s) within this item
                if field_schema.multiple:
                    elements = select_list(item_elem, field_schema.selector)
                else:
                    elements = select_list(item_elem, field_schema.selector)[:1]

                if not elements:
                    # No match found
                    if field_schema.required:
                        item_data[field_name] = None  # Mark as missing
                    else:
                        item_data[field_name] = field_schema.default
                    continue

                # Extract value(s)
                if field_schema.multiple:
                    values: list[str] = []
                    for elem in elements:
                        value = _extract_value(elem, field_schema.attribute)
                        if value:
                            values.append(value)
                    item_data[field_name] = values
                else:
                    # Single value
                    value = _extract_value(elements[0], field_schema.attribute)
                    item_data[field_name] = value if value is not None else field_schema.default

            except Exception:
                # Field extraction failed
                if field_schema.required:
                    item_data[field_name] = None
                else:
                    item_data[field_name] = field_schema.default

        items.append(item_data)

    return items


def _extract_value(element: Tag, attribute: str | None) -> str | None:
    """Extract value from element (text or attribute)."""
    if attribute:
        # Extract attribute value
        value = attr_str(element, attribute)
        return value or None
    else:
        # Extract text content
        text = element.get_text(strip=True)
        return text if text else None


def format_preview(items: list[dict[str, Any]], limit: int = 5) -> str:
    """
    Format preview results for terminal display.

    Args:
        items: Extracted items
        limit: Max items to display

    Returns:
        Formatted string
    """
    try:
        from io import StringIO

        from rich import box
        from rich.console import Console
        from rich.table import Table

        output = StringIO()
        console = Console(file=output, width=120)

        if not items:
            console.print("[yellow]No items extracted[/yellow]")
            return output.getvalue()

        console.print(f"\n[bold cyan]Preview: {len(items)} item(s) extracted[/bold cyan]\n")

        # Show first few items in table
        display_items = items[:limit]

        if display_items:
            # Get all field names
            all_fields: set[str] = set()
            for item in display_items:
                all_fields.update(item.keys())
            fields = sorted(all_fields)

            # Create table
            table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
            table.add_column("#", style="dim", width=4)

            for field in fields:
                table.add_column(field, max_width=40)

            # Add rows
            for idx, item in enumerate(display_items, 1):
                values = [str(idx)]
                for field in fields:
                    value = item.get(field, "")
                    # Truncate long values
                    if isinstance(value, list):
                        value_str = f"[{len(value)} items]"
                    else:
                        value_str = str(value)[:40] if value is not None else "[dim]—[/dim]"
                    values.append(value_str)

                table.add_row(*values)

            console.print(table)

        if len(items) > limit:
            console.print(f"\n[dim]... and {len(items) - limit} more items[/dim]")

        return output.getvalue()

    except ImportError:
        # Fallback without rich
        return _format_preview_simple(items, limit)


def _format_preview_simple(items: list[dict[str, Any]], limit: int = 5) -> str:
    """Fallback preview formatter without rich."""
    if not items:
        return "No items extracted"

    lines = [f"\nPreview: {len(items)} item(s) extracted\n"]
    lines.append("=" * 60)

    for idx, item in enumerate(items[:limit], 1):
        lines.append(f"\nItem {idx}:")
        for key, value in item.items():
            if isinstance(value, list):
                value_str = f"[{len(value)} items]"
            else:
                value_str = str(value)[:60] if value else "—"
            lines.append(f"  {key}: {value_str}")

    if len(items) > limit:
        lines.append(f"\n... and {len(items) - limit} more items")

    lines.append("")
    return "\n".join(lines)
