"""Tests for generic transform module."""

import pandas as pd
import pytest

from quarry.transforms.generic import normalize


class TestNormalize:
    """Tests for the normalize function."""

    def test_empty_records(self):
        """Test normalization of empty record list."""
        result = normalize([])

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    def test_basic_records(self):
        """Test normalization of basic records."""
        records = [
            {"id": "1", "title": "First", "url": "https://example.com/1"},
            {"id": "2", "title": "Second", "url": "https://example.com/2"},
        ]

        result = normalize(records)

        assert len(result) == 2
        assert list(result["id"]) == ["1", "2"]
        assert list(result["title"]) == ["First", "Second"]

    def test_adds_missing_id_from_url(self):
        """Test that missing id is derived from url."""
        records = [
            {"title": "First", "url": "https://example.com/1"},
            {"title": "Second", "url": "https://example.com/2"},
        ]

        result = normalize(records)

        assert "id" in result.columns
        assert list(result["id"]) == ["https://example.com/1", "https://example.com/2"]

    def test_adds_missing_id_as_index_when_no_url(self):
        """Test that missing id uses index when url also missing."""
        records = [
            {"title": "First"},
            {"title": "Second"},
        ]

        result = normalize(records)

        assert "id" in result.columns
        # Should be index as string
        assert list(result["id"]) == ["0", "1"]

    def test_adds_missing_url_column(self):
        """Test that missing url column is added as empty string."""
        records = [
            {"id": "1", "title": "First"},
        ]

        result = normalize(records)

        assert "url" in result.columns
        assert result["url"].iloc[0] == ""

    def test_adds_missing_title_column(self):
        """Test that missing title column is added as empty string."""
        records = [
            {"id": "1", "url": "https://example.com"},
        ]

        result = normalize(records)

        assert "title" in result.columns
        assert result["title"].iloc[0] == ""

    def test_fills_na_values(self):
        """Test that NA values are filled with empty string."""
        records = [
            {"id": "1", "title": None, "url": "https://example.com"},
        ]

        result = normalize(records)

        assert result["title"].iloc[0] == ""

    def test_preserves_extra_columns(self):
        """Test that extra columns beyond id/title/url are preserved."""
        records = [
            {
                "id": "1",
                "title": "First",
                "url": "https://example.com",
                "author": "John",
                "date": "2024-01-01",
            }
        ]

        result = normalize(records)

        assert "author" in result.columns
        assert "date" in result.columns
        assert result["author"].iloc[0] == "John"

    def test_handles_mixed_records(self):
        """Test normalization with records having different keys."""
        records = [
            {"id": "1", "title": "First"},
            {"id": "2", "url": "https://example.com"},
            {"title": "Third", "author": "Jane"},
        ]

        result = normalize(records)

        assert len(result) == 3
        assert "id" in result.columns
        assert "title" in result.columns
        assert "url" in result.columns
        assert "author" in result.columns

    def test_single_record(self):
        """Test normalization of a single record."""
        records = [{"id": "1", "title": "Only One", "url": "https://example.com"}]

        result = normalize(records)

        assert len(result) == 1
        assert result["title"].iloc[0] == "Only One"

    def test_numeric_values(self):
        """Test that numeric values are preserved."""
        records = [
            {"id": "1", "title": "Test", "url": "https://example.com", "count": 42}
        ]

        result = normalize(records)

        assert result["count"].iloc[0] == 42


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
