"""Tests for quarry/tools/ship/base.py."""

import json
import pytest
from pathlib import Path

from quarry.tools.ship.base import Exporter, ExporterFactory
from quarry.tools.ship.exporters import CSVExporter, JSONExporter, SQLiteExporter


class TestExporterInit:
    """Tests for Exporter base class initialization."""

    def test_init_stores_destination(self):
        """Test exporter stores destination."""
        # Create a concrete subclass for testing
        exporter = CSVExporter("/path/to/output.csv")
        assert exporter.destination == "/path/to/output.csv"

    def test_init_stores_options(self):
        """Test exporter stores options."""
        exporter = CSVExporter("/path/to/output.csv", delimiter=";")
        assert exporter.options["delimiter"] == ";"

    def test_init_creates_zeroed_stats(self):
        """Test exporter initializes with zeroed stats."""
        exporter = CSVExporter("/path/to/output.csv")
        assert exporter.stats["records_read"] == 0
        assert exporter.stats["records_written"] == 0
        assert exporter.stats["records_failed"] == 0


class TestExporterReadJsonl:
    """Tests for _read_jsonl method."""

    def test_read_jsonl_yields_records(self, tmp_path):
        """Test _read_jsonl yields valid records."""
        input_file = tmp_path / "input.jsonl"
        records = [{"id": 1}, {"id": 2}, {"id": 3}]
        input_file.write_text("\n".join(json.dumps(r) for r in records))

        exporter = CSVExporter(str(tmp_path / "output.csv"))
        result = list(exporter._read_jsonl(input_file))

        assert len(result) == 3
        assert exporter.stats["records_read"] == 3

    def test_read_jsonl_skips_empty_lines(self, tmp_path):
        """Test _read_jsonl skips empty lines."""
        input_file = tmp_path / "input.jsonl"
        input_file.write_text('{"id": 1}\n\n{"id": 2}\n   \n{"id": 3}')

        exporter = CSVExporter(str(tmp_path / "output.csv"))
        result = list(exporter._read_jsonl(input_file))

        assert len(result) == 3

    def test_read_jsonl_handles_invalid_json(self, tmp_path):
        """Test _read_jsonl counts failed records."""
        input_file = tmp_path / "input.jsonl"
        input_file.write_text('{"id": 1}\nnot json\n{"id": 2}')

        exporter = CSVExporter(str(tmp_path / "output.csv"))
        result = list(exporter._read_jsonl(input_file))

        assert len(result) == 2
        assert exporter.stats["records_read"] == 2
        assert exporter.stats["records_failed"] == 1


class TestExporterFactory:
    """Tests for ExporterFactory."""

    def test_create_csv_exporter_by_extension(self, tmp_path):
        """Test factory creates CSVExporter for .csv files."""
        exporter = ExporterFactory.create(str(tmp_path / "output.csv"))
        assert isinstance(exporter, CSVExporter)

    def test_create_json_exporter_by_extension(self, tmp_path):
        """Test factory creates JSONExporter for .json files."""
        exporter = ExporterFactory.create(str(tmp_path / "output.json"))
        assert isinstance(exporter, JSONExporter)

    def test_create_sqlite_exporter_by_db_extension(self, tmp_path):
        """Test factory creates SQLiteExporter for .db files."""
        exporter = ExporterFactory.create(str(tmp_path / "output.db"))
        assert isinstance(exporter, SQLiteExporter)

    def test_create_sqlite_exporter_by_sqlite_extension(self, tmp_path):
        """Test factory creates SQLiteExporter for .sqlite files."""
        exporter = ExporterFactory.create(str(tmp_path / "output.sqlite"))
        assert isinstance(exporter, SQLiteExporter)

    def test_create_sqlite_exporter_by_sqlite3_extension(self, tmp_path):
        """Test factory creates SQLiteExporter for .sqlite3 files."""
        exporter = ExporterFactory.create(str(tmp_path / "output.sqlite3"))
        assert isinstance(exporter, SQLiteExporter)

    def test_create_sqlite_exporter_by_connection_string(self, tmp_path):
        """Test factory creates SQLiteExporter for sqlite:// connection."""
        # Note: When path ends with .db, the extension check comes first
        # Use a path without extension to force sqlite:// scheme handling
        db_path = str(tmp_path / "mydb")
        exporter = ExporterFactory.create(f"sqlite://{db_path}")
        assert isinstance(exporter, SQLiteExporter)
        # Factory strips sqlite:// scheme
        assert exporter.destination == db_path

    def test_create_passes_options(self, tmp_path):
        """Test factory passes options to exporter."""
        exporter = ExporterFactory.create(
            str(tmp_path / "output.csv"),
            delimiter=";",
            include_headers=False,
        )
        assert exporter.options["delimiter"] == ";"
        assert exporter.options["include_headers"] is False

    def test_create_raises_for_unknown_format(self):
        """Test factory raises ValueError for unknown format."""
        with pytest.raises(ValueError, match="Cannot determine export format"):
            ExporterFactory.create("/path/to/output.unknown")

    def test_create_raises_for_mysql(self):
        """Test factory raises NotImplementedError for MySQL."""
        with pytest.raises(NotImplementedError, match="MySQL export coming soon"):
            ExporterFactory.create("mysql://localhost/db")

    def test_create_handles_uppercase_extension(self, tmp_path):
        """Test factory handles uppercase extensions."""
        exporter = ExporterFactory.create(str(tmp_path / "output.CSV"))
        assert isinstance(exporter, CSVExporter)

    def test_create_handles_mixed_case_extension(self, tmp_path):
        """Test factory handles mixed case extensions."""
        exporter = ExporterFactory.create(str(tmp_path / "output.Json"))
        assert isinstance(exporter, JSONExporter)


class TestExporterFactoryPostgres:
    """Tests for PostgresExporter factory creation."""

    def test_create_postgres_exporter_postgresql_scheme(self):
        """Test factory creates PostgresExporter for postgresql:// scheme."""
        from quarry.tools.ship.exporters import PostgresExporter

        exporter = ExporterFactory.create("postgresql://user:pass@localhost:5432/db")
        assert isinstance(exporter, PostgresExporter)

    def test_create_postgres_exporter_postgres_scheme(self):
        """Test factory creates PostgresExporter for postgres:// scheme."""
        from quarry.tools.ship.exporters import PostgresExporter

        exporter = ExporterFactory.create("postgres://user:pass@localhost:5432/db")
        assert isinstance(exporter, PostgresExporter)
