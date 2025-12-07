"""Centralized filesystem helpers for Quarry outputs."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

OUTPUT_ENV_VAR = "QUARRY_OUTPUT_DIR"

_SCHEMA_SEGMENTS = ("schemas",)
_OUTPUT_SEGMENTS = ("data", "out")
_CACHE_SEGMENTS = ("data", "cache")
_EXPORT_SEGMENTS = ("exports",)
_FOREMAN_SEGMENTS = ("foreman_tutorial",)


@lru_cache(maxsize=1)
def _resolved_base_dir() -> Path:
    """Return the base directory for Quarry outputs."""
    env_value = os.environ.get(OUTPUT_ENV_VAR)
    if env_value:
        return Path(env_value).expanduser()
    return Path.cwd()


def get_base_dir(create: bool = True) -> Path:
    """Return the base output directory, creating it if requested."""
    base = _resolved_base_dir()
    if create:
        base.mkdir(parents=True, exist_ok=True)
    return base


def _subdir(segments: tuple[str, ...], create: bool) -> Path:
    """Return a subdirectory under the base path."""
    base = get_base_dir(create=create)
    if not segments:
        return base
    path = base.joinpath(*segments)
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_schema_dir(create: bool = False) -> Path:
    """Directory used for schema files."""
    return _subdir(_SCHEMA_SEGMENTS, create)


def get_output_dir(create: bool = False) -> Path:
    """Directory used for extracted JSONL output."""
    return _subdir(_OUTPUT_SEGMENTS, create)


def get_cache_dir(create: bool = False) -> Path:
    """Directory used for cache/state artifacts."""
    return _subdir(_CACHE_SEGMENTS, create)


def get_export_dir(create: bool = False) -> Path:
    """Directory used for exported artifacts (CSV, parquet, etc.)."""
    return _subdir(_EXPORT_SEGMENTS, create)


def get_foreman_dir(create: bool = False) -> Path:
    """Directory for the Foreman tutorial assets."""
    return _subdir(_FOREMAN_SEGMENTS, create)


def ensure_parent_dir(path: Path) -> None:
    """Ensure the parent directory for a file exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


def _sanitize_name(value: str | None, fallback: str) -> str:
    value = (value or "").strip()
    return value or fallback


def default_schema_path(name: str | None, create_dirs: bool = False) -> Path:
    """Return the default schema path for a given schema name."""
    safe_name = _sanitize_name(name, "schema")
    directory = get_schema_dir(create=create_dirs)
    return directory / f"{safe_name}.yml"


def default_extraction_output(name: str | None, create_dirs: bool = False) -> Path:
    """Return the default extraction output path for a schema."""
    safe_name = _sanitize_name(name, "output")
    directory = get_output_dir(create=create_dirs)
    return directory / f"{safe_name}.jsonl"


def default_polished_output(
    stem: str,
    suffix: str | None = None,
    create_dirs: bool = False,
) -> Path:
    """Return the default polished output path based on an input stem."""
    safe_name = _sanitize_name(stem, "output")
    directory = get_output_dir(create=create_dirs)
    file_suffix = suffix or ".jsonl"
    if file_suffix and not file_suffix.startswith("."):
        file_suffix = f".{file_suffix}"
    return directory / f"{safe_name}_polished{file_suffix}"


def default_export_path(
    base_name: str | None,
    extension: str = "csv",
    create_dirs: bool = False,
) -> Path:
    """Return the default export destination path."""
    safe_name = _sanitize_name(base_name, "quarry_export")
    ext = extension.lstrip(".")
    directory = get_export_dir(create=create_dirs)
    return directory / f"{safe_name}.{ext}"


def default_state_db_path(create_dirs: bool = True) -> Path:
    """Return the default SQLite path for job state."""
    directory = get_cache_dir(create=create_dirs)
    path = directory / "state.sqlite"
    if create_dirs:
        ensure_parent_dir(path)
    return path


def default_robots_cache_path(create_dirs: bool = True) -> Path:
    """Return the default SQLite path for robots.txt cache."""
    directory = get_cache_dir(create=create_dirs)
    path = directory / "robots.sqlite"
    if create_dirs:
        ensure_parent_dir(path)
    return path


def default_sink_path_template(extension: str = "parquet", create_dirs: bool = True) -> str:
    """Return the default sink template path for batch jobs."""
    ext = extension.lstrip(".")
    directory = get_cache_dir(create=create_dirs)
    template = directory / "{job}" / f"%Y%m%dT%H%M%SZ.{ext}"
    return str(template)


def auto_path_mode_enabled() -> bool:
    """Return True if QUARRY_OUTPUT_DIR is configured."""
    return bool(os.environ.get(OUTPUT_ENV_VAR))


def describe_base_dir() -> str:
    """Return a human-friendly description of the base directory."""
    return str(get_base_dir(create=False))
