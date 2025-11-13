"""CLI for Crate export tool."""

import sys
import click

from .base import ExporterFactory


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.argument("destination")
@click.option(
    "--table",
    help="Table name for database exports (default: 'records')"
)
@click.option(
    "--if-exists",
    type=click.Choice(["replace", "append", "fail"]),
    default="replace",
    help="What to do if table/file exists (default: replace)"
)
@click.option(
    "--delimiter",
    default=",",
    help="CSV delimiter (default: ',')"
)
@click.option(
    "--pretty",
    is_flag=True,
    help="Pretty-print JSON output"
)
@click.option(
    "--exclude-meta/--include-meta",
    default=True,
    help="Exclude _meta field from export (default: exclude)"
)
@click.option(
    "--stats",
    is_flag=True,
    help="Show detailed statistics"
)
def crate(input_file, destination, table, if_exists, delimiter, pretty, exclude_meta, stats):
    """
    Package and export data to various destinations.
    
    CRATE exports data from JSONL files to CSV, JSON, databases, and more.
    It automatically detects the format from the destination.
    
    \b
    Examples:
      foundry crate data.jsonl output.csv
      foundry crate data.jsonl output.json --pretty
      foundry crate data.jsonl data.db --table products
      foundry crate data.jsonl sqlite://data.db --table records
      foundry crate data.jsonl output.csv --delimiter "|"
    
    \b
    Supported formats:
      • CSV files (.csv)
      • JSON files (.json)
      • SQLite databases (.db, .sqlite, sqlite://)
      • PostgreSQL (coming soon)
      • MySQL (coming soon)
    """
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
        click.echo(f"✅ Exported {result_stats['records_written']} records to {destination}", err=True)
        
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
    crate()
