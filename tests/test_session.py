"""Tests for session state management module."""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from quarry.lib import session


class TestSessionManagement:
    """Tests for session file operations."""

    @pytest.fixture(autouse=True)
    def temp_session_file(self, tmp_path):
        """Use a temporary session file for each test."""
        temp_file = tmp_path / ".quarry" / "session.json"
        with patch.object(session, "_SESSION_FILE", temp_file):
            yield temp_file

    def test_ensure_session_dir_creates_directory(self, temp_session_file):
        """Test that _ensure_session_dir creates parent directory."""
        assert not temp_session_file.parent.exists()

        session._ensure_session_dir()

        assert temp_session_file.parent.exists()

    def test_load_session_returns_empty_when_no_file(self, temp_session_file):
        """Test loading session when file doesn't exist."""
        result = session._load_session()
        assert result == {}

    def test_load_session_returns_data(self, temp_session_file):
        """Test loading existing session data."""
        temp_session_file.parent.mkdir(parents=True, exist_ok=True)
        temp_session_file.write_text('{"key": "value"}', encoding="utf-8")

        result = session._load_session()

        assert result == {"key": "value"}

    def test_load_session_handles_invalid_json(self, temp_session_file):
        """Test loading session with invalid JSON."""
        temp_session_file.parent.mkdir(parents=True, exist_ok=True)
        temp_session_file.write_text("not valid json", encoding="utf-8")

        result = session._load_session()

        assert result == {}

    def test_load_session_handles_non_dict(self, temp_session_file):
        """Test loading session with non-dict JSON."""
        temp_session_file.parent.mkdir(parents=True, exist_ok=True)
        temp_session_file.write_text('["list", "not", "dict"]', encoding="utf-8")

        result = session._load_session()

        assert result == {}

    def test_save_session_creates_file(self, temp_session_file):
        """Test saving session creates file."""
        data = {"test": "data"}

        session._save_session(data)

        assert temp_session_file.exists()
        content = json.loads(temp_session_file.read_text(encoding="utf-8"))
        assert content == data


class TestSchemaSession:
    """Tests for schema session functions."""

    @pytest.fixture(autouse=True)
    def temp_session_file(self, tmp_path):
        """Use a temporary session file for each test."""
        temp_file = tmp_path / ".quarry" / "session.json"
        with patch.object(session, "_SESSION_FILE", temp_file):
            yield temp_file

    def test_set_last_schema_basic(self, temp_session_file):
        """Test setting last schema with minimal args."""
        session.set_last_schema("/path/to/schema.yml")

        result = session.get_last_schema()

        assert result is not None
        assert "schema.yml" in result["path"]
        assert result["url"] is None
        assert "timestamp" in result

    def test_set_last_schema_with_url(self, temp_session_file):
        """Test setting last schema with URL."""
        session.set_last_schema("/path/to/schema.yml", url="https://example.com")

        result = session.get_last_schema()

        assert result["url"] == "https://example.com"

    def test_set_last_schema_with_metadata(self, temp_session_file):
        """Test setting last schema with metadata."""
        metadata = {"records": 100, "fields": ["title", "url"]}
        session.set_last_schema("/path/to/schema.yml", metadata=metadata)

        result = session.get_last_schema()

        assert result["metadata"] == metadata

    def test_get_last_schema_returns_none_when_empty(self, temp_session_file):
        """Test getting last schema when none set."""
        result = session.get_last_schema()
        assert result is None

    def test_set_last_schema_overwrites_previous(self, temp_session_file):
        """Test that setting schema overwrites previous."""
        session.set_last_schema("/first/schema.yml")
        session.set_last_schema("/second/schema.yml")

        result = session.get_last_schema()

        assert "second" in result["path"]


class TestAnalysisSession:
    """Tests for analysis session functions."""

    @pytest.fixture(autouse=True)
    def temp_session_file(self, tmp_path):
        """Use a temporary session file for each test."""
        temp_file = tmp_path / ".quarry" / "session.json"
        with patch.object(session, "_SESSION_FILE", temp_file):
            yield temp_file

    def test_set_last_analysis(self, temp_session_file):
        """Test setting last analysis data."""
        data = {"url": "https://example.com", "framework": "react"}

        session.set_last_analysis(data)
        result = session.get_last_analysis()

        assert result["url"] == "https://example.com"
        assert result["framework"] == "react"
        assert "timestamp" in result

    def test_get_last_analysis_returns_none_when_empty(self, temp_session_file):
        """Test getting last analysis when none set."""
        result = session.get_last_analysis()
        assert result is None

    def test_set_last_analysis_does_not_mutate_input(self, temp_session_file):
        """Test that set_last_analysis doesn't modify input dict."""
        data = {"key": "value"}
        original_keys = set(data.keys())

        session.set_last_analysis(data)

        # Original dict should not have timestamp added
        assert set(data.keys()) == original_keys


class TestOutputSession:
    """Tests for output session functions."""

    @pytest.fixture(autouse=True)
    def temp_session_file(self, tmp_path):
        """Use a temporary session file for each test."""
        temp_file = tmp_path / ".quarry" / "session.json"
        with patch.object(session, "_SESSION_FILE", temp_file):
            yield temp_file

    def test_set_last_output(self, temp_session_file):
        """Test setting last output data."""
        session.set_last_output("/output/data.jsonl", "jsonl", 500)

        result = session.get_last_output()

        assert result is not None
        assert "data.jsonl" in result["path"]
        assert result["format"] == "jsonl"
        assert result["record_count"] == 500
        assert "timestamp" in result

    def test_get_last_output_returns_none_when_empty(self, temp_session_file):
        """Test getting last output when none set."""
        result = session.get_last_output()
        assert result is None

    def test_multiple_session_types_coexist(self, temp_session_file):
        """Test that different session types don't overwrite each other."""
        session.set_last_schema("/path/schema.yml")
        session.set_last_analysis({"url": "https://example.com"})
        session.set_last_output("/output/data.csv", "csv", 100)

        schema = session.get_last_schema()
        analysis = session.get_last_analysis()
        output = session.get_last_output()

        assert schema is not None
        assert analysis is not None
        assert output is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
