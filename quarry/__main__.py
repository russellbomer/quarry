"""Main entry point for running foundry as a module."""

from quarry.wizard import run_wizard

if __name__ == "__main__":
    # If called with 'python -m foundry' or 'python -m foundry.wizard'
    run_wizard()
