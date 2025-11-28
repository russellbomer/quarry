"""Logging configuration for Quarry.

Call `setup_logging()` early (e.g., CLI entry) to configure logging level and format
from environment variables:
- QUARRY_LOG_LEVEL (default INFO)
- QUARRY_LOG_JSON (1 to emit JSON)
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging() -> None:
    level_name = os.getenv("QUARRY_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    use_json = os.getenv("QUARRY_LOG_JSON") == "1"

    root = logging.getLogger()
    root.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root.handlers.clear()

    handler = logging.StreamHandler(stream=sys.stderr)
    if use_json:
        handler.setFormatter(JsonFormatter())
    else:
        fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))

    root.addHandler(handler)
