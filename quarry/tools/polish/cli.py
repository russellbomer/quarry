"""CLI for Polish tool."""

import sys
import click
import questionary
from pathlib import Path

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
    It's designed to work with output from the Forge tool.
    
    \b
    Interactive Mode (default):
      foundry polish
      → Prompts for input file and operations
    
    \b
    Batch Mode (with arguments):
      foundry polish data.jsonl --dedupe
      foundry polish data.jsonl --dedupe-keys title link --batch
      foundry polish data.jsonl --transform url:extract_domain
      foundry polish data.jsonl --dedupe --skip-invalid --output clean.jsonl
    """
    
    # Interactive mode: prompt for missing values
    if not batch_mode and not input_file:
        click.echo("✨ Foundry Polish - Interactive Mode\n", err=True)
        
        # Prompt for input file
        input_file = questionary.path(
            "Input file (JSONL):",
            only_files=True,
            validate=lambda x: Path(x).exists() or "File does not exist"
        ).ask()
        
        if not input_file:
            click.echo("Cancelled", err=True)
            sys.exit(0)
        
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
    
    # Validate required input in batch mode
    if not input_file:
        click.echo("Error: No input file specified", err=True)
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
    
    except Exception as e:
        click.echo(f"❌ Processing failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    polish()
