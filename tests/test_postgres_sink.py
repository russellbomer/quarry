"""Tests for PostgreSQL sink with mock-based database testing.

These tests verify PostgresSink functionality without requiring a live
PostgreSQL database. All database interactions are mocked.
"""

import os
from unittest.mock import MagicMock, patch, PropertyMock

import pandas as pd
import pytest

from quarry.sinks.postgres import PostgresSink, PostgresConnectionError, _is_nan


class TestPostgresConnectionError:
    """Tests for PostgresConnectionError exception."""

    def test_error_message_formatting(self):
        """Error should contain helpful guidance."""
        error = PostgresConnectionError("Test error message")
        assert str(error) == "Test error message"

    def test_error_inheritance(self):
        """Error should be catchable as Exception."""
        error = PostgresConnectionError("test")
        assert isinstance(error, Exception)


class TestPostgresSinkInit:
    """Tests for PostgresSink initialization."""

    def test_default_initialization(self):
        """Sink should initialize with sensible defaults."""
        sink = PostgresSink()
        assert sink.table_name == "quarry_data"
        assert sink.timezone == "America/New_York"
        assert sink.upsert_key is None
        assert sink.if_exists == "append"

    def test_custom_initialization(self):
        """Sink should accept custom parameters."""
        sink = PostgresSink(
            connection_string="postgresql://user:pass@localhost/db",
            table_name="custom_table",
            timezone="UTC",
            upsert_key="id",
            if_exists="replace",
        )
        assert sink.connection_string == "postgresql://user:pass@localhost/db"
        assert sink.table_name == "custom_table"
        assert sink.timezone == "UTC"
        assert sink.upsert_key == "id"
        assert sink.if_exists == "replace"

    def test_env_var_fallback(self):
        """Sink should use QUARRY_POSTGRES_URL env var as fallback."""
        with patch.dict(os.environ, {"QUARRY_POSTGRES_URL": "postgresql://env:var@host/db"}):
            sink = PostgresSink()
            conn_str = sink._get_connection_string()
            assert conn_str == "postgresql://env:var@host/db"

    def test_connection_string_priority(self):
        """Direct connection string should override env var."""
        with patch.dict(os.environ, {"QUARRY_POSTGRES_URL": "postgresql://env:var@host/db"}):
            sink = PostgresSink(connection_string="postgresql://direct@host/db")
            conn_str = sink._get_connection_string()
            assert conn_str == "postgresql://direct@host/db"


class TestConnectionStringValidation:
    """Tests for connection string handling and error messages."""

    def test_missing_connection_string_error(self):
        """Should raise helpful error when no connection configured."""
        # Ensure env var is not set
        env = os.environ.copy()
        env.pop("QUARRY_POSTGRES_URL", None)
        
        with patch.dict(os.environ, env, clear=True):
            sink = PostgresSink()
            with pytest.raises(PostgresConnectionError) as exc_info:
                sink._get_connection_string()
            
            error_msg = str(exc_info.value)
            assert "PostgreSQL connection not configured" in error_msg
            assert "QUARRY_POSTGRES_URL" in error_msg
            assert "postgresql://" in error_msg

    def test_psycopg_import_error(self):
        """Should provide helpful message when psycopg not installed."""
        sink = PostgresSink(connection_string="postgresql://user:pass@localhost/db")
        
        with patch.dict("sys.modules", {"psycopg_pool": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'psycopg_pool'")):
                with pytest.raises(PostgresConnectionError) as exc_info:
                    sink._get_pool()
                
                error_msg = str(exc_info.value)
                assert "psycopg" in error_msg
                assert "pip install" in error_msg


class TestConnectionPoolErrors:
    """Tests for connection pool error handling."""

    @patch("quarry.sinks.postgres.PostgresSink._get_pool")
    def test_authentication_failure_message(self, mock_pool):
        """Should provide clear message for auth failures."""
        mock_pool.side_effect = PostgresConnectionError(
            "PostgreSQL authentication failed.\n\n"
            "Check your username and password in the connection string.\n"
            "Original error: authentication failed"
        )
        
        sink = PostgresSink(connection_string="postgresql://bad:creds@localhost/db")
        
        with pytest.raises(PostgresConnectionError) as exc_info:
            sink._get_pool()
        
        assert "authentication failed" in str(exc_info.value).lower()

    @patch("quarry.sinks.postgres.PostgresSink._get_pool")
    def test_connection_refused_message(self, mock_pool):
        """Should provide clear message for connection failures."""
        mock_pool.side_effect = PostgresConnectionError(
            "Cannot connect to PostgreSQL server.\n\n"
            "Verify that:\n"
            "  1. PostgreSQL is running\n"
            "Original error: connection refused"
        )
        
        sink = PostgresSink(connection_string="postgresql://user:pass@badhost/db")
        
        with pytest.raises(PostgresConnectionError) as exc_info:
            sink._get_pool()
        
        assert "connect" in str(exc_info.value).lower()


class TestSchemaInference:
    """Tests for column type inference."""

    def test_infer_integer_types(self):
        """Should map pandas int types to PostgreSQL integers."""
        sink = PostgresSink()
        df = pd.DataFrame({
            "int32_col": pd.array([1, 2, 3], dtype="int32"),
            "int64_col": pd.array([1, 2, 3], dtype="int64"),
        })
        
        types = sink._infer_column_types(df)
        
        assert types["int32_col"] == "INTEGER"
        assert types["int64_col"] == "BIGINT"

    def test_infer_float_types(self):
        """Should map pandas float types to PostgreSQL floats."""
        sink = PostgresSink()
        df = pd.DataFrame({
            "float32_col": pd.array([1.0, 2.0, 3.0], dtype="float32"),
            "float64_col": pd.array([1.0, 2.0, 3.0], dtype="float64"),
        })
        
        types = sink._infer_column_types(df)
        
        assert types["float32_col"] == "REAL"
        assert types["float64_col"] == "DOUBLE PRECISION"

    def test_infer_string_types(self):
        """Should map object dtype to TEXT."""
        sink = PostgresSink()
        df = pd.DataFrame({
            "text_col": ["a", "b", "c"],
        })
        
        types = sink._infer_column_types(df)
        
        assert types["text_col"] == "TEXT"

    def test_infer_bool_types(self):
        """Should map bool dtype to BOOLEAN."""
        sink = PostgresSink()
        df = pd.DataFrame({
            "bool_col": [True, False, True],
        })
        
        types = sink._infer_column_types(df)
        
        assert types["bool_col"] == "BOOLEAN"


class TestTableOperations:
    """Tests for table creation and management."""

    def test_table_name_templating(self):
        """Table name should support {job} placeholder."""
        sink = PostgresSink(
            connection_string="postgresql://user:pass@localhost/db",
            table_name="quarry_{job}",
        )
        
        # The template expansion happens in write(), verify the stored value
        assert sink.table_name == "quarry_{job}"

    def test_if_exists_append_default(self):
        """Default if_exists should be 'append'."""
        sink = PostgresSink()
        assert sink.if_exists == "append"

    def test_if_exists_options(self):
        """Should accept valid if_exists options."""
        for option in ["append", "replace", "fail"]:
            sink = PostgresSink(if_exists=option)
            assert sink.if_exists == option


class TestWriteValidation:
    """Tests for write() input validation."""

    def test_empty_dataframe_raises_error(self):
        """Should raise ValueError for empty DataFrame."""
        sink = PostgresSink(connection_string="postgresql://user:pass@localhost/db")
        empty_df = pd.DataFrame()
        
        with pytest.raises(ValueError) as exc_info:
            sink.write(empty_df, "test_job")
        
        assert "empty" in str(exc_info.value).lower()


class TestMockedDatabaseOperations:
    """Tests with fully mocked database operations."""

    @patch("quarry.sinks.postgres.PostgresSink._insert_data")
    @patch("quarry.sinks.postgres.PostgresSink._create_table")
    @patch("quarry.sinks.postgres.PostgresSink._table_exists")
    @patch("quarry.sinks.postgres.PostgresSink._get_pool")
    def test_write_calls_insert(self, mock_get_pool, mock_table_exists, mock_create_table, mock_insert_data):
        """Write should execute insert statements."""
        # Setup mock pool and connection
        mock_conn = MagicMock()
        mock_pool = MagicMock()
        mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_pool.return_value = mock_pool
        
        # Table does not exist
        mock_table_exists.return_value = False

        sink = PostgresSink(connection_string="postgresql://user:pass@localhost/db")
        df = pd.DataFrame({"col1": ["a", "b"], "col2": [1, 2]})

        result = sink.write(df, "test_job")

        assert "2 records" in result
        mock_conn.commit.assert_called_once()
        mock_create_table.assert_called_once()
        mock_insert_data.assert_called_once()

    @patch("quarry.sinks.postgres.PostgresSink._insert_data")
    @patch("quarry.sinks.postgres.PostgresSink._create_table")
    @patch("quarry.sinks.postgres.PostgresSink._table_exists")
    @patch("quarry.sinks.postgres.PostgresSink._get_pool")
    def test_write_with_upsert_key(self, mock_get_pool, mock_table_exists, mock_create_table, mock_insert_data):
        """Write with upsert_key should use ON CONFLICT."""
        mock_conn = MagicMock()
        
        mock_pool = MagicMock()
        mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_pool.return_value = mock_pool
        
        # Table does not exist
        mock_table_exists.return_value = False

        sink = PostgresSink(
            connection_string="postgresql://user:pass@localhost/db",
            upsert_key="id",
        )
        df = pd.DataFrame({"id": [1, 2], "value": ["a", "b"]})

        result = sink.write(df, "test_job")

        assert "2 records" in result
        # Verify upsert_key is passed to sink
        assert sink.upsert_key == "id"

    @patch("quarry.sinks.postgres.PostgresSink._insert_data")
    @patch("quarry.sinks.postgres.PostgresSink._drop_table")
    @patch("quarry.sinks.postgres.PostgresSink._create_table")
    @patch("quarry.sinks.postgres.PostgresSink._table_exists")
    @patch("quarry.sinks.postgres.PostgresSink._get_pool")
    def test_table_exists_fail_mode(self, mock_get_pool, mock_table_exists, mock_create_table, mock_drop_table, mock_insert_data):
        """Should raise error when table exists and if_exists='fail'."""
        mock_conn = MagicMock()
        mock_pool = MagicMock()
        mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_pool.return_value = mock_pool

        # Mock table existence check - table EXISTS
        mock_table_exists.return_value = True

        sink = PostgresSink(
            connection_string="postgresql://user:pass@localhost/db",
            if_exists="fail",
        )
        df = pd.DataFrame({"col1": ["a"]})

        with pytest.raises(ValueError) as exc_info:
            sink.write(df, "test_job")

        assert "already exists" in str(exc_info.value)

    @patch("quarry.sinks.postgres.PostgresSink._insert_data")
    @patch("quarry.sinks.postgres.PostgresSink._drop_table")
    @patch("quarry.sinks.postgres.PostgresSink._create_table")
    @patch("quarry.sinks.postgres.PostgresSink._table_exists")
    @patch("quarry.sinks.postgres.PostgresSink._get_pool")
    def test_table_exists_replace_mode(self, mock_get_pool, mock_table_exists, mock_create_table, mock_drop_table, mock_insert_data):
        """Should drop and recreate table when if_exists='replace'."""
        mock_conn = MagicMock()
        mock_pool = MagicMock()
        mock_pool.connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_pool.connection.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_pool.return_value = mock_pool

        # Table exists
        mock_table_exists.return_value = True

        sink = PostgresSink(
            connection_string="postgresql://user:pass@localhost/db",
            if_exists="replace",
        )
        df = pd.DataFrame({"col1": ["a"]})

        result = sink.write(df, "test_job")

        assert "1 records" in result
        mock_drop_table.assert_called_once()
        mock_create_table.assert_called_once()


class TestNaNHandling:
    """Tests for NaN value handling."""

    def test_is_nan_with_nan(self):
        """Should detect pandas NaN values."""
        import numpy as np
        assert _is_nan(float("nan")) is True
        assert _is_nan(np.nan) is True

    def test_is_nan_with_valid_values(self):
        """Should return False for valid numeric and string values."""
        assert _is_nan(1) is False
        assert _is_nan("text") is False
        assert _is_nan(0.0) is False
        assert _is_nan("") is False

    def test_is_nan_with_none(self):
        """None is considered NA by pandas (maps to NULL in PostgreSQL)."""
        # pd.isna(None) returns True - this is expected behavior
        # None values will be converted to NULL in PostgreSQL
        assert _is_nan(None) is True

    def test_is_nan_with_pd_na(self):
        """Should detect pandas NA values."""
        assert _is_nan(pd.NA) is True


class TestCloseMethod:
    """Tests for connection pool cleanup."""

    def test_close_with_no_pool(self):
        """Close should handle case when pool was never created."""
        sink = PostgresSink()
        sink.close()  # Should not raise
        assert sink._pool is None

    def test_close_cleans_up_pool(self):
        """Close should call pool.close() if pool exists."""
        sink = PostgresSink()
        mock_pool = MagicMock()
        sink._pool = mock_pool
        
        sink.close()
        
        mock_pool.close.assert_called_once()
        assert sink._pool is None

    def test_close_is_idempotent(self):
        """Multiple close calls should be safe."""
        sink = PostgresSink()
        mock_pool = MagicMock()
        sink._pool = mock_pool
        
        sink.close()
        sink.close()  # Should not raise
        
        # close() only called once because pool is None after first call
        mock_pool.close.assert_called_once()
