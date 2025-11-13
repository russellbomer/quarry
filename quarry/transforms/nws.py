"""NWS alert normalization."""

from quarry.transforms.base import Frame, safe_to_iso

_SEVERITY_WEIGHT = {"Warning": 3, "Watch": 2, "Advisory": 1}


def normalize(records: list[dict]) -> Frame:
    """Normalize NWS alert records into DataFrame."""
    rows = []
    for rec in records:
        type_val = rec.get("type", "Advisory")
        severity = rec.get("severity")
        severity_weight = _SEVERITY_WEIGHT.get(type_val, 1)

        rows.append(
            {
                "id": rec.get("id", ""),
                "source": "nws",
                "title": rec.get("headline", ""),
                "url": rec.get("url", ""),
                "posted_at": safe_to_iso(rec.get("start")),
                "type": type_val,
                "area": rec.get("area", ""),
                "severity": severity,
                "severity_weight": severity_weight,
                "end": safe_to_iso(rec.get("end")),
            }
        )

    return Frame(rows)
