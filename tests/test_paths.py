"""Tests for QUARRY_OUTPUT_DIR-aware path helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from quarry.lib import paths


@pytest.fixture(autouse=True)
def reset_paths_cache(monkeypatch):
    """Reset cached base directory between tests."""
    paths._resolved_base_dir.cache_clear()  # type: ignore[attr-defined]
    monkeypatch.delenv(paths.OUTPUT_ENV_VAR, raising=False)
    yield
    paths._resolved_base_dir.cache_clear()  # type: ignore[attr-defined]
    monkeypatch.delenv(paths.OUTPUT_ENV_VAR, raising=False)


def test_base_dir_defaults_to_cwd():
    """Without env var, the base directory is the current working directory."""
    assert paths.get_base_dir(create=False) == Path.cwd()


def test_output_dir_uses_env(monkeypatch, tmp_path):
    """QUARRY_OUTPUT_DIR drives output subdirectories when set."""
    base = tmp_path / "quarry_outputs"
    monkeypatch.setenv(paths.OUTPUT_ENV_VAR, str(base))
    paths._resolved_base_dir.cache_clear()  # type: ignore[attr-defined]

    output_dir = paths.get_output_dir(create=True)
    assert output_dir == base / "data" / "out"
    assert output_dir.exists()

    schema_path = paths.default_schema_path("example", create_dirs=True)
    assert schema_path == base / "schemas" / "example.yml"
    assert schema_path.parent.exists()
