"""FDA recall normalization."""

from quarry.transforms.base import Frame, safe_to_iso

_CLASS_WEIGHT = {"I": 3, "II": 2, "III": 1}


def normalize(records: list[dict]) -> Frame:
    """Normalize FDA recall records into DataFrame."""
    rows = []
    for rec in records:
        class_val = rec.get("class", "")
        class_weight = _CLASS_WEIGHT.get(class_val, 1)

        rows.append(
            {
                "id": rec.get("id", ""),
                "source": "fda",
                "title": rec.get("title", ""),
                "url": rec.get("url", ""),
                "posted_at": safe_to_iso(rec.get("posted_at")),
                "class": class_val,
                "class_weight": class_weight,
                "category": rec.get("category", ""),
                "brand": rec.get("brand", ""),
                "reason": rec.get("reason", ""),
                "description": rec.get("description", ""),
            }
        )

    return Frame(rows)
