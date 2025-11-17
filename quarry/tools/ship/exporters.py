"""Concrete exporter implementations."""

import csv
import json
import sqlite3
from pathlib import Path

from .base import Exporter


class CSVExporter(Exporter):
    """
    Export data to CSV format.

    Options:
        delimiter: Column delimiter (default: ',')
        quoting: CSV quoting style (default: QUOTE_MINIMAL)
        encoding: File encoding (default: 'utf-8')
        exclude_meta: Exclude _meta field (default: True)
    """

    def export(self, input_file: str | Path) -> dict[str, int]:
        """Export JSONL to CSV."""
        output_path = Path(self.destination)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Options
        delimiter = self.options.get("delimiter", ",")
        quoting = self.options.get("quoting", csv.QUOTE_MINIMAL)
        encoding = self.options.get("encoding", "utf-8")
        exclude_meta = self.options.get("exclude_meta", True)

        # Collect all records to determine headers
        records: list[dict[str, object]] = []
        for record in self._read_jsonl(input_file):
            if exclude_meta and "_meta" in record:
                record = {k: v for k, v in record.items() if k != "_meta"}
            records.append(record)

        if not records:
            # No records, create empty file
            output_path.write_text("", encoding=encoding)
            return self.stats

        # Determine headers from all records
        headers_set: set[str] = set()
        for record in records:
            headers_set.update(record.keys())
        headers: list[str] = sorted(headers_set)  # Consistent order

        # Write CSV
        with output_path.open("w", encoding=encoding, newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=headers,
                delimiter=delimiter,
                quoting=quoting,
            )

            writer.writeheader()
            for record in records:
                try:
                    # Convert non-string values
                    row: dict[str, str] = {}
                    for key in headers:
                        value = record.get(key)
                        if value is None:
                            row[key] = ""
                        elif isinstance(value, (list, dict)):
                            row[key] = json.dumps(value)
                        else:
                            row[key] = str(value)

                    writer.writerow(row)
                    self.stats["records_written"] += 1
                except Exception:
                    self.stats["records_failed"] += 1

        return self.stats


class JSONExporter(Exporter):
    """
    Export data to JSON array format.

    Options:
        pretty: Pretty-print JSON (default: False)
        indent: Indentation spaces if pretty (default: 2)
        exclude_meta: Exclude _meta field (default: False)
    """

    def export(self, input_file: str | Path) -> dict[str, int]:
        """Export JSONL to JSON array."""
        output_path = Path(self.destination)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Options
        pretty = self.options.get("pretty", False)
        indent = self.options.get("indent", 2) if pretty else None
        exclude_meta = self.options.get("exclude_meta", False)

        # Collect all records
        records = []
        for record in self._read_jsonl(input_file):
            if exclude_meta and "_meta" in record:
                record = {k: v for k, v in record.items() if k != "_meta"}

            records.append(record)
            self.stats["records_written"] += 1

        # Write JSON array
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(records, f, indent=indent, default=str)

        return self.stats


class SQLiteExporter(Exporter):
    """
    Export data to SQLite database.

    Options:
        table_name: Table name (default: 'records')
        if_exists: 'replace', 'append', or 'fail' (default: 'replace')
        exclude_meta: Exclude _meta field (default: True)
    """

    def export(self, input_file: str | Path) -> dict[str, int]:
        """Export JSONL to SQLite database."""
        db_path = Path(self.destination)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Options
        table_name = self.options.get("table_name", "records")
        if_exists = self.options.get("if_exists", "replace")
        exclude_meta = self.options.get("exclude_meta", True)

        # Validate table name
        if not table_name.isidentifier():
            raise ValueError(f"Invalid table name: {table_name}")

        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            # Read first batch to determine schema
            records: list[dict[str, object]] = []
            columns: set[str] = set()

            for record in self._read_jsonl(input_file):
                if exclude_meta and "_meta" in record:
                    record = {k: v for k, v in record.items() if k != "_meta"}

                columns.update(record.keys())
                records.append(record)

            if not records:
                conn.close()
                return self.stats

            columns_list: list[str] = sorted(columns)  # Consistent order

            # Handle if_exists
            if if_exists == "replace":
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            elif if_exists == "fail":
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
                )
                if cursor.fetchone():
                    raise ValueError(f"Table '{table_name}' already exists")

            # Create table
            column_defs = ", ".join(f'"{col}" TEXT' for col in columns)
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({column_defs})")

            # Insert records
            placeholders = ", ".join("?" * len(columns_list))
            column_names = ", ".join(f'"{col}"' for col in columns_list)
            insert_sql = f'INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})'

            for record in records:
                try:
                    values: list[str | None] = []
                    for col in columns_list:
                        value = record.get(col)
                        if value is None:
                            values.append(None)
                        elif isinstance(value, (list, dict)):
                            values.append(json.dumps(value))
                        else:
                            values.append(str(value))

                    cursor.execute(insert_sql, values)
                    self.stats["records_written"] += 1
                except Exception:
                    self.stats["records_failed"] += 1

            conn.commit()

        finally:
            conn.close()

        return self.stats
