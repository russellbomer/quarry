"""PostgreSQL sink implementation.

Provides database export capabilities with:
- Connection string configuration (CLI flags or environment variables)
- Automatic table creation with schema inference
- Upsert capability for incremental extraction runs
- Connection pooling for performance
- Clear error messages for connection failures
"""

import math
import os
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from quarry.transforms.base import Frame

# Type alias for psycopg connection (lazy import)
PsycopgConnection = Any


class PostgresConnectionError(Exception):
    """Raised when PostgreSQL connection fails with helpful guidance."""

    pass


class PostgresSink:
    """PostgreSQL database sink with upsert support and connection pooling.

    Supports connection via:
    - Direct connection string: postgresql://user:pass@host:port/database
    - Environment variable: QUARRY_POSTGRES_URL
    - Individual parameters: host, port, database, user, password
    """

    def __init__(
        self,
        connection_string: str | None = None,
        table_name: str = "quarry_data",
        timezone: str = "America/New_York",
        upsert_key: str | None = None,
        if_exists: str = "append",  # append, replace, fail
    ):
        """Initialize PostgreSQL sink.

        Args:
            connection_string: PostgreSQL connection URL (postgresql://...).
                              Falls back to QUARRY_POSTGRES_URL env var.
            table_name: Target table name. Supports {job} placeholder.
            timezone: Timezone for timestamp generation.
            upsert_key: Column name for upsert conflict resolution.
                       If None, simple inserts are used.
            if_exists: Behavior when table exists:
                      - 'append': Add rows to existing table (default)
                      - 'replace': Drop and recreate table
                      - 'fail': Raise error if table exists
        """
        self.connection_string = connection_string or os.environ.get("QUARRY_POSTGRES_URL")
        self.table_name = table_name
        self.timezone = timezone
        self.upsert_key = upsert_key
        self.if_exists = if_exists
        self._pool: Any = None

    def _get_connection_string(self) -> str:
        """Get connection string with helpful error if missing."""
        if self.connection_string:
            return self.connection_string

        # Check environment variable
        env_url = os.environ.get("QUARRY_POSTGRES_URL")
        if env_url:
            return env_url

        raise PostgresConnectionError(
            "PostgreSQL connection not configured.\n\n"
            "Please provide a connection string using one of these methods:\n"
            "  1. Pass directly: PostgresSink(connection_string='postgresql://...')\n"
            "  2. Set environment variable: export QUARRY_POSTGRES_URL='postgresql://...'\n"
            "  3. Use ship command: quarry ship data.jsonl postgres://user:pass@host/db\n\n"
            "Connection string format:\n"
            "  postgresql://username:password@hostname:5432/database\n\n"
            "Example:\n"
            "  postgresql://quarry:secret@localhost:5432/extractions"
        )

    def _get_pool(self) -> Any:
        """Get or create connection pool with helpful error handling."""
        if self._pool is not None:
            return self._pool

        try:
            import psycopg_pool  # noqa: PLC0415
        except ImportError as err:
            raise PostgresConnectionError(
                "PostgreSQL support requires the 'psycopg' package.\n\n"
                "Install it with:\n"
                "  pip install 'psycopg[binary,pool]'\n\n"
                "Or add to your requirements.txt:\n"
                "  psycopg[binary,pool]"
            ) from err

        conn_str = self._get_connection_string()

        try:
            self._pool = psycopg_pool.ConnectionPool(
                conn_str,
                min_size=1,
                max_size=5,
                timeout=30,
            )
            # Test the connection
            with self._pool.connection() as conn:
                conn.execute("SELECT 1")
            return self._pool
        except Exception as e:
            error_msg = str(e).lower()

            # Provide specific guidance based on error type
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
                    f"  3. Firewall rules allow the connection\n"
                    f"  4. PostgreSQL is configured to accept connections\n\n"
                    f"Original error: {e}"
                ) from e
            elif "database" in error_msg and "does not exist" in error_msg:
                raise PostgresConnectionError(
                    f"PostgreSQL database does not exist.\n\n"
                    f"Create the database first with:\n"
                    f"  createdb <database_name>\n\n"
                    f"Or connect with psql and run:\n"
                    f"  CREATE DATABASE <database_name>;\n\n"
                    f"Original error: {e}"
                ) from e
            else:
                raise PostgresConnectionError(
                    f"PostgreSQL connection failed.\n\n"
                    f"Error: {e}\n\n"
                    f"Connection string format:\n"
                    f"  postgresql://username:password@hostname:5432/database"
                ) from e

    def _infer_column_types(self, df: Frame) -> dict[str, str]:
        """Infer PostgreSQL column types from DataFrame dtypes."""
        type_mapping = {
            "int64": "BIGINT",
            "int32": "INTEGER",
            "float64": "DOUBLE PRECISION",
            "float32": "REAL",
            "bool": "BOOLEAN",
            "datetime64[ns]": "TIMESTAMP",
            "object": "TEXT",
        }

        columns = {}
        for col in df.columns:
            dtype_str = str(df[col].dtype)
            pg_type = type_mapping.get(dtype_str, "TEXT")
            columns[col] = pg_type

        return columns

    def _create_table(self, conn: Any, table: str, columns: dict[str, str]) -> None:
        """Create table with inferred schema."""
        from psycopg import sql  # noqa: PLC0415

        # Build column definitions
        col_defs = []
        for col_name, col_type in columns.items():
            # Quote column names to handle special characters
            col_defs.append(sql.SQL("{} {}").format(sql.Identifier(col_name), sql.SQL(col_type)))

        # Add primary key if upsert key specified
        if self.upsert_key and self.upsert_key in columns:
            col_defs.append(sql.SQL("PRIMARY KEY ({})").format(sql.Identifier(self.upsert_key)))

        create_sql = sql.SQL("CREATE TABLE IF NOT EXISTS {} ({})").format(
            sql.Identifier(table),
            sql.SQL(", ").join(col_defs),
        )

        conn.execute(create_sql)

    def _table_exists(self, conn: Any, table: str) -> bool:
        """Check if table exists."""
        result = conn.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)",
            (table,),
        ).fetchone()
        return result[0] if result else False

    def _drop_table(self, conn: Any, table: str) -> None:
        """Drop table if exists."""
        from psycopg import sql  # noqa: PLC0415

        conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table)))

    def write(self, df: Frame, job: str) -> str:
        """Write DataFrame to PostgreSQL table.

        Args:
            df: DataFrame to write
            job: Job name (used for table name placeholder)

        Returns:
            Summary string with record count

        Raises:
            ValueError: If DataFrame is empty
            PostgresConnectionError: If connection fails
        """
        if df.empty:
            raise ValueError("Cannot write empty DataFrame")

        # Expand table name template
        try:
            tz = ZoneInfo(self.timezone)
        except Exception:
            tz = ZoneInfo("America/New_York")

        now = datetime.now(tz)
        table = now.strftime(self.table_name)
        table = table.replace("{job}", job)

        # Sanitize table name (basic safety)
        table = "".join(c for c in table if c.isalnum() or c == "_")

        pool = self._get_pool()
        columns = self._infer_column_types(df)

        with pool.connection() as conn:
            # Handle if_exists behavior
            table_exists = self._table_exists(conn, table)

            if table_exists:
                if self.if_exists == "fail":
                    raise ValueError(f"Table '{table}' already exists and if_exists='fail'")
                elif self.if_exists == "replace":
                    self._drop_table(conn, table)
                    self._create_table(conn, table, columns)
                # else: append - table already exists, just insert
            else:
                self._create_table(conn, table, columns)

            # Insert data
            self._insert_data(conn, table, df, columns)
            conn.commit()

        return f"postgresql://{table} ({len(df)} records)"

    def _insert_data(self, conn: Any, table: str, df: Frame, columns: dict[str, str]) -> None:
        """Insert DataFrame rows into table."""
        from psycopg import sql  # noqa: PLC0415

        col_names = list(columns.keys())
        col_identifiers = [sql.Identifier(c) for c in col_names]

        if self.upsert_key and self.upsert_key in col_names:
            # Upsert (INSERT ... ON CONFLICT DO UPDATE)
            update_cols = [c for c in col_names if c != self.upsert_key]
            update_set = sql.SQL(", ").join(
                sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(c), sql.Identifier(c))
                for c in update_cols
            )

            insert_sql = sql.SQL(
                "INSERT INTO {} ({}) VALUES ({}) ON CONFLICT ({}) DO UPDATE SET {}"
            ).format(
                sql.Identifier(table),
                sql.SQL(", ").join(col_identifiers),
                sql.SQL(", ").join(sql.Placeholder() for _ in col_names),
                sql.Identifier(self.upsert_key),
                update_set,
            )
        else:
            # Simple insert
            insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table),
                sql.SQL(", ").join(col_identifiers),
                sql.SQL(", ").join(sql.Placeholder() for _ in col_names),
            )

        # Execute batch insert
        with conn.cursor() as cur:
            for _, row in df.iterrows():
                values = [row[col] if not _is_nan(row[col]) else None for col in col_names]
                cur.execute(insert_sql, values)

    def close(self) -> None:
        """Close connection pool."""
        if self._pool is not None:
            self._pool.close()
            self._pool = None


def _is_nan(value: Any) -> bool:
    """Check if value is NaN (pandas compatibility)."""
    try:
        import pandas as pd  # noqa: PLC0415

        return bool(pd.isna(value))
    except (ImportError, TypeError):
        return isinstance(value, float) and math.isnan(value)
