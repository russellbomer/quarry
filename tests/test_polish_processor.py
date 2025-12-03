"""Tests for quarry/tools/polish/processor.py."""

import json
import tempfile
from pathlib import Path

import pytest

from quarry.tools.polish.processor import PolishProcessor


class TestPolishProcessorInit:
    """Tests for PolishProcessor initialization."""

    def test_init_creates_empty_stats(self):
        """Test processor initializes with zeroed stats."""
        processor = PolishProcessor()

        assert processor.stats["records_read"] == 0
        assert processor.stats["records_written"] == 0
        assert processor.stats["records_skipped"] == 0
        assert processor.stats["duplicates_removed"] == 0
        assert processor.stats["validation_errors"] == 0


class TestPolishProcessorBasic:
    """Tests for basic processing functionality."""

    def test_process_simple_copy(self, tmp_path):
        """Test processing without transformations copies records."""
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"

        records = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        input_file.write_text("\n".join(json.dumps(r) for r in records))

        processor = PolishProcessor()
        stats = processor.process(input_file, output_file)

        assert stats["records_read"] == 2
        assert stats["records_written"] == 2
        assert stats["records_skipped"] == 0

        # Verify output
        output_lines = output_file.read_text().strip().split("\n")
        assert len(output_lines) == 2

    def test_process_skips_empty_lines(self, tmp_path):
        """Test processor skips empty lines in input."""
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"

        input_file.write_text('{"id": 1}\n\n{"id": 2}\n   \n{"id": 3}')

        processor = PolishProcessor()
        stats = processor.process(input_file, output_file)

        assert stats["records_read"] == 3
        assert stats["records_written"] == 3

    def test_process_skips_invalid_json(self, tmp_path):
        """Test processor skips lines with invalid JSON."""
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"

        input_file.write_text('{"id": 1}\nnot json\n{"id": 2}')

        processor = PolishProcessor()
        stats = processor.process(input_file, output_file)

        assert stats["records_read"] == 2
        assert stats["records_skipped"] == 1
        assert stats["records_written"] == 2

    def test_process_creates_output_directory(self, tmp_path):
        """Test processor creates output directory if missing."""
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "nested" / "dir" / "output.jsonl"

        input_file.write_text('{"id": 1}')

        processor = PolishProcessor()
        processor.process(input_file, output_file)

        assert output_file.exists()


class TestPolishProcessorTransformations:
    """Tests for transformation functionality."""

    def test_apply_single_transformation(self, tmp_path):
        """Test applying a single transformation to a field."""
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"

        input_file.write_text('{"name": "  hello world  "}')

        transformations = {
            "name": [{"transform": "normalize_text"}]
        }

        processor = PolishProcessor()
        processor.process(input_file, output_file, transformations=transformations)

        output = json.loads(output_file.read_text().strip())
        assert output["name"] == "hello world"

    def test_apply_multiple_transformations_to_field(self, tmp_path):
        """Test applying multiple transformations to same field."""
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"

        input_file.write_text('{"text": "  HELLO WORLD  "}')

        transformations = {
            "text": [
                {"transform": "normalize_text"},
                {"transform": "lowercase"},
            ]
        }

        processor = PolishProcessor()
        processor.process(input_file, output_file, transformations=transformations)

        output = json.loads(output_file.read_text().strip())
        assert output["text"] == "hello world"

    def test_transformation_with_kwargs(self, tmp_path):
        """Test transformation with additional parameters."""
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"

        input_file.write_text('{"text": "This is a very long string"}')

        transformations = {
            "text": [{"transform": "truncate_text", "max_length": 10}]
        }

        processor = PolishProcessor()
        processor.process(input_file, output_file, transformations=transformations)

        output = json.loads(output_file.read_text().strip())
        # truncate_text adds "..." suffix so result may be max_length + 3
        assert len(output["text"]) <= 13

    def test_transformation_skips_missing_field(self, tmp_path):
        """Test transformation skips fields not in record."""
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"

        input_file.write_text('{"id": 1}')

        transformations = {
            "nonexistent": [{"transform": "uppercase"}]
        }

        processor = PolishProcessor()
        stats = processor.process(input_file, output_file, transformations=transformations)

        assert stats["records_written"] == 1
        output = json.loads(output_file.read_text().strip())
        assert output == {"id": 1}

    def test_transformation_skips_invalid_transform_name(self, tmp_path):
        """Test transformation skips when transform name missing."""
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"

        input_file.write_text('{"name": "test"}')

        transformations = {
            "name": [{"not_transform": "uppercase"}]  # Missing 'transform' key
        }

        processor = PolishProcessor()
        processor.process(input_file, output_file, transformations=transformations)

        output = json.loads(output_file.read_text().strip())
        assert output["name"] == "test"  # Unchanged

    def test_transformation_handles_errors_gracefully(self, tmp_path):
        """Test transformation errors don't crash processing."""
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"

        # parse_date returns None for invalid dates (doesn't raise)
        input_file.write_text('{"date": "not-a-date"}')

        transformations = {
            "date": [{"transform": "parse_date"}]
        }

        processor = PolishProcessor()
        stats = processor.process(input_file, output_file, transformations=transformations)

        assert stats["records_written"] == 1
        # parse_date returns None for unparseable dates
        output = json.loads(output_file.read_text().strip())
        assert output["date"] is None


class TestPolishProcessorDeduplication:
    """Tests for deduplication functionality."""

    def test_deduplicate_first_strategy(self, tmp_path):
        """Test deduplication with 'first' strategy."""
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"

        records = [
            {"id": 1, "name": "First"},
            {"id": 1, "name": "Duplicate"},
            {"id": 2, "name": "Second"},
        ]
        input_file.write_text("\n".join(json.dumps(r) for r in records))

        processor = PolishProcessor()
        stats = processor.process(
            input_file,
            output_file,
            deduplicate=True,
            dedupe_keys=["id"],
            dedupe_strategy="first",
        )

        assert stats["records_read"] == 3
        assert stats["duplicates_removed"] == 1
        assert stats["records_written"] == 2

        output_lines = output_file.read_text().strip().split("\n")
        output_records = [json.loads(line) for line in output_lines]
        assert output_records[0]["name"] == "First"

    def test_deduplicate_last_strategy(self, tmp_path):
        """Test deduplication with 'last' strategy."""
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"

        records = [
            {"id": 1, "name": "First"},
            {"id": 1, "name": "Last"},
            {"id": 2, "name": "Second"},
        ]
        input_file.write_text("\n".join(json.dumps(r) for r in records))

        processor = PolishProcessor()
        stats = processor.process(
            input_file,
            output_file,
            deduplicate=True,
            dedupe_keys=["id"],
            dedupe_strategy="last",
        )

        assert stats["records_read"] == 3
        assert stats["duplicates_removed"] == 1
        assert stats["records_written"] == 2

        output_lines = output_file.read_text().strip().split("\n")
        output_records = [json.loads(line) for line in output_lines]
        # Last duplicate should be kept
        names = [r["name"] for r in output_records]
        assert "Last" in names
        assert "First" not in names

    def test_deduplicate_without_keys_uses_full_record(self, tmp_path):
        """Test deduplication uses full record when no keys specified."""
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"

        records = [
            {"id": 1, "name": "Alice"},
            {"id": 1, "name": "Alice"},  # Exact duplicate
            {"id": 1, "name": "Different"},  # Same id but different name
        ]
        input_file.write_text("\n".join(json.dumps(r) for r in records))

        processor = PolishProcessor()
        stats = processor.process(
            input_file,
            output_file,
            deduplicate=True,
            dedupe_keys=None,  # Full record
        )

        assert stats["records_read"] == 3
        assert stats["duplicates_removed"] == 1  # Only exact duplicate removed
        assert stats["records_written"] == 2


class TestPolishProcessorValidation:
    """Tests for validation functionality."""

    def test_validation_errors_counted(self, tmp_path):
        """Test validation errors are counted."""
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"

        input_file.write_text('{"url": "not-a-url"}')

        validation_rules = {
            "url": {"type": "url"}
        }

        processor = PolishProcessor()
        stats = processor.process(
            input_file,
            output_file,
            validation_rules=validation_rules,
        )

        assert stats["validation_errors"] == 1
        assert stats["records_written"] == 1  # Still written without skip_invalid

    def test_skip_invalid_skips_failed_validation(self, tmp_path):
        """Test skip_invalid skips records failing validation."""
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"

        records = [
            {"url": "https://example.com"},
            {"url": "not-a-url"},
        ]
        input_file.write_text("\n".join(json.dumps(r) for r in records))

        validation_rules = {
            "url": {"type": "url"}
        }

        processor = PolishProcessor()
        stats = processor.process(
            input_file,
            output_file,
            validation_rules=validation_rules,
            skip_invalid=True,
        )

        assert stats["validation_errors"] == 1
        assert stats["records_skipped"] == 1
        assert stats["records_written"] == 1


class TestPolishProcessorFilter:
    """Tests for filter function."""

    def test_filter_func_filters_records(self, tmp_path):
        """Test filter_func filters out records."""
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"

        records = [
            {"id": 1, "status": "active"},
            {"id": 2, "status": "inactive"},
            {"id": 3, "status": "active"},
        ]
        input_file.write_text("\n".join(json.dumps(r) for r in records))

        # Only keep active records
        def filter_active(record):
            return record.get("status") == "active"

        processor = PolishProcessor()
        stats = processor.process(
            input_file,
            output_file,
            filter_func=filter_active,
        )

        assert stats["records_read"] == 3
        assert stats["records_skipped"] == 1
        assert stats["records_written"] == 2


class TestPolishProcessorCombined:
    """Tests for combined operations."""

    def test_transform_filter_and_deduplicate(self, tmp_path):
        """Test combining transformations, filter, and deduplication."""
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"

        records = [
            {"id": 1, "name": "  ALICE  ", "active": True},
            {"id": 1, "name": "  alice  ", "active": True},  # Duplicate by id
            {"id": 2, "name": "  BOB  ", "active": False},  # Filtered out
            {"id": 3, "name": "  CAROL  ", "active": True},
        ]
        input_file.write_text("\n".join(json.dumps(r) for r in records))

        processor = PolishProcessor()
        stats = processor.process(
            input_file,
            output_file,
            deduplicate=True,
            dedupe_keys=["id"],
            transformations={
                "name": [{"transform": "normalize_text"}, {"transform": "lowercase"}]
            },
            filter_func=lambda r: r.get("active"),
        )

        assert stats["records_read"] == 4
        assert stats["records_skipped"] == 1  # Bob filtered
        assert stats["duplicates_removed"] == 1
        assert stats["records_written"] == 2

        output_lines = output_file.read_text().strip().split("\n")
        output_records = [json.loads(line) for line in output_lines]
        names = [r["name"] for r in output_records]
        assert "alice" in names
        assert "carol" in names
