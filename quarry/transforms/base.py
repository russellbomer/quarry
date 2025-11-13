"""Base transform utilities."""

import pandas as pd

Frame = pd.DataFrame


def safe_to_iso(dt_str: str | None) -> str | None:
    """
    Convert datetime string to ISO format, or return None if invalid.

    Uses pandas.to_datetime with UTC and coercion.
    """
    if not dt_str:
        return None

    try:
        dt = pd.to_datetime(dt_str, utc=True, errors="coerce")
        if pd.isna(dt):
            return None
        return dt.isoformat()
    except Exception:
        return None
