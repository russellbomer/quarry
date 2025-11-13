"""Tests for state management."""

import sqlite3
import tempfile
from pathlib import Path

from quarry.state import load_cursor, save_cursor, upsert_items

# Test constants
EXPECTED_NEW_COUNT_FIRST = 2
EXPECTED_NEW_COUNT_SECOND = 1
EXPECTED_TOTAL_ITEMS = 3


def test_upsert_items_deduplication() -> None:
    """Test that upsert_items only counts new inserts, not updates."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name

    try:
        # First insert
        records1 = [
            {"id": "001", "title": "Item 1"},
            {"id": "002", "title": "Item 2"},
        ]
        new_count1 = upsert_items("test_job", records1, db_path=db_path)
        assert new_count1 == EXPECTED_NEW_COUNT_FIRST

        # Second insert with duplicates
        records2 = [
            {"id": "001", "title": "Item 1 Updated"},  # Duplicate
            {"id": "003", "title": "Item 3"},  # New
        ]
        new_count2 = upsert_items("test_job", records2, db_path=db_path)
        assert new_count2 == EXPECTED_NEW_COUNT_SECOND  # Only one new insert

        # Verify all three items exist
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id FROM items WHERE job = ? ORDER BY id", ("test_job",)
        ).fetchall()
        conn.close()
        assert len(rows) == EXPECTED_TOTAL_ITEMS
        assert [r["id"] for r in rows] == ["001", "002", "003"]

    finally:
        Path(db_path).unlink(missing_ok=True)


def test_cursor_save_load() -> None:
    """Test cursor save and load functionality."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name

    try:
        # Initially no cursor
        cursor = load_cursor("test_job", db_path=db_path)
        assert cursor is None

        # Save cursor
        save_cursor("test_job", "cursor-123", db_path=db_path)
        cursor = load_cursor("test_job", db_path=db_path)
        assert cursor == "cursor-123"

        # Update cursor
        save_cursor("test_job", "cursor-456", db_path=db_path)
        cursor = load_cursor("test_job", db_path=db_path)
        assert cursor == "cursor-456"

    finally:
        Path(db_path).unlink(missing_ok=True)
