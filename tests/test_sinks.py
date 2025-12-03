"""Tests for CSV and JSONL sink implementations."""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from quarry.sinks.csv import CSVSink
from quarry.sinks.jsonl import JSONLSink


class TestCSVSink:
    """Tests for CSVSink."""

    def test_init_defaults(self):
        """Should initialize with default timezone."""
        sink = CSVSink("output.csv")
        assert sink.path_template == "output.csv"
        assert sink.timezone == "America/New_York"

    def test_init_custom_timezone(self):
        """Should accept custom timezone."""
        sink = CSVSink("output.csv", timezone="UTC")
        assert sink.timezone == "UTC"

    def test_write_creates_file(self):
        """Should write DataFrame to CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.csv"
            sink = CSVSink(str(path))
            df = pd.DataFrame({"col1": ["a", "b"], "col2": [1, 2]})

            result = sink.write(df, "test_job")

            assert Path(result).exists()
            assert Path(result).read_text().startswith("col1,col2")

    def test_write_creates_parent_dirs(self):
        """Should create parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nested" / "dirs" / "test.csv"
            sink = CSVSink(str(path))
            df = pd.DataFrame({"col1": ["a"]})

            result = sink.write(df, "test_job")

            assert Path(result).exists()

    def test_write_empty_dataframe_raises(self):
        """Should raise ValueError for empty DataFrame."""
        sink = CSVSink("output.csv")
        empty_df = pd.DataFrame()

        with pytest.raises(ValueError) as exc_info:
            sink.write(empty_df, "test_job")

        assert "empty" in str(exc_info.value).lower()

    def test_write_job_placeholder(self):
        """Should replace {job} placeholder in path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "{job}_output.csv"
            sink = CSVSink(str(path))
            df = pd.DataFrame({"col1": ["a"]})

            result = sink.write(df, "my_job")

            assert "my_job_output.csv" in result

    def test_write_invalid_timezone_fallback(self):
        """Should fallback to America/New_York for invalid timezone."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.csv"
            sink = CSVSink(str(path), timezone="Invalid/Timezone")
            df = pd.DataFrame({"col1": ["a"]})

            # Should not raise, should fallback gracefully
            result = sink.write(df, "test_job")
            assert Path(result).exists()

    def test_write_timestamp_template(self):
        """Should expand strftime patterns in path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data_%Y%m%d.csv"
            sink = CSVSink(str(path))
            df = pd.DataFrame({"col1": ["a"]})

            result = sink.write(df, "test_job")

            # Result should have date expanded, not literal %Y%m%d
            assert "%Y" not in result
            assert Path(result).exists()


class TestJSONLSink:
    """Tests for JSONLSink."""

    def test_init_defaults(self):
        """Should initialize with default timezone."""
        sink = JSONLSink("output.jsonl")
        assert sink.path_template == "output.jsonl"
        assert sink.timezone == "America/New_York"

    def test_init_custom_timezone(self):
        """Should accept custom timezone."""
        sink = JSONLSink("output.jsonl", timezone="UTC")
        assert sink.timezone == "UTC"

    def test_write_creates_file(self):
        """Should write DataFrame to JSONL file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl"
            sink = JSONLSink(str(path))
            df = pd.DataFrame({"col1": ["a", "b"], "col2": [1, 2]})

            result = sink.write(df, "test_job")

            assert Path(result).exists()
            lines = Path(result).read_text().strip().split("\n")
            assert len(lines) == 2

    def test_write_valid_json_lines(self):
        """Should write valid JSON on each line."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl"
            sink = JSONLSink(str(path))
            df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [30, 25]})

            result = sink.write(df, "test_job")

            lines = Path(result).read_text().strip().split("\n")
            for line in lines:
                data = json.loads(line)  # Should not raise
                assert "name" in data
                assert "age" in data

    def test_write_creates_parent_dirs(self):
        """Should create parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "nested" / "dirs" / "test.jsonl"
            sink = JSONLSink(str(path))
            df = pd.DataFrame({"col1": ["a"]})

            result = sink.write(df, "test_job")

            assert Path(result).exists()

    def test_write_empty_dataframe_raises(self):
        """Should raise ValueError for empty DataFrame."""
        sink = JSONLSink("output.jsonl")
        empty_df = pd.DataFrame()

        with pytest.raises(ValueError) as exc_info:
            sink.write(empty_df, "test_job")

        assert "empty" in str(exc_info.value).lower()

    def test_write_job_placeholder(self):
        """Should replace {job} placeholder in path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "{job}_output.jsonl"
            sink = JSONLSink(str(path))
            df = pd.DataFrame({"col1": ["a"]})

            result = sink.write(df, "my_job")

            assert "my_job_output.jsonl" in result

    def test_write_invalid_timezone_fallback(self):
        """Should fallback to America/New_York for invalid timezone."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl"
            sink = JSONLSink(str(path), timezone="Invalid/Timezone")
            df = pd.DataFrame({"col1": ["a"]})

            # Should not raise, should fallback gracefully
            result = sink.write(df, "test_job")
            assert Path(result).exists()

    def test_write_handles_complex_types(self):
        """Should serialize complex types (lists, dicts) as JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.jsonl"
            sink = JSONLSink(str(path))
            df = pd.DataFrame({
                "name": ["Alice"],
                "tags": [["python", "data"]],
                "meta": [{"key": "value"}],
            })

            result = sink.write(df, "test_job")

            line = Path(result).read_text().strip()
            data = json.loads(line)
            assert data["tags"] == ["python", "data"]
            assert data["meta"] == {"key": "value"}

    def test_write_timestamp_template(self):
        """Should expand strftime patterns in path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "data_%Y%m%d.jsonl"
            sink = JSONLSink(str(path))
            df = pd.DataFrame({"col1": ["a"]})

            result = sink.write(df, "test_job")

            # Result should have date expanded
            assert "%Y" not in result
            assert Path(result).exists()
