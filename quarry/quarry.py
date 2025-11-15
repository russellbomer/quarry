"""
Quarry - Modern Web Data Extraction Suite

Tools:
  scout      Analyze HTML structure and detect patterns
  survey     Design extraction schemas interactively  
  excavate   Execute extraction at scale
  polish     Clean, validate, and enrich data
  ship       Package and export data anywhere
"""

import sys

import click
from rich.console import Console

from quarry.tools.scout.cli import scout as scout_command
from quarry.tools.survey.cli import survey as survey_command
from quarry.tools.excavate.cli import excavate as excavate_command
from quarry.tools.polish.cli import polish as polish_command
from quarry.tools.ship.cli import ship as ship_command
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
    
    A modern toolkit for analyzing, extracting, and exporting web data.
    
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
    if ctx.invoked_subcommand is None:
        console = Console()
        console.print(BANNER)
        console.print()  # Add blank line
        console.print("[dim]A modern toolkit for analyzing, extracting, and exporting web data.[/dim]")
        console.print()
        console.print("Available tools: [cyan]scout[/cyan] | [cyan]survey[/cyan] | [cyan]excavate[/cyan] | [cyan]polish[/cyan] | [cyan]ship[/cyan]")
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

