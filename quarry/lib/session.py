"""Session state management for chaining interactive tools.

This module provides a simple mechanism for tools to pass data to each other
in interactive workflows. For example, survey can create a schema and offer to
pass it directly to excavate.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_SESSION_FILE = Path.home() / ".quarry" / "session.json"


def _ensure_session_dir() -> None:
    """Create session directory if it doesn't exist."""
    _SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_session() -> dict[str, Any]:
    """Load session data from file."""
    if not _SESSION_FILE.exists():
        return {}
    
    try:
        with _SESSION_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_session(data: dict[str, Any]) -> None:
    """Save session data to file."""
    _ensure_session_dir()
    with _SESSION_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def set_last_schema(schema_path: str, url: str | None = None) -> None:
    """
    Store the most recently created/used schema.
    
    Args:
        schema_path: Path to the schema file
        url: Optional URL associated with the schema
    """
    session = _load_session()
    session["last_schema"] = {
        "path": str(Path(schema_path).absolute()),
        "url": url,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    _save_session(session)


def get_last_schema() -> dict[str, Any] | None:
    """
    Get the most recently created/used schema.
    
    Returns:
        Dict with keys: path, url, timestamp, or None if no schema stored
    """
    session = _load_session()
    return session.get("last_schema")


def set_last_output(output_path: str, format: str, record_count: int) -> None:
    """
    Store the most recently generated output file.
    
    Args:
        output_path: Path to the output file
        format: Format of the output (jsonl, csv, json, etc.)
        record_count: Number of records in the output
    """
    session = _load_session()
    session["last_output"] = {
        "path": str(Path(output_path).absolute()),
        "format": format,
        "record_count": record_count,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    _save_session(session)


def get_last_output() -> dict[str, Any] | None:
    """
    Get the most recently generated output file.
    
    Returns:
        Dict with keys: path, format, record_count, timestamp, or None
    """
    session = _load_session()
    return session.get("last_output")


def clear_session() -> None:
    """Clear all session data."""
    if _SESSION_FILE.exists():
        _SESSION_FILE.unlink()
