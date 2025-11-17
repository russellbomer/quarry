"""CLI interface for Forge tool."""

import sys
from pathlib import Path

import click
import questionary

from quarry.lib.schemas import load_schema
from quarry.lib.session import get_last_schema, set_last_output

from .executor import ExcavateExecutor, write_jsonl


@click.command()
@click.argument("schema_file", type=click.Path(exists=True), required=False)
@click.option("--url", "-u", help="URL to extract from (overrides schema URL)")
@click.option("--file", "-f", type=click.Path(exists=True), help="HTML file to extract from")
@click.option("--output", "-o", type=click.Path(), help="Output file path (default: output.jsonl)")
@click.option("--max-pages", type=int, help="Maximum pages to fetch (for pagination)")
@click.option("--no-metadata", is_flag=True, help="Don't include _meta field in output")
@click.option("--pretty", is_flag=True, help="Pretty-print JSON output (not JSONL)")
@click.option(
    "--batch/--interactive",
    "batch_mode",
    default=False,
    help="Batch mode (skip prompts, fail if arguments missing)",
)
def excavate(schema_file, url, file, output, max_pages, no_metadata, pretty, batch_mode):
    """
    Execute extraction at scale using a schema.

    EXCAVATE runs the extraction engine to pull structured data from web pages.
    It handles pagination, rate limiting, and exports to JSONL format.

    \b
    Interactive Mode (default):
      quarry excavate
      → Prompts for schema, source, and output

    \b
    Batch Mode (with flags for automation):
      quarry excavate schema.yml --url https://example.com --output data.jsonl
      quarry excavate schema.yml --file page.html --batch
      quarry excavate schema.yml --max-pages 10
    """
    # Show helpful error if called without required argument
    if not schema_file and not sys.stdin.isatty():
        # Non-interactive terminal (piped/scripted), show error
        click.echo("❌ Error: No schema file specified", err=True)
        click.echo("", err=True)
        click.echo("Usage: quarry excavate SCHEMA_FILE [OPTIONS]", err=True)
        click.echo("", err=True)
        click.echo("Examples:", err=True)
        click.echo("  quarry excavate schema.yml --url https://example.com", err=True)
        click.echo("  quarry excavate schema.yml --file page.html", err=True)
        click.echo("  quarry excavate  # Interactive mode", err=True)
        click.echo("", err=True)
        click.echo("Run 'quarry excavate --help' for full options.", err=True)
        sys.exit(1)

    if not schema_file and batch_mode:
        # Batch mode without schema, show error
        click.echo("❌ Error: No schema file specified", err=True)
        click.echo("", err=True)
        click.echo("Usage: quarry excavate SCHEMA_FILE [OPTIONS]", err=True)
        click.echo("", err=True)
        click.echo("Examples:", err=True)
        click.echo("  quarry excavate schema.yml --url https://example.com", err=True)
        click.echo("  quarry excavate schema.yml --file page.html", err=True)
        click.echo("  quarry excavate  # Interactive mode", err=True)
        click.echo("", err=True)
        click.echo("Run 'quarry excavate --help' for full options.", err=True)
        sys.exit(1)

    # Interactive mode: prompt for missing values
    if not batch_mode and not schema_file:
        click.echo("🔨 Quarry Excavate - Interactive Mode\n", err=True)

        try:
            # Check if there's a schema from a previous tool invocation
            last_schema = get_last_schema()
            if last_schema:
                from datetime import datetime

                timestamp = datetime.fromisoformat(last_schema["timestamp"])
                time_ago = (datetime.now(timestamp.tzinfo) - timestamp).total_seconds()

                # Only offer if schema was created in the last 5 minutes
                if time_ago < 300:  # 5 minutes
                    click.echo(f"💡 Found recent schema: {last_schema['path']}", err=True)
                    if click.confirm("Use this schema?", default=True):
                        schema_file = last_schema["path"]
                        if last_schema.get("url") and not url:
                            url = last_schema["url"]

            # Prompt for schema file if not set
            if not schema_file:
                schema_file = questionary.path(
                    "Schema file:", validate=lambda x: Path(x).exists() or "File does not exist"
                ).ask()

                if not schema_file:
                    click.echo("Cancelled", err=True)
                    sys.exit(0)
        except (KeyboardInterrupt, EOFError):
            # Interactive mode failed, show helpful error
            click.echo("\n", err=True)
            click.echo("❌ Interactive mode cancelled or unavailable", err=True)
            click.echo("", err=True)
            click.echo("Usage: quarry excavate SCHEMA_FILE [OPTIONS]", err=True)
            click.echo("", err=True)
            click.echo("Examples:", err=True)
            click.echo("  quarry excavate schema.yml --url https://example.com", err=True)
            click.echo("  quarry excavate schema.yml --file page.html", err=True)
            click.echo("", err=True)
            click.echo("Run 'quarry excavate --help' for full options.", err=True)
            sys.exit(1)

    # Final check - should not reach here in normal flow
    if not schema_file:
        click.echo("❌ Error: No schema file specified", err=True)
        sys.exit(1)

    # Load schema
    click.echo(f"📋 Loading schema: {schema_file}", err=True)
    try:
        schema = load_schema(schema_file)
    except Exception as e:
        click.echo(f"❌ Error loading schema: {e}", err=True)
        sys.exit(1)

    # Interactive prompts for source
    if not batch_mode and not url and not file:
        choices = ["URL", "Local file"]
        if schema.url:
            choices.append("Use schema URL")
        source_type = questionary.select("Data source:", choices=choices).ask()

        if not source_type:
            click.echo("Cancelled", err=True)
            sys.exit(0)

        if source_type == "URL":
            url = questionary.text(
                "Enter URL:", validate=lambda x: len(x) > 0 or "URL cannot be empty"
            ).ask()
            if not url:
                sys.exit(0)
        elif source_type == "Local file":
            file = questionary.path(
                "HTML file path:", validate=lambda x: Path(x).exists() or "File does not exist"
            ).ask()
            if not file:
                sys.exit(0)
        # else: Use schema URL (already set)

    # Interactive prompt for output
    if not batch_mode and not output:
        default_output = f"{schema.name}.jsonl" if schema.name else "output.jsonl"
        output = questionary.text("Output file:", default=default_output).ask()

        if not output:
            output = default_output

    # Set default output if still not specified
    if not output:
        output = "output.jsonl"

    # Get HTML source
    html = None
    target_url = None

    if file:
        # Load from file
        click.echo(f"📄 Loading HTML from {file}...", err=True)
        try:
            html = Path(file).read_text(encoding="utf-8")
            target_url = f"file://{Path(file).absolute()}"
        except Exception as e:
            click.echo(f"❌ Error loading file: {e}", err=True)
            sys.exit(1)
    else:
        # Determine URL
        target_url = url or schema.url
        if not target_url:
            click.echo("❌ Error: No URL specified (use --url or set url in schema)", err=True)
            sys.exit(1)

    # Create executor
    executor = ExcavateExecutor(schema)

    # Execute extraction
    try:
        if html:
            # Extract from provided HTML
            click.echo("🔨 Extracting from file...", err=True)
            items = executor.parser.parse(html)

            # Add metadata if requested
            if not no_metadata:
                for item in items:
                    item["_meta"] = {
                        "url": target_url,
                        "fetched_at": __import__('datetime').datetime.now().isoformat(),
                        "schema": schema.name,
                    }

            executor.stats["items_extracted"] = len(items)

        elif schema.pagination:
            click.echo(f"🔨 Extracting from {target_url} (with pagination)...", err=True)
            items = executor.fetch_with_pagination(
                target_url, max_pages=max_pages, include_metadata=not no_metadata
            )
        else:
            click.echo(f"🔨 Extracting from {target_url}...", err=True)
            items = executor.fetch_url(target_url, include_metadata=not no_metadata)

    except Exception as e:
        click.echo(f"❌ Extraction failed: {e}", err=True)
        sys.exit(1)

    # Write output
    if items:
        if pretty:
            # Pretty JSON (not JSONL)
            import json

            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8") as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
            click.echo(f"✅ Wrote {len(items)} items to {output} (JSON)", err=True)
            set_last_output(output, "json", len(items))
        else:
            # JSONL format
            count = write_jsonl(items, output)
            click.echo(f"✅ Wrote {count} items to {output} (JSONL)", err=True)
            set_last_output(output, "jsonl", count)

        # Show stats
        stats = executor.get_stats()
        click.echo("\n📊 Statistics:", err=True)
        click.echo(f"   URLs fetched: {stats['urls_fetched']}", err=True)
        click.echo(f"   Items extracted: {stats['items_extracted']}", err=True)
        if stats['errors'] > 0:
            click.echo(f"   Errors: {stats['errors']}", err=True)

        # Offer to run polish next
        if not batch_mode and not pretty:  # Only for JSONL output
            click.echo("", err=True)
            if click.confirm("🔗 Run polish now to clean/transform this data?", default=False):
                click.echo("", err=True)
                click.echo("Starting polish...", err=True)
                click.echo("─" * 50, err=True)

                # Import here to avoid circular dependency
                from quarry.tools.polish.cli import polish

                # Invoke polish command directly
                ctx = click.get_current_context()
                ctx.invoke(
                    polish,
                    input_file=output,
                    output=None,
                    dedupe=None,
                    dedupe_keys=(),
                    dedupe_strategy="first",
                    transform=(),
                    skip_invalid=False,
                    stats=False,
                    batch_mode=False,
                )
    else:
        click.echo("⚠️  No items extracted", err=True)


if __name__ == "__main__":
    excavate()
