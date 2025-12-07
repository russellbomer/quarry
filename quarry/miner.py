"""Interactive miner workflow for Quarry tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, cast

import questionary
from questionary import Style as QStyle
from rich.console import Console
from rich.panel import Panel

from quarry.lib import paths
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


def _auto_paths_enabled() -> bool:
    """Return True when QUARRY_OUTPUT_DIR should drive path defaults."""
    return paths.auto_path_mode_enabled()


def _notify_auto_destination(action: str, target: Path) -> None:
    """Show a short message explaining where automated outputs go."""
    target_display = str(target)
    console.print(
        f"[{COLORS['info']}]{action}: {target_display}"
        f" (set by {paths.OUTPUT_ENV_VAR})[/{COLORS['info']}]"
    )


def run_miner() -> None:
    """Launch the interactive miner."""
    try:
        _run_miner()
    except KeyboardInterrupt:
        console.print(f"\n[{COLORS['warning']}]Miner cancelled by user[/{COLORS['warning']}]")


def _run_miner() -> None:
    console.print(Panel.fit("Quarry Miner", border_style=COLORS["primary"]))
    console.print("[dim]Starting full extraction pipeline...[/dim]\n")

    # Step 1: Create schema
    console.print(f"[{COLORS['primary']}]Step 1: Create Schema[/{COLORS['primary']}]")
    current_schema = _create_schema_flow()
    if not current_schema:
        console.print(f"[{COLORS['warning']}]Pipeline cancelled[/{COLORS['warning']}]")
        return

    # Step 2: Run extraction
    console.print(f"\n[{COLORS['primary']}]Step 2: Extract Data[/{COLORS['primary']}]")
    if not questionary.confirm("Continue to extraction?", default=True).ask():
        console.print(f"[{COLORS['success']}]Schema saved. Run 'quarry.excavate {current_schema}' to extract data.[/{COLORS['success']}]")
        return

    current_output = _run_extraction_flow(current_schema)
    if not current_output:
        console.print(f"[{COLORS['warning']}]Pipeline stopped at extraction[/{COLORS['warning']}]")
        return

    # Step 3: Polish data
    console.print(f"\n[{COLORS['primary']}]Step 3: Polish Data[/{COLORS['primary']}]")
    if not questionary.confirm("Continue to polish?", default=True).ask():
        console.print(f"[{COLORS['success']}]Data extracted to {current_output}[/{COLORS['success']}]")
        return

    polished_output = _run_polish_flow(current_output)
    if not polished_output:
        polished_output = current_output

    # Step 4: Export data
    console.print(f"\n[{COLORS['primary']}]Step 4: Export Data[/{COLORS['primary']}]")
    if not questionary.confirm("Continue to export?", default=True).ask():
        console.print(f"[{COLORS['success']}]Data ready at {polished_output}[/{COLORS['success']}]")
        return

    _run_export_flow(polished_output)
    
    console.print(f"\n[{COLORS['success']}]✨ Pipeline complete![/{COLORS['success']}]")


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

    auto_paths = _auto_paths_enabled()
    output_default = paths.default_schema_path(schema.name, create_dirs=auto_paths)
    if auto_paths:
        output_path = str(output_default)
        _notify_auto_destination("Saving schema to", output_default)
    else:
        output_path = questionary.path(
            "Save schema as",
            default=str(output_default),
        ).ask()

    if not output_path:
        console.print(f"[{COLORS['warning']}]Schema not saved[/{COLORS['warning']}]")
        return None

    output_path_obj = Path(output_path)
    paths.ensure_parent_dir(output_path_obj)
    save_schema(schema, output_path_obj)
    output_path_str = str(output_path_obj)
    set_last_schema(
        output_path_str,
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
    console.print(f"[{COLORS['success']}]Schema saved to {output_path_str}[/{COLORS['success']}]")
    return str(Path(output_path_str).absolute())


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

    auto_paths = _auto_paths_enabled()
    schema_label = schema.name or Path(schema_path).stem
    output_default = paths.default_extraction_output(schema_label, create_dirs=auto_paths)
    if auto_paths:
        output_path = str(output_default)
        _notify_auto_destination("Writing extraction output to", output_default)
    else:
        output_path = questionary.path(
            "Write results to",
            default=str(output_default),
        ).ask()

    if not output_path:
        console.print(f"[{COLORS['warning']}]Results not saved[/{COLORS['warning']}]")
        return None

    try:
        output_path_obj = Path(output_path)
        paths.ensure_parent_dir(output_path_obj)
        output_path = str(output_path_obj)
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

    absolute_output = str(Path(output_path).absolute())
    set_last_output(absolute_output, "jsonl", len(items))
    return absolute_output


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

    auto_paths = _auto_paths_enabled()
    input_path_obj = Path(input_path)
    polished_stem = input_path_obj.stem
    output_default = paths.default_polished_output(
        polished_stem,
        suffix=input_path_obj.suffix,
        create_dirs=auto_paths,
    )
    if auto_paths:
        output_path = str(output_default)
        _notify_auto_destination("Saving polished data to", output_default)
    else:
        output_path = questionary.path(
            "Save polished data as",
            default=str(output_default),
        ).ask()

    if not output_path:
        console.print(f"[{COLORS['warning']}]Polish step cancelled[/{COLORS['warning']}]")
        return input_path

    try:
        output_path_obj = Path(output_path)
        paths.ensure_parent_dir(output_path_obj)
        stats = processor.process(
            input_file=input_path,
            output_file=str(output_path_obj),
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
        f"{output_path_obj}[/{COLORS['success']}]",
    )
    output_abs = str(Path(output_path_obj).absolute())
    set_last_output(output_abs, "jsonl", stats["records_written"])
    return output_abs


def _run_export_flow(input_path: str) -> None:
    default_filename = Path(input_path).stem or "quarry_export"
    auto_paths = _auto_paths_enabled()

    # Prompt for export format first
    format_choice = questionary.select(
        "Export format:",
        choices=[
            questionary.Choice("CSV - Comma-separated values", value="csv"),
            questionary.Choice("JSON - Pretty JSON array", value="json"),
            questionary.Choice("JSONL - JSON Lines (streaming)", value="jsonl"),
            questionary.Choice("Parquet - Columnar format", value="parquet"),
            questionary.Choice("PostgreSQL - Database table", value="postgres"),
            questionary.Choice("SQLite - Database file", value="sqlite"),
        ],
    ).ask()

    if not format_choice:
        console.print(f"[{COLORS['warning']}]Export cancelled[/{COLORS['warning']}]")
        return

    # Handle PostgreSQL connection string separately
    if format_choice == "postgres":
        console.print()
        console.print("[dim]PostgreSQL connection examples:[/dim]")
        console.print("[dim]  postgresql://user:password@localhost/dbname[/dim]")
        console.print("[dim]  postgresql://user@localhost:5432/mydb[/dim]")
        console.print()
        
        destination = questionary.text(
            "PostgreSQL connection string",
            default="postgresql://user:password@localhost/quarry",
        ).ask()
        
        if not destination:
            console.print(f"[{COLORS['warning']}]Export cancelled[/{COLORS['warning']}]")
            return
    else:
        # Set extension based on choice for file-based exports
        extension_map = {
            "csv": "csv",
            "json": "json",
            "jsonl": "jsonl",
            "parquet": "parquet",
            "sqlite": "db",
        }
        extension = extension_map.get(format_choice, "csv")

        default_destination = paths.default_export_path(
            default_filename,
            extension=extension,
            create_dirs=auto_paths,
        )
        if auto_paths:
            destination = str(default_destination)
            _notify_auto_destination("Export destination", default_destination)
        else:
            destination = questionary.text(
                f"Export destination (e.g., output.{extension})",
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
        pretty = questionary.confirm("Pretty-print JSON?", default=True).ask()
        options["pretty"] = bool(pretty)
    elif dest_lower.startswith("postgresql://") or dest_lower.startswith("postgres://"):
        table = questionary.text("Table name", default="records").ask()
        if table:
            options["table_name"] = table
        
        mode = questionary.select(
            "If table exists",
            choices=["append", "replace", "fail"],
            default="append",
        ).ask()
        if mode:
            options["if_exists"] = mode
        
        exclude_meta = questionary.confirm(
            "Exclude _meta field?",
            default=True,
        ).ask()
        options["exclude_meta"] = bool(exclude_meta)
        
        upsert = questionary.confirm(
            "Use upsert (INSERT ... ON CONFLICT)?",
            default=False,
        ).ask()
        if upsert:
            upsert_key = questionary.text(
                "Upsert key column (e.g., 'id' or 'url')",
                default="",
            ).ask()
            if upsert_key and upsert_key.strip():
                options["upsert_key"] = upsert_key.strip()
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


__all__ = ["run_miner"]
