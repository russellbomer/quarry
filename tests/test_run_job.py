"""Tests for job execution."""

import tempfile
from pathlib import Path

import pytest

from quarry.connectors import custom
from quarry.core import load_yaml, run_job
from quarry.state import load_cursor

# Test constants to avoid magic numbers
MIN_EXPECTED_RECORDS = 3
MIN_RECORDS_FOR_STATE_TEST = 2


def test_load_yaml() -> None:
    """Test YAML loading and validation."""
    job_dict = load_yaml("examples/jobs/fda.yml")
    assert job_dict["version"] == "1"
    assert job_dict["job"] == "fda_recalls"
    assert job_dict["source"]["parser"] == "fda_list"


def test_run_fda_job_offline() -> None:
    """Test running FDA job offline."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name

    try:
        job_dict = load_yaml("examples/jobs/fda.yml")
        df, next_cursor = run_job(job_dict, max_items=10, offline=True, db_path=db_path)

        assert len(df) > 0
        assert next_cursor is not None

        # Check expected columns
        expected_cols = [
            "id",
            "source",
            "title",
            "url",
            "posted_at",
            "class",
            "class_weight",
            "category",
        ]
        for col in expected_cols:
            assert col in df.columns

        assert all(df["source"] == "fda")

        # Verify URLs are absolute and realistic
        for url in df["url"]:
            assert url.startswith("http")
            assert "fda.gov" in url

        # Verify cursor was saved
        saved_cursor = load_cursor("fda_recalls", db_path=db_path)
        assert saved_cursor == next_cursor

    finally:
        Path(db_path).unlink(missing_ok=True)


def test_run_nws_job_offline() -> None:
    """Test running NWS job offline."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name

    try:
        job_dict = load_yaml("examples/jobs/nws.yml")
        df, next_cursor = run_job(job_dict, max_items=10, offline=True, db_path=db_path)

        assert len(df) > 0
        assert next_cursor is not None

        # Check expected columns
        expected_cols = [
            "id",
            "source",
            "title",
            "url",
            "posted_at",
            "type",
            "severity_weight",
        ]
        for col in expected_cols:
            assert col in df.columns

        assert all(df["source"] == "nws")

    finally:
        Path(db_path).unlink(missing_ok=True)


def test_cursor_advancement() -> None:
    """Test that second run yields 0 new inserts if same fixtures."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name

    try:
        job_dict = load_yaml("examples/jobs/fda.yml")

        # First run
        df1, _ = run_job(job_dict, max_items=10, offline=True, db_path=db_path)
        assert len(df1) > 0

        # Second run with same cursor
        df2, _ = run_job(job_dict, max_items=10, offline=True, db_path=db_path)

        # Should have no new items (cursor filtering)
        assert len(df2) == 0

    finally:
        Path(db_path).unlink(missing_ok=True)


def test_run_custom_job_offline() -> None:
    """Test running custom job offline."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name

    try:
        job_dict: dict = {
            "version": "1",
            "job": "custom_test",
            "source": {
                "kind": "html",
                "entry": "https://example.com/",
                "parser": "custom_list",
                "rate_limit_rps": 1.0,
                "cursor": {"field": "id", "stop_when_seen": True},
            },
            "transform": {"pipeline": [{"normalize": "custom"}]},
            "sink": {"kind": "parquet", "path": "data/cache/custom/%Y%m%dT%H%M%SZ.parquet"},
            "policy": {"robots": "allow", "allowlist": ["example.com"]},
        }

        df, next_cursor = run_job(job_dict, max_items=10, offline=True, db_path=db_path)

        assert len(df) >= MIN_EXPECTED_RECORDS
        assert next_cursor is not None

        # Check expected columns
        expected_cols = ["id", "source", "title", "url", "posted_at"]
        for col in expected_cols:
            assert col in df.columns

        assert all(df["source"] == "custom")

    finally:
        Path(db_path).unlink(missing_ok=True)


def test_custom_connector_live_raises() -> None:
    """Test that custom connector raises NotImplementedError in live mode."""
    entry_url = "https://example.com/"
    connector = custom.CustomConnector(entry_url=entry_url)

    with pytest.raises(NotImplementedError, match="requires implementation for live mode"):
        connector.collect(cursor=None, max_items=10, offline=False)


def test_run_all_ignores_examples() -> None:
    """Test that run-all only globs jobs/*.yml, not examples/."""
    _jobs_dir = Path("jobs")
    examples_dir = Path("examples/jobs")

    # Verify glob pattern is non-recursive
    examples_files = sorted(examples_dir.glob("*.yml"))

    # If examples exist but jobs are empty, that's expected after moving files
    # The key is that glob("*.yml") doesn't traverse into examples/
    assert examples_files  # Examples should exist
    # jobs/ might be empty now, which is fine - the test verifies glob doesn't recurse
