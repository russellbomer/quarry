"""Concrete exporter implementations."""

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any

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


class PostgresExporter(Exporter):
    """
    Export data to PostgreSQL database.

    Options:
        table_name: Table name (default: 'records')
        if_exists: 'replace', 'append', or 'fail' (default: 'append')
        upsert_key: Column for upsert conflict resolution (default: None)
        exclude_meta: Exclude _meta field (default: True)
    """

    def export(self, input_file: str | Path) -> dict[str, int]:
        """Export JSONL to PostgreSQL database."""
        try:
            import psycopg  # noqa: PLC0415
            import psycopg.sql as sql  # noqa: PLC0415, PLR0402
        except ImportError as err:
            from quarry.sinks.postgres import PostgresConnectionError

            raise PostgresConnectionError(
                "PostgreSQL support requires the 'psycopg' package.\n\n"
                "Install it with:\n"
                "  pip install 'psycopg[binary]'\n\n"
                "Or add to your requirements.txt:\n"
                "  psycopg[binary]"
            ) from err

        # Options
        table_name = self.options.get("table_name", "records")
        if_exists = self.options.get("if_exists", "append")
        upsert_key = self.options.get("upsert_key")
        exclude_meta = self.options.get("exclude_meta", True)

        # Sanitize table name
        table_name = "".join(c for c in table_name if c.isalnum() or c == "_")

        try:
            conn = psycopg.connect(self.destination)
        except Exception as e:
            from quarry.sinks.postgres import PostgresConnectionError

            error_msg = str(e).lower()

            if "authentication failed" in error_msg or "password" in error_msg:
                raise PostgresConnectionError(
                    f"PostgreSQL authentication failed.\n\n"
                    f"Check your username and password in the connection string.\n"
                    f"Original error: {e}"
                ) from e
            elif "could not connect" in error_msg or "connection refused" in error_msg:
                raise PostgresConnectionError(
                    f"Cannot connect to PostgreSQL server.\n\n"
                    f"Verify that:\n"
                    f"  1. PostgreSQL is running on the specified host and port\n"
                    f"  2. The hostname is correct and reachable\n"
                    f"  3. Firewall rules allow the connection\n\n"
                    f"Original error: {e}"
                ) from e
            else:
                raise PostgresConnectionError(f"PostgreSQL connection failed: {e}") from e

        try:
            cursor = conn.cursor()

            # Read records and determine schema
            records: list[dict[str, Any]] = []
            columns: set[str] = set()

            for record in self._read_jsonl(input_file):
                if exclude_meta and "_meta" in record:
                    record = {k: v for k, v in record.items() if k != "_meta"}
                columns.update(record.keys())
                records.append(record)

            if not records:
                conn.close()
                return self.stats

            columns_list: list[str] = sorted(columns)

            # Check if table exists
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
                (table_name,),
            )
            table_exists = cursor.fetchone()[0]

            # Handle if_exists
            if table_exists:
                if if_exists == "fail":
                    raise ValueError(f"Table '{table_name}' already exists")
                elif if_exists == "replace":
                    cursor.execute(
                        sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table_name))
                    )
                    table_exists = False

            # Create table if needed
            if not table_exists:
                col_defs = sql.SQL(", ").join(
                    sql.SQL("{} TEXT").format(sql.Identifier(col)) for col in columns_list
                )
                create_sql = sql.SQL("CREATE TABLE {} ({})").format(
                    sql.Identifier(table_name),
                    col_defs,
                )
                cursor.execute(create_sql)

            # Build insert SQL
            col_identifiers = [sql.Identifier(c) for c in columns_list]

            if upsert_key and upsert_key in columns_list:
                # Upsert with ON CONFLICT
                update_cols = [c for c in columns_list if c != upsert_key]
                update_set = sql.SQL(", ").join(
                    sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(c), sql.Identifier(c))
                    for c in update_cols
                )
                insert_sql = sql.SQL(
                    "INSERT INTO {} ({}) VALUES ({}) ON CONFLICT ({}) DO UPDATE SET {}"
                ).format(
                    sql.Identifier(table_name),
                    sql.SQL(", ").join(col_identifiers),
                    sql.SQL(", ").join(sql.Placeholder() for _ in columns_list),
                    sql.Identifier(upsert_key),
                    update_set,
                )
            else:
                insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(table_name),
                    sql.SQL(", ").join(col_identifiers),
                    sql.SQL(", ").join(sql.Placeholder() for _ in columns_list),
                )

            # Insert records
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
