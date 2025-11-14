"""CLI interface for Blueprint tool."""

import sys
from pathlib import Path

import click
import questionary

from quarry.lib.http import get_html
from quarry.lib.schemas import load_schema, save_schema
from quarry.lib.session import set_last_schema
from quarry.lib.prompts import prompt_text, prompt_choice, prompt_confirm
from .builder import build_schema_interactive, load_analysis_from_file
from .preview import preview_extraction, format_preview
from .job_generator import generate_job_yaml, save_job_yaml


@click.group()
def survey():
    """Design extraction schemas interactively."""
    pass


@survey.command("create")
@click.option(
    "--from-probe", "-p",
    type=click.Path(exists=True),
    help="Use Probe analysis JSON as starting point"
)
@click.option(
    "--url", "-u",
    help="Target URL to analyze"
)
@click.option(
    "--file", "-f",
    type=click.Path(exists=True),
    help="HTML file to analyze"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="schema.yml",
    help="Output file (default: schema.yml)"
)
@click.option(
    "--preview/--no-preview",
    default=True,
    help="Preview extraction before saving (default: yes)"
)
@click.option(
    "--job",
    is_flag=True,
    help="Generate job YAML (for 'quarry run') instead of schema"
)
@click.option(
    "--job-name",
    help="Job name (required with --job)"
)
@click.option(
    "--sink-kind",
    type=click.Choice(["parquet", "csv", "jsonl"]),
    default="parquet",
    help="Output format for job (default: parquet)"
)
def create(from_probe, url, file, output, preview, job, job_name, sink_kind):
    """
    Create a new extraction schema or job YAML interactively.
    
    \b
    Schema mode (default):
      quarry survey create
      quarry survey create --url https://example.com
      quarry survey create --from-probe analysis.json
      → Creates schema.yml for use with 'quarry excavate'
    
    \b
    Job mode (--job flag):
      quarry survey create --job --job-name my_scraper
      quarry survey create --job --job-name blog --url https://blog.com
      → Creates jobs/my_scraper.yml for use with 'quarry run'
    """
    # Validate job mode requirements
    if job and not job_name:
        # Prompt for job name
        job_name = prompt_text(
            "Job name:",
            validator=lambda x: (bool(x), "Job name is required") if x else (False, "Job name is required"),
            allow_cancel=False
        )
    
    # Set default output for job mode
    if job and output == "schema.yml":
        output = f"jobs/{job_name}.yml"
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
    
    # Save schema or job
    try:
        if job:
            # Generate and save job YAML
            click.echo(f"\n📦 Generating job YAML...", err=True)
            
            # Extract domain for allowlist
            from urllib.parse import urlparse
            allowlist = []
            if schema.url:
                domain = urlparse(schema.url).netloc
                allowlist = [domain]
            
            # Generate job spec
            job_spec = generate_job_yaml(
                schema=schema,
                job_name=job_name,
                output_path=f"data/cache/{job_name}/%Y%m%dT%H%M%SZ.{sink_kind}",
                sink_kind=sink_kind,
                rate_limit=1.0,
                cursor_field="url",
                allowlist=allowlist,
            )
            
            # Save job file
            save_job_yaml(job_spec, output)
            click.echo(f"\n✅ Job saved to: {output}", err=True)
            click.echo(f"\nRun with: quarry run {output}", err=True)
        else:
            # Save schema file
            save_schema(schema, output)
            click.echo(f"\n✅ Schema saved to: {output}", err=True)
            
            # Store in session for potential chaining
            set_last_schema(output, schema.url)
            
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
                ctx.invoke(excavate,
                          schema_file=str(output),
                          url=schema.url,
                          file=None,
                          output="output.jsonl",
                          max_pages=None,
                          no_metadata=False,
                          pretty=False,
                          batch_mode=False)
            
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
        click.echo(f"\n✅ Schema is valid!", err=True)
        click.echo(f"   Name: {schema.name}", err=True)
        click.echo(f"   Item selector: {schema.item_selector}", err=True)
        click.echo(f"   Fields: {len(schema.fields)}", err=True)
        
        if schema.pagination:
            click.echo(f"   Pagination: enabled", err=True)
        
    except Exception as e:
        click.echo(f"\n❌ Validation failed:", err=True)
        click.echo(f"   {e}", err=True)
        sys.exit(1)


@survey.command("preview")
@click.argument("schema_file", type=click.Path(exists=True))
@click.option(
    "--url", "-u",
    help="URL to extract from"
)
@click.option(
    "--file", "-f",
    type=click.Path(exists=True),
    help="HTML file to extract from"
)
@click.option(
    "--limit", "-n",
    type=int,
    default=5,
    help="Max items to show (default: 5)"
)
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


@survey.command("to-job")
@click.argument("schema_file", type=click.Path(exists=True))
@click.option(
    "--job-name", "-n",
    required=True,
    help="Name for the job"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Output job file (default: jobs/{job_name}.yml)"
)
@click.option(
    "--sink-kind",
    type=click.Choice(["parquet", "csv", "jsonl"]),
    default="parquet",
    help="Output format (default: parquet)"
)
@click.option(
    "--cursor-field",
    default="url",
    help="Field to use for deduplication (default: url)"
)
@click.option(
    "--rate-limit",
    type=float,
    default=1.0,
    help="Requests per second (default: 1.0)"
)
def to_job(schema_file, job_name, output, sink_kind, cursor_field, rate_limit):
    """
    Convert an extraction schema to a job YAML.
    
    \b
    Examples:
      quarry survey to-job schema.yml --job-name my_scraper
      quarry survey to-job schema.yml -n blog --sink-kind csv
    
    This is useful when you already have a schema from 'survey create'
    and want to generate a job file for 'quarry run'.
    """
    # Set default output
    if not output:
        output = f"jobs/{job_name}.yml"
    
    # Load schema
    click.echo(f"📋 Loading schema from {schema_file}...", err=True)
    try:
        schema = load_schema(schema_file)
    except Exception as e:
        click.echo(f"Error loading schema: {e}", err=True)
        sys.exit(1)
    
    # Extract domain for allowlist
    from urllib.parse import urlparse
    allowlist = []
    if schema.url:
        domain = urlparse(schema.url).netloc
        allowlist = [domain]
        click.echo(f"📍 Using URL: {schema.url}", err=True)
        click.echo(f"   Allowlist: {domain}", err=True)
    
    # Generate job spec
    click.echo(f"\n📦 Generating job YAML...", err=True)
    try:
        job_spec = generate_job_yaml(
            schema=schema,
            job_name=job_name,
            output_path=f"data/cache/{job_name}/%Y%m%dT%H%M%SZ.{sink_kind}",
            sink_kind=sink_kind,
            rate_limit=rate_limit,
            cursor_field=cursor_field,
            allowlist=allowlist,
        )
    except Exception as e:
        click.echo(f"Error generating job: {e}", err=True)
        sys.exit(1)
    
    # Save job file
    try:
        save_job_yaml(job_spec, output)
        click.echo(f"\n✅ Job saved to: {output}", err=True)
        click.echo(f"\nRun with: quarry run {output}", err=True)
    except Exception as e:
        click.echo(f"Error saving job: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    blueprint()
