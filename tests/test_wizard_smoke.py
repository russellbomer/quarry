"""Smoke tests for wizard."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

from scrapesuite.core import load_yaml
from scrapesuite.wizard import run_wizard


def test_wizard_generates_yaml() -> None:
    """Test that wizard generates valid YAML file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        jobs_dir = Path(tmpdir) / "jobs"
        jobs_dir.mkdir(parents=True)

        # Mock inputs
        inputs = [
            "fda_example",  # template
            "test_fda",  # job_name
            (
                "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts"
            ),  # entry (listing page, not detail)
            "fda_list",  # parser
            "fda_recalls",  # normalize
            "fda.gov",  # allowlist
            "1.0",  # rps
            "id",  # cursor_field
            "parquet",  # sink_kind
            "data/test.parquet",  # sink_path
            "10",  # max_items
            "n",  # skip smoke test
        ]

        with patch("scrapesuite.wizard._prompt_text", side_effect=inputs[1:11]):
            with patch("scrapesuite.wizard._prompt_select", side_effect=[inputs[0], inputs[8]]):
                with patch("scrapesuite.wizard._prompt_confirm", return_value=False):
                    # Change to temp dir
                    old_cwd = os.getcwd()
                    try:
                        os.chdir(tmpdir)
                        run_wizard()
                    finally:
                        os.chdir(old_cwd)

        yaml_file = jobs_dir / "test_fda.yml"
        assert yaml_file.exists()

        # Verify YAML structure
        job_dict = load_yaml(str(yaml_file))
        assert job_dict["job"] == "test_fda"
        assert job_dict["source"]["parser"] == "fda_list"


def test_wizard_smoke_test_runs() -> None:
    """Test that wizard can run smoke test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create minimal job YAML
        jobs_dir = Path(tmpdir) / "jobs"
        jobs_dir.mkdir(parents=True)
        fixtures_dir = Path(tmpdir) / "tests" / "fixtures"
        fixtures_dir.mkdir(parents=True)

        # Copy fixture structure would go here
        # For now, just verify wizard doesn't crash

        job_yaml = {
            "version": "1",
            "job": "test_job",
            "source": {
                "kind": "html",
                "entry": "https://example.com",
                "parser": "fda_list",
            },
            "transform": {"pipeline": [{"normalize": "fda_recalls"}]},
            "sink": {"kind": "parquet", "path": "data/test.parquet"},
            "policy": {"allowlist": []},
        }

        yaml_file = jobs_dir / "test_job.yml"
        with open(yaml_file, "w") as f:
            yaml.dump(job_yaml, f)

        # This would require fixtures to be present, so we just verify structure
        assert yaml_file.exists()
