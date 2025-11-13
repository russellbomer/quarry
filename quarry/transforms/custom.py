"""Custom record normalization."""

from quarry.transforms.base import Frame, safe_to_iso


def normalize(records: list[dict]) -> Frame:
    """Normalize custom records into DataFrame."""
    rows = []
    for rec in records:
        rows.append(
            {
                "id": rec.get("id", ""),
                "source": "custom",
                "title": rec.get("title", ""),
                "url": rec.get("url", ""),
                "posted_at": safe_to_iso(rec.get("posted_at")),
            }
        )

    return Frame(rows)
