"""CLI interface for Blueprint tool."""

import sys
from pathlib import Path

import click

from quarry.lib.http import get_html
from quarry.lib.schemas import load_schema, save_schema
from quarry.lib.session import set_last_schema

from .builder import build_schema_interactive, load_analysis_from_file
from .preview import format_preview, preview_extraction


@click.group()
def survey():
    """Design extraction schemas interactively."""
    pass


@survey.command("create")
@click.option(
    "--from-probe",
    "-p",
    type=click.Path(exists=True),
    help="Use Probe analysis JSON as starting point",
)
@click.option("--url", "-u", help="Target URL to analyze")
@click.option("--file", "-f", type=click.Path(exists=True), help="HTML file to analyze")
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="schema.yml",
    help="Output schema file (default: schema.yml)",
)
@click.option(
    "--preview/--no-preview", default=True, help="Preview extraction before saving (default: yes)"
)
def create(from_probe, url, file, output, preview):
    """
    Create a new extraction schema interactively.

    \b
    Examples:
      quarry survey create
      quarry survey create --url https://example.com
      quarry survey create --from-probe analysis.json
      quarry survey create --file page.html --output my-schema.yml
    """
    # Load analysis if provided
    analysis = None
    if from_probe:
        click.echo(f"📊 Loading Probe analysis from {from_probe}", err=True)
        try:
            analysis = load_analysis_from_file(from_probe)
        except Exception as e:
            click.echo(f"Error loading analysis: {e}", err=True)
            sys.exit(1)

    # Load HTML if file provided
    html = None
    if file:
        click.echo(f"📄 Loading HTML from {file}", err=True)
        try:
            html = Path(file).read_text(encoding="utf-8")
        except Exception as e:
            click.echo(f"Error loading file: {e}", err=True)
            sys.exit(1)

    # Build schema interactively
    click.echo("🔨 Starting interactive builder...\n", err=True)
    try:
        schema = build_schema_interactive(url=url, analysis=analysis, html=html)
    except KeyboardInterrupt:
        click.echo("\n\nCancelled by user", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\nError building schema: {e}", err=True)
        sys.exit(1)

    # Preview extraction if requested
    if preview:
        # Get HTML for preview
        preview_html = html
        if not preview_html and schema.url:
            click.echo(f"\n🌐 Fetching {schema.url} for preview...", err=True)
            try:
                preview_html = get_html(schema.url)
            except Exception as e:
                click.echo(f"Warning: Could not fetch URL for preview: {e}", err=True)

        if preview_html:
            click.echo("\n🔍 Preview extraction...", err=True)
            try:
                items = preview_extraction(preview_html, schema, limit=5)
                output_text = format_preview(items, limit=5)
                click.echo(output_text)

                if not click.confirm("\nSave this schema?", default=True):
                    click.echo("Schema not saved", err=True)
                    sys.exit(0)
            except Exception as e:
                click.echo(f"Preview error: {e}", err=True)
                if not click.confirm("Save anyway?", default=False):
                    sys.exit(1)

    # Save schema
    try:
        save_schema(schema, output)
        click.echo(f"\n✅ Schema saved to: {output}", err=True)

        # Store in session for potential chaining
        set_last_schema(
            output,
            schema.url,
            metadata={
                "name": schema.name,
                "fields": list(schema.fields.keys()),
                "item_selector": schema.item_selector,
            },
        )

        # Offer to run excavate next
        click.echo("", err=True)
        if click.confirm("🔗 Run excavate now with this schema?", default=False):
            click.echo("", err=True)
            click.echo("Starting excavate...", err=True)
            click.echo("─" * 50, err=True)

            # Import here to avoid circular dependency
            from quarry.tools.excavate.cli import excavate

            # Invoke excavate command directly
            ctx = click.get_current_context()
            ctx.invoke(
                excavate,
                schema_file=str(output),
                url=schema.url,
                file=None,
                output="output.jsonl",
                max_pages=None,
                no_metadata=False,
                pretty=False,
                batch_mode=False,
            )

    except Exception as e:
        click.echo(f"Error saving schema: {e}", err=True)
        sys.exit(1)


@survey.command("validate")
@click.argument("schema_file", type=click.Path(exists=True))
def validate(schema_file):
    """
    Validate an extraction schema file.

    \b
    Example:
      quarry survey validate schema.yml
    """
    click.echo(f"🔍 Validating {schema_file}...", err=True)

    try:
        schema = load_schema(schema_file)
        click.echo("\n✅ Schema is valid!", err=True)
        click.echo(f"   Name: {schema.name}", err=True)
        click.echo(f"   Item selector: {schema.item_selector}", err=True)
        click.echo(f"   Fields: {len(schema.fields)}", err=True)

        if schema.pagination:
            click.echo("   Pagination: enabled", err=True)

    except Exception as e:
        click.echo("\n❌ Validation failed:", err=True)
        click.echo(f"   {e}", err=True)
        sys.exit(1)


@survey.command("preview")
@click.argument("schema_file", type=click.Path(exists=True))
@click.option("--url", "-u", help="URL to extract from")
@click.option("--file", "-f", type=click.Path(exists=True), help="HTML file to extract from")
@click.option("--limit", "-n", type=int, default=5, help="Max items to show (default: 5)")
def preview_cmd(schema_file, url, file, limit):
    """
    Preview extraction using a schema.

    \b
    Examples:
      quarry survey preview schema.yml --url https://example.com
      quarry survey preview schema.yml --file page.html
    """
    # Load schema
    click.echo(f"📋 Loading schema from {schema_file}...", err=True)
    try:
        schema = load_schema(schema_file)
    except Exception as e:
        click.echo(f"Error loading schema: {e}", err=True)
        sys.exit(1)

    # Get HTML
    html = None
    if file:
        click.echo(f"📄 Loading HTML from {file}...", err=True)
        try:
            html = Path(file).read_text(encoding="utf-8")
        except Exception as e:
            click.echo(f"Error loading file: {e}", err=True)
            sys.exit(1)
    elif url:
        click.echo(f"🌐 Fetching {url}...", err=True)
        try:
            html = get_html(url)
        except Exception as e:
            click.echo(f"Error fetching URL: {e}", err=True)
            sys.exit(1)
    elif schema.url:
        click.echo(f"🌐 Using schema URL: {schema.url}...", err=True)
        try:
            html = get_html(schema.url)
        except Exception as e:
            click.echo(f"Error fetching URL: {e}", err=True)
            sys.exit(1)
    else:
        click.echo("Error: Provide --url or --file option", err=True)
        sys.exit(1)

    # Extract and display
    click.echo("🔍 Extracting...", err=True)
    try:
        items = preview_extraction(html, schema, limit=limit)
        output_text = format_preview(items, limit=limit)
        click.echo(output_text)
    except Exception as e:
        click.echo(f"Extraction error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    survey()
