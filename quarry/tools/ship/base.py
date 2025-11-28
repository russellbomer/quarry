"""Base exporter interface and factory."""

import json
from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path
from typing import Any


class Exporter(ABC):
    """
    Abstract base class for data exporters.

    All exporters must implement the export() method to write
    data from a JSONL file to their target destination.
    """

    def __init__(self, destination: str, **options: Any):
        """
        Initialize exporter.

        Args:
            destination: Target destination (file path, connection string, etc.)
            **options: Exporter-specific options
        """
        self.destination = destination
        self.options = options
        self.stats = {
            "records_read": 0,
            "records_written": 0,
            "records_failed": 0,
        }

    @abstractmethod
    def export(self, input_file: str | Path) -> dict[str, int]:
        """
        Export data from JSONL file to destination.

        Args:
            input_file: Path to input JSONL file

        Returns:
            Statistics dictionary with counts
        """
        pass

    def _read_jsonl(self, input_file: str | Path) -> Iterator[dict[str, Any]]:
        """
        Read records from JSONL file.

        Args:
            input_file: Path to JSONL file

        Yields:
            Dictionary records
        """
        input_path = Path(input_file)

        with input_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    record = json.loads(line)
                    self.stats["records_read"] += 1
                    yield record
                except json.JSONDecodeError:
                    self.stats["records_failed"] += 1
                    continue


class ExporterFactory:
    """
    Factory for creating appropriate exporters based on destination.

    Supports automatic format detection from:
    - File extensions (.csv, .json, .db, .sqlite)
    - Connection strings (postgresql://, mysql://, sqlite://)
    """

    @staticmethod
    def create(destination: str, **options: Any) -> Exporter:
        """
        Create appropriate exporter for destination.

        Args:
            destination: Target destination
            **options: Exporter-specific options

        Returns:
            Configured Exporter instance

        Raises:
            ValueError: If destination format cannot be determined
        """
        from .exporters import CSVExporter, JSONExporter, PostgresExporter, SQLiteExporter

        dest_lower = destination.lower()

        # File-based exporters
        if dest_lower.endswith(".csv"):
            return CSVExporter(destination, **options)

        elif dest_lower.endswith(".json"):
            return JSONExporter(destination, **options)

        elif dest_lower.endswith((".db", ".sqlite", ".sqlite3")):
            return SQLiteExporter(destination, **options)

        # Connection string-based exporters
        elif dest_lower.startswith("sqlite://"):
            # Remove scheme for file path
            db_path = destination[9:]  # Remove "sqlite://"
            return SQLiteExporter(db_path, **options)

        elif dest_lower.startswith(("postgresql://", "postgres://")):
            return PostgresExporter(destination, **options)

        elif dest_lower.startswith("mysql://"):
            raise NotImplementedError("MySQL export coming soon")

        else:
            raise ValueError(
                f"Cannot determine export format for: {destination}\n"
                f"Supported: .csv, .json, .db/.sqlite, sqlite://, postgresql://"
            )
