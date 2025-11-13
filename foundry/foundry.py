"""
Foundry - Modern Web Data Extraction Suite

Tools:
  probe      Analyze HTML structure and detect patterns
  blueprint  Design extraction schemas interactively  
  forge      Execute extraction at scale
  polish     Clean, validate, and enrich data
  crate      Package and export data anywhere
"""

import click

from foundry.tools.probe.cli import probe as probe_command
from foundry.tools.blueprint.cli import blueprint as blueprint_command
from foundry.tools.forge.cli import forge as forge_command
from foundry.tools.polish.cli import polish as polish_command
from foundry.tools.crate.cli import crate as crate_command


@click.group()
@click.version_option(version="2.0.0", prog_name="foundry")
def foundry():
    """
    Foundry - Web Data Extraction Suite
    
    A modern toolkit for analyzing, extracting, and exporting web data.
    
    \b
    Tools:
      • probe      - Analyze HTML and detect patterns
      • blueprint  - Design extraction schemas
      • forge      - Execute extraction at scale
      • polish     - Transform and enrich data
      • crate      - Export data anywhere
    
    \b
    Examples:
      foundry probe https://example.com
      foundry blueprint schema.yml --preview
      foundry forge schema.yml --output data.jsonl
      foundry polish data.jsonl --dedupe
      foundry crate data.jsonl postgres://localhost/db
    """
    pass


# Add tool commands
foundry.add_command(probe_command, name="probe")
foundry.add_command(blueprint_command, name="blueprint")
foundry.add_command(forge_command, name="forge")
foundry.add_command(polish_command, name="polish")
foundry.add_command(crate_command, name="crate")


def main():
    """Entry point for the foundry command."""
    foundry()


if __name__ == "__main__":
    main()
