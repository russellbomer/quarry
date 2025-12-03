"""Quarry Foreman - Interactive guided tutorial with real data extraction.

Provides a comprehensive, hands-on walkthrough of the Quarry pipeline where
users perform actual extraction operations on a real website.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import click
import questionary
from questionary import Style as QStyle
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

from quarry.lib.theme import COLORS, QUARRY_THEME, QUESTIONARY_STYLE

console = Console(theme=QUARRY_THEME)
q_style = QStyle.from_dict(QUESTIONARY_STYLE)

# Constants
MAX_DISPLAY_LEN = 50
FOREMAN_DIR = Path("foreman_tutorial")
PREVIEW_ROWS = 5
KB_SIZE = 1024


# =============================================================================
# Helper Functions
# =============================================================================


def _print_step(step: int, total: int, title: str) -> None:
    """Print a step header."""
    console.print()
    console.print(
        f"[bold {COLORS['primary']}]━━━ Step {step}/{total}: {title} ━━━[/bold {COLORS['primary']}]"
    )
    console.print()


def _print_explanation(text: str) -> None:
    """Print explanatory text."""
    console.print(Panel(text, border_style=COLORS["dim"], padding=(1, 2)))


def _print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"\n[{COLORS['success']}]✓ {message}[/{COLORS['success']}]")


def _print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"\n[{COLORS['error']}]✗ {message}[/{COLORS['error']}]")


def _print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[{COLORS['tertiary']}]> {message}[/{COLORS['tertiary']}]")


def _print_tip(message: str) -> None:
    """Print a tip/hint."""
    console.print(f"[{COLORS['warning']}]💡 Tip: {message}[/{COLORS['warning']}]")


def _print_command(cmd: str) -> None:
    """Print the equivalent CLI command."""
    console.print(f"\n[{COLORS['dim']}]CLI equivalent:[/{COLORS['dim']}]")
    console.print(f"  [{COLORS['secondary']}]$ {cmd}[/{COLORS['secondary']}]")


def _show_progress(message: str) -> Progress:
    """Create a progress spinner context."""
    return Progress(
        SpinnerColumn(style=COLORS["secondary"]),
        TextColumn(f"[{COLORS['dim']}]{message}[/{COLORS['dim']}]"),
        console=console,
        transient=True,
    )


def _wait_for_continue() -> bool:
    """Prompt user to continue or exit."""
    console.print()
    result = questionary.confirm(
        "Continue to next step?",
        default=True,
        style=q_style,
    ).ask()
    return bool(result)


def _show_yaml(content: str, title: str = "Schema") -> None:
    """Display YAML content with syntax highlighting."""
    syntax = Syntax(content, "yaml", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title=title, border_style=COLORS["tertiary"]))


def _truncate(text: str, max_len: int = MAX_DISPLAY_LEN) -> str:
    """Truncate text for display."""
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def _ensure_dir(path: Path) -> None:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Tutorial State
# =============================================================================


class TutorialState:
    """Holds user inputs and results throughout the tutorial."""

    def __init__(self) -> None:
        self.url: str = ""
        self.job_name: str = ""
        self.item_selector: str = ""
        self.fields: dict[str, dict[str, Any]] = {}
        self.output_format: str = ""
        self.polish_options: list[str] = []

        # Real data
        self.html: str = ""
        self.extracted_data: list[dict[str, Any]] = []
        self.polished_data: list[dict[str, Any]] = []

        # File paths
        self.schema_file: Path = FOREMAN_DIR / "schema.yml"
        self.raw_file: Path = FOREMAN_DIR / "extracted.jsonl"
        self.polished_file: Path = FOREMAN_DIR / "polished.jsonl"
        self.export_file: Path = FOREMAN_DIR / "output.csv"


# =============================================================================
# Step Implementations
# =============================================================================


def _show_welcome() -> bool:
    """Display welcome screen."""
    console.clear()
    console.print()
    console.print(
        Panel(
            f"[bold {COLORS['primary']}]Welcome to Quarry Foreman"
            f"[/bold {COLORS['primary']}]\n\n"
            f"[{COLORS['secondary']}]An interactive tutorial with real data extraction"
            f"[/{COLORS['secondary']}]\n\n"
            "This tutorial will guide you through the complete Quarry workflow,\n"
            "performing [bold]actual extraction[/bold] on a real website.\n\n"
            f"[{COLORS['tertiary']}]What you'll do:[/{COLORS['tertiary']}]\n\n"
            f"  [{COLORS['primary']}]1. Scout[/{COLORS['primary']}]    "
            "Fetch and analyze a live webpage\n"
            f"  [{COLORS['primary']}]2. Survey[/{COLORS['primary']}]   "
            "Define CSS selectors to target data\n"
            f"  [{COLORS['primary']}]3. Excavate[/{COLORS['primary']}] "
            "Extract real data from the page\n"
            f"  [{COLORS['primary']}]4. Polish[/{COLORS['primary']}]   "
            "Clean and validate the data\n"
            f"  [{COLORS['primary']}]5. Ship[/{COLORS['primary']}]     "
            "Export to a real file\n\n"
            f"[{COLORS['dim']}]All output files will be saved to: ./{FOREMAN_DIR}/"
            f"[/{COLORS['dim']}]\n"
            f"[{COLORS['dim']}]Estimated time: 5-10 minutes[/{COLORS['dim']}]",
            border_style=COLORS["primary"],
            title="🏗️ Foreman Tutorial",
            title_align="left",
        )
    )
    console.print()

    result = questionary.confirm(
        "Ready to begin the tutorial?",
        default=True,
        style=q_style,
    ).ask()
    return bool(result)


def _step_scout(state: TutorialState) -> bool:
    """Step 1: Scout - Fetch and analyze page structure."""
    _print_step(1, 5, "Scout")

    _print_explanation(
        f"[bold]What is Scout?[/bold]\n\n"
        "Scout fetches a webpage and analyzes its structure to help you\n"
        "understand what data is available and how to extract it.\n\n"
        f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] "
        "Detects repeated patterns (lists, tables, cards)\n"
        f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] "
        "Identifies frameworks (React, WordPress, etc.)\n"
        f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] "
        "Suggests CSS selectors for common elements\n\n"
        f"[{COLORS['dim']}]We'll use Hacker News as our example - it has a clean,\n"
        f"predictable structure that's perfect for learning.[/{COLORS['dim']}]"
    )

    console.print()

    # Get URL
    url = questionary.text(
        "Enter the URL to analyze:",
        default="https://news.ycombinator.com",
        style=q_style,
    ).ask()

    if not url:
        return False

    state.url = url
    _print_command(f"quarry scout {url}")

    console.print()

    # Actually fetch the page
    try:
        from quarry.lib.http import get_html  # noqa: PLC0415

        with _show_progress(f"Fetching {url}...") as progress:
            progress.add_task("", total=None)
            # Set environment to allow fetch even if robots.txt blocks
            os.environ["QUARRY_IGNORE_ROBOTS"] = "1"
            state.html = get_html(url, respect_robots=False)

        _print_success(f"Fetched {len(state.html):,} bytes of HTML")

    except Exception as e:
        _print_error(f"Failed to fetch URL: {e}")
        console.print(
            f"\n[{COLORS['dim']}]Make sure you have internet connectivity.[/{COLORS['dim']}]"
        )
        return False

    # Analyze the page
    try:
        from quarry.tools.scout.analyzer import analyze_page  # noqa: PLC0415

        with _show_progress("Analyzing page structure...") as progress:
            progress.add_task("", total=None)
            analysis = analyze_page(state.html, url)

        # Show results
        _display_scout_results(analysis)

    except Exception as e:
        _print_info(f"Analysis encountered an issue: {e}")
        _print_info("Continuing with manual configuration...")

    _print_success("Scout analysis complete!")

    console.print()
    _print_tip(
        "On Hacker News, each story is in a <tr> element with class 'athing'.\n"
        "         We'll use this selector in the next step."
    )

    return _wait_for_continue()


def _display_scout_results(analysis: dict[str, Any]) -> None:
    """Display scout analysis results in a table."""
    table = Table(
        title="Scout Analysis Results",
        border_style=COLORS["tertiary"],
        title_style=f"bold {COLORS['primary']}",
    )
    table.add_column("Finding", style=COLORS["secondary"])
    table.add_column("Details", style="white")

    # Frameworks
    frameworks = analysis.get("frameworks", [])
    if frameworks:
        fw_names = [f.get("name", "Unknown") for f in frameworks[:3]]
        table.add_row("Frameworks", ", ".join(fw_names))
    else:
        table.add_row("Frameworks", "None detected (static HTML)")

    # Containers/repeated elements
    containers = analysis.get("containers", [])
    if containers:
        top_container = containers[0] if containers else {}
        selector = top_container.get("selector", "Unknown")
        count = top_container.get("count", 0)
        table.add_row("Repeated Items", f"{count} items ({selector})")
    else:
        table.add_row("Repeated Items", "Analyzing...")

    # Page stats
    stats = analysis.get("statistics", {})
    table.add_row("Links", str(stats.get("links", 0)))
    table.add_row("Forms", str(stats.get("forms", 0)))
    table.add_row("Tables", str(stats.get("tables", 0)))

    console.print(table)


def _step_survey(state: TutorialState) -> bool:
    """Step 2: Survey - Define extraction schema."""
    _print_step(2, 5, "Survey")

    _print_explanation(
        f"[bold]What is Survey?[/bold]\n\n"
        "Survey helps you build an extraction schema that tells Quarry\n"
        "exactly what data to extract and how to find it.\n\n"
        f"[bold {COLORS['secondary']}]Key concepts:[/bold {COLORS['secondary']}]\n\n"
        f"  [{COLORS['tertiary']}]Item Selector[/{COLORS['tertiary']}] - "
        "Identifies each repeated item on the page\n"
        f"  [{COLORS['tertiary']}]Field Selectors[/{COLORS['tertiary']}] - "
        "Target specific data within each item\n"
        f"  [{COLORS['tertiary']}]Attributes[/{COLORS['tertiary']}] - "
        "Extract href, src, etc. instead of text content"
    )

    console.print()

    # Job name
    job_name = questionary.text(
        "Name for this extraction job:",
        default="hackernews_stories",
        style=q_style,
    ).ask()

    if not job_name:
        return False

    state.job_name = job_name

    console.print()
    console.print(
        f"[{COLORS['tertiary']}]The item selector identifies each story row.\n"
        f"On Hacker News, stories are in <tr class=\"athing\"> elements."
        f"[/{COLORS['tertiary']}]"
    )
    console.print()

    # Item selector
    item_selector = questionary.text(
        "Item selector (CSS):",
        default="tr.athing",
        style=q_style,
    ).ask()

    if not item_selector:
        return False

    state.item_selector = item_selector

    # Define fields
    console.print()
    _print_info("Now define the fields to extract from each story.")
    _print_tip("CSS selectors are relative to each item container.")
    console.print()

    fields = _collect_fields()
    state.fields = fields

    # Generate and save schema
    schema_yaml = _generate_schema_yaml(state)
    _show_yaml(schema_yaml, title="Generated Schema")

    # Save to file
    _ensure_dir(FOREMAN_DIR)
    state.schema_file.write_text(schema_yaml, encoding="utf-8")

    _print_command(f"quarry survey {state.schema_file} --preview")
    _print_success(f"Schema saved to {state.schema_file}")

    return _wait_for_continue()


def _collect_fields() -> dict[str, dict[str, Any]]:
    """Collect field definitions from user."""
    fields: dict[str, dict[str, Any]] = {}

    # Field 1: Title
    console.print(f"[bold {COLORS['secondary']}]Field 1: title[/bold {COLORS['secondary']}]")
    title_sel = questionary.text(
        "  CSS selector:",
        default="td.title > span.titleline > a",
        style=q_style,
    ).ask()
    if title_sel:
        fields["title"] = {"selector": title_sel}

    # Field 2: Link
    console.print()
    console.print(f"[bold {COLORS['secondary']}]Field 2: link[/bold {COLORS['secondary']}]")
    console.print(
        f"  [{COLORS['dim']}]To get the URL, extract the 'href' attribute[/{COLORS['dim']}]"
    )
    link_sel = questionary.text(
        "  CSS selector:",
        default="td.title > span.titleline > a",
        style=q_style,
    ).ask()
    if link_sel:
        link_attr = questionary.text(
            "  Attribute to extract:",
            default="href",
            style=q_style,
        ).ask()
        fields["link"] = {"selector": link_sel}
        if link_attr:
            fields["link"]["attribute"] = link_attr

    # Field 3: Rank
    console.print()
    console.print(f"[bold {COLORS['secondary']}]Field 3: rank[/bold {COLORS['secondary']}]")
    rank_sel = questionary.text(
        "  CSS selector:",
        default="td.title > span.rank",
        style=q_style,
    ).ask()
    if rank_sel:
        fields["rank"] = {"selector": rank_sel}

    # Add more fields?
    console.print()
    add_more = questionary.confirm(
        "Add more fields?",
        default=False,
        style=q_style,
    ).ask()

    while add_more:
        _collect_custom_field(fields)
        add_more = questionary.confirm(
            "Add another field?",
            default=False,
            style=q_style,
        ).ask()

    return fields


def _collect_custom_field(fields: dict[str, dict[str, Any]]) -> None:
    """Collect a custom field from user input."""
    console.print()
    field_name = questionary.text(
        "Field name (or Enter to finish):",
        style=q_style,
    ).ask()

    if not field_name:
        return

    field_sel = questionary.text(
        f"  CSS selector for {field_name}:",
        style=q_style,
    ).ask()

    if field_sel:
        field_attr = questionary.text(
            "  Attribute (leave empty for text):",
            style=q_style,
        ).ask()
        fields[field_name] = {"selector": field_sel}
        if field_attr:
            fields[field_name]["attribute"] = field_attr


def _generate_schema_yaml(state: TutorialState) -> str:
    """Generate YAML schema from state."""
    lines = [
        f"name: {state.job_name}",
        f"url: {state.url}",
        f'item_selector: "{state.item_selector}"',
        "fields:",
    ]

    for name, config in state.fields.items():
        lines.append(f"  {name}:")
        lines.append(f'    selector: "{config["selector"]}"')
        if config.get("attribute"):
            lines.append(f'    attribute: "{config["attribute"]}"')

    return "\n".join(lines)


def _step_excavate(state: TutorialState) -> bool:
    """Step 3: Excavate - Extract real data."""
    _print_step(3, 5, "Excavate")

    _print_explanation(
        f"[bold]What is Excavate?[/bold]\n\n"
        "Excavate applies your schema to the fetched page and extracts\n"
        "structured data. It outputs JSONL (one JSON object per line).\n\n"
        f"[bold {COLORS['secondary']}]Capabilities:[/bold {COLORS['secondary']}]\n\n"
        f"  [{COLORS['tertiary']}]•[/{COLORS['tertiary']}] "
        "Single page or multi-page extraction\n"
        f"  [{COLORS['tertiary']}]•[/{COLORS['tertiary']}] "
        "Rate limiting to be polite to servers\n"
        f"  [{COLORS['tertiary']}]•[/{COLORS['tertiary']}] "
        "Metadata injection (source URL, timestamp)\n\n"
        f"[{COLORS['dim']}]We'll extract data from the page we already fetched."
        f"[/{COLORS['dim']}]"
    )

    console.print()
    _print_command(f"quarry excavate {state.schema_file} --output {state.raw_file}")
    console.print()

    # Perform extraction using the existing HTML
    try:
        from quarry.lib.schemas import load_schema  # noqa: PLC0415
        from quarry.tools.excavate.parser import SchemaParser  # noqa: PLC0415

        with _show_progress("Extracting data...") as progress:
            progress.add_task("", total=None)

            schema = load_schema(state.schema_file)
            parser = SchemaParser(schema)
            items = parser.parse(state.html)

            # Add metadata
            now = datetime.now().isoformat()
            for item in items:
                item["_meta"] = {
                    "url": state.url,
                    "extracted_at": now,
                    "schema": state.job_name,
                }

            state.extracted_data = items

        # Save to JSONL
        _ensure_dir(FOREMAN_DIR)
        with state.raw_file.open("w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        # Show results
        _display_extracted_data(state, items)

    except Exception as e:
        _print_error(f"Extraction failed: {e}")
        return False

    return _wait_for_continue()


def _display_extracted_data(state: TutorialState, items: list[dict[str, Any]]) -> None:
    """Display extracted data in a table."""
    console.print()
    if items:
        table = Table(
            title=f"Extracted Data ({len(items)} records)",
            border_style=COLORS["success"],
            title_style=f"bold {COLORS['success']}",
        )

        # Add columns for each field
        for field in state.fields.keys():
            table.add_column(field.title(), style=COLORS["secondary"], max_width=45)

        # Show first PREVIEW_ROWS items
        for item in items[:PREVIEW_ROWS]:
            row = []
            for field in state.fields.keys():
                val = str(item.get(field, "—"))
                row.append(_truncate(val, 42))
            table.add_row(*row)

        console.print(table)

        if len(items) > PREVIEW_ROWS:
            remaining = len(items) - PREVIEW_ROWS
            console.print(f"[{COLORS['dim']}]... and {remaining} more records[/{COLORS['dim']}]")

        _print_success(f"Extracted {len(items)} records to {state.raw_file}")
    else:
        _print_error("No data extracted. Check your selectors.")
        _print_tip(
            "The item selector might not match any elements,\n"
            "         or the field selectors might be incorrect."
        )


def _step_polish(state: TutorialState) -> bool:
    """Step 4: Polish - Clean and transform data."""
    _print_step(4, 5, "Polish")

    _print_explanation(
        f"[bold]What is Polish?[/bold]\n\n"
        "Polish cleans and transforms your extracted data:\n\n"
        f"[bold {COLORS['secondary']}]Cleaning:[/bold {COLORS['secondary']}]\n"
        f"  [{COLORS['tertiary']}]--dedupe[/{COLORS['tertiary']}]        "
        "Remove duplicate records\n"
        f"  [{COLORS['tertiary']}]--strip[/{COLORS['tertiary']}]         "
        "Trim whitespace from text\n\n"
        f"[bold {COLORS['secondary']}]Validation:[/bold {COLORS['secondary']}]\n"
        f"  [{COLORS['tertiary']}]--validate-urls[/{COLORS['tertiary']}] "
        "Check URL fields are valid\n"
        f"  [{COLORS['tertiary']}]--drop-empty[/{COLORS['tertiary']}]    "
        "Remove records with missing data"
    )

    console.print()

    # Select operations
    polish_ops = questionary.checkbox(
        "Select polish operations:",
        choices=[
            questionary.Choice("Remove duplicates", checked=True),
            questionary.Choice("Strip whitespace", checked=True),
            questionary.Choice("Drop records with empty required fields", checked=False),
        ],
        style=q_style,
    ).ask()

    if polish_ops is None:
        return False

    state.polish_options = polish_ops

    # Build command
    cmd_parts = [f"quarry polish {state.raw_file}"]
    if "Remove duplicates" in polish_ops:
        cmd_parts.append("--dedupe")
    if "Strip whitespace" in polish_ops:
        cmd_parts.append("--strip")
    cmd_parts.append(f"--output {state.polished_file}")

    _print_command(" ".join(cmd_parts))
    console.print()

    # Apply polish operations
    stats = _apply_polish_operations(state, polish_ops)
    if stats is None:
        return False

    # Show results
    console.print()
    console.print(f"[{COLORS['tertiary']}]Polish Results:[/{COLORS['tertiary']}]")
    console.print(
        f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] "
        f"Input records: {len(state.extracted_data)}"
    )
    if "Remove duplicates" in polish_ops:
        console.print(
            f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] "
            f"Duplicates removed: {stats['duplicates']}"
        )
    if "Strip whitespace" in polish_ops:
        console.print(
            f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] "
            f"Fields stripped: {stats['stripped']}"
        )
    console.print(
        f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] "
        f"Output records: {len(state.polished_data)}"
    )

    _print_success(f"Polished data saved to {state.polished_file}")

    return _wait_for_continue()


def _apply_polish_operations(state: TutorialState, polish_ops: list[str]) -> dict[str, int] | None:
    """Apply polish operations and return stats."""
    try:
        with _show_progress("Applying polish operations...") as progress:
            progress.add_task("", total=None)

            polished = []
            seen_hashes: set[str] = set()
            duplicates = 0
            stripped = 0

            for record in state.extracted_data:
                # Skip _meta for deduplication
                record_copy = {k: v for k, v in record.items() if not k.startswith("_")}

                # Strip whitespace
                if "Strip whitespace" in polish_ops:
                    for key, val in record_copy.items():
                        if isinstance(val, str):
                            new_val = val.strip()
                            if new_val != val:
                                stripped += 1
                            record_copy[key] = new_val

                # Deduplicate
                if "Remove duplicates" in polish_ops:
                    record_hash = json.dumps(record_copy, sort_keys=True)
                    if record_hash in seen_hashes:
                        duplicates += 1
                        continue
                    seen_hashes.add(record_hash)

                # Reconstruct with meta
                final_record = {**record_copy}
                if "_meta" in record:
                    final_record["_meta"] = record["_meta"]

                polished.append(final_record)

            state.polished_data = polished

        # Save polished data
        with state.polished_file.open("w", encoding="utf-8") as f:
            for item in polished:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        return {"duplicates": duplicates, "stripped": stripped}

    except Exception as e:
        _print_error(f"Polish failed: {e}")
        # Fall back to using extracted data directly
        state.polished_data = state.extracted_data
        state.polished_file = state.raw_file
        return None


def _step_ship(state: TutorialState) -> bool:
    """Step 5: Ship - Export to final format."""
    _print_step(5, 5, "Ship")

    _print_explanation(
        f"[bold]What is Ship?[/bold]\n\n"
        "Ship exports your cleaned data to various formats:\n\n"
        f"[bold {COLORS['secondary']}]File Formats:[/bold {COLORS['secondary']}]\n"
        f"  [{COLORS['tertiary']}]CSV[/{COLORS['tertiary']}]      "
        "Spreadsheet-compatible (Excel, Google Sheets)\n"
        f"  [{COLORS['tertiary']}]JSON[/{COLORS['tertiary']}]     "
        "Web/API friendly format\n\n"
        f"[bold {COLORS['secondary']}]Databases:[/bold {COLORS['secondary']}]\n"
        f"  [{COLORS['tertiary']}]SQLite[/{COLORS['tertiary']}]   "
        "Local database file\n"
        f"  [{COLORS['tertiary']}]PostgreSQL[/{COLORS['tertiary']}] "
        "Production database"
    )

    console.print()

    # Choose format
    export_format = questionary.select(
        "Choose export format:",
        choices=["CSV", "JSON", "SQLite"],
        default="CSV",
        style=q_style,
    ).ask()

    if not export_format:
        return False

    state.output_format = export_format.lower()

    # Set output path
    if state.output_format == "csv":
        state.export_file = FOREMAN_DIR / f"{state.job_name}.csv"
    elif state.output_format == "json":
        state.export_file = FOREMAN_DIR / f"{state.job_name}.json"
    else:
        state.export_file = FOREMAN_DIR / f"{state.job_name}.db"

    console.print()
    output_path = questionary.text(
        "Output file:",
        default=str(state.export_file),
        style=q_style,
    ).ask()

    if output_path:
        state.export_file = Path(output_path)

    _print_command(f"quarry ship {state.polished_file} {state.export_file}")
    console.print()

    # Perform export
    return _perform_export(state)


def _perform_export(state: TutorialState) -> bool:
    """Perform the actual export operation."""
    try:
        from quarry.tools.ship.base import ExporterFactory  # noqa: PLC0415

        with _show_progress(f"Exporting to {state.output_format.upper()}...") as progress:
            progress.add_task("", total=None)

            # Ensure parent directory exists
            _ensure_dir(state.export_file.parent)

            exporter = ExporterFactory.create(
                str(state.export_file),
                exclude_meta=True,
            )
            stats = exporter.export(str(state.polished_file))

        console.print()
        console.print(f"[{COLORS['tertiary']}]Export Results:[/{COLORS['tertiary']}]")
        console.print(
            f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] "
            f"Records exported: {stats.get('records_written', len(state.polished_data))}"
        )
        console.print(
            f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] "
            f"Format: {state.output_format.upper()}"
        )
        console.print(
            f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] File: {state.export_file}"
        )

        # Show file size
        if state.export_file.exists():
            size = state.export_file.stat().st_size
            if size < KB_SIZE:
                size_str = f"{size} bytes"
            else:
                size_str = f"{size / KB_SIZE:.1f} KB"
            console.print(f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] Size: {size_str}")

        _print_success(f"Data exported to {state.export_file}")
        return True

    except Exception as e:
        _print_error(f"Export failed: {e}")
        return False


def _show_summary(state: TutorialState) -> None:
    """Display tutorial summary."""
    console.print()

    # List created files
    files_created = []
    for f in [state.schema_file, state.raw_file, state.polished_file, state.export_file]:
        if f.exists():
            files_created.append(str(f))

    files_list = "\n".join(
        f"    [{COLORS['tertiary']}]•[/{COLORS['tertiary']}] {f}" for f in files_created
    )

    console.print(
        Panel(
            f"[bold {COLORS['success']}]🎉 Tutorial Complete!"
            f"[/bold {COLORS['success']}]\n\n"
            f"You extracted [bold]{len(state.polished_data)}[/bold] records "
            f"from {state.url}\n\n"
            f"[bold {COLORS['secondary']}]Files created:[/bold {COLORS['secondary']}]\n"
            f"{files_list}\n\n"
            f"[bold {COLORS['secondary']}]What you learned:[/bold {COLORS['secondary']}]\n"
            f"  [{COLORS['primary']}]1. Scout[/{COLORS['primary']}]    → "
            "Analyze page structure\n"
            f"  [{COLORS['primary']}]2. Survey[/{COLORS['primary']}]   → "
            "Define extraction schema\n"
            f"  [{COLORS['primary']}]3. Excavate[/{COLORS['primary']}] → "
            "Extract structured data\n"
            f"  [{COLORS['primary']}]4. Polish[/{COLORS['primary']}]   → "
            "Clean and validate\n"
            f"  [{COLORS['primary']}]5. Ship[/{COLORS['primary']}]     → "
            "Export to any format\n\n"
            f"[{COLORS['dim']}]View your data:[/{COLORS['dim']}]\n"
            f"  [{COLORS['secondary']}]cat {state.export_file}[/{COLORS['secondary']}]",
            border_style=COLORS["success"],
            title="Summary",
            title_align="left",
        )
    )
    console.print()


# =============================================================================
# Main Tutorial Flow
# =============================================================================


def _run_foreman_tutorial() -> None:
    """Execute the guided tutorial flow."""
    if not _show_welcome():
        console.print(
            f"\n[{COLORS['dim']}]No problem! Run 'quarry foreman' when you're ready."
            f"[/{COLORS['dim']}]"
        )
        return

    state = TutorialState()

    # Run each step
    steps = [
        _step_scout,
        _step_survey,
        _step_excavate,
        _step_polish,
        _step_ship,
    ]

    for step_func in steps:
        if not step_func(state):
            console.print(
                f"\n[{COLORS['warning']}]Tutorial paused. Your progress is saved in "
                f"{FOREMAN_DIR}/[/{COLORS['warning']}]"
            )
            return

    _show_summary(state)


def run_foreman() -> None:
    """Launch the Foreman guided tutorial."""
    try:
        _run_foreman_tutorial()
    except KeyboardInterrupt:
        console.print(
            f"\n\n[{COLORS['warning']}]Tutorial cancelled. "
            f"Run 'quarry foreman' to start again![/{COLORS['warning']}]"
        )


@click.command()
def foreman() -> None:
    """
    Launch the interactive guided tutorial with real data extraction.

    Foreman provides a hands-on walkthrough of the complete Quarry pipeline,
    performing actual extraction on a live website.

    \b
    The tutorial covers:
      1. Scout    - Fetch and analyze a webpage
      2. Survey   - Define CSS selectors for extraction
      3. Excavate - Extract real data from the page
      4. Polish   - Clean and validate the data
      5. Ship     - Export to CSV, JSON, or SQLite

    \b
    All output files are saved to: ./foreman_tutorial/

    \b
    Estimated time: 5-10 minutes

    \b
    Example:
      quarry foreman
    """
    run_foreman()


__all__ = ["foreman", "run_foreman"]
