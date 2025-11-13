"""Tests for connector parsers."""

import pytest

import quarry.connectors.custom as custom_mod
from quarry.connectors import custom, fda, nws

# Test constants to avoid magic numbers
MIN_EXPECTED_RECORDS = 3
MIN_RECORDS_FOR_CURSOR_TEST = 2


def test_fda_connector_offline() -> None:
    """Test FDA connector in offline mode with real URL parsing."""
    entry_url = "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts"
    connector = fda.FDAConnector(entry_url=entry_url)
    records, next_cursor = connector.collect(cursor=None, max_items=10, offline=True)

    assert len(records) >= MIN_EXPECTED_RECORDS
    assert next_cursor is not None

    # Check first record has required keys
    first = records[0]
    assert "id" in first
    assert "title" in first
    assert "url" in first
    assert first["id"] == next_cursor  # Next cursor should be first ID

    # Verify URLs are absolute
    for rec in records:
        assert rec["url"].startswith("http")
        assert rec["url"].startswith(entry_url) or rec["url"].startswith("https://www.fda.gov")

    # Verify IDs are slugs (not synthetic FDA-001 patterns)
    for rec in records:
        assert "id" in rec
        assert rec["id"]
        # IDs should be slugs, not synthetic patterns
        assert not rec["id"].startswith("FDA-")

    # Verify IDs match slug extraction (last path segment)
    # First record should have slug "acme-foods-allergy-alert-undeclared-wheat-choc-bars"
    assert records[0]["id"] == "acme-foods-allergy-alert-undeclared-wheat-choc-bars"
    assert records[1]["id"] == "contoso-dairy-recall-foreign-object-plastic-fragments"


def test_nws_connector_offline() -> None:
    """Test NWS connector in offline mode."""
    entry_url = "https://alerts.weather.gov/cap/us.php?x=0"
    connector = nws.NWSConnector(entry_url=entry_url)
    records, next_cursor = connector.collect(cursor=None, max_items=10, offline=True)

    assert len(records) > 0
    assert next_cursor is not None

    # Check first record has required keys
    first = records[0]
    assert "id" in first
    assert "headline" in first or "title" in first
    assert first["id"] == next_cursor

    # Check all records have IDs
    for rec in records:
        assert "id" in rec
        assert rec["id"]


def test_fda_cursor_filtering() -> None:
    """Test that cursor stops collection at seen item."""
    entry_url = "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts"
    connector = fda.FDAConnector(entry_url=entry_url)
    records, _ = connector.collect(cursor=None, max_items=10, offline=True)

    if len(records) >= MIN_RECORDS_FOR_CURSOR_TEST:
        cursor_id = records[1]["id"]
        filtered_records, _ = connector.collect(cursor=cursor_id, max_items=10, offline=True)
        # Should stop before cursor, so only first item
        assert len(filtered_records) == 1
        assert filtered_records[0]["id"] == records[0]["id"]


def test_fda_deprecation_warning() -> None:
    """Test that FDAConnector without entry_url emits DeprecationWarning."""
    with pytest.warns(DeprecationWarning, match="missing entry_url"):
        connector = fda.FDAConnector()
        # Should still work with fallback
        records, _ = connector.collect(cursor=None, max_items=10, offline=True)
        assert len(records) >= MIN_EXPECTED_RECORDS


def test_nws_deprecation_warning() -> None:
    """Test that NWSConnector without entry_url emits DeprecationWarning."""
    with pytest.warns(DeprecationWarning, match="missing entry_url"):
        connector = nws.NWSConnector()
        # Should still work with fallback
        records, _ = connector.collect(cursor=None, max_items=10, offline=True)
        assert len(records) > 0


def test_custom_connector_offline() -> None:
    """Test custom connector in offline mode."""
    entry_url = "https://example.com/"
    connector = custom.CustomConnector(entry_url=entry_url)
    records, next_cursor = connector.collect(cursor=None, max_items=10, offline=True)

    assert len(records) >= MIN_EXPECTED_RECORDS
    assert next_cursor is not None

    # Check first record has required keys
    first = records[0]
    assert "id" in first
    assert "title" in first
    assert "url" in first
    assert first["id"] == next_cursor

    # Check all records have required fields
    for rec in records:
        assert "id" in rec
        assert "title" in rec
        assert "url" in rec
        assert rec["id"]


def test_custom_connector_synthesis_warning(tmp_path, monkeypatch) -> None:
    """Test that custom connector emits UserWarning when fixture missing."""
    # Temporarily change to a dir without the fixture
    original_path = custom_mod.Path

    def mock_path(path_str: str) -> custom_mod.Path:
        p = original_path(path_str)
        # Force non-existence for the fixture
        if "custom_list.html" in str(p):
            return original_path("/nonexistent/custom_list.html")
        return p

    monkeypatch.setattr(custom_mod, "Path", mock_path)

    entry_url = "https://example.com/"
    with pytest.warns(UserWarning, match="Fixture not found"):
        connector = custom.CustomConnector(entry_url=entry_url)
        records, _ = connector.collect(cursor=None, max_items=10, offline=True)
        assert len(records) >= MIN_EXPECTED_RECORDS
