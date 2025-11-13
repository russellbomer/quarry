"""CLI interface for Probe tool."""

import sys
from pathlib import Path

import click

from foundry.lib.http import get_html
from .analyzer import analyze_page
from .reporter import format_as_json, format_as_terminal


@click.command()
@click.argument("url_or_file", required=False)
@click.option(
    "--file", "-f",
    type=click.Path(exists=True),
    help="Analyze HTML from file instead of URL"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Save output to file (default: print to stdout)"
)
@click.option(
    "--format",
    type=click.Choice(["terminal", "json"], case_sensitive=False),
    default="terminal",
    help="Output format (default: terminal)"
)
@click.option(
    "--pretty/--compact",
    default=True,
    help="Pretty-print JSON output (default: pretty)"
)
@click.option(
    "--find-api",
    is_flag=True,
    help="Show guide for finding API endpoints (infinite scroll sites)"
)
def probe(url_or_file, file, output, format, pretty, find_api):
    """
    Analyze HTML structure and detect patterns.
    
    PROBE examines web pages to identify:
    
    \b
    • Frameworks (Bootstrap, React, WordPress, etc.)
    • Repeated elements (likely data items)  
    • Page structure and metadata
    • Extraction suggestions
    
    \b
    Examples:
      foundry probe https://news.ycombinator.com
      foundry probe --file page.html --format json
      foundry probe https://github.com --output analysis.json
      foundry probe --find-api  # Guide for infinite scroll sites
    """
    
    # Show API finding guide if requested
    if find_api:
        from .api_guide import show_api_guide
        show_api_guide()
        return
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
        click.echo("Error: Provide a URL or use --file option", err=True)
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


if __name__ == "__main__":
    probe()
