"""Interactive workflow wizard for Quarry tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import questionary
from rich.console import Console
from rich.panel import Panel

from quarry.lib.schemas import load_schema, save_schema
from quarry.lib.session import (
    get_last_output,
    get_last_schema,
    set_last_output,
    set_last_schema,
)
from quarry.tools.excavate.executor import ExcavateExecutor, write_jsonl
from quarry.tools.polish.processor import PolishProcessor
from quarry.tools.ship.base import ExporterFactory
from quarry.tools.survey.builder import build_schema_interactive

console = Console()


def run_wizard() -> None:
    """Launch the interactive wizard."""
    try:
        _run_wizard()
    except KeyboardInterrupt:
        console.print("\n[yellow]Wizard cancelled by user[/yellow]")


def _run_wizard() -> None:
    console.print(Panel.fit("Quarry Wizard", border_style="cyan"))

    current_schema: str | None = None
    last_schema = get_last_schema()
    if last_schema:
        current_schema = last_schema.get("path")

    current_output: str | None = None
    last_output = get_last_output()
    if last_output:
        current_output = last_output.get("path")

    while True:
        action = questionary.select(
            "Select an action",
            choices=[
                "Create or edit schema",
                "Run extraction",
                "Polish data",
                "Export data",
                "Exit",
            ],
        ).ask()

        if action == "Create or edit schema":
            current_schema = _create_schema_flow()
        elif action == "Run extraction":
            if not current_schema:
                current_schema = _prompt_schema_path()
            if current_schema:
                current_output = _run_extraction_flow(current_schema)
        elif action == "Polish data":
            if not current_output:
                current_output = _prompt_output_path()
            if current_output:
                current_output = _run_polish_flow(current_output)
        elif action == "Export data":
            if not current_output:
                current_output = _prompt_output_path()
            if current_output:
                _run_export_flow(current_output)
        else:
            console.print("\n[green]Goodbye![/green]")
            return


def _create_schema_flow() -> str | None:
    url = questionary.text("Target URL (optional)", default="").ask()
    html_path = questionary.path("Local HTML file (optional)", default="").ask()
    html_content: str | None = None

    if html_path:
        try:
            html_content = Path(html_path).read_text(encoding="utf-8")
        except OSError as err:
            console.print(f"[red]Failed to read HTML file: {err}[/red]")
            html_content = None

    schema = build_schema_interactive(url=url or None, analysis=None, html=html_content)
    output_default = Path("schemas") / f"{schema.name}.yml"
    output_path = questionary.path(
        "Save schema as",
        default=str(output_default),
    ).ask()

    if not output_path:
        console.print("[yellow]Schema not saved[/yellow]")
        return None

    save_schema(schema, output_path)
    set_last_schema(output_path, schema.url)
    console.print(f"[green]Schema saved to {output_path}[/green]")
    return str(Path(output_path).absolute())


def _prompt_schema_path() -> str | None:
    path = questionary.path(
        "Schema file path",
        validate=lambda value: Path(value).exists() or "File not found",
    ).ask()
    if not path:
        console.print("[yellow]No schema selected[/yellow]")
        return None
    return str(Path(path).absolute())


def _run_extraction_flow(schema_path: str) -> str | None:
    try:
        schema = load_schema(schema_path)
    except Exception as err:  # noqa: BLE001
        console.print(f"[red]Failed to load schema: {err}[/red]")
        return None

    default_url = schema.url or ""
    target_url = questionary.text("URL to extract", default=default_url).ask()
    if not target_url:
        console.print("[yellow]Extraction skipped (no URL provided)[/yellow]")
        return None

    include_metadata = questionary.confirm("Include metadata (_meta field)?", default=True).ask()
    use_pagination = bool(schema.pagination)
    max_pages: int | None = None

    if use_pagination:
        paginate = questionary.confirm("Follow pagination?", default=True).ask()
        if paginate:
            max_pages_answer = questionary.text(
                "Maximum pages (blank = schema default)",
                default="",
            ).ask()
            if max_pages_answer and max_pages_answer.strip():
                try:
                    max_pages = int(max_pages_answer)
                except ValueError:
                    console.print("[yellow]Invalid number, using schema setting[/yellow]")
            if not max_pages:
                max_pages = schema.pagination.max_pages
        else:
            use_pagination = False

    executor = ExcavateExecutor(schema)

    console.print("\n[dim]Fetching data...[/dim]")
    try:
        if use_pagination:
            items = executor.fetch_with_pagination(
                target_url,
                max_pages=max_pages,
                include_metadata=include_metadata,
            )
        else:
            items = executor.fetch_url(target_url, include_metadata=include_metadata)
    except Exception as err:  # noqa: BLE001
        console.print(f"[red]Extraction failed: {err}[/red]")
        return None

    if not items:
        console.print("[yellow]No items extracted[/yellow]")

    default_output = Path("data") / "out" / f"{schema.name}.jsonl"
    output_path = questionary.path(
        "Write results to",
        default=str(default_output),
    ).ask()

    if not output_path:
        console.print("[yellow]Results not saved[/yellow]")
        return None

    try:
        write_jsonl(items, output_path)
    except Exception as err:  # noqa: BLE001
        console.print(f"[red]Failed to write output: {err}[/red]")
        return None

    stats = executor.get_stats()
    console.print(
        f"[green]Saved {stats['items_extracted']} items from {stats['urls_fetched']} page(s) to {output_path}[/green]",
    )

    set_last_output(output_path, "jsonl", len(items))
    return str(Path(output_path).absolute())


def _prompt_output_path() -> str | None:
    path = questionary.path(
        "JSONL file path",
        validate=lambda value: Path(value).exists() or "File not found",
    ).ask()
    if not path:
        console.print("[yellow]No JSONL file selected[/yellow]")
        return None
    return str(Path(path).absolute())


def _run_polish_flow(input_path: str) -> str | None:
    processor = PolishProcessor()

    dedupe = questionary.confirm("Deduplicate records?", default=False).ask()
    dedupe_fields: list[str] | None = None
    dedupe_strategy = "first"

    if dedupe:
        fields_answer = questionary.text(
            "Comma-separated fields for dedupe (blank = full record)",
            default="",
        ).ask()
        if fields_answer:
            dedupe_fields = [field.strip() for field in fields_answer.split(",") if field.strip()]
        dedupe_strategy = (
            questionary.select(
                "Deduplication strategy",
                choices=["first", "last"],
                default="first",
            ).ask()
            or "first"
        )

    skip_invalid = questionary.confirm("Skip records that fail validation?", default=False).ask()

    default_output = Path(input_path).with_name(Path(input_path).stem + "_polished.jsonl")
    output_path = questionary.path(
        "Save polished data as",
        default=str(default_output),
    ).ask()

    if not output_path:
        console.print("[yellow]Polish step cancelled[/yellow]")
        return input_path

    try:
        stats = processor.process(
            input_file=input_path,
            output_file=output_path,
            deduplicate=dedupe,
            dedupe_keys=dedupe_fields,
            dedupe_strategy=dedupe_strategy,
            transformations=None,
            validation_rules=None,
            skip_invalid=skip_invalid,
            filter_func=None,
        )
    except Exception as err:  # noqa: BLE001
        console.print(f"[red]Polish failed: {err}[/red]")
        return input_path

    console.print(
        f"[green]Polish complete: {stats['records_written']} records written to {output_path}[/green]",
    )
    set_last_output(output_path, "jsonl", stats["records_written"])
    return str(Path(output_path).absolute())


def _run_export_flow(input_path: str) -> None:
    destination = questionary.text("Export destination (e.g., output.csv)", default="").ask()
    if not destination:
        console.print("[yellow]Export skipped[/yellow]")
        return

    options: dict[str, Any] = {}

    dest_lower = destination.lower()
    if dest_lower.endswith(".csv"):
        delimiter = questionary.text("CSV delimiter", default=",").ask()
        if delimiter:
            options["delimiter"] = delimiter
    elif dest_lower.endswith(".json"):
        pretty = questionary.confirm("Pretty-print JSON?", default=False).ask()
        options["pretty"] = bool(pretty)
    elif dest_lower.endswith((".db", ".sqlite", ".sqlite3")) or dest_lower.startswith("sqlite://"):
        table = questionary.text("Table name", default="records").ask()
        if table:
            options["table"] = table
        mode = questionary.select(
            "If table exists",
            choices=["replace", "append", "fail"],
            default="replace",
        ).ask()
        if mode:
            options["if_exists"] = mode

    try:
        exporter = ExporterFactory.create(destination, **options)
        stats = exporter.export(input_path)
    except NotImplementedError as err:
        console.print(f"[yellow]{err}[/yellow]")
        return
    except Exception as err:  # noqa: BLE001
        console.print(f"[red]Export failed: {err}[/red]")
        return

    console.print(
        f"[green]Exported {stats['records_written']} records to {destination}[/green]",
    )


__all__ = ["run_wizard"]
