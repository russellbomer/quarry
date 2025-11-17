"""Interactive prompt utilities with retry logic."""

import sys
from collections.abc import Callable
from pathlib import Path
from typing import cast

import click
import questionary


class RetryablePrompt:
    """Wrapper for prompts that allows retrying on validation failures."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def ask_with_retry(
        self,
        prompt_fn: Callable[[], str | None],
        validator: Callable[[str], tuple[bool, str | None]] | None = None,
        allow_cancel: bool = True,
    ) -> str | None:
        """
        Ask a question with retry logic on validation failure.

        Args:
            prompt_fn: Function that prompts and returns user input
            validator: Optional function that returns (is_valid, error_message)
            allow_cancel: If True, user can cancel; if False, must retry

        Returns:
            User input if valid, None if cancelled (when allow_cancel=True)
        """
        attempts = 0

        while attempts < self.max_retries:
            try:
                answer = prompt_fn()

                # User cancelled
                if answer is None:
                    if allow_cancel:
                        return None
                    else:
                        click.echo("⚠️  Input required. Please try again.", err=True)
                        attempts += 1
                        continue

                # Validate if validator provided
                if validator:
                    is_valid, error_msg = validator(answer)
                    if not is_valid:
                        click.echo(f"❌ {error_msg}", err=True)

                        if attempts < self.max_retries - 1:
                            retry = questionary.confirm("Try again?", default=True).ask()

                            if not retry:
                                if allow_cancel:
                                    return None
                                else:
                                    click.echo("⚠️  Input required.", err=True)

                        attempts += 1
                        continue

                return answer

            except (KeyboardInterrupt, EOFError):
                if allow_cancel:
                    click.echo("\nCancelled", err=True)
                    return None
                else:
                    click.echo("\n⚠️  Input required. Please try again.", err=True)
                    attempts += 1

        # Max retries reached
        if allow_cancel:
            click.echo(f"❌ Maximum attempts ({self.max_retries}) reached", err=True)
            return None
        else:
            click.echo(f"❌ Maximum attempts ({self.max_retries}) reached. Exiting.", err=True)
            sys.exit(1)


def prompt_url(message: str = "Enter URL:", allow_cancel: bool = True) -> str | None:
    """
    Prompt for a URL with validation and retry logic.

    Args:
        message: Prompt message
        allow_cancel: Whether user can cancel

    Returns:
        Valid URL or None if cancelled
    """

    def validate_url(url: str) -> tuple[bool, str | None]:
        if not url:
            return False, "URL cannot be empty"
        if not (url.startswith("http://") or url.startswith("https://")):
            return False, "URL must start with http:// or https://"
        return True, None

    prompter = RetryablePrompt()

    return prompter.ask_with_retry(
        lambda: questionary.text(message).ask(), validator=validate_url, allow_cancel=allow_cancel
    )


def prompt_file(message: str = "Enter file path:", allow_cancel: bool = True) -> str | None:
    """
    Prompt for a file path with validation and retry logic.

    Args:
        message: Prompt message
        allow_cancel: Whether user can cancel

    Returns:
        Valid file path or None if cancelled
    """

    def validate_file(filepath: str) -> tuple[bool, str | None]:
        if not filepath:
            return False, "File path cannot be empty"

        path = Path(filepath)
        if not path.exists():
            return False, f"File not found: {filepath}"
        if not path.is_file():
            return False, f"Not a file: {filepath}"

        return True, None

    prompter = RetryablePrompt()

    return prompter.ask_with_retry(
        lambda: questionary.path(message).ask(), validator=validate_file, allow_cancel=allow_cancel
    )


def prompt_choice(message: str, choices: list[str], allow_cancel: bool = True) -> str | None:
    """
    Prompt for a choice from a list with retry logic.

    Args:
        message: Prompt message
        choices: List of choices
        allow_cancel: Whether user can cancel

    Returns:
        Selected choice or None if cancelled
    """
    prompter = RetryablePrompt()

    return prompter.ask_with_retry(
        lambda: questionary.select(message, choices=choices).ask(), allow_cancel=allow_cancel
    )


def prompt_text(
    message: str,
    default: str | None = None,
    validator: Callable[[str], tuple[bool, str | None]] | None = None,
    allow_cancel: bool = True,
) -> str | None:
    """
    Prompt for text input with validation and retry logic.

    Args:
        message: Prompt message
        default: Default value
        validator: Optional validation function
        allow_cancel: Whether user can cancel

    Returns:
        User input or None if cancelled
    """
    prompter = RetryablePrompt()

    def ask():
        if default:
            return questionary.text(message, default=default).ask()
        return questionary.text(message).ask()

    return prompter.ask_with_retry(ask, validator=validator, allow_cancel=allow_cancel)


def prompt_confirm(message: str, default: bool = True, allow_cancel: bool = False) -> bool | None:
    """
    Prompt for yes/no confirmation.

    Args:
        message: Prompt message
        default: Default value
        allow_cancel: Whether user can cancel (returns None)

    Returns:
        True/False for yes/no, or None if cancelled (when allow_cancel=True)
    """
    try:
        result = cast(bool | None, questionary.confirm(message, default=default).ask())
        if result is None and not allow_cancel:
            return default
        return result
    except (KeyboardInterrupt, EOFError):
        if allow_cancel:
            return None
        return default
