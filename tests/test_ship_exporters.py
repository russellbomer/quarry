"""Tests for ship exporters module."""

import csv
import json
import sqlite3
from pathlib import Path

import pytest

from quarry.tools.ship.exporters import CSVExporter, JSONExporter, SQLiteExporter


class TestCSVExporter:
    """Tests for CSVExporter class."""

    @pytest.fixture
    def sample_jsonl(self, tmp_path):
        """Create sample JSONL input file."""
        jsonl_path = tmp_path / "input.jsonl"
        records = [
            {"id": "1", "title": "First", "author": "Alice"},
            {"id": "2", "title": "Second", "author": "Bob"},
        ]
        jsonl_path.write_text(
            "\n".join(json.dumps(r) for r in records), encoding="utf-8"
        )
        return jsonl_path

    def test_export_basic(self, tmp_path, sample_jsonl):
        """Test basic CSV export."""
        output_path = tmp_path / "output.csv"
        exporter = CSVExporter(str(output_path))

        stats = exporter.export(sample_jsonl)

        assert output_path.exists()
        assert stats["records_written"] == 2

        # Verify content
        with output_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["title"] == "First"

    def test_export_creates_parent_dirs(self, tmp_path, sample_jsonl):
        """Test that export creates parent directories."""
        output_path = tmp_path / "nested" / "dirs" / "output.csv"
        exporter = CSVExporter(str(output_path))

        exporter.export(sample_jsonl)

        assert output_path.exists()

    def test_export_empty_file(self, tmp_path):
        """Test export with empty input."""
        jsonl_path = tmp_path / "empty.jsonl"
        jsonl_path.write_text("", encoding="utf-8")

        output_path = tmp_path / "output.csv"
        exporter = CSVExporter(str(output_path))

        stats = exporter.export(jsonl_path)

        assert output_path.exists()
        assert stats["records_written"] == 0

    def test_export_excludes_meta(self, tmp_path):
        """Test that _meta field is excluded by default."""
        jsonl_path = tmp_path / "input.jsonl"
        record = {"id": "1", "title": "Test", "_meta": {"url": "http://example.com"}}
        jsonl_path.write_text(json.dumps(record), encoding="utf-8")

        output_path = tmp_path / "output.csv"
        exporter = CSVExporter(str(output_path), exclude_meta=True)

        exporter.export(jsonl_path)

        with output_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert "_meta" not in rows[0]

    def test_export_custom_delimiter(self, tmp_path, sample_jsonl):
        """Test export with custom delimiter."""
        output_path = tmp_path / "output.csv"
        exporter = CSVExporter(str(output_path), delimiter=";")

        exporter.export(sample_jsonl)

        content = output_path.read_text(encoding="utf-8")
        assert ";" in content

    def test_export_handles_nested_values(self, tmp_path):
        """Test export converts nested values to JSON strings."""
        jsonl_path = tmp_path / "input.jsonl"
        record = {"id": "1", "tags": ["a", "b"], "meta": {"key": "value"}}
        jsonl_path.write_text(json.dumps(record), encoding="utf-8")

        output_path = tmp_path / "output.csv"
        exporter = CSVExporter(str(output_path))

        exporter.export(jsonl_path)

        with output_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Nested values should be JSON strings
        assert rows[0]["tags"] == '["a", "b"]'

    def test_export_handles_varying_columns(self, tmp_path):
        """Test export handles records with different columns."""
        jsonl_path = tmp_path / "input.jsonl"
        records = [
            {"id": "1", "title": "First"},
            {"id": "2", "author": "Bob"},  # Different columns
        ]
        jsonl_path.write_text(
            "\n".join(json.dumps(r) for r in records), encoding="utf-8"
        )

        output_path = tmp_path / "output.csv"
        exporter = CSVExporter(str(output_path))

        stats = exporter.export(jsonl_path)

        assert stats["records_written"] == 2

        with output_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

        # Should have all columns from all records
        assert "title" in fieldnames
        assert "author" in fieldnames


class TestJSONExporter:
    """Tests for JSONExporter class."""

    @pytest.fixture
    def sample_jsonl(self, tmp_path):
        """Create sample JSONL input file."""
        jsonl_path = tmp_path / "input.jsonl"
        records = [
            {"id": "1", "title": "First"},
            {"id": "2", "title": "Second"},
        ]
        jsonl_path.write_text(
            "\n".join(json.dumps(r) for r in records), encoding="utf-8"
        )
        return jsonl_path

    def test_export_basic(self, tmp_path, sample_jsonl):
        """Test basic JSON export."""
        output_path = tmp_path / "output.json"
        exporter = JSONExporter(str(output_path))

        stats = exporter.export(sample_jsonl)

        assert output_path.exists()
        assert stats["records_written"] == 2

        # Verify content is JSON array
        with output_path.open(encoding="utf-8") as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["title"] == "First"

    def test_export_pretty(self, tmp_path, sample_jsonl):
        """Test pretty-printed JSON export."""
        output_path = tmp_path / "output.json"
        exporter = JSONExporter(str(output_path), pretty=True, indent=4)

        exporter.export(sample_jsonl)

        content = output_path.read_text(encoding="utf-8")
        # Pretty printed should have newlines and indentation
        assert "\n" in content
        assert "    " in content  # 4 space indent

    def test_export_excludes_meta(self, tmp_path):
        """Test that _meta field can be excluded."""
        jsonl_path = tmp_path / "input.jsonl"
        record = {"id": "1", "_meta": {"url": "http://example.com"}}
        jsonl_path.write_text(json.dumps(record), encoding="utf-8")

        output_path = tmp_path / "output.json"
        exporter = JSONExporter(str(output_path), exclude_meta=True)

        exporter.export(jsonl_path)

        with output_path.open(encoding="utf-8") as f:
            data = json.load(f)

        assert "_meta" not in data[0]

    def test_export_empty_input(self, tmp_path):
        """Test export with empty input."""
        jsonl_path = tmp_path / "empty.jsonl"
        jsonl_path.write_text("", encoding="utf-8")

        output_path = tmp_path / "output.json"
        exporter = JSONExporter(str(output_path))

        stats = exporter.export(jsonl_path)

        assert stats["records_written"] == 0
        with output_path.open(encoding="utf-8") as f:
            data = json.load(f)
        assert data == []


class TestSQLiteExporter:
    """Tests for SQLiteExporter class."""

    @pytest.fixture
    def sample_jsonl(self, tmp_path):
        """Create sample JSONL input file."""
        jsonl_path = tmp_path / "input.jsonl"
        records = [
            {"id": "1", "title": "First", "author": "Alice"},
            {"id": "2", "title": "Second", "author": "Bob"},
        ]
        jsonl_path.write_text(
            "\n".join(json.dumps(r) for r in records), encoding="utf-8"
        )
        return jsonl_path

    def test_export_basic(self, tmp_path, sample_jsonl):
        """Test basic SQLite export."""
        db_path = tmp_path / "output.db"
        exporter = SQLiteExporter(str(db_path))

        stats = exporter.export(sample_jsonl)

        assert db_path.exists()
        assert stats["records_written"] == 2

        # Verify content
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM records")
        rows = cursor.fetchall()
        conn.close()

        assert len(rows) == 2

    def test_export_custom_table_name(self, tmp_path, sample_jsonl):
        """Test export with custom table name."""
        db_path = tmp_path / "output.db"
        exporter = SQLiteExporter(str(db_path), table_name="my_data")

        exporter.export(sample_jsonl)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        assert "my_data" in tables

    def test_export_replace_mode(self, tmp_path, sample_jsonl):
        """Test replace mode drops existing table."""
        db_path = tmp_path / "output.db"

        # First export
        exporter1 = SQLiteExporter(str(db_path), if_exists="replace")
        exporter1.export(sample_jsonl)

        # Second export should replace
        exporter2 = SQLiteExporter(str(db_path), if_exists="replace")
        stats = exporter2.export(sample_jsonl)

        assert stats["records_written"] == 2

        # Should still have only 2 records
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM records")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 2

    def test_export_fail_mode_raises(self, tmp_path, sample_jsonl):
        """Test fail mode raises when table exists."""
        db_path = tmp_path / "output.db"

        # First export
        exporter1 = SQLiteExporter(str(db_path))
        exporter1.export(sample_jsonl)

        # Second export should fail
        exporter2 = SQLiteExporter(str(db_path), if_exists="fail")
        with pytest.raises(ValueError) as exc_info:
            exporter2.export(sample_jsonl)

        assert "already exists" in str(exc_info.value)

    def test_export_invalid_table_name(self, tmp_path, sample_jsonl):
        """Test invalid table name raises error."""
        db_path = tmp_path / "output.db"
        exporter = SQLiteExporter(str(db_path), table_name="drop table;")

        with pytest.raises(ValueError) as exc_info:
            exporter.export(sample_jsonl)

        assert "Invalid table name" in str(exc_info.value)

    def test_export_empty_input(self, tmp_path):
        """Test export with empty input."""
        jsonl_path = tmp_path / "empty.jsonl"
        jsonl_path.write_text("", encoding="utf-8")

        db_path = tmp_path / "output.db"
        exporter = SQLiteExporter(str(db_path))

        stats = exporter.export(jsonl_path)

        assert stats["records_written"] == 0

    def test_export_excludes_meta(self, tmp_path):
        """Test that _meta field is excluded by default."""
        jsonl_path = tmp_path / "input.jsonl"
        record = {"id": "1", "title": "Test", "_meta": {"url": "http://example.com"}}
        jsonl_path.write_text(json.dumps(record), encoding="utf-8")

        db_path = tmp_path / "output.db"
        exporter = SQLiteExporter(str(db_path), exclude_meta=True)

        exporter.export(jsonl_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(records)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()

        assert "_meta" not in columns

    def test_export_handles_nested_values(self, tmp_path):
        """Test export converts nested values to JSON strings."""
        jsonl_path = tmp_path / "input.jsonl"
        record = {"id": "1", "tags": ["a", "b"]}
        jsonl_path.write_text(json.dumps(record), encoding="utf-8")

        db_path = tmp_path / "output.db"
        exporter = SQLiteExporter(str(db_path))

        exporter.export(jsonl_path)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT tags FROM records")
        value = cursor.fetchone()[0]
        conn.close()

        assert value == '["a", "b"]'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
