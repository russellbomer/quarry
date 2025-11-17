"""CLI for Crate export tool."""

import sys
from pathlib import Path

import click
import questionary

from quarry.lib.prompts import prompt_choice, prompt_file
from quarry.lib.session import get_last_output

from .base import ExporterFactory


@click.command()
@click.argument("input_file", type=click.Path(exists=True), required=False)
@click.argument("destination", required=False)
@click.option("--table", help="Table name for database exports (default: 'records')")
@click.option(
    "--if-exists",
    type=click.Choice(["replace", "append", "fail"]),
    default="replace",
    help="What to do if table/file exists (default: replace)",
)
@click.option("--delimiter", default=",", help="CSV delimiter (default: ',')")
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output")
@click.option(
    "--exclude-meta/--include-meta",
    default=True,
    help="Exclude _meta field from export (default: exclude)",
)
@click.option("--stats", is_flag=True, help="Show detailed statistics")
@click.option(
    "--batch/--interactive",
    "batch_mode",
    default=False,
    help="Batch mode (skip prompts, fail if arguments missing)",
)
def ship(
    input_file, destination, table, if_exists, delimiter, pretty, exclude_meta, stats, batch_mode
):
    """
    Package and export data to various destinations.

    SHIP exports data from JSONL files to CSV, JSON, databases, and more.
    It automatically detects the format from the destination.

    \b
    Interactive Mode (default):
      quarry ship
      → Prompts for input file and export format

    \b
    Batch Mode (with arguments):
      quarry ship data.jsonl output.csv
      quarry ship data.jsonl output.json --pretty --batch
      quarry ship data.jsonl data.db --table products
      quarry ship data.jsonl output.csv --delimiter "|"

    \b
    Supported formats:
      • CSV files (.csv)
      • JSON files (.json)
      • SQLite databases (.db, .sqlite, sqlite://)
      • Parquet files (.parquet)
    """

    # Show helpful error if called without required argument
    if not input_file and not sys.stdin.isatty():
        # Non-interactive terminal (piped/scripted), show error
        click.echo("❌ Error: No input file specified", err=True)
        click.echo("", err=True)
        click.echo("Usage: quarry ship INPUT_FILE DESTINATION [OPTIONS]", err=True)
        click.echo("", err=True)
        click.echo("Examples:", err=True)
        click.echo("  quarry ship data.jsonl output.csv", err=True)
        click.echo("  quarry ship data.jsonl output.json --pretty", err=True)
        click.echo("  quarry ship  # Interactive mode", err=True)
        click.echo("", err=True)
        click.echo("Run 'quarry ship --help' for full options.", err=True)
        sys.exit(1)

    if batch_mode and not input_file:
        # Batch mode without input, show error
        click.echo("❌ Error: No input file specified", err=True)
        click.echo("", err=True)
        click.echo("Usage: quarry ship INPUT_FILE DESTINATION [OPTIONS]", err=True)
        click.echo("", err=True)
        click.echo("Examples:", err=True)
        click.echo("  quarry ship data.jsonl output.csv", err=True)
        click.echo("  quarry ship data.jsonl output.json --pretty", err=True)
        click.echo("  quarry ship  # Interactive mode", err=True)
        click.echo("", err=True)
        click.echo("Run 'quarry ship --help' for full options.", err=True)
        sys.exit(1)

    # Interactive mode: prompt for missing values
    if not batch_mode and not input_file:
        click.echo("📦 Quarry Ship - Interactive Mode\n", err=True)

        try:
            # Check if there's output from a previous tool invocation
            last_output = get_last_output()
            if last_output and last_output.get("format") == "jsonl":
                from datetime import datetime

                timestamp = datetime.fromisoformat(last_output["timestamp"])
                time_ago = (datetime.now(timestamp.tzinfo) - timestamp).total_seconds()

                # Only offer if output was created in the last 5 minutes
                if time_ago < 300:  # 5 minutes
                    click.echo(f"💡 Found recent output: {last_output['path']}", err=True)
                    click.echo(f"   ({last_output['record_count']} records)", err=True)
                    if click.confirm("Use this file?", default=True):
                        input_file = last_output["path"]

            # Prompt for input file if not set
            if not input_file:
                input_file = prompt_file("Input file (JSONL):", allow_cancel=True)

                if not input_file:
                    click.echo("Cancelled", err=True)
                    sys.exit(0)
        except (KeyboardInterrupt, EOFError):
            # Interactive mode failed, show helpful error
            click.echo("\n", err=True)
            click.echo("❌ Interactive mode cancelled or unavailable", err=True)
            click.echo("", err=True)
            click.echo("Usage: quarry ship INPUT_FILE DESTINATION [OPTIONS]", err=True)
            click.echo("", err=True)
            click.echo("Examples:", err=True)
            click.echo("  quarry ship data.jsonl output.csv", err=True)
            click.echo("  quarry ship data.jsonl output.json --pretty", err=True)
            click.echo("", err=True)
            click.echo("Run 'quarry ship --help' for full options.", err=True)
            sys.exit(1)

    if not batch_mode and not destination:
        # Prompt for export format
        format_choice = prompt_choice(
            "Export format:",
            choices=["CSV", "JSON", "SQLite database", "Parquet"],
            allow_cancel=True,
        )

        if not format_choice:
            click.echo("Cancelled", err=True)
            sys.exit(0)

        # Get default filename based on input
        input_path = Path(input_file)

        if format_choice == "CSV":
            default_dest = str(input_path.with_suffix(".csv"))
        elif format_choice == "JSON":
            default_dest = str(input_path.with_suffix(".json"))
            pretty = questionary.confirm("Pretty-print JSON?", default=True).ask()
        elif format_choice == "SQLite database":
            default_dest = str(input_path.with_suffix(".db"))
            table = questionary.text("Table name:", default="records").ask()
        else:  # Parquet
            default_dest = str(input_path.with_suffix(".parquet"))

        # Prompt for destination
        destination = questionary.text("Output destination:", default=default_dest).ask()

        if not destination:
            click.echo("Cancelled", err=True)
            sys.exit(0)

        # Ask about metadata
        exclude_meta = questionary.confirm("Exclude _meta field from export?", default=True).ask()

    # Final validation - should not reach here in normal flow
    if not input_file:
        click.echo("❌ Error: No input file specified", err=True)
        sys.exit(1)

    if not destination:
        click.echo("❌ Error: No destination specified", err=True)
        sys.exit(1)

    click.echo(f"📦 Exporting {input_file} to {destination}...", err=True)

    # Build options
    options = {
        "exclude_meta": exclude_meta,
    }

    if table:
        options["table_name"] = table

    if delimiter != ",":
        options["delimiter"] = delimiter

    if pretty:
        options["pretty"] = True

    if if_exists != "replace":
        options["if_exists"] = if_exists

    try:
        # Create appropriate exporter
        exporter = ExporterFactory.create(destination, **options)

        # Export data
        result_stats = exporter.export(input_file)

        # Report results
        click.echo(
            f"✅ Exported {result_stats['records_written']} records to {destination}", err=True
        )

        if stats or result_stats["records_failed"] > 0:
            click.echo("\n📊 Statistics:", err=True)
            click.echo(f"   Records read: {result_stats['records_read']}", err=True)
            click.echo(f"   Records written: {result_stats['records_written']}", err=True)

            if result_stats["records_failed"] > 0:
                click.echo(f"   Records failed: {result_stats['records_failed']}", err=True)

    except Exception as e:
        click.echo(f"❌ Export failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    ship()
