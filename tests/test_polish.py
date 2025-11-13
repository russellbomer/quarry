"""Tests for Polish data transformation tool."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from foundry.tools.polish.deduplicator import Deduplicator
from foundry.tools.polish.transformers import (
    normalize_text,
    clean_whitespace,
    parse_date,
    extract_domain,
    remove_html_tags,
    truncate_text,
)
from foundry.tools.polish.validators import (
    validate_email,
    validate_url,
    validate_date_format,
    validate_length,
    validate_range,
    validate_record,
)
from foundry.tools.polish.processor import PolishProcessor


class TestDeduplicator:
    """Test the Deduplicator class."""
    
    def test_first_strategy_no_duplicates(self):
        """Test deduplication with no duplicates."""
        dedup = Deduplicator(strategy="first")
        
        record1 = {"title": "Item 1", "url": "http://example.com/1"}
        record2 = {"title": "Item 2", "url": "http://example.com/2"}
        
        assert not dedup.is_duplicate(record1)
        assert not dedup.is_duplicate(record2)
        
        stats = dedup.get_stats()
        assert stats["unique_count"] == 2
    
    def test_first_strategy_with_duplicates(self):
        """Test deduplication keeps first occurrence."""
        dedup = Deduplicator(strategy="first")
        
        record1 = {"title": "Item 1", "url": "http://example.com"}
        record2 = {"title": "Item 1", "url": "http://example.com"}
        
        assert not dedup.is_duplicate(record1)  # First - keep
        assert dedup.is_duplicate(record2)      # Duplicate - skip
    
    def test_key_fields_deduplication(self):
        """Test deduplication using specific key fields."""
        dedup = Deduplicator(key_fields=["title"], strategy="first")
        
        record1 = {"title": "Item 1", "url": "http://example.com/1"}
        record2 = {"title": "Item 1", "url": "http://example.com/2"}  # Different URL
        
        assert not dedup.is_duplicate(record1)
        assert dedup.is_duplicate(record2)  # Same title = duplicate
    
    def test_last_strategy(self):
        """Test deduplication keeps last occurrence."""
        dedup = Deduplicator(key_fields=["title"], strategy="last")
        
        record1 = {"title": "Item 1", "value": "first"}
        record2 = {"title": "Item 1", "value": "last"}
        
        dedup.is_duplicate(record1)
        dedup.is_duplicate(record2)
        
        unique = dedup.get_unique_records()
        assert len(unique) == 1
        assert unique[0]["value"] == "last"
    
    def test_ignores_metadata(self):
        """Test that _meta field is ignored in deduplication."""
        dedup = Deduplicator(strategy="first")
        
        record1 = {"title": "Item 1", "_meta": {"timestamp": "2024-01-01"}}
        record2 = {"title": "Item 1", "_meta": {"timestamp": "2024-01-02"}}
        
        assert not dedup.is_duplicate(record1)
        assert dedup.is_duplicate(record2)  # Same data, different meta


class TestTransformers:
    """Test transformation functions."""
    
    def test_normalize_text(self):
        """Test text normalization."""
        assert normalize_text("  Hello   World  ") == "Hello World"
        assert normalize_text("Single") == "Single"
        assert normalize_text("   ") is None
        assert normalize_text(None) is None
    
    def test_clean_whitespace(self):
        """Test whitespace cleaning."""
        assert clean_whitespace("  Hello   World  ") == "Hello World"
        assert clean_whitespace("NoSpaces") == "NoSpaces"
        assert clean_whitespace("   ") is None
    
    def test_parse_date_iso(self):
        """Test parsing ISO date."""
        assert parse_date("2024-01-15") == "2024-01-15"
    
    def test_parse_date_us_format(self):
        """Test parsing US date format."""
        assert parse_date("01/15/2024") == "2024-01-15"
    
    def test_parse_date_written(self):
        """Test parsing written date."""
        assert parse_date("January 15, 2024") == "2024-01-15"
        assert parse_date("Jan 15, 2024") == "2024-01-15"
    
    def test_parse_date_invalid(self):
        """Test parsing invalid date."""
        assert parse_date("not a date") is None
        assert parse_date(None) is None
    
    def test_extract_domain(self):
        """Test domain extraction from URLs."""
        assert extract_domain("https://www.example.com/path") == "example.com"
        assert extract_domain("http://subdomain.example.org/page") == "subdomain.example.org"
        assert extract_domain("example.com") == "example.com"
        assert extract_domain("www.example.com") == "example.com"
        assert extract_domain(None) is None
    
    def test_remove_html_tags(self):
        """Test HTML tag removal."""
        assert remove_html_tags("<p>Hello</p>") == "Hello"
        assert remove_html_tags("<div>Hello <b>World</b></div>") == "Hello World"
        assert remove_html_tags("No tags") == "No tags"
        assert remove_html_tags(None) is None
    
    def test_truncate_text(self):
        """Test text truncation."""
        long_text = "A" * 200
        truncated = truncate_text(long_text, max_length=100)
        assert len(truncated) <= 103  # 100 + "..."
        assert truncated.endswith("...")
        
        short_text = "Short"
        assert truncate_text(short_text, max_length=100) == "Short"


class TestValidators:
    """Test validation functions."""
    
    def test_validate_email(self):
        """Test email validation."""
        assert validate_email("user@example.com") is True
        assert validate_email("user.name+tag@example.co.uk") is True
        assert validate_email("invalid@") is False
        assert validate_email("@example.com") is False
        assert validate_email("not-an-email") is False
        assert validate_email(None) is False
    
    def test_validate_url(self):
        """Test URL validation."""
        assert validate_url("https://example.com") is True
        assert validate_url("http://example.com/path") is True
        assert validate_url("https://sub.example.com/path?query=1") is True
        assert validate_url("not-a-url") is False
        assert validate_url("example.com") is False  # Missing protocol
        assert validate_url(None) is False
    
    def test_validate_date_format(self):
        """Test date format validation."""
        assert validate_date_format("2024-01-15") is True
        assert validate_date_format("2024-13-45") is True  # Passes regex, not date validity
        assert validate_date_format("01/15/2024") is False  # Wrong format
        assert validate_date_format(None) is False
    
    def test_validate_length(self):
        """Test length validation."""
        assert validate_length("Hello", min_len=3, max_len=10) is True
        assert validate_length("Hi", min_len=3) is False
        assert validate_length("Very long text", max_len=5) is False
        assert validate_length(None, min_len=1) is False
    
    def test_validate_range(self):
        """Test numeric range validation."""
        assert validate_range(5, min_val=0, max_val=10) is True
        assert validate_range(5, min_val=10) is False
        assert validate_range(5, max_val=3) is False
        assert validate_range(None, min_val=0) is False
    
    def test_validate_record_required(self):
        """Test record validation with required fields."""
        rules = {
            "title": {"required": True},
            "email": {"type": "email"},
        }
        
        # Valid record
        record1 = {"title": "Test", "email": "user@example.com"}
        errors = validate_record(record1, rules)
        assert len(errors) == 0
        
        # Missing required field
        record2 = {"email": "user@example.com"}
        errors = validate_record(record2, rules)
        assert len(errors) == 1
        assert errors[0].field == "title"
    
    def test_validate_record_types(self):
        """Test record validation with type checks."""
        rules = {
            "email": {"type": "email"},
            "url": {"type": "url"},
        }
        
        # Valid record
        record1 = {"email": "user@example.com", "url": "https://example.com"}
        errors = validate_record(record1, rules)
        assert len(errors) == 0
        
        # Invalid email
        record2 = {"email": "not-email", "url": "https://example.com"}
        errors = validate_record(record2, rules)
        assert len(errors) == 1
        assert errors[0].field == "email"


class TestPolishProcessor:
    """Test the PolishProcessor class."""
    
    def test_process_basic(self):
        """Test basic processing without transformations."""
        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.jsonl"
            output_file = Path(tmpdir) / "output.jsonl"
            
            # Create input file
            with input_file.open("w") as f:
                f.write(json.dumps({"title": "Item 1"}) + "\n")
                f.write(json.dumps({"title": "Item 2"}) + "\n")
            
            # Process
            processor = PolishProcessor()
            stats = processor.process(input_file, output_file)
            
            assert stats["records_read"] == 2
            assert stats["records_written"] == 2
            assert stats["records_skipped"] == 0
    
    def test_process_with_deduplication(self):
        """Test processing with deduplication."""
        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.jsonl"
            output_file = Path(tmpdir) / "output.jsonl"
            
            # Create input with duplicates
            with input_file.open("w") as f:
                f.write(json.dumps({"title": "Item 1"}) + "\n")
                f.write(json.dumps({"title": "Item 2"}) + "\n")
                f.write(json.dumps({"title": "Item 1"}) + "\n")  # Duplicate
            
            # Process with deduplication
            processor = PolishProcessor()
            stats = processor.process(
                input_file,
                output_file,
                deduplicate=True,
                dedupe_strategy="first",
            )
            
            assert stats["records_read"] == 3
            assert stats["records_written"] == 2
            assert stats["duplicates_removed"] == 1
    
    def test_process_with_transformations(self):
        """Test processing with field transformations."""
        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.jsonl"
            output_file = Path(tmpdir) / "output.jsonl"
            
            # Create input
            with input_file.open("w") as f:
                f.write(json.dumps({"url": "https://www.example.com/path"}) + "\n")
            
            # Process with transformation
            processor = PolishProcessor()
            processor.process(
                input_file,
                output_file,
                transformations={
                    "url": [{"transform": "extract_domain"}]
                }
            )
            
            # Check output
            with output_file.open("r") as f:
                record = json.loads(f.readline())
                assert record["url"] == "example.com"
    
    def test_process_with_filter(self):
        """Test processing with filter function."""
        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.jsonl"
            output_file = Path(tmpdir) / "output.jsonl"
            
            # Create input
            with input_file.open("w") as f:
                f.write(json.dumps({"value": 10}) + "\n")
                f.write(json.dumps({"value": 5}) + "\n")
                f.write(json.dumps({"value": 15}) + "\n")
            
            # Process with filter (keep only value >= 10)
            processor = PolishProcessor()
            stats = processor.process(
                input_file,
                output_file,
                filter_func=lambda r: r.get("value", 0) >= 10
            )
            
            assert stats["records_read"] == 3
            assert stats["records_written"] == 2
            assert stats["records_skipped"] == 1


class TestIntegration:
    """Integration tests with real-world scenarios."""
    
    def test_full_pipeline(self):
        """Test complete polish pipeline."""
        with TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "input.jsonl"
            output_file = Path(tmpdir) / "output.jsonl"
            
            # Create realistic input
            with input_file.open("w") as f:
                # Duplicate items with transformable data
                f.write(json.dumps({
                    "title": "  Item 1  ",
                    "url": "https://www.example.com/page1",
                    "description": "  <p>HTML  content</p>  "
                }) + "\n")
                f.write(json.dumps({
                    "title": "Item 2",
                    "url": "https://another.com/page2",
                    "description": "Normal text"
                }) + "\n")
                f.write(json.dumps({
                    "title": "  Item 1  ",  # Duplicate
                    "url": "https://www.example.com/page1",
                    "description": "  <p>HTML  content</p>  "
                }) + "\n")
            
            # Process with everything
            processor = PolishProcessor()
            stats = processor.process(
                input_file,
                output_file,
                deduplicate=True,
                dedupe_keys=["title", "url"],
                transformations={
                    "title": [{"transform": "clean_whitespace"}],
                    "url": [{"transform": "extract_domain"}],
                    "description": [
                        {"transform": "remove_html_tags"},
                        {"transform": "clean_whitespace"},
                    ],
                },
            )
            
            assert stats["records_read"] == 3
            assert stats["records_written"] == 2
            assert stats["duplicates_removed"] == 1
            
            # Verify transformations
            with output_file.open("r") as f:
                record1 = json.loads(f.readline())
                assert record1["title"] == "Item 1"
                assert record1["url"] == "example.com"
                assert record1["description"] == "HTML content"
