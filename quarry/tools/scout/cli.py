"""CLI interface for Probe tool."""

import sys
from pathlib import Path

import click
import questionary

from quarry.lib.http import get_html
from quarry.lib.prompts import prompt_choice, prompt_confirm, prompt_file, prompt_url

from .analyzer import analyze_page
from .reporter import format_as_json, format_as_terminal


@click.command()
@click.argument("url_or_file", required=False)
@click.option(
    "--file", "-f", type=click.Path(exists=True), help="Analyze HTML from file instead of URL"
)
@click.option(
    "--output", "-o", type=click.Path(), help="Save output to file (default: print to stdout)"
)
@click.option(
    "--format",
    type=click.Choice(["terminal", "json"], case_sensitive=False),
    default="terminal",
    help="Output format (default: terminal)",
)
@click.option("--pretty/--compact", default=True, help="Pretty-print JSON output (default: pretty)")
@click.option(
    "--find-api", is_flag=True, help="Show guide for finding API endpoints (infinite scroll sites)"
)
@click.option(
    "--batch/--interactive",
    "batch_mode",
    default=False,
    help="Batch mode (skip prompts, fail if arguments missing)",
)
def scout(url_or_file, file, output, format, pretty, find_api, batch_mode):
    """
    Analyze HTML structure and detect patterns.

    SCOUT examines web pages to identify:

    \b
    • Frameworks (Bootstrap, React, WordPress, etc.)
    • Repeated elements (likely data items)
    • Page structure and metadata
    • Extraction suggestions

    \b
    Interactive Mode (default):
      quarry scout
      → Prompts for URL or file path

    \b
    Batch Mode (with arguments):
      quarry scout https://news.ycombinator.com
      quarry scout --file page.html --format json
      quarry scout https://github.com --output analysis.json --batch
      quarry scout --find-api  # Guide for infinite scroll sites
    """

    # Show API finding guide if requested
    if find_api:
        from .api_guide import show_api_guide

        show_api_guide()
        return

    # Interactive mode: prompt for missing values
    if not batch_mode and not url_or_file and not file:
        click.echo("🔍 Quarry Scout - Interactive Mode\n", err=True)

        # Prompt for source type (with retry)
        source_type = prompt_choice("Analyze:", choices=["URL", "Local file"], allow_cancel=True)

        if not source_type:
            click.echo("Cancelled", err=True)
            sys.exit(0)

        if source_type == "URL":
            url_or_file = prompt_url("Enter URL:", allow_cancel=True)
            if not url_or_file:
                sys.exit(0)
        else:  # Local file
            file = prompt_file("HTML file path:", allow_cancel=True)
            if not file:
                sys.exit(0)

        # Ask about output
        save_output = prompt_confirm("Save results to file?", default=False)

        if save_output:
            output = questionary.text("Output file:", default="scout_analysis.json").ask()

            if output:
                # Suggest JSON format if saving
                format = (
                    prompt_choice(
                        "Output format:", choices=["json", "terminal"], allow_cancel=False
                    )
                    or "json"
                )

    # Validate required arguments in batch mode
    if not url_or_file and not file:
        click.echo("Error: Provide a URL or use --file option", err=True)
        sys.exit(1)

    # Determine source
    if file:
        html_source = Path(file)
        url = None
        click.echo(f"📄 Analyzing file: {file}", err=True)
    elif url_or_file:
        if url_or_file.startswith("http://") or url_or_file.startswith("https://"):
            html_source = url_or_file
            url = url_or_file
            click.echo(f"🌐 Fetching: {url}", err=True)
        else:
            # Treat as file path
            html_source = Path(url_or_file)
            url = None
            click.echo(f"📄 Analyzing file: {url_or_file}", err=True)
    else:
        # Should not reach here due to validation above
        click.echo("Error: No source specified", err=True)
        sys.exit(1)

    # Get HTML
    try:
        if isinstance(html_source, Path):
            html = html_source.read_text(encoding="utf-8")
        else:
            html = get_html(html_source)
    except Exception as e:
        click.echo(f"Error loading HTML: {e}", err=True)
        sys.exit(1)

    if not html:
        click.echo("Error: No HTML content retrieved", err=True)
        sys.exit(1)

    # Analyze
    click.echo("🔍 Analyzing...", err=True)
    try:
        analysis = analyze_page(html, url=url)
    except Exception as e:
        click.echo(f"Error during analysis: {e}", err=True)
        sys.exit(1)

    # Format output
    if format.lower() == "json":
        result = format_as_json(analysis, pretty=pretty)
    else:
        result = format_as_terminal(analysis)

    # Output
    if output:
        output_path = Path(output)
        output_path.write_text(result, encoding="utf-8")
        click.echo(f"✅ Saved to: {output}", err=True)
    else:
        click.echo(result)

    # Offer to run survey next (only in interactive mode and if we have a URL)
    if not batch_mode and url and format.lower() == "terminal":
        click.echo("", err=True)
        if click.confirm("🔗 Create extraction schema now with survey?", default=False):
            click.echo("", err=True)
            click.echo("Starting survey...", err=True)
            click.echo("─" * 50, err=True)

            # Import here to avoid circular dependency
            from quarry.tools.survey.cli import create

            # Save analysis to temp file if not already saved
            analysis_file = None
            if output and format.lower() == "json":
                analysis_file = output
            elif format.lower() == "terminal":
                # Save analysis to temp file for survey to use
                import json
                import tempfile

                fd, analysis_file = tempfile.mkstemp(suffix=".json", prefix="probe_")
                with open(fd, 'w') as f:
                    json.dump(analysis, f, indent=2)

            # Build context for survey create
            ctx = click.get_current_context()

            # Invoke create command directly with new context
            try:
                ctx.invoke(
                    create,
                    url=url,
                    from_probe=analysis_file,
                    file=None,
                    output="schema.yml",
                    preview=True,
                )
            finally:
                # Clean up temp file if we created one
                if analysis_file and not output:
                    import os

                    try:
                        os.unlink(analysis_file)
                    except Exception:
                        pass


if __name__ == "__main__":
    scout()
