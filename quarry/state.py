"""SQLite state management for jobs and items."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DEFAULT_DB_PATH = "data/cache/state.sqlite"


def open_db(path: str | None = None) -> sqlite3.Connection:
    """Open or create SQLite database with proper schema."""
    db_path = path or _DEFAULT_DB_PATH
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Create tables
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs_state (
            job TEXT PRIMARY KEY,
            last_cursor TEXT,
            last_run TEXT
        )
    """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            job TEXT,
            id TEXT,
            payload_json TEXT,
            first_seen TEXT,
            last_seen TEXT,
            PRIMARY KEY (job, id)
        )
    """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS failed_urls (
            job TEXT,
            url TEXT,
            error_message TEXT,
            retry_count INTEGER,
            last_attempt TEXT,
            PRIMARY KEY (job, url)
        )
    """
    )
    conn.commit()
    return conn


def load_cursor(job: str, db_path: str | None = None) -> str | None:
    """Load the last cursor for a job."""
    conn = open_db(db_path)
    cursor = conn.execute("SELECT last_cursor FROM jobs_state WHERE job = ?", (job,)).fetchone()
    conn.close()
    return cursor["last_cursor"] if cursor and cursor["last_cursor"] else None


def save_cursor(job: str, cursor: str | None, db_path: str | None = None) -> None:
    """Save or update the cursor for a job."""
    conn = open_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO jobs_state (job, last_cursor, last_run)
        VALUES (?, ?, ?)
        ON CONFLICT(job) DO UPDATE SET
            last_cursor = excluded.last_cursor,
            last_run = excluded.last_run
    """,
        (job, cursor, now),
    )
    conn.commit()
    conn.close()


def upsert_items(job: str, records: list[dict[str, Any]], db_path: str | None = None) -> int:
    """
    Idempotent insert/update of items by (job, id).

    Returns:
        Count of newly inserted rows (0 if all were updates).
    """
    conn = open_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    new_count = 0

    for record in records:
        item_id = str(record.get("id", ""))
        if not item_id:
            continue

        payload_json = json.dumps(record)

        # Check if exists
        existing = conn.execute(
            "SELECT first_seen FROM items WHERE job = ? AND id = ?",
            (job, item_id),
        ).fetchone()

        if existing:
            # Update
            conn.execute(
                """
                UPDATE items
                SET payload_json = ?, last_seen = ?
                WHERE job = ? AND id = ?
            """,
                (payload_json, now, job, item_id),
            )
        else:
            # Insert
            new_count += 1
            conn.execute(
                """
                INSERT INTO items (job, id, payload_json, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?)
            """,
                (job, item_id, payload_json, now, now),
            )

    conn.commit()
    conn.close()
    return new_count


def record_failed_url(job: str, url: str, error_message: str, db_path: str | None = None) -> None:
    """
    Record a failed URL with error details.

    Increments retry_count if URL already failed before.
    """
    conn = open_db(db_path)
    now = datetime.now(timezone.utc).isoformat()

    # Check if URL already failed
    existing = conn.execute(
        "SELECT retry_count FROM failed_urls WHERE job = ? AND url = ?",
        (job, url),
    ).fetchone()

    if existing:
        # Increment retry count
        new_count = existing["retry_count"] + 1
        conn.execute(
            """
            UPDATE failed_urls
            SET error_message = ?, retry_count = ?, last_attempt = ?
            WHERE job = ? AND url = ?
        """,
            (error_message, new_count, now, job, url),
        )
    else:
        # First failure
        conn.execute(
            """
            INSERT INTO failed_urls (job, url, error_message, retry_count, last_attempt)
            VALUES (?, ?, ?, ?, ?)
        """,
            (job, url, error_message, 1, now),
        )

    conn.commit()
    conn.close()


def get_failed_urls(job: str, db_path: str | None = None) -> list[dict[str, Any]]:
    """
    Get all failed URLs for a job.

    Returns:
        List of dicts with keys: url, error_message, retry_count, last_attempt
    """
    conn = open_db(db_path)
    rows = conn.execute(
        "SELECT url, error_message, retry_count, last_attempt FROM failed_urls WHERE job = ?",
        (job,),
    ).fetchall()
    conn.close()

    return [dict(row) for row in rows]
