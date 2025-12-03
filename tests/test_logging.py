"""Tests for logging configuration module."""

import json
import logging
import os
from unittest.mock import patch

import pytest

from quarry.lib.logging import JsonFormatter, setup_logging


class TestJsonFormatter:
    """Tests for JsonFormatter class."""

    def test_format_basic_message(self):
        """Test formatting a basic log message."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["level"] == "INFO"
        assert parsed["name"] == "test.logger"
        assert parsed["message"] == "Test message"
        assert "time" in parsed

    def test_format_with_args(self):
        """Test formatting a message with arguments."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=10,
            msg="Value is %s",
            args=("hello",),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["message"] == "Value is hello"
        assert parsed["level"] == "WARNING"

    def test_format_with_exception(self):
        """Test formatting a message with exception info."""
        formatter = JsonFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["level"] == "ERROR"
        assert "exc_info" in parsed
        assert "ValueError" in parsed["exc_info"]
        assert "Test error" in parsed["exc_info"]

    def test_format_non_ascii(self):
        """Test formatting with non-ASCII characters."""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="こんにちは世界",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)
        parsed = json.loads(result)

        assert parsed["message"] == "こんにちは世界"


class TestSetupLogging:
    """Tests for setup_logging function."""

    def teardown_method(self):
        """Clean up after each test."""
        # Reset root logger
        root = logging.getLogger()
        root.handlers.clear()
        root.setLevel(logging.WARNING)

    @patch.dict(os.environ, {"QUARRY_LOG_LEVEL": "DEBUG"}, clear=False)
    def test_debug_level(self):
        """Test setting DEBUG log level."""
        setup_logging()

        root = logging.getLogger()
        assert root.level == logging.DEBUG

    @patch.dict(os.environ, {"QUARRY_LOG_LEVEL": "ERROR"}, clear=False)
    def test_error_level(self):
        """Test setting ERROR log level."""
        setup_logging()

        root = logging.getLogger()
        assert root.level == logging.ERROR

    @patch.dict(os.environ, {"QUARRY_LOG_LEVEL": "info"}, clear=False)
    def test_case_insensitive_level(self):
        """Test that log level is case insensitive."""
        setup_logging()

        root = logging.getLogger()
        assert root.level == logging.INFO

    @patch.dict(os.environ, {"QUARRY_LOG_LEVEL": "INVALID"}, clear=False)
    def test_invalid_level_defaults_to_info(self):
        """Test that invalid log level defaults to INFO."""
        setup_logging()

        root = logging.getLogger()
        assert root.level == logging.INFO

    @patch.dict(os.environ, {}, clear=True)
    def test_default_level_is_info(self):
        """Test default log level is INFO when not set."""
        # Clear the env vars we care about
        os.environ.pop("QUARRY_LOG_LEVEL", None)
        os.environ.pop("QUARRY_LOG_JSON", None)

        setup_logging()

        root = logging.getLogger()
        assert root.level == logging.INFO

    @patch.dict(os.environ, {"QUARRY_LOG_JSON": "1"}, clear=False)
    def test_json_format_enabled(self):
        """Test JSON logging when QUARRY_LOG_JSON=1."""
        setup_logging()

        root = logging.getLogger()
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0].formatter, JsonFormatter)

    @patch.dict(os.environ, {"QUARRY_LOG_JSON": "0"}, clear=False)
    def test_json_format_disabled(self):
        """Test standard logging when QUARRY_LOG_JSON is not 1."""
        setup_logging()

        root = logging.getLogger()
        assert len(root.handlers) == 1
        assert not isinstance(root.handlers[0].formatter, JsonFormatter)

    def test_clears_existing_handlers(self):
        """Test that setup_logging clears existing handlers."""
        root = logging.getLogger()
        # Count handlers before adding our test handlers
        initial_count = len(root.handlers)
        root.addHandler(logging.StreamHandler())
        root.addHandler(logging.StreamHandler())
        assert len(root.handlers) == initial_count + 2

        with patch.dict(os.environ, {}, clear=False):
            setup_logging()

        # Should have exactly 1 handler after setup (our stderr handler)
        assert len(root.handlers) == 1

    def test_handler_writes_to_stderr(self):
        """Test that handler is configured for stderr."""
        import sys

        setup_logging()

        root = logging.getLogger()
        handler = root.handlers[0]
        assert handler.stream is sys.stderr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
