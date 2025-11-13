"""CLI for Polish tool."""

import sys
import click
from pathlib import Path

from .processor import PolishProcessor


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Output file path (default: input_polished.jsonl)"
)
@click.option(
    "--dedupe/--no-dedupe",
    default=False,
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
def polish(input_file, output, dedupe, dedupe_keys, dedupe_strategy, transform, skip_invalid, stats):
    """
    Transform and enrich extracted data.
    
    POLISH cleans, deduplicates, validates, and enriches data from JSONL files.
    It's designed to work with output from the Forge tool.
    
    \b
    Examples:
      foundry polish data.jsonl --dedupe
      foundry polish data.jsonl --dedupe-keys title link
      foundry polish data.jsonl --transform url:extract_domain
      foundry polish data.jsonl --dedupe --skip-invalid --output clean.jsonl
    """
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
