"""Tests for quarry/tools/polish/deduplicator.py."""

import pytest

from quarry.tools.polish.deduplicator import Deduplicator


class TestDeduplicatorInit:
    """Tests for Deduplicator initialization."""

    def test_init_defaults(self):
        """Test default initialization."""
        dedup = Deduplicator()

        assert dedup.key_fields is None
        assert dedup.strategy == "first"
        assert len(dedup.seen_hashes) == 0
        assert len(dedup.last_records) == 0
        assert dedup.processed_count == 0
        assert dedup.duplicate_count == 0

    def test_init_with_key_fields(self):
        """Test initialization with key fields."""
        dedup = Deduplicator(key_fields=["id", "name"])

        assert dedup.key_fields == ["id", "name"]

    def test_init_with_last_strategy(self):
        """Test initialization with last strategy."""
        dedup = Deduplicator(strategy="last")

        assert dedup.strategy == "last"


class TestDeduplicatorComputeHash:
    """Tests for hash computation."""

    def test_compute_hash_full_record(self):
        """Test hash computation for full record."""
        dedup = Deduplicator()

        record = {"id": 1, "name": "Alice"}
        hash1 = dedup._compute_hash(record)
        hash2 = dedup._compute_hash(record)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_compute_hash_different_records(self):
        """Test different records produce different hashes."""
        dedup = Deduplicator()

        record1 = {"id": 1, "name": "Alice"}
        record2 = {"id": 2, "name": "Bob"}

        hash1 = dedup._compute_hash(record1)
        hash2 = dedup._compute_hash(record2)

        assert hash1 != hash2

    def test_compute_hash_key_fields_only(self):
        """Test hash uses only key fields when specified."""
        dedup = Deduplicator(key_fields=["id"])

        record1 = {"id": 1, "name": "Alice"}
        record2 = {"id": 1, "name": "Different"}

        hash1 = dedup._compute_hash(record1)
        hash2 = dedup._compute_hash(record2)

        # Same id = same hash despite different name
        assert hash1 == hash2

    def test_compute_hash_excludes_meta(self):
        """Test hash excludes _meta field."""
        dedup = Deduplicator()

        record1 = {"id": 1, "_meta": {"timestamp": "2024-01-01"}}
        record2 = {"id": 1, "_meta": {"timestamp": "2024-01-02"}}

        hash1 = dedup._compute_hash(record1)
        hash2 = dedup._compute_hash(record2)

        assert hash1 == hash2

    def test_compute_hash_handles_missing_key_fields(self):
        """Test hash handles missing key fields gracefully."""
        dedup = Deduplicator(key_fields=["id", "missing_field"])

        record = {"id": 1, "name": "Alice"}
        hash1 = dedup._compute_hash(record)

        # Should not raise, missing field becomes None
        assert len(hash1) == 64


class TestDeduplicatorFirstStrategy:
    """Tests for 'first' deduplication strategy."""

    def test_first_unique_returns_false(self):
        """Test first unique record returns False (not duplicate)."""
        dedup = Deduplicator(strategy="first")

        result = dedup.is_duplicate({"id": 1})

        assert result is False
        assert dedup.processed_count == 1
        assert dedup.duplicate_count == 0

    def test_first_duplicate_returns_true(self):
        """Test subsequent duplicate returns True."""
        dedup = Deduplicator(strategy="first")

        dedup.is_duplicate({"id": 1})
        result = dedup.is_duplicate({"id": 1})

        assert result is True
        assert dedup.processed_count == 2
        assert dedup.duplicate_count == 1

    def test_first_different_records_all_unique(self):
        """Test different records are all unique."""
        dedup = Deduplicator(strategy="first")

        results = [
            dedup.is_duplicate({"id": i})
            for i in range(5)
        ]

        assert all(r is False for r in results)
        assert dedup.duplicate_count == 0

    def test_first_tracks_seen_hashes(self):
        """Test first strategy tracks seen hashes."""
        dedup = Deduplicator(strategy="first")

        dedup.is_duplicate({"id": 1})
        dedup.is_duplicate({"id": 2})
        dedup.is_duplicate({"id": 1})  # Duplicate

        assert len(dedup.seen_hashes) == 2


class TestDeduplicatorLastStrategy:
    """Tests for 'last' deduplication strategy."""

    def test_last_always_returns_false_during_processing(self):
        """Test last strategy never returns True during processing."""
        dedup = Deduplicator(strategy="last")

        results = [
            dedup.is_duplicate({"id": 1}),
            dedup.is_duplicate({"id": 1}),  # Duplicate
            dedup.is_duplicate({"id": 1}),  # Another duplicate
        ]

        # Never skip during processing
        assert all(r is False for r in results)

    def test_last_counts_duplicates(self):
        """Test last strategy counts duplicates correctly."""
        dedup = Deduplicator(strategy="last", key_fields=["id"])

        dedup.is_duplicate({"id": 1, "value": "first"})
        dedup.is_duplicate({"id": 1, "value": "second"})
        dedup.is_duplicate({"id": 1, "value": "third"})

        # Duplicate count tracks when hash already exists in last_records
        assert dedup.duplicate_count == 2
        assert dedup.processed_count == 3

    def test_last_stores_records(self):
        """Test last strategy stores records for later retrieval."""
        dedup = Deduplicator(strategy="last", key_fields=["id"])

        dedup.is_duplicate({"id": 1, "value": "first"})
        dedup.is_duplicate({"id": 1, "value": "last"})

        assert len(dedup.last_records) == 1  # Only one unique key

    def test_get_unique_records_returns_last(self):
        """Test get_unique_records returns last occurrence."""
        dedup = Deduplicator(strategy="last", key_fields=["id"])

        dedup.is_duplicate({"id": 1, "value": "first"})
        dedup.is_duplicate({"id": 2, "value": "only"})
        dedup.is_duplicate({"id": 1, "value": "last"})

        unique = dedup.get_unique_records()

        assert len(unique) == 2
        values = [r["value"] for r in unique]
        assert "last" in values
        assert "only" in values
        assert "first" not in values


class TestDeduplicatorGetUniqueRecords:
    """Tests for get_unique_records method."""

    def test_get_unique_records_raises_for_first_strategy(self):
        """Test get_unique_records raises error for first strategy."""
        dedup = Deduplicator(strategy="first")

        dedup.is_duplicate({"id": 1})

        with pytest.raises(ValueError, match="only valid for 'last' strategy"):
            dedup.get_unique_records()

    def test_get_unique_records_empty_for_no_records(self):
        """Test get_unique_records returns empty for no records."""
        dedup = Deduplicator(strategy="last")

        unique = dedup.get_unique_records()

        assert unique == []


class TestDeduplicatorReset:
    """Tests for reset functionality."""

    def test_reset_clears_all_state(self):
        """Test reset clears all tracking state."""
        dedup = Deduplicator(strategy="first")

        dedup.is_duplicate({"id": 1})
        dedup.is_duplicate({"id": 2})
        dedup.is_duplicate({"id": 1})

        dedup.reset()

        assert len(dedup.seen_hashes) == 0
        assert len(dedup.last_records) == 0
        assert dedup.processed_count == 0
        assert dedup.duplicate_count == 0

    def test_reset_allows_reprocessing(self):
        """Test after reset, previously seen records are unique again."""
        dedup = Deduplicator(strategy="first")

        dedup.is_duplicate({"id": 1})
        assert dedup.is_duplicate({"id": 1}) is True

        dedup.reset()

        # Same record now unique again
        assert dedup.is_duplicate({"id": 1}) is False


class TestDeduplicatorGetStats:
    """Tests for get_stats method."""

    def test_get_stats_first_strategy(self):
        """Test get_stats for first strategy."""
        dedup = Deduplicator(strategy="first")

        dedup.is_duplicate({"id": 1})
        dedup.is_duplicate({"id": 2})
        dedup.is_duplicate({"id": 1})
        dedup.is_duplicate({"id": 3})

        stats = dedup.get_stats()

        assert stats["processed_count"] == 4
        assert stats["unique_count"] == 3
        assert stats["duplicate_count"] == 1

    def test_get_stats_last_strategy(self):
        """Test get_stats for last strategy."""
        dedup = Deduplicator(strategy="last", key_fields=["id"])

        dedup.is_duplicate({"id": 1, "v": 1})
        dedup.is_duplicate({"id": 2, "v": 1})
        dedup.is_duplicate({"id": 1, "v": 2})

        stats = dedup.get_stats()

        assert stats["processed_count"] == 3
        assert stats["unique_count"] == 2
        assert stats["duplicate_count"] == 1

    def test_get_stats_empty(self):
        """Test get_stats with no records processed."""
        dedup = Deduplicator()

        stats = dedup.get_stats()

        assert stats["processed_count"] == 0
        assert stats["unique_count"] == 0
        assert stats["duplicate_count"] == 0


class TestDeduplicatorEdgeCases:
    """Tests for edge cases."""

    def test_empty_record(self):
        """Test handling empty records."""
        dedup = Deduplicator()

        result1 = dedup.is_duplicate({})
        result2 = dedup.is_duplicate({})

        assert result1 is False
        assert result2 is True

    def test_nested_values(self):
        """Test handling nested values in records."""
        dedup = Deduplicator()

        record = {"id": 1, "data": {"nested": "value"}}
        result1 = dedup.is_duplicate(record)
        result2 = dedup.is_duplicate(record)

        assert result1 is False
        assert result2 is True

    def test_list_values(self):
        """Test handling list values in records."""
        dedup = Deduplicator()

        record = {"id": 1, "tags": ["a", "b", "c"]}
        result1 = dedup.is_duplicate(record)
        result2 = dedup.is_duplicate(record)

        assert result1 is False
        assert result2 is True

    def test_order_independent_hashing(self):
        """Test hash is independent of key order."""
        dedup = Deduplicator()

        record1 = {"a": 1, "b": 2}
        record2 = {"b": 2, "a": 1}

        hash1 = dedup._compute_hash(record1)
        hash2 = dedup._compute_hash(record2)

        assert hash1 == hash2
