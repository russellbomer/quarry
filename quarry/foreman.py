"""Quarry Foreman - Interactive guided tutorial for new users.

Provides a comprehensive, hands-on walkthrough of the Quarry pipeline where
users input real values they would use in production workflows.
"""

from __future__ import annotations

import time

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
MAX_DISPLAY_LEN = 37  # Max length for truncated display values


# =============================================================================
# Helper Functions
# =============================================================================

def _print_step(step: int, total: int, title: str) -> None:
    """Print a step header."""
    console.print()
    console.print(
        f"[bold {COLORS['primary']}]━━━ Step {step}/{total}: {title} ━━━"
        f"[/bold {COLORS['primary']}]"
    )
    console.print()


def _print_explanation(text: str) -> None:
    """Print explanatory text."""
    console.print(Panel(text, border_style=COLORS["dim"], padding=(1, 2)))


def _print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"\n[{COLORS['success']}]✓ {message}[/{COLORS['success']}]")


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


def _simulate_work(message: str, duration: float = 1.0) -> None:
    """Show a spinner while simulating work."""
    with Progress(
        SpinnerColumn(style=COLORS["secondary"]),
        TextColumn(f"[{COLORS['dim']}]{message}[/{COLORS['dim']}]"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("", total=None)
        time.sleep(duration)


def _wait_for_continue() -> bool:
    """Prompt user to continue or exit."""
    return questionary.confirm(
        "Continue to next step?",
        default=True,
        style=q_style,
    ).ask()


def _show_yaml(content: str, title: str = "Schema") -> None:
    """Display YAML content with syntax highlighting."""
    syntax = Syntax(content, "yaml", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title=title, border_style=COLORS["tertiary"]))


# =============================================================================
# Tutorial State
# =============================================================================

class TutorialState:
    """Holds user inputs throughout the tutorial."""

    def __init__(self):
        self.url: str = ""
        self.job_name: str = ""
        self.item_selector: str = ""
        self.fields: dict = {}
        self.output_format: str = ""
        self.output_file: str = ""
        self.polish_options: list = []


# =============================================================================
# Step Implementations
# =============================================================================

def _show_welcome() -> bool:
    """Display welcome screen."""
    console.clear()
    console.print()
    console.print(
        Panel(
            f"[bold {COLORS['primary']}]Welcome to Quarry Foreman[/bold {COLORS['primary']}]\n\n"
            f"[{COLORS['secondary']}]An interactive tutorial for web data extraction"
            f"[/{COLORS['secondary']}]\n\n"
            "This tutorial will guide you through the complete Quarry workflow.\n"
            "You'll input real values—just like you would in production—to learn\n"
            "how each tool works.\n\n"
            f"[{COLORS['tertiary']}]What you'll learn:[/{COLORS['tertiary']}]\n\n"
            f"  [{COLORS['primary']}]1. Scout[/{COLORS['primary']}]    "
            "Analyze a webpage to understand its structure\n"
            f"  [{COLORS['primary']}]2. Survey[/{COLORS['primary']}]   "
            "Define CSS selectors to target specific data\n"
            f"  [{COLORS['primary']}]3. Excavate[/{COLORS['primary']}] "
            "Extract structured data from the page\n"
            f"  [{COLORS['primary']}]4. Polish[/{COLORS['primary']}]   "
            "Clean, validate, and transform the data\n"
            f"  [{COLORS['primary']}]5. Ship[/{COLORS['primary']}]     "
            "Export to CSV, JSON, SQLite, or PostgreSQL\n\n"
            f"[{COLORS['dim']}]Estimated time: 5-7 minutes[/{COLORS['dim']}]",
            border_style=COLORS["primary"],
            title="🏗️ Foreman Tutorial",
            title_align="left",
        )
    )
    console.print()

    return questionary.confirm(
        "Ready to begin the tutorial?",
        default=True,
        style=q_style,
    ).ask()


def _step_scout(state: TutorialState) -> bool:
    """Step 1: Scout - Analyze page structure."""
    _print_step(1, 5, "Scout")

    _print_explanation(
        f"[bold]What is Scout?[/bold]\n\n"
        "Scout analyzes a webpage to help you understand its structure before\n"
        "you start extracting data. It detects:\n\n"
        f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] "
        "Repeated patterns (lists, tables, cards)\n"
        f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] "
        "Framework signatures (React, Vue, WordPress)\n"
        f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] "
        "API endpoints for data-heavy sites\n"
        f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] "
        "Pagination and infinite scroll patterns\n\n"
        f"[{COLORS['dim']}]Scout saves you time by identifying the best extraction "
        f"strategy upfront.[/{COLORS['dim']}]"
    )

    console.print()
    _print_info("Let's analyze a real webpage. We'll use Hacker News as our example.")
    console.print()

    # Get URL from user
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
    _simulate_work(f"Analyzing {url}...", 2.0)

    # Show simulated results
    table = Table(
        title="Scout Analysis Results",
        border_style=COLORS["tertiary"],
        title_style=f"bold {COLORS['primary']}",
    )
    table.add_column("Finding", style=COLORS["secondary"])
    table.add_column("Details", style="white")
    table.add_row("Page Type", "News/Link Aggregator")
    table.add_row("Framework", "Server-rendered HTML (no JS framework)")
    table.add_row("Repeated Items", "30 story entries detected")
    table.add_row("Item Selector", "tr.athing")
    table.add_row("Pagination", "More link at bottom")
    table.add_row("API Detected", "None (static HTML)")

    console.print(table)

    _print_success("Scout analysis complete!")

    console.print()
    _print_tip(
        "Scout's output helps you decide whether to use CSS selectors (for static HTML)\n"
        "         or API extraction (for JavaScript-heavy sites)."
    )

    console.print()
    return _wait_for_continue()


def _collect_field(
    field_num: int,
    field_name: str,
    default_selector: str,
    hint: str | None = None,
    default_attr: str | None = None,
) -> dict | None:
    """Collect a single field definition from user input."""
    header = f"[bold {COLORS['secondary']}]Field {field_num}: {field_name.title()}"
    console.print(f"{header}[/bold {COLORS['secondary']}]")
    if hint:
        console.print(f"  [{COLORS['dim']}]{hint}[/{COLORS['dim']}]")

    selector = questionary.text(
        f"  CSS selector for {field_name}:",
        default=default_selector,
        style=q_style,
    ).ask()

    if not selector:
        return None

    field_config: dict = {"selector": selector}

    if default_attr is not None:
        attr = questionary.text(
            "  Attribute to extract (leave empty for text):",
            default=default_attr,
            style=q_style,
        ).ask()
        if attr:
            field_config["attribute"] = attr

    return field_config


def _collect_additional_fields(fields: dict) -> None:
    """Allow user to add additional custom fields."""
    while True:
        console.print()
        field_name = questionary.text(
            "Field name (or press Enter to finish):",
            style=q_style,
        ).ask()

        if not field_name:
            break

        field_sel = questionary.text(
            f"  CSS selector for {field_name}:",
            style=q_style,
        ).ask()

        if field_sel:
            field_attr = questionary.text(
                "  Attribute to extract (leave empty for text):",
                style=q_style,
            ).ask()
            fields[field_name] = {"selector": field_sel}
            if field_attr:
                fields[field_name]["attribute"] = field_attr


def _generate_schema_yaml(state: TutorialState) -> str:
    """Generate YAML representation of the schema."""
    schema_yaml = f"""name: {state.job_name}
url: {state.url}
item_selector: "{state.item_selector}"
fields:"""
    for fname, fconfig in state.fields.items():
        schema_yaml += f"\n  {fname}:"
        schema_yaml += f"\n    selector: \"{fconfig['selector']}\""
        if fconfig.get("attribute"):
            schema_yaml += f"\n    attribute: \"{fconfig['attribute']}\""
    return schema_yaml


def _step_survey(state: TutorialState) -> bool:
    """Step 2: Survey - Define extraction schema."""
    _print_step(2, 5, "Survey")

    _print_explanation(
        f"[bold]What is Survey?[/bold]\n\n"
        "Survey helps you build an extraction schema—a blueprint that tells\n"
        "Quarry exactly what data to extract and how to find it.\n\n"
        f"[bold {COLORS['secondary']}]Key concepts:[/bold {COLORS['secondary']}]\n\n"
        f"  [{COLORS['tertiary']}]Item Selector[/{COLORS['tertiary']}] - "
        "CSS selector for repeated items (e.g., each story row)\n"
        f"  [{COLORS['tertiary']}]Field Selectors[/{COLORS['tertiary']}] - "
        "CSS selectors for data within each item\n"
        f"  [{COLORS['tertiary']}]Attributes[/{COLORS['tertiary']}] - "
        "Extract href, src, or other attributes instead of text\n\n"
        f"[{COLORS['dim']}]The schema is saved as a YAML file that can be "
        f"reused and version-controlled.[/{COLORS['dim']}]"
    )

    console.print()
    _print_info("Let's build a schema for extracting Hacker News stories.")
    console.print()

    # Job name
    job_name = questionary.text(
        "Give your extraction job a name:",
        default="hackernews_stories",
        style=q_style,
    ).ask()

    if not job_name:
        return False

    state.job_name = job_name

    console.print()
    _print_info("Now we need to identify how to find each story on the page.")
    console.print()

    # Item selector with explanation
    console.print(
        f"[{COLORS['tertiary']}]The item selector identifies each repeated element.\n"
        f"On Hacker News, each story is in a <tr> with class 'athing'.[/{COLORS['tertiary']}]"
    )
    console.print()

    item_selector = questionary.text(
        "Enter the item selector (CSS):",
        default="tr.athing",
        style=q_style,
    ).ask()

    if not item_selector:
        return False

    state.item_selector = item_selector

    console.print()
    _print_info("Now let's define the fields to extract from each story.")
    _print_tip("Fields use CSS selectors relative to each item.")
    console.print()

    # Collect fields
    fields: dict = {}

    title_field = _collect_field(1, "title", "td.title > span.titleline > a")
    if title_field:
        fields["title"] = title_field

    console.print()

    link_field = _collect_field(
        2,
        "link",
        "td.title > span.titleline > a",
        hint="To get the URL, we extract the 'href' attribute from the same element.",
        default_attr="href",
    )
    if link_field:
        fields["link"] = link_field

    console.print()

    rank_field = _collect_field(3, "rank", "td.title > span.rank")
    if rank_field:
        fields["rank"] = rank_field

    state.fields = fields

    # Add more fields?
    console.print()
    add_more = questionary.confirm(
        "Would you like to add more fields?",
        default=False,
        style=q_style,
    ).ask()

    if add_more:
        _collect_additional_fields(fields)

    # Show the generated schema
    console.print()
    _show_yaml(_generate_schema_yaml(state), title="Generated Schema")

    _print_command(f"quarry survey schemas/{state.job_name}.yml --preview")
    _print_success(f"Schema '{state.job_name}' created with {len(fields)} fields!")

    console.print()
    return _wait_for_continue()


def _step_excavate(state: TutorialState) -> bool:
    """Step 3: Excavate - Extract data."""
    _print_step(3, 5, "Excavate")

    _print_explanation(
        f"[bold]What is Excavate?[/bold]\n\n"
        "Excavate is the extraction engine. It takes your schema and applies it\n"
        "to one or more pages, outputting structured data.\n\n"
        f"[bold {COLORS['secondary']}]Capabilities:[/bold {COLORS['secondary']}]\n\n"
        f"  [{COLORS['tertiary']}]Single page[/{COLORS['tertiary']}] - "
        "Extract from one URL\n"
        f"  [{COLORS['tertiary']}]Multiple pages[/{COLORS['tertiary']}] - "
        "Follow pagination automatically\n"
        f"  [{COLORS['tertiary']}]Rate limiting[/{COLORS['tertiary']}] - "
        "Respect server limits with configurable delays\n"
        f"  [{COLORS['tertiary']}]Retry logic[/{COLORS['tertiary']}] - "
        "Handle temporary failures gracefully\n"
        f"  [{COLORS['tertiary']}]Caching[/{COLORS['tertiary']}] - "
        "Cache responses to speed up development\n\n"
        f"[{COLORS['dim']}]Output is saved as JSONL (JSON Lines) for "
        f"easy processing.[/{COLORS['dim']}]"
    )

    console.print()

    # Configure extraction
    console.print(
        f"[{COLORS['tertiary']}]Let's configure the extraction settings."
        f"[/{COLORS['tertiary']}]"
    )
    console.print()

    # Number of pages
    questionary.select(
        "How many pages should we extract?",
        choices=[
            "1 page (just the first page)",
            "3 pages (follow pagination)",
            "All pages (until no more results)",
        ],
        default="1 page (just the first page)",
        style=q_style,
    ).ask()

    # Rate limiting
    console.print()
    console.print(
        f"[{COLORS['dim']}]Rate limiting prevents overwhelming the server "
        f"and getting blocked.[/{COLORS['dim']}]"
    )
    questionary.select(
        "Delay between requests:",
        choices=[
            "0.5 seconds (fast)",
            "1 second (recommended)",
            "2 seconds (polite)",
            "5 seconds (very conservative)",
        ],
        default="1 second (recommended)",
        style=q_style,
    ).ask()

    # Output file
    console.print()
    output_file = questionary.text(
        "Output file name:",
        default=f"data/{state.job_name}.jsonl",
        style=q_style,
    ).ask()

    if not output_file:
        output_file = f"data/{state.job_name}.jsonl"

    _print_command(f"quarry excavate schemas/{state.job_name}.yml --output {output_file}")

    console.print()
    _simulate_work(f"Extracting data from {state.url}...", 2.5)

    # Show sample extracted data
    sample_data = [
        {"rank": "1.", "title": "Show HN: Open source AI code editor", "link": "https://..."},
        {"rank": "2.", "title": "The unreasonable effectiveness of just showing up", "link": "https://..."},
        {"rank": "3.", "title": "PostgreSQL 17 released with major performance gains", "link": "https://..."},
    ]

    table = Table(
        title=f"Extracted Data Preview (from {output_file})",
        border_style=COLORS["success"],
        title_style=f"bold {COLORS['success']}",
    )
    for field in state.fields.keys():
        table.add_column(field.title(), style=COLORS["secondary"], max_width=40)

    for item in sample_data:
        row = []
        for field in state.fields.keys():
            val = item.get(field, "—")
            if len(str(val)) > MAX_DISPLAY_LEN:
                val = str(val)[:MAX_DISPLAY_LEN] + "..."
            row.append(str(val))
        table.add_row(*row)

    console.print(table)

    console.print()
    console.print(
        f"[{COLORS['dim']}]... and 27 more records[/{COLORS['dim']}]"
    )

    _print_success(f"Extracted 30 records to {output_file}")

    state.output_file = output_file

    console.print()
    return _wait_for_continue()


def _step_polish(state: TutorialState) -> bool:
    """Step 4: Polish - Clean and transform data."""
    _print_step(4, 5, "Polish")

    _print_explanation(
        f"[bold]What is Polish?[/bold]\n\n"
        "Raw extracted data often needs cleaning before it's ready to use.\n"
        "Polish provides a toolkit of data transformations:\n\n"
        f"[bold {COLORS['secondary']}]Cleaning:[/bold {COLORS['secondary']}]\n"
        f"  [{COLORS['tertiary']}]--dedupe[/{COLORS['tertiary']}]        "
        "Remove duplicate records\n"
        f"  [{COLORS['tertiary']}]--strip[/{COLORS['tertiary']}]         "
        "Trim whitespace from text fields\n"
        f"  [{COLORS['tertiary']}]--drop-empty[/{COLORS['tertiary']}]    "
        "Remove records with missing required fields\n\n"
        f"[bold {COLORS['secondary']}]Validation:[/bold {COLORS['secondary']}]\n"
        f"  [{COLORS['tertiary']}]--validate-urls[/{COLORS['tertiary']}] "
        "Check that URL fields are valid\n"
        f"  [{COLORS['tertiary']}]--validate-email[/{COLORS['tertiary']}]"
        " Validate email addresses\n\n"
        f"[bold {COLORS['secondary']}]Transformation:[/bold {COLORS['secondary']}]\n"
        f"  [{COLORS['tertiary']}]--normalize[/{COLORS['tertiary']}]     "
        "Standardize text (lowercase, remove accents)\n"
        f"  [{COLORS['tertiary']}]--extract-domain[/{COLORS['tertiary']}]"
        " Extract domain from URL fields"
    )

    console.print()
    _print_info("Select the polish operations to apply to your data.")
    console.print()

    # Multi-select polish options
    polish_ops = questionary.checkbox(
        "Select operations to apply:",
        choices=[
            questionary.Choice("Remove duplicates (--dedupe)", checked=True),
            questionary.Choice("Strip whitespace (--strip)", checked=True),
            questionary.Choice("Validate URLs (--validate-urls)", checked=True),
            questionary.Choice("Drop empty records (--drop-empty)", checked=False),
            questionary.Choice("Normalize text (--normalize)", checked=False),
        ],
        style=q_style,
    ).ask()

    if polish_ops is None:
        return False

    state.polish_options = polish_ops

    # Build command
    cmd_parts = [f"quarry polish {state.output_file}"]
    if "Remove duplicates (--dedupe)" in polish_ops:
        cmd_parts.append("--dedupe")
    if "Strip whitespace (--strip)" in polish_ops:
        cmd_parts.append("--strip")
    if "Validate URLs (--validate-urls)" in polish_ops:
        cmd_parts.append("--validate-urls")
    if "Drop empty records (--drop-empty)" in polish_ops:
        cmd_parts.append("--drop-empty")
    if "Normalize text (--normalize)" in polish_ops:
        cmd_parts.append("--normalize")

    polished_file = state.output_file.replace(".jsonl", "_polished.jsonl")
    cmd_parts.append(f"--output {polished_file}")

    _print_command(" ".join(cmd_parts))

    console.print()
    _simulate_work("Applying polish operations...", 1.5)

    # Show results
    console.print()
    console.print(
        f"[{COLORS['tertiary']}]Polish Results:[/{COLORS['tertiary']}]"
    )
    console.print(f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] Input records: 30")
    console.print(f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] Duplicates removed: 0")
    console.print(f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] Invalid URLs: 0")
    console.print(f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] Empty records dropped: 0")
    console.print(f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] Output records: 30")

    state.output_file = polished_file
    _print_success(f"Polished data saved to {polished_file}")

    console.print()
    return _wait_for_continue()


def _step_ship(state: TutorialState) -> bool:
    """Step 5: Ship - Export data."""
    _print_step(5, 5, "Ship")

    _print_explanation(
        f"[bold]What is Ship?[/bold]\n\n"
        "Ship exports your cleaned data to various formats and destinations:\n\n"
        f"[bold {COLORS['secondary']}]File Formats:[/bold {COLORS['secondary']}]\n"
        f"  [{COLORS['tertiary']}]CSV[/{COLORS['tertiary']}]      "
        "Spreadsheet-compatible, great for Excel/Google Sheets\n"
        f"  [{COLORS['tertiary']}]JSON[/{COLORS['tertiary']}]     "
        "Structured data for APIs and web applications\n"
        f"  [{COLORS['tertiary']}]Parquet[/{COLORS['tertiary']}]  "
        "Columnar format, efficient for large datasets\n\n"
        f"[bold {COLORS['secondary']}]Databases:[/bold {COLORS['secondary']}]\n"
        f"  [{COLORS['tertiary']}]SQLite[/{COLORS['tertiary']}]   "
        "Local database, no server required\n"
        f"  [{COLORS['tertiary']}]PostgreSQL[/{COLORS['tertiary']}]"
        " Production database with connection string\n\n"
        f"[{COLORS['dim']}]Ship automatically creates tables and infers column types "
        f"from your data.[/{COLORS['dim']}]"
    )

    console.print()

    # Choose format
    export_format = questionary.select(
        "Choose export format:",
        choices=[
            "CSV - Spreadsheet compatible",
            "JSON - Web/API friendly",
            "SQLite - Local database",
            "PostgreSQL - Production database",
        ],
        default="CSV - Spreadsheet compatible",
        style=q_style,
    ).ask()

    if not export_format:
        return False

    state.output_format = export_format.split(" - ")[0].lower()

    console.print()

    # Format-specific options
    if state.output_format == "csv":
        output_dest = questionary.text(
            "Output filename:",
            default=f"exports/{state.job_name}.csv",
            style=q_style,
        ).ask()
        _print_command(f"quarry ship {state.output_file} {output_dest}")

    elif state.output_format == "json":
        output_dest = questionary.text(
            "Output filename:",
            default=f"exports/{state.job_name}.json",
            style=q_style,
        ).ask()
        pretty = questionary.confirm(
            "Pretty print (human readable)?",
            default=True,
            style=q_style,
        ).ask()
        cmd = f"quarry ship {state.output_file} {output_dest}"
        if pretty:
            cmd += " --pretty"
        _print_command(cmd)

    elif state.output_format == "sqlite":
        output_dest = questionary.text(
            "Database filename:",
            default=f"exports/{state.job_name}.db",
            style=q_style,
        ).ask()
        table_name = questionary.text(
            "Table name:",
            default="stories",
            style=q_style,
        ).ask()
        _print_command(
            f"quarry ship {state.output_file} sqlite:///{output_dest} "
            f"--table {table_name}"
        )

    elif state.output_format == "postgresql":
        console.print(
            f"[{COLORS['dim']}]PostgreSQL connection string format:\n"
            f"  postgresql://user:password@host:port/database[/{COLORS['dim']}]"
        )
        console.print()
        output_dest = questionary.text(
            "Connection string:",
            default="postgresql://localhost:5432/mydb",
            style=q_style,
        ).ask()
        table_name = questionary.text(
            "Table name:",
            default="stories",
            style=q_style,
        ).ask()
        if_exists = questionary.select(
            "If table exists:",
            choices=["append", "replace", "fail"],
            default="append",
            style=q_style,
        ).ask()
        _print_command(
            f"quarry ship {state.output_file} {output_dest} "
            f"--table {table_name} --if-exists {if_exists}"
        )

    console.print()
    _simulate_work(f"Exporting to {state.output_format.upper()}...", 1.5)

    _print_success(f"Data exported successfully to {state.output_format.upper()}!")

    return True


def _show_summary(state: TutorialState) -> None:
    """Display tutorial summary with next steps."""
    console.print()
    console.print(
        Panel(
            f"[bold {COLORS['success']}]🎉 Tutorial Complete!"
            f"[/bold {COLORS['success']}]\n\n"
            "You've learned the complete Quarry workflow:\n\n"
            f"  [{COLORS['primary']}]1. Scout[/{COLORS['primary']}]    → "
            f"Analyzed {state.url}\n"
            f"  [{COLORS['primary']}]2. Survey[/{COLORS['primary']}]   → "
            f"Created schema '{state.job_name}' with {len(state.fields)} fields\n"
            f"  [{COLORS['primary']}]3. Excavate[/{COLORS['primary']}] → "
            "Extracted 30 records\n"
            f"  [{COLORS['primary']}]4. Polish[/{COLORS['primary']}]   → "
            f"Applied {len(state.polish_options)} cleaning operations\n"
            f"  [{COLORS['primary']}]5. Ship[/{COLORS['primary']}]     → "
            f"Exported to {state.output_format.upper()}\n\n"
            f"[bold {COLORS['secondary']}]Quick Reference:[/bold {COLORS['secondary']}]\n\n"
            f"  [{COLORS['dim']}]# Analyze a new site[/{COLORS['dim']}]\n"
            f"  [{COLORS['secondary']}]quarry scout https://example.com"
            f"[/{COLORS['secondary']}]\n\n"
            f"  [{COLORS['dim']}]# Create schema interactively[/{COLORS['dim']}]\n"
            f"  [{COLORS['secondary']}]quarry init[/{COLORS['secondary']}]\n\n"
            f"  [{COLORS['dim']}]# Extract data[/{COLORS['dim']}]\n"
            f"  [{COLORS['secondary']}]quarry excavate schema.yml -o data.jsonl"
            f"[/{COLORS['secondary']}]\n\n"
            f"  [{COLORS['dim']}]# Clean and export[/{COLORS['dim']}]\n"
            f"  [{COLORS['secondary']}]quarry polish data.jsonl --dedupe | "
            f"quarry ship - output.csv[/{COLORS['secondary']}]",
            border_style=COLORS["success"],
            title="Summary",
            title_align="left",
        )
    )

    console.print()
    console.print(
        f"[{COLORS['tertiary']}]📚 For more information:[/{COLORS['tertiary']}]"
    )
    console.print(
        f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] "
        "Run any command with --help for detailed options"
    )
    console.print(
        f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] "
        "See USAGE_GUIDE.md for complete documentation"
    )
    console.print(
        f"  [{COLORS['secondary']}]•[/{COLORS['secondary']}] "
        "Check examples/ folder for sample schemas"
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

    # Run each step, stopping if user cancels
    if not _step_scout(state):
        return

    if not _step_survey(state):
        return

    if not _step_excavate(state):
        return

    if not _step_polish(state):
        return

    if not _step_ship(state):
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
def foreman():
    """
    Launch the interactive guided tutorial for new users.

    Foreman provides a comprehensive, hands-on walkthrough of the Quarry
    pipeline. You'll input real values—just like you would in production—
    to learn how each tool works.

    \b
    The tutorial covers:
      1. Scout    - Analyze webpage structure
      2. Survey   - Define extraction schemas with CSS selectors
      3. Excavate - Extract structured data
      4. Polish   - Clean and validate data
      5. Ship     - Export to CSV, JSON, SQLite, or PostgreSQL

    \b
    Estimated time: 5-7 minutes

    \b
    Example:
      quarry foreman
    """
    run_foreman()


__all__ = ["foreman", "run_foreman"]
