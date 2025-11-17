"""
Quarry - Modern Web Data Extraction Suite

Tools:
  run        Execute job YAMLs with the classic pipeline
  scout      Analyze HTML structure and detect patterns
  survey     Design extraction schemas interactively
  excavate   Execute extraction at scale
  polish     Clean, validate, and enrich data
  ship       Package and export data anywhere
"""

import os
import sys

import click
from rich.console import Console

from quarry.core import load_yaml, run_job
from quarry.lib.logging import setup_logging
from quarry.tools.excavate.cli import excavate as excavate_command
from quarry.tools.polish.cli import polish as polish_command
from quarry.tools.scout.cli import scout as scout_command
from quarry.tools.ship.cli import ship as ship_command
from quarry.tools.survey.cli import survey as survey_command
from quarry.wizard import run_wizard

BANNER = """
[cyan] ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗ ██╗   ██╗[/cyan]
[cyan]██╔═══██╗██║   ██║██╔══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝[/cyan]
[bright_cyan]██║   ██║██║   ██║███████║██████╔╝██████╔╝ ╚████╔╝ [/bright_cyan]
[bright_cyan]██║▄▄ ██║██║   ██║██╔══██║██╔══██╗██╔══██╗  ╚██╔╝  [/bright_cyan]
[blue]╚██████╔╝╚██████╔╝██║  ██║██║  ██║██║  ██║   ██║   [/blue]
[blue] ╚══▀▀═╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   [/blue]
[dim]           Web Data Extraction Suite v2.0[/dim]
"""


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version="2.0.0", prog_name="quarry")
def quarry(ctx):
    """
    Quarry - Web Data Extraction Suite

    A straightforward toolkit for analyzing, extracting, and exporting web data.

    \b
    Tools:
      • scout      - Analyze HTML and detect patterns
      • survey     - Design extraction schemas
      • excavate   - Execute extraction at scale
      • polish     - Transform and enrich data
      • ship       - Export data anywhere

    \b
    Examples:
      quarry scout https://example.com
      quarry survey schema.yml --preview
      quarry excavate schema.yml --output data.jsonl
      quarry polish data.jsonl --dedupe
      quarry ship data.jsonl postgres://localhost/db
    """
    # Initialize logging per env (non-disruptive to rich/click output)
    setup_logging()
    if ctx.invoked_subcommand is None:
        console = Console()
        console.print(BANNER)
        console.print()
        console.print(
            "[dim]A straightforward toolkit for analyzing, extracting, and exporting web data."
            "[/dim]"
        )
        console.print()
        console.print(
            "Available tools: [cyan]run[/cyan] | [cyan]scout[/cyan] | [cyan]survey[/cyan] | "
            "[cyan]excavate[/cyan] | [cyan]polish[/cyan] | [cyan]ship[/cyan]"
        )
        console.print()
        console.print("Run [yellow]quarry --help[/yellow] to see all commands and options.")
        console.print("Run [yellow]quarry <tool> --help[/yellow] for tool-specific help.")
        console.print()
        ctx.exit()


# Add tool commands
quarry.add_command(scout_command, name="scout")
quarry.add_command(survey_command, name="survey")
quarry.add_command(excavate_command, name="excavate")
quarry.add_command(polish_command, name="polish")
quarry.add_command(ship_command, name="ship")


@quarry.command()
@click.argument("job_file", type=click.Path(exists=True))
@click.option(
    "--max-items", type=int, default=200, show_default=True, help="Maximum items to collect"
)
@click.option(
    "--live/--offline", default=False, help="Use live network requests instead of fixtures"
)
@click.option("--db-path", type=click.Path(), help="SQLite state database location")
@click.option(
    "--timezone", default="America/New_York", show_default=True, help="Timezone for sink paths"
)
@click.option("--interactive", is_flag=True, help="Prompt before bypassing robots.txt blocks")
@click.option("--ignore-robots", is_flag=True, help="Ignore robots.txt (testing only)")
def run(job_file, max_items, live, db_path, timezone, interactive, ignore_robots):
    """Execute a job YAML through the classic pipeline."""

    previous_interactive = os.environ.get("QUARRY_INTERACTIVE")
    previous_ignore = os.environ.get("QUARRY_IGNORE_ROBOTS")

    try:
        if interactive:
            os.environ["QUARRY_INTERACTIVE"] = "1"
        elif previous_interactive is None:
            os.environ.pop("QUARRY_INTERACTIVE", None)

        if ignore_robots:
            os.environ["QUARRY_IGNORE_ROBOTS"] = "1"
        elif previous_ignore is None:
            os.environ.pop("QUARRY_IGNORE_ROBOTS", None)

        try:
            job_dict = load_yaml(job_file)
        except Exception as exc:
            click.echo(f"❌ Failed to load job: {exc}", err=True)
            sys.exit(1)

        try:
            dataframe, next_cursor = run_job(
                job_dict,
                max_items=max_items,
                offline=not live,
                db_path=db_path,
                timezone=timezone,
            )
        except Exception as exc:
            click.echo(f"❌ Job execution failed: {exc}", err=True)
            sys.exit(1)

    finally:
        if previous_interactive is not None:
            os.environ["QUARRY_INTERACTIVE"] = previous_interactive
        else:
            os.environ.pop("QUARRY_INTERACTIVE", None)

        if previous_ignore is not None:
            os.environ["QUARRY_IGNORE_ROBOTS"] = previous_ignore
        else:
            os.environ.pop("QUARRY_IGNORE_ROBOTS", None)

    record_count = len(dataframe) if dataframe is not None else 0
    click.echo(f"✅ Completed job '{job_dict.get('job', job_file)}' with {record_count} records")

    if next_cursor:
        click.echo(f"↪ Next cursor: {next_cursor}")


@quarry.command()
def init():
    """
    Launch interactive wizard to create extraction jobs.

    The wizard guides you through:
    • Job name and configuration
    • Source URL and parser selection
    • Framework detection (WordPress, React, etc.)
    • Field mapping and selectors
    • Output format (Parquet/CSV/JSONL)

    \b
    Example:
      quarry init
      → Creates jobs/<name>.yml
    """
    try:
        run_wizard()
    except KeyboardInterrupt:
        click.echo("\n[yellow]Cancelled[/yellow]")
        sys.exit(1)
    except Exception as e:
        click.echo(f"[red]Error: {e}[/red]", err=True)
        sys.exit(1)


def main():
    """Entry point for the quarry command."""
    quarry()


if __name__ == "__main__":
    main()
