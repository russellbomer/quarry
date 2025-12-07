"""Tests for Ship export tool."""

import csv
import json
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from quarry.tools.ship.base import ExporterFactory
from quarry.tools.ship.exporters import (
    CSVExporter,
    JSONExporter,
    SQLiteExporter,
)


class TestCSVExporter:
    """Test CSV export functionality."""

    def test_basic_csv_export(self):
        """Test basic CSV export."""
        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.jsonl"
            output_file = Path(tmpdir) / "output.csv"

            # Create input JSONL
            with input_file.open("w") as f:
                f.write(json.dumps({"title": "Item 1", "value": "100"}) + "\n")
                f.write(json.dumps({"title": "Item 2", "value": "200"}) + "\n")

            # Export
            exporter = CSVExporter(str(output_file))
            stats = exporter.export(input_file)

            assert stats["records_read"] == 2
            assert stats["records_written"] == 2
            assert output_file.exists()

            # Verify CSV content
            with output_file.open("r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                assert len(rows) == 2
                assert rows[0]["title"] == "Item 1"
                assert rows[0]["value"] == "100"

    def test_csv_excludes_meta(self):
        """Test that _meta field is excluded by default."""
        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.jsonl"
            output_file = Path(tmpdir) / "output.csv"

            # Create input with _meta
            with input_file.open("w") as f:
                f.write(
                    json.dumps({"title": "Item", "_meta": {"url": "http://example.com"}}) + "\n"
                )

            # Export
            exporter = CSVExporter(str(output_file))
            exporter.export(input_file)

            # Verify _meta not in CSV
            with output_file.open("r") as f:
                reader = csv.DictReader(f)
                assert "_meta" not in reader.fieldnames

    def test_csv_custom_delimiter(self):
        """Test CSV with custom delimiter."""
        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.jsonl"
            output_file = Path(tmpdir) / "output.csv"

            # Create input
            with input_file.open("w") as f:
                f.write(json.dumps({"a": "1", "b": "2"}) + "\n")

            # Export with pipe delimiter
            exporter = CSVExporter(str(output_file), delimiter="|")
            exporter.export(input_file)

            # Verify delimiter
            content = output_file.read_text()
            assert "|" in content
            assert "," not in content or content.count(",") == 0  # No commas as delimiters

    def test_csv_handles_complex_values(self):
        """Test CSV handles lists and dicts."""
        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.jsonl"
            output_file = Path(tmpdir) / "output.csv"

            # Create input with complex values
            with input_file.open("w") as f:
                f.write(
                    json.dumps(
                        {"title": "Item", "tags": ["tag1", "tag2"], "metadata": {"key": "value"}}
                    )
                    + "\n"
                )

            # Export
            exporter = CSVExporter(str(output_file))
            exporter.export(input_file)

            # Verify complex values are JSON-encoded
            with output_file.open("r") as f:
                reader = csv.DictReader(f)
                row = next(reader)

                assert json.loads(row["tags"]) == ["tag1", "tag2"]
                assert json.loads(row["metadata"]) == {"key": "value"}


class TestJSONExporter:
    """Test JSON export functionality."""

    def test_basic_json_export(self):
        """Test basic JSON array export."""
        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.jsonl"
            output_file = Path(tmpdir) / "output.json"

            # Create input
            with input_file.open("w") as f:
                f.write(json.dumps({"title": "Item 1"}) + "\n")
                f.write(json.dumps({"title": "Item 2"}) + "\n")

            # Export
            exporter = JSONExporter(str(output_file))
            stats = exporter.export(input_file)

            assert stats["records_read"] == 2
            assert stats["records_written"] == 2

            # Verify JSON
            with output_file.open("r") as f:
                data = json.load(f)

                assert isinstance(data, list)
                assert len(data) == 2
                assert data[0]["title"] == "Item 1"

    def test_json_pretty_print(self):
        """Test JSON pretty printing."""
        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.jsonl"
            output_file = Path(tmpdir) / "output.json"

            # Create input
            with input_file.open("w") as f:
                f.write(json.dumps({"title": "Item"}) + "\n")

            # Export with pretty printing
            exporter = JSONExporter(str(output_file), pretty=True)
            exporter.export(input_file)

            # Verify formatting
            content = output_file.read_text()
            assert "\n" in content
            assert "  " in content  # Indentation

    def test_json_excludes_meta(self):
        """Test that _meta can be excluded."""
        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.jsonl"
            output_file = Path(tmpdir) / "output.json"

            # Create input with _meta
            with input_file.open("w") as f:
                f.write(
                    json.dumps({"title": "Item", "_meta": {"url": "http://example.com"}}) + "\n"
                )

            # Export with exclude_meta
            exporter = JSONExporter(str(output_file), exclude_meta=True)
            exporter.export(input_file)

            # Verify _meta excluded
            with output_file.open("r") as f:
                data = json.load(f)
                assert "_meta" not in data[0]


class TestSQLiteExporter:
    """Test SQLite export functionality."""

    def test_basic_sqlite_export(self):
        """Test basic SQLite export."""
        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.jsonl"
            db_file = Path(tmpdir) / "output.db"

            # Create input
            with input_file.open("w") as f:
                f.write(json.dumps({"title": "Item 1", "value": 100}) + "\n")
                f.write(json.dumps({"title": "Item 2", "value": 200}) + "\n")

            # Export
            exporter = SQLiteExporter(str(db_file))
            stats = exporter.export(input_file)

            assert stats["records_read"] == 2
            assert stats["records_written"] == 2
            assert db_file.exists()

            # Verify database
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM records")
            rows = cursor.fetchall()
            conn.close()

            assert len(rows) == 2

    def test_sqlite_custom_table_name(self):
        """Test SQLite with custom table name."""
        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.jsonl"
            db_file = Path(tmpdir) / "output.db"

            # Create input
            with input_file.open("w") as f:
                f.write(json.dumps({"title": "Item"}) + "\n")

            # Export with custom table
            exporter = SQLiteExporter(str(db_file), table_name="products")
            exporter.export(input_file)

            # Verify table exists
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()

            assert "products" in tables

    def test_sqlite_if_exists_replace(self):
        """Test SQLite replace mode."""
        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.jsonl"
            db_file = Path(tmpdir) / "output.db"

            # Create input
            with input_file.open("w") as f:
                f.write(json.dumps({"title": "Item 1"}) + "\n")

            # First export
            exporter1 = SQLiteExporter(str(db_file))
            exporter1.export(input_file)

            # Second export (replace)
            with input_file.open("w") as f:
                f.write(json.dumps({"title": "Item 2"}) + "\n")

            exporter2 = SQLiteExporter(str(db_file), if_exists="replace")
            exporter2.export(input_file)

            # Verify only new data exists
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM records")
            count = cursor.fetchone()[0]
            conn.close()

            assert count == 1  # Only one record (replaced)

    def test_sqlite_if_exists_append(self):
        """Test SQLite append mode."""
        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.jsonl"
            db_file = Path(tmpdir) / "output.db"

            # First export
            with input_file.open("w") as f:
                f.write(json.dumps({"title": "Item 1"}) + "\n")

            exporter1 = SQLiteExporter(str(db_file))
            exporter1.export(input_file)

            # Second export (append)
            with input_file.open("w") as f:
                f.write(json.dumps({"title": "Item 2"}) + "\n")

            exporter2 = SQLiteExporter(str(db_file), if_exists="append")
            exporter2.export(input_file)

            # Verify both records exist
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM records")
            count = cursor.fetchone()[0]
            conn.close()

            assert count == 2  # Both records

    def test_sqlite_handles_null_values(self):
        """Test SQLite handles None/null values."""
        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.jsonl"
            db_file = Path(tmpdir) / "output.db"

            # Create input with null
            with input_file.open("w") as f:
                f.write(json.dumps({"title": "Item", "value": None}) + "\n")

            # Export
            exporter = SQLiteExporter(str(db_file))
            exporter.export(input_file)

            # Verify null handling
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM records")
            value = cursor.fetchone()[0]
            conn.close()

            assert value is None


class TestExporterFactory:
    """Test the ExporterFactory."""

    def test_factory_creates_csv_exporter(self):
        """Test factory creates CSV exporter for .csv files."""
        exporter = ExporterFactory.create("output.csv")
        assert isinstance(exporter, CSVExporter)

    def test_factory_creates_json_exporter(self):
        """Test factory creates JSON exporter for .json files."""
        exporter = ExporterFactory.create("output.json")
        assert isinstance(exporter, JSONExporter)

    def test_factory_creates_sqlite_exporter(self):
        """Test factory creates SQLite exporter for .db files."""
        exporter = ExporterFactory.create("output.db")
        assert isinstance(exporter, SQLiteExporter)

        exporter = ExporterFactory.create("output.sqlite")
        assert isinstance(exporter, SQLiteExporter)

    def test_factory_handles_sqlite_scheme(self):
        """Test factory handles sqlite:// URLs."""
        exporter = ExporterFactory.create("sqlite://data.db")
        assert isinstance(exporter, SQLiteExporter)

    def test_factory_unknown_format_raises(self):
        """Test factory raises for unknown formats."""
        with pytest.raises(ValueError, match="Cannot determine export format"):
            ExporterFactory.create("output.unknown")

    def test_factory_passes_options(self):
        """Test factory passes options to exporters."""
        exporter = ExporterFactory.create("output.csv", delimiter="|")
        assert exporter.options["delimiter"] == "|"


class TestIntegration:
    """Integration tests with real workflows."""

    def test_complete_export_workflow(self):
        """Test complete export workflow to multiple formats."""
        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.jsonl"

            # Create realistic input
            with input_file.open("w") as f:
                f.write(
                    json.dumps(
                        {
                            "title": "Item 1",
                            "url": "http://example.com/1",
                            "value": 100,
                            "_meta": {"fetched_at": "2024-01-01"},
                        }
                    )
                    + "\n"
                )
                f.write(
                    json.dumps(
                        {
                            "title": "Item 2",
                            "url": "http://example.com/2",
                            "value": 200,
                            "_meta": {"fetched_at": "2024-01-02"},
                        }
                    )
                    + "\n"
                )

            # Export to CSV
            csv_file = Path(tmpdir) / "output.csv"
            csv_exporter = CSVExporter(str(csv_file))
            csv_stats = csv_exporter.export(input_file)
            assert csv_stats["records_written"] == 2
            assert csv_file.exists()

            # Export to JSON
            json_file = Path(tmpdir) / "output.json"
            json_exporter = JSONExporter(str(json_file), pretty=True)
            json_stats = json_exporter.export(input_file)
            assert json_stats["records_written"] == 2
            assert json_file.exists()

            # Export to SQLite
            db_file = Path(tmpdir) / "output.db"
            sqlite_exporter = SQLiteExporter(str(db_file), table_name="items")
            sqlite_stats = sqlite_exporter.export(input_file)
            assert sqlite_stats["records_written"] == 2
            assert db_file.exists()
