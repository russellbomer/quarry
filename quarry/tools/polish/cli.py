"""CLI for Polish tool."""

import sys
import click
import questionary
from pathlib import Path

from quarry.lib.session import get_last_output, set_last_output
from .processor import PolishProcessor


@click.command()
@click.argument("input_file", type=click.Path(exists=True), required=False)
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Output file path (default: input_polished.jsonl)"
)
@click.option(
    "--dedupe/--no-dedupe",
    default=None,
    help="Remove duplicate records"
)
@click.option(
    "--dedupe-keys",
    multiple=True,
    help="Fields to use for deduplication (can specify multiple)"
)
@click.option(
    "--dedupe-strategy",
    type=click.Choice(["first", "last"]),
    default="first",
    help="Keep first or last occurrence of duplicates"
)
@click.option(
    "--transform",
    multiple=True,
    help="Apply transformation: field:transform_name (e.g., url:extract_domain)"
)
@click.option(
    "--skip-invalid",
    is_flag=True,
    help="Skip records that fail validation"
)
@click.option(
    "--stats",
    is_flag=True,
    help="Show detailed statistics"
)
@click.option(
    "--batch/--interactive",
    "batch_mode",
    default=False,
    help="Batch mode (skip prompts, fail if arguments missing)"
)
def polish(input_file, output, dedupe, dedupe_keys, dedupe_strategy, transform, skip_invalid, stats, batch_mode):
    """
    Transform and enrich extracted data.
    
    POLISH cleans, deduplicates, validates, and enriches data from JSONL files.
    It's designed to work with output from the excavate tool.
    
    \b
    Interactive Mode (default):
      quarry polish
      → Prompts for input file and operations
    
    \b
    Batch Mode (with arguments):
      quarry polish data.jsonl --dedupe
      quarry polish data.jsonl --dedupe-keys title link --batch
      quarry polish data.jsonl --transform url:extract_domain
      quarry polish data.jsonl --dedupe --skip-invalid --output clean.jsonl
    """
    
    # Show helpful error if called without required argument
    if not input_file and not sys.stdin.isatty():
        # Non-interactive terminal (piped/scripted), show error
        click.echo("❌ Error: No input file specified", err=True)
        click.echo("", err=True)
        click.echo("Usage: quarry polish INPUT_FILE [OPTIONS]", err=True)
        click.echo("", err=True)
        click.echo("Examples:", err=True)
        click.echo("  quarry polish data.jsonl --dedupe", err=True)
        click.echo("  quarry polish data.jsonl --dedupe-keys title url", err=True)
        click.echo("  quarry polish  # Interactive mode", err=True)
        click.echo("", err=True)
        click.echo("Run 'quarry polish --help' for full options.", err=True)
        sys.exit(1)
    
    if not input_file and batch_mode:
        # Batch mode without input, show error
        click.echo("❌ Error: No input file specified", err=True)
        click.echo("", err=True)
        click.echo("Usage: quarry polish INPUT_FILE [OPTIONS]", err=True)
        click.echo("", err=True)
        click.echo("Examples:", err=True)
        click.echo("  quarry polish data.jsonl --dedupe", err=True)
        click.echo("  quarry polish data.jsonl --dedupe-keys title url", err=True)
        click.echo("  quarry polish  # Interactive mode", err=True)
        click.echo("", err=True)
        click.echo("Run 'quarry polish --help' for full options.", err=True)
        sys.exit(1)
    
    # Interactive mode: prompt for missing values
    if not batch_mode and not input_file:
        click.echo("✨ Quarry Polish - Interactive Mode\n", err=True)
        
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
                input_file = questionary.path(
                    "Input file (JSONL):",
                    validate=lambda x: Path(x).exists() or "File does not exist"
                ).ask()
                
                if not input_file:
                    click.echo("Cancelled", err=True)
                    sys.exit(0)
        except (KeyboardInterrupt, EOFError):
            # Interactive mode failed, show helpful error
            click.echo("\n", err=True)
            click.echo("❌ Interactive mode cancelled or unavailable", err=True)
            click.echo("", err=True)
            click.echo("Usage: quarry polish INPUT_FILE [OPTIONS]", err=True)
            click.echo("", err=True)
            click.echo("Examples:", err=True)
            click.echo("  quarry polish data.jsonl --dedupe", err=True)
            click.echo("  quarry polish data.jsonl --dedupe-keys title url", err=True)
            click.echo("", err=True)
            click.echo("Run 'quarry polish --help' for full options.", err=True)
            sys.exit(1)
        
        # Ask what operations to perform
        operations = questionary.checkbox(
            "Select operations:",
            choices=[
                "Deduplicate records",
                "Transform fields",
                "Skip invalid records",
                "Show detailed statistics"
            ]
        ).ask()
        
        if not operations:
            click.echo("No operations selected, exiting", err=True)
            sys.exit(0)
        
        # Set flags based on selections
        dedupe = "Deduplicate records" in operations
        skip_invalid = "Skip invalid records" in operations
        stats = "Show detailed statistics" in operations
        
        # If deduplication selected, ask for keys
        if dedupe:
            dedupe_keys_input = questionary.text(
                "Dedupe keys (space-separated, or leave empty for all fields):",
                default=""
            ).ask()
            
            if dedupe_keys_input:
                dedupe_keys = tuple(dedupe_keys_input.split())
            else:
                dedupe_keys = ()
        
        # If transform selected, ask for transformations
        if "Transform fields" in operations:
            transform_list = []
            add_more = True
            
            while add_more:
                field = questionary.text(
                    "Field to transform:",
                    validate=lambda x: len(x) > 0 or "Field name required"
                ).ask()
                
                if not field:
                    break
                
                transform_name = questionary.select(
                    f"Transformation for '{field}':",
                    choices=[
                        "normalize_text",
                        "extract_domain",
                        "uppercase",
                        "lowercase",
                        "strip_html",
                        "parse_date"
                    ]
                ).ask()
                
                if transform_name:
                    transform_list.append(f"{field}:{transform_name}")
                
                add_more = questionary.confirm(
                    "Add another transformation?",
                    default=False
                ).ask()
                
                if not add_more:
                    break
            
            transform = tuple(transform_list) if transform_list else ()
        
        # Prompt for output
        if not output:
            input_path = Path(input_file)
            default_output = str(input_path.parent / f"{input_path.stem}_polished{input_path.suffix}")
            output = questionary.text(
                "Output file:",
                default=default_output
            ).ask()
    
    # Final validation - should not reach here in normal flow
    if not input_file:
        click.echo("❌ Error: No input file specified", err=True)
        sys.exit(1)
    
    # Set dedupe to False if still None
    if dedupe is None:
        dedupe = False
    
    # Determine output file
    if not output:
        input_path = Path(input_file)
        output = input_path.parent / f"{input_path.stem}_polished{input_path.suffix}"
    
    click.echo(f"📋 Processing {input_file}...", err=True)
    
    # Parse transformations
    transformations = {}
    if transform:
        for t in transform:
            if ":" not in t:
                click.echo(f"⚠️  Invalid transformation format: {t} (expected field:transform)", err=True)
                continue
            
            field, transform_name = t.split(":", 1)
            if field not in transformations:
                transformations[field] = []
            transformations[field].append({"transform": transform_name})
    
    # Convert dedupe_keys tuple to list
    dedupe_key_list = list(dedupe_keys) if dedupe_keys else None
    
    # Create processor
    processor = PolishProcessor()
    
    try:
        # Process data
        result_stats = processor.process(
            input_file=input_file,
            output_file=output,
            deduplicate=dedupe,
            dedupe_keys=dedupe_key_list,
            dedupe_strategy=dedupe_strategy,
            transformations=transformations if transformations else None,
            skip_invalid=skip_invalid,
        )
        
        # Report results
        click.echo(f"✅ Wrote {result_stats['records_written']} records to {output}", err=True)
        
        # Store in session for potential chaining
        set_last_output(output, "jsonl", result_stats['records_written'])
        
        if stats or dedupe or skip_invalid:
            click.echo("\n📊 Statistics:", err=True)
            click.echo(f"   Records read: {result_stats['records_read']}", err=True)
            click.echo(f"   Records written: {result_stats['records_written']}", err=True)
            
            if result_stats['records_skipped'] > 0:
                click.echo(f"   Records skipped: {result_stats['records_skipped']}", err=True)
            
            if dedupe and result_stats['duplicates_removed'] > 0:
                click.echo(f"   Duplicates removed: {result_stats['duplicates_removed']}", err=True)
            
            if result_stats['validation_errors'] > 0:
                click.echo(f"   Validation errors: {result_stats['validation_errors']}", err=True)
        
        # Offer to run ship next
        if not batch_mode:
            click.echo("", err=True)
            if click.confirm("🔗 Run ship now to export this data?", default=False):
                click.echo("", err=True)
                click.echo("Starting ship...", err=True)
                click.echo("─" * 50, err=True)
                
                # Import here to avoid circular dependency
                from quarry.tools.ship.cli import ship
                
                # Invoke ship command directly
                ctx = click.get_current_context()
                ctx.invoke(ship,
                          input_file=output,
                          destination=None,
                          table=None,
                          if_exists="replace",
                          delimiter=",",
                          pretty=False,
                          exclude_meta=True,
                          stats=False,
                          batch_mode=False)
    
    except Exception as e:
        click.echo(f"❌ Processing failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    polish()
