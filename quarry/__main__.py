"""Main entry point for running quarry as a module."""

from quarry.wizard import run_wizard

if __name__ == "__main__":
    # If called with 'python -m quarry' or 'python -m quarry.wizard'
    run_wizard()
