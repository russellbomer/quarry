"""
Quarry - Modern Web Data Extraction Suite

Tools:
  scout      Analyze HTML structure and detect patterns
  survey     Design extraction schemas interactively  
  excavate   Execute extraction at scale
  polish     Clean, validate, and enrich data
  ship       Package and export data anywhere
"""

import click

from quarry.tools.scout.cli import scout as scout_command
from quarry.tools.survey.cli import survey as survey_command
from quarry.tools.excavate.cli import excavate as excavate_command
from quarry.tools.polish.cli import polish as polish_command
from quarry.tools.ship.cli import ship as ship_command


@click.group()
@click.version_option(version="2.0.0", prog_name="quarry")
def quarry():
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
    pass


# Add tool commands
quarry.add_command(scout_command, name="scout")
quarry.add_command(survey_command, name="survey")
quarry.add_command(excavate_command, name="excavate")
quarry.add_command(polish_command, name="polish")
quarry.add_command(ship_command, name="ship")


def main():
    """Entry point for the quarry command."""
    quarry()


if __name__ == "__main__":
    main()

