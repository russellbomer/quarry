"""Tests for failed URL tracking."""

import tempfile
from pathlib import Path

from quarry.state import get_failed_urls, open_db, record_failed_url

# Test constants
EXPECTED_RETRY_COUNT = 3
EXPECTED_FAILED_COUNT = 3


def test_record_failed_url_new():
    """Recording a new failed URL initializes retry count to 1."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")

        record_failed_url("test_job", "https://example.com/page", "Timeout error", db_path)

        failed = get_failed_urls("test_job", db_path)
        assert len(failed) == 1
        assert failed[0]["url"] == "https://example.com/page"
        assert failed[0]["error_message"] == "Timeout error"
        assert failed[0]["retry_count"] == 1


def test_record_failed_url_duplicate():
    """Recording same URL multiple times increments retry count."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")

        # Fail 3 times
        record_failed_url("test_job", "https://example.com/page", "Error 1", db_path)
        record_failed_url("test_job", "https://example.com/page", "Error 2", db_path)
        record_failed_url("test_job", "https://example.com/page", "Error 3", db_path)

        failed = get_failed_urls("test_job", db_path)
        assert len(failed) == 1
        assert failed[0]["retry_count"] == EXPECTED_RETRY_COUNT
        assert failed[0]["error_message"] == "Error 3"  # Latest error


def test_record_failed_url_multiple():
    """Different URLs are tracked independently."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")

        record_failed_url("test_job", "https://example.com/page1", "Error A", db_path)
        record_failed_url("test_job", "https://example.com/page2", "Error B", db_path)
        record_failed_url("test_job", "https://example.com/page3", "Error C", db_path)

        failed = get_failed_urls("test_job", db_path)
        assert len(failed) == EXPECTED_FAILED_COUNT

        urls = {f["url"] for f in failed}
        assert urls == {
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3",
        }


def test_failed_urls_job_isolation():
    """Failed URLs are isolated per job."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")

        record_failed_url("job1", "https://example.com/page", "Error X", db_path)
        record_failed_url("job2", "https://example.com/page", "Error Y", db_path)

        failed_job1 = get_failed_urls("job1", db_path)
        failed_job2 = get_failed_urls("job2", db_path)

        assert len(failed_job1) == 1
        assert len(failed_job2) == 1
        assert failed_job1[0]["error_message"] == "Error X"
        assert failed_job2[0]["error_message"] == "Error Y"


def test_failed_urls_table_created():
    """Failed URLs table is created automatically."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test.db")

        conn = open_db(db_path)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        assert "failed_urls" in tables
