"""Interactive workflow wizard for Quarry tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast

import questionary
from questionary import Style as QStyle
from rich.console import Console
from rich.panel import Panel

from quarry.lib.http import get_html
from quarry.lib.schemas import load_schema, save_schema
from quarry.lib.session import (
    get_last_analysis,
    get_last_output,
    get_last_schema,
    set_last_analysis,
    set_last_output,
    set_last_schema,
)
from quarry.lib.theme import COLORS, QUARRY_THEME, QUESTIONARY_STYLE
from quarry.tools.excavate.executor import ExcavateExecutor, write_jsonl
from quarry.tools.polish.processor import PolishProcessor
from quarry.tools.scout.analyzer import analyze_page
from quarry.tools.ship.base import ExporterFactory
from quarry.tools.survey.builder import build_schema_interactive

console = Console(theme=QUARRY_THEME)

# Questionary style using Mars/Jupiter palette
q_style = QStyle.from_dict(QUESTIONARY_STYLE)


def run_wizard() -> None:
    """Launch the interactive wizard."""
    try:
        _run_wizard()
    except KeyboardInterrupt:
        console.print(f"\n[{COLORS['warning']}]Wizard cancelled by user[/{COLORS['warning']}]")


def _run_wizard() -> None:
    console.print(Panel.fit("Quarry Wizard", border_style=COLORS["primary"]))

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
            style=q_style,
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
            console.print(f"\n[{COLORS['success']}]Goodbye![/{COLORS['success']}]")
            return


def _create_schema_flow() -> str | None:
    url = questionary.text("Target URL (optional)", default="").ask()
    html_path = questionary.path("Local HTML file (optional)", default="").ask()
    html_content: str | None = None
    analysis: dict[str, Any] | None = None

    if html_path:
        try:
            html_content = Path(html_path).read_text(encoding="utf-8")
        except OSError as err:
            console.print(f"[{COLORS['error']}]Failed to read HTML file: {err}[/{COLORS['error']}]")
            html_content = None
    elif url:
        try:
            console.print("[dim]Running Scout analysis...[/dim]")
            html_content = get_html(url)
        except Exception as err:
            console.print(f"[{COLORS['error']}]Failed to fetch URL: {err}[/{COLORS['error']}]")
            html_content = None

    if html_content:
        try:
            analysis = analyze_page(html_content, url=url or None)
        except Exception as err:
            console.print(
                f"[{COLORS['warning']}]Scout analysis failed: {err}[/{COLORS['warning']}]"
            )
            analysis = None

    if analysis:
        frameworks = analysis.get("frameworks") or []
        framework_summary = (
            ", ".join(f"{fw['name']} ({fw['confidence'] * 100:.0f}%)" for fw in frameworks[:2])
            if frameworks
            else "None detected"
        )
        container_count = len(analysis.get("containers") or [])
        suggested_selector = (analysis.get("suggestions") or {}).get("item_selector") or "n/a"
        console.print(
            Panel(
                f"Frameworks: {framework_summary}\n"
                f"Candidate containers: {container_count}\n"
                f"Suggested item selector (prefills next step): {suggested_selector}",
                title="Scout Summary",
                title_align="left",
                border_style=COLORS["tertiary"],
                expand=False,
            )
        )

    schema = build_schema_interactive(
        url=url or None,
        analysis=analysis,
        html=html_content,
    )
    output_default = Path("schemas") / f"{schema.name}.yml"
    output_path = questionary.path(
        "Save schema as",
        default=str(output_default),
    ).ask()

    if not output_path:
        console.print(f"[{COLORS['warning']}]Schema not saved[/{COLORS['warning']}]")
        return None

    save_schema(schema, output_path)
    set_last_schema(
        output_path,
        schema.url,
        metadata={
            "name": schema.name,
            "fields": list(schema.fields.keys()),
            "item_selector": schema.item_selector,
        },
    )
    if analysis:
        set_last_analysis(
            {
                "url": schema.url or url,
                "frameworks": analysis.get("frameworks"),
                "suggested_selector": (analysis.get("suggestions") or {}).get("item_selector"),
                "field_candidates": (analysis.get("suggestions") or {}).get("field_candidates"),
                "containers": analysis.get("containers"),
                "schema_name": schema.name,
                "schema_fields": list(schema.fields.keys()),
            }
        )
    console.print(f"[{COLORS['success']}]Schema saved to {output_path}[/{COLORS['success']}]")
    return str(Path(output_path).absolute())


def _prompt_schema_path() -> str | None:
    path = questionary.path(
        "Schema file path",
        validate=lambda value: Path(value).exists() or "File not found",
    ).ask()
    if not path:
        console.print(f"[{COLORS['warning']}]No schema selected[/{COLORS['warning']}]")
        return None
    return str(Path(path).absolute())


def _run_extraction_flow(schema_path: str) -> str | None:
    try:
        schema = load_schema(schema_path)
    except Exception as err:
        console.print(f"[{COLORS['error']}]Failed to load schema: {err}[/{COLORS['error']}]")
        return None

    last_analysis = get_last_analysis()
    if last_analysis:
        frameworks = last_analysis.get("frameworks") or []
        framework_summary = (
            ", ".join(fw.get("name", "") for fw in frameworks[:2]) if frameworks else "n/a"
        )
        suggested_selector = last_analysis.get("suggested_selector") or "n/a"
        console.print(
            Panel(
                f"Schema: {last_analysis.get('schema_name', schema.name)}\n"
                f"Framework hint: {framework_summary}\n"
                f"Suggested selector: {suggested_selector}",
                title="Extraction Context",
                title_align="left",
                border_style=COLORS["tertiary"],
                expand=False,
            )
        )

    default_url = schema.url or ""
    target_url = questionary.text("URL to extract", default=default_url).ask()
    if not target_url:
        console.print(
            f"[{COLORS['warning']}]Extraction skipped (no URL provided)[/{COLORS['warning']}]"
        )
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
                    warn = COLORS['warning']
                    console.print(f"[{warn}]Invalid number, using schema setting[/{warn}]")
            if not max_pages:
                assert schema.pagination is not None
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
    except Exception as err:
        console.print(f"[{COLORS['error']}]Extraction failed: {err}[/{COLORS['error']}]")
        return None

    if not items:
        console.print(f"[{COLORS['warning']}]No items extracted[/{COLORS['warning']}]")

    default_output = Path("data") / "out" / f"{schema.name}.jsonl"
    output_path = questionary.path(
        "Write results to",
        default=str(default_output),
    ).ask()

    if not output_path:
        console.print(f"[{COLORS['warning']}]Results not saved[/{COLORS['warning']}]")
        return None

    try:
        write_jsonl(items, output_path)
    except Exception as err:
        console.print(f"[{COLORS['error']}]Failed to write output: {err}[/{COLORS['error']}]")
        return None

    stats = executor.get_stats()
    ok = COLORS['success']
    console.print(
        f"[{ok}]Saved {stats['items_extracted']} items from {stats['urls_fetched']} page(s) "
        f"to {output_path}[/{ok}]",
    )

    set_last_output(output_path, "jsonl", len(items))
    return str(Path(output_path).absolute())


def _prompt_output_path() -> str | None:
    path = questionary.path(
        "JSONL file path",
        validate=lambda value: Path(value).exists() or "File not found",
    ).ask()
    if not path:
        console.print(f"[{COLORS['warning']}]No JSONL file selected[/{COLORS['warning']}]")
        return None
    return str(Path(path).absolute())


def _run_polish_flow(input_path: str) -> str | None:
    processor = PolishProcessor()

    dedupe = questionary.confirm("Deduplicate records?", default=False).ask()
    dedupe_fields: list[str] | None = None
    dedupe_strategy = "first"

    if dedupe:
        suggested_fields: list[str] = []
        last_schema = get_last_schema()
        if last_schema and last_schema.get("path") and Path(last_schema["path"]).exists():
            try:
                schema = load_schema(last_schema["path"])
                for candidate in ("id", "link", "url", "slug"):
                    if candidate in schema.fields:
                        suggested_fields = [candidate]
                        break
            except Exception:  # pragma: no cover - advisory only
                suggested_fields = []

        fields_answer = questionary.text(
            "Comma-separated fields for dedupe (blank = full record)",
            default=", ".join(suggested_fields) if suggested_fields else "",
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
        console.print(f"[{COLORS['warning']}]Polish step cancelled[/{COLORS['warning']}]")
        return input_path

    try:
        stats = processor.process(
            input_file=input_path,
            output_file=output_path,
            deduplicate=dedupe,
            dedupe_keys=dedupe_fields,
            dedupe_strategy=cast(Literal["first", "last"], dedupe_strategy),
            transformations=None,
            validation_rules=None,
            skip_invalid=skip_invalid,
            filter_func=None,
        )
    except Exception as err:
        console.print(f"[{COLORS['error']}]Polish failed: {err}[/{COLORS['error']}]")
        return input_path

    console.print(
        f"[{COLORS['success']}]Polish complete: {stats['records_written']} records written to "
        f"{output_path}[/{COLORS['success']}]",
    )
    set_last_output(output_path, "jsonl", stats["records_written"])
    return str(Path(output_path).absolute())


def _run_export_flow(input_path: str) -> None:
    default_filename = Path(input_path).stem or "quarry_export"
    default_destination = Path.cwd() / f"{default_filename}.csv"
    destination = questionary.text(
        "Export destination (e.g., output.csv)",
        default=str(default_destination),
    ).ask()
    if not destination:
        destination = str(default_destination)
        console.print(
            f"[{COLORS['info']}]Using default export path {destination}[/{COLORS['info']}]"
        )

    last_output = get_last_output()
    if last_output:
        console.print(
            Panel(
                f"Records ready: {last_output.get('record_count', 'n/a')}\n"
                f"Source file: {last_output.get('path', '')}",
                title="Current Dataset",
                title_align="left",
                border_style=COLORS["tertiary"],
                expand=False,
            )
        )

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
        console.print(f"[{COLORS['warning']}]{err}[/{COLORS['warning']}]")
        return
    except Exception as err:
        console.print(f"[{COLORS['error']}]Export failed: {err}[/{COLORS['error']}]")
        return

    ok = COLORS['success']
    console.print(f"[{ok}]Exported {stats['records_written']} records to {destination}[/{ok}]")


__all__ = ["run_wizard"]
