"""CLI for Polish tool."""

import sys
from pathlib import Path
from typing import Any, Literal, cast

import click
import questionary

from quarry.lib.session import get_last_output, set_last_output

from .processor import PolishProcessor


@click.command()
@click.argument("input_file", type=click.Path(exists=True), required=False)
@click.option(
    "--output", "-o", type=click.Path(), help="Output file path (default: input_polished.jsonl)"
)
@click.option("--dedupe/--no-dedupe", default=None, help="Remove duplicate records")
@click.option(
    "--dedupe-keys", multiple=True, help="Fields to use for deduplication (can specify multiple)"
)
@click.option(
    "--dedupe-strategy",
    type=click.Choice(["first", "last"]),
    default="first",
    help="Keep first or last occurrence of duplicates",
)
@click.option(
    "--transform",
    multiple=True,
    help="Apply transformation: field:transform_name (e.g., url:extract_domain)",
)
@click.option("--skip-invalid", is_flag=True, help="Skip records that fail validation")
@click.option("--stats", is_flag=True, help="Show detailed statistics")
@click.option(
    "--batch/--interactive",
    "batch_mode",
    default=False,
    help="Batch mode (skip prompts, fail if arguments missing)",
)
def polish(
    input_file,
    output,
    dedupe,
    dedupe_keys,
    dedupe_strategy,
    transform,
    skip_invalid,
    stats,
    batch_mode,
):
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
    # Initialize validation_rules (may be populated in interactive mode)
    validation_rules: dict[str, dict[str, Any]] = {}

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
                    validate=lambda x: Path(x).exists() or "File does not exist",
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
                questionary.Choice("Deduplicate records", checked=False),
                questionary.Choice("Transform fields", checked=False),
                questionary.Choice("Validate fields", checked=False),
                questionary.Choice("Skip invalid records", checked=False),
                questionary.Choice("Show detailed statistics", checked=True),
            ],
        ).ask()

        if not operations:
            click.echo("No operations selected, exiting", err=True)
            sys.exit(0)

        # Set flags based on selections
        dedupe = "Deduplicate records" in operations
        skip_invalid = "Skip invalid records" in operations
        stats = "Show detailed statistics" in operations

        # Try to read field names from the input file for better UX
        available_fields: list[str] = []
        try:
            import json

            with open(input_file, encoding="utf-8") as f:
                first_line = f.readline().strip()
                if first_line:
                    sample = json.loads(first_line)
                    # Exclude _meta field from suggestions
                    available_fields = [k for k in sample.keys() if not k.startswith("_")]
        except Exception:
            pass  # Fall back to manual entry

        # If deduplication selected, ask for keys
        if dedupe:
            if available_fields:
                click.echo(f"\n📋 Available fields: {', '.join(available_fields)}", err=True)
                dedupe_choice = questionary.select(
                    "How to select dedupe keys?",
                    choices=[
                        questionary.Choice("Select from available fields", value="select"),
                        questionary.Choice("Use all fields (full record comparison)", value="all"),
                        questionary.Choice("Enter field names manually", value="manual"),
                    ],
                ).ask()

                if dedupe_choice == "select":
                    selected_keys = questionary.checkbox(
                        "Select fields for deduplication:",
                        choices=available_fields,
                    ).ask()
                    dedupe_keys = tuple(selected_keys) if selected_keys else ()
                elif dedupe_choice == "all":
                    dedupe_keys = ()
                else:  # manual
                    dedupe_keys_input = questionary.text(
                        "Dedupe keys (space-separated):", default=""
                    ).ask()
                    dedupe_keys = tuple(dedupe_keys_input.split()) if dedupe_keys_input else ()
            else:
                dedupe_keys_input = questionary.text(
                    "Dedupe keys (space-separated, or leave empty for all fields):", default=""
                ).ask()
                dedupe_keys = tuple(dedupe_keys_input.split()) if dedupe_keys_input else ()

            # Ask for strategy
            dedupe_strategy = (
                questionary.select(
                    "Which duplicate to keep?",
                    choices=[
                        questionary.Choice("Keep first occurrence", value="first"),
                        questionary.Choice("Keep last occurrence", value="last"),
                    ],
                ).ask()
                or "first"
            )

        # If transform selected, ask for transformations
        if "Transform fields" in operations:
            transform_list = []
            add_more = True

            # Show available transforms with descriptions
            click.echo("\n📋 Available transformations:", err=True)
            click.echo("   normalize_text    - Clean whitespace, standardize text", err=True)
            click.echo("   clean_whitespace  - Remove extra spaces only", err=True)
            click.echo("   uppercase         - Convert to UPPERCASE", err=True)
            click.echo("   lowercase         - Convert to lowercase", err=True)
            click.echo("   extract_domain    - Get domain from URL", err=True)
            click.echo("   parse_date        - Normalize date to YYYY-MM-DD", err=True)
            click.echo("   strip_html        - Remove HTML tags", err=True)
            click.echo("   truncate_text     - Limit text length (100 chars)", err=True)
            click.echo("", err=True)

            while add_more:
                field = questionary.text(
                    "Field to transform (or Enter to finish):",
                    default="",
                ).ask()

                if not field:
                    break

                transform_name = questionary.select(
                    f"Transformation for '{field}':",
                    choices=[
                        questionary.Choice(
                            "normalize_text - Clean whitespace", value="normalize_text"
                        ),
                        questionary.Choice(
                            "clean_whitespace - Remove extra spaces", value="clean_whitespace"
                        ),
                        questionary.Choice("uppercase - Convert to UPPERCASE", value="uppercase"),
                        questionary.Choice("lowercase - Convert to lowercase", value="lowercase"),
                        questionary.Choice(
                            "extract_domain - Get domain from URL", value="extract_domain"
                        ),
                        questionary.Choice(
                            "parse_date - Normalize to YYYY-MM-DD", value="parse_date"
                        ),
                        questionary.Choice("strip_html - Remove HTML tags", value="strip_html"),
                        questionary.Choice(
                            "truncate_text - Limit to 100 chars", value="truncate_text"
                        ),
                    ],
                ).ask()

                if transform_name:
                    transform_list.append(f"{field}:{transform_name}")
                    click.echo(f"   ✓ Added: {field} → {transform_name}", err=True)

                add_more = questionary.confirm("Add another transformation?", default=False).ask()

                if not add_more:
                    break

            transform = tuple(transform_list) if transform_list else ()

        # If validate selected, ask for validation rules
        if "Validate fields" in operations:
            click.echo("\n🔍 Configure validation rules:", err=True)
            add_more = True

            while add_more:
                if available_fields:
                    field = questionary.select(
                        "Field to validate (or select 'Done'):",
                        choices=[*available_fields, "[Done - finish validation setup]"],
                    ).ask()
                    if field == "[Done - finish validation setup]":
                        break
                else:
                    field = questionary.text(
                        "Field to validate (or Enter to finish):",
                        default="",
                    ).ask()
                    if not field:
                        break

                # Select validation type
                validation_type = questionary.select(
                    f"Validation for '{field}':",
                    choices=[
                        questionary.Choice("Required - must not be empty", value="required"),
                        questionary.Choice("Email - valid email format", value="email"),
                        questionary.Choice("URL - valid URL format", value="url"),
                        questionary.Choice("Date - YYYY-MM-DD format", value="date"),
                        questionary.Choice("Min length - minimum characters", value="min_length"),
                        questionary.Choice("Max length - maximum characters", value="max_length"),
                    ],
                ).ask()

                if validation_type:
                    if field not in validation_rules:
                        validation_rules[field] = {}

                    if validation_type == "required":
                        validation_rules[field]["required"] = True
                    elif validation_type in ("email", "url", "date"):
                        validation_rules[field]["type"] = validation_type
                    elif validation_type == "min_length":
                        min_val = questionary.text("Minimum length:", default="1").ask()
                        validation_rules[field]["min_length"] = int(min_val) if min_val else 1
                    elif validation_type == "max_length":
                        max_val = questionary.text("Maximum length:", default="255").ask()
                        validation_rules[field]["max_length"] = int(max_val) if max_val else 255

                    click.echo(f"   ✓ Added: {field} → {validation_type}", err=True)

                add_more = questionary.confirm("Add another validation rule?", default=False).ask()

                if not add_more:
                    break

        # Prompt for output
        if not output:
            input_path = Path(input_file)
            default_output = str(
                input_path.parent / f"{input_path.stem}_polished{input_path.suffix}"
            )
            output = questionary.text("Output file:", default=default_output).ask()

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
    transformations: dict[str, list[dict[str, Any]]] = {}
    if transform:
        for t in transform:
            if ":" not in t:
                click.echo(
                    f"⚠️  Invalid transformation format: {t} (expected field:transform)", err=True
                )
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
            dedupe_strategy=cast(Literal["first", "last"], dedupe_strategy),
            transformations=transformations if transformations else None,
            validation_rules=validation_rules if validation_rules else None,
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
                ctx.invoke(
                    ship,
                    input_file=output,
                    destination=None,
                    table=None,
                    if_exists="replace",
                    delimiter=",",
                    pretty=False,
                    exclude_meta=True,
                    stats=False,
                    batch_mode=False,
                )

    except Exception as e:
        click.echo(f"❌ Processing failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    polish()
